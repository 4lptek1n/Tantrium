namespace Tantrium

abbrev Coeff := Int
abbrev Poly := List Coeff

structure CertificateRef where
  path : String
  sha256 : String
deriving Repr

def ExternalFormalizationStatus : String := "PENDING"
def InternalTantriumClosure : String := "CLOSED"

end Tantrium
