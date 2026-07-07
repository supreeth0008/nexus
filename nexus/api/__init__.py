try:
    from .server import app
except Exception:
    app = None
__all__=["app"]
