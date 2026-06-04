from __future__ import annotations

import csv
import importlib.util
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "results" / "engine"
RUNNER = ROOT / "tools" / "run_positivity_engine_v1.py"

spec = importlib.util.spec_from_file_location("v1", RUNNER)
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)


def fmt(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def q_coeff(m, ell, x):
    d = x + 2
    sums = v1.newton_sums(d, m, 2 * ell)
    return Fraction(((-1) ** m) * sums[m][2 * ell])


def finite_diffs(vals):
    level = list(vals)
    out = []
    while level:
        out.append(level[0])
        level = [level[i + 1] - level[i] for i in range(len(level) - 1)]
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def main(max_m=12, max_ell=4, xmax=18):
    ENGINE.mkdir(parents=True, exist_ok=True)
    d_rows = []
    a_rows = []
    summary = []
    for m in range(max_m + 1):
        for ell in range(max_ell + 1):
            vals = [q_coeff(m, ell, x) for x in range(xmax + 1)]
            D = finite_diffs(vals)
            nz = [(a, c) for a, c in enumerate(D) if c]
            if not nz:
                continue
            degree = max(a for a, c in nz)
            neg = [(a, c) for a, c in nz if c < 0]
            for a, c in nz:
                d_rows.append({"m": m, "ell": ell, "a": a, "D": fmt(c)})
            for p in range(degree + 1):
                for s in range(degree + 1 - p):
                    c = D[p + s]
                    if c:
                        a_rows.append({"m": m, "ell": ell, "p": p, "s": s, "a": p + s, "A": fmt(c)})
            summary.append({"m": m, "ell": ell, "degree": degree, "D_nonzero": len(nz), "D_negative": len(neg)})

    outputs = [
        ("newton_D_binomial_table.csv", ["m", "ell", "a", "D"], d_rows),
        ("newton_A_double_binomial_table.csv", ["m", "ell", "p", "s", "a", "A"], a_rows),
        ("newton_moment_summary.csv", ["m", "ell", "degree", "D_nonzero", "D_negative"], summary),
    ]
    for name, fields, rows in outputs:
        with (ENGINE / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(rows)

    report = [
        "Newton moment Vandermonde checkpoint",
        "",
        "x = d - 2 = n + (j - 1)",
        "Q_m_ell(x) = coeff lambda^(2 ell) in (-1)^m s_m",
        "Q_m_ell(x) = sum_a D(m,ell,a) binom(x,a)",
        "A(m,ell,p,s) = D(m,ell,p+s)",
        "",
        f"D rows: {len(d_rows)}",
        f"A rows: {len(a_rows)}",
        f"negative D rows: {sum(1 for r in d_rows if Fraction(r['D']) < 0)}",
    ]
    (ENGINE / "newton_moment_vandermonde_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
