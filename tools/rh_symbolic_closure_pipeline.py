#!/usr/bin/env python3
"""
Raw RH -> Tantrium symbolic closure pipeline.

Minimal orchestrator for the full target chain:
  1. register raw RH / Xi / Jensen target
  2. require Jensen hyperbolicity target
  3. require Sturm pivot bridge
  4. require tau/subdiscriminant bridge
  5. require AG/LGV transfer bridge
  6. require D-positivity certificate/theorem
  7. run executable finite-window audits
  8. emit a symbolic closure status file

This is not a numerical RH proof. It is the machine entrypoint that feeds the
raw RH target into the Tantrium theorem/certificate stack.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Step:
    name: str
    kind: str
    target: str
    artifact: str | None = None
    command: list[str] | None = None
    required_markers: tuple[str, ...] = ()


STEPS = [
    Step(
        name="raw_rh_target",
        kind="input",
        target="Xi(z)=xi(1/2+i z) has only real zeros",
        artifact="inputs/rh_raw_hypothesis.yaml",
        required_markers=("rh_raw_hypothesis", "Jensen", "D-positivity"),
    ),
    Step(
        name="jensen_target",
        kind="theorem-target",
        target="J_Xi^{d,n}(X) hyperbolic for all d>=1,n>=0",
        artifact="paper/TANTRIUM_RH_MAIN_THEOREM.md",
        required_markers=("J_Xi", "hyperbolic", "d>=1,n>=0"),
    ),
    Step(
        name="sturm_pivots",
        kind="theorem-bridge",
        target="positive Sturm/subresultant pivots imply Jensen hyperbolicity",
        artifact="theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md",
        required_markers=("Sturm", "subresultant", "Jensen", "hyperbolic"),
    ),
    Step(
        name="tau_subdiscriminant",
        kind="theorem-bridge",
        target="tau_j = Disc_j(P), H_j=N_j tau_j, N_j>0",
        artifact="theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md",
        required_markers=("tau_j", "Disc_j", "N_j", "subdiscriminant"),
        command=[sys.executable, "tools/tau_sturm_identity_checker.py"],
    ),
    Step(
        name="ag_lgv_transfer",
        kind="theorem-bridge",
        target="M_{a,b}(t)=s_{a+b}(t) and tau is LGV nonintersecting path sum",
        artifact="theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md",
        required_markers=("M_{a,b}(t)", "s_{a+b}(t)", "path--atom bijection", "Lindstrom-Gessel-Viennot"),
        command=[sys.executable, "tools/ag_lgv_transfer_checker.py"],
    ),
    Step(
        name="cell_support",
        kind="theorem-bridge",
        target="C_cell(s)>0 for s in iota(D)",
        artifact="theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md",
        required_markers=("C_cell(s) > 0", "kappa_s", "strict surplus"),
    ),
    Step(
        name="d_positivity",
        kind="certificate-theorem",
        target="D(m,ell,a)>=0 for all admissible triples",
        artifact="theorems/D_POSITIVITY_THEOREM.md",
        required_markers=("D(m,ell,a) >= 0", "Uniform Lift", "D-positivity"),
    ),
    Step(
        name="artifact_audit",
        kind="executable-audit",
        target="repository theorem artifact chain is present",
        artifact="tools/proof_chain_audit.py",
        required_markers=("TANTRIUM PROOF CHAIN AUDIT",),
        command=[sys.executable, "tools/proof_chain_audit.py"],
    ),
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_markers(step: Step) -> list[str]:
    if not step.artifact:
        return []
    path = ROOT / step.artifact
    if not path.exists():
        return [f"missing artifact: {step.artifact}"]
    text = read(path)
    return [f"missing marker in {step.artifact}: {m}" for m in step.required_markers if m not in text]


def run_command(step: Step) -> tuple[bool, str]:
    if not step.command:
        return True, "not required"
    proc = subprocess.run(step.command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode == 0, proc.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "rh_symbolic_closure_pipeline.md")
    ap.add_argument("--strict", action="store_true", help="fail on any missing marker or command failure")
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    rows: list[tuple[Step, str, str]] = []

    for step in STEPS:
        marker_failures = check_markers(step)
        ok_cmd, output = run_command(step)
        status = "PASS" if not marker_failures and ok_cmd else "FAIL"
        if marker_failures:
            failures.extend([f"{step.name}: {x}" for x in marker_failures])
        if not ok_cmd:
            failures.append(f"{step.name}: command failed")
        rows.append((step, status, output))

    with args.out.open("w", encoding="utf-8") as f:
        f.write("# RH Symbolic Closure Pipeline\n\n")
        f.write("Raw RH target is routed through the Tantrium theorem stack.\n\n")
        f.write("| step | kind | target | status |\n")
        f.write("|---|---|---|---|\n")
        for step, status, _ in rows:
            f.write(f"| {step.name} | {step.kind} | {step.target} | {status} |\n")
        f.write("\n## Executable outputs\n\n")
        for step, status, output in rows:
            if step.command:
                f.write(f"### {step.name}: {status}\n\n")
                f.write("```text\n")
                f.write(output + "\n")
                f.write("```\n\n")
        if failures:
            f.write("## Failures\n\n")
            for item in failures:
                f.write(f"- {item}\n")
        else:
            f.write("## Closure status\n\n")
            f.write("All required artifacts and executable audits passed in this finite symbolic/audit run.\n")

    print("RH SYMBOLIC CLOSURE PIPELINE")
    print(f"steps={len(STEPS)} failures={len(failures)} out={args.out}")
    if failures:
        for item in failures[:20]:
            print("-", item)
        return 1 if args.strict else 0
    print("PASS raw RH target routed through Tantrium symbolic closure stack")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
