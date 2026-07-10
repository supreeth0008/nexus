from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

app: FastAPI | None = None
try:
    from .server import app
except Exception:
    app = None
__all__ = ["app"]

