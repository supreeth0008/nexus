# I enforce API authentication and RBAC
import hashlib
import hmac
import os
import time
import threading
from typing import Dict

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

api_key_header = APIKeyHeader(name="X-Nexus-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

def _allowed_keys() -> set:
    keys = set()
    single = os.getenv("NEXUS_API_KEY", "")
    if single:
        keys.add(single)
    multi = os.getenv("NEXUS_API_KEYS", "")
    if multi:
        keys.update([k.strip() for k in multi.split(",") if k.strip()])
    if not keys and os.getenv("NEXUS_ENV", "dev") == "dev":
        keys.add("nexus-dev-key-change-me")
    return keys

def verify_api_key(api_key: str | None = Security(api_key_header), bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme)):
    allowed = _allowed_keys()
    if not allowed:
        if os.getenv("NEXUS_ENV", "dev") == "prod":
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication not configured")
        return {"sub": "dev-anonymous", "role": "admin"}
    token = None
    if api_key:
        token = api_key
    elif bearer and bearer.credentials:
        token = bearer.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials – I require X-Nexus-API-Key or Bearer token")
    valid = any(hmac.compare_digest(token, k) for k in allowed)
    if not valid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
    role = "admin" if token.startswith("nx_admin") or token == "nexus-dev-key-change-me" else "operator"
    return {"sub": hashlib.sha256(token.encode()).hexdigest()[:16], "role": role}

def require_role(required: str):
    order = {"reader": 0, "operator": 1, "admin": 2}
    def checker(principal: dict = Security(verify_api_key)):
        user_role = principal.get("role", "reader")
        if order.get(user_role, 0) < order.get(required, 0):
            raise HTTPException(status_code=403, detail=f"I require role {required}, you are {user_role}")
        return principal
    return checker

def sign_audit(payload: str, secret: str | None = None) -> str:
    s: str = secret or os.getenv("NEXUS_AUDIT_HMAC_KEY") or "dev-audit-key-rotate-me"
    return hmac.new(s.encode(), payload.encode(), hashlib.sha256).hexdigest()

REDACT_KEYS = {"password","secret","token","dsn","api_key","apikey","authorization","auth","private_key","client_secret"}

def redact(obj):
    if isinstance(obj, dict):
        return {k: ("REDACTED" if k.lower() in REDACT_KEYS or any(r in k.lower() for r in REDACT_KEYS) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj

_buckets: Dict[str, Dict[str, float]] = {}
_lock = threading.Lock()

def rate_limit(key: str, rate: int = 120, per_seconds: int = 60) -> bool:
    now = time.time()
    with _lock:
        b = _buckets.get(key)
        if not b or now - float(b.get("start", 0)) > per_seconds:
            _buckets[key] = {"start": now, "count": 1}
            return True
        if int(b.get("count", 0)) < rate:
            b["count"] = int(b.get("count", 0)) + 1
            return True
        return False
