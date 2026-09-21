タスクID：W43-01

状態：完了（今回指定の型・境界・局所移行の範囲）

分類・運用状態：core。アプリ未接続。実運用の有効化/配備はしていない。

今回の責務とv0.4差分：W30-07引継ぎ/R1修正報告・証拠と指定仕様を確認。既存backendに同責務の実装がないことを検索確認し、既存Python services配置・unittestを使用。別packageやmodelsの置換はない。既存JSON Schemaを実行時検証に再利用し、旧分類不明を未分類のまま明示移行する。

対応REQ/AUTO/V04・仕様箇所：V04-018/019/037、contracts/memory.schema.jsonのSchemaRole/CognitiveSchemaPayload/EventTime、docs/quality-assessment.md・migration.md・data-contract.md。受入全体の実アプリ合格を意味しない。

変更ファイル：C:/Users/keima/Desktop/4-me-not/ を基点とする絶対パスは以下。行数は別紙W43-01-files.jsonに記録。

- C:/Users/keima/Desktop/4-me-not/backend/requirements.txt:11 — 既存依存へjsonschema[format]追加。
- C:/Users/keima/Desktop/4-me-not/backend/services/memory_contracts.py:1 — 既存Schemaの検証・コピー。
- C:/Users/keima/Desktop/4-me-not/backend/services/schema_roles.py:1 — 役割検証・明示移行。
- C:/Users/keima/Desktop/4-me-not/tests/memory/test_schema_roles.py:1 — 正負fixtureと移行検査。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/validate_local_tasks.py:1 — タスク開始基準と隔離仕様検証。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/test_local_validation.py:1 — 意図外差分の検出試験。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W43-01-contract.md:1 — map・接続境界。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W43-01-start.json:1 — 変更前基準。以後更新しない。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W43-01-validation-19_vouds.json:1 — 新しい検査証拠。対応するlocal/runner/active/baselines/whitespaceログを新規保存。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W43-01-report.md:1 — 本報告。

不変条件の確認根拠：開始時hash基準から許可したファイルだけ変更、意図外差分0、検査中変更0。既存未コミット変更・models・W30履歴・19作業版を保持。ZIP hashはW30-01と一致。純粋変換はstable ID/全旧フィールド/原文digestを保持。認可・自動分類・必須Prediction依存なし。

契約/API/DTO・互換/移行：wire/API変更なし。移行mapはW43-01-contract.md。注入する旧/新契約と由来版は信頼するadapterの責務。新項目を削っただけのデータ契約3→2要求も拒否する。保存や実データの分類判断は行わない。

停止・取消・復旧：局所関数を接続しなければ実作用なし。入力は変更しない。DB適用/ロールバック/過去効果の回収なし。

テスト：型・境界・局所単体 / cwd C:/Users/keima/Desktop/4-me-not / & 'C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 docs/implementation/validate_local_tasks.py W43-01 / 終了0。局所5件、基準検査3件、作業版114件、旧版25+11件合格。git diff --check終了0。各子コマンド・cwd・終了コード・ログはvalidation-19_vouds.jsonに記録。subTestは加算しない。依存は隔離済みspec用jsonschema4.26.0を使用し、アプリ全依存の再インストールは未実施。

未実装・未実施・未決：Gate/実認証/DB保存・移行/API/UI/queue/実機/LLMの結合・実アプリ受入は未実施。本責務は保存portを呼ばず、fakeは配布合成fixtureのみ。M1〜M4/D1〜D9の判断を変更せず、それに依存する接続をしない。今回の局所条件に未達なし。

レビュー：自己点検のみ。今回の変更の独立レビューは未実施。W30 R1の独立再レビュー解消はユーザー報告として受領し、今回のレビューに転用していない。

情報境界：合成fixtureだけ使用。通常ログは検査名/件数/パス、例外はコードのみ。外部送信・本番DB・公開・pushなし。

引継ぎ：Schema注入と保存/Revision接続は後続。EXECUTION_ORDER.mdに従う次の推奨IDはW42-01。
