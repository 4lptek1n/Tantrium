"""Markdown reporting for recurrence campaigns."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def write_recurrence_report(
    out_dir: Path,
    inventory: dict[str, Any],
    qjr_tables: dict[str, Any],
    candidates: list[dict[str, Any]],
    ranking: dict[str, Any],
    verification: dict[str, Any],
    synthesis: dict[str, Any],
) -> None:
    lines = [
        "# Subresultant Recurrence Campaign Report",
        "",
        f"Status: `{synthesis['status']}`",
        f"Best candidate: `{synthesis['best_candidate']}`",
        f"Refined subgap: `{synthesis['refined_subgap']}`",
        "",
        "## Inventory",
        "",
        f"- Source files scanned: `{len(inventory['sources']['source_records'])}`",
        f"- Engine CSV files inventoried: `{len(inventory['engine_csv_files'])}`",
        f"- QJR rows generated: `{len(qjr_tables['rows'])}`",
        "",
        "## Ranked Recurrences",
        "",
    ]
    for item in ranking["ranked_candidates"]:
        lines.append(f"- `{item['candidate_id']}` score `{item['score']}`: {item['statement']}")
    lines.extend(
        [
            "",
            "## Verification",
            "",
            f"Finite checks passed: `{verification['all_finite_checks_passed']}`",
            "",
            "No theorem is promoted here. The remaining mathematical obstruction is identifying the normal-form recurrence with the true hidden H quotient extracted from the subresultant chain.",
        ]
    )
    (out_dir / "recurrence_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
