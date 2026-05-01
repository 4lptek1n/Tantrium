from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gate_a_b_artifacts_exist():
    required = [
        "math/gate_a.py",
        "math/gate_a_verify.py",
        "theorems/GATE_A_PERTURBATION_THEOREM.md",
        "theorems/GATE_A_CROSS_RATIO_THEOREM.md",
        "theorems/GATE_B_STAIRCASE_THEOREM.md",
        "docs/GATE_A_B_INTEGRATION.md",
    ]
    for rel in required:
        assert (ROOT / rel).exists(), rel


def test_gate_b_document_records_staircase_law():
    text = (ROOT / "theorems/GATE_B_STAIRCASE_THEOREM.md").read_text(encoding="utf-8")
    assert "2^{T_j}" in text
    assert "r(2j-r-1)/2" in text
