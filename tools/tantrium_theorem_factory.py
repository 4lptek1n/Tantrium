#!/usr/bin/env python3
"""Generate Gate A/B theorem candidates."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.theorem_factory import generate_theorem_candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium theorem factory")
    parser.add_argument("--blocker", default="MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR")
    args = parser.parse_args()
    catalog = generate_theorem_candidates(args.blocker)
    print("TANTRIUM THEOREM FACTORY")
    print(f"BLOCKER: {args.blocker}")
    print(f"CANDIDATES: {catalog['candidate_count']}")
    print("RESULT: THEOREM_CANDIDATES_GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
