#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY=python
fi

LOG_DIR="results/reproducibility"
VENV_DIR=".venv-reproduce"
mkdir -p "$LOG_DIR"

"$PY" -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e .

export PYTHONPATH="$ROOT"

run_step() {
  local name="$1"
  shift
  echo "== $name =="
  "$@" >"$LOG_DIR/${name}.stdout.log" 2>"$LOG_DIR/${name}.stderr.log"
}

run_step rh_strict python tools/tantrium_rh_machine.py --strict
run_step rh_prove python tools/tantrium_rh_machine.py --prove
run_step rh_full python tools/tantrium_rh_machine.py --full
run_step artifact_manifest python tools/tantrium_artifact_manifest.py --command-used "scripts/reproduce_tantrium_local.sh"
run_step independent_verifier python tools/independent_verifier.py

echo "TANTRIUM REPRODUCTION COMPLETE"
echo "logs: $LOG_DIR"
