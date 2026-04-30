# ell=3 Atom-to-Rj Map

This fixes the concrete atom map needed by the ell=3 reducer.

The convention is calibrated by the known ell=1 atom

```text
E1 = -y R2 + 7/24 y^3 R3.
```

The general working atom rule is

```text
E_s = (-1)^s y^s R_{s+1} + (-1)^{s+1} (s+13)/48 y^{s+2} R_{s+2}.
```

For s=1..6 this gives:

```text
E1 = -y R2 + 7/24 y^3 R3
E2 = y^2 R3 - 5/16 y^4 R4
E3 = -y^3 R4 + 1/3 y^5 R5
E4 = y^4 R5 - 17/48 y^6 R6
E5 = -y^5 R6 + 3/8 y^7 R7
E6 = y^6 R7 - 19/48 y^8 R8
```

The machine-readable table is:

```text
results/engine/ell_atom_to_Rj_map.csv
```

This table is the bridge needed to specialize the ell=3 cumulant kernel from formal atom coefficients into explicit R_j products.

Next target:

```text
results/engine/ell3_kernel_Rj_specialized.csv
```

Then reduce the R_j products to q_d / mixed-depth variables and search the ell=3 quotient factor.
