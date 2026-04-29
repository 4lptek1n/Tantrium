from fractions import Fraction
from math import prod

# Candidate general-j fit for the second low-edge coefficient
# H_{d,j}(t)=sum_k a_k^{(j)}(n)t^k, n=d-j-1.
# This script records the current local fit extracted from exact/cached laws.


def alpha(j):
    return Fraction((j - 1) * (675*j**3 + 2205*j**2 + 2558*j - 904), 1536)


def beta(j):
    return Fraction((j - 1) * (345*j**4 + 1456*j**3 + 2627*j**2 + 980*j - 452), 768)


def gamma(j):
    return Fraction((j - 1) * (4439*j**4 - 25342*j**3 + 103833*j**2 - 183786*j + 126960), 1536)


def a2_candidate(j, n):
    return alpha(j)*n*n + beta(j)*n + gamma(j)


def main():
    for j in range(1, 8):
        print(f"j={j}")
        print("  alpha =", alpha(j))
        print("  beta  =", beta(j))
        print("  gamma =", gamma(j))
        print("  samples:", [a2_candidate(j, n) for n in range(3)])


if __name__ == "__main__":
    main()
