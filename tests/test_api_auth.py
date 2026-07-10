import os
import sys
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from nexus.api.server import app
from nexus.security.auth import verify_api_key


@pytest.fixture
def client():
    return TestClient(app)


@contextmanager
def _env_var(key: str, value: str):
    old = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old


def test_missing_api_key_returns_401(client):
    with _env_var("NEXUS_API_KEY", "nx_test_key"):
        response = client.get("/v1/incidents")
    assert response.status_code == 401


def test_invalid_api_key_returns_403(client):
    with _env_var("NEXUS_API_KEY", "nx_test_key"):
        response = client.get(
            "/v1/incidents",
            headers={"X-Nexus-API-Key": "not-a-valid-key"},
        )
    assert response.status_code == 403


def test_valid_api_key_returns_200(client):
    with _env_var("NEXUS_API_KEY", "nx_admin_test_key"):
        response = client.get(
            "/v1/incidents",
            headers={"X-Nexus-API-Key": "nx_admin_test_key"},
        )
    assert response.status_code == 200
    assert "incidents" in response.json()


def test_verify_api_key_rejects_missing_credentials():
    with _env_var("NEXUS_API_KEY", "nx_test_key"):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(None, None)
        assert exc_info.value.status_code == 401


def test_auth_fallback_does_not_grant_admin():
    """
    Regression test: if nexus.security.auth fails to import, the server
    module must refuse to load rather than fall back to an admin-everyone stub.
    """
    # Remove cached server module so re-import uses our fake-broken auth.
    sys.modules.pop("nexus.api.server", None)
    sys.modules.pop("nexus.security.auth", None)

    real_auth = sys.modules.get("nexus.security.auth")
    # Replace the auth module with None so the relative import fails.
    sys.modules["nexus.security.auth"] = None

    try:
        with pytest.raises(RuntimeError, match="authentication is required"):
            import nexus.api.server  # noqa: F401
    finally:
        # Restore the real auth module for subsequent tests.
        sys.modules["nexus.security.auth"] = real_auth
        sys.modules.pop("nexus.api.server", None)
