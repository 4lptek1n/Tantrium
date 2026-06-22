#!/usr/bin/env python3
"""Verify the ell=2 diagonal-residue TP backbone:
the binomial-origin conversion operator M_Delta (i-coordinate) is TP, and equals
L^Delta with L the nonnegative bidiagonal Pascal generator (Whitney/Loewner TP),
so by Cauchy-Binet the iterated conversion is TP at every depth. Exact arithmetic."""
import sympy as sp
from math import comb
from itertools import combinations

def toeplitz(D, n):
    return sp.Matrix([[comb(D, j-l) if j >= l else 0 for l in range(n)] for j in range(n)])

def all_minors_nonneg(M):
    h, w = M.shape; bad = tot = 0
    for o in range(1, min(h, w)+1):
        for ri in combinations(range(h), o):
            for ci in combinations(range(w), o):
                tot += 1
                if M[list(ri), list(ci)].det() < 0: bad += 1
    return bad, tot

def main():
    n = 7
    L = sp.Matrix([[1 if (j-l) in (0, 1) else 0 for l in range(n)] for j in range(n)])
    for D in [1, 2, 3, 4]:
        M = toeplitz(D, n)
        bad, tot = all_minors_nonneg(M)
        assert bad == 0, f"Delta={D} not TP"
        assert L**D == M, f"L^{D} != Toeplitz({D})"
        print(f"Delta={D}: TP (0/{tot} negative minors) and M_Delta == L^Delta  [OK]")
    print("Backbone verified: each descent layer = L^Delta is TP; Cauchy-Binet -> iterate TP.")

if __name__ == "__main__":
    main()
