# W30-04：4権限と呼出主体の局所型契約

状態：仕様作業版。ADR-014の独立軸を具体化するが、既存DRAFTの承認や実認証の接続を意味しない。

## 型の正本と入力の分離

contracts/authority-boundary.schema.jsonは既存memory.schema.jsonへの参照だけでAuthority、DecisionOutcome、PermissionBasis、CandidateRequest、AuditActorを定義する。AuthoritySetは4権限の複数集合で、内部表現では重複を拒否する。既存GateDecisionのwire制約は変更しない。operation-registry.jsonが操作ごとの必要権限の正本であり、複合操作の全要素が必要。例えばmessage_sendはAttentionとAction、entity_mergeはStructureとEpistemic。どちらか一つで代替しない。

contracts/authority_boundary.pyのrequired_authorities(*, caller: CallerFields, candidate: Mapping, vault_id: str)は、別入力の形・vault一致を点検して登録簿の必要権限集合を返す。返すのは要求であり許可ではない。modelがprofile_adoptの必要権限を調べられても、その操作を実行できない。check_required_setは必要権限の欠落/余分/重複/未知を拒否する局所契約検査で、同意やGrantの判定ではない。

CallerFieldsは検証済みadapterの出力位置を示す内部型。候補JSONをCallerFieldsへ変換するfactoryは提供しない。辞書をcaller引数へ渡すと拒否する。ただしPythonのconstructorやSchema検証は認証装置ではなく、同一プロセス内の信頼済みコードは構築できる。アプリ側のadapterが未接続の現状では、HTTP/LLMからこの型を作って実行へ渡してはならない。認証セッション、vault所有/所属、service principal、失効を実検証したadapterのみが将来生成する。

GateRequestにactor/risk/approved/confirmation_valid/権限配列等を追加すると既存additionalProperties=falseで拒否する。既存purpose、payload_digest、Snapshotも候補であり、自己申告した対象・版・digestを確認receiptとして信用しない。GateDecisionはコアからの出力であり、モデルが同じ形を生成しても許可ではない。outcomeとbasisは独立型だが、実際の合法な組合せ・現在版への束縛は後続Gateで検査する。

## Actorの明示対応（認証から監査表現への一方向）

| 検証済みcaller.role | 操作の監査Actor.kind | 必要条件 |
|---|---|---|
| owner | user | 対象vaultの本人を認証し、adapterで解決したActor IDと一致 |
| model | model | 信頼済み実行主体のIDと一致。ownerへ昇格しない |
| system | rule | 登録されたサービス/固定ルールの主体IDと一致 |
| importer | importer | 認証された取込主体のIDと一致 |

check_actor_bindingは対応kindとUUID同一性を検査するだけで、Actorからcallerを作らない。Source.speaker/subject/claimant/relayや過去Revision.authorへこの対応を適用しない。ownerがmodel作成候補を採用する際も候補authorをuserに変更せず、本人の採用操作の監査主体だけを別記録する。user表記がある文章やActor JSONだけではownerになれない。

## DRAFT・実接続の判断

- W30-01 D2、W30-02/03のsession/account/vault adapterは未承認・未接続。提案は既存account認証を再利用し、vault対応表とActor ID対応を明示して解決する。account ID＝Actor ID＝vault IDとは仮定しない。既存dev fallbackを本人認証の証拠にするとモデルからの偽装経路を作るため、実接続時は検証済みsessionと区別する。本人・認証担当が対応/移行を判断する。
- system/ruleの具体service principal登録と失効方式は未決。上表は操作監査の条件付き対応であり、既存ruleデータへの一括権限付与ではない。サービス登録案はworkerの停止・監査・権限範囲に影響する。登録不明な主体は実接続時に拒否する。
- GateDecisionの重複権限やoutcome/basisの組合せをwire Schemaでも狭める案はconsumer互換に影響するため未承認。今回は内部集合を重複拒否し、既存wireと86定義は保持する。
- 機微判定/提示範囲、採否名称統一、Task/SKIPPED写像、予定採用を学習同意とする案は従来通り未承認。今回の型から保存・学習・提示・送信・行動への包括許可を作らない。

## 検証と担当境界

AUTO-006：modelとownerの監査組合せを拒否、既存参照Gateのmodel採用拒否を回帰。AUTO-007：高confidenceでも本人確認を代替しない。AUTO-017：追加property拒否。AUTO-003、V04-004、V04-037と全参照資材は既存テストを継続する。

型検査はDraft202012ValidatorによるSchema自体・合成正負入力・参照解決検査。Pythonの型注釈を静的型検査済みとは報告しない。局所コードはGateDecision、receipt、allow、外部作用を発行しない。実認証・4権限ごとの同意評価・確認/委任・TOCTOU・DB/UI受入は未実施。W33等の実接続で確認する。

原文/ID/digestと人物役割、provisional/shadow、FeatureControl/Deployment/Gate、採用≠真実、全由来required_featuresを維持する。品質continue・検索回数・無反応は認可情報ではない。停止/撤回・消去は現在状態が優先するが、今回それらのGateやbarrierは実装しない。
