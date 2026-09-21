# W30 契約レビュー・後続の入口（W30-07）

## 採用方針・契約・検証を分離

配布物v0.4 / データ契約3 / HTTP案v3。ADR-001/002/019等の合意方向とADR-014/017の設計方針を保持。ADR-024〜027等の詳細DRAFTを承認へ上げない。既存/apiの実装と仕様案を同一視しない。Gate本体・実認証・実DB/API/UI・LLM・端末受入は未実施、独立レビューも未実施。

後続は参照ZIPにdocs/spec/v0.4の部分作業版を重ねる。再現入口は実repo docs/implementation/W30-07-validate.ps1、ファイル一覧/hashと実SPEC_ROOTはW30-07-validation.json。本書は新たなSchema正本や配布物署名ではない。元ZIPのmanifestは元配布物の記録として保持する。

## W30各責務

| ID | 状態 | 差分・検証 | 残る実接続 |
|---|---|---|---|
| W30-01 | 棚卸し完了 | 196コードhash・用語/port/差異 | 実装済み判定は当時の証拠に限定 |
| W30-02 | 局所契約検証完了 | 独立状態軸・既存86定義再利用 | Ledger/採否transaction |
| W30-03 | 局所契約検証完了 | provisional利用・shadow隔離 | 検索/提示/依存継承 |
| W30-04 | 局所型検証完了 | 4権限・caller/候補の分離 | 実認証/receipt/Gate |
| W30-05 | 対応監査完了 | 46操作/38 API/25機能・未対応一覧 | M1〜M4の判断に依存する写像変更は停止 |
| W30-06 | 局所移行契約検証完了 | 元版照合・Source不変・限定変換例 | 本人確認・実DB移行/復元 |
| W30-07 | 資材整合検査完了 | 全参照/fixture/AUTO/V04/図と判断追跡 | 本人承認や実受入へ読み替えない |

## 全論点の状態（DRAFTは未承認）

| ID | 論点・案・影響 | 現在の制限/判断先 |
|---|---|---|
| D1 | confirmed_by_user/user_adopted明示adapter案。wire互換に影響 | 現名保持、contract owner |
| D2 | session/account/vault/Actor対応、system登録/失効案。認証・監査に影響 | dev fallbackやActor自己申告をowner化しない。本人/認証担当 |
| D3 | 画像/OCRのID/hash/時刻をSourceへ対応。由来・欠損に影響 | 不明を空依存へ変換しない。保存担当/本人 |
| D4 | 採用と学習同意を用途Planで分離。既存組織履歴機能に影響 | 包括同意を作らない。本人/権限担当 |
| D5 | Task/Intentionの唯一の正本とSKIPPED対応。再開意思に影響 | 自動写像なし。本人/実装担当 |
| D6 | 旧api/外部embeddingも送信Gateへ接続。宛先/payload/同意に影響 | 実接続未実施。本人/権限担当 |
| D7 | 端末保存・鍵・復旧方式。データ所在に影響 | 実機受入なし。端末担当/本人 |
| D8 | 実験依存と停止barrier。起動/応答/データ由来へ影響 | coreを実験へ必須依存させない。実装/独立検証担当 |
| D9 | 実アプリ試験件数更新。実測と宣言数を分離 | 本検査でアプリ数を更新しない。実受入担当 |
| M1 | evaluateUseの37対46クラス。全9追加案/専用経路案で公開用途が変わる | 写像変更停止、contract ownerの判断待ち |
| M2 | counterevidence_searchのAPI未対応。内部限定案/評価入口追加案 | 実接続停止、contract owner判断待ち |
| M3 | 8機能の直接操作なし。共通操作利用/研究用途案 | 新APIを捏造しない、機能担当判断待ち |
| M4 | 予定委任・機微推論提示・外部AIの具体対象。本人負担/送信範囲に影響 | 対象/条件の包括承認なし。本人判断待ち |
| T1 | GateDecision重複権限/outcomeとbasisのwire制約強化案 | 内部集合のみ検査、既存wire保持。互換判断待ち |

W30-03のinterpretation internal上限は維持。機微分類の具体閾値・仮説提示対象はM4、既存MemoryEntry状態の写像はD3/D5に含める。全DRAFTを本人の正式採用とする判断はしていない。これらに依存する実装は止めるが、独立した局所検査は実行できる。

## 差分の同期先と図の確認

- memory.schema.jsonはW30-02注記のみ、全検証制約の原版比較を継続。補助authority-boundary.schema.jsonもJSON参照検査対象へ追加。
- OpenAPI/API inventory/REQ/feature/operation/CSVは変更なし。W30-05の未対応を文書化し、テストが既存差を許可済みの写像と誤認しない。
- 6図はdocs/diagrams-index.jsonと本文内Mermaidの一致を既存テストで検査。01-system/02-use/03-correction/04-prediction/05-stopは設計図で、Gate・原本保持・候補・任意性を表す。00-currentは原配布物が参照した旧固定repoの図（7ルーター）で、現在repoの棚卸し図ではない。現在の事実はW30-01と今回のコード不変証拠を読む。
- 図の描画・視覚検証は未実施。本文/ソースの一致と設計上の意味の自己点検だけを報告する。図の一致から認証や停止の実装完了を導かない。

## AUTO/V04/REQ追跡

全受入は本文の参照整合を確認する。以下の「資材確認」は実アプリ受入合格ではない。局所実装の具体証拠は各W30報告とactive.logに限定する。

| REQ | 受入 | API参照 | 状態 |
|---|---|---|---|
| REQ-AUTO-001 | AUTO-001 | importSource,recordDerivation | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-002 | AUTO-002 | recordDerivation | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-003 | AUTO-003 | recordDerivation,recall,promoteDeployment,suspendDeployment | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-004 | AUTO-004 | recall | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-005 | AUTO-005 | recordDerivation | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-006 | AUTO-006 | adoptDerivation,approveChange | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-007 | AUTO-007 | evaluateUse | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-008 | AUTO-008 | adoptDerivation | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-009 | AUTO-009 | createGrant,executeAction | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-010 | AUTO-010 | activateIntention,prepareAction | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-011 | AUTO-011 | prepareAction,evaluateUse | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-012 | AUTO-012 | recordConfirmation,executeAction | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-013 | AUTO-013 | revokeGrant,executeAction | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-014 | AUTO-014 | executeAction,getAction | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-015 | AUTO-015 | executeAction,approveChange | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-016 | AUTO-016 | executeAction,getAction | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-017 | AUTO-017 | evaluateUse,createGrant | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-018 | AUTO-018 | approveChange,recall,executeAction | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-019 | AUTO-019 | erase,getItem | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-020 | AUTO-020 | erase | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-021 | AUTO-021 | evaluateUse,executeAction | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-022 | AUTO-022 | recall,recordPresentation | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-023 | AUTO-023 | evaluateUse,recordPresentation | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-024 | AUTO-024 | recordConfirmation,recordFeedback | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-025 | AUTO-025 | recordSchemaApplication | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-026 | AUTO-026 | recordObservation,activateIntention | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-027 | AUTO-027 | recordDerivation,transitionIntention | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-028 | AUTO-028 | prepareModel | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-029 | AUTO-029 | revokeGrant,activateModel | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-030 | AUTO-030 | activateModel,promoteDeployment | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-031 | AUTO-031 | recordConfirmation,recordFeedback | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-032 | AUTO-032 | evaluateUse | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-033 | AUTO-033 | executeAction | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-034 | AUTO-034 |  | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-035 | AUTO-035 | recall,recordFeedback | 参照整合確認・実アプリ未実施 |
| REQ-AUTO-036 | AUTO-036 |  | 参照整合確認・実アプリ未実施 |
| REQ-V04-001 | V04-001 | importSource,approveChange,recall | 参照整合確認・実アプリ未実施 |
| REQ-V04-002 | V04-002 | recordPrediction,getFeatureControl,recall | 参照整合確認・実アプリ未実施 |
| REQ-V04-003 | V04-003 | changeFeatureControl,evaluateUse | 参照整合確認・実アプリ未実施 |
| REQ-V04-004 | V04-004 | getFeatureControl | 参照整合確認・実アプリ未実施 |
| REQ-V04-005 | V04-005 | evaluatePrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-006 | V04-006 | recordPrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-007 | V04-007 | recordPrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-008 | V04-008 | recordOutcome,evaluatePrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-009 | V04-009 | recordOutcome,evaluatePrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-010 | V04-010 | recordOutcome,evaluatePrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-011 | V04-011 | getAction,evaluatePrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-012 | V04-012 | recordOutcome | 参照整合確認・実アプリ未実施 |
| REQ-V04-013 | V04-013 | evaluatePrediction,recordDerivation | 参照整合確認・実アプリ未実施 |
| REQ-V04-014 | V04-014 | evaluatePrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-015 | V04-015 | recordOutcome,evaluatePrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-016 | V04-016 | evaluatePrediction | 参照整合確認・実アプリ未実施 |
| REQ-V04-017 | V04-017 | evaluatePrediction,recordDerivation,adoptDerivation | 参照整合確認・実アプリ未実施 |
| REQ-V04-018 | V04-018 | recordDerivation | 参照整合確認・実アプリ未実施 |
| REQ-V04-019 | V04-019 | getDerivation | 参照整合確認・実アプリ未実施 |
| REQ-V04-020 | V04-020 | adoptDerivation | 参照整合確認・実アプリ未実施 |
| REQ-V04-021 | V04-021 | recordAssessment,evaluateUse,executeAction | 参照整合確認・実アプリ未実施 |
| REQ-V04-022 | V04-022 | promoteDeployment,evaluateUse | 参照整合確認・実アプリ未実施 |
| REQ-V04-023 | V04-023 | recordOutcome,recordDerivation | 参照整合確認・実アプリ未実施 |
| REQ-V04-024 | V04-024 | changeFeatureControl,recall | 参照整合確認・実アプリ未実施 |
| REQ-V04-025 | V04-025 | changeFeatureControl,promoteDeployment | 参照整合確認・実アプリ未実施 |
| REQ-V04-026 | V04-026 | changeFeatureControl,getSource | 参照整合確認・実アプリ未実施 |
| REQ-V04-027 | V04-027 | recordDerivation,adoptDerivation | 参照整合確認・実アプリ未実施 |
| REQ-V04-028 | V04-028 | changeFeatureControl,getAction | 参照整合確認・実アプリ未実施 |
| REQ-V04-029 | V04-029 | recall,recordPresentation | 参照整合確認・実アプリ未実施 |
| REQ-V04-030 | V04-030 | changeFeatureControl,executeAction | 参照整合確認・実アプリ未実施 |
| REQ-V04-031 | V04-031 | evaluatePrediction,promoteDeployment | 参照整合確認・実アプリ未実施 |
| REQ-V04-032 | V04-032 | getDerivation,evaluateUse | 参照整合確認・実アプリ未実施 |
| REQ-V04-033 | V04-033 | promoteDeployment | 参照整合確認・実アプリ未実施 |
| REQ-V04-034 | V04-034 | changeFeatureControl | 参照整合確認・実アプリ未実施 |
| REQ-V04-035 | V04-035 | recordDerivation,evaluateUse | 参照整合確認・実アプリ未実施 |
| REQ-V04-036 | V04-036 | recordOutcome,changeFeatureControl | 参照整合確認・実アプリ未実施 |
| REQ-V04-037 | V04-037 | importSource | 参照整合確認・実アプリ未実施 |
| REQ-V04-038 | V04-038 | changeFeatureControl,getFeatureControl | 参照整合確認・実アプリ未実施 |
| REQ-V04-039 | V04-039 | promoteDeployment | 参照整合確認・実アプリ未実施 |
| REQ-V04-040 | V04-040 | changeFeatureControl,activateIntention,getAction | 参照整合確認・実アプリ未実施 |

新規85件ではなく原配布物85件を独立して検査し、W30の追加局所検査を含む作業版と別記する。旧v0.3/v0.1も別実行する。合格は未承認の委任を有効化しない。

次の推奨IDはEXECUTION_ORDER.mdのW43-01。今回それ以降には着手しない。
