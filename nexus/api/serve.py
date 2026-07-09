# I serve the Nexus HTTP API – production ready
def run_api(host: str="0.0.0.0", port: int=8080, reload: bool=False):
    # I try uvicorn, fallback gracefully
    try:
        import uvicorn

        from .server import app
        if app is None:
            raise RuntimeError("FastAPI not installed – pip install fastapi uvicorn")
        # I log startup
        print(f"Nexus API starting – I listen on http://{host}:{port}")
        print(f"Docs: http://{host}:{port}/docs")
        uvicorn.run("nexus.api.server:app", host=host, port=port, reload=reload, log_level="info")
    except ImportError as e:
        print(f"I could not start API server – missing dependency: {e}")
        print("I recommend: pip install fastapi uvicorn")
        raise SystemExit(1) from None
if __name__ == "__main__":
    run_api()
