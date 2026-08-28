"""Demo data seeding: users, orgs, ports, carriers, 120+ shipments, events, alerts."""
import random
from datetime import datetime, timezone, timedelta
import ml
from auth import hash_password

random.seed(42)

PORTS = [
    {"name": "Port of Shanghai", "country": "China", "code": "CNSHA", "lat": 31.23, "lng": 121.47, "congestion": 72},
    {"name": "Port of Singapore", "country": "Singapore", "code": "SGSIN", "lat": 1.29, "lng": 103.85, "congestion": 48},
    {"name": "Port of Rotterdam", "country": "Netherlands", "code": "NLRTM", "lat": 51.95, "lng": 4.14, "congestion": 55},
    {"name": "Port of Los Angeles", "country": "USA", "code": "USLAX", "lat": 33.74, "lng": -118.27, "congestion": 81},
    {"name": "Port of Hamburg", "country": "Germany", "code": "DEHAM", "lat": 53.54, "lng": 9.98, "congestion": 44},
    {"name": "Jebel Ali Port", "country": "UAE", "code": "AEJEA", "lat": 25.01, "lng": 55.06, "congestion": 39},
    {"name": "Port of Mumbai", "country": "India", "code": "INBOM", "lat": 18.94, "lng": 72.84, "congestion": 68},
    {"name": "Port of Santos", "country": "Brazil", "code": "BRSSZ", "lat": -23.96, "lng": -46.33, "congestion": 63},
    {"name": "Port of Felixstowe", "country": "UK", "code": "GBFXT", "lat": 51.96, "lng": 1.31, "congestion": 51},
    {"name": "Port of Tokyo", "country": "Japan", "code": "JPTYO", "lat": 35.61, "lng": 139.77, "congestion": 42},
    {"name": "Port of Sydney", "country": "Australia", "code": "AUSYD", "lat": -33.85, "lng": 151.21, "congestion": 37},
    {"name": "Port of Le Havre", "country": "France", "code": "FRLEH", "lat": 49.48, "lng": 0.11, "congestion": 46},
]

CARRIERS = ["Maersk Line", "MSC", "CMA CGM", "Hapag-Lloyd", "COSCO Shipping", "Evergreen Marine"]
CATEGORIES = ["Electronics", "Pharmaceuticals", "Textiles", "Automotive", "Food & Beverage",
              "Machinery", "Chemicals", "Consumer Goods", "Luxury"]
METHODS = ["Sea", "Air", "Rail", "Road", "Express"]
STATUSES = ["Preparing", "In Transit", "Customs", "Delayed", "At Risk", "Delivered", "Cancelled"]
PRIORITIES = ["Standard", "High", "Critical"]
CUSTOMERS = ["Acme Retail", "Nordic Home", "TechMart", "GlobalPharma", "AutoParts Co",
             "FreshFoods Ltd", "LuxeGoods", "BuildRight", "MediCare Supply", "UrbanStyle"]


def _carrier_stats():
    stats = []
    for c in CARRIERS:
        on_time = round(random.uniform(78, 95), 1)
        stats.append({
            "id": c.lower().replace(" ", "-"), "name": c,
            "on_time_pct": on_time,
            "avg_delay_days": round(random.uniform(0.8, 3.4), 1),
            "cancellation_rate": round(random.uniform(0.5, 4.5), 1),
            "risk_score": round(100 - on_time + random.uniform(0, 12), 1),
        })
    return stats


def _gen_shipments(carrier_stats):
    ships = []
    now = datetime.now(timezone.utc)
    for i in range(126):
        origin = random.choice(PORTS)
        dest = random.choice([p for p in PORTS if p["name"] != origin["name"]])
        carrier = random.choice(carrier_stats)
        category = random.choice(CATEGORIES)
        method = random.choice(METHODS)
        docs = random.choice(["Complete", "Complete", "Complete", "Incomplete", "Missing"])
        value = random.randint(800, 90000)

        port_risk = origin["congestion"] * 0.6 + dest["congestion"] * 0.4
        customs = ml.predict_customs({
            "destination_country": dest["country"], "product_category": category,
            "shipment_value": value, "current_congestion": dest["congestion"],
            "season": random.choice(["Normal", "Peak", "Off-Peak"]), "documentation_status": docs,
        })
        geo = random.uniform(10, 85)
        factors = {
            "port": round(port_risk, 1), "customs": customs["delay_probability"],
            "geopolitical": round(geo, 1), "carrier": carrier["risk_score"],
            "route": round(random.uniform(15, 70), 1), "weather": round(random.uniform(5, 60), 1),
        }
        risk = ml.compute_risk(factors)
        status = random.choices(STATUSES, weights=[10, 34, 12, 10, 14, 16, 4])[0]
        created = now - timedelta(days=random.randint(1, 40))
        eta = created + timedelta(days=random.randint(6, 30))
        sid = f"TS-{2026}{i:04d}"
        route_path = [origin["name"], "Transit Hub", dest["name"]]
        current_loc = origin["name"] if status in ("Preparing",) else (
            dest["name"] if status == "Delivered" else "Transit Hub")
        ships.append({
            "id": sid, "shipment_id": sid, "order_id": f"ORD-{10000 + i}",
            "origin": origin["name"], "destination": dest["name"],
            "origin_coords": [origin["lat"], origin["lng"]],
            "dest_coords": [dest["lat"], dest["lng"]],
            "current_location": current_loc, "route": route_path,
            "carrier": carrier["name"], "product_category": category,
            "product_value": value, "weight_kg": random.randint(50, 24000),
            "shipping_method": method, "customs_status": random.choice(["Cleared", "Pending", "Under Review", "Held"]),
            "status": status, "expected_delivery": eta.date().isoformat(),
            "customer_priority": random.choice(PRIORITIES), "customer_name": random.choice(CUSTOMERS),
            "risk_score": risk["score"], "risk_category": risk["category"],
            "risk_factors": factors, "documentation_status": docs,
            "created_at": created.isoformat(),
        })
    return ships


def _gen_events():
    now = datetime.now(timezone.utc)
    raw = [
        ("Port of Los Angeles Labor Strike", "Dockworkers union announces 5-day strike halting container operations.",
         "Port of Los Angeles", "Strike", "Critical", "North America", "5 days", ["USLAX corridors"]),
        ("Red Sea Shipping Lane Disruption", "Vessels rerouting around Cape of Good Hope amid security concerns.",
         "Red Sea", "Conflict", "High", "Middle East", "Ongoing", ["Asia-Europe"]),
        ("Shanghai Port Congestion Surge", "Peak-season volumes drive average dwell time up 40%.",
         "Port of Shanghai", "Port Closure", "High", "East Asia", "2 weeks", ["Trans-Pacific"]),
        ("New EU Import Regulation", "Updated documentation requirements for electronics imports take effect.",
         "European Union", "Regulation", "Moderate", "Europe", "Permanent", ["Asia-Europe"]),
        ("Typhoon Warning - South China Sea", "Category 3 typhoon expected to disrupt regional shipping lanes.",
         "South China Sea", "Weather", "High", "Southeast Asia", "3-5 days", ["Intra-Asia"]),
        ("Rotterdam Customs System Outage", "Temporary IT outage slows customs clearance processing.",
         "Port of Rotterdam", "Carrier Disruption", "Moderate", "Europe", "1-2 days", ["Europe inland"]),
        ("Trade Sanctions Update", "New export restrictions announced affecting select commodity flows.",
         "Global", "Sanction", "High", "Global", "Indefinite", ["Multiple"]),
        ("India-Pakistan Border Restriction", "Land border crossing temporarily restricted for freight.",
         "Wagah Border", "Border Closure", "Moderate", "South Asia", "1 week", ["Overland Asia"]),
    ]
    events = []
    for i, (title, desc, loc, etype, sev, region, dur, routes) in enumerate(raw):
        events.append({
            "id": f"EVT-{1000 + i}", "title": title, "description": desc, "location": loc,
            "event_type": etype, "severity": sev, "affected_region": region,
            "estimated_duration": dur, "affected_routes": routes,
            "source": random.choice(["Reuters", "Lloyd's List", "Port Authority", "Government Advisory"]),
            "detected_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))).isoformat(),
        })
    return events


def _gen_alerts(ships):
    now = datetime.now(timezone.utc)
    levels = ["Info", "Warning", "High", "Critical"]
    templates = [
        ("Shipment risk increased", "High"), ("ETA changed significantly", "Warning"),
        ("Port marked high risk", "High"), ("Customs delay probability up", "Warning"),
        ("Geopolitical event affects route", "Critical"), ("Carrier performance dropped", "High"),
        ("Compliance issue detected", "Warning"), ("New disruption detected", "Critical"),
        ("Shipment cleared customs", "Info"),
    ]
    alerts = []
    for i in range(28):
        s = random.choice(ships)
        title, level = random.choice(templates)
        alerts.append({
            "id": f"ALR-{5000 + i}", "title": title, "level": level,
            "message": f'{title} for shipment {s["shipment_id"]} ({s["origin"]} → {s["destination"]}).',
            "shipment_id": s["shipment_id"], "read": random.random() > 0.6, "archived": False,
            "created_at": (now - timedelta(hours=random.randint(0, 120))).isoformat(),
        })
    return alerts


def _gen_recommendations(ships):
    now = datetime.now(timezone.utc)
    high_risk = [s for s in ships if s["risk_score"] >= 55][:12]
    recs = []
    for i, s in enumerate(high_risk):
        recs.append({
            "id": f"REC-{7000 + i}", "shipment_id": s["shipment_id"],
            "action": f'Reroute {s["shipment_id"]} via alternative corridor',
            "reasons": [
                "Current route has high assessed disruption risk",
                "Alternative route lowers exposure with comparable ETA",
                "Additional cost is within acceptable tolerance",
            ],
            "expected_outcome": {"eta": "down", "risk": "down", "cost": "up"},
            "explanation": "Rerouting reduces disruption exposure while keeping delivery within the most-likely ETA window.",
            "confidence": random.randint(72, 92), "status": "pending",
            "created_at": (now - timedelta(hours=random.randint(1, 48))).isoformat(),
            "decided_by": None, "decided_at": None, "decision_reason": None,
        })
    return recs


def _gen_predictions(ships):
    """Continuous-learning records: predicted vs actual."""
    recs = []
    for s in random.sample([x for x in ships if x["status"] == "Delivered"], k=min(20, len([x for x in ships if x["status"] == "Delivered"]))):
        predicted = round(random.uniform(5, 22), 1)
        actual = round(predicted + random.uniform(-2, 4), 1)
        recs.append({
            "id": f"PRD-{s['shipment_id']}", "shipment_id": s["shipment_id"],
            "predicted_eta_days": predicted, "actual_eta_days": actual,
            "error_days": round(abs(predicted - actual), 1),
            "confidence": random.randint(70, 92),
            "created_at": s["created_at"],
        })
    return recs


async def seed_all(db):
    admin_email = __import__("os").environ.get("ADMIN_EMAIL", "admin@tradesentinel.demo")
    admin_password = __import__("os").environ.get("ADMIN_PASSWORD", "Admin@123")

    # indexes
    await db.users.create_index("email", unique=True)
    try:
        await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    except Exception:
        pass
    await db.login_attempts.create_index("identifier")
    await db.shipments.create_index("shipment_id")

    # users (idempotent)
    demo_users = [
        {"email": admin_email, "password": admin_password, "name": "Kaniksha Suresh",
         "role": "admin", "organization": "TradeSentinel HQ", "phone": "+1-555-0100"},
        {"email": "admin@tradesentinel.demo", "password": "Admin@123", "name": "System Admin",
         "role": "admin", "organization": "TradeSentinel HQ", "phone": "+1-555-0101"},
        {"email": "manager@tradesentinel.demo", "password": "Manager@123", "name": "Morgan Reyes",
         "role": "manager", "organization": "Acme Global Logistics", "phone": "+1-555-0102"},
        {"email": "viewer@tradesentinel.demo", "password": "Viewer@123", "name": "Sam Lee",
         "role": "viewer", "organization": "Acme Global Logistics", "phone": "+1-555-0103"},
    ]
    for u in demo_users:
        existing = await db.users.find_one({"email": u["email"]})
        doc = {"email": u["email"], "password_hash": hash_password(u["password"]),
               "name": u["name"], "role": u["role"], "organization": u["organization"],
               "phone": u["phone"], "created_at": datetime.now(timezone.utc).isoformat()}
        if existing is None:
            await db.users.insert_one(doc)
        else:
            await db.users.update_one({"email": u["email"]},
                                      {"$set": {"password_hash": doc["password_hash"], "role": u["role"]}})

    # organizations
    if await db.organizations.count_documents({}) == 0:
        await db.organizations.insert_many([
            {"id": "org-hq", "name": "TradeSentinel HQ", "country": "USA", "users": 4, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": "org-acme", "name": "Acme Global Logistics", "country": "USA", "users": 12, "created_at": datetime.now(timezone.utc).isoformat()},
        ])

    # only seed operational data once
    if await db.shipments.count_documents({}) > 0:
        return

    carrier_stats = _carrier_stats()
    ships = _gen_shipments(carrier_stats)
    events = _gen_events()
    alerts = _gen_alerts(ships)
    recs = _gen_recommendations(ships)
    preds = _gen_predictions(ships)

    await db.carriers.insert_many(carrier_stats)
    await db.ports.insert_many([{**p, "id": p["code"],
                                 "risk_score": round(p["congestion"] * 0.7 + random.uniform(5, 20), 1)} for p in PORTS])
    await db.shipments.insert_many(ships)
    await db.geopolitical_events.insert_many(events)
    await db.alerts.insert_many(alerts)
    await db.recovery_recommendations.insert_many(recs)
    await db.predictions.insert_many(preds)
    await db.audit_logs.insert_one({
        "id": "AUD-0001", "actor": "system", "action": "seed",
        "detail": f"Seeded {len(ships)} shipments, {len(events)} events, {len(alerts)} alerts",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })



async def reset_demo(db):
    """Wipe operational collections (keep users & preferences) and re-seed."""
    for c in ["shipments", "geopolitical_events", "alerts", "recovery_recommendations",
              "approvals", "predictions", "ports", "carriers", "documents",
              "compliance_checks", "audit_logs", "integrations"]:
        await db[c].delete_many({})
    await seed_all(db)
