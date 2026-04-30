# The Tantrium Positivity Engine: A Structural Attack on the Riemann Hypothesis via Jensen-Sturm Chains and Log-Det Cumulants

## Abstract

This manuscript records the current state of the Tantrium program: a structural positivity program aimed at the Riemann Hypothesis through the Pólya-Jensen-Sturm route. The central idea is to replace a direct attack on the zero set of the Riemann xi-function by a positivity problem for normalized Hankel-subdiscriminant factors

```text
H_{d,j}(t) = tau_{d,j}(t) / tau_{d,j}(0),
```

where

```text
tau_{d,j}(t) = det[s_{a+b}(t)]_{a,b=0}^{j}.
```

The program reduces Jensen hyperbolicity to sign-control of Sturm pivots, then seeks to prove that the relevant pivot factors have positive coefficients. The computational and structural engine developed for this purpose, the Tantrium Positivity Engine, combines tau generation, coefficient atlases, log-det cumulants, failure hunting, and split-family dominance certificates.

The current record contains several structural victories: the tau-subdiscriminant bridge, the universal cross-ratio identity, the log-det cumulant dictionary for the coefficients of `H_{d,j}`, atlas evidence for coefficient positivity through significant finite frontiers, and layer-by-layer positivity mechanisms for the `D(m, ell, a)` seed program. In particular, the ell=2 layer produced a diagonal residue mechanism with dyadic transport, and the ell=3 layer has been reduced to a higher split-family dominance problem with an explicit q=20 internal split-family certificate.

This document is deliberately precise about status. It does not claim that the Riemann Hypothesis is already proved. Rather, it records a coherent structural path, the verified parts of that path, and the remaining uniformization problem needed to turn the current finite and local certificates into a global theorem.

---

## 1. Introduction

### 1.1. The Riemann Hypothesis and the positivity strategy

The Riemann Hypothesis asserts that all nontrivial zeros of the Riemann zeta-function lie on the critical line. A classical route toward this statement passes through the completed xi-function. If one can show that the relevant entire function has only real zeros after the standard change of variables, then the Riemann Hypothesis follows.

The Tantrium program follows the Pólya-Jensen philosophy: instead of studying the zeros of the xi-function directly, study the hyperbolicity of Jensen polynomials attached to its Taylor coefficients. If every required Jensen polynomial is hyperbolic, then the limiting entire function has only real zeros.

The question is therefore transformed:

```text
RH
  <- real-rootedness of xi-side entire function
  <- hyperbolicity of Jensen polynomials J^{d,n}
  <- positivity of Sturm-chain pivots
  <- coefficient positivity of hidden factors H_{d,j}(t).
```

The guiding reduction is that Sturm hyperbolicity can be certified if the normalized pivot factors `H_{d,j}(t)` stay positive on the relevant parameter domain. The strongest available way to guarantee this is coefficient positivity:

```text
H_{d,j}(t) in R_{>0}[t].
```

This is the Global Coefficient Positivity Program.

### 1.2. The distinctive contribution of the Tantrium program

The distinctive feature of this program is that the positivity problem is not treated as a brute-force numerical claim. It is attacked structurally through three interlocking mechanisms:

1. **Tau-subdiscriminant structure.** The Sturm pivots are normalized Hankel determinants, and those determinants are subdiscriminants.
2. **Log-det cumulants.** The coefficients of `H_{d,j}` are controlled by cumulants `L_2, L_4, L_6, ...` through an exponential dictionary.
3. **D-seed positivity.** The underlying positive source is expressed in terms of seed objects `D(m, ell, a)` organized by an `ell`-layer hierarchy.

The Tantrium Positivity Engine is the computational and conceptual system that makes this program executable. It does not merely compute isolated coefficients. It generates atlases, searches for failures, extracts cumulant laws, and builds candidate dominance certificates.

### 1.3. Status of the program

The program currently has:

- a tau-Hankel formulation of Sturm pivots;
- a universal cross-ratio identity connecting successive pivots;
- closed and verified formulas for low coefficients;
- atlas evidence for positivity across substantial finite windows;
- structural layer victories for ell=0 and ell=1;
- a diagonal residue mechanism for ell=2;
- a higher split-family certificate for the q=20 obstruction in ell=3.

The remaining decisive task is **uniformization**: the local and finite split-family certificates must be upgraded into a global theorem valid for all relevant parameters.

---

## 2. Theoretical Architecture

### 2.1. Jensen polynomials and Sturm chains

Let `J^{d,n}(X)` denote the Jensen polynomial of degree `d` associated with the relevant coefficient sequence at shift `n`. The Pólya-Jensen route asks for hyperbolicity of these polynomials.

For a real polynomial, hyperbolicity can be studied by its Sturm chain. In the Tantrium formulation, the nontrivial pivot factors in the Sturm chain are encoded by normalized polynomials

```text
H_{d,j}(t),
```

where `j` indexes the Sturm/subdiscriminant level and `t` is the square of the transition parameter.

The operational goal is:

```text
H_{d,j}(t) > 0 for t >= 0.
```

A sufficient condition is coefficient positivity:

```text
H_{d,j}(t) = sum_k a_k^{(j)} t^k,
qquad a_k^{(j)} > 0.
```

This turns a real-rootedness problem into a structured positivity problem.

### 2.2. Tau determinants and subdiscriminants

The pivot factors are encoded by Hankel tau determinants. Let `s_m(t)` be the Newton sums of the associated polynomial family. Define

```text
tau_{d,j}(t) = det[s_{a+b}(t)]_{a,b=0}^{j}.
```

The normalized hidden factor is

```text
H_{d,j}(t) = tau_{d,j}(t) / tau_{d,j}(0).
```

The normalization is explicit at `t=0`:

```text
tau_{d,j}(0) = 2^{-j(j+1)/2} prod_{m=0}^{j} (d-m)^{j+1-m}.
```

The theoretical architecture rests on three lemmas.

#### Lemma A: tau equals subdiscriminant

The Hankel determinant `tau_{d,j}` is the relevant subdiscriminant of the polynomial family. This connects the moment/Newton-sum formulation to Sturm theory.

#### Lemma B: Desnanot-Jacobi on Hankel minors

Hankel minors satisfy a Desnanot-Jacobi/Dodgson condensation identity. This identity gives recursive control over adjacent determinant levels.

#### Lemma C: subresultant PRS bridge

The subdiscriminant chain matches the subresultant polynomial remainder sequence after normalization. This bridges the determinant formulation and the actual Sturm-chain pivots.

Together, these yield the universal cross-ratio identity.

### 2.3. The universal cross-ratio identity

The key normalized relation is

```text
rho_{d,j}(t)
  = ((d-j)/2) * H_{d,j-2}(t) H_{d,j}(t) / H_{d,j-1}(t)^2.
```

This identity is the first global organizing law of the pivot system. It says that the Sturm pivot ratios are not independent: they are controlled by adjacent normalized tau factors.

The positivity implication is direct. If the family `H_{d,j}` is positive on the relevant domain, then the cross-ratio factors preserve positivity through the Sturm chain.

### 2.4. Global Coefficient Positivity

The central theorem target is:

```text
Global Coefficient Positivity Theorem.
For all admissible d,j,k,
  a_k^{(j)}(d) > 0
where
  H_{d,j}(t) = sum_k a_k^{(j)}(d) t^k.
```

If this theorem holds, then

```text
H_{d,j}(t) > 0 for t >= 0,
```

and the Sturm-chain obstruction is removed.

### 2.5. Log-det cumulants

A central breakthrough was to stop expanding raw determinants directly and instead work with the logarithm:

```text
log(H_{d,j}(t)) = L_2 t + L_4 t^2 + L_6 t^3 + L_8 t^4 + ...
```

The coefficient-cumulant dictionary is:

```text
a_1 = L_2,

a_2 = L_4 + L_2^2/2,

a_3 = L_6 + L_2 L_4 + L_2^3/6,

a_4 = L_8 + L_2 L_6 + L_4^2/2
          + L_2^2 L_4/2 + L_2^4/24.
```

This changed the nature of the problem. Individual cumulants may have signs, but the exponential recombination can be positive. The positivity source is therefore not visible in raw traces alone; it appears through structured cumulant recombination.

Known low-level results include:

```text
a_1(d,j) = j(45dj + 51d - 22j^2 - 48j - 26) / 48.
```

In the variable `n = d-j-1`, this becomes a manifestly positive expression for admissible parameters.

---

## 3. The Tantrium Positivity Engine

### 3.1. The D-seed program

The coefficient positivity problem is further reduced to a hierarchy of seed quantities

```text
D(m, ell, a).
```

Here `ell` indexes the layer of the positivity problem. The intended chain is:

```text
D-positivity
  -> Newton-sum positivity
  -> Hankel/total positivity
  -> positivity of H_{d,j}
  -> Sturm positivity
  -> Jensen hyperbolicity.
```

The layer structure gives the proof campaign its battlefield:

```text
ell=0: base positivity
ell=1: split-pair dominance
ell=2: diagonal residue dominance
ell=3: higher split-family dominance
ell>=4: dyadic transport hierarchy
```

### 3.2. Engine architecture

The Tantrium Positivity Engine is organized as a research operating system.

```text
core/
  polynomial generation
  Newton sums
  Hankel tau determinants
  Sturm pivots

positivity/
  coefficient atlas
  cumulant engine
  failure hunter
  moment/path search
  certificate builder

tools/
  batch runners
  ell-layer reducers
  dominance testers

results/
  atlases
  cumulants
  kernels
  certificates

docs/
  theorem status
  layer proofs
  architecture notes
```

The key workflow is:

```text
Newton sums
  -> Hankel tau determinant
  -> normalized H_{d,j}
  -> coefficient atlas
  -> log-det cumulant dictionary
  -> failure search
  -> layer dominance certificate.
```

### 3.3. Atlas and failure hunting

The atlas layer scans triples `(k,j,n)` and records the sign of coefficients. A representative clean frontier recorded by the program is:

```text
a_0,...,a_6 clean through j <= 7, n <= 7,
failures = 0.
```

This is not a proof, but it is crucial evidence. More importantly, the atlas guides the proof search. It shows where signs remain stable, where denominators arise, which coordinates simplify, and where candidate dominance mechanisms should be looked for.

Failure hunting is equally important. A single negative coefficient would destroy the global conjecture in its naive form. The engine therefore treats both outcomes as useful:

```text
failure found     -> locate true boundary;
failure not found -> strengthen structural hypothesis.
```

### 3.4. Cumulant discovery loop

The cumulant engine fits and verifies formulas for `L_2, L_4, L_6, ...`. The key discovery is that high-complexity trace pieces can collapse into low-degree polynomial laws after summation.

For example, attempts to solve individual trace terms in `L_4` were unwieldy, but their total simplified into a manageable law. This taught a major methodological lesson:

```text
The structure is not in isolated trace fragments;
the structure is in their cumulant recombination.
```

---

## 4. The D-Positivity War: Structural Victories

### 4.1. The base layer ell=0

The ell=0 layer is the structural base. It fixes the base signs and establishes the initial positive seed behavior. In the proof hierarchy, ell=0 provides the ground layer from which split families and residue mechanisms are built.

At this layer the positivity is direct: no serious transport is required. It is the analogue of the constant positive floor in the later dominance arguments.

### 4.2. The first layer ell=1: split-pair dominance

At ell=1 the first nontrivial cancellation appears. The central object is a Delta-type difference

```text
Delta_n = Q_n - M_n.
```

The proof mechanism uses split-pair dominance. Negative contributions are paired with positive sources through explicit injections. Two named injections organize the proof:

```text
Wrapping injection,
Root-Top injection.
```

The key lesson of ell=1 is that positivity is not termwise. It is dominance by structured transport. This insight becomes decisive for ell=2 and ell=3.

### 4.3. The second layer ell=2: diagonal residue theorem

The ell=2 layer was the first major obstruction. Several natural approaches failed:

- scalar ratio dominance was too crude;
- simple pairwise cancellation did not see the correct geometry;
- fixed coordinate fits missed the moving boundary;
- naive total positivity arguments did not expose the needed residue signs.

The decisive coordinate was

```text
m = max_k(r) - k.
```

This diagonal coordinate revealed the right residue structure. The transport constant that emerged was

```text
8^{-m} = 2^{-3m}.
```

This constant reflects three half-weight transfers combined through the ell=2 split-pair geometry. The final statement is the diagonal residue theorem: after moving to the right diagonal coordinate, the residual expression `S_m(i)` is nonnegative term by term or by positive path-family expansion.

The ell=2 proof therefore has the form:

```text
raw signed field
  -> diagonal coordinate m
  -> dyadic transport with 8^{-m}
  -> nonnegative residue S_m(i)
  -> ell=2 closed.
```

This was the first convincing sign that the D-seed program had the right architecture.

### 4.4. The third layer ell=3: higher split-family dominance

The ell=3 layer is more complex. The kernel must pass through multiple reductions:

```text
ell=3 cumulant kernel
  -> R_j monomial kernel
  -> q_d Hermite kernel
  -> mixed-depth q_d/q_{d-1} kernel
  -> paired Delta field
  -> internal split-family dominance.
```

The R-to-q reduction uses the Hermite recurrence

```text
R_0 = 1,
R_1 = q_d,
R_{j+2} = 2Y^{-1} R_{j+1} + 2(j-d)Y^{-1} R_j.
```

Then the depth identity

```text
q_d - d = (Y/2) q_d q_{d-1}
```

is used to remove powers of `d` and convert the kernel to mixed-depth form.

#### 4.4.1. Mixed-depth kernel

The mixed-depth kernel has rows of the form

```text
C Y^a q_d^k q_{d-1}^j.
```

A representative run produced:

```text
548 mixed-depth rows,
275 positive rows,
273 negative rows,
q_d power range 1..12,
q_{d-1} depth range 0..9.
```

The near equality of positive and negative row counts confirms that naive coefficient positivity is not the right view. The right view is dominance.

#### 4.4.2. Paired Delta shadow

The paired Delta factor is

```text
Y^a q_d^k q_{d-1}^j (1 - Y q_d q_{d-1}).
```

The paired grouper found:

```text
Exact C/-C shifted Delta pairs: 0
Opposite-sign shifted candidates: 132
Greedy paired Delta rows: 130
Rows touched by paired Deltas: 257
Residual rows: 418
```

This means ell=3 is not a pure two-row Delta decomposition. It is a higher split-family problem.

#### 4.4.3. Factorized structural target

The discovered structural target is

```text
K_3 = sum_{q,diff} c_{q,diff} Y^diff q_d^q (1 - Y q_{d-1})^{q/2}.
```

The factor

```text
(1 - Y q_{d-1})^{q/2}
```

is the ell=3 analogue of lower-level Delta operators. It packages many mixed-depth rows into a single split-family operator.

#### 4.4.4. q=20 diff dominance

The isolated q=20 obstruction closes after projection to diff. The diff table is:

```text
diff  8: negative mass 12005/165888
diff  9: positive mass 31213/331776
diff 10: positive mass 123922813/4299816960
diff 11: negative mass 24823939/573308928
diff 12: negative mass 588245/95551488.
```

The totals are

```text
S = 528443293/4299816960,
D = 69842689/573308928,
S - D = 9246251/8599633920 > 0.
```

Thus the projected diff field is positive.

#### 4.4.5. q=20 internal split dominance

The more refined certificate keeps the internal tuple

```text
(q, q_d_power, q_{d-1}_power, Y_power, diff).
```

For the q=20 target, the internal tester found:

```text
Deficit rows: 18
Candidate source rows: 29
```

With source policy `q >= 20`, `diff(source) >= diff(target)`, and the qdiff transport model, the cover closes:

```text
uncovered deficit = 0,
max half-power used = 2.
```

Equivalently, transfers of weight at least

```text
2^{-2} = 1/4
```

suffice for the q=20 obstruction.

A strict `q > 20` source policy does not close the obstruction. Therefore ell=3 dominance has the form

```text
same-level internal split
+
higher-level spillover.
```

This is the correct higher split-family picture.

#### 4.4.6. Current ell=3 lemma status

The current verified statement is:

```text
The q=20 obstruction in the ell=3 mixed-depth kernel is closed by internal split-family dominance with dyadic qdiff transport of loss at most 2^{-2}.
```

The remaining step for the full ell=3 theorem is uniformization: prove that the same type of cover exists for every relevant q-family.

---

## 5. Conclusion and Future Work

### 5.1. What has been achieved

The Tantrium program has produced a coherent structural positivity attack on the Riemann Hypothesis through Jensen-Sturm chains. Its main achievements are:

1. Sturm pivots have been connected to normalized Hankel tau determinants.
2. The universal cross-ratio identity organizes the pivot chain.
3. The log-det cumulant dictionary gives a workable coefficient calculus.
4. Atlas and failure-hunter tools provide reliable finite frontiers.
5. D-seed layer analysis has produced nontrivial dominance mechanisms.
6. ell=2 produced a diagonal residue theorem with dyadic transport.
7. ell=3 produced a higher split-family mechanism and a q=20 internal certificate.

These are structural advances. They do not yet constitute a complete proof of RH, but they give a concrete route for completing one.

### 5.2. The remaining mathematical task

The central remaining task is a unified dyadic transport theorem.

A plausible global statement is:

```text
For every ell and every admissible internal deficit cell,
there exists a finite family of positive source cells and dyadic weights
2^{-r} whose transported mass dominates the deficit.
```

The ell=2 case suggests conservative losses of the form

```text
8^{-m} = 2^{-3m}.
```

The ell=3 q=20 certificate shows that a sharper `2^{-2}` transport can close a key obstruction in the qdiff model. The next task is to identify the exact uniform exponent law.

### 5.3. Higher layers ell >= 4

For ell=4 and beyond, the expected workflow is:

```text
1. generate the ell-layer cumulant kernel;
2. specialize to R_j monomials;
3. reduce to q_d Hermite coordinates;
4. convert to mixed-depth variables;
5. expose paired and higher Delta families;
6. build internal split-family covers;
7. prove a uniform dyadic transport theorem.
```

If this pipeline stabilizes, it would provide a repeatable proof architecture rather than a case-by-case computation.

### 5.4. Wider applications

The methods developed here may have uses beyond this specific RH program. The engine combines:

- symbolic positivity atlases;
- Hankel determinant factorization;
- log-det cumulant expansions;
- dyadic transport certificates;
- total-positivity inspired path models.

These tools may be useful in other positivity-heavy domains: special functions, orthogonal polynomial systems, spectral stability, certified numerical analysis, cryptographic positivity constraints, and quantum simulation sign-control problems.

---

# Appendix A. Main scripts and their functions

## Core positivity and coefficient tools

```text
tools/run_positivity_engine_v0.py
```

Runs the first integrated positivity engine: coefficient catalog, cumulant status, failure frontier, and theorem status.

```text
tools/coefficient_batch_engine_fast.py
```

Computes coefficient atlases using Bareiss elimination over truncated series.

```text
positivity/cumulants.py
```

Stores and manipulates log-det cumulant formulas.

```text
positivity/failure_hunter.py
```

Searches finite frontiers for negative coefficients or structural failures.

## ell=3 pipeline

```text
tools/ell3_cumulant_kernel_generator.py
```

Generates the ell=3 cumulant skeleton, i.e. partitions of total lambda weight 6.

```text
tools/ell3_rj_specialized_kernel.py
```

Uses `ell_atom_to_Rj_map.csv` to specialize ell=3 cumulant blocks into R_j monomials. It does not collapse products such as `R_a R_b` into `R_{a+b}`.

```text
tools/ell3_qd_reducer.py
```

Applies the Hermite recurrence for `R_j` and writes the q_d-basis kernel.

```text
tools/ell3_delta_transform.py
```

Uses

```text
d = q_d - (Y/2) q_d q_{d-1}
```

to convert the q_d kernel into mixed-depth variables.

```text
tools/ell3_paired_delta_grouper.py
```

Searches for paired Delta blocks of the form

```text
Y^a q_d^k q_{d-1}^j (1 - Y q_d q_{d-1}).
```

```text
tools/ell3_diff_dominance_tester.py
```

Projects mixed-depth data to q/diff and tests whether positive diff sources dominate negative diff deficits.

```text
tools/ell3_internal_split_dominance_tester.py
```

Keeps internal indices `(q, q_d_power, q_{d-1}_power, Y_power, diff)` and searches for weighted source-to-deficit covers.

# Appendix B. Formal theorem statements

## B.1. Tau-subdiscriminant lemma

For the polynomial family under consideration, the Hankel determinant

```text
tau_{d,j}(t) = det[s_{a+b}(t)]_{a,b=0}^{j}
```

is the relevant subdiscriminant controlling the j-th Sturm pivot after normalization.

## B.2. Universal cross-ratio theorem

For admissible `d,j`, the normalized factors satisfy

```text
rho_{d,j}(t)
  = ((d-j)/2) H_{d,j-2}(t) H_{d,j}(t) / H_{d,j-1}(t)^2.
```

## B.3. Global Coefficient Positivity target

For all admissible `d,j,k`,

```text
a_k^{(j)}(d) > 0,
```

where

```text
H_{d,j}(t) = sum_k a_k^{(j)}(d) t^k.
```

## B.4. Log-det cumulant dictionary

If

```text
log H_{d,j}(t) = sum_{r>=1} L_{2r} t^r,
```

then the first coefficients are

```text
a_1 = L_2,
a_2 = L_4 + L_2^2/2,
a_3 = L_6 + L_2 L_4 + L_2^3/6,
a_4 = L_8 + L_2 L_6 + L_4^2/2
      + L_2^2 L_4/2 + L_2^4/24.
```

## B.5. ell=2 diagonal residue theorem, template statement

After passing to the diagonal coordinate

```text
m = max_k(r) - k,
```

the ell=2 residual field admits a nonnegative residue decomposition with dyadic transport controlled by

```text
8^{-m}.
```

## B.6. ell=3 higher split-family certificate, q=20

In the ell=3 mixed-depth kernel, the q=20 negative internal cells are dominated by positive split-family sources with:

```text
source q >= target q,
source diff >= target diff,
dyadic edge weights beta = 2^{-r},
r <= 2 in the qdiff certificate,
uncovered deficit = 0.
```

This closes the q=20 obstruction and supplies the template for the full ell=3 uniform theorem.

---

## Final note

The Tantrium program began as a search through difficult symbolic terrain and evolved into a structured positivity engine. Its current lesson is clear:

```text
The route to RH here is not one miraculous identity.
It is a hierarchy of positivity transports.
```

The next decisive act is to prove that the transport hierarchy is uniform.
