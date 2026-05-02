#!/usr/bin/env python3
"""Generate theorem candidates for a Tantrium research OS campaign."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.evidence_miner import mine_evidence
from tantrium.research_os.research_director import campaign_dir
from tantrium.research_os.scheduler import resolve_campaign
from tantrium.research_os.theorem_synthesizer import synthesize_candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium theorem synthesizer")
    parser.add_argument("--campaign", required=True, choices=["lah", "coefficient_frontier", "goldbach_minor_arc", "rh_formalization"])
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    campaign = resolve_campaign(args.campaign)
    out_dir = campaign_dir(campaign)
    evidence = mine_evidence(campaign.campaign_id, out_dir, deep=args.deep)
    candidates = synthesize_candidates(campaign.campaign_id, evidence, out_dir)
    print("TANTRIUM THEOREM SYNTHESIZER")
    print(f"CAMPAIGN: {campaign.campaign_id}")
    print(f"CANDIDATES: {len(candidates)}")
    print("RESULT: CANDIDATE_THEOREMS_GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
