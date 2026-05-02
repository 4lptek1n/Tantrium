"""Parameter search windows for theorem candidates."""
from __future__ import annotations


def search_window(deep: bool = False) -> dict[str, object]:
    return {
        "j": [1, 10 if deep else 8],
        "r": "0..j",
        "n": [0, 12 if deep else 8],
        "boundary_cases": ["r=0", "r=j", "j=7 K7 boundary"],
    }
