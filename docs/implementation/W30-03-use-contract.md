# W30-03 詳細報告・利用条件契約

タスクID：W30-03
状態：完了
分類・運用状態：core。仕様・局所検証の担当範囲で完了。アプリ配備なし。disabled/shadow等の実運用状態は未確認であり、実装完了と同一視しない。

## 今回の責務とv0.4差分

W30-02の詳細報告、状態契約、validation.json、active/baselinesログを確認。W30-01の既存port棚卸しと現コードも確認した。実repoのAGENTS.mdは確認済みの不在を前提とし、新規作成していない。指定タスクパックのGUIDE.md/tasks/W30-03.mdを作業規則として参照した。

既存のArtifactView/Grade/DeploymentView/RecallV3Requestを再利用。状態文書へ採否×用途別配備の表、内部検索・提示・getItemの境界を追加。権限表へ操作ごとの追加条件とDRAFTの論点を追記した。Schema/API/enum/registryの意味や受理集合は変更していない。v0.4配布物、データ契約3、HTTP案/v3と稼働/apiを区別する。

仕様配置はdocs/spec/v0.4の同じ部分作業版を継続。今回のrunnerは参照ZIPを新規一時領域に展開し、W30-02の4ファイルと今回のauthority-matrix/fixture/testの3ファイルを重ねる。完全配布物ではなく7ファイルのoverlay。その他の仕様は参照ZIPを読む。W30-02報告・検査証拠は当時の履歴として保持し、現在の再現入口はW30-03-validate.ps1を使う。

参照ZIP：C:/Users/keima/.codex/.chatgpt-projects/g-p-696486f280d081918418aa6ea3658d1c/deliverables/4-me-not-v0.4-codex-task-pack/reference/4-me-not-collab-v0.4.zip
SHA-256：811A9B2E19FE4CFF7C3AE106D4B2115D40B83A67E429D3F8C8509B64FA307C5E（変更なし）。inputs/archive/sourcesは変更なし。

## 対応REQ/AUTO/V04・仕様箇所

| 要求・受入 | 仕様根拠 | 今回の証拠と限界 |
|---|---|---|
| REQ-AUTO-003 / AUTO-003 | promotion.feature:17、state-model、api-semantics:74 | shadowのlive検索拒否、採用との独立8組、配備表。実投影切替は未接続 |
| REQ-AUTO-004 / AUTO-004 | promotion.feature:23、RecallV3Hit/Request | internal仮説利用と根拠/経路/条件の合成例。実検索器の継承は未実装 |
| REQ-AUTO-005 / AUTO-005 | promotion.feature:29、decision-review | Schemaを通る採否/出自/経路等6改変を意味検査で拒否。実再要約/DAGの証明ではない |
| REQ-V04-004 / V04-004 | v04.feature:23、feature-registry | test_v04_assetsを含む全体検査。coreの実験必須依存を追加していない |
| REQ-V04-037 / V04-037 | v04.feature:221、migration | W30-02制約比較とv04検査が回帰合格。実データ移行なし |

getItemはapi-semantics:20とItemView/MemoryRevisionに従い、未採用の応答形を拒否する例を追加。受入本文・REQ・OpenAPI・CSVは既存の意味を変えないため複製編集せず、全参照整合を既存資材検査で確認した。

## 変更ファイル

以下の追加/削除は今回開始時との差分。authority-matrixは新規overlayなので、repo追加89行のうち原仕様からの実差分は+23/-0。state-modelは既存overlayへ+27/-0。既存未追跡を含む他ファイルは保持。

| 絶対パス:行 | 内容 | 追加/削除 |
|---|---|---|
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/docs/state-model.md:119 | 利用条件表・契約例の境界 | +27/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/docs/authority-matrix.md:68 | 内部/表示/行動条件・DRAFT | +89/-0（原仕様比+23/-0） |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/fixtures/w30-03-use-cases.json:1 | 15判定例・6経路改変 | +28/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/tests/test_w30_03_use_conditions.py:1 | 新6局所テスト | +117/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-03-validate.ps1:1 | ZIP再構成・検査・hash記録 | +85/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-03-validation.json:1 | 最終検証環境/終了/hash | +90/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-03-active.log:1 | 最終99件 | +104/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-03-baselines.log:1 | 旧版25+11件 | +48/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-03-first-active.log:1 | 初回失敗の保存 | +140/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-03-first-validation.json:1 | 初回環境/終了/hash | +90/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-03-use-contract.md:1 | 本報告 | +84/-0 |

## 不変条件の確認根拠

検査前後とW30-01からのコード196ファイルhash一致。既存追跡15ファイルの未コミット差分331追加/5削除、既存modelsと未追跡機能を保持。W30-02のSchema/fixture/test hashも一致。全Schema制約比較が合格し、86定義・38 API・46操作・25機能を保持した。

shadowのlive混入、ラベルだけの提示許可、enabledだけの送信許可を参照規則で拒否。仮説印・元根拠・経路・条件・不確実性を合成例で保持。原文/ID/digest、speaker/subject/claimant/relay、採用と真実、required_featuresの全由来、保存/学習/提示/送信/行動の分離を契約として維持。continue、高confidence、検索回数、無反応から採用や権限を作らない。実アプリの強制力を検証したとは主張しない。

契約/API/DTO・互換/移行：型・wire・稼働API変更なし、DB移行なし。getItemの採用名confirmed_by_userとArtifactのuser_adoptedは従来のまま。既存状態定義を再作成していない。

停止・取消・復旧：今回アプリ操作なし。契約では停止/撤回を待たせず、依存結果を隔離し非依存baselineへ戻す。shadowからの昇格も対象版/用途再検査と新projection generationが必要。実barrier/復旧は未実装。既送信情報・完了行動・過去に与えた影響は停止で回収できない。

## テスト

起点cwd：C:/Users/keima/Desktop/4-me-not
起点コマンド：& './docs/implementation/W30-03-validate.ps1'（最終終了0）。Python/Dependencies/SourceZipは引数変更可。Python 3.12.14、jsonschema[format] 4.26.0、一時依存領域W30-02-depsを再利用し、アプリの依存変更なし。

SPEC_ROOT（両子コマンドのcwd）：C:/Users/keima/AppData/Local/Temp/4-me-not-W30-03-run-c40941dd3c694e4cb8da54497b06427f/4-me-not-collab-v0.4
Python実パス：C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
環境：PYTHONUTF8=1、PYTHONDONTWRITEBYTECODE=1、PYTHONPATH=C:/Users/keima/AppData/Local/Temp/4-me-not-W30-02-deps（runner終了時に元の環境へ戻す）。

| 層 | 実子コマンド（pythonは上記実パス） | 終了 | 件数 | 証拠（上記絶対パス表参照） |
|---|---|---:|---|---|
| 仕様資材・参照規則 | python -X utf8 -m unittest discover -s tests -p "test_*.py" -v | 0 | 99/99（従来93＋新6） | W30-03-active.log、validation.json |
| 旧版資材・参照規則 | python scripts/check_baselines.py | 0 | v0.3 25/25、v0.1 11/11 | W30-03-baselines.log |

初回は99件中1エラー、終了1。追加合成例のVersionRef.resource_typeをartifactと誤記したため、既存enumのderivedへ修正し全体を再実行。初回ログとhashをfirst-*に保存。Schemaを緩めて通したのではない。subTest数をunittest件数に加算しない。

## 未実装・未実施・未決

実アプリ受入、DB/API結合、実認証、実検索/再要約、LLM品質、UI/端末、実FeatureControl/停止競合は未実施。仕様資材の合格と区別する。既存E1（account）/E2・E3（保存・提案）/E6（検索）を再利用候補として維持し、新サービスを追加しない。TrustedFactsの組立・配備tuple照合・interpretation用途上限・投影切替は参照Gate未実装であるため、局所合格を接続済みと扱わない。

W30-01 D1〜D9とW30-02 DRAFTを未承認のまま保持。今回に影響する具体論点・提案・影響はauthority-matrix:82以降に記載。機微な人物仮説の表示対象は固定分類＋本人再確認案だが、範囲拡大は同意/表示負担/人物評価へ影響するため本人判断が必要。今回はinterpretationのinternal上限を維持。認証caller接続はsession/account/vaultから作る案で、誤接続は隔離を迂回するため未接続。採否wire統一はgetItem互換、Task/SKIPPED写像や予定採用→組織学習同意は内容採否・用途に影響するため自動変換しない。

レビュー：Codexの自己点検。独立レビュー未実施。内部検索もliveである点、記録laneと現在配備の違い、仮説ラベルが包括提示許可でない点を明文化。初回参照種別の誤りは修正・再検証済み。

情報境界：合成fixtureと参照コードのみ。実原文・秘密・.envの値を読まず、通常ログは検査出力のみ。今回ネットワーク/外部payload送信・本番DB・公開・pushは行っていない。

引継ぎ：本部分作業版と未承認DRAFTを継続し、実接続の不足を引き継ぐ。EXECUTION_ORDER.md:16に従う次の推奨IDは **W30-04**。次タスクには着手していない。
