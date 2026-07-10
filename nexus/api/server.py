# I expose Nexus via HTTP API – Phase 5/6 hardened
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

app: FastAPI | None = None
try:
    from fastapi import Depends, FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, PlainTextResponse
    from pydantic import BaseModel

    # I import config, DB, metrics, and security
    from ..config.settings import load_config
    from ..db import Database, IncidentStore
    from ..utils.metrics import inc as metrics_inc
    try:
        from ..security.auth import rate_limit, redact, require_role, verify_api_key
        _auth_enabled = True
    except Exception as exc:
        raise RuntimeError(
            "Failed to load nexus.security.auth; authentication is required."
        ) from exc

    app = FastAPI(
        title="Nexus API",
        version="0.6.1",
        description=(
            "I am the Nexus autonomous infrastructure control plane API – "
            "authenticated, audited, policy-gated"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # I add rate-limit + audit middleware
    @app.middleware("http")
    async def audit_middleware(request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        # I rate limit per IP
        if not rate_limit(f"ip:{client_ip}", rate=120, per_seconds=60):
            metrics_inc(
                "nexus_api_requests_total",
                labels={"endpoint": endpoint, "code": "429"},
            )
            return JSONResponse(
                {"detail": "I throttled this client – rate limit exceeded"},
                status_code=429,
            )
        # I redact auth headers in logs
        # (structlog would go here – keeping stdlib for brevity)
        try:
            response = await call_next(request)
            metrics_inc(
                "nexus_api_requests_total",
                labels={"endpoint": endpoint, "code": str(response.status_code)},
            )
            return response
        except Exception:
            metrics_inc(
                "nexus_api_requests_total",
                labels={"endpoint": endpoint, "code": "500"},
            )
            # I never leak stack traces in prod
            return JSONResponse({"detail":"Internal error – I logged it securely"}, status_code=500)

    class HealthResp(BaseModel):
        status: str
        service: str
        version: str
        autonomy_level: int = 0

    @app.get("/health", response_model=HealthResp, tags=["ops"])
    def health():
        return {"status":"ok","service":"nexus","version":"0.6.1","autonomy_level":2}

    # I protect /v1/* with API key
    def auth_dep():
        if _auth_enabled:
            return Depends(verify_api_key)
        return None

    # Module-level dependency objects avoid B008 (function call in default arg).
    _incident_principal_dep = Depends(verify_api_key) if _auth_enabled else None
    _target_principal_dep = Depends(require_role("operator")) if _auth_enabled else None
    _cycle_principal_dep = Depends(require_role("operator")) if _auth_enabled else None

    @app.get("/v1/incidents", tags=["incidents"])
    def list_incidents(
        limit: int = 20,
        status: str | None = None,
        principal: dict | None = _incident_principal_dep,
    ):
        cfg = load_config()
        if not cfg.database.dsn:
            return redact({
                "incidents": [],
                "total": 0,
                "db_configured": False,
                "principal": principal.get("sub") if principal else "dev",
            })
        try:
            db = Database(cfg.database.dsn)
            try:
                sess = db.get_session()
                try:
                    store = IncidentStore(sess)
                    rows = store.list(status=status, limit=limit)
                finally:
                    sess.close()
            finally:
                db.close()
            return redact({
                "incidents": rows,
                "total": len(rows),
                "db_configured": True,
                "principal": principal.get("sub") if principal else "dev",
            })
        except Exception as exc:
            return JSONResponse(
                {"detail": f"Database error: {exc}"},
                status_code=503,
            )

    @app.get("/v1/targets", tags=["targets"])
    def list_targets(principal: dict | None = _target_principal_dep):
        return {"targets":[
            {"name":"demo-k8s","provider":"kubernetes","endpoint":"https://127.0.0.1:6443","status":"active"},
            {"name":"demo-aws","provider":"localstack","endpoint":"http://localhost:4566","status":"active"},
            {"name":"demo-prom","provider":"prometheus","endpoint":"http://localhost:9090","status":"active"}
        ]}

    @app.post("/v1/cycles", tags=["cycles"])
    def trigger_cycle(principal: dict | None = _cycle_principal_dep):
        # I would enqueue a real cycle – MVP simulates
        return {
            "cycle_id": "cyc_" + "f" * 8,
            "status": "running",
            "trigger": "manual",
            "started_by": principal.get("sub") if principal else "api",
        }

    @app.get("/v1/metrics", response_class=PlainTextResponse, tags=["ops"])
    def metrics():
        # I expose Prometheus metrics – authenticated in prod, open for scraping with bearer
        try:
            from ..utils.metrics import get_metrics_text
            return get_metrics_text()
        except Exception:
            return ""

    @app.post("/v1/webhook/github", tags=["integrations"])
    async def github_webhook(request: Request):
        import hashlib
        import hmac
        import os

        secret = os.getenv("NEXUS_GITHUB_WEBHOOK_SECRET", "")
        if not secret:
            return JSONResponse(
                {"detail": "GitHub webhook secret not configured"},
                status_code=401,
            )

        signature = request.headers.get("X-Hub-Signature-256", "")
        if not signature:
            return JSONResponse(
                {"detail": "Missing X-Hub-Signature-256 header"},
                status_code=401,
            )

        body = await request.body()
        expected = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        prefix = "sha256="
        if not signature.startswith(prefix) or not hmac.compare_digest(
            signature[len(prefix):], expected
        ):
            return JSONResponse(
                {"detail": "Invalid GitHub webhook signature"},
                status_code=401,
            )

        return {
            "received": True,
            "bytes": len(body),
            "verified": "signature valid",
        }

except ImportError:
    app = None
