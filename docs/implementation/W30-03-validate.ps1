param(
    [string]$Python = 'C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
    [string]$Dependencies = (Join-Path ([IO.Path]::GetTempPath()) '4-me-not-W30-02-deps'),
    [string]$SourceZip = 'C:/Users/keima/.codex/.chatgpt-projects/g-p-696486f280d081918418aa6ea3658d1c/deliverables/4-me-not-v0.4-codex-task-pack/reference/4-me-not-collab-v0.4.zip'
)
# Reconstruct a disposable specification working tree; never start the app/DB.
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$overlay = Join-Path $repo 'docs/spec/v0.4'
$prior = Get-Content (Join-Path $PSScriptRoot 'W30-01-evidence.json') -Raw | ConvertFrom-Json
$zipHash = (Get-FileHash -LiteralPath $SourceZip).Hash
if ($zipHash -ne $prior.archive_sha256) { throw 'Source ZIP differs from W30-01 evidence' }
if (-not (Test-Path -LiteralPath $Python)) { throw "Python is missing: $Python" }
$work = Join-Path ([IO.Path]::GetTempPath()) ('4-me-not-W30-03-run-' + [guid]::NewGuid().ToString('N'))
Expand-Archive -LiteralPath $SourceZip -DestinationPath $work
$specRoot = Join-Path $work '4-me-not-collab-v0.4'
Copy-Item -LiteralPath (Join-Path $specRoot 'contracts/memory.schema.json') -Destination (Join-Path $specRoot 'w30-02-baseline-memory.schema.json')
$overlayFiles = @(
    'contracts/memory.schema.json',
    'docs/state-model.md',
    'fixtures/w30-02-state-cases.json',
    'tests/test_w30_02_state_axes.py',
    'docs/authority-matrix.md',
    'fixtures/w30-03-use-cases.json',
    'tests/test_w30_03_use_conditions.py'
)
$copied = @()
foreach ($relative in $overlayFiles) {
    $from = Join-Path $overlay $relative
    $to = Join-Path $specRoot $relative
    Copy-Item -LiteralPath $from -Destination $to
    $copied += [ordered]@{ path=$relative; sha256=(Get-FileHash -LiteralPath $from).Hash }
}
$before = @($prior.code_files | ForEach-Object {
    [ordered]@{path=$_.path; sha256=(Get-FileHash -LiteralPath (Join-Path $repo $_.path)).Hash}
})
$results = @()
$previousUtf8 = $env:PYTHONUTF8
$previousPath = $env:PYTHONPATH
$previousBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONUTF8 = '1'
    $env:PYTHONPATH = $Dependencies
    $env:PYTHONDONTWRITEBYTECODE = '1'
    Push-Location $specRoot
    try {
        $version = @(& $Python -c 'import sys, importlib.metadata; print(sys.version); print("jsonschema=" + importlib.metadata.version("jsonschema"))' 2>&1 | ForEach-Object { "$_" })
        if ($LASTEXITCODE -ne 0) { throw "Specification dependency preflight failed: $($version -join ' ')" }
        foreach ($run in @(
            @{name='active'; argv=@('-X','utf8','-m','unittest','discover','-s','tests','-p','test_*.py','-v')},
            @{name='baselines'; argv=@('scripts/check_baselines.py')}
        )) {
            $arguments = $run.argv
            $output = @(& $Python @arguments 2>&1 | ForEach-Object { "$_" })
            $code = $LASTEXITCODE
            $log = Join-Path $PSScriptRoot ('W30-03-' + $run.name + '.log')
            $output | Set-Content -LiteralPath $log -Encoding utf8
            $counts = @([regex]::Matches(($output -join "`n"), 'Ran (\d+) tests? in') | ForEach-Object { [int]$_.Groups[1].Value })
            $results += [ordered]@{
                name=$run.name; working_directory=$specRoot; executable=$Python; arguments=$arguments
                exit_code=$code; unittest_counts=$counts; log=$log
            }
            Write-Output ($run.name + ': exit=' + $code + ', tests=' + ($counts -join '+'))
        }
    } finally { Pop-Location }
} finally {
    $env:PYTHONUTF8 = $previousUtf8
    $env:PYTHONPATH = $previousPath
    $env:PYTHONDONTWRITEBYTECODE = $previousBytecode
}
$changedDuringRun = @($before | Where-Object { (Get-FileHash -LiteralPath (Join-Path $repo $_.path)).Hash -ne $_.sha256 })
$changedSinceInventory = @($prior.code_files | Where-Object { (Get-FileHash -LiteralPath (Join-Path $repo $_.path)).Hash -ne $_.sha256 })
$record = [ordered]@{
    task='W30-03'; timestamp=(Get-Date -Format o); repo=$repo; spec_root=$specRoot
    source_zip=$SourceZip; source_zip_sha256=$zipHash; source_zip_unchanged=((Get-FileHash -LiteralPath $SourceZip).Hash -eq $zipHash)
    runtime=$version; dependency_directory=$Dependencies; environment=@{PYTHONUTF8='1'; PYTHONDONTWRITEBYTECODE='1'}
    overlay_files=$copied; results=$results
    existing_code_files_checked=$before.Count; code_changed_during_run=$changedDuringRun; code_changed_since_W30_01=$changedSinceInventory
    scope='Specification schema/fixtures and existing reference rules only. No application acceptance, DB, real data, production Gate or independent review.'
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'W30-03-validation.json') -Encoding utf8
Write-Output "Working SPEC_ROOT: $specRoot"
Write-Output ('Existing code changed during run: ' + $changedDuringRun.Count)
Write-Output ('Existing code changed since W30-01: ' + $changedSinceInventory.Count)
foreach ($changed in $changedSinceInventory) {
    Write-Output ('Changed since W30-01: ' + $changed.path)
}
foreach ($changed in $changedDuringRun) {
    Write-Output ('Changed during run: ' + $changed.path)
}
if (@($results | Where-Object exit_code -ne 0).Count -or $changedDuringRun.Count -or $changedSinceInventory.Count -or -not $record.source_zip_unchanged) { exit 1 }

