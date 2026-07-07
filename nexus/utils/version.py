import sys
VERSION="0.2.0"; COMMIT="python-rewrite"; DATE="2026-07-07"
def build_info()->dict:
    return {"version":VERSION,"commit":COMMIT,"date":DATE,"python_version":sys.version.split()[0]}
