# Tantrium Roadmap

Tantrium is a long-running research and product project. The immediate goal is to turn the Sturm–Toda discovery into a reproducible structure-discovery engine.

## Phase 0 — Repository Stabilization

- [x] Add project manifesto and README.
- [x] Add Sturm–Toda case study notes.
- [x] Add Lah shadow notes.
- [ ] Add reproducible Python engine.
- [ ] Add test suite.
- [ ] Add cached verification summaries.

## Phase 1 — Reproducible Case Study

Target: make the first discovery fully reproducible from code.

- Generate `P_{lambda,d}` from the exponential generating function.
- Compute normalized Sturm chains.
- Extract pivots `rho_{d,j}`.
- Factor pivots into hidden factors `H_{d,j}`.
- Verify the cross-ratio form.
- Verify the staircase ramp law for `j <= 5`.
- Verify the Lah shadow limit.

## Phase 2 — Proof Skeleton

Target: convert computational structure into a written proof path.

- Formalize the scaled epsilon expansion.
- Express `H_{d,j}` as normalized principal subresultants.
- Derive the determinant/cross-ratio identity.
- Identify the positivity mechanism.
- Search for a cancellation-free or path-counting model.

## Phase 3 — Discovery Engine

Target: generalize from one case study to a framework.

- Add a generic `System` interface.
- Add operator-based object generation.
- Add symbolic invariant extraction.
- Add pattern mining utilities.
- Add conjecture formatting.
- Add verification reports.

## Phase 4 — Product Direction

Possible product directions:

1. Mathematical structure discovery.
2. Stability certification for symbolic systems.
3. Spectral safety tools for AI/ML models.
4. Scientific discovery workflows combining computation, algebra, and verification.

## Guiding Principle

Do not sell guesses. Expose structure and certify it.
