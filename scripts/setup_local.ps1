param(
    [switch]$SkipDocker,
    [switch]$SkipFrontend,
    [switch]$SkipDemoData
)

$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Wait-ComposeDb {
    $ContainerId = docker compose ps -q db
    if (-not $ContainerId) {
        throw "PostgreSQL container was not found."
    }

    for ($Index = 0; $Index -lt 60; $Index++) {
        $Health = docker inspect --format "{{.State.Health.Status}}" $ContainerId 2>$null
        if ($Health -eq "healthy") {
            return
        }

        Start-Sleep -Seconds 2
    }

    throw "PostgreSQL did not become healthy in time."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

if (-not $SkipDocker) {
    if (Test-Command "docker") {
        docker compose up -d db
        Wait-ComposeDb
    } else {
        Write-Warning "Docker was not found. Start PostgreSQL yourself, or rerun with Docker installed."
    }
}

if (-not (Test-Path ".venv")) {
    if (Test-Command "py") {
        py -3 -m venv .venv
    } elseif (Test-Command "python") {
        python -m venv .venv
    } else {
        throw "Python was not found. Install Python 3.11+ and rerun this script."
    }
}

$Python = Join-Path $RootDir ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r "backend\requirements.txt"
& $Python -m alembic upgrade head

if (-not $SkipDemoData) {
    & $Python "scripts\seed_demo_data.py"
    & $Python "scripts\rebuild_search_index.py"
}

if (-not $SkipFrontend) {
    if (-not (Test-Command "npm")) {
        throw "npm was not found. Install Node.js 18+ and rerun this script, or use -SkipFrontend."
    }

    Push-Location "frontend"
    try {
        npm install
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Backend:  .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host "Frontend: cd frontend; npm run dev"
