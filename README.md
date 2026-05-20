# 4-me-not

「誰と、どこで、何を、どこまで話したか」を記録し、次に会う前に思い出せるようにする個人向けの人間関係メモアプリです。

会話の内容だけでなく、人物、所属コミュニティ、話題の階層、共有度を一緒に保存します。曖昧な記憶から人物や過去の会話を探せる検索機能も備えています。

## Features

- 会話・面談・通話・メッセージなどのやり取りを記録
- 人物ごとに最近話した内容、話した話題、まだ話していない話題を確認
- コミュニティと話題を階層構造で管理
- 「話した」「一部だけ話した」「話していない」の共有度を記録
- キーワード検索と埋め込みベース検索を組み合わせた「思い出す検索」
- PC向けのサイドナビUIと、スマートフォン向けのタブ/スワイプUI
- AlembicによるDBマイグレーション
- デモデータ投入スクリプトとAPIスモークテスト

## Tech Stack

| Layer | Tools |
| --- | --- |
| Frontend | React 18, TypeScript, Vite |
| Backend | FastAPI, Pydantic, SQLAlchemy, SQLModel |
| Database | PostgreSQL, Alembic |
| Search | OpenAI Embeddings optional, local hash embedding fallback |
| Test | unittest, FastAPI TestClient |

## Architecture

```mermaid
flowchart LR
  UI["React / Vite frontend"] --> API["FastAPI API"]
  API --> Service["Service layer"]
  Service --> DB[("PostgreSQL")]
  Service --> Search["Search index builder"]
  Search --> DB
  Search -. optional .-> OpenAI["OpenAI Embeddings API"]
```

```mermaid
erDiagram
  ACCOUNT ||--o{ PERSON : owns
  ACCOUNT ||--o{ COMMUNITY : owns
  ACCOUNT ||--o{ TOPIC : owns
  ACCOUNT ||--o{ INTERACTION : owns
  PERSON ||--o{ INTERACTION : has
  COMMUNITY ||--o{ INTERACTION : context
  TOPIC ||--o{ INTERACTION : topic
  PERSON ||--o{ SEARCH_DOCUMENT : indexed_as
  COMMUNITY ||--o{ SEARCH_DOCUMENT : indexed_as
  TOPIC ||--o{ SEARCH_DOCUMENT : indexed_as
  INTERACTION ||--o{ SEARCH_DOCUMENT : indexed_as
```

## Project Structure

```text
4-me-not/
  backend/
    app/          FastAPI app and routers
    db/           SQLAlchemy engine/session setup
    models/       ORM models
    services/     application logic and search logic
    testing/      demo-data helpers
  frontend/
    src/          React UI
  migrations/     Alembic migrations
  scripts/        seed/search/test helper scripts
  tests/          backend smoke and service tests
```

## Setup

### 1. Environment

Create `.env` in the project root.

```env
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/DB_NAME

# Optional. If omitted, search uses the local fallback embedding.
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

The application uses the `formegot` PostgreSQL schema. The schema and tables are managed by Alembic migrations.

### 2. Backend

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\seed_demo_data.py
.\.venv\Scripts\python.exe scripts\rebuild_search_index.py
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to `http://127.0.0.1:8000`.

## Demo Data

The demo seed creates sample communities, topics, people, and interactions around university life, job hunting, internships, and personal relationships.

```powershell
.\.venv\Scripts\python.exe scripts\seed_demo_data.py
.\.venv\Scripts\python.exe scripts\rebuild_search_index.py
```

To remove only the generated demo data:

```powershell
.\.venv\Scripts\python.exe scripts\seed_demo_data.py --clear-only
```

## Test

Backend:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend production build:

```powershell
cd frontend
npm run build
```

Current smoke tests cover:

- health check
- reference data CRUD
- community duplicate validation
- visibility and delete behavior
- interaction recording
- search endpoint
- person dashboard
- interaction overview
- post-save background processing hooks

## API Overview

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | health check |
| `GET /api/persons` | list people |
| `POST /api/persons` | create person |
| `GET /api/communities` | list communities |
| `POST /api/communities` | create community |
| `GET /api/topics` | list topics |
| `POST /api/topics` | create topic |
| `GET /api/interactions` | list and filter interactions |
| `POST /api/interactions` | record interaction |
| `GET /api/interactions/overview` | home summary |
| `GET /api/persons/{person_id}/dashboard` | person dashboard |
| `GET /api/search` | memory search |

## Design Notes

### Search

Search documents are built from people, communities, topics, and interactions. Each document stores a normalized text representation and an embedding.

If `OPENAI_API_KEY` is available, the app uses OpenAI embeddings. Without an API key, it falls back to a deterministic local hash embedding so the demo can run without external services.

Search scoring combines:

- semantic similarity
- keyword coverage
- recency

The response also groups results by target type and returns a deterministic summary that helps identify likely people and related records.

### Share Level

The app does not treat all remembered information as equally shareable. Each interaction has a share level:

- `SHARED`: already talked about
- `PARTIAL`: partially talked about
- `WITHHELD`: not talked about yet

This allows the person dashboard to separate conversation-safe topics from topics that should not be brought up directly yet.

### Account Scope

The database schema already has `accounts` and `account_id` on core tables. The current app uses a fixed default account for local/demo use. This keeps the portfolio demo simple while leaving a path to add authentication later.

## Current Limitations

- Authentication is not implemented yet. The app currently uses a fixed default account.
- AI parsing, insight generation, relation updates, and calendar sync have service placeholders, but are not production features yet.
- Search currently loads candidate documents from the database and scores them in application code. For larger datasets, pgvector or PostgreSQL full-text search would be a better production design.
- The frontend has no E2E tests yet.
- Deployment artifacts such as Docker Compose and screenshots are not included yet.

## Future Work

- Add login and per-user session handling
- Add Docker Compose for PostgreSQL, backend, and frontend
- Add screenshots or a short demo video to the README
- Replace in-memory search scoring with pgvector or a database-backed ranking strategy
- Add Playwright tests for the main user flows
- Implement AI parsing for extracting topics, reminders, and person insights from free-form notes
- Improve observability with structured logging and error monitoring
