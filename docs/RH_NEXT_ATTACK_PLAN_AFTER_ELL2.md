# RH next attack plan after ell=2

## Current honest status

The Riemann Hypothesis is not proved yet.

The Tantrium program has reduced the main positivity chain to a highly structured finite set of positivity mechanisms. The ell=2 layer now has a concrete path-model proof target:

```text
Diagonal Residue Theorem:
S_m(i) >= 0.
```

The current ell=2 path-model identity is

```text
C_next(i) = 8^(-m) C_converted(i) + S_m(i).
```

The r=3..30 exact atlas gives:

```text
negative residual sources = 0
zero residual sources = 0
```

so the target is experimentally very strong.

## Immediate priority

Do not jump to ell=3 before formalizing ell=2.

The next mathematical task is to turn `docs/ELL2_DIAGONAL_RESIDUE_PATH_MODEL.md` into a formal proof by specifying the eight missing pieces:

1. exact path objects counted by `C_m(i)`;
2. binomial-origin conversion map;
3. Wrapping map;
4. RootTop map;
5. SplitPair map;
6. injectivity of the composite map;
7. exact weight factor `8^(-m)`;
8. disjoint residual complement.

## Proof target 1: formal ell=2 closure

Write a formal theorem:

```text
Theorem. For every admissible m,i,
C_next(i) - 8^(-m) C_converted(i) >= 0.
```

Proof strategy:

```text
C_next path families
= transported image from C_m
  disjoint_union residual path families.
```

Every residual family has positive weight, so `S_m(i)>=0`.

## Proof target 2: D-positive chain integration

Once ell=2 is formalized, connect it back into the existing chain:

```text
Diagonal Residue Theorem
=> non-circular q8 production
=> diagonal positivity
=> rho_k(r) >= 0
=> R_r(z) positive
=> ell=2 Region C closes
=> ell=2 layer closes.
```

Then state exactly what remains for full D-positivity across all ell.

## Proof target 3: ell=3 scout only after ell=2 formalization

After formal ell=2 closure, run an ell=3 scout with the same architecture:

```text
1. reduce to quotient;
2. build rho atlas;
3. find natural coordinates;
4. locate production operator;
5. identify residual theorem.
```

The ell=2 mechanism predicts that ell=3 will require a higher residual path model, not a scalar recurrence.

## Publication plan

Paper 1:

```text
D-positive seeds and Newton moment positivity.
```

Paper 2:

```text
ell=0 and ell=1 split-pair dominance.
```

Paper 3:

```text
ell=2 diagonal residue model and non-circular q8 production.
```

## Rule going forward

No theorem is marked closed until the formal map/injection/complement proof is written.

Atlas evidence is used to find the theorem; it is not itself the theorem.
