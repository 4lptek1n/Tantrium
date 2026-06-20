# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

Instead, report privately via GitHub's
[private vulnerability reporting](https://github.com/4lptek1n/tantrium/security/advisories/new)
(Security → Advisories → "Report a vulnerability"). We aim to acknowledge reports
within a few days and will coordinate a fix and disclosure timeline with you.

## Supported versions

This project is in early development (0.x). Only the latest `main` is supported.

## Supply-chain practices

Releases follow [Scientific-Python SPEC-8](https://scientific-python.org/specs/spec-0008/):

- PyPI publishing uses **Trusted Publishing (OIDC)** — no long-lived tokens.
- Publishing runs in a protected GitHub Environment requiring manual approval.
- Release artifacts carry **signed build-provenance attestations** (PEP 740).
- Dependencies and GitHub Actions are monitored by Dependabot; the codebase is
  scanned with CodeQL.
