#!/usr/bin/env bash
set -u

mkdir -p results/engine results/certificates results/atlas docs

echo "[ell5] persistent runner started at $(date -u)"

if [ ! -f results/engine/ell5_mixed_depth_kernel.csv ]; then
  echo "[ell5] mixed-depth cache missing; building ell5 kernel"
  python -u tools/build_kernel.py --ell 5
else
  echo "[ell5] mixed-depth cache found; skipping kernel rebuild"
fi

if [ -f results/engine/ell5_mixed_depth_kernel.csv ]; then
  echo "[ell5] running auto scan through ell=5"
  python -u tools/tantrium.py certify --scan all --max-ell 5 --model auto --report results/certificates/scan_all_auto_ell1_ell5_report.md > results/certificates/scan_all_auto_ell1_ell5.log 2>&1
  echo "[ell5] scan finished with status $?"
  echo "--- scan report ---"
  cat results/certificates/scan_all_auto_ell1_ell5_report.md || true
  echo "--- status update ---"
  python -u tools/tantrium.py status --update || true
  python -u tools/tantrium.py compare-atlas || true
else
  echo "[ell5] ERROR: mixed-depth kernel still missing after build attempt"
  exit 2
fi

echo "[ell5] persistent runner finished at $(date -u)"
