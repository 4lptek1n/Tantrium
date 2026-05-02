#!/usr/bin/env python3
"""Attempt research-level certificates and refined subgap certificates."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.certificate_builder import build_research_certificate
from tantrium.research_os.counterexample_hunter import search_counterexamples
from tantrium.research_os.evidence_miner import mine_evidence
from tantrium.research_os.research_director import campaign_dir
from tantrium.research_os.scheduler import resolve_campaign
from tantrium.research_os.strategy_engine import rank_and_attempt
from tantrium.research_os.theorem_synthesizer import synthesize_candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium certificate builder")
    parser.add_argument("--campaign", required=True, choices=["lah", "coefficient_frontier", "goldbach_minor_arc", "rh_formalization"])
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    campaign = resolve_campaign(args.campaign)
    out_dir = campaign_dir(campaign)
    evidence = mine_evidence(campaign.campaign_id, out_dir, deep=args.deep)
    candidates = synthesize_candidates(campaign.campaign_id, evidence, out_dir)
    counterexamples = search_counterexamples(campaign.campaign_id, out_dir, deep=args.deep)
    attempts = rank_and_attempt(campaign.campaign_id, candidates, out_dir)
    cert = build_research_certificate(campaign.campaign_id, out_dir, attempts, counterexamples)
    print("TANTRIUM CERTIFICATE BUILDER")
    print(f"CAMPAIGN: {campaign.campaign_id}")
    print(f"STATUS: {cert['status']}")
    print(f"REFINED_SUBGAP: {cert['refined_subgap']}")
    print("RESULT: CERTIFICATE_ATTEMPTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
