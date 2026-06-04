#!/usr/bin/env python3
"""Run counterexample search records for a Tantrium campaign."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.counterexample_hunter import search_counterexamples
from tantrium.research_os.research_director import campaign_dir
from tantrium.research_os.scheduler import resolve_campaign


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium counterexample hunter")
    parser.add_argument("--campaign", required=True, choices=["lah", "coefficient_frontier", "goldbach_minor_arc", "rh_formalization"])
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    campaign = resolve_campaign(args.campaign)
    result = search_counterexamples(campaign.campaign_id, campaign_dir(campaign), deep=args.deep)
    print("TANTRIUM COUNTEREXAMPLE HUNTER")
    print(f"CAMPAIGN: {campaign.campaign_id}")
    print(f"COUNTEREXAMPLE_FOUND: {result['found']}")
    print("RESULT: COUNTEREXAMPLE_SEARCH_COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
