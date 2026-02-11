$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$venvRoot = if ($env:VIRTUAL_ENV) { $env:VIRTUAL_ENV } else { Join-Path $repoRoot ".venv" }
$venvPython = Join-Path $venvRoot "Scripts\python.exe"
$venvJupyter = Join-Path $venvRoot "Scripts\jupyter.exe"
$contentsDir = Join-Path $repoRoot "docs\jupyterlite\contents"
$outputDir = Join-Path $repoRoot "docs\public\jupyterlite"
$wheelsDir = Join-Path $repoRoot "docs\jupyterlite\wheels"

# Clean previous build artifacts
Remove-Item -Recurse -Force $outputDir -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $wheelsDir -ErrorAction SilentlyContinue

New-Item -Force -ItemType Directory $outputDir | Out-Null
New-Item -Force -ItemType Directory $wheelsDir | Out-Null

Write-Host "Building ipygame wheel..."
& $venvPython -m pip install --quiet --upgrade build
& $venvPython -m build --wheel --outdir $wheelsDir $repoRoot

$wheelPath = (Get-ChildItem $wheelsDir -Filter "*.whl" | Select-Object -First 1).FullName

$buildArgs = @(
    "lite", "build",
    "--config", (Join-Path $repoRoot "docs\jupyterlite\jupyter_lite_config.json"),
    "--contents", $contentsDir,
    "--output-dir", $outputDir
)

if ($wheelPath) {
    Write-Host "Including local wheel: $wheelPath"
    $buildArgs += "--piplite-wheels"
    $buildArgs += $wheelPath
}

# Run Build
Write-Host "Running JupyterLite build..."
if (Test-Path $venvJupyter) {
  & $venvJupyter $buildArgs
} else {
  & $venvPython -m jupyter $buildArgs
}

Write-Host "JupyterLite build complete."
