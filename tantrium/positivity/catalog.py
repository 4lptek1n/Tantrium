"""Coefficient catalog checkpoint for the Positivity Engine."""

CLEAN_FRONTIER = {
    "K": 6,
    "J": 7,
    "N": 7,
    "failures": 0,
    "radar": "a0..a6 clean through j=7, failures=0",
}


def frontier_lines():
    return [f"a{k}: coefficient-positive through j=7" for k in range(7)]


def current_radar():
    return CLEAN_FRONTIER["radar"]
