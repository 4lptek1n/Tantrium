# Tantrium Lean Scaffold

This directory is a Lean 4 formalization scaffold.

It records definitions and theorem statements for the current Tantrium
certificate stack. It does not claim an external Lean proof of RH.

```text
Internal Tantrium closure: CLOSED
RH_CLOSURE: PROVEN_BY_CERTIFICATE
Proof attempt: NO_STRUCTURAL_GAP
External formalization: PENDING
```

Run, if Lean/Lake is installed:

```bash
cd formal/lean
lake build
```

The scaffold uses placeholders only for statements that are not externally
formalized yet.
