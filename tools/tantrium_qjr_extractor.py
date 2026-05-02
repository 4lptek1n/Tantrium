#!/usr/bin/env python3
"""Generate QJR normal-form evidence tables."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.recurrence.qjr_extractor import build_qjr_tables


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium QJR extractor")
    parser.add_argument("--max-j", type=int, default=8)
    args = parser.parse_args()
    out_dir = REPO_ROOT / "results" / "research_os" / "campaigns" / "subresultant_recurrence"
    table = build_qjr_tables(out_dir, max_j=args.max_j)
    print("TANTRIUM QJR EXTRACTOR")
    print(f"ROWS: {len(table['rows'])}")
    print("RESULT: QJR_TABLES_GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
