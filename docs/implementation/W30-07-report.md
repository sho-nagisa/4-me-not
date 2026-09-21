# W30-07 指定形式の完了報告

タスクID：W30-07
状態：完了（仕様資材・局所契約の整合確認範囲）
分類・運用状態：core。実配備なし、Gate本体・実認証接続・実アプリ受入は未実施。

今回の責務とv0.4差分：W30-06報告・114件と旧版証拠、指定仕様を確認。W30-01〜06の判断と対応表を一つのレビュー入口へ整理し、76 REQ/AUTO/V04を追跡。既存参照テストを補助Schemaにも拡張した（原仕様比+1/-1）。既存86定義・38 API・46操作・25機能は再定義していない。W30-05で検出した未対応写像は未決として保持。

対応REQ/AUTO/V04・仕様箇所：REQ-AUTO-001〜036/AUTO-001〜036、REQ-V04-001〜040/V04-001〜040の全参照整合。特にAUTO-003/V04-004/V04-037の独立軸・依存・版の回帰。Schema/OpenAPI/fixtures/requirements/acceptance、diagrams-indexの6図と本文を既存test_contract_assets/test_policy_reference/test_v04_assetsで検査。受入本文の参照検査を実アプリ受入に読み替えない。

変更ファイル（全て今回repoへ新規追加、削除0。既存test_contract_assets.pyの原仕様からの実差分は参照対象1行の+1/-1）：
- C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/tests/test_contract_assets.py:1 — 参照検査/レビュー/再現/証拠、+162/-0
- C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/docs/w30-review.md:1 — 参照検査/レビュー/再現/証拠、+134/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-07-validate.ps1:1 — 参照検査/レビュー/再現/証拠、+111/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-07-validation.json:1 — 参照検査/レビュー/再現/証拠、+160/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-07-published.log:1 — 参照検査/レビュー/再現/証拠、+90/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-07-active.log:1 — 参照検査/レビュー/再現/証拠、+119/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-07-baselines.log:1 — 参照検査/レビュー/再現/証拠、+48/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-07-report.md:1 — 本報告、+41/-0

不変条件の確認根拠：原Schema全制約の比較、全資材/参照規則合格。W30-04の12ファイルhash一致、196コードhashはW30-01および検査前後から変更0。既存追跡15ファイル331追加/5削除、既存未追跡・modelsを保持。参照ZIP SHA256 811A9B2E19FE4CFF7C3AE106D4B2115D40B83A67E429D3F8C8509B64FA307C5E不変。同期sources/inputs/archive原本は読取専用。

契約/API/DTO・互換/移行：既存wire/API変更なし。配布物v0.4、データ契約3、HTTP案v3を維持。後続の入口は原ZIP＋19ファイルの部分作業版docs/spec/v0.4。完全配布物の再署名ではない。ファイルhashとSPEC_ROOTは今回validation.json、再現はW30-07-validate.ps1。W30-01〜06の証拠は当時の履歴として保持。

停止・取消・復旧：実作用なし。現在の消去/撤回を過去snapshotで巻き戻さず、未承認委任を有効化しない。新たな許可や停止barrierは実装していない。過去送信・完了行動の回収も未実施。

テスト：起点 C:/Users/keima/Desktop/4-me-not、& ./docs/implementation/W30-07-validate.ps1、終了0。
- 原配布物の仕様資材・参照規則 / C:\Users\keima\AppData\Local\Temp\4-me-not-W30-07-run-40813f5c15f643aca90fc1e9f4e54d9a\published\4-me-not-collab-v0.4 / C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8 -m unittest discover -s tests -p test_*.py -v / exit=0 / 合格 85件 / C:\Users\keima\Desktop\4-me-not\docs\implementation\W30-07-published.log
- 作業版の仕様資材・局所契約・参照規則 / C:\Users\keima\AppData\Local\Temp\4-me-not-W30-07-run-40813f5c15f643aca90fc1e9f4e54d9a\4-me-not-collab-v0.4 / C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8 -m unittest discover -s tests -p test_*.py -v / exit=0 / 合格 114件 / C:\Users\keima\Desktop\4-me-not\docs\implementation\W30-07-active.log
- 旧版の仕様資材・参照規則 / C:\Users\keima\AppData\Local\Temp\4-me-not-W30-07-run-40813f5c15f643aca90fc1e9f4e54d9a\4-me-not-collab-v0.4 / C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe scripts/check_baselines.py / exit=0 / 合格 25+11件 / C:\Users\keima\Desktop\4-me-not\docs\implementation\W30-07-baselines.log
原配布物85件と作業版114件（85＋W30追加29）を別ディレクトリで実行。旧版v0.3 25/v0.1 11は別実行。Python3.12.14/jsonschema4.26.0・UTF8/依存パスはvalidation.json。初回合格後、レビュー文書の検査状態確定に合わせ再実行して全合格。subTestを件数に加算しない。git diff --checkは終了0。

未実装・未実施・未決：全D1〜D9、W30-03の機微提示/状態写像、W30-04のsystem登録・wire制約、W30-05 M1〜M4をw30-review.mdに追跡。M1 evaluateUse不足9クラス、M2 counterevidence_search未対応、M3直接操作なし8機能、M4予定委任/機微提示/外部AIの具体対象。全追加案/専用経路案は公開用途・確認範囲・負担が変わるため本人/contract owner判断待ちで、その写像変更・実接続は停止。DRAFTを承認へ変更していない。独立した資材検査はこの判断に依存しない。

Gate本体・実認証・確認receipt・DB移行/復元・API/UI/実機・実LLM/外部送信受入は未実施。今回の必須局所検査に未達なし。実アプリ/core全体の完成条件は未達のまま。図はソース一致と意味の自己点検のみで、描画/視覚検証は未実施。00-current図の7ルーターは原配布物の旧固定repoを表すため、現在repoの事実はW30-01棚卸しを参照する。

レビュー：Codex自己点検、独立レビュー未実施。追加Schemaが従来の2ファイル限定参照検査から漏れる点を修正。設計図・旧snapshot・現アプリを区別し、既知の未対応が残ることを明記。

情報境界：合成fixtureとコード読取のみ。実原文・秘密の読取/通常ログ出力なし、外部payload送信・DB更新・公開・pushなし。

引継ぎ：既存E1/E2/E3/E6 portの未接続と全DRAFTを保持。EXECUTION_ORDER.md:20の次の推奨IDはW43-01。W30-07以降には着手しない。
