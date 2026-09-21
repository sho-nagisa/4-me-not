# 状態モデルと履歴

## 1. 独立した軸

| 軸 | 値 | 意味 |
|---|---|---|
| epistemic_kind | direct_record / self_report / hearsay / external_claim / ai_hypothesis / hypothetical | 内容をどこから知ったか。採用後も由来は維持 |
| review_status | provisional / user_adopted / user_rejected | 本人の採否。原文保存には採用不要 |
| lifecycle | current / stale / retracted / erased | いま利用可能か。staleは古い版でなく派生根拠が失効した状態も含む |
| rollout_stage | shadow / internal / presentation / enabled | 機能版と用途の配備設定。特定記憶の真偽ではない |
| authorization outcome | allow / allow_provisional / require_confirmation / defer / deny | 特定の入力・利用目的・現在のpolicyに対する判定 |
| authorization basis | ordinary_policy / interactive / delegated / none | 何を根拠に実行可能か |

保存された生成物の本文・出典・版は不変。ReviewDecision、Retraction、PolicyChange、PromotionReceiptなどを追記し、現在の採否・利用可否は投影で求める。撤回は原文の捏造ではない。

## 2. 三系列とsnapshot

Content Ledger：本人が採用/訂正した記憶・構造・Schemaの変更、parent_commit、content_head。
Derivation Log：自動のBoundary/Episode/Gist/候補リンク/Schemaの保存、入力版とproducer版、generation。生成を記録することは承認ではない。
Operation/Learning Log：提示、本人の評価、適用結果、Gate判定、委任、Action、モデル版、削除イベント。本文のCommitへ混ぜない。

Snapshotはcontent_head、derivation_generation、policy_version、erasure_epoch、参照したobject/revision、および学習版を記録する。再現には採用した出力本体も必要で、同じプロンプトから同じ文章を再生成できるとはしない。

## 3. 承認の意味

provisional → user_adoptedは、同じ不変Revisionへの本人の採用イベント。本文も変えるなら新Revisionを作る。二つの操作を一取引にまとめられるが、生成者を本人へ書き換えない。

本人からの直接明示の依頼が対象・内容・用途を一意に定めるなら、その入力とUI表示をinteractive確認の証拠として使える。空の「OK」だけを別の操作・別の版・別の相手への許可に拡張しない。

## 4. 訂正・無効化

訂正：新原本/訂正証拠 → 新内容版 → content_head更新＋dependencyの利用停止。依存するSchema・Gist・関連・学習特徴・開いているworkspaceを追跡する。大きな再生成は後続jobでもよいが、旧派生物を使えるままにはしない。

過去を閲覧するときも現在のpolicyとerasureを適用する。古いcommitへ戻しても許可撤回・消去を巻き戻さない。取り込み/履歴保持と、利用停止・本文削除を区別する。

## 5. 状態機械のガード

- AI/importerはreview_status=user_adoptedを生成レスポンスで設定できない。
- 学習器はpolicy、source attribution、確定した予定状態を変更できない。
- shadowの成果物はinternalに自動混入しない。配備昇格にはmodel/用途ごとの評価が必要。
- provisionalを参照した出力は、その根拠を引き継ぐ。要約・別モデル経由で採用済み扱いにしない。
- user_adoptedでもstale/retracted/erasedは通常利用不可。
- 依存有効性が検証不能ならdefer。確認ボタンで破損データを有効にする操作は設けない。


## v0.4：機能分類と任意性の独立軸

feature_tier=core/experimental/evaluation_onlyは製品内の役割。decision_statusは採用合意、implementation_statusは実装状況。FeatureControl.state=enabled/disabledはopt-in/停止。Deploymentのrollout_stageとは別で、enabledだけではlive権限を得ない。

PredictionRecordのsealed_at/contentは不変。PredictionView.result_stateは結果イベントから求める。use_status=eligible/audit_only/blockedは現在の利用可否。Outcomeの未観測・期限切れを失敗へ写像しない。Evaluationは評価履歴であってSchemaの採用ではない。

Feature停止は予測が偽だったという意味でなく、利用をやめる判断。lifecycle=currentの記録でも、機能依存が停止なら通常利用不可。OFF時にreview_statusを勝手にuser_rejectedへ変えず、現在projectionから隔離する。

QualityAssessmentのcontinueは『現在の範囲で追加懸念が見つからなかった』という助言であり、GateDecisionのallowとは異なる。点検/配備/採用/利用の状態を一本の段階昇格enumへ統合しない。

## W30-02：既存契約の状態軸と書込境界

この追記は配布v0.4・契約3の既存境界を具体化する。詳細契約全体の承認、W30-01のDRAFT承認、稼働API移行を意味しない。既存enum/const/必須項目は変更しない。以下の書込主体は信頼済み実行コンテキストであり、入力JSONのActor自己申告ではない。

| 軸／実在するフィールド | 値・位置づけ | 書込主体とガード | 他軸から導かないこと |
|---|---|---|---|
| 出自：MemoryDraft.epistemic_kind | 第1節の6値 | 原本・帰属を検査したコアが保存。本文訂正は新Revision | 採用・高confidenceでdirect_recordに変えない |
| 派生の出自：DerivationRequest.epistemic_kind | ai_hypothesis固定 | 許可された生成adapterの結果をコアが検査 | 再要約や別モデルを経ても本人申告に変えない |
| 内容採否：ArtifactView.review_status | provisional/user_adopted/user_rejected | 生成時はprovisional。本人の具体版への採否を追記しコアが投影 | 配備・利用可能性・真偽とは別 |
| 採用記録：MemoryRevision.review_state | confirmed_by_user固定 | 認証本人の確認を検証した採用取引。approved_by.kind=userはDTO制約にすぎない | ArtifactViewのフィールド名・文字列に自動統一しない |
| 変更提案：ChangeRecord.state | proposed/accepted/rejected | 許可された提案者がpropose、認証ownerのapprove/rejectをコアが記録 | authorは提案者。model著の提案がownerに採用されてもauthorを本人へ書き換えない |
| 利用状態：ArtifactView.lifecycle | current/stale/retracted/erased | 現在の根拠・訂正・撤回・消去に従いコアが投影 | user_adoptedでも通常利用できるとは限らない |
| 記録時の配備：ArtifactView.recorded_lane | shadow/internal/presentation/enabled | 信頼済みproducerの記録時配備をコアが保存 | 現在のDeploymentへの追従上書きや採用状態化をしない |
| 現在配備：DeploymentView.stage | shadow/internal/presentation/enabled/suspended | 昇格はowner確認と固定評価。停止はowner/登録済み安全装置 | suspendedはrecorded_laneの追加値ではない |
| 機能制御：FeatureControlView.state | enabled/disabled | opt-inはowner確認、停止は信頼済みowner/system。core無効化は別途拒否 | enabledをlive配備/外部送信許可にしない |
| 機能分類：feature-registry.tier | core/experimental/evaluation_only | 合意を受けた契約管理者が登録。変更ADRと必要な本人判断 | 採否・有効化・実装完了とは別 |
| 方針合意：feature-registry.decision_status | agreed-direction/adopted-for-design/accepted-experimental/candidate/evaluation-plan/reference_only（現行値） | 本人/契約判断の記録に基づく | accepted-experimentalを本番ONとしない |
| 実装進捗：feature-registry.implementation_status | 配布資材はspecified-not-implemented | 実repoはコード・実測証拠から別途報告 | 配布資材の値や試験件数を実repo完成判定に使わない |
| 利用認可：GateDecision.outcome / basis | 第1節の判定5値／根拠4値 | 信頼済みコアが具体Planと現在状態を検査 | 品質助言continue、分類core、採用、配備からallowを生成しない |
| 版座標：Snapshot | content_head/derivation_generation/policy_version/erasure_epoch/learner_version/feature_epoch | 各履歴のコア保存処理が取得 | 数値世代を採否や配備の単一段階へ変換しない |

Featureの分類・合意・実装進捗はregistryのフィールドであり、MemoryRevisionやArtifactViewに同名の定義があるという意味ではない。review_statusの変更でもcontent/出典/producer/required_featuresは不変。required_featuresは全依存とtrusted producerから求め、AIの空配列申告を信用しない。

## W30-02：合法・禁止遷移と守るガード

「合法」は必要条件を満たす参照契約の意味で、実装済み・無条件許可ではない。Schemaは一つの値の形を検査し、前後比較・認証・現在のACL・原子性は保証しない。

| 操作／前→後 | 契約上の条件 | 禁止例／検証・後続 |
|---|---|---|
| 新規派生→provisional | 許可された生成元、入力版/出典、記録時lane。content_headの採用commitとは別 | 生成requestへのreview_status/required_features/recorded_lane混入は未知propertyとして拒否。W32-01へ接続 |
| provisional→user_adopted | ownerの具体版への確認、同一不変版、review event。epistemic_kind/本文/出典/producer/全依存は保持 | model/importerがownerと自己申告して採用、採用時に出自変更/実験依存消去は不可。W31-05/W33-06 |
| provisional→user_rejected | ownerの対象版への却下event。本文は書き換えない | AIによる無反応の却下化は不可。採用後の却下は単純rejectで処理しない。W31-05 |
| proposed→accepted/rejected | approve/rejectはowner。authorは元の提案者のまま。採用時にはHEAD/receipt等の取引ガードも必要 | author=modelという理由だけでownerの採用を禁止するSchema条件は追加しない。W31-05/09 |
| user_adoptedの本文訂正 | 新Revisionを作り、current pointerと依存利用停止を整合させる | 同じ版の本文/Source文字列/ID/digestを上書きしない。W31-06/07 |
| current→stale | 根拠の訂正/失効を検知したコアが通常利用を止める | 採用済みや高scoreでも旧依存を表示/実行しない。参照規則はdependencies_current=Falseでdefer。W31-07 |
| current等→retracted/erased | 対象と権限を検証した撤回/消去。消去は読取停止が先、物理処理は別 | erasedのpayloadを通常GETで返さない（既存契約は404）。enumにerasedがあっても本文返却許可にならない。W31/W33/W40-11 |
| stale/retracted/erased→通常利用 | 単なる状態書換え/古いsnapshot再生で復活させない。訂正・再生成・現在の台帳に基づく別処理が必要 | schema-validな過去データだけで許可を復活しない。参照規則は現在のerased/permission/dependencyを入力して拒否。実復元はW38-07 |
| 配備昇格／停止 | producer/用途ごとの評価・本人確認、停止は安全装置からも可 | 採用でshadowをliveへ自動昇格しない。W30-03と配備担当へ引継ぎ |
| FeatureControl enabled→disabled→enabled | 停止は利用依存を隔離。再ONは具体確認からshadowへ戻し再評価 | 旧liveの自動復活、採否のuser_rejected化、独立原本の消去は不可。実barrier/epochはW42 |
| require_confirmation/defer/deny→allow | 現在状態で新たな具体UsePlan判定。確認不能な依存不整合は保留 | 品質continue/採用済み/検索回数/無反応によるallowへの書換えは不可。W33 |

ArtifactViewは保存/投影を表す型としてstaleやerasedの形も記述できる。GETの応答可否は別の利用境界で決める。今回、erasedをenumから削除したり、同型を通常読取認可の代用品にする破壊変更は行わない。

## W30-02：対応・移行案（DRAFTを承認へ進めない）

| 差異 | 今回固定する非破壊扱い | 未承認の案と影響／判断者 |
|---|---|---|
| confirmed_by_user / user_adopted | 両方の既存wire表現を保持。意味説明ではどちらも本人採用の文脈を指すが型同一とはしない | 将来の明示adapterまたは版付き名称統一。consumer/fixture/移行/拒否規則に影響。contract owner、W30-06 |
| Actor user/rule / caller owner/system | DTO自己申告は権限ではない。既存表現のまま | 認証文脈への具体adapterはW30-01 D2のまま。session/account/vault接続に影響。本人＋認証担当、W30-04 |
| Task pending/accepted/dismissed、TODO/DONE/SKIPPED | 現行モデルの状態を保持。記憶採否/Intentionへ変換しない | SKIPPED→cancelled等の一意写像は未承認。既存データの意味・再開意思に影響。本人、W36-01/06 |
| MemoryEntry processing/review/stored/failed/accepted | 取込処理の集約状態として保持 | lifecycleやprovisionalへの移行は未承認。解析失敗と本人却下を混同する影響がある。保存担当＋本人、W31/W39 |
| 採用済み予定→組織履歴補完 | 既存コードの挙動を変更しない。予定採用と学習同意は同じと確定しない | 具体用途Plan/同意接続はW30-01 D4のまま。既存便利機能と将来の利用停止に影響。本人＋権限担当、W33/W37 |

今回のJSON Schema差分は$commentだけで、受理集合・86型・契約version・38 API・46操作・25機能を維持する。破壊的な名称変更、旧データの変換、DRAFTの承認はない。既存API/DTO/fixture/受入本文は変更不要で、その互換性を既存資材試験で検査する。

## W30-02：検証範囲と接続制限

`fixtures/w30-02-state-cases.json` と `tests/test_w30_02_state_axes.py` は合成の型/状態例と既存 `reference/policy_model.py` の参照規則を照合する。採用前後例の比較は契約例の点検であり、採用transactionの実装ではない。既存Schemaで拒否できる偽装と、型は通るが信頼済みcallerで拒否すべき偽装を分ける。

重点対応：AUTO-003（独立軸・shadow）、AUTO-005（仮説/依存保持）、AUTO-008（採用≠真実）、AUTO-018（stale通常利用停止）、AUTO-019（消去優先）。関連AUTO-006、V04-004、V04-037も局所検査する。REQは対応するREQ-AUTO/REQ-V04。API/feature/REQの全参照は既存test_v04_assets.pyで確認する。

実repoでは既存account認証、Task/MemoryProposalのaccepted、OCR保存、検索があるが、Source/Ledger/4権限Gate/配備/FeatureControl portは未接続。現在の/apiをこの検査で保護したことにはしない。実DB・本人認証・失効伝播・通常GET 404・TOCTOU・外部送信・実機は後続担当の試験であり、ここでは合格扱いにしない。

## W30-03：未採用内容と用途別配備の利用条件

以下はADR-014/017とdecision-review、api-semanticsの具体化。既存DRAFT契約の承認状態は変更しない。既存ArtifactView/Grade/DeploymentView/RecallV3Requestを再利用し、新しい状態enumを作らない。

| 現在の対象feature × producer_version × purposeのstage | provisionalの実運用内部検索 | user_adoptedの実運用内部検索 | 本人への提示 | 外部送信・行動 |
|---|---|---|---|---|
| shadow | 不可（検証領域のみ） | 不可（採用でも配備を越えない） | 不可 | 不可 |
| internal | 条件付き可、仮説経路を保持 | 条件付き可、採用済み経路も保持 | 不可 | 不可 |
| presentation | 条件付き可 | 条件付き可 | 別Attention判定で条件付き可 | 不可 |
| enabled | 条件付き可 | 条件付き可 | 別Attention判定で条件付き可 | 別Action判定・確認/限定委任が必要 |
| suspended/対象配備不明 | 通常利用不可 | 通常利用不可 | 不可 | 不可 |

表は用途の上限であり許可証ではない。全行で現在のACL、同意、消去、依存版・required_features、FeatureControl、操作固有条件を再検査する。user_rejected/retracted/erased等の記録形がSchemaを通っても通常利用を許さない。監査閲覧は通常検索と別用途。停止/撤回操作は新規利用の上限表で妨げない。

Gradeのfeature/producer_version/purposeは一組。例えばgist × generator-v1 × internal_recallのinternal配備は、同じ生成器のreflection提示、generator-v2、schema機能へ引き継げない。Gradeは評価・承認情報を含むが現在の利用許可ではなく、DeploymentViewの現在版とUsePlanを照合する。未知の組は推測で補わない。

ArtifactView.recorded_laneは生成時の履歴であり現在のDeployment.stageではない。shadow成果物は昇格だけで一括live化しない。api-semanticsの通り、対象版の有効性・用途policyを再検査し新projection generationに取り込む。記録時laneや出自を上書きしない。再検査記録・原子的切替は後続実装であり、今回の参照Gateにはない。

### 内部候補・提示・本人採用版を分ける

- RecallV3Request.include_provisional=trueは候補拡張の要求だけ。falseなら未採用候補を含めない。mode=internalでも実検索の結果に影響すればlive利用であり、shadowを許さない。stageやtrusted callerをこのDTOへ追加して自己申告させない。
- RecallV3Hitのreview_status、epistemic_kind、evidence_refs、route_refs、conditions、uncertaintiesにより仮説候補を表現する。再要約でも元根拠・経路・制限を継承し、別モデルや採用イベントでai_hypothesisを事実へ洗浄しない。required_featuresは参照先の全由来から求める。Hitに重複した新正本を追加しない。
- exactの候補拡張と最終事実の根拠は別。include_provisional=trueのexactを型だけで禁止せず、最終回答は検証済み原文へ戻る。候補に使えた仮説を確定回答に変えない。
- getItemは既存ItemView.current_revision/MemoryRevisionの本人採用版のみ。ArtifactViewやprovisionalのRevisionを返さない。allow_provisionalはapproveChange/adoptDerivationを呼んだことにも、本人採用イベントにもならない。採用済みでも出自ai_hypothesisは保持する。

局所例はfixtures/w30-03-use-cases.jsonとtests/test_w30_03_use_conditions.py。既存参照Gateでは実運用の内部検索にもtrusted live_use=Trueを明示する。既定Falseは検証計算の例に限る。経路継承テストは合成例の意味整合検査であり、実検索器/DAG継承の実装ではない。
