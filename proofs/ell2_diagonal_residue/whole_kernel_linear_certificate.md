# ell=2 whole-kernel linear certificate

This note records the finite-window linear certificate search for the ell=2 mixed-depth kernel.

## Kernel

From the mixed-depth rewrite,

```text
P2 = K4*M^4 + K3*M^3 + K2*M^2 + K1*M + K0,
M = q_d q_(d-1).
```

Pairwise dominance fails:

```text
K4*M^4 does not dominate K3*M^3 alone,
K2*M^2 does not dominate K1*M alone.
```

Therefore ell=2 requires whole-kernel dominance.

## Certificate tested

For each verified row r and binomial coordinate a, split the five layer contributions into positive capacity and negative deficit:

```text
pos_capacity(r,a) = sum_i max(layer_i(r,a),0)
neg_deficit(r,a) = sum_i max(-layer_i(r,a),0)
surplus(r,a) = pos_capacity(r,a) - neg_deficit(r,a).
```

The coordinate is certified in the finite window if

```text
surplus(r,a) >= 0.
```

This is a finite-window linear certificate. It is not yet a symbolic all-r proof.

## Verified result

For r=2..10, every checked binomial coordinate has nonnegative surplus.

```text
r=2  degree=5  negative_D=0  deficit_coordinates=9   min_surplus=0 at_a=6
r=3  degree=6  negative_D=0  deficit_coordinates=10  min_surplus=0 at_a=7
r=4  degree=7  negative_D=0  deficit_coordinates=10  min_surplus=0 at_a=8
r=5  degree=8  negative_D=0  deficit_coordinates=11  min_surplus=0 at_a=9
r=6  degree=9  negative_D=0  deficit_coordinates=11  min_surplus=0 at_a=10
r=7  degree=10 negative_D=0  deficit_coordinates=12  min_surplus=0 at_a=11
r=8  degree=11 negative_D=0  deficit_coordinates=13  min_surplus=0 at_a=12
r=9  degree=12 negative_D=0  deficit_coordinates=14  min_surplus=0 at_a=13
r=10 degree=13 negative_D=0  deficit_coordinates=15  min_surplus=0 at_a=14
```

The zeros at the trailing coordinates are structural boundary zeros, not failures.

## Interpretation

The verified-window certificate confirms:

```text
positive capacity from all layers jointly dominates all negative residuals.
```

The ell=2 proof target is now a parametric multi-layer certificate explaining this same surplus formula uniformly in r.

## Output files

Local generated outputs:

```text
/mnt/data/tantrium_ell2_certificate/ell2_whole_kernel_certificate_report.md
/mnt/data/tantrium_ell2_certificate/ell2_whole_kernel_certificate_summary.csv
/mnt/data/tantrium_ell2_certificate/ell2_whole_kernel_certificate_by_coordinate.csv
```

## Status

ell=2 is not globally proved yet.

Completed:

1. P2 q-power extraction.
2. Mixed-depth rewrite P2=sum K_i M^i.
3. Pairwise dominance failure identified.
4. Whole-kernel finite-window linear certificate verified for r=2..10.

Open:

Find a symbolic all-r certificate or a multi-layer injection realizing the coordinatewise surplus formula.
