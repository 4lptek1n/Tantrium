$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$LogDir = Join-Path $Root "results\reproducibility"
$VenvDir = Join-Path $Root ".venv-reproduce"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

& $Python -m venv $VenvDir
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e .

$env:PYTHONPATH = "$Root"

function Invoke-TantriumStep {
    param(
        [string]$Name,
        [string[]]$Command
    )
    $stdout = Join-Path $LogDir "$Name.stdout.log"
    $stderr = Join-Path $LogDir "$Name.stderr.log"
    Write-Host "== $Name =="
    & $VenvPython @Command > $stdout 2> $stderr
}

Invoke-TantriumStep "rh_strict" @("tools/tantrium_rh_machine.py", "--strict")
Invoke-TantriumStep "rh_prove" @("tools/tantrium_rh_machine.py", "--prove")
Invoke-TantriumStep "rh_full" @("tools/tantrium_rh_machine.py", "--full")
Invoke-TantriumStep "artifact_manifest" @("tools/tantrium_artifact_manifest.py", "--command-used", "scripts/reproduce_tantrium_windows.ps1")
Invoke-TantriumStep "independent_verifier" @("tools/independent_verifier.py")

Write-Host "TANTRIUM REPRODUCTION COMPLETE"
Write-Host "logs: $LogDir"
