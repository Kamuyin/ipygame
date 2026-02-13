$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$venvRoot = if ($env:VIRTUAL_ENV) { $env:VIRTUAL_ENV } else { Join-Path $repoRoot ".venv" }
$venvPython = Join-Path $venvRoot "Scripts\python.exe"
$venvJupyter = Join-Path $venvRoot "Scripts\jupyter.exe"
$contentsDir = Join-Path $repoRoot "docs\jupyterlite\contents"
$outputDir = Join-Path $repoRoot "docs\public\jupyterlite"
$wheelsDir = Join-Path $repoRoot "docs\jupyterlite\wheels"
$xeusEnvFile = Join-Path $repoRoot "docs\jupyterlite\environment.yml"

# Clean previous build artifacts
Remove-Item -Recurse -Force $outputDir -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $wheelsDir -ErrorAction SilentlyContinue

New-Item -Force -ItemType Directory $outputDir | Out-Null
New-Item -Force -ItemType Directory $wheelsDir | Out-Null

Write-Host "Ensuring host Python has pip..."
& $venvPython -m pip --version *> $null
if ($LASTEXITCODE -ne 0) {
  & $venvPython -m ensurepip --upgrade
}

Write-Host "Building ipygame wheel..."
& $venvPython -m build --wheel --outdir $wheelsDir $repoRoot

$wheelPath = (Get-ChildItem $wheelsDir -Filter "*.whl" | Select-Object -First 1).FullName
if (-not $wheelPath) {
  throw "No wheel found in $wheelsDir"
}

$wheelName = [System.IO.Path]::GetFileName($wheelPath)

$xeusEnvContent = @"
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
      - ./wheels/$wheelName
"@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($xeusEnvFile, $xeusEnvContent, $utf8NoBom)

Write-Host "Generated xeus environment: $xeusEnvFile"

$buildArgs = @(
    "lite", "build",
    "--config", (Join-Path $repoRoot "docs\jupyterlite\jupyter_lite_config.json"),
    "--contents", $contentsDir,
  "--output-dir", $outputDir,
  "--XeusAddon.environment_file", $xeusEnvFile
)

# Run Build
Write-Host "Running JupyterLite build..."
if (Test-Path $venvJupyter) {
  & $venvJupyter $buildArgs
} else {
  & $venvPython -m jupyter $buildArgs
}

Write-Host "JupyterLite build complete."
