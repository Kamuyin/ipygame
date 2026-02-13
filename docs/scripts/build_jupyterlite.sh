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
XEUS_ENV_FILE="$REPO_ROOT/docs/jupyterlite/environment.yml"

echo "Cleaning up previous builds..."
rm -rf "$OUTPUT_DIR"
rm -rf "$WHEELS_DIR"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$WHEELS_DIR"

echo "Building ipygame wheel..."
"$PYTHON_EXEC" -m build --wheel --outdir "$WHEELS_DIR" "$REPO_ROOT"

# Find the built wheel
WHEEL_PATH=$(find "$WHEELS_DIR" -name "*.whl" | head -n 1)
WHEEL_BASENAME=""
if [[ -n "${WHEEL_PATH:-}" && -f "$WHEEL_PATH" ]]; then
    WHEEL_BASENAME="$(basename "$WHEEL_PATH")"
fi

if [[ -z "$WHEEL_BASENAME" ]]; then
    echo "No wheel found in $WHEELS_DIR"
    exit 1
fi

echo "Generating xeus environment: $XEUS_ENV_FILE"
cat > "$XEUS_ENV_FILE" <<EOF
name: xeus-python-kernel
channels:
  - https://prefix.dev/emscripten-forge-dev
  - https://prefix.dev/conda-forge
dependencies:
  - xeus-python
  - numpy
  - pillow
  - ipywidgets
  - ipycanvas
  - pip
  - pip:
      - ./wheels/$WHEEL_BASENAME
EOF

echo "Running JupyterLite build..."
CMD=("$JUPYTER_EXEC" "lite" "build" \
    "--config" "$REPO_ROOT/docs/jupyterlite/jupyter_lite_config.json" \
    "--contents" "$CONTENTS_DIR" \
    "--output-dir" "$OUTPUT_DIR" \
    "--XeusAddon.environment_file" "$XEUS_ENV_FILE")

"${CMD[@]}"

echo "JupyterLite build complete."
