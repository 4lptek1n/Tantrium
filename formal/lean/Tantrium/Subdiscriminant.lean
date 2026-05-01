import Tantrium.Tau

namespace Tantrium

def subdiscriminant (_p : Poly) (_j : Nat) : Int := 0

-- Source: theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md
theorem tau_equals_subdiscriminant_statement (p : Poly) (j : Nat) :
    tauSymbol p j = subdiscriminant p j := by
  sorry

end Tantrium
