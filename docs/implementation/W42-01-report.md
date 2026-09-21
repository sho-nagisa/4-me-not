タスクID：W42-01

状態：完了（分類・依存制約・局所compositionの範囲）

分類・運用状態：core。experimental/evaluation_onlyの定義はdisabled/shadow。実アプリ未接続で実運用状態の変更なし。

今回の責務とv0.4差分：指定仕様/W30-07引継ぎ/R1報告を確認。25機能を既存JSONから読込み、3分類と合意/実装/配備を別フィールドで保持する。未知tier/feature/循環/コアから非coreへの必須依存を拒否。コア側に任意portを定義し、Prediction未登録で局所compositionが構築できる。25サービス化やGate追加なし。

対応REQ/AUTO/V04・仕様箇所：V04-001/002/004/035の型・局所責務。contracts/feature-registry.json、FeatureControlView/Snapshot、docs/feature-catalog.md・feature-control.md。停止/再起動/通知等の受入全体は未実施。

変更ファイル（追加/削除行数はW42-01-files.json）：

- C:/Users/keima/Desktop/4-me-not/backend/services/memory_features.py:1 — registry・分類チェック・任意port。
- C:/Users/keima/Desktop/4-me-not/tests/memory/test_memory_features.py:1 — 正負境界・import・未登録試験。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W42-01-contract.md:1 — 局所契約・未接続境界。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W42-01-start.json:1 — W43-01完了後の基準。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W42-01-validation-1wgw3es6.json:1 — 新規証拠。local/runner/active/baselines/whitespaceログを対応する新名で保存。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W42-01-report.md:1 — 本報告。

不変条件の確認根拠：開始基準から意図外差分0、実行中変更0、ZIP hash一致。既存models・未コミット変更・W30とW43履歴・作業版19ファイルを保持。未登録/注入済みのどちらでも拡張を呼ばない。既定OFF、candidate/evaluation_onlyのlive拒否、core必須依存拒否を実関数で試験した。

契約/API/DTO・互換/移行：wire/API/原registry変更なし。Schema検証器を再利用。registryの実装進捗文字列を現在のアプリ状態と推論しない。任意port登録は有効化/許可ではない。

停止・取消・復旧：局所compositionの生成だけで外部作用なし。実停止barrier/epoch/queue/保存/復元は後続であり、この層で実行許可を出さない。過去作用を回収したとの主張なし。

テスト：型・境界・局所単体 / cwd C:/Users/keima/Desktop/4-me-not / & 'C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 docs/implementation/validate_local_tasks.py W42-01 / 終了0。局所13件（今回8＋W43回帰5）、基準検査3件、作業版114件、旧版25+11件合格。git diff --check終了0。子コマンド・cwd・logはvalidation-1wgw3es6.json。fakeは異常registryと呼んではならないportのみ。

未実装・未実施・未決：FastAPI全体起動・実保存・Gate/認証・FeatureControl変更・barrier・queue/worker・実通知・停止競合・実アプリ受入未実施。局所条件は達成。M1〜M4/D1〜D9を承認に変更せず、依存する接続はしない。動的Python全体の依存保証はなく、今回3コアモジュールの静的importと負例を検査した。

レビュー：自己点検のみ。今回の変更について独立レビュー未実施。

情報境界：合成fixture/registryのみ。秘密や実原文のログ出力なし、外部payload/本番DB/公開/pushなし。

引継ぎ：制御/認証/永続化は後続port。EXECUTION_ORDER.mdの次の推奨IDはW31-01。
