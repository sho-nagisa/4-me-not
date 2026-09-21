タスクID：W31-03

状態：完了（不変Revision・current projection・局所transaction参加の範囲）

分類・運用状態：core、アプリ未接続。認可/依存port未接続なら拒否/保留。

今回の責務とv0.4差分：W31-02の実装・検査合格を確認して開始。MemoryDraft/MemoryRevision/ItemView、W30のconfirmed_by_user、SourceStorage/SourceEvidenceを再利用。stable Item記録、insert-only Revision、親鎖、current pointerを分離し、get_item/get_revisionを実装した。

対応REQ/AUTO/V04・仕様箇所：REQ-AUTO-008/019、対応AUTOの局所部分。docs/state-model・data-contract・migration・feature-control、MemoryDraft.additional_dependency_refs/MemoryRevision.required_features。

変更ファイル（全て新規）：
- C:\Users\keima\Desktop\4-me-not\backend\services\memory_revisions.py:1 — +125/-0
- C:\Users\keima\Desktop\4-me-not\docs\implementation\W31-03-contract.md:1 — +38/-0
- C:\Users\keima\Desktop\4-me-not\tests\memory\test_memory_revisions.py:1 — +155/-0
- C:\Users\keima\Desktop\4-me-not\docs\implementation\W31-03-start.json:1 — 開始hash基準。
- C:\Users\keima\Desktop\4-me-not\docs\implementation\W31-03-validation-k_hc17bg.json:1 — 最終検査証拠。初回validation-3e0fdepk.jsonと両runのログは保持。
- C:\Users\keima\Desktop\4-me-not\docs\implementation\W31-03-report.md:1 — 本報告。

不変条件の確認根拠：旧Revision/原文を変更せず現在版を更新。parent/current/item/vault整合、不存在・provisional・消去後履歴の拒否を検査。current欠落時は同Itemの新規扱いも拒否。ai_hypothesisと追加依存/required_features保持。空の自己申告を信頼せず信頼する依存結果との不一致は拒否。開始時から意図外差分0、検査中変更0、既存models/未コミット変更/過去証拠/ZIP/19作業版保持。

契約/API/DTO・互換/移行：wire変更なし。内部project_inはW31-04の外側transactionへ参加する部品でありapproveChangeではない。basis_headはprojection基準、vault全体HEADとの整合はW31-04。current/payload/履歴の分離とDependencyPort境界はW31-03-contract.md。DB移行なし。

停止・取消・復旧：current更新途中の失敗でRevision/Item追加もrollbackするfake取引。履歴にも現在AccessPortとDependencyPortを適用。実失効barrier/物理消去/復元/過去効果回収は未実施。

テスト：型/局所storage fake結合 / cwd C:\Users\keima\Desktop\4-me-not / Python -B -X utf8 docs/implementation/validate_storage_tasks.py W31-03を実行。初回は追加テストの配置ミスによるNameErrorで終了1。テスト配置だけ修正し、最初のログ/証拠6ファイルを明示的な今回の履歴としてallowlistへ加えて同runner.mainを再実行。開始基準は更新していない。最終終了0、局所46件（今回11＋前段35）、基準検査3件、仕様114件、旧版25+11件、git diff --check合格。実PythonはC:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。子コマンド/cwd/log/hashはvalidation-k_hc17bg.json。

未実装・未実施・未決：実DB/認証/本人確認/Gate/closure計算/失効伝播/HTTP/UI/実アプリ受入は未実施。fakeの認可と依存集合はtest oracleのみ。DependencyPort未接続なら、依存なしと申告されても保留。W42-03で全ref/producer/版/vault/現在利用を照合する。既存DRAFT/DB保存案/Actor写像は未承認のまま。今回局所条件に未達なし。

レビュー：自己点検のみ、独立レビュー未実施。テスト配置ミスは修正・全体追試済み。

情報境界：合成Source/Revisionのみ、本文を通常ログ/例外へ出さず、実ユーザーDB・外部送信・公開・pushなし。

引継ぎ：project_inをContent Ledger transactionへ接続する次の推奨IDはW31-04。
