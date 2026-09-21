タスクID：W31-02

状態：完了（指定されたstorage port・決定的fake・局所操作と試験の範囲）

分類・運用状態：core。アプリ未接続。認可port未接続時は拒否。

今回の責務とv0.4差分：前3件の報告/実装/証拠hashと原ZIP＋作業版の指定仕様を確認。ImportRequest/Source/ImportReceiptとSourceEvidenceを再利用し、import_source/get_sourceをatomic storage portへ接続した。既存OCR/accountの保存とは別責務であり、既存models/DBを置換していない。

対応REQ/AUTO/V04・仕様箇所：REQ-AUTO-001/015/019、対応AUTO、V04-001/026/037の局所部分。docs/api-semantics・data-contract・migration、ImportRequest/ImportReceipt/Source。

変更ファイル（全て新規）：
- C:\Users\keima\Desktop\4-me-not\backend\services\memory_storage.py:1 — +49/-0
- C:\Users\keima\Desktop\4-me-not\backend\services\source_storage.py:1 — +73/-0
- C:\Users\keima\Desktop\4-me-not\docs\implementation\W31-02-contract.md:1 — +40/-0
- C:\Users\keima\Desktop\4-me-not\docs\implementation\validate_storage_tasks.py:1 — +14/-0
- C:\Users\keima\Desktop\4-me-not\tests\memory\storage_fakes.py:1 — +68/-0
- C:\Users\keima\Desktop\4-me-not\tests\memory\test_source_storage.py:1 — +112/-0
- C:\Users\keima\Desktop\4-me-not\docs\implementation\W31-02-start.json:1 — 開始時hash基準。
- C:\Users\keima\Desktop\4-me-not\docs\implementation\W31-02-validation-izz7377f.json:1 — 実コマンド/cwd/終了値/件数/hash/ログ。
- C:\Users\keima\Desktop\4-me-not\docs\implementation\W31-02-report.md:1 — 本報告。検査ログ5本は証拠JSONのresultsに絶対パスを記録。

不変条件の確認根拠：同一再送でSource1件、ID/原文/時刻不変。異内容キー拒否。Source/receipt/commitの3箇所失敗で全rollback。vault/caller/固定operationで隔離。初回/再送/getSource返却前に現在認可・消去portを検査。開始時から意図外差分0、検査中変更0、参照ZIP hash一致。既存models・未コミット変更・過去証拠・19仕様作業版保持。

契約/API/DTO・互換/移行：wire変更なし。dict入口のcanonical値と原文UTF-8保持であり、HTTP転送JSONの空白byte保持ではない。HTTP route/Header長制約のadapterは未接続。契約2は明示移行なしで受理しない。詳細とDB案はW31-02-contract.md。

停止・取消・復旧：fake取引は失敗で破棄。認可未接続は拒否。解析を呼ばず保存成功と分離。実DB rollback/物理消去/過去効果回収は未実施。

テスト：局所storage port/fake結合 / cwd C:\Users\keima\Desktop\4-me-not / & 'C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -X utf8 docs/implementation/validate_storage_tasks.py W31-02 / 終了0。局所35件（今回9＋既存26）、基準検査3件、仕様114件、旧版25+11件、git diff --check合格。証拠はW31-02-validation-izz7377f.json。各子cwd/コマンド/logも同JSON。最初に今回9件を個別実行し合格後、総合検査を実施した。

未実装・未実施・未決：実DB/HTTP/認証/Gate/queue/解析/実ユーザー移行/実アプリ受入未実施。fakeはtests内だけで、認証や永続性の実証ではない。DB永続adapter案・account/vault写像・OCR Source移行はDRAFTのまま。既存PostgreSQLへ別表/一意制約を設ける案はID/認証/移行へ影響するため、これに依存する実接続は停止。今回のport/fake局所条件は達成し、後続の独立した局所作業を妨げない。

レビュー：自己点検。今回の独立レビュー未実施。

情報境界：合成データのみ。通常ログ/例外へ本文を含めず、外部送信・本番DB・公開・pushなし。

引継ぎ：現在認証/ACL/消去の整合境界はW33等で接続。次の推奨IDはW31-03。
