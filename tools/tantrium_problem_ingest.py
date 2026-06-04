#!/usr/bin/env python3
"""Write Tantrium research OS problem IR."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.problem_ir import write_problem_ir
from tantrium.research_os.scheduler import resolve_campaign


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium problem ingest")
    parser.add_argument("--campaign", required=True, choices=["lah", "coefficient_frontier", "goldbach_minor_arc", "rh_formalization"])
    args = parser.parse_args()
    campaign = resolve_campaign(args.campaign)
    path = write_problem_ir(campaign.campaign_id)
    print("TANTRIUM PROBLEM INGEST")
    print(f"CAMPAIGN: {campaign.campaign_id}")
    print(f"OUTPUT: {path.relative_to(REPO_ROOT)}")
    print("RESULT: PROBLEM_IR_GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
