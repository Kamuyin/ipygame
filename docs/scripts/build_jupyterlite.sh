#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  venv_python="$VIRTUAL_ENV/bin/python"
else
  venv_python="$repo_root/.venv/bin/python"
fi
contents_dir="$repo_root/docs/jupyterlite/contents"
output_dir="$repo_root/docs/public/jupyterlite"
wheels_dir="$output_dir/wheels"

mkdir -p "$output_dir" "$wheels_dir"

"$venv_python" -m pip install --quiet --upgrade build
"$venv_python" -m build --wheel --outdir "$wheels_dir" "$repo_root"

wheel_paths=("$wheels_dir"/ipygame-*.whl)

"$venv_python" -m jupyter lite build \
  --config "$repo_root/docs/jupyterlite/jupyter_lite_config.json" \
  --settings-overrides "$repo_root/docs/jupyterlite/overrides.json" \
  --piplite-wheels "${wheel_paths[@]}" \
  --contents "$contents_dir" \
  --output-dir "$output_dir"
