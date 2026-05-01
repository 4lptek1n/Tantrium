# Lean/Coq Formalization Roadmap

External formalization remains `PENDING`. This roadmap defines how to turn the
current Tantrium certificate stack into a formal proof development.

## Lean Module Plan

```text
Tantrium.Basic
Tantrium.Tau
Tantrium.Subdiscriminant
Tantrium.Sturm
Tantrium.DyadicTransport
Tantrium.DPositivity
Tantrium.AGLGV
Tantrium.RHChain
```

## Definition Order

1. Finite sequences, coefficient arrays, and polynomial normalization.
2. Determinants, Hankel matrices, and Vandermonde products.
3. Subdiscriminants and tau symbols.
4. Sturm pivot predicates.
5. AG/LGV path-family data structures.
6. D-positivity predicates and dyadic transport maps.
7. RH chain interface theorem using external classical assumptions.

## Easiest First Lemmas

```text
certificate hash consistency
finite determinant identity schemas
Vandermonde-square expansion statements
tau/subdiscriminant definitions
finite map injectivity statements for Gate A/B artifacts
```

## Hardest Lemmas

```text
all-parameter dyadic capacity
all-parameter AG/LGV path bijection
normalization from tau positivity to Sturm pivots
Jensen hyperbolicity to Laguerre-Polya closure
```

## Mathlib Connections

Use mathlib for:

```text
polynomial algebra
matrix determinants
finite sums
multisets and finite types
real-rooted polynomial predicates where available
```

Classical theorems that should be imported or separately formalized:

```text
Cauchy-Binet
LGV lemma
Sturm theorem
Polya-Jensen theorem
Laguerre-Polya characterization
```

The first formalization milestone should not attempt the full RH closure. It
should formalize the Tau/Subdiscriminant and AG/LGV bridge statements with
explicit assumptions.
