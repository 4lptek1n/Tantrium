# Dyadic Transport Theorem

## Status

This document is the current formal blueprint for the final Tantrium induction step. It records the theorem we must turn from a verified finite-layer pattern into a uniform proof.

It does **not** by itself claim that the Riemann Hypothesis is proved. The point of this file is sharper: it isolates the exact universal transport lemma whose proof would close global D-positivity and therefore complete the Tantrium route.

---

## 1. The target theorem

For every layer `ell >= 1`, every admissible D-seed satisfies

```text
D(m, ell, a) >= 0.
```

The expected mechanism is **dyadic transport**: every negative deficit cell in the connected cumulant kernel is injected into positive source cells through a finite family of combinatorial maps with weights

```text
beta = 2^(-r).
```

The final theorem must give an explicit uniform depth bound

```text
r <= c(ell, m, a)
```

and must prove that the induced source usage never overspends the positive cone.

---

## 2. Empirical and structural base mechanisms

### 2.1 ell=1: Split-Pair Dominance

The first layer is governed by the primitive Delta split

```text
Delta_n = Q_n - M_n.
```

The essential feature is not the notation, but the shape:

```text
positive top family - one-step mixed family >= 0.
```

The associated transport map is `split_pair`. In the Foundry implementation this map must be allowed to use all sources; it is not a purely q-monotone map.

### 2.2 ell=2: Diagonal Residue Theorem

The second layer reveals the diagonal coordinate

```text
m = max_k(r) - k
```

and the dyadic scale

```text
8^(-m) = 2^(-3m).
```

This is the first place where transport is not merely local. It is a diagonal residue transfer: mass travels along a structured residue family, paying three half-losses per depth step.

The primitive maps are the same conceptual maps as ell=1, but composed:

```text
Wrapping + Root-Top + Split-Pair.
```

### 2.3 ell=3: Higher Split-Family Dominance

The third layer exposes the higher Delta operator. The key factorization has the schematic form

```text
K_3 = sum c(q,diff) * Y^diff * q_d^q * (1 - Y q_{d-1})^(q/2).
```

The factor

```text
(1 - Y q_{d-1})^(q/2)
```

is the higher split-family analogue of the ell=1 Delta and ell=2 residue families.

The `qdiff` interior model closes the principal higher-layer obstruction. The special q=20 obstruction was closed by internal split-family dominance with maximum observed half-power

```text
r <= 2.
```

This provides the first concrete evidence that higher layers have stronger internal supply than the lower diagonal-residue model suggests.

### 2.4 ell=4 and ell=5: model dispatch evidence

The Foundry no longer uses one transport model globally. The correct object is a dispatch family:

```text
ell = 1                  -> split_pair
ell = 2                  -> diagonal_residue
ell >= 3, low q <= 10    -> low_q_family / q6_low_family
ell >= 3, top q = max_q  -> boundary_family
ell >= 3, interior q     -> qdiff
```

The important structural correction is model-aware source filtering:

```text
split_pair, diagonal_residue, low_q_family, boundary_family -> source_policy = all
qdiff                                                       -> source_policy = q_ge_target
```

The earlier failures of the automatic scan were not evidence against transport. They came from deleting valid non-q-monotone sources before the correct model was selected.

---

## 3. Abstract transport language

A layer kernel is viewed as a signed finite measure on cells

```text
cell = (ell, q, p, Y, diff, auxiliary indices)
```

where positive cells are sources and negative cells are deficits.

A transport certificate is a directed weighted multigraph

```text
source_cell --2^(-r)--> deficit_cell
```

such that

```text
sum_delivered(deficit) >= demand(deficit)
sum_raw_used(source)   <= mass(source).
```

A model is admissible if its edges are induced by one of the primitive maps or their permitted compositions.

Primitive maps:

```text
W  = Wrapping
R  = Root-Top
B  = Split-Pair
DR = Diagonal Residue composition
QD = qdiff interior split
LQ = low-q split-family map
BD = top-boundary split-family map
```

Each map has a dyadic cost:

```text
cost(edge) = number of half-losses = r.
```

The transport theorem must prove that the total cost is bounded uniformly by a combinatorial depth function and that the capacity inequalities hold in every layer.

---

## 4. Uniform Lift Lemma

### Lemma target

For every `ell = k+1`, the connected cumulant kernel admits a split-family decomposition

```text
Layer(k+1)
  = PositiveSources(k+1)
    - Deficits(k+1)
    + Residue(k+1),
```

such that

```text
Deficits(k+1)
  <= DyadicTransport(PositiveSources(k+1))
     + PositiveCone(D layers <= k).
```

The dyadic transport uses only the primitive family

```text
Wrapping, Root-Top, Split-Pair,
Diagonal Residue, qdiff interior split,
low-q split, boundary split.
```

The residue must be a nonnegative combination of lower-layer D-seeds once layers `<= k` are known positive.

### Equivalent operational form

For every deficit cell `d` in layer `k+1`, there is a finite list of source cells `s_i` and dyadic costs `r_i` such that

```text
mass(d) <= sum_i 2^(-r_i) mass(s_i)
```

and globally

```text
sum_{d using s} raw_used(s -> d) <= mass(s).
```

This is exactly the certificate condition implemented by the Foundry certificate object.

---

## 5. Why the lift should exist

The observed layers show the same structural law in different coordinates.

### 5.1 Delta law

Every successful layer produces a positive top family and a one-step mixed family:

```text
Top(q) - Mixed(q-1, depth+1).
```

In ell=1 this is `Delta_n`. In ell=2 it appears as diagonal residue. In ell=3 it appears as the factor

```text
(1 - Y q_{d-1})^(q/2).
```

The conjectural uniform statement is that every connected cumulant layer contains this Delta law after the correct internal split-family coordinates are chosen.

### 5.2 Dyadic loss law

The only denominators introduced by the Hermite depth identity are powers of two:

```text
d = q_d - (Y/2) q_d q_{d-1}.
```

Therefore every transport loss should be dyadic. Higher layers may introduce more split choices, but not new prime denominators in the transport weights.

### 5.3 Boundary and low-q law

The interior q-region is governed by qdiff. Low q and top q are boundary regions where q-monotone filtering is invalid. These regions require separate maps:

```text
low_q_family
boundary_family
```

The uniform theorem should therefore not state that one model works everywhere. It should state that the dispatch family covers all regions with compatible dyadic costs.

---

## 6. Induction proof skeleton

### Base

The base mechanisms are:

```text
ell=1: split_pair
ell=2: diagonal_residue
ell=3: higher split-family / qdiff interior closure
```

The Foundry evidence through ell=4 and ell=5 supports the same dispatch family.

### Induction hypothesis

Assume for every layer `j <= k` all D-seeds are nonnegative and every obstruction recorded by the layer kernel admits a dyadic transport certificate.

### Induction step

Consider layer `k+1`.

1. Generate the connected cumulant kernel `L_{2k+2}`.
2. Reduce it to the Hermite q-basis.
3. Apply the mixed-depth identity

```text
d = q_d - (Y/2) q_d q_{d-1}.
```

4. Decompose the resulting signed kernel into:

```text
interior qdiff region
low-q split-family region
top-boundary region
lower-layer residue
```

5. Apply the corresponding transport map to each region.
6. The residue is in the positive cone generated by layers `<= k`, hence is nonnegative by the induction hypothesis.
7. The transport inequalities cover every deficit without overspending sources.

Therefore every D-seed in layer `k+1` is nonnegative.

This completes the induction once the Uniform Lift Lemma is made unconditional.

---

## 7. Consequence for the Tantrium chain

If the Uniform Lift Lemma is proved, then global D-positivity follows:

```text
D(m, ell, a) >= 0 for all admissible (m, ell, a).
```

The intended chain is then:

```text
D-positivity
  -> Newton moment positivity
  -> Hankel / tau determinant positivity
  -> cumulant and coefficient positivity
  -> positive Sturm pivot coefficients
  -> Jensen polynomial hyperbolicity
  -> Polya-Jensen conclusion
```

This is the point at which the Tantrium route would become a complete RH proof route, provided every implication in the chain is formalized without hidden regularity or limiting assumptions.

---

## 8. What remains to make this a proof

The following pieces must be written as formal lemmas rather than computational observations.

### 8.1 Dispatch completeness

Prove that every cell in every layer belongs to exactly one of the regions:

```text
ell=1 base
ell=2 diagonal residue
ell>=3 low q
ell>=3 interior
ell>=3 top boundary
lower-layer residue
```

### 8.2 Map admissibility

For each model prove that its edges are induced by legitimate algebraic injections:

```text
split_pair
 diagonal_residue
qdiff
low_q_family
q6_low_family
boundary_family
```

### 8.3 Capacity bound

Prove the global no-overspend inequality:

```text
used(source) <= mass(source)
```

not merely cellwise coverage.

### 8.4 Residue positivity

Prove that the leftover term after transport lies in

```text
PositiveCone(D layers <= k).
```

### 8.5 Explicit dyadic depth function

Give the closed form of

```text
c(ell, m, a)
```

or a sufficient upper bound that is strong enough to make the capacity inequalities hold.

---

## 9. Executable targets

The proof program should be reflected in tools:

```text
tools/uniform_lift_lemma_tester.py
```

should test the lift across layers and record the first failure coordinate.

```text
tools/tantrium.py certify --scan all --max-ell N --model auto
```

should remain the finite-layer certificate sweep.

The expected output format is either

```text
No obstruction found in scanned kernels.
```

or

```text
First obstruction: ell=X q=Y model=Z errors=[...]
```

---

## 10. Final formulation

**Dyadic Transport Theorem.** If the dispatch completeness, map admissibility, capacity bound, residue positivity, and explicit dyadic depth lemmas hold for the primitive transport family, then every D-seed in every layer is nonnegative.

**Uniform Lift Lemma.** The connected cumulant kernel in layer `k+1` decomposes into transport-coverable split-family deficits plus a positive cone of lower-layer D-seeds, with dyadic loss bounded by an explicit combinatorial depth function.

The remaining work is to remove the conditional word **if** from these two statements.
