タスクID：W31-01

状態：完了（Source・根拠位置の型・境界・局所実装の範囲）

分類・運用状態：core。実アプリ未接続、運用の有効化なし。

今回の責務とv0.4差分：W30-07/R1引継ぎ・指定仕様を確認。Source/Message複合ID・vault・由来契約版を照合し、多言語引用から一意なUTF-8区間を算出する。既存JSON SchemaとPython基盤を再利用し、新package/DBモデル/保存サービスは作らない。

対応REQ/AUTO/V04・仕様箇所：REQ-AUTO-001/AUTO-001の原文保持・型の局所部分。docs/data-contract.md・api-semantics.md・migration.md、Source/Message/EvidenceInput/EvidenceSpan/EvidenceLocator/VersionRef。関連AUTO-015/018/019を含むAPI・端末・消去等の実受入全体は対象外。

変更ファイル（追加/削除行数はW31-01-files.json）：

- C:/Users/keima/Desktop/4-me-not/backend/services/source_evidence.py:1 — Source境界・UTF-8位置・媒体/ref形状。
- C:/Users/keima/Desktop/4-me-not/tests/memory/test_source_evidence.py:1 — 多言語/複合ID/契約版/byte境界等。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W31-01-contract.md:1 — 契約・再検証・接続port。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W31-01-start.json:1 — W42-01後の開始基準。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W31-01-validation-7rrf2ayv.json:1 — 初回総合証拠。local/runner/active/baselines/whitespaceログを新名保存。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W31-01-local-final.log:1 — 整数値4.0の追加境界検査後の追試。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W31-01-final-evidence.json:1 — 最終hash・開始時差分・追試対応。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W31-01-report.md:1 — 本報告。

不変条件の確認根拠：開始基準から意図外差分0、初回検査中変更0、ZIP hash一致。W30/W43/W42の過去成果と証拠、models、既存未コミット変更、参照ZIPと19作業版を保持。原文コピーとUTF-8 SHA-256を検査し、正規化なし・入力/snapshot変更から原文が独立することを確認した。新SourceをPredictionへ必須依存させない。

契約/API/DTO・互換/移行：wire/API変更なし。契約2や由来版2の偽装入力は明示移行要求。由来座標の実認証は未接続。text以外はunion形状だけ、VersionRefも存在/許可の証明ではない。訂正APIや既存OCR移行は追加していない。

停止・取消・復旧：純粋なメモリ上の検証・コピーのみ。失敗でも原文を変更しない。永続保存・rollback・消去barrier・過去送信回収なし。

テスト：型・境界・局所単体 / cwd C:/Users/keima/Desktop/4-me-not。

- & 'C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 docs/implementation/validate_local_tasks.py W31-01 — 終了0。初回局所25件、基準検査3件、作業版114件、旧版25+11件合格。各cwd/子コマンド/終了コード/logはvalidation-7rrf2ayv.json。
- 同Pythonで -X utf8 -m unittest discover -s tests/memory -p test_*.py -v — 終了0、最終26件（W43:5、W42:8、W31:13）。W31-01-local-final.log。初回合格後、自己点検でJSONの整数値4.0をslice用intへ変換し、非整数/booleanの拒否も追加したため追試。仕様は変えておらず、作業版/旧版試験を重複実行していない。
- git diff --check — 終了0。最終差分/hashはfinal-evidence.json。

未実装・未実施・未決：実Source保存と解析失敗後のDB原文保持はW31-02、認証/現在ACL/GateはW33、媒体存在/読取/実範囲はW39。DB/API/UI/queue/LLM/実機・実アプリ受入未実施。fixtureは架空Sourceだけで、mock DBやfake認証による結合完了を主張しない。局所条件に未達なし。M1〜M4/D1〜D9等DRAFTは未承認のまま。今回に必要な新しい意味判断は発生しなかった。

レビュー：自己点検のみ、今回3件の独立レビューは未実施。W30 R1の独立再レビュー解消とは別。

情報境界：実原文/人物/秘密を使用せず、合成データのみ。例外はコード、通常ログは検査名/件数/パス。外部payload送信・本番DB・公開・pushなし。

引継ぎ：3件の局所実装は完了。未決はW30のM1〜M4/D1〜D9等を保持。Gate写像・本人方針に依存する接続前に個別判断が必要。EXECUTION_ORDER.mdに従う次の推奨IDはW31-02。W31-02以降には着手していない。
