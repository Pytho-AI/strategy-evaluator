#!/usr/bin/env bash
# Replace the served frontend with a new bundled HTML artifact, then verify it.
#
#   ./deploy/swap-ui.sh ~/Downloads/UI_V3.html
#
# The original artifact is never modified. The recovered tree replaces app/ui/src,
# app/ui/assets and app/ui/vendor; app/ui/index.html and app/ui/src/api.js (the API
# client) are preserved unless the recovery supplies its own.
set -euo pipefail
ARTIFACT="${1:?usage: deploy/swap-ui.sh <bundled .html>}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGING="$(mktemp -d)"

echo "==> artifact $(basename "$ARTIFACT")"
shasum -a 256 "$ARTIFACT"
"$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/app/ui/tools/extract.py" "$ARTIFACT" "$STAGING/decoded"
echo "==> decoded to $STAGING/decoded"
echo "Review, then run app/ui/tools/lay_out_source.py to place the tree, and re-run the UI tests."
echo "Staging kept at: $STAGING"
