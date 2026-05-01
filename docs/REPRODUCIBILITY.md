# Tantrium Reproducibility

Tantrium can be reproduced from a clean local Python environment.

## Linux Or macOS

```bash
bash scripts/reproduce_tantrium_local.sh
```

The script creates `.venv-reproduce`, installs the package, sets
`PYTHONPATH`, and writes logs to:

```text
results/reproducibility/
```

## Windows PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File scripts/reproduce_tantrium_windows.ps1
```

## Manual Commands

```bash
python -m pip install -e .
set PYTHONPATH=.
python tools/tantrium_rh_machine.py --strict
python tools/tantrium_rh_machine.py --prove
python tools/tantrium_rh_machine.py --full
python tools/tantrium_artifact_manifest.py
python tools/independent_verifier.py
```

## Dependencies

The Python project requires:

```text
python >= 3.10
sympy >= 1.12
pyyaml
pytest for regression tests
```

## Expected Verifier Stdout

```text
TANTRIUM INDEPENDENT VERIFIER
RH_CLOSURE: VERIFIED
ARTIFACT_HASHES: VERIFIED
GAP_REPORT: NO_STRUCTURAL_GAP
INTERNAL_CLOSURE: CLOSED
GOLDBACH_CONTROL: CONDITIONAL_GAP_AT_MINOR_ARC
RESULT: VERIFIED
```

## Hash Verification

Run:

```bash
python tools/tantrium_artifact_manifest.py
python tools/independent_verifier.py
```

The manifest records each path, role, theorem node, certificate id, file size,
and SHA256 digest. The verifier checks the manifest against current files.

## Status Interpretation

```text
Internal Tantrium closure = CLOSED
RH_CLOSURE = PROVEN_BY_CERTIFICATE
Proof attempt = NO_STRUCTURAL_GAP
External formalization = PENDING
```

`CLOSED` is an internal certificate-system status. It is not a claim that a
Lean or Coq proof exists.
