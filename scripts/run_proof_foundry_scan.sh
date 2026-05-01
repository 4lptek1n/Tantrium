#!/usr/bin/env bash
set -euo pipefail

MAX_ELL="${1:-5}"
MODEL="${2:-qdiff}"
REPO="${GITHUB_REPOSITORY:-4lptek1n/Tantrium}"
WORKFLOW="tantrium-scan.yml"
ARTIFACT_DIR="results/github-actions"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI 'gh' is required. Install it from https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated. Run: gh auth login" >&2
  exit 1
fi

echo "Triggering Tantrium Proof Foundry scan..."
echo "repo=$REPO workflow=$WORKFLOW max_ell=$MAX_ELL model=$MODEL"

gh workflow run "$WORKFLOW" \
  --repo "$REPO" \
  -f max_ell="$MAX_ELL" \
  -f model="$MODEL"

echo "Waiting for workflow run to appear..."
sleep 5

RUN_ID="$(gh run list --repo "$REPO" --workflow "$WORKFLOW" --limit 1 --json databaseId --jq '.[0].databaseId')"
if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
  echo "Could not find workflow run." >&2
  exit 1
fi

echo "Watching run $RUN_ID..."
gh run watch "$RUN_ID" --repo "$REPO" --exit-status

mkdir -p "$ARTIFACT_DIR"
echo "Downloading artifacts to $ARTIFACT_DIR..."
gh run download "$RUN_ID" --repo "$REPO" --dir "$ARTIFACT_DIR"

echo "Done. Key report paths:"
find "$ARTIFACT_DIR" -type f | sort | sed 's#^#  #'
