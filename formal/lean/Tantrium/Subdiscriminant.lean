import Tantrium.Tau
import Tantrium.TauSubdiscriminant

namespace Tantrium

open Finset

/- Source: theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md

The earlier `Poly`-level statement here was a vacuous placeholder: both
`tauSymbol` and `subdiscriminant` were defined as the constant `0`, so the
"identity" `tauSymbol p j = subdiscriminant p j` was a disguised `0 = 0`
discharged by `sorry`.

The genuine identity `tau_j = Disc_j(P)` is about the roots of `P`, and it is
now proved for real in `Tantrium.TauSubdiscriminant.det_momentMatrix`: the
Hankel determinant of the Newton power sums equals the discriminant. We
re-export it here under the original name so downstream files refer to the
real theorem rather than the placeholder. -/

/-- **tau = subdiscriminant** (principal case, normalization `c = 1`).

For a root system `x : Fin n → R`, the Hankel determinant of the Newton power
sums `s_{a+b} = ∑ i, (x i)^(a+b)` equals the `j`-th subdiscriminant in the top
case `j + 1 = n`, namely the discriminant `∏_{i<j} (x j - x i)²`.

This is a real, axiom-free proof (no `sorry`); see `det_momentMatrix`. -/
theorem tau_equals_subdiscriminant_statement
    {R : Type*} [CommRing R] {n : ℕ} (x : Fin n → R) :
    (momentMatrix x).det = (∏ i : Fin n, ∏ j ∈ Ioi i, (x j - x i)) ^ 2 :=
  det_momentMatrix x

end Tantrium
