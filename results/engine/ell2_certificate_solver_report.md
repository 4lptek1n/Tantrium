# ell=2 certificate solver report

Generated finite-window allocation for the ell=2 certificate matrix.

## Result

- strict even-source certificate feasible everywhere: `False`
- full whole-kernel certificate feasible everywhere: `True`

The strict certificate uses only positive capacity from M4, M2, and M0 against deficits from M3, M1, and M0. It fails at the r=2 edge.

The full certificate uses positive pieces from all layers M0..M4 and is feasible in the verified window.

## Strict summary

```text
r,coords,feasible_coords,min_surplus,max_uncovered
2,9,6,-1214657/648,1214657/648
3,10,10,0,0
4,11,11,0,0
5,12,12,0,0
6,13,13,0,0
7,14,14,0,0
8,15,15,0,0
9,16,16,0,0
10,17,17,0,0
```

## Full whole-kernel summary

```text
r,coords,feasible_coords,min_surplus,max_uncovered
2,9,9,0,0
3,10,10,0,0
4,11,11,0,0
5,12,12,0,0
6,13,13,0,0
7,14,14,0,0
8,15,15,0,0
9,16,16,0,0
10,17,17,0,0
```

## Interpretation

The ell=2 matrix cannot be certified by the naive even-source budget alone. It needs the all-layer source set.

This is still a finite-window certificate, not a global all-r proof.
