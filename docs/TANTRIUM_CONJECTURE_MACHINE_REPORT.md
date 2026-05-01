# Tantrium Conjecture Machine Report

The conjecture machine gives Tantrium a common interface for multiple
mathematical targets. This is a control against blind `PASS` behavior.

| Problem | Status | First Gap | Main Certificate | Notes |
|---------|--------|-----------|------------------|-------|
| `rh` | `INTERNAL_CLOSED` | none | `results/certificates/rh_symbolic_closure_certificate.json` | Internal Tantrium closure is `CLOSED`; external formalization is `PENDING`. |
| `goldbach` | `CONDITIONAL_GAP` | `MINOR_ARC_BOUND` | `results/certificates/goldbach_circle_method_certificate.json` | The control problem remains conditional at the expected minor-arc bound. |
| `lah` | `CERTIFIED_SCHEMA` | none | `math/gate_a_verify.py` | Historical Gate A/Lah schema and finite scripts. |
| `hankel` | `CERTIFIED_SCHEMA` | none | `results/certificates/ag_lgv_parametric_certificate.json` | AG/LGV and tau machinery. |
| `coefficient_positivity` | `ATLAS_DRIVEN` | `FIRST_UNCERTIFIED_ATLAS_FRONTIER` | `results/atlas/manifest.json` | Atlas-driven frontier, not a blind closure. |

Run:

```bash
python tools/tantrium_conjecture_machine.py --problem rh --full
python tools/tantrium_conjecture_machine.py --problem goldbach --full
python tools/tantrium_conjecture_machine.py --problem lah --full
python tools/tantrium_conjecture_machine.py --problem hankel --full
python tools/tantrium_conjecture_machine.py --problem coefficient_positivity --full
```
