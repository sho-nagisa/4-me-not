#!/usr/bin/env bash
set -euo pipefail

SKIP_DOCKER=0
SKIP_FRONTEND=0
SKIP_DEMO_DATA=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-docker)
      SKIP_DOCKER=1
      shift
      ;;
    --skip-frontend)
      SKIP_FRONTEND=1
      shift
      ;;
    --skip-demo-data)
      SKIP_DEMO_DATA=1
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if [[ "$SKIP_DOCKER" -eq 0 ]]; then
  if command -v docker >/dev/null 2>&1; then
    docker compose up -d db
    container_id="$(docker compose ps -q db)"
    if [[ -z "$container_id" ]]; then
      echo "PostgreSQL container was not found." >&2
      exit 1
    fi

    for _ in $(seq 1 60); do
      health="$(docker inspect --format '{{.State.Health.Status}}' "$container_id" 2>/dev/null || true)"
      if [[ "$health" == "healthy" ]]; then
        break
      fi
      sleep 2
    done

    if [[ "${health:-}" != "healthy" ]]; then
      echo "PostgreSQL did not become healthy in time." >&2
      exit 1
    fi
  else
    echo "Docker was not found. Start PostgreSQL yourself, or rerun with Docker installed." >&2
  fi
fi

PYTHON_BIN="${PYTHON:-python3}"
if [[ ! -d .venv ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

VENV_PY=".venv/bin/python"
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r backend/requirements.txt
"$VENV_PY" -m alembic upgrade head

if [[ "$SKIP_DEMO_DATA" -eq 0 ]]; then
  "$VENV_PY" scripts/seed_demo_data.py
  "$VENV_PY" scripts/rebuild_search_index.py
fi

if [[ "$SKIP_FRONTEND" -eq 0 ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm was not found. Install Node.js 18+ and rerun this script, or use --skip-frontend." >&2
    exit 1
  fi

  (cd frontend && npm install)
fi

cat <<'EOF'

Setup complete.
Backend:  .venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
Frontend: cd frontend && npm run dev
EOF
