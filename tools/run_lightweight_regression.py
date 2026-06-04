#!/usr/bin/env python3
"""Run the lightweight Tantrium regression suite."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


COMMANDS = [
    [sys.executable, "tools/independent_verifier.py"],
    [sys.executable, "tools/tantrium_formalization_audit.py"],
    [sys.executable, "tools/tantrium_theorem_graph_audit.py"],
    [sys.executable, "-m", "pytest", "tests", "-q"],
]


def main() -> int:
    for command in COMMANDS:
        print("$ " + " ".join(command))
        result = subprocess.run(command, cwd=REPO_ROOT, text=True)
        if result.returncode != 0:
            print("RESULT: FAILED")
            return result.returncode
    print("TANTRIUM LIGHTWEIGHT REGRESSION")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
