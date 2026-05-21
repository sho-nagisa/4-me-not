# 4-me-not

「誰と、どこで、何を、どこまで話したか」を記録して、次に会う前に思い出せるようにする個人向けの人間関係メモアプリです。

会話・メッセージ・面談などのやり取りを、人物、コミュニティ、話題、共有度と一緒に保存します。曖昧な記憶から過去の会話や相手を探せる「思い出す検索」も備えています。

## Screenshots

以下は `scripts/seed_demo_data.py` で投入したデモデータの画面です。

| Home overview | Record context |
| --- | --- |
| ![Home overview](docs/screenshots/home-overview.png) | ![Record context](docs/screenshots/record-context.png) |

| Memory search | Person dashboard |
| --- | --- |
| ![Memory search](docs/screenshots/memory-search.png) | ![Person dashboard](docs/screenshots/person-dashboard.png) |

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
  scripts/      demo data, search index, smoke helpers
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

## セットアップ

`.env` をプロジェクトルートに作成します。

```env
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/DB_NAME

# Optional. If omitted, search uses the local fallback embedding.
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

バックエンドを起動します。

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\seed_demo_data.py
.\.venv\Scripts\python.exe scripts\rebuild_search_index.py
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

フロントエンドを起動します。

```powershell
cd frontend
npm install
npm run dev
```

ブラウザで `http://localhost:5173` を開きます。Vite は `/api` を `http://127.0.0.1:8000` にプロキシします。

## よく使うコマンド

```powershell
# Backend tests
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Frontend production build
cd frontend
npm run build

# Demo data reset
.\.venv\Scripts\python.exe scripts\seed_demo_data.py --clear-only
.\.venv\Scripts\python.exe scripts\seed_demo_data.py
.\.venv\Scripts\python.exe scripts\rebuild_search_index.py
```

## API

起動後は以下から確認できます。

- Health check: `GET http://127.0.0.1:8000/api/health`
- FastAPI docs: `http://127.0.0.1:8000/docs`

主要なAPIは人物、コミュニティ、話題、やり取り、人物ダッシュボード、検索です。

## 補足

検索設計、共有度、現在の制約、今後やりたいことは [docs/technical-notes.md](docs/technical-notes.md) にまとめています。
