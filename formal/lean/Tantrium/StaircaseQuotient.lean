import Tantrium.SubresultantRecurrence

namespace Tantrium

/- Source artifact:
  results/research_os/candidates/GENERAL_QUOTIENT_DEGREE_THEOREM.json -/

structure StaircaseQuotient where
  j : Nat
  r : Nat
  degree : Nat
deriving Repr

def expectedStaircaseQuotient (j r : Nat) : StaircaseQuotient :=
  { j := j, r := r, degree := qjrDegree j r }

theorem staircase_quotient_degree_candidate (j r : Nat) :
    (expectedStaircaseQuotient j r).degree = qjrDegree j r := by
  rfl

end Tantrium
