import sys

VERSION = "1.0.0"
COMMIT = "prod-ready"
DATE = "2026-07-08"


def build_info() -> dict:
    return {
        "version": VERSION,
        "commit": COMMIT,
        "date": DATE,
        "python_version": sys.version.split()[0],
    }
