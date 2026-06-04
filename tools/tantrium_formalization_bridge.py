#!/usr/bin/env python3
"""Generate Tantrium research OS formalization work queues."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.evidence_miner import mine_evidence
from tantrium.research_os.formalization_bridge import build_formalization_outputs
from tantrium.research_os.research_director import campaign_dir
from tantrium.research_os.scheduler import resolve_campaign
from tantrium.research_os.theorem_synthesizer import synthesize_candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium formalization bridge")
    parser.add_argument("--campaign", default="rh_formalization", choices=["lah", "coefficient_frontier", "goldbach_minor_arc", "rh_formalization"])
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    campaign = resolve_campaign(args.campaign)
    out_dir = campaign_dir(campaign)
    evidence = mine_evidence(campaign.campaign_id, out_dir, deep=args.deep)
    candidates = synthesize_candidates(campaign.campaign_id, evidence, out_dir)
    queue = build_formalization_outputs(campaign.campaign_id, candidates, out_dir)
    print("TANTRIUM FORMALIZATION BRIDGE")
    print(f"CAMPAIGN: {campaign.campaign_id}")
    print(f"WORK_ITEMS: {len(queue['work_queue'])}")
    print("RESULT: FORMALIZATION_SCAFFOLD_GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
