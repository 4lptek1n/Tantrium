# Goldbach Singular Series Positivity Theorem

## Statement

For every even integer n > 2, the singular series

    G(n) = prod_{p | n, p>2} (p-1)/(p-2)  *  prod_{p prime, p>2} (1 - 1/(p-1)^2)

satisfies G(n) > 0.

Furthermore, G(n) >= C > 0 for an explicit constant C independent of n.

## Proof Sketch

1. **Product formula:** G(n) is a product of local factors, each > 0.
   - For primes p | n with p > 2: factor = (p-1)/(p-2) > 1.
   - For primes p ∤ n with p > 2: factor = (1 - 1/(p-1)^2) ∈ (0,1).
2. **Convergence:** The product over p ∤ n converges absolutely (ratio test).
3. **Positivity:** Each factor is strictly positive; infinite product of positive terms
   bounded away from 0.
4. **Lower bound:** G(n) >= prod_{p>2} (1 - 1/(p-1)^2) = C_0 > 0 (Mertens-type estimate).

## Certificate Reference

`results/certificates/goldbach_singular_series_certificate.json`

## Status

`THEOREM_FILE_PRESENT`
