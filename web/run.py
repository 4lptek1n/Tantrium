#!/usr/bin/env python3
"""Tantrium Web — Launcher"""
import uvicorn, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"\n  TANTRIUM ASI — http://localhost:{port}\n")
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False, app_dir=str(Path(__file__).parent))
