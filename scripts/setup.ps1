Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "python not found. Install Python 3.12+ and rerun."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Error "npm not found. Install Node.js 20+ and rerun."
}

if (-not (Test-Path "backend\.venv")) {
  python -m venv backend\.venv
}

.\backend\.venv\Scripts\python -m pip install --upgrade pip
.\backend\.venv\Scripts\python -m pip install -r backend\requirements.txt

npm install
npm --prefix frontend install

if (-not (Test-Path "rephraser\.venv")) {
  python -m venv rephraser\.venv
}

.\rephraser\.venv\Scripts\python -m pip install --upgrade pip
.\rephraser\.venv\Scripts\python -m pip install -r rephraser\requirements.txt

Write-Output "Setup complete. Run: npm run dev"
