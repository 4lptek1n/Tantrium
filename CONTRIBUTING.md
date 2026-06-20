# Contributing to Tantrium

Thanks for your interest in contributing! This document covers the workflow and
the conventions specific to this project.

## Development setup

```bash
git clone https://github.com/4lptek1n/tantrium
cd tantrium
python -m pip install -e ".[dev]"   # add ,chem ,vision ,nlp ,server as needed
pre-commit install                  # run lint/format on every commit
```

## Quality gates (run before opening a PR)

```bash
ruff check .            # lint
ruff format .           # format
pytest                  # tests (rdkit/spaCy tests skip if those extras are absent)
mypy                    # type check (informational; codebase is gradually typed)
```

CI runs the same checks across Python 3.10–3.13.

## Project conventions

- **Flat imports:** `from tantrium import ...` — there is no `tantrium.agi`.
- **The math kernel is the moat.** Code under `src/tantrium/core/`, `proof/`, and
  `algebra/` (RH / positivity / moments / Sturm / dyadic transport) is deterministic
  and load-bearing. Changes there require owner review and a clear justification —
  never refactor it toward a "lowest common denominator."
- **Tests are required** for behavior changes. Prefer structural fixtures over any
  network/data dependency. Keep them deterministic.
- **Don't commit** generated state or large data (`.tantrium/`, `results/agi/` are
  git-ignored). No secrets or credentials.

## Pull requests

1. Branch from `main`.
2. Keep the PR focused; fill in the PR template checklist.
3. Reference any related issues (`Closes #N`).
4. Ensure CI is green.

## Reporting bugs / requesting features

Use the issue templates. For security issues, see [SECURITY.md](SECURITY.md) — do
**not** open a public issue.
