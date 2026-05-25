param(
    [switch]$SkipDocker,
    [switch]$SkipFrontend,
    [switch]$SkipCleanup,
    [switch]$ResetDbVolume,
    [int]$StopAfterSuccesses = 0
)

$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir
# Checks whether a command exists.
function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# Runs docker compose against the test compose file.
function Invoke-TestCompose {
    docker compose -f docker-compose.test.yml @args
}

# Waits for the test DB to become healthy.
function Wait-ComposeDb {
    $ContainerId = Invoke-TestCompose ps -q db-test
    if (-not $ContainerId) {
        throw "Test PostgreSQL container was not found."
    }

    for ($Index = 0; $Index -lt 60; $Index++) {
        $Health = docker inspect --format "{{.State.Health.Status}}" $ContainerId 2>$null
        if ($Health -eq "healthy") {
            return
        }

        Start-Sleep -Seconds 2
    }

    throw "Test PostgreSQL did not become healthy in time."
}
# Starts the test PostgreSQL container when local Docker support is enabled.
if (-not $SkipDocker) {
    if (-not (Test-Command "docker")) {
        throw "Docker was not found. Start PostgreSQL yourself, or rerun without local Docker support."
    }

    if ($ResetDbVolume) {
        Write-Host "Recreating test PostgreSQL container..."
        Invoke-TestCompose down -v
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    Invoke-TestCompose up -d db-test
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    Wait-ComposeDb
}

$Python = Join-Path $RootDir ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Python virtualenv was not found at $Python"
}
# Runs backend tests against the disposable PostgreSQL database.
$TestDatabaseUrl = "postgresql://forme_not@127.0.0.1:55432/forme_not"
$TestArgs = @("-m", "scripts.run_tests", "--db-url", $TestDatabaseUrl, "--migrate")
if ($SkipCleanup) {
    $TestArgs += "--skip-cleanup"
}
if ($StopAfterSuccesses -gt 0) {
    $TestArgs += "--stop-after-successes"
    $TestArgs += $StopAfterSuccesses.ToString()
}

Write-Host "Running backend tests..."
& $Python @TestArgs
$BackendExitCode = $LASTEXITCODE
if ($BackendExitCode -ne 0 -and -not $ResetDbVolume) {
    Write-Host ""
    Write-Host "Test run failed. To recreate the disposable test DB container and rerun tests, execute:"
    Write-Host ""
    Write-Host "  .\scripts\run_tests_local.ps1 -ResetDbVolume"
    Write-Host ""
}

$FrontendExitCode = 0
if (-not $SkipFrontend) {
    if (Test-Command "npm.cmd") {
        $Npm = "npm.cmd"
    } elseif (Test-Command "npm") {
        $Npm = "npm"
    } else {
        throw "npm was not found. Install Node.js 18+ and rerun this script, or use -SkipFrontend."
    }

    Push-Location (Join-Path $RootDir "frontend")
    try {
        Write-Host "Running frontend tests..."
        & $Npm test
        $FrontendExitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

if ($BackendExitCode -ne 0) {
    exit $BackendExitCode
}

exit $FrontendExitCode
