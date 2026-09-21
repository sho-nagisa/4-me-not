# W30-02 完了報告・仕様作業版の入口

タスクID：W30-02
状態：完了（独立状態軸の契約・局所検証の範囲）。
分類・運用状態：core。アプリへの配備は未実施。disabled/shadowの実運用状態を主張しない。

## 今回の責務とv0.4差分

W30-01棚卸しと28項目の検査証拠を読み、当時のコード196ファイルが現在も同じhashであることを確認した。実repoのAGENTS.mdは新規作成していない。作業規則は指定のv0.4タスクパックtasks/W30-02.mdを参照した。

既存の状態enum/constが独立しているため再定義しなかった。MemoryRevision、ChangeRecord、ArtifactView、Snapshot等9定義に注記を加え、書込主体・ガード・合法/禁止遷移・移行保留をstate-modelへ追記した。v0.4の機能分類、方針合意、実装進捗、FeatureControl、配備、認可の違いも固定した。

型の受理集合は変更なし。既存Schemaの全検証制約を注記を除いて比較し一致を検証した。86定義・38 API・46操作・25機能、既存REQ/AUTO/V04を保持。稼働/apiのコード・DTO・DBは変更していない。

## 仕様配置と再現方法

- 参照ZIP：`C:/Users/keima/.codex/.chatgpt-projects/g-p-696486f280d081918418aa6ea3658d1c/deliverables/4-me-not-v0.4-codex-task-pack/reference/4-me-not-collab-v0.4.zip`
- ZIP SHA-256：`811A9B2E19FE4CFF7C3AE106D4B2115D40B83A67E429D3F8C8509B64FA307C5E`。W30-01の証拠と一致し、変更なし。
- 永続する作業差分：`C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/`。4ファイルのみを保持する部分作業版であり、独立した完全な仕様配布物ではない。
- 検証時のSPEC_ROOT：`C:/Users/keima/AppData/Local/Temp/4-me-not-W30-02-run-58c93a9223bf4bfb885185e231575e63/4-me-not-collab-v0.4`。
- 読む際は部分作業版の該当4ファイルを優先し、その他は参照ZIPを使う。検査スクリプトは毎回新しい一時領域へZIPを展開し、4ファイルを上書きしてこの組合せを再現する。同期原本・inputs・archiveは編集しない。
- 後続でこの同責務を変更する場合も同じ作業版を継続する。別のSchema正本や新サービスを追加しない。W30-01の履歴文書・証拠は当時の事実として保持する。

実repoルートから次で再現する：

```powershell
& './docs/implementation/W30-02-validate.ps1'
```

Python 3.12.14とjsonschema[format] 4.26.0を使用。アプリ環境に依存を追加していない。一時依存領域を削除した場合は次で再準備できる（今回実行済み、終了0）。

```powershell
& 'C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m pip install --disable-pip-version-check --target 'C:/Users/keima/AppData/Local/Temp/4-me-not-W30-02-deps' 'jsonschema[format]==4.26.0'
```

検査スクリプトはPython/Dependencies/SourceZipのパスを引数で変更可能。W30-01で記録したZIP hashを検査する。作業版manifest.jsonを新しい配布物の署名や完成証拠として更新してはいない。原ZIPのmanifestは原本の記録であり、今回の差分hashはW30-02-validation.jsonが保持する。

## 対応REQ/AUTO/V04・仕様箇所

| 要求・受入 | 根拠 | 今回の証拠／後続の制限 |
|---|---|---|
| REQ-AUTO-003 / AUTO-003 | state-model独立軸、promotion.feature:17 | 48種の採否×lifecycle×laneの保存形と参照規則のshadow拒否。実検索接続はW30-03/W34 |
| REQ-AUTO-005 / AUTO-005 | promotion.feature:29、DerivationRequest | AIの出自偽装・依存消去・再生成時の採用洗浄を型/前後例で拒否。実DAG継承はW31-07/W32 |
| REQ-AUTO-008 / AUTO-008 | promotion.feature:47、MemoryRevision/ArtifactView | 本人採用でもai_hypothesisを保持。原文・producer・required_featuresを変える前後例を不適合とする。実取引はW31-05 |
| REQ-AUTO-018 / AUTO-018 | promotion.feature:107、state-model訂正 | 採用済みでも現在の依存失効でdefer。実barrier/再生成はW31-07 |
| REQ-AUTO-019 / AUTO-019 | promotion.feature:113、api-semantics削除 | 現在のerased/撤回で拒否。通常GET 404・backup復元の実行試験はW38/W40 |
| REQ-AUTO-006 / AUTO-006 | promotion.feature:35、operation-registry profile_adopt | 型上userの申告と認証済みownerを区別。trusted model/importerは拒否。実認証接続はW30-04/W33 |
| REQ-V04-004 / V04-004 | v04.feature:23、feature-registry | 既存test_v04_assetsのcore依存・registry/API/REQ整合。実構成/停止試験はW42 |
| REQ-V04-037 / V04-037 | v04.feature:221、migration | v2入力拒否、v3制約とwire名維持。実データ移行はW30-06/W40-11 |

API/受入本文に意味変更がないため、OpenAPI・API inventory・REQ・既存fixture・受入本文は複製変更しなかった。参照ZIPを使った統合資材検査で一致を確認した。参照規則をアプリ受入の合格とは扱わない。

## 変更ファイル

すべて実repoでは新規追加。Schemaと状態文書は原仕様からの限定作業版なので、repoへの追加量と原仕様からの実差分を分ける。すべて削除0行。

| 絶対パス:行 | 内容 | repo追加行数 | 原仕様からの実差分 |
|---|---|---:|---|
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/contracts/memory.schema.json:436 | 9定義の境界注記 | 5098 | +9/-0、検証制約の変更なし |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/docs/state-model.md:56 | 書込主体・遷移・移行表 | 117 | +63/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/fixtures/w30-02-state-cases.json:1 | 合成正負fixture | 44 | 新規 |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/tests/test_w30_02_state_axes.py:1 | 型/前後例/既存参照規則8テスト | 180 | 新規 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-02-validate.ps1:1 | 部分作業版の再現・検証・hash保存 | 81 | 新規 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-02-validation.json:1 | 実行環境・結果・差分hash | 78 | 新規 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-02-active.log:1 | 作業版93件の実行記録 | 98 | 新規 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-02-baselines.log:1 | 旧版25+11件の実行記録 | 48 | 新規 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-02-state-contract.md:1 | 本報告・作業版入口 | 103 | 新規 |

## 不変条件・互換/移行・停止/取消/復旧

既存コード196ファイルはW30-01時点・今回実行前後のhashが一致。既存未コミット15追跡ファイルの差分331追加/5削除と既存未追跡機能を保持。models構成・アプリ設定・DB・原ZIPに変更なし。

採否を真実へ昇格せず、原文/ID/digestと役割帰属を保持する契約例にした。採用後もrequired_featuresとproducerは維持。保存/学習/提示/外部送信/行動の権限を混ぜず、continue・高confidence・無反応・検索回数から権限や真偽を作らない。実コアの停止/取消/復旧は未実装のまま。停止による既送信情報・完了行動の回収を主張しない。

## テスト

実repoでの起点コマンドは前述のW30-02-validate.ps1、終了0。以下はその実子コマンド。作業ディレクトリは上記SPEC_ROOT、実Pythonパスはvalidation.jsonに記録。PYTHONUTF8=1を子プロセスにも継承した。

| 検証層 | 実コマンド（pythonは上記実行ファイル） | 終了 | 結果 | 証拠 |
|---|---|---:|---|---|
| 仕様資材・参照規則 | python -X utf8 -m unittest discover -s tests -p "test_*.py" -v | 0 | 93/93合格（既存85＋新8） | W30-02-active.log |
| 旧版資材・参照規則 | python scripts/check_baselines.py | 0 | v0.3 25/25、v0.1 11/11合格 | W30-02-baselines.log |

新8テストはSchema正負17例、独立軸48組、未知/他軸enum20例、既存参照判定11例、採否前後6例、改変4例、Snapshot混入5例、全Schema制約比較を含む。subTest数をunittest件数へ水増ししていない。実Gate/認証/採用DB transactionは作っておらず、前後例の検査helperを実装済みサービスとは扱わない。

環境準備の初回importはjsonschema未導入で終了1。指定版を一時領域へ導入して解消。実試験は最初の実行で全件合格。git diff --no-indexの終了1は原仕様との差分存在を示す正常な比較結果でありテスト失敗ではない。

## 未実装・未実施・未決

W30-01 D1〜D9を承認へ変更していない。今回の意味判断が必要な点は次のとおり。

- confirmed_by_user→user_adoptedの名称統一/adapter：consumer・fixture・移行の影響がある。現wire表現を保持し、contract ownerがW30-06で判断する。
- Taskのaccepted/dismissedやSKIPPEDを記憶採否/Intentionへ写像する案：既存データの意味と再開意思に影響。本人がW36で判断する。今回は自動変換なし。
- Actor user/ruleと認証owner/systemの具体接続：session/account/vaultに影響。W30-04/W33で判断。DTO自己申告は権限にならないという境界だけ維持。
- 予定採用を組織履歴学習の同意として扱うか：用途・撤回に影響するため包括同意にしない。本人＋権限担当へ引継ぎ。

実アプリ受入、DB、UI、実LLM、外部送信、端末、独立レビューは未実施。環境不足による今回必須試験の未達はない。既存portはW30-01 E1/E2/E3/E4/E6を再利用候補として維持し、Ledger/Gate/FeatureControl未接続を明記した。

レビュー：Codexによる自己点検。独立レビュー未実施。指摘として状態author/approverの混同、recorded_lane/current Deploymentの混同、型適合と読取許可の混同を文書・注記・fixtureで防いだ。

情報境界：合成fixtureと参照コードだけを使用し、実原文・.env・秘密を読まず通常ログへ出していない。依存パッケージ取得のネットワーク通信のみ実施。ユーザーデータの外部payload・送信は0件。

引継ぎ：EXECUTION_ORDER.md:15の次の推奨IDは **W30-03**（前提W30-02）。独立軸と保留中DRAFT、今回の部分作業版を引き継ぐ。次タスクには着手していない。
