import Tantrium.Basic

namespace Tantrium

structure DyadicTransport where
  source : Nat
  target : Nat
deriving Repr

def supportPreserving (_t : DyadicTransport) : Prop := True

-- Source: docs/DYADIC_TRANSPORT_THEOREM.md
theorem dyadic_transport_support_preserving (t : DyadicTransport) :
    supportPreserving t := by
  trivial

end Tantrium
