# 4-me-not

人との関りを改めてみることで大切にしていきたと思い作っています。
どの人とどのくらい関わったか、何をしたかどこにいたかを振り返るきっかけになればいいと思います。
最終的にカレンダーから読み取り自動で記録できるようにしていきたいと思っています。

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

## 工夫したポイント

### 検索キャッシュ

初回検索時に `search_documents` からメモリ上の検索キャッシュを作成します。キャッシュには、パース済みのembedding、タイトル、要約、検索用テキスト、人物名、コミュニティパス、話題パスを保持するようにしています。

これにより、検索のたびに同じ検索ドキュメントをPostgreSQLから読み直したり、`embedding_json` を毎回パースしたりする処理を避けています。現在のローカルデモデータでの、初回検索後の検索は約20〜30msで実行できます。

検索結果に関わるデータが変わる可能性がある操作では、キャッシュを破棄します。

- interactionのindex更新
- 検索indexの全再構築
- 人物の作成、表示状態の変更、削除
- コミュニティの作成、表示状態の変更、削除
- 話題の作成

### 検索システム

検索結果は単一の指標だけではなく、複数のスコアを組み合わせて並べています。

```text
0.55 * semantic_score
+ 0.35 * keyword_score
+ 0.10 * recency_score
```

人物名、話題名、具体的な言葉が一致したときの強さを残しつつ、「面接 志望動機」「返信頻度 気になる人」のような曖昧な思い出し方にも対応できるようにしています。

### 思い出すためのデータ設計

会話記録は、本文だけでなく、人物、コミュニティ、話題、やり取りの種類、共有度、日時、補足メモと一緒に保存しています。これにより、単純な全文検索だけでなく、「どこで」「誰と」「何について」話したかという文脈からも探せるようにしています。

また、`share_level` によって「すでに話したこと」と「まだ話していないこと」を分けています。人物ダッシュボードでは、単なる履歴確認ではなく、次に会う前の会話準備に使える情報として整理できます。

## 設計メモ

### 検索

人物、コミュニティ、話題、会話記録から検索用ドキュメントを作成しています。各ドキュメントには、検索用に整形したテキストとembeddingを保存します。

`OPENAI_API_KEY` が設定されている場合はOpenAI Embeddingsを利用します。APIキーがない場合は、外部サービスなしでデモを動かせるように、決定的に生成できるローカルのhash embeddingにフォールバックします。

検索スコアは、以下の要素を組み合わせています。

- semantic similarity
- keyword coverage
- recency

検索結果は、人物、会話、コミュニティ、話題ごとにグルーピングして返します。また、上位結果から「誰のことを探していそうか」を整理するための決定的なsummaryも返します。

### 共有度

記録した情報を、すべて同じように会話で扱えるものとは見なしていません。各会話記録には共有度を持たせています。

- `SHARED`: すでに話した
- `PARTIAL`: 一部だけ話した
- `WITHHELD`: まだ話していない

これにより、人物ダッシュボードで「次に自然に話せそうなこと」と「まだ直接触れない方がよいこと」を分けて確認できます。

### アカウントスコープ

DBスキーマには `accounts` と各主要テーブルの `account_id` を用意しています。現時点ではローカルデモ用に固定のデフォルトアカウントを使っています。ポートフォリオとしての実行しやすさを優先しつつ、後から認証を追加できる構造にしています。

## 現在の制約

- 認証はまだ実装していません。現在は固定のデフォルトアカウントを使っています。
- AIによる解析、insight生成、関係性更新、カレンダー同期はサービスの枠だけあり、本番機能としては未実装です。
- 初回検索時にメモリキャッシュを作っていますが、大規模データではpgvectorやPostgreSQL全文検索など、DB側で検索を最適化する設計が必要です。
- フロントエンドのE2Eテストはまだありません。
- Docker Compose、スクリーンショット、デモ動画などの公開用資料はまだ含めていません。

## 今後やりたいこと

- ログインとユーザーごとのセッション管理を追加する
- PostgreSQL、バックエンド、フロントエンドをまとめて起動できるDocker Composeを追加する
- READMEにスクリーンショットや短いデモ動画を追加する
- データ量が増えた場合に備えて、pgvectorやDB側ランキングに移行する
- 主要なユーザーフローにPlaywrightのE2Eテストを追加する
- 自由記述メモから話題、リマインダー、人物insightを抽出するAI解析を実装する
- 構造化ログやエラー監視を整備する
