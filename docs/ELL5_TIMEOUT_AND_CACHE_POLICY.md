# ELL=5 Timeout and Cache Policy

The fixed auto dispatch closes cached kernels through ell=4.

For ell=5, the bottleneck is not certification. The bottleneck is kernel generation, especially the Rj-specialization and qd reduction stages. In short interactive sandboxes this may timeout before `results/engine/ell5_mixed_depth_kernel.csv` is produced.

Policy:

1. Do not rebuild ell5 from scratch during every scan.
2. Treat `results/engine/ell5_mixed_depth_kernel.csv` as a cache artifact.
3. Once the ell5 mixed-depth kernel is present, run:

```bash
python tools/tantrium.py certify --scan all --max-ell 5 --model auto --build-missing false
```

or scan ell5 directly:

```bash
python tools/tantrium.py certify --input results/engine/ell5_mixed_depth_kernel.csv --scan all --max-ell 5 --model auto
```

Current dispatch expectation for ell5:

```text
q <= 10       -> low_q_family / q6_low_family
interior q    -> qdiff
top q=max_q   -> boundary_family
```

The missing artifact is therefore operational, not a new mathematical obstruction.
