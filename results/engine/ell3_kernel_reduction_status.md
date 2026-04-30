# ell=3 kernel reduction status

Concrete progress:

```text
tools/ell3_cumulant_kernel_generator.py
```

already generated the 11 connected cumulant terms of total weight 6.

Now the second tool has been added:

```text
tools/ell3_rj_symbolic_reducer.py
```

It reduces the 11 cumulant terms formally by using the generic atom map

```text
E_s = sum_j e_{s,j} R_j.
```

The cumulant expectation rule is implemented at the symbolic level:

```text
mu(R_{j1} ... R_{jk}) -> R_{j1+...+jk}.
```

This produces a formal R_j kernel with atom coefficient monomials.

## Why generic coefficients?

The repo does not yet contain a canonical concrete table for the atom map

```text
E_s -> sum_j e_{s,j} R_j.
```

So the reducer is written to accept the atom map symbolically first. Once the concrete `e_{s,j}` values are supplied, the same reducer gives the actual ell=3 R_j kernel and then the q_d/Y reduction can be applied.

## Next exact task

Add the concrete atom map file:

```text
results/engine/ell_atom_to_Rj_map.csv
```

with columns:

```text
s,j,coefficient
```

Then specialize the symbolic reducer and emit:

```text
results/engine/ell3_kernel_Rj_specialized.csv
results/engine/ell3_kernel_qd.csv
```

Status: ell=3 reduction engine started; concrete atom map still needed.
