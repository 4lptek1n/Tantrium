#!/usr/bin/env python3
"""Mine subresultant/QJR recurrence candidates."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.recurrence import mine_subresultant_recurrences


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium subresultant recurrence miner")
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    result = mine_subresultant_recurrences(deep=args.deep)
    synthesis = result["synthesis"]
    print("TANTRIUM SUBRESULTANT RECURRENCE MINER")
    print(f"STATUS: {synthesis['status']}")
    print(f"BEST_CANDIDATE: {synthesis['best_candidate']}")
    print(f"REFINED_SUBGAP: {synthesis['refined_subgap']}")
    print("RESULT: GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
