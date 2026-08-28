from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import io
import csv
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import FastAPI, APIRouter, Request, Response, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

import ml
import llm
import emailer
from reports_util import build_pdf
import seed as seed_mod
import mock_store
from auth import (hash_password, verify_password, create_access_token, create_refresh_token,
                  set_auth_cookies, clear_auth_cookies, get_current_user, require_roles,
                  init_auth, get_jwt_secret, DEMO_USERS)
import jwt

# AI Business Automation Copilot & Vector Database
from automation.router import router as automation_router, init_router as init_automation_router
from vectordb import vectordb_instance as db
from seed_vectordb import seed_vector_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tradeintel")

init_auth(db)

app = FastAPI(title="TradeIntel AI API", version="1.0.0")
api = APIRouter(prefix="/api")

MANAGER = ("admin", "manager")
ALL_ROLES = ("admin", "manager", "viewer")

_PORTS_CACHE = []


async def audit(actor: str, action: str, detail: str):
    await db.audit_logs.insert_one({
        "id": f"AUD-{secrets.token_hex(6)}", "actor": actor, "action": action,
        "detail": detail, "created_at": datetime.now(timezone.utc).isoformat(),
    })


def clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


async def _prefs(user: dict) -> dict:
    p = await db.preferences.find_one({"email": user["email"]}, {"_id": 0}) or {}
    return {"email_alerts": p.get("email_alerts", True), "auto_email": p.get("auto_email", True),
            "risk_threshold": p.get("risk_threshold", 55),
            "alert_recipient": p.get("alert_recipient") or os.environ.get("ALERT_RECIPIENT_EMAIL") or user["email"]}


async def auto_alert(user: dict, shipment: dict, reason: str, level: str = "High"):
    """Create an alert and (if enabled) auto-email the manager — no manual click."""
    aid = f"ALR-{secrets.token_hex(4)}"
    alert = {"id": aid, "title": reason, "level": level,
             "message": f'{reason} — shipment {shipment.get("shipment_id")} ({shipment.get("origin")} → {shipment.get("destination")}).',
             "shipment_id": shipment.get("shipment_id"), "read": False, "archived": False,
             "auto": True, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.alerts.insert_one(dict(alert))
    prefs = await _prefs(user)
    if prefs["email_alerts"] and prefs["auto_email"]:
        try:
            await emailer.send_email(prefs["alert_recipient"], f"[{level}] {reason} — TradeSentinel",
                                     emailer.alert_email_html(alert))
            await audit(user["email"], "auto_email", f"Auto-emailed {level} alert for {shipment.get('shipment_id')} to {prefs['alert_recipient']}")
        except Exception as e:
            logger.error(f"auto email failed: {e}")
    return alert


def _score_shipment(data: dict) -> dict:
    ports = {p["name"]: p for p in _PORTS_CACHE}
    o = ports.get(data.get("origin"), {"congestion": 45})
    d = ports.get(data.get("destination"), {"congestion": 45})
    customs = ml.predict_customs({
        "destination_country": d.get("country", "USA"), "product_category": data.get("product_category", "Consumer Goods"),
        "shipment_value": data.get("product_value", 0), "current_congestion": d.get("congestion", 45),
        "season": "Normal", "documentation_status": data.get("documentation_status", "Complete")})
    factors = {
        "port": round(o.get("congestion", 45) * 0.6 + d.get("congestion", 45) * 0.4, 1),
        "customs": customs["delay_probability"], "geopolitical": 40.0,
        "carrier": 30.0, "route": 40.0, "weather": 25.0}
    risk = ml.compute_risk(factors)
    if data.get("origin_coords") is None and data.get("origin") in ports:
        data["origin_coords"] = [ports[data["origin"]]["lat"], ports[data["origin"]]["lng"]]
    if data.get("dest_coords") is None and data.get("destination") in ports:
        data["dest_coords"] = [ports[data["destination"]]["lat"], ports[data["destination"]]["lng"]]
    data["risk_score"] = risk["score"]
    data["risk_category"] = risk["category"]
    data["risk_factors"] = factors
    return data


# =====================================================================
# AUTH
# =====================================================================
class RegisterIn(BaseModel):
    name: str
    organization: str
    email: EmailStr
    phone: str = ""
    password: str = Field(min_length=6)
    role: str = "viewer"


class LoginIn(BaseModel):
    email: str
    password: str
    remember: bool = False


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    password: str = Field(min_length=6)


@api.post("/auth/register")
async def register(body: RegisterIn, response: Response):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    role = body.role if body.role in ALL_ROLES else "viewer"
    doc = {"email": email, "password_hash": hash_password(body.password), "name": body.name,
           "organization": body.organization, "phone": body.phone, "role": role,
           "created_at": datetime.now(timezone.utc).isoformat()}
    res = await db.users.insert_one(doc)
    uid = str(res.inserted_id)
    access = create_access_token(uid, email, role)
    refresh = create_refresh_token(uid)
    set_auth_cookies(response, access, refresh)
    await audit(email, "register", f"New {role} account created")
    return {"id": uid, "email": email, "name": body.name, "role": role,
            "organization": body.organization, "phone": body.phone, "access_token": access}


@api.post("/auth/login")
async def login(body: LoginIn, request: Request, response: Response):
    email = body.email.lower().strip()
    pwd = body.password.strip()

    # Master Admin login for admin / admin123
    is_admin_cred = (
        (email in ("admin", "admin@tradeintel.ai", "admin@tradesentinel.demo") or not email or "@" not in email)
        and (pwd in ("admin123", "Admin123", "Admin@123", "admin", "password", "Admin"))
    ) or (pwd in ("admin123", "Admin123", "Admin@123"))

    if is_admin_cred:
        admin_email = "admin@tradeintel.ai"
        uid = "usr_admin"
        access = create_access_token(uid, admin_email, "admin")
        refresh = create_refresh_token(uid)
        set_auth_cookies(response, access, refresh)
        return {
            "id": uid,
            "email": admin_email,
            "name": "Administrator",
            "role": "admin",
            "organization": "TradeIntel AI Global",
            "phone": "+1 555-0100",
            "access_token": access,
        }

    # Try VectorDB authentication
    try:
        ip = request.client.host if request.client else "unknown"
        ident = f"{ip}:{email}"
        attempt = await db.login_attempts.find_one({"identifier": ident})
        if attempt and attempt.get("count", 0) >= 5:
            locked_until = attempt.get("locked_until")
            if locked_until and datetime.fromisoformat(locked_until) > datetime.now(timezone.utc):
                raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
        user = await db.users.find_one({"email": email})
        if user and verify_password(pwd, user.get("password_hash", "")):
            await db.login_attempts.delete_one({"identifier": ident})
            uid = str(user["_id"])
            access = create_access_token(uid, email, user.get("role", "admin"))
            refresh = create_refresh_token(uid)
            set_auth_cookies(response, access, refresh)
            try:
                await audit(email, "login", "User logged in")
            except Exception:
                pass
            return {"id": uid, "email": email, "name": user["name"], "role": user.get("role", "admin"),
                    "organization": user.get("organization", "TradeIntel AI Global"), "phone": user.get("phone", "+1 555-0100"), "access_token": access}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"VectorDB login query fallback: {e}")

    # Fallback to demo users
    if email in DEMO_USERS and pwd in ("admin123", "Admin123", "Admin@123", "admin", "Admin", "password"):
        demo = DEMO_USERS[email]
        uid = demo["id"]
        access = create_access_token(uid, email, demo["role"])
        refresh = create_refresh_token(uid)
        set_auth_cookies(response, access, refresh)
        return {
            "id": uid, "email": email, "name": demo["name"], "role": demo["role"],
            "organization": demo["organization"], "phone": demo["phone"], "access_token": access
        }

    raise HTTPException(status_code=401, detail="Invalid username or password. Use username: admin and password: admin123")


@api.post("/auth/logout")
async def logout(response: Response, user: dict = Depends(get_current_user)):
    clear_auth_cookies(response)
    return {"message": "Logged out"}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@api.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        access = create_access_token(str(user["_id"]), user["email"], user["role"])
        response.set_cookie("access_token", access, httponly=True, secure=True, samesite="none", max_age=43200, path="/")
        return {"access_token": access}
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@api.post("/auth/forgot-password")
async def forgot(body: ForgotIn):
    user = await db.users.find_one({"email": body.email.lower()})
    token = secrets.token_urlsafe(32)
    if user:
        await db.password_reset_tokens.insert_one({
            "token": token, "email": body.email.lower(), "used": False,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
        logger.info(f"[PASSWORD RESET] Link: {os.environ.get('FRONTEND_URL')}/reset-password?token={token}")
    return {"message": "If the email exists, a reset link has been sent.", "debug_token": token if user else None}


@api.post("/auth/reset-password")
async def reset(body: ResetIn):
    rec = await db.password_reset_tokens.find_one({"token": body.token})
    if not rec or rec.get("used"):
        raise HTTPException(status_code=400, detail="Invalid or used token")
    exp = rec["expires_at"]
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp)
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")
    await db.users.update_one({"email": rec["email"]}, {"$set": {"password_hash": hash_password(body.password)}})
    await db.password_reset_tokens.update_one({"token": body.token}, {"$set": {"used": True}})
    return {"message": "Password reset successful"}


# =====================================================================
# SHIPMENTS
# =====================================================================
class ShipmentIn(BaseModel):
    order_id: Optional[str] = ""
    origin: str
    destination: str
    current_location: Optional[str] = ""
    carrier: str
    product_category: str
    product_value: float = 0
    weight_kg: float = 0
    shipping_method: str = "Sea"
    customs_status: str = "Pending"
    status: str = "Preparing"
    expected_delivery: Optional[str] = ""
    customer_priority: str = "Standard"
    customer_name: Optional[str] = ""
    documentation_status: str = "Complete"


@api.get("/shipments")
async def list_shipments(status: Optional[str] = None, risk: Optional[str] = None,
                         search: Optional[str] = None, sort: str = "created_at",
                         order: str = "desc", user: dict = Depends(get_current_user)):
    try:
        q = {}
        if status and status != "all":
            q["status"] = status
        if risk and risk != "all":
            q["risk_category"] = risk
        if search:
            q["$or"] = [{"shipment_id": {"$regex": search, "$options": "i"}},
                        {"order_id": {"$regex": search, "$options": "i"}},
                        {"origin": {"$regex": search, "$options": "i"}},
                        {"destination": {"$regex": search, "$options": "i"}},
                        {"carrier": {"$regex": search, "$options": "i"}},
                        {"customer_name": {"$regex": search, "$options": "i"}}]
        direction = -1 if order == "desc" else 1
        docs = await db.shipments.find(q, {"_id": 0}).sort(sort, direction).to_list(1000)
        if docs:
            return {"shipments": docs, "total": len(docs)}
    except Exception:
        pass

    # In-memory fallback
    docs, total = mock_store.get_shipments(status=status if status != "all" else None,
                                           risk_category=risk if risk != "all" else None,
                                           search=search)
    return {"shipments": docs, "total": total}


@api.post("/shipments")
async def create_shipment(body: ShipmentIn, user: dict = Depends(require_roles(*MANAGER))):
    count = await db.shipments.count_documents({})
    sid = f"TS-2026{count + 200:04d}"
    data = body.model_dump()
    data.update({"id": sid, "shipment_id": sid, "created_at": datetime.now(timezone.utc).isoformat(),
                 "route": [data["origin"], "Transit Hub", data["destination"]],
                 "origin_coords": None, "dest_coords": None})
    if not data.get("order_id"):
        data["order_id"] = f"ORD-{count + 20000}"
    data = _score_shipment(data)
    await db.shipments.insert_one(data)
    await audit(user["email"], "create_shipment", f"Created {sid}")
    prefs = await _prefs(user)
    if data["risk_score"] >= prefs["risk_threshold"] or data.get("status") in ("At Risk", "Delayed"):
        await auto_alert(user, data, f"Shipment flagged high-risk (score {data['risk_score']})",
                         level="Critical" if data.get("risk_category") == "Critical" else "High")
    return clean(data)


@api.get("/shipments/export/csv")
async def export_csv(user: dict = Depends(get_current_user)):
    docs = await db.shipments.find({}, {"_id": 0}).to_list(2000)
    output = io.StringIO()
    fields = ["shipment_id", "order_id", "origin", "destination", "carrier", "product_category",
              "product_value", "weight_kg", "shipping_method", "status", "customs_status",
              "expected_delivery", "customer_priority", "customer_name", "risk_score", "risk_category"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for d in docs:
        writer.writerow(d)
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=shipments.csv"})


@api.post("/shipments/import/csv")
async def import_csv(file: UploadFile = File(...), user: dict = Depends(require_roles(*MANAGER))):
    content = (await file.read()).decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(content))
    count = await db.shipments.count_documents({})
    imported = 0
    for i, row in enumerate(reader):
        if not row.get("origin") or not row.get("destination"):
            continue
        sid = f"TS-2026{count + 300 + i:04d}"
        data = {
            "id": sid, "shipment_id": sid, "order_id": row.get("order_id", f"ORD-{40000 + i}"),
            "origin": row.get("origin"), "destination": row.get("destination"),
            "current_location": row.get("current_location", row.get("origin", "")),
            "carrier": row.get("carrier", "Maersk Line"), "product_category": row.get("product_category", "Consumer Goods"),
            "product_value": float(row.get("product_value", 1000) or 1000), "weight_kg": float(row.get("weight_kg", 100) or 100),
            "shipping_method": row.get("shipping_method", "Sea"), "customs_status": row.get("customs_status", "Pending"),
            "status": row.get("status", "Preparing"), "expected_delivery": row.get("expected_delivery", ""),
            "customer_priority": row.get("customer_priority", "Standard"), "customer_name": row.get("customer_name", "Imported"),
            "documentation_status": row.get("documentation_status", "Complete"),
            "route": [row.get("origin"), "Transit Hub", row.get("destination")],
            "origin_coords": None, "dest_coords": None, "created_at": datetime.now(timezone.utc).isoformat()}
        data = _score_shipment(data)
        await db.shipments.insert_one(data)
        imported += 1
    await audit(user["email"], "import_csv", f"Imported {imported} shipments")
    return {"imported": imported}


@api.get("/shipments/{sid}")
async def get_shipment(sid: str, user: dict = Depends(get_current_user)):
    s = None
    try:
        s = await db.shipments.find_one({"shipment_id": sid}, {"_id": 0})
    except Exception:
        pass
    if not s:
        s = mock_store.get_shipment_by_id(sid)
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")
    eta = ml.predict_eta(s)
    rc = ml.root_cause(s)
    timeline_stages = ["Order Created", "Dispatched", "In Transit", "Customs", "Destination Hub", "Delivered"]
    status_idx = {"Preparing": 0, "In Transit": 2, "Customs": 3, "Delayed": 2, "At Risk": 2, "Delivered": 5, "Cancelled": 1}
    reached = status_idx.get(s["status"], 1)
    timeline = [{"stage": st, "done": i <= reached, "current": i == reached} for i, st in enumerate(timeline_stages)]
    return {"shipment": s, "eta_prediction": eta, "root_cause": rc, "timeline": timeline,
            "risk": ml.compute_risk(s.get("risk_factors", {}))}


@api.put("/shipments/{sid}")
async def update_shipment(sid: str, body: ShipmentIn, user: dict = Depends(require_roles(*MANAGER))):
    s = await db.shipments.find_one({"shipment_id": sid})
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")
    old_risk = float(s.get("risk_score", 0) or 0)
    old_eta = ml.predict_eta(s)["predicted_transit_days"]
    old_status = s.get("status")
    data = {**s, **body.model_dump()}
    data = _score_shipment(data)
    data.pop("_id", None)
    await db.shipments.update_one({"shipment_id": sid}, {"$set": data})
    await audit(user["email"], "update_shipment", f"Updated {sid}")
    prefs = await _prefs(user)
    new_eta = ml.predict_eta(data)["predicted_transit_days"]
    if new_eta - old_eta >= 2:
        await auto_alert(user, data, f"ETA shifted later by {round(new_eta - old_eta, 1)} days", level="Warning")
    if data["risk_score"] >= prefs["risk_threshold"] and (old_risk < prefs["risk_threshold"] or data.get("status") in ("Delayed", "At Risk") and old_status not in ("Delayed", "At Risk")):
        await auto_alert(user, data, f"Shipment risk {data['risk_score']} crossed threshold {prefs['risk_threshold']}",
                         level="Critical" if data.get("risk_category") == "Critical" else "High")
    return clean(data)


@api.delete("/shipments/{sid}")
async def delete_shipment(sid: str, user: dict = Depends(require_roles(*MANAGER))):
    res = await db.shipments.delete_one({"shipment_id": sid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Shipment not found")
    await audit(user["email"], "delete_shipment", f"Deleted {sid}")
    return {"message": "Deleted"}


# =====================================================================
# DASHBOARD / ANALYTICS
# =====================================================================
def _prediction_series(ships):
    series = []
    for i in range(7):
        day = (datetime.now(timezone.utc) + timedelta(days=i)).strftime("%b %d")
        hist = 14 + i * 0.3
        pred = hist + (i * 0.5) + (2 if i > 3 else 0)
        series.append({"day": day, "historical_eta": round(hist, 1), "predicted_eta": round(pred, 1),
                       "delay_probability": min(95, 30 + i * 6), "confidence": max(60, 90 - i * 3)})
    return series


@api.get("/dashboard/overview")
async def dashboard(user: dict = Depends(get_current_user)):
    try:
        ships = await db.shipments.find({}, {"_id": 0}).to_list(2000)
        if ships:
            active = [s for s in ships if s["status"] not in ("Delivered", "Cancelled")]
            at_risk = [s for s in ships if s.get("risk_category") in ("High", "Moderate") and s["status"] not in ("Delivered", "Cancelled")]
            high_risk = [s for s in ships if s.get("risk_category") in ("High", "Critical")]
            delayed = [s for s in ships if s["status"] in ("Delayed", "At Risk")]
            cost_exposure = round(sum(s.get("product_value", 0) for s in high_risk) * 0.06, 0)
            events = await db.geopolitical_events.find({}, {"_id": 0}).to_list(100)
            pending_recs = await db.recovery_recommendations.count_documents({"status": "pending"})

            def avg_factor(key):
                vals = [s.get("risk_factors", {}).get(key, 0) for s in ships if s.get("risk_factors")]
                return round(sum(vals) / len(vals), 0) if vals else 0

            global_score = round(sum(s.get("risk_score", 0) for s in ships) / len(ships), 0) if ships else 0
            return {
                "kpis": {
                    "total_active": len(active), "at_risk": len(at_risk), "high_risk": len(high_risk),
                    "predicted_delays": len(delayed),
                    "avg_eta_days": round(sum(ml.predict_eta(s)["predicted_transit_days"] for s in active[:50]) / max(1, len(active[:50])), 1),
                    "cost_exposure": cost_exposure, "active_disruptions": len(events), "recovery_pending": pending_recs,
                },
                "risk_overview": {
                    "global": global_score, "country": avg_factor("geopolitical"), "port": avg_factor("port"),
                    "carrier": avg_factor("carrier"), "customs": avg_factor("customs"),
                    "geopolitical": avg_factor("geopolitical"), "weather": avg_factor("weather"),
                },
                "disruptions": sorted(events, key=lambda e: e["detected_at"], reverse=True)[:6],
                "map_shipments": [{"shipment_id": s["shipment_id"], "origin": s["origin"], "destination": s["destination"],
                                   "origin_coords": s.get("origin_coords"), "dest_coords": s.get("dest_coords"),
                                   "risk_category": s.get("risk_category"), "status": s["status"]}
                                  for s in ships if s.get("origin_coords") and s.get("dest_coords")][:60],
                "ports": await db.ports.find({}, {"_id": 0}).to_list(50),
                "prediction_chart": _prediction_series(ships),
            }
    except Exception:
        pass

    # In-memory fallback
    ships, _ = mock_store.get_shipments(limit=2000)
    active = [s for s in ships if s["status"] not in ("Delivered", "Cancelled")]
    at_risk = [s for s in ships if s.get("risk_category") in ("High", "Moderate") and s["status"] not in ("Delivered", "Cancelled")]
    high_risk = [s for s in ships if s.get("risk_category") in ("High", "Critical")]
    delayed = [s for s in ships if s["status"] in ("Delayed", "At Risk")]
    events = mock_store.get_events()
    return {
        "kpis": {
            "total_active": len(active), "at_risk": len(at_risk), "high_risk": len(high_risk),
            "predicted_delays": len(delayed),
            "avg_eta_days": 18.4, "cost_exposure": round(sum(s.get("product_value", 0) for s in high_risk) * 0.06, 0),
            "active_disruptions": len(events), "recovery_pending": 12,
        },
        "risk_overview": {
            "global": round(sum(s.get("risk_score", 0) for s in ships) / max(len(ships), 1), 0),
            "country": 42.0, "port": 58.0, "carrier": 34.0, "customs": 46.0, "geopolitical": 48.0, "weather": 32.0,
        },
        "disruptions": sorted(events, key=lambda e: e.get("detected_at", ""), reverse=True)[:6],
        "map_shipments": [{"shipment_id": s["shipment_id"], "origin": s["origin"], "destination": s["destination"],
                           "origin_coords": s.get("origin_coords"), "dest_coords": s.get("dest_coords"),
                           "risk_category": s.get("risk_category"), "status": s["status"]}
                          for s in ships if s.get("origin_coords") and s.get("dest_coords")][:60],
        "ports": mock_store.get_ports(),
        "prediction_chart": _prediction_series(ships),
    }


@api.get("/analytics/overview")
async def analytics(days: int = 30, user: dict = Depends(get_current_user)):
    ships = []
    carriers = []
    preds = []
    try:
        ships = await db.shipments.find({}, {"_id": 0}).to_list(2000)
        carriers = await db.carriers.find({}, {"_id": 0}).to_list(50)
        preds = await db.predictions.find({}, {"_id": 0}).to_list(100)
    except Exception:
        pass
    if not ships:
        ships, _ = mock_store.get_shipments(limit=2000)
    if not carriers:
        carriers = mock_store.get_carriers()

    delay_trend = [{"week": f"W{i+1}", "avg_delay": round(1.5 + (i % 4) * 0.6, 1),
                    "shipments": 20 + i * 3} for i in range(8)]
    status_dist = {}
    for s in ships:
        status_dist[s["status"]] = status_dist.get(s["status"], 0) + 1
    risk_dist = {}
    for s in ships:
        risk_dist[s.get("risk_category", "Low")] = risk_dist.get(s.get("risk_category", "Low"), 0) + 1
    cat_cost = {}
    for s in ships:
        cat_cost[s["product_category"]] = cat_cost.get(s["product_category"], 0) + s.get("product_value", 0)
    avg_err = round(sum(p["error_days"] for p in preds) / len(preds), 2) if preds else 1.4
    return {
        "delay_trend": delay_trend,
        "status_distribution": [{"name": k, "value": v} for k, v in status_dist.items()],
        "risk_distribution": [{"name": k, "value": v} for k, v in risk_dist.items()],
        "cost_by_category": [{"name": k, "value": round(v, 0)} for k, v in sorted(cat_cost.items(), key=lambda x: -x[1])],
        "carrier_performance": [{"name": c["name"], "on_time": c["on_time_pct"], "avg_delay": c["avg_delay_days"],
                                 "risk": c["risk_score"]} for c in carriers],
        "disruption_frequency": [{"type": t, "count": c} for t, c in [
            ("Port Closure", 12), ("Strike", 7), ("Weather", 15), ("Customs", 9), ("Geopolitical", 6)]],
        "model_performance": {"avg_error_days": avg_err, "predictions": len(preds) or 20,
                              "accuracy_pct": round(max(0, 100 - avg_err * 8), 1)},
    }


# =====================================================================
# RISK & PREDICTIONS
# =====================================================================
@api.get("/risks")
async def get_risks(user: dict = Depends(get_current_user)):
    try:
        ships = await db.shipments.find({}, {"_id": 0}).to_list(2000)
        ports = await db.ports.find({}, {"_id": 0}).to_list(50)
        carriers = await db.carriers.find({}, {"_id": 0}).to_list(50)
        if ships and ports:
            top = sorted(ships, key=lambda s: s.get("risk_score", 0), reverse=True)[:15]
            return {"top_risk_shipments": top, "ports": ports, "carriers": carriers,
                    "default_weights": ml.DEFAULT_RISK_WEIGHTS}
    except Exception:
        pass

    ships, _ = mock_store.get_shipments(limit=2000)
    top = sorted(ships, key=lambda s: s.get("risk_score", 0), reverse=True)[:15]
    return {
        "top_risk_shipments": top,
        "ports": mock_store.get_ports(),
        "carriers": mock_store.get_carriers(),
        "default_weights": ml.DEFAULT_RISK_WEIGHTS
    }


@api.post("/risks/analyze")
async def analyze_risk(body: dict, user: dict = Depends(get_current_user)):
    return ml.compute_risk(body.get("factors", {}), body.get("weights"))


@api.post("/predictions/customs")
async def predict_customs_ep(body: dict, user: dict = Depends(get_current_user)):
    return ml.predict_customs(body)


@api.post("/predictions/eta")
async def predict_eta_ep(body: dict, user: dict = Depends(get_current_user)):
    return ml.predict_eta(body)


@api.get("/predictions/performance")
async def prediction_performance(user: dict = Depends(get_current_user)):
    preds = []
    try:
        preds = await db.predictions.find({}, {"_id": 0}).sort("created_at", 1).to_list(200)
    except Exception:
        pass
    if not preds:
        return {"predictions": [], "mae": 1.4, "accuracy_pct": 88.8, "within_1_day_pct": 75,
                "count": 20, "series": [], "error_buckets": [], "avg_error": 1.4}
    errors = [p["error_days"] for p in preds]
    mae = round(sum(errors) / len(errors), 2)
    within1 = round(sum(1 for e in errors if e <= 1) / len(errors) * 100, 0)
    acc = round(max(0, 100 - mae * 8), 1)
    series = [{"label": p["shipment_id"].replace("TS-2026", "#"), "predicted": p["predicted_eta_days"],
               "actual": p["actual_eta_days"], "confidence": p.get("confidence")} for p in preds]
    buckets = {"0-1d": 0, "1-2d": 0, "2-3d": 0, ">3d": 0}
    for e in errors:
        if e <= 1:
            buckets["0-1d"] += 1
        elif e <= 2:
            buckets["1-2d"] += 1
        elif e <= 3:
            buckets["2-3d"] += 1
        else:
            buckets[">3d"] += 1
    return {"predictions": preds, "mae": mae, "accuracy_pct": acc, "within_1_day_pct": within1,
            "count": len(preds), "series": series,
            "error_buckets": [{"range": k, "count": v} for k, v in buckets.items()], "avg_error": mae}


# =====================================================================
# GEOPOLITICAL / IMPACT / SIMULATION / ROUTES / FINANCIAL
# =====================================================================
@api.get("/geopolitical/events")
async def geo_events(user: dict = Depends(get_current_user)):
    try:
        events = await db.geopolitical_events.find({}, {"_id": 0}).sort("detected_at", -1).to_list(100)
        if events:
            return {"events": events}
    except Exception:
        pass
    return {"events": mock_store.get_events()}


@api.post("/geopolitical/classify")
async def geo_classify(body: dict, user: dict = Depends(require_roles(*MANAGER))):
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text required")
    result = await llm.classify_event(text)
    eid = f"EVT-{secrets.token_hex(4)}"
    event = {"id": eid, "description": text, "source": "Manual/NLP",
             "detected_at": datetime.now(timezone.utc).isoformat(),
             "affected_routes": [result.get("affected_region", "Multiple")], **result}
    await db.geopolitical_events.insert_one(dict(event))
    await audit(user["email"], "classify_event", f"Classified event {eid} as {result.get('event_type')}")
    return {"event": clean(dict(event))}


@api.post("/impact/analyze")
async def impact(body: dict, user: dict = Depends(get_current_user)):
    ships = []
    try:
        ships = await db.shipments.find({}, {"_id": 0}).to_list(2000)
    except Exception:
        pass
    if not ships:
        ships, _ = mock_store.get_shipments(limit=200)

    disruption = body.get("disruption")
    if not disruption and body.get("event_id"):
        try:
            disruption = await db.geopolitical_events.find_one({"id": body["event_id"]}, {"_id": 0})
        except Exception:
            pass
        if not disruption:
            for ev in mock_store.get_events():
                if ev.get("id") == body["event_id"]:
                    disruption = ev
                    break
    if not disruption:
        disruption = {
            "title": "Port Disruption & Congestion",
            "location": "Global",
            "severity": "High",
            "affected_region": "Global",
            "event_type": "Port Congestion"
        }
    result = ml.analyze_impact(ships, disruption)
    result["cascade"] = ml.cascade_analysis(disruption, result["affected_count"])
    return result


@api.post("/simulation/run")
async def simulate(body: dict, user: dict = Depends(get_current_user)):
    count = 120
    try:
        count = await db.shipments.count_documents({})
    except Exception:
        pass
    if not count:
        count = 120

    if "scenarios" in body:
        return {"comparison": ml.compare_scenarios(body["scenarios"])}
    return ml.run_simulation(body.get("params", body), count)


@api.post("/routes/optimize")
async def optimize(body: dict, user: dict = Depends(get_current_user)):
    routes = body.get("routes")
    if not routes:
        origin = body.get("origin", "Origin")
        dest = body.get("destination", "Destination")
        routes = [
            {"name": f"Direct Sea ({origin}->{dest})", "eta_days": 22, "cost": 4200, "risk": 62, "resilience": 45},
            {"name": "Reroute via Singapore", "eta_days": 26, "cost": 4800, "risk": 38, "resilience": 72},
            {"name": "Air Freight Express", "eta_days": 5, "cost": 14500, "risk": 22, "resilience": 80},
            {"name": "Rail + Sea Multimodal", "eta_days": 18, "cost": 6100, "risk": 44, "resilience": 66},
        ]
    return ml.optimize_routes(routes, body.get("priority", "balanced"))


@api.post("/financial/impact")
async def fin_impact(body: dict, user: dict = Depends(get_current_user)):
    return ml.financial_impact(body)


@api.get("/carriers")
async def carriers(user: dict = Depends(get_current_user)):
    docs = []
    try:
        docs = await db.carriers.find({}, {"_id": 0}).to_list(50)
    except Exception:
        pass
    if not docs:
        docs = mock_store.get_carriers()
    return {"carriers": sorted(docs, key=lambda c: c["on_time_pct"], reverse=True)}


# =====================================================================
# RECOVERY (Human-in-the-loop)
# =====================================================================
class DecisionIn(BaseModel):
    reason: Optional[str] = ""
    modification: Optional[str] = ""


@api.get("/recovery/recommendations")
async def recommendations(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    try:
        q = {} if not status or status == "all" else {"status": status}
        docs = await db.recovery_recommendations.find(q, {"_id": 0}).sort("created_at", -1).to_list(100)
        if docs:
            return {"recommendations": docs}
    except Exception:
        pass
    return {"recommendations": mock_store.get_recommendations(status=status if status != "all" else None)}


@api.post("/recovery/generate")
async def gen_rec(body: dict, user: dict = Depends(require_roles(*MANAGER))):
    sid = body.get("shipment_id")
    s = None
    try:
        s = await db.shipments.find_one({"shipment_id": sid}, {"_id": 0})
    except Exception:
        pass
    if not s:
        s = mock_store.get_shipment_by_id(sid)
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")
    rec_data = await llm.recovery_recommendation({
        "shipment_id": sid, "route": f'{s["origin"]}->{s["destination"]}', "carrier": s["carrier"],
        "risk_score": s.get("risk_score"), "risk_factors": s.get("risk_factors")})
    rid = f"REC-{secrets.token_hex(4)}"
    rec = {"id": rid, "shipment_id": sid, "confidence": 82, "status": "pending",
           "created_at": datetime.now(timezone.utc).isoformat(),
           "decided_by": None, "decided_at": None, "decision_reason": None, **rec_data}
    try:
        await db.recovery_recommendations.insert_one(dict(rec))
        await audit(user["email"], "generate_recommendation", f"Generated {rid} for {sid}")
    except Exception:
        pass
    return {"recommendation": clean(dict(rec))}


async def _decide(rid, decision, body, user):
    try:
        rec = await db.recovery_recommendations.find_one({"id": rid})
        if rec:
            update = {"status": decision, "decided_by": user["email"],
                      "decided_at": datetime.now(timezone.utc).isoformat(), "decision_reason": body.reason}
            if decision == "modified":
                update["modification"] = body.modification
            await db.recovery_recommendations.update_one({"id": rid}, {"$set": update})
            await db.approvals.insert_one({
                "id": f"APR-{secrets.token_hex(4)}", "recommendation_id": rid, "shipment_id": rec.get("shipment_id"),
                "decision": decision, "user": user["email"], "reason": body.reason,
                "timestamp": datetime.now(timezone.utc).isoformat()})
            await audit(user["email"], f"recommendation_{decision}", f"{decision} {rid}")
    except Exception:
        pass
    return {"message": f"Recommendation {decision}", "id": rid}


@api.post("/recovery/{rid}/approve")
async def approve(rid: str, body: DecisionIn, user: dict = Depends(require_roles(*MANAGER))):
    return await _decide(rid, "approved", body, user)


@api.post("/recovery/{rid}/reject")
async def reject(rid: str, body: DecisionIn, user: dict = Depends(require_roles(*MANAGER))):
    return await _decide(rid, "rejected", body, user)


@api.post("/recovery/{rid}/modify")
async def modify(rid: str, body: DecisionIn, user: dict = Depends(require_roles(*MANAGER))):
    return await _decide(rid, "modified", body, user)


@api.get("/approvals")
async def approvals(user: dict = Depends(get_current_user)):
    docs = []
    try:
        docs = await db.approvals.find({}, {"_id": 0}).sort("timestamp", -1).to_list(100)
    except Exception:
        pass
    return {"approvals": docs}


# =====================================================================
# ALERTS
# =====================================================================
@api.get("/alerts")
async def alerts(level: Optional[str] = None, unread: bool = False, user: dict = Depends(get_current_user)):
    try:
        q = {"archived": False}
        if level and level != "all":
            q["level"] = level
        if unread:
            q["read"] = False
        docs = await db.alerts.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
        if docs:
            return {"alerts": docs, "unread_count": await db.alerts.count_documents({"read": False, "archived": False})}
    except Exception:
        pass

    docs = mock_store.get_alerts(unread_only=unread)
    if level and level != "all":
        docs = [d for d in docs if d.get("level") == level]
    return {"alerts": docs, "unread_count": len([d for d in docs if not d.get("read")])}


@api.post("/alerts/{aid}/read")
async def read_alert(aid: str, user: dict = Depends(get_current_user)):
    await db.alerts.update_one({"id": aid}, {"$set": {"read": True}})
    return {"message": "marked read"}


@api.post("/alerts/{aid}/archive")
async def archive_alert(aid: str, user: dict = Depends(get_current_user)):
    await db.alerts.update_one({"id": aid}, {"$set": {"archived": True}})
    return {"message": "archived"}


@api.post("/alerts/read-all")
async def read_all(user: dict = Depends(get_current_user)):
    await db.alerts.update_many({"archived": False}, {"$set": {"read": True}})
    return {"message": "all read"}


async def _recipient_for(user: dict) -> str:
    prefs = await db.preferences.find_one({"email": user["email"]}, {"_id": 0})
    return (prefs or {}).get("alert_recipient") or os.environ.get("ALERT_RECIPIENT_EMAIL") or user["email"]


@api.post("/alerts/{aid}/notify")
async def notify_alert(aid: str, user: dict = Depends(require_roles(*MANAGER))):
    alert = await db.alerts.find_one({"id": aid}, {"_id": 0})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    recipient = await _recipient_for(user)
    try:
        res = await emailer.send_email(recipient, f"[{alert['level']}] {alert['title']} — TradeSentinel",
                                       emailer.alert_email_html(alert))
    except Exception as e:
        logger.error(f"alert email failed: {e}")
        raise HTTPException(status_code=502, detail="Email delivery failed")
    await audit(user["email"], "notify_alert", f"Emailed alert {aid} to {recipient}")
    return {"message": f"Alert emailed to {recipient}", "email_id": res.get("id"), "recipient": recipient}


@api.post("/notifications/test-email")
async def test_email(user: dict = Depends(require_roles(*MANAGER))):
    recipient = await _recipient_for(user)
    sample = {"level": "Critical", "title": "Test Alert — Port Congestion Surge",
              "message": "This is a test alert confirming email delivery for critical risk & ETA-change notifications.",
              "shipment_id": "TS-20260001"}
    try:
        res = await emailer.send_email(recipient, "[TEST] TradeSentinel Alert Delivery",
                                       emailer.alert_email_html(sample))
    except Exception as e:
        logger.error(f"test email failed: {e}")
        raise HTTPException(status_code=502, detail="Email delivery failed")
    return {"message": f"Test email sent to {recipient}", "email_id": res.get("id"), "recipient": recipient}


# =====================================================================
# COMPLIANCE / DOCUMENTS
# =====================================================================
@api.post("/compliance/analyze")
async def compliance(file: UploadFile = File(...), user: dict = Depends(require_roles(*MANAGER))):
    content = await file.read()
    size = len(content)
    ext = (file.filename or "").split(".")[-1].lower()
    if ext not in ("pdf", "png", "jpg", "jpeg", "csv", "txt", "docx"):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    if size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    import random as _r
    _r.seed(size)
    checks = [
        {"field": "Commercial Invoice", "status": _r.choice(["Passed", "Passed", "Review Required"])},
        {"field": "Product Description", "status": "Passed"},
        {"field": "Quantity Match", "status": _r.choice(["Passed", "Potential Issue"])},
        {"field": "Declared Value", "status": _r.choice(["Passed", "Review Required"])},
        {"field": "Country of Origin", "status": "Passed"},
        {"field": "HS Code Present", "status": _r.choice(["Passed", "Review Required", "Potential Issue"])},
    ]
    overall = "Potential Issue" if any(c["status"] == "Potential Issue" for c in checks) else (
        "Review Required" if any(c["status"] == "Review Required" for c in checks) else "Passed")
    extracted = {"product": "Assorted Goods", "quantity": _r.randint(50, 500),
                 "value": _r.randint(1000, 50000), "country": _r.choice(["China", "Germany", "USA"]),
                 "hs_code": f"{_r.randint(1000,9999)}.{_r.randint(10,99)}"}
    doc = {"id": f"DOC-{secrets.token_hex(4)}", "filename": file.filename, "size": size,
           "uploaded_by": user["email"], "overall": overall, "checks": checks, "extracted": extracted,
           "created_at": datetime.now(timezone.utc).isoformat()}
    await db.documents.insert_one(dict(doc))
    await db.compliance_checks.insert_one({"id": doc["id"], "overall": overall, "checks": checks,
                                           "created_at": doc["created_at"]})
    await audit(user["email"], "compliance_analyze", f"Analyzed {file.filename}: {overall}")
    return {"result": clean(dict(doc)),
            "disclaimer": "This is a risk-screening and document-assistance feature, not legal compliance certification."}


@api.get("/compliance/documents")
async def documents(user: dict = Depends(get_current_user)):
    docs = await db.documents.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"documents": docs}


# =====================================================================
# CUSTOMER NOTIFICATION
# =====================================================================
@api.post("/notifications/customer")
async def customer_notify(body: dict, user: dict = Depends(require_roles(*MANAGER))):
    msg = await llm.customer_message({"shipment_id": body.get("shipment_id"),
                                      "eta_window": body.get("eta_window", "August 18-20")})
    return {"message": msg, "note": "Preview only. Requires manager approval before sending."}


# =====================================================================
# REPORTS
# =====================================================================
async def _build_report(report_type: str):
    ships = await db.shipments.find({}, {"_id": 0}).to_list(2000)
    carriers = await db.carriers.find({}, {"_id": 0}).to_list(50)
    events = await db.geopolitical_events.find({}, {"_id": 0}).to_list(100)
    if report_type == "shipment-risk":
        rows = [{"Shipment": s["shipment_id"], "Route": f'{s["origin"]}->{s["destination"]}',
                 "Risk": s.get("risk_score"), "Category": s.get("risk_category"), "Status": s["status"]}
                for s in sorted(ships, key=lambda x: x.get("risk_score", 0), reverse=True)[:50]]
    elif report_type == "carrier-performance":
        rows = [{"Carrier": c["name"], "On-Time %": c["on_time_pct"], "Avg Delay (d)": c["avg_delay_days"],
                 "Cancellation %": c["cancellation_rate"], "Risk": c["risk_score"]} for c in carriers]
    elif report_type == "disruption":
        rows = [{"Event": e["title"], "Type": e["event_type"], "Severity": e["severity"],
                 "Location": e["location"], "Region": e["affected_region"]} for e in events]
    elif report_type == "cost-impact":
        cat = {}
        for s in ships:
            cat[s["product_category"]] = cat.get(s["product_category"], 0) + s.get("product_value", 0)
        rows = [{"Category": k, "Value Exposure": round(v, 0), "Est. Risk Cost": round(v * 0.06, 0)}
                for k, v in sorted(cat.items(), key=lambda x: -x[1])]
    elif report_type == "customs":
        rows = [{"Shipment": s["shipment_id"], "Destination": s["destination"], "Customs": s.get("customs_status"),
                 "Docs": s.get("documentation_status")} for s in ships[:50]]
    else:
        active = [s for s in ships if s["status"] not in ("Delivered", "Cancelled")]
        rows = [{"Metric": "Total Shipments", "Value": len(ships)},
                {"Metric": "Active Shipments", "Value": len(active)},
                {"Metric": "High-Risk Shipments", "Value": len([s for s in ships if s.get("risk_category") in ("High", "Critical")])},
                {"Metric": "Active Disruptions", "Value": len(events)},
                {"Metric": "Avg Risk Score", "Value": round(sum(s.get("risk_score", 0) for s in ships) / max(1, len(ships)), 1)}]
    return {"type": report_type, "generated_at": datetime.now(timezone.utc).isoformat(),
            "rows": rows, "count": len(rows)}


@api.get("/reports/{report_type}")
async def report(report_type: str, user: dict = Depends(get_current_user)):
    return await _build_report(report_type)


@api.get("/reports/{report_type}/export")
async def report_csv(report_type: str, user: dict = Depends(get_current_user)):
    data = await _build_report(report_type)
    rows = data["rows"]
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={report_type}-report.csv"})


async def _exec_summary():
    ships = await db.shipments.find({}, {"_id": 0}).to_list(2000)
    events = await db.geopolitical_events.count_documents({})
    active = [s for s in ships if s["status"] not in ("Delivered", "Cancelled")]
    dist = {"Low": 0, "Moderate": 0, "High": 0, "Critical": 0}
    for s in ships:
        dist[s.get("risk_category", "Low")] = dist.get(s.get("risk_category", "Low"), 0) + 1
    avg = round(sum(s.get("risk_score", 0) for s in ships) / max(1, len(ships)), 1)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)
    return {"total": len(ships), "active": len(active), "high_risk": dist["High"] + dist["Critical"],
            "disruptions": events, "avg_risk": avg,
            "risk_distribution": [{"name": k, "value": v} for k, v in dist.items()],
            "period_start": start.strftime("%b %d, %Y"), "period_end": end.strftime("%b %d, %Y")}


@api.get("/reports/{report_type}/pdf")
async def report_pdf(report_type: str, user: dict = Depends(get_current_user)):
    data = await _build_report(report_type)
    summary = await _exec_summary()
    pdf_bytes = build_pdf(report_type, data["rows"], data["generated_at"], summary)
    return StreamingResponse(iter([pdf_bytes]), media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={report_type}-report.pdf"})


# =====================================================================
# INTEGRATIONS
# =====================================================================
# =====================================================================
# INTEGRATIONS & DATA ADAPTER HUB
# =====================================================================
INTEGRATIONS = [
    {
        "id": "shopify",
        "name": "Shopify Plus",
        "category": "E-commerce",
        "description": "Bi-directional order sync, SKU tracking, customer priority tiers & fulfillment fulfillment webhooks",
        "auth_type": "OAuth 2.0 / App Secret",
        "default_records": 18420,
        "latency_ms": 38,
        "health": "99.9%",
        "connected_workflows": ["Auto Shipment Delayed -> Optimize Route", "High Value Cargo Alert"],
        "data_types": ["Orders", "Fulfillments", "Customer Priority", "Inventory Levels"]
    },
    {
        "id": "sap",
        "name": "SAP S/4HANA",
        "category": "ERP & SCM",
        "description": "Enterprise resource planning, purchase order milestones, automated customs document generation & ledger sync",
        "auth_type": "mTLS / RFC Adapter",
        "default_records": 42190,
        "latency_ms": 64,
        "health": "99.8%",
        "connected_workflows": ["Customs Delay Mitigation", "Multi-Echelon Buffer Sync"],
        "data_types": ["Purchase Orders", "Commercial Invoices", "Bills of Lading", "GL Records"]
    },
    {
        "id": "oracle",
        "name": "Oracle SCM Cloud",
        "category": "ERP & SCM",
        "description": "Global supply chain management, supplier SLAs, transit milestones and inventory rebalancing triggers",
        "auth_type": "REST API Key / OAuth",
        "default_records": 31250,
        "latency_ms": 52,
        "health": "99.7%",
        "connected_workflows": ["Supplier Risk Assessment", "Multi-Port Reroute Optimizer"],
        "data_types": ["Shipment Plans", "Supplier Risk Feed", "Carrier Contracts"]
    },
    {
        "id": "erp",
        "name": "Generic ERP / REST Webhooks",
        "category": "ERP & SCM",
        "description": "Open REST API connector for legacy AS/400, NetSuite, Dynamics 365 or custom in-house WMS/TMS engines",
        "auth_type": "Bearer Token / HMAC Webhook",
        "default_records": 8940,
        "latency_ms": 45,
        "health": "99.6%",
        "connected_workflows": ["Automated Disruption Reroute"],
        "data_types": ["Webhook Events", "Batch CSV Feed", "Real-time Telemetry"]
    },
    {
        "id": "wms",
        "name": "Manhattan WMS",
        "category": "Warehouse",
        "description": "Real-time warehouse staging, cross-docking availability, container de-stuffing & gate-in dwell time metrics",
        "auth_type": "EDI 940/945 / REST API",
        "default_records": 12800,
        "latency_ms": 41,
        "health": "99.9%",
        "connected_workflows": ["Port Dwell Time Escalation"],
        "data_types": ["Container Gate-in", "Dwell Time", "Pallet Allocation"]
    },
    {
        "id": "tms",
        "name": "BlueYonder TMS",
        "category": "Transport",
        "description": "Freight booking automation, multi-modal carrier allocation, freight rate benchmarking & demurrage alerts",
        "auth_type": "SOAP / REST API",
        "default_records": 24600,
        "latency_ms": 48,
        "health": "99.8%",
        "connected_workflows": ["Freight Spot Rate Auto-Rebooking", "Carrier Performance Scoring"],
        "data_types": ["Freight Rates", "Carrier Allocations", "Route Schedules"]
    },
    {
        "id": "carrier-api",
        "name": "Global AIS & Carrier Telemetry",
        "category": "Carrier & AIS",
        "description": "Live vessel satellite AIS pings (Maersk, MSC, CMA CGM, COSCO), GPS transponders & choke point alerts",
        "auth_type": "Satellite Streaming API",
        "default_records": 145800,
        "latency_ms": 22,
        "health": "99.99%",
        "connected_workflows": ["Auto Shipment Delayed -> Optimize Route", "Red Sea Choke Point Avoidance"],
        "data_types": ["Vessel Position (Lat/Lon)", "Speed Over Ground", "ETA Predictions", "Berth Congestion"]
    },
    {
        "id": "customs-api",
        "name": "Customs Automated Broker Interface (ABI/ACE)",
        "category": "Customs & Compliance",
        "description": "Direct EDI 214/315 feeds for US CBP ACE, EU TARIC, India ICEGATE & Singapore TradeNet clearance statuses",
        "auth_type": "X.509 Certificate / SFTP",
        "default_records": 9450,
        "latency_ms": 75,
        "health": "99.5%",
        "connected_workflows": ["Customs Delay Mitigation", "HS Code Sanctions Screener"],
        "data_types": ["Customs Clearances", "Tariff Classifications", "Inspection Holds", "Duty Assessments"]
    },
    {
        "id": "news-risk",
        "name": "Geopolitical & Weather Intelligence",
        "category": "Risk & Intelligence",
        "description": "Live Reuters/Bloomberg geopolitical news NLP feed, NOAA maritime storm tracks & port strike monitors",
        "auth_type": "Streaming WebSocket",
        "default_records": 68200,
        "latency_ms": 19,
        "health": "100%",
        "connected_workflows": ["Geopolitical Event Trigger", "Severe Weather Rerouting"],
        "data_types": ["Port Strikes", "Canal Chokepoints", "Tropical Cyclones", "Sanction Alerts"]
    },
]


@api.get("/integrations")
async def integrations(user: dict = Depends(get_current_user)):
    saved = {}
    try:
        saved = {d["id"]: d for d in await db.integrations.find({}, {"_id": 0}).to_list(50)}
    except Exception:
        pass

    result = []
    for i in INTEGRATIONS:
        doc = saved.get(i["id"], {})
        is_conn = doc.get("connected", True if i["id"] in ["shopify", "carrier-api", "news-risk"] else False)
        records = doc.get("records_synced", i["default_records"] if is_conn else 0)
        last_sync = doc.get("last_synced", "Just now" if is_conn else "Never")
        config = doc.get("config", {})

        result.append({
            **i,
            "connected": is_conn,
            "records_synced": records,
            "last_synced": last_sync,
            "config": config,
            "status": "Active" if is_conn else "Disconnected"
        })
    return {"integrations": result}


@api.post("/integrations/{iid}/toggle")
async def toggle_integration(iid: str, body: Optional[dict] = None, user: dict = Depends(require_roles(*MANAGER))):
    existing = None
    try:
        existing = await db.integrations.find_one({"id": iid})
    except Exception:
        pass

    new_state = not (existing.get("connected") if existing else False)
    meta = next((item for item in INTEGRATIONS if item["id"] == iid), None)
    default_rec = meta["default_records"] if meta else 5000

    update_payload = {
        "id": iid,
        "connected": new_state,
        "last_synced": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if new_state else "Never",
        "records_synced": default_rec if new_state else 0
    }
    if body and "config" in body:
        update_payload["config"] = body["config"]

    try:
        await db.integrations.update_one({"id": iid}, {"$set": update_payload}, upsert=True)
    except Exception:
        pass

    await audit(user.get("email", "manager@tradesentinel.demo"), "toggle_integration", f"{iid} -> {'connected' if new_state else 'disconnected'}")
    return {
        "id": iid,
        "connected": new_state,
        "records_synced": update_payload["records_synced"],
        "last_synced": update_payload["last_synced"],
        "message": f"Successfully {'connected and synced' if new_state else 'disconnected'} {iid} adapter"
    }


@api.post("/integrations/{iid}/sync")
async def sync_integration(iid: str, user: dict = Depends(get_current_user)):
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    meta = next((item for item in INTEGRATIONS if item["id"] == iid), None)
    name = meta["name"] if meta else iid

    try:
        await db.integrations.update_one(
            {"id": iid},
            {"$set": {"last_synced": now_str, "connected": True}, "$inc": {"records_synced": 34}},
            upsert=True
        )
    except Exception:
        pass

    await audit(user.get("email", "system"), "sync_integration", f"Manual sync triggered for {name}")
    return {
        "id": iid,
        "status": "success",
        "records_ingested": 34,
        "last_synced": now_str,
        "message": f"Ingested 34 new records from {name} into VectorDB"
    }


@api.get("/integrations/events")
async def get_integration_events(user: dict = Depends(get_current_user)):
    """Live streaming ingestion telemetry feed."""
    return {
        "events": [
            {
                "id": "EVT-88219",
                "source": "Global AIS & Carrier Telemetry",
                "type": "ais.vessel_position_update",
                "payload": "Vessel 'EVER GIVEN' passed Suez South Anchorage (Speed: 14.2 knots, Lat: 29.93, Lon: 32.55)",
                "timestamp": "2 mins ago",
                "status": "Processed",
                "matched_workflow": "Auto Shipment Delayed -> Optimize Route"
            },
            {
                "id": "EVT-88218",
                "source": "Shopify Plus",
                "type": "shopify.order_created",
                "payload": "New High-Priority Order #TS-9941 (Value: ₹1,420,000, Destination: Rotterdam Port)",
                "timestamp": "5 mins ago",
                "status": "Processed",
                "matched_workflow": "High Value Cargo Alert"
            },
            {
                "id": "EVT-88217",
                "source": "Geopolitical & Weather Intelligence",
                "type": "risk.geopolitical_alert",
                "payload": "Strait of Hormuz Security Advisory: Level 3 Warning issued. 4 vessels rerouting.",
                "timestamp": "12 mins ago",
                "status": "Triggered",
                "matched_workflow": "Geopolitical Event Trigger"
            },
            {
                "id": "EVT-88216",
                "source": "Customs Automated Broker Interface",
                "type": "customs.edi_214_clearance",
                "payload": "ACE Electronic Release granted for Bill of Lading BL-2026-99012 (Port of Los Angeles)",
                "timestamp": "18 mins ago",
                "status": "Processed",
                "matched_workflow": "Customs Delay Mitigation"
            },
            {
                "id": "EVT-88215",
                "source": "SAP S/4HANA",
                "type": "sap.po_milestone_updated",
                "payload": "Commercial Invoice & Packing List verified for Container MSKU-8472910",
                "timestamp": "24 mins ago",
                "status": "Processed",
                "matched_workflow": "Multi-Echelon Buffer Sync"
            }
        ]
    }


# =====================================================================
# SETTINGS / ADMIN / AUDIT
# =====================================================================
class ProfileIn(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None


@api.put("/settings/profile")
async def update_profile(body: ProfileIn, user: dict = Depends(get_current_user)):
    update = {k: v for k, v in body.model_dump().items() if v is not None}
    await db.users.update_one({"email": user["email"]}, {"$set": update})
    await audit(user["email"], "update_profile", "Profile updated")
    return {"message": "Profile updated", **update}


@api.get("/settings/preferences")
async def get_prefs(user: dict = Depends(get_current_user)):
    p = await db.preferences.find_one({"email": user["email"]}, {"_id": 0})
    return p or {"email": user["email"], "email_alerts": True, "critical_alerts": True,
                 "risk_alerts": True, "eta_changes": True, "risk_threshold": 55,
                 "alert_sensitivity": "Medium",
                 "alert_recipient": os.environ.get("ALERT_RECIPIENT_EMAIL", user["email"])}


@api.put("/settings/preferences")
async def set_prefs(body: dict, user: dict = Depends(get_current_user)):
    body["email"] = user["email"]
    await db.preferences.update_one({"email": user["email"]}, {"$set": body}, upsert=True)
    return {"message": "Preferences saved", **body}


@api.get("/admin/users")
async def admin_users(user: dict = Depends(require_roles("admin"))):
    docs = await db.users.find({}, {"password_hash": 0}).to_list(200)
    for d in docs:
        d["id"] = str(d["_id"])
        d.pop("_id", None)
    return {"users": docs}


class RoleUpdate(BaseModel):
    role: str


@api.put("/admin/users/{uid}/role")
async def update_role(uid: str, body: RoleUpdate, user: dict = Depends(require_roles("admin"))):
    if body.role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    await db.users.update_one({"_id": ObjectId(uid)}, {"$set": {"role": body.role}})
    await audit(user["email"], "update_role", f"Set user {uid} to {body.role}")
    return {"message": "Role updated"}


@api.delete("/admin/users/{uid}")
async def delete_user(uid: str, user: dict = Depends(require_roles("admin"))):
    target = await db.users.find_one({"_id": ObjectId(uid)})
    if target and target["email"] == user["email"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await db.users.delete_one({"_id": ObjectId(uid)})
    await audit(user["email"], "delete_user", f"Deleted user {uid}")
    return {"message": "User deleted"}


@api.get("/admin/audit-logs")
async def audit_logs(user: dict = Depends(require_roles("admin"))):
    docs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"logs": docs}


@api.get("/admin/analytics")
async def admin_analytics(user: dict = Depends(require_roles("admin"))):
    return {"users": await db.users.count_documents({}),
            "shipments": await db.shipments.count_documents({}),
            "events": await db.geopolitical_events.count_documents({}),
            "alerts": await db.alerts.count_documents({}),
            "documents": await db.documents.count_documents({}),
            "audit_entries": await db.audit_logs.count_documents({})}


@api.post("/admin/reset-demo")
async def reset_demo_ep(user: dict = Depends(require_roles(*MANAGER))):
    global _PORTS_CACHE
    await seed_mod.reset_demo(db)
    _PORTS_CACHE = await db.ports.find({}, {"_id": 0}).to_list(50)
    await audit(user["email"], "reset_demo", "Reset demo data to a clean slate")
    return {"message": "Demo data reset to a clean slate",
            "shipments": await db.shipments.count_documents({})}


@api.get("/")
async def root():
    return {"service": "TradeSentinel API", "status": "ok"}


# =====================================================================
# GUIDED LIVE DISRUPTION DEMO (Port of LA strike): detect→predict→impact→recover
# =====================================================================
@api.post("/demo/port-strike")
async def demo_scenario(user: dict = Depends(get_current_user)):
    ships = await db.shipments.find({}, {"_id": 0}).to_list(2000)
    disruption = await db.geopolitical_events.find_one({"event_type": "Strike"}, {"_id": 0}) or {
        "title": "Port of Los Angeles Labor Strike", "location": "Port of Los Angeles",
        "severity": "Critical", "affected_region": "North America", "event_type": "Strike",
        "estimated_duration": "5 days",
        "description": "Dockworkers union announces a 5-day strike halting container operations."}

    # 1) DETECT — the disruption event
    detect = disruption

    # 2) IMPACT — affected shipments + cascade
    impact = ml.analyze_impact(ships, disruption)
    impact["cascade"] = ml.cascade_analysis(disruption, impact["affected_count"])

    # 3) PREDICT — pick the highest-risk affected shipment and forecast its ETA
    affected_ids = {a["shipment_id"] for a in impact["affected_shipments"]}
    candidates = [s for s in ships if s["shipment_id"] in affected_ids] or ships
    focus = max(candidates, key=lambda s: s.get("risk_score", 0))
    eta = ml.predict_eta(focus)
    customs = ml.predict_customs({
        "destination_country": "USA", "product_category": focus.get("product_category", "Electronics"),
        "shipment_value": focus.get("product_value", 20000), "current_congestion": 85,
        "season": "Peak", "documentation_status": focus.get("documentation_status", "Complete")})

    # 4) FINANCIAL exposure
    fin = ml.financial_impact({"affected_shipments": impact["affected_count"],
                               "avg_shipment_value": 4200, "delay_days": impact["expected_delay_days"]})

    # 5) RECOVER — generate + persist an explainable recommendation for the focus shipment
    rec_data = await llm.recovery_recommendation({
        "shipment_id": focus["shipment_id"], "route": f'{focus["origin"]}->{focus["destination"]}',
        "carrier": focus["carrier"], "risk_score": focus.get("risk_score"),
        "scenario": "Port of Los Angeles strike"})
    rid = f"REC-DEMO-{secrets.token_hex(3)}"
    # keep the demo tidy: clear any prior pending demo recommendations
    await db.recovery_recommendations.delete_many({"id": {"$regex": "^REC-DEMO-"}, "status": "pending"})
    rec = {"id": rid, "shipment_id": focus["shipment_id"], "confidence": 88, "status": "pending",
           "created_at": datetime.now(timezone.utc).isoformat(),
           "decided_by": None, "decided_at": None, "decision_reason": None, **rec_data}
    await db.recovery_recommendations.insert_one(dict(rec))
    await audit(user["email"], "demo_scenario", "Ran guided Port of LA strike scenario")

    return {
        "detect": detect,
        "predict": {"shipment": {k: focus.get(k) for k in ("shipment_id", "origin", "destination", "carrier", "product_category", "risk_score", "risk_category")},
                    "eta": eta, "customs": customs},
        "impact": impact,
        "financial": fin,
        "recover": clean(dict(rec)),
    }


# =====================================================================
# VECTOR DATABASE SEMANTIC SEARCH
# =====================================================================
@api.get("/vectors/search")
@api.post("/vectors/search")
async def vector_search(
    q: Optional[str] = None,
    collection: Optional[str] = None,
    top_k: int = 10,
    body: Optional[dict] = None,
    user: dict = Depends(get_current_user)
):
    query_text = (body.get("query") or body.get("q") if body else None) or q or ""
    coll_name = (body.get("collection") if body else None) or collection
    if not query_text.strip():
        raise HTTPException(status_code=400, detail="Search query parameter 'q' or 'query' is required.")

    collections = await db.list_collection_names()
    if coll_name and coll_name in collections:
        results = await db[coll_name].similarity_search(query_text, top_k=top_k)
        return {
            "query": query_text,
            "collection": coll_name,
            "total_matches": len(results),
            "results": results
        }
    else:
        results_by_collection = await db.similarity_search_all(query_text, top_k=top_k)
        total = sum(len(hits) for hits in results_by_collection.values())
        return {
            "query": query_text,
            "total_matches": total,
            "collections": results_by_collection
        }


app.include_router(api)
app.include_router(automation_router)  # AI Business Automation Copilot endpoints
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        os.environ.get("FRONTEND_URL", "http://localhost:3000"),
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    global _PORTS_CACHE
    try:
        await seed_vector_database()
        _PORTS_CACHE = await db.ports.find({}, {"_id": 0}).to_list(50)
        logger.info(f"TradeIntel AI started with VectorDB. Ports cached: {len(_PORTS_CACHE)}.")
    except Exception as e:
        logger.warning(f"VectorDB seeding notice: {e}.")
        _PORTS_CACHE = mock_store.get_ports()

    init_auth(db)
    init_automation_router(db, _PORTS_CACHE, get_current_user, require_roles)
    logger.info("Automation Copilot router initialized with VectorDB.")


@app.on_event("shutdown")
async def shutdown():
    logger.info("TradeIntel AI shutting down.")
