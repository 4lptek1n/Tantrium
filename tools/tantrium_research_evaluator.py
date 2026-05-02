#!/usr/bin/env python3
"""Run Tantrium research OS self-evaluation benchmarks."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.evaluator import run_benchmarks


def main() -> int:
    report = run_benchmarks()
    subprocess.run(
        [sys.executable, "tools/tantrium_artifact_manifest.py", "--command-used", "python tools/tantrium_research_evaluator.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    print("TANTRIUM RESEARCH EVALUATOR")
    print(f"BENCHMARKS: {len(report['benchmarks'])}")
    print(f"RESULT: {report['result']}")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
