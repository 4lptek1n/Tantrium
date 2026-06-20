# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims to
adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `[build-system]` (hatchling) so the package is installable/buildable reproducibly.
- PEP 621 metadata: classifiers, keywords, `project.urls`, `py.typed` marker.
- Tooling config in `pyproject.toml`: Ruff (lint + format), mypy, coverage.
- Pre-commit hooks (`.pre-commit-config.yaml`).
- GitHub Actions: CI (lint, type-check, test matrix 3.10–3.13, build), CodeQL,
  and a Release workflow publishing to PyPI via Trusted Publishing (OIDC).
- Dependabot for pip + GitHub Actions.
- Community files: CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CITATION, issue/PR
  templates, CODEOWNERS.

### Removed
- The natural-language layer (fitless LM / embeddings / transformer / Speaker /
  narration / conversation facades).
- The acquisition/learning machinery (growth, observe, ingest, researcher,
  cognition, pursue, text-relation extraction). The system computes over its
  existing manifold and does not autonomously acquire.

### Notes
- A software license has not yet been chosen; until a `LICENSE` is added the code
  is "all rights reserved". Choose one before the first PyPI release.

[Unreleased]: https://github.com/4lptek1n/tantrium/commits/main
