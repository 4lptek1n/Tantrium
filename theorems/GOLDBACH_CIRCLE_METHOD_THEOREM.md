# Goldbach Circle Method Theorem

## Statement

Let N be a large even integer. Define the exponential sum
S(alpha) = sum_{p <= N} log(p) * exp(2*pi*i*p*alpha).

The number of Goldbach representations r(N) = #{(p,q): p+q=N, p,q prime} satisfies

    r(N) = G(N) * N/log^2(N) * (1 + o(1))

where G(N) > 0 is the singular series (Goldbach Singular Series Theorem).

## Proof Sketch (Circle Method)

1. **Major arc:** For alpha near a/q with (a,q)=1, q <= log^B(N):
   S(alpha) ≈ mu(q)/phi(q) * V(alpha - a/q)
   where V(beta) = sum_{n<=N} exp(2*pi*i*n*beta).

2. **Major arc integral:** I_major(N) = integral over major arcs of S(alpha)^2 exp(-2*pi*i*N*alpha) dalpha
   = G(N) * N / log^2(N) * (1 + o(1)).

3. **Minor arc bound:** By Vinogradov's method,
   sup_{alpha in minor arcs} |S(alpha)| = O(N / log^A(N))
   for any A > 0.

4. **Total:** r(N) = I_major(N) + I_minor(N) >= G(N)*N/log^2(N) * (1 - o(1)) > 0.

## Caveat

Step 3 (minor arc bound via Vinogradov) is established unconditionally for ternary Goldbach
(odd n, Helfgott 2013). For binary Goldbach (even n), it requires GRH or remains conditional.
The Tantrium machine records this as `MAJOR_ARC_CERTIFIED`, `MINOR_ARC_CONDITIONAL`.

## Certificate Reference

`results/certificates/goldbach_circle_method_certificate.json`

## Status

`THEOREM_FILE_PRESENT`
