import sys
VERSION = "0.6.0"
COMMIT = "phase6-prod"
DATE = "2026-07-07"
def build_info() -> dict:
    return {
        "version": VERSION,
        "commit": COMMIT,
        "date": DATE,
        "python_version": sys.version.split()[0],
    }
