# I enforce API authentication and RBAC
import os, hmac, hashlib, time
from typing import Optional, Tuple
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
# I support API key and Bearer OIDC-style tokens
api_key_header = APIKeyHeader(name="X-Nexus-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)
# I load allowed keys from env – in production use a proper secrets store
def _allowed_keys() -> set:
    keys = set()
    # I read NEXUS_API_KEY (single) and NEXUS_API_KEYS (comma-separated)
    single = os.getenv("NEXUS_API_KEY", "")
    if single:
        keys.add(single)
    multi = os.getenv("NEXUS_API_KEYS", "")
    if multi:
        keys.update([k.strip() for k in multi.split(",") if k.strip()])
    # I provide a dev fallback – NEVER in production
    if not keys and os.getenv("NEXUS_ENV", "dev") == "dev":
        keys.add("nexus-dev-key-change-me")
    return keys
def verify_api_key(api_key: Optional[str] = Security(api_key_header),
                   bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)):
    # I allow either X-Nexus-API-Key header or Authorization: Bearer <token>
    allowed = _allowed_keys()
    if not allowed:
        # I fail closed if no keys configured in prod
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
    # I use constant-time compare to prevent timing attacks
    valid = any(hmac.compare_digest(token, k) for k in allowed)
    if not valid:
        # I rate-limit auth failures in middleware – here I just reject
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
    # I map key → role (simple – full RBAC would use JWT claims)
    role = "admin" if token.startswith("nx_admin") or token == "nexus-dev-key-change-me" else "operator"
    return {"sub": hashlib.sha256(token.encode()).hexdigest()[:16], "role": role}
def require_role(required: str):
    # I enforce RBAC – roles: reader < operator < admin
    order = {"reader":0, "operator":1, "admin":2}
    def checker(principal: dict = Security(verify_api_key)):
        user_role = principal.get("role", "reader")
        if order.get(user_role,0) < order.get(required,0):
            raise HTTPException(status_code=403, detail=f"I require role {required}, you are {user_role}")
        return principal
    return checker
# I sign audit entries to detect tampering
def sign_audit(payload: str, secret: Optional[str]=None) -> str:
    secret = secret or os.getenv("NEXUS_AUDIT_HMAC_KEY", "dev-audit-key-rotate-me")
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
# I redact secrets from logs / API responses
REDACT_KEYS = {"password","secret","token","dsn","api_key","apikey","authorization","auth","private_key","client_secret"}
def redact(obj):
    if isinstance(obj, dict):
        return {k: ("REDACTED" if k.lower() in REDACT_KEYS or any(r in k.lower() for r in REDACT_KEYS) else redact(v)) for k,v in obj.items()}
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj
# I provide simple rate limiting (token bucket in-memory – for production use Redis)
import threading
_buckets = {}
_lock = threading.Lock()
def rate_limit(key: str, rate: int=60, per_seconds: int=60) -> bool:
    # I allow `rate` requests per `per_seconds`
    # returns True if allowed, False if throttled
    now = time.time()
    with _lock:
        b = _buckets.get(key)
        if not b or now - b["start"] > per_seconds:
            _buckets[key] = {"start": now, "count": 1}
            return True
        if b["count"] < rate:
            b["count"] += 1
            return True
        return False
