#requires -Version 5.1
<#
.SYNOPSIS
    Windows PowerShell task runner for energy-optimal-rag.

.EXAMPLE
    .\tasks.ps1 setup
    .\tasks.ps1 test
    .\tasks.ps1 validate
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("help", "setup", "test", "lint", "format", "validate", "clean")]
    [string]$Task = "help"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Resolve the interpreter: explicit override, active conda env, the documented
# Anaconda install, then PATH. This avoids picking up an unrelated Python.
function Resolve-Python {
    if ($env:RAG_ENERGY_PYTHON) { return $env:RAG_ENERGY_PYTHON }
    if ($env:CONDA_PREFIX) {
        $condaPython = Join-Path $env:CONDA_PREFIX "python.exe"
        if (Test-Path $condaPython) { return $condaPython }
    }
    $anacondaPython = "C:\ProgramData\anaconda3\python.exe"
    if (Test-Path $anacondaPython) { return $anacondaPython }
    return "python"
}

$Python = Resolve-Python

Push-Location $Root
try {
    switch ($Task) {
        "help" {
            Write-Host "Targets:"
            Write-Host "  setup     Create/refresh the conda env and install the package"
            Write-Host "  test      Run the fast test suite"
            Write-Host "  lint      Run ruff check"
            Write-Host "  format    Run ruff format"
            Write-Host "  validate  Parse and validate all TOML configs"
            Write-Host "  clean     Remove caches and build artifacts (keeps data and runs)"
        }
        "setup" {
            conda env create -f environment.yml
            if ($LASTEXITCODE -ne 0) {
                conda env update -f environment.yml --prune
            }
            if ($LASTEXITCODE -ne 0) { throw "conda environment setup failed" }
            conda run -n energy-optimal-rag python -m pip install -e ".[dev]"
            if ($LASTEXITCODE -ne 0) { throw "editable install failed" }
        }
        "test" {
            & $Python -m pytest -q
            if ($LASTEXITCODE -ne 0) { throw "tests failed" }
        }
        "lint" {
            & $Python -m ruff check .
            if ($LASTEXITCODE -ne 0) { throw "lint failed" }
        }
        "format" {
            & $Python -m ruff format .
            if ($LASTEXITCODE -ne 0) { throw "format failed" }
        }
        "validate" {
            & $Python -m rag_energy.cli validate
            if ($LASTEXITCODE -ne 0) { throw "config validation failed" }
        }
        "clean" {
            $targets = @("build", "dist", ".pytest_cache", ".ruff_cache", ".mypy_cache", "htmlcov")
            foreach ($t in $targets) {
                if (Test-Path $t) { Remove-Item -Recurse -Force $t }
            }
            Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" |
                ForEach-Object { Remove-Item -Recurse -Force $_.FullName }
            Get-ChildItem -Path . -Recurse -Directory -Filter "*.egg-info" |
                ForEach-Object { Remove-Item -Recurse -Force $_.FullName }
            Write-Host "Cleaned caches and build artifacts. data/ and runs/ were preserved."
        }
    }
}
finally {
    Pop-Location
}
