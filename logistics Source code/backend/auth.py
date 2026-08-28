"""Authentication: bcrypt hashing, JWT access/refresh tokens, RBAC helpers."""
import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request, Depends

try:
    from bson import ObjectId
except ImportError:
    ObjectId = str

JWT_ALGORITHM = "HS256"

ADMIN_USER = {
    "id": "usr_admin",
    "name": "Administrator",
    "email": "admin",
    "role": "admin",
    "organization": "TradeIntel AI Global",
    "phone": "+1 555-0100",
}

DEMO_USERS = {
    "admin": ADMIN_USER,
    "admin@tradeintel.ai": ADMIN_USER,
    "admin@tradesentinel.demo": ADMIN_USER,
}


def get_jwt_secret() -> str:
    return os.environ.get("JWT_SECRET", "e9a2f7d3c5b8a14e9f2d6c8b1a4f7e3d5c9b2a1f4e7d8c5b9a2f1e4d7c8b5a3f")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
        "type": "access",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def set_auth_cookies(response, access: str, refresh: str):
    response.set_cookie(
        "access_token", access, httponly=True, secure=False,
        samesite="lax", max_age=43200, path="/"
    )
    response.set_cookie(
        "refresh_token", refresh, httponly=True, secure=False,
        samesite="lax", max_age=604800, path="/"
    )


def clear_auth_cookies(response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


_db_ref = {"db": None}


def init_auth(db):
    _db_ref["db"] = db


async def get_current_user(request: Request) -> dict:
    db = _db_ref["db"]
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        email = payload.get("email", "").lower()
        sub = payload.get("sub", "")

        if db is not None:
            try:
                if ObjectId != str and ObjectId.is_valid(sub):
                    user = await db.users.find_one({"_id": ObjectId(sub)})
                    if user:
                        user["id"] = str(user["_id"])
                        user.pop("_id", None)
                        user.pop("password_hash", None)
                        return user
                user_by_email = await db.users.find_one({"email": email})
                if user_by_email:
                    user_by_email["id"] = str(user_by_email.get("_id", sub))
                    user_by_email.pop("_id", None)
                    user_by_email.pop("password_hash", None)
                    return user_by_email
            except Exception:
                pass

        # Demo users fallback
        if email in DEMO_USERS:
            return DEMO_USERS[email]

        return {
            "id": sub or "usr_admin",
            "email": email or "admin@tradeintel.ai",
            "name": email.split("@")[0].replace(".", " ").title() if email else "Administrator",
            "role": payload.get("role", "admin"),
            "organization": "TradeIntel AI Global",
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_roles(*roles):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker
