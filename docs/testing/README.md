# テスト概要

このフォルダは、4-me-not のテスト方針、実行方法、カバレッジ範囲をまとめる入口です。
個別のテストファイルごとの詳細は、下の「詳細ページ」から確認します。

## 実行方法

Windows でローカルの disposable PostgreSQL を使って、バックエンドとフロントエンドのテストをまとめて実行します。

```powershell
.\scripts\run_tests_local.ps1
```

バックエンドだけ確認したい場合は、フロントエンドテストを省略できます。

```powershell
.\scripts\run_tests_local.ps1 -SkipFrontend
```

テスト DB を作り直してから実行したい場合は、次を使います。

```powershell
.\scripts\run_tests_local.ps1 -ResetDbVolume
```

既に DB を用意している場合は、バックエンドテストを直接実行できます。

```powershell
.\.venv\Scripts\python.exe -m scripts.run_tests --db-url postgresql://forme_not@127.0.0.1:55432/forme_not --migrate
```

フロントエンドテストだけ実行する場合は、`frontend` 配下で Vitest を実行します。

```powershell
cd frontend
npm test
```

## テスト構成

| 領域 | 主なファイル | 確認していること |
| --- | --- | --- |
| API スモーク | `tests/test_api_smoke.py` | health check、参照データ、やり取り記録、検索、人物ダッシュボード、概要 API |
| 認証 | `tests/test_auth.py` | 登録、ログイン、ログアウト、セッション Cookie、アカウントスコープ |
| 参照データと記録 | `tests/test_reference_interaction_expanded.py` | 人物、コミュニティ、トピック、やり取りの入力検証、hidden 制御、削除時の整合性 |
| タスク | `tests/test_task_workflow_expanded.py` | タスク候補抽出、手動作成、更新、完了/再オープン、候補の承認/却下、検索連携 |
| タスク候補抽出 | `tests/test_task_candidate_extraction.py` | 日本語の期限表現、タスクらしい文だけを候補化する判定 |
| 検索 | `tests/test_search_expanded.py` | インデックス作成、対象種別フィルタ、日付範囲、fuzzy、検索ログ、RAG 回答、embedding fallback、キャッシュ |
| カレンダーとリマインダー | `tests/test_calendar_reminder_expanded.py` | 予定作成、参加者、時刻検証、検索インデックス、外部 ID 重複、リマインダー日時 |
| バックグラウンド処理 | `tests/test_interaction_background_processing.py` | やり取り保存後の AI 処理、検索・タスク候補などの後続処理キュー |
| テスト基盤 | `tests/test_support.py` | TestClient、DB fixture、テストデータ作成、クリーンアップ |
| フロントエンド | `frontend/src/pages/interactionNew/offlineInteractions.test.ts` | オフライン時の記録キュー、再送、状態管理 |

## 優先度サマリ

現在のテスト数は、バックエンド `100` 件、フロントエンド `4` 件です。
優先度はテストコードにタグとしては持たせず、このドキュメント上で「どこを厚く守るか」の運用目安として扱います。

| 優先度 | 現在の守り方 | 主な対象 | 追加・修正時の扱い |
| --- | --- | --- | --- |
| P0 | 主要ワークフローとデータ保護を広めに固定 | 認証、記録、検索、人物ダッシュボード、タスク候補、予定、hidden/アカウント境界 | 仕様変更時は同時に更新する。失敗したらリリースを止める |
| P1 | 境界条件と状態遷移を厚めに固定 | UUID/必須項目/重複/日付範囲、タスク承認・却下、検索キャッシュ、一覧順序 | 関連機能を触ったら追加または更新する |
| P2 | 補助ロジックと局所的な UI 状態を固定 | 期限表現の抽出、検索スコア helper、embedding fallback、オフラインキュー、バックグラウンド処理 | 壊れると不便だが、狭い範囲で直せるものを押さえる |

| 領域 | 現在の件数 |
| --- | ---: |
| API スモーク | 9 |
| 認証 | 2 |
| 参照データと記録 | 28 |
| タスク | 21 |
| タスク候補抽出 | 2 |
| 検索 | 25 |
| カレンダーとリマインダー | 11 |
| バックグラウンド処理 | 2 |
| フロントエンド | 4 |

## 優先して守る観点

- 主要ワークフローが壊れていないこと: 記録、検索、人物確認、タスク候補、予定、リマインダー。
- データ境界が漏れないこと: hidden な人物/コミュニティ、別アカウントのデータ、削除済み参照。
- 検索結果が古い状態を残さないこと: タスク却下、人物変更、予定削除、再インデックス。
- 外部サービスがなくても動くこと: `OPENAI_API_KEY` が空、または OpenAI request が失敗した場合はローカル fallback を使う。
- テスト後にデータを残しにくいこと: `[TEST:` prefix のデータを cleanup する。

## 追加するときの目安

新しい API やサービスを追加するときは、まずサービス層または API 層で正常系と代表的な異常系を固定します。
画面で複数状態を扱う変更は、状態変換の小さな単位をフロントエンドテストに寄せます。

特に次の変更は、既存テストの拡張対象です。

- 新しい参照データ種別を追加する。
- 検索対象やランキング条件を増やす。
- タスク候補、予定、リマインダーの自動生成ロジックを変える。
- アカウントスコープや hidden 制御に関わるクエリを変更する。
- オフライン保存、再送、バックグラウンド処理の順序を変える。

## 詳細ページ

- [API スモーク](test_api_smoke.md)
- [認証](test_auth.md)
- [カレンダーとリマインダー](test_calendar_reminder_expanded.md)
- [バックグラウンド処理](test_interaction_background_processing.md)
- [参照データとやり取り](test_reference_interaction_expanded.md)
- [検索](test_search_expanded.md)
- [テスト基盤](test_support.md)
- [タスク候補抽出](test_task_candidate_extraction.md)
- [タスクワークフロー](test_task_workflow_expanded.md)
