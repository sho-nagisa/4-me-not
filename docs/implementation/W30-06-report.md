# W30-06 指定形式の完了報告

タスクID：W30-06
状態：完了（局所移行契約・合成例の範囲）
分類・運用状態：core。実配備なし、Gate/実認証/実アプリ受入は未実施。

今回の責務とv0.4差分：W30-05報告・109件の検査証拠と指定仕様を確認。v0.4配布物/契約3/v3と旧v2/v1/現apiの入口・互換・拒否・移行証拠・差戻しを表にした。旧ZIPの合成Sourceを既存旧Schemaで検証し明示変換する純粋な例を追加。原文/主体/IDと全フィールドを版以外保持し、同じ入力は同じ候補と監査digestを返す。実DBの移行/冪等transactionではない。

対応REQ/AUTO/V04・仕様箇所：REQ-AUTO-015/019、AUTO-015/019、REQ-V04-037/V04-037を局所検査。AUTO-003/V04-004も回帰。根拠はmigration/data-contract/api-semantics、ImportRequest/Source/MemoryRevision/Error、OpenAPIのinfoとv3 path。API・既存wireは変更なし。

変更ファイル（新規追加、削除0。migration.mdは原仕様31行＋追記22行、原仕様比+22/-0）：
- C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/docs/migration.md:1 — 移行契約/例/検査/証拠、+53/-0
- C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/contracts/migration_examples.py:1 — 移行契約/例/検査/証拠、+54/-0
- C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/tests/test_w30_06_migration.py:1 — 移行契約/例/検査/証拠、+70/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-06-validate.ps1:1 — 移行契約/例/検査/証拠、+101/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-06-validation.json:1 — 移行契約/例/検査/証拠、+130/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-06-active.log:1 — 移行契約/例/検査/証拠、+119/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-06-baselines.log:1 — 移行契約/例/検査/証拠、+48/-0
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-06-report.md:1 — 本報告、+36/-0

不変条件の確認根拠：全114件合格と196コードhash不変、参照ZIP hash不変（validation.json）。既存models・未コミット変更・前提のoverlayを保持。原文正規化なし。未知required_featuresは読取限定とし空の非依存へ変換しない。旧承認/share_levelは新用途の許可ではない。原文/人物役割/全由来/採否と真実/配備と認可を保持。

契約/API/DTO・互換/移行：既存wireの受理集合・OpenAPIは変更なし。Sourceにdigestフィールドを捏造せず監査証拠側に全内容hashを持つ。v2とv3の同形データは型だけで出所判定できないので、確認済み取込経路の元契約版を別に照合する。出所の認証自体は未実装。

停止・取消・復旧：v3項目を削っただけのv2逆変換は拒否。旧領域への差戻しは最新の消去/撤回台帳が前提で、台帳不明なら通常利用保留。実backup復元・過去の送信回収は行っていない。

テスト：起点 C:/Users/keima/Desktop/4-me-not、& ./docs/implementation/W30-06-validate.ps1、終了0。
- 仕様資材・局所規則 / C:\Users\keima\AppData\Local\Temp\4-me-not-W30-06-run-f2b96a78387c4328967328424826ca31\4-me-not-collab-v0.4 / C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8 -m unittest discover -s tests -p test_*.py -v / exit=0 / 合格 114件 / C:\Users\keima\Desktop\4-me-not\docs\implementation\W30-06-active.log
- 仕様資材・局所規則 / C:\Users\keima\AppData\Local\Temp\4-me-not-W30-06-run-f2b96a78387c4328967328424826ca31\4-me-not-collab-v0.4 / C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe scripts/check_baselines.py / exit=0 / 合格 25+11件 / C:\Users\keima\Desktop\4-me-not\docs\implementation\W30-06-baselines.log
Python3.12.14/jsonschema4.26.0・UTF8と一時依存を再利用。既存109＋新5＝114件、旧版25＋11。初回合格、subTestを件数に加算しない。

未実装・未実施・未決：実adapter/DB/API/UI/Gate/認証/receipt/復元受入なし。D1〜D6のID/採否/媒体/用途/Task対応は本人判断待ち。具体案は明示対応表＋dry-run比較後に切替、影響はID/時刻/出自/許可範囲/再開意思。自動変換しない。W30-05 M1〜M4は依然未承認で写像変更・実接続を停止。局所例はその判断に依存しない。

レビュー：Codex自己点検、独立レビュー未実施。型だけで偽装版を見破れるという過大な主張を避け、確認済み出所との照合を明記。情報境界：元ZIPの合成fixture、コード読取のみ。実原文・秘密・外部payload送信なし。

引継ぎ：既存E1/E2/E3/E6は未接続・対応判断待ち。次の推奨ID W30-07。本報告後に許可済みの整合確認へ進む。
