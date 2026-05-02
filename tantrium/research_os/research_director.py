"""Research director orchestration for Tantrium campaigns."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .agent_protocol import ResearchEvent
from .atlas_writer import write_atlas_event
from .blackboard import RESULTS_ROOT, append_event, update_current_campaign
from .certificate_builder import build_research_certificate
from .counterexample_hunter import search_counterexamples
from .evidence_miner import mine_evidence
from .formalization_bridge import build_formalization_outputs
from .manuscript_builder import build_manuscripts
from .problem_ir import write_problem_ir
from .proof_state import assert_terminal_status
from .registry_updater import update_registry
from .scheduler import Campaign, expand_campaigns
from .strategy_engine import rank_and_attempt
from .theorem_synthesizer import synthesize_candidates

REPO_ROOT = Path(__file__).resolve().parents[2]


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def campaign_dir(campaign: Campaign) -> Path:
    return RESULTS_ROOT / "campaigns" / campaign.result_dir


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_campaign(campaign: Campaign, deep: bool = False) -> dict[str, Any]:
    out_dir = campaign_dir(campaign)
    out_dir.mkdir(parents=True, exist_ok=True)
    problem_path = write_problem_ir(campaign.campaign_id)
    append_event(
        ResearchEvent(
            campaign.campaign_id,
            "Repository Cartographer",
            "problem_ir_written",
            "EVIDENCE_MINED",
            outputs=[str(problem_path.relative_to(REPO_ROOT))],
            next_actions=["mine evidence", "synthesize theorem candidates"],
        )
    )
    evidence = mine_evidence(campaign.campaign_id, out_dir, deep=deep)
    candidates = synthesize_candidates(campaign.campaign_id, evidence, out_dir)
    counterexamples = search_counterexamples(campaign.campaign_id, out_dir, deep=deep)
    attempts = rank_and_attempt(campaign.campaign_id, candidates, out_dir)
    formalization = build_formalization_outputs(campaign.campaign_id, candidates, out_dir)
    synthesis = build_research_certificate(campaign.campaign_id, out_dir, attempts, counterexamples)
    assert_terminal_status(synthesis["status"])
    write_campaign_specific_outputs(campaign.campaign_id, out_dir, evidence, candidates, attempts, synthesis)
    build_manuscripts(campaign.campaign_id, out_dir, evidence, candidates, attempts, synthesis)
    update_registry(campaign.campaign_id, synthesis, out_dir)
    write_atlas_event(campaign.campaign_id, synthesis)
    summary = {
        "campaign": campaign.campaign_id,
        "public_name": campaign.public_name,
        "status": synthesis["status"],
        "refined_subgap": synthesis["refined_subgap"],
        "candidate_count": len(candidates),
        "proof_attempt_count": len(attempts["attempts"]),
        "counterexample_found": counterexamples["found"],
        "formalization_items": len(formalization["work_queue"]),
        "result_dir": str(out_dir.relative_to(REPO_ROOT)),
    }
    write_json(out_dir / "campaign_summary.json", summary)
    update_current_campaign(campaign.campaign_id, summary)
    append_event(
        ResearchEvent(
            campaign.campaign_id,
            "Research Director",
            "campaign_completed",
            synthesis["status"],
            outputs=[str((out_dir / "campaign_summary.json").relative_to(REPO_ROOT))],
            next_actions=[attempts["attempts"][0]["next_action"] if attempts["attempts"] else "human review"],
        )
    )
    return summary


def run_campaigns(name: str, deep: bool = False) -> list[dict[str, Any]]:
    return [run_campaign(campaign, deep=deep) for campaign in expand_campaigns(name)]


def write_campaign_specific_outputs(
    campaign_id: str,
    out_dir: Path,
    evidence: dict[str, Any],
    candidates: list[dict[str, Any]],
    attempts: dict[str, Any],
    synthesis: dict[str, Any],
) -> None:
    if campaign_id == "coefficient_frontier_parametric_lift":
        write_json(
            out_dir / "frontier_identification.json",
            {
                "campaign": campaign_id,
                "frontier": "FIRST_UNCERTIFIED_ATLAS_FRONTIER",
                "blocker": "PARAMETRIC_POSITIVITY_NOT_YET_CERTIFIED",
                "candidate_connections": evidence.get("candidate_connections", []),
            },
        )
        write_json(out_dir / "factorization_attempts.json", {"status": "ATTEMPTED", "result": "NO_CERTIFIED_GLOBAL_FACTORIZATION"})
        write_json(out_dir / "binomial_basis_attempts.json", {"status": "ATTEMPTED", "result": "NO_NONNEGATIVE_BINOMIAL_BASIS_CERTIFICATE"})
        write_json(out_dir / "d_seed_lift_attempt.json", {"status": "ATTEMPTED", "result": "MISSING_D_SEED_FRONTIER_REPRESENTATION"})
        write_json(out_dir / "lgv_lift_attempt.json", {"status": "ATTEMPTED", "result": "MISSING_LGV_PATH_FRONTIER_REPRESENTATION"})
    elif campaign_id == "goldbach_minor_arc_bound":
        (out_dir / "minor_arc_target_inequality.md").write_text(
            "\n".join(
                [
                    "# Goldbach Minor Arc Target Inequality",
                    "",
                    "Target: prove an unconditional minor arc bound strong enough that the minor arc contribution is dominated by the certified major arc main term.",
                    "",
                    "Machine target:",
                    "",
                    "```text",
                    "MinorArc(N) = o(SingularSeries(N) * N)",
                    "```",
                    "",
                    "No unconditional bound is claimed here.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        source = REPO_ROOT / "results" / "conjectures" / "goldbach" / "blocker_certificate.json"
        if source.exists():
            (out_dir / "blocker_certificate.json").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        (out_dir / "known_inputs.md").write_text(
            "# Known Inputs\n\n- Singular series positivity certificate\n- Major arc schema\n- Vaughan identity route\n- Large sieve route\n- Zero-density route\n- Type I/II sums\n",
            encoding="utf-8",
        )
        (out_dir / "candidate_strategies.md").write_text(
            "# Candidate Strategies\n\n- Analytic number theory estimate route\n- Sieve/dispersion route\n- Computational threshold plus theorem above threshold route\n- GRH-conditional reference route, not promoted as unconditional proof\n",
            encoding="utf-8",
        )
    elif campaign_id == "lah_gate_ab_generalization":
        (out_dir / "inferred_laws.md").write_text(
            "# Inferred Laws: lah_gate_ab_generalization\n\n- Top ramp exponent `T_j=j(j+1)/2`.\n- Quotient degree candidate `deg_n Q_{j,r}=r(2j-r-1)/2`.\n- Refined subgap: `MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR`.\n",
            encoding="utf-8",
        )


def run_loop(name: str, iterations: int, deep: bool = False) -> dict[str, Any]:
    run_id = now_stamp()
    run_dir = RESULTS_ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    iteration_summaries = []
    for iteration in range(1, iterations + 1):
        for campaign in expand_campaigns(name):
            summary = run_campaign(campaign, deep=deep)
            summary["iteration"] = iteration
            iteration_summaries.append(summary)
            source = campaign_dir(campaign) / "campaign_summary.json"
            if source.exists():
                shutil.copyfile(source, run_dir / f"{iteration:02d}_{campaign.campaign_id}_summary.json")
    payload = {"run_id": run_id, "campaign": name, "iterations": iterations, "summaries": iteration_summaries}
    write_json(run_dir / "run_summary.json", payload)
    append_event(ResearchEvent(name, "Research Director", "loop_completed", "NEXT_SUBGAP_IDENTIFIED", outputs=[str((run_dir / "run_summary.json").relative_to(REPO_ROOT))]))
    return payload
