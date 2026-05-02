from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gate_ab_v2_outputs_exist():
    required = [
        "results/research_os/campaigns/subresultant_recurrence/qjr_tables.json",
        "results/research_os/campaigns/subresultant_recurrence/h_factor_inventory.json",
        "results/research_os/campaigns/subresultant_recurrence/recurrence_report.md",
        "theorems/SUBRESULTANT_QJR_RECURRENCE_CONJECTURE.md",
        "docs/TANTRIUM_THEOREM_CANDIDATE_CATALOG.md",
    ]
    for rel in required:
        assert (ROOT / rel).exists(), rel
