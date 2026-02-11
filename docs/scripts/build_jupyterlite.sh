#!/usr/bin/env bash
set -euo pipefail

# Resolve directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Go up two levels from docs/scripts -> root
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    PYTHON_EXEC="$VIRTUAL_ENV/bin/python"
    JUPYTER_EXEC="$VIRTUAL_ENV/bin/jupyter"
else
    # Fallback/CI assumption: python/jupyter are on PATH
    PYTHON_EXEC="python"
    JUPYTER_EXEC="jupyter"
fi

CONTENTS_DIR="$REPO_ROOT/docs/jupyterlite/contents"
OUTPUT_DIR="$REPO_ROOT/docs/public/jupyterlite"
WHEELS_DIR="$REPO_ROOT/docs/jupyterlite/wheels"

echo "Cleaning up previous builds..."
rm -rf "$OUTPUT_DIR"
rm -rf "$WHEELS_DIR"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$WHEELS_DIR"

echo "Building ipygame wheel..."
"$PYTHON_EXEC" -m build --wheel --outdir "$WHEELS_DIR" "$REPO_ROOT"

# Find the built wheel
WHEEL_PATH=$(find "$WHEELS_DIR" -name "*.whl" | head -n 1)

echo "Running JupyterLite build..."
CMD=("$JUPYTER_EXEC" "lite" "build" \
    "--config" "$REPO_ROOT/docs/jupyterlite/jupyter_lite_config.json" \
    "--contents" "$CONTENTS_DIR" \
    "--output-dir" "$OUTPUT_DIR")

if [[ -f "$WHEEL_PATH" ]]; then
    echo "Including local wheel: $WHEEL_PATH"
    CMD+=("--piplite-wheels" "$WHEEL_PATH")
fi

"${CMD[@]}"

echo "JupyterLite build complete."
