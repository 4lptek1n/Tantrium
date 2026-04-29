"""Log-det cumulant identities for the Positivity Engine."""

CUMULANT_IDENTITIES = {
    "a1": "L2",
    "a2": "L4 + L2^2/2",
    "a3": "L6 + L2*L4 + L2^3/6",
    "a4": "L8 + L2*L6 + L4^2/2 + L2^2*L4/2 + L2^4/24",
}


def identity(name):
    return CUMULANT_IDENTITIES[name]


def available_identities():
    return dict(CUMULANT_IDENTITIES)


def cumulant_levels():
    return ["L2", "L4", "L6", "L8"]
