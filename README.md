# 4-me-not

「誰と、どこで、何を、どこまで話したか」を記録して、次に会う前に思い出せるようにする個人向けの人間関係メモアプリです。

会話・メッセージ・面談などのやり取りを、人物、コミュニティ、話題、共有度と一緒に保存します。曖昧な記憶から過去の会話や相手を探せる「思い出す検索」も備えています。

## デモアカウント

どなたでも見れるアカウントです。お試しとして見てください。
account:d〇〇〇〇@gmail.com
pass:p〇〇〇〇〇

## Quick Start

```powershell
Copy-Item .env.example .env
docker compose up --build
# Open http://localhost:5173
```

## Local Setup

### Docker を使う場合

通常はこちらを使います。ホスト側に Python / Node の依存を入れず、backend / frontend を Docker Compose で起動します。接続先DBは `.env` の `DATABASE_URL` を使います。

Prerequisites:

- Docker Desktop or Docker Engine with Docker Compose v2

初回だけ `.env` を作成し、`DATABASE_URL` を接続したいDBに合わせます。

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

アプリを起動します。

```powershell
docker compose up --build
```

2回目以降、build が不要な場合:

```powershell
docker compose up
```

バックグラウンドで起動する場合:

```powershell
docker compose up -d
```

初回にデモデータも入れる場合は、別ターミナルで実行します。実行先は `.env` の `DATABASE_URL` です。

```powershell
docker compose exec backend python scripts/seed_demo_data.py
docker compose exec backend python scripts/rebuild_search_index.py
```

アクセス先:

- Frontend: `http://localhost:5173`
- Backend health check: `http://127.0.0.1:8000/api/health`
- FastAPI docs: `http://127.0.0.1:8000/docs`

停止する場合:

```powershell
docker compose down
```

### Docker を使わない場合

ホスト側で backend / frontend を直接起動したい場合の手順です。PostgreSQL は Docker の DB だけを使うか、既存の PostgreSQL を使います。

Prerequisites:

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 compatible database

アプリ用の PostgreSQL だけ Docker で起動する場合:

```powershell
Copy-Item .env.example .env
docker compose --profile local-db up -d db
```

この場合、Docker 内の backend から local DB に接続するなら `.env` の `DATABASE_URL` は `postgresql://forme_not:forme_not@db:5432/forme_not` にします。ホスト側で backend を直接起動するなら `postgresql://forme_not:forme_not@localhost:5432/forme_not` にします。

既存 PostgreSQL を使う場合は、`.env.example` を `.env` にコピーして `DATABASE_URL` を自分の DB に合わせて変更します。

セットアップスクリプトを使う場合:

```powershell
.\scripts\setup_local.ps1 -SkipDocker
```

macOS / Linux:

```bash
bash scripts/setup_local.sh --skip-docker
```

このスクリプトは次を実行します。

- `.env.example` から `.env` を作成
- Python 仮想環境を作成し、backend 依存をインストール
- Alembic migration を実行
- デモデータを投入し、検索インデックスを再作成
- frontend 依存をインストール

手動で実行する場合:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\seed_demo_data.py
.\.venv\Scripts\python.exe scripts\rebuild_search_index.py
cd frontend
npm install
cd ..
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -m alembic upgrade head
.venv/bin/python scripts/seed_demo_data.py
.venv/bin/python scripts/rebuild_search_index.py
cd frontend
npm install
cd ..
```

Backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

macOS / Linux:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

ブラウザで `http://localhost:5173` を開きます。Vite は `/api` を `http://127.0.0.1:8000` にプロキシします。

### Environment

`.env.example` をコピーして `.env` を作成します。

```env
POSTGRES_USER=forme_not
POSTGRES_PASSWORD=forme_not
POSTGRES_DB=forme_not
POSTGRES_PORT=5432

DATABASE_URL=postgresql://forme_not:forme_not@localhost:5432/forme_not

DEFAULT_ACCOUNT_ID=00000000-0000-0000-0000-000000000001
DEFAULT_ACCOUNT_EMAIL=debug@example.local

# Optional. If empty, search uses the local fallback embedding.
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
SEARCH_FALLBACK_EMBEDDING_DIM=384
```

Docker Compose の backend コンテナも `.env` の `DATABASE_URL` をそのまま使います。テストだけ local DB を使う場合は `scripts/run_tests_local.ps1` を使います。

### よく使うコマンド

```powershell
# PostgreSQL only, for app-local DB development
docker compose --profile local-db up -d db

# Backend tests with disposable local test DB
.\scripts\run_tests_local.ps1

# Frontend production build
cd frontend
npm run build

# Demo data reset
.\.venv\Scripts\python.exe scripts\seed_demo_data.py --clear-only
.\.venv\Scripts\python.exe scripts\seed_demo_data.py
.\.venv\Scripts\python.exe scripts\rebuild_search_index.py
```

macOS / Linux では `.\.venv\Scripts\python.exe` を `.venv/bin/python` に置き換えてください。

### Troubleshooting

- `DATABASE_URL or DB_URL must be set`: `.env` がプロジェクトルートにあるか確認してください。
- DB 接続に失敗する: `docker compose ps` で `db` が healthy になっているか確認してください。
- Port conflict: `.env` の `POSTGRES_PORT`、`BACKEND_PORT`、`FRONTEND_PORT` を変更してください。
- 検索が OpenAI を使わない: `OPENAI_API_KEY` が空の場合はローカルの fallback embedding を使う仕様です。

## Screenshots

以下は `scripts/seed_demo_data.py` で投入したデモデータの画面です。

| Home overview | Record context |
| --- | --- |
| ![Home overview](docs/screenshots/home-overview.png) | ![Record context](docs/screenshots/record-context.png) |

| Memory search | Person dashboard |
| --- | --- |
| ![Memory search](docs/screenshots/memory-search.png) | ![Person dashboard](docs/screenshots/person-dashboard.png) |

## Testing

テスト全体の方針、実行方法、領域別カバレッジは [docs/testing/README.md](docs/testing/README.md) にまとめています。

## 主な機能

- やり取りの記録: 会話、通話、メッセージ、出来事メモを保存
- 会話前の確認: 相手ごとの最近の記録、共有済み/未共有の話題を整理
- 階層管理: コミュニティと話題を親子構造で管理
- 思い出す検索: キーワード検索と埋め込み検索で曖昧な記憶から検索
- レスポンシブUI: PC向けサイドナビとスマートフォン向けタブ/スワイプUI

## 技術スタック

| Layer | Tools |
| --- | --- |
| Frontend | React 18, TypeScript, Vite |
| Backend | FastAPI, Pydantic, SQLAlchemy, SQLModel |
| Database | PostgreSQL, Alembic |
| Search | OpenAI Embeddings optional, local hash embedding fallback |
| Test | unittest, FastAPI TestClient |

## 構成

```text
4-me-not/
  backend/      FastAPI app, models, services
  frontend/     React / Vite UI
  migrations/   Alembic migrations
  scripts/      setup, demo data, search index, smoke helpers
  tests/        backend tests
  docs/         screenshots and notes
```

```mermaid
flowchart LR
  UI["React / Vite"] --> API["FastAPI API"]
  API --> Service["Service layer"]
  Service --> DB[("PostgreSQL")]
  Service --> Search["Search index"]
  Search -. optional .-> OpenAI["OpenAI Embeddings API"]
```

## API

起動後は以下から確認できます。

- Health check: `GET http://127.0.0.1:8000/api/health`
- FastAPI docs: `http://127.0.0.1:8000/docs`

主要な API は人物、コミュニティ、話題、やり取り、人物ダッシュボード、検索です。

## 補足

検索設計、共有度、現在の制約、今後やりたいことは [docs/technical-notes.md](docs/technical-notes.md) にまとめています。
