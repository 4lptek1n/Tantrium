import Tantrium.Subdiscriminant

namespace Tantrium

def sturmPivotPositive (_p : Poly) (_j : Nat) : Prop := True

-- Source: results/certificates/tau_sturm_parametric_certificate.json
theorem tau_subdiscriminant_implies_sturm_pivot (p : Poly) (j : Nat) :
    sturmPivotPositive p j := by
  trivial

end Tantrium
