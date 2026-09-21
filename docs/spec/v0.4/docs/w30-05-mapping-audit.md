# W30-05 Authority Matrix対応監査

既存登録簿からの読取監査。DRAFTの承認・アプリ接続を意味しない。元46操作・38 API・25 featureの正本は変更なし。複数対応は用途ごとの候補であり、callerが弱いクラスを選ぶ許可ではない。

## 操作 → 機能・API

| operation | feature | authorities | gate | API候補 |
|---|---|---|---|---|
| source_import | source | structure | auto | importSource,evaluateUse |
| capture_start | selected_media | action | confirm_or_delegate | evaluateUse |
| capture_stop | selected_media | action | auto | evaluateUse |
| transcribe_local | selected_media | structure | auto | evaluateUse |
| transcribe_remote | selected_media | structure,action | confirm_or_delegate | evaluateUse,executeAction |
| boundary_generate | episode_structure | structure | auto | recordDerivation,evaluateUse |
| episode_group | episode_structure | structure | auto | recordDerivation,evaluateUse |
| embedding_local | recall | structure | auto | evaluateUse |
| embedding_remote | recall | structure,action | confirm_or_delegate | evaluateUse,executeAction |
| topic_generate | semantic_network | structure | auto | recordDerivation,evaluateUse |
| semantic_link_generate | semantic_network | structure | auto | recordDerivation,evaluateUse |
| entity_merge | semantic_network | structure,epistemic | confirm | evaluateUse,adoptDerivation |
| gist_generate | gist | structure | auto | recordDerivation,evaluateUse |
| interpretation_generate | schema | structure,epistemic | auto | recordDerivation,evaluateUse |
| schema_generate | schema | structure,epistemic | auto | recordDerivation,evaluateUse |
| recall_internal | recall | structure | auto | getSource,getItem,getDerivation,evaluateUse,recall |
| workspace_build | recall | structure | auto | evaluateUse |
| present_reflection | life_support | attention | auto | evaluateUse,recordPresentation |
| present_exact | life_support | attention | auto | evaluateUse,recordPresentation |
| profile_adopt | ledger | epistemic | confirm | approveChange,evaluateUse,adoptDerivation |
| high_impact_advice | authority | epistemic,attention | confirm | evaluateUse |
| intention_generate | intentions | structure | auto | recordDerivation,evaluateUse |
| intention_activate | intentions | epistemic,action | confirm_or_delegate | evaluateUse,activateIntention |
| notification_schedule | life_support | attention,action | confirm_or_delegate | evaluateUse,executeAction |
| calendar_create | life_support | action | confirm_or_delegate | evaluateUse,executeAction |
| calendar_delete | life_support | action | confirm | evaluateUse,executeAction |
| external_ai_send | authority | action | confirm_or_delegate | evaluateUse,executeAction |
| message_send | life_support | attention,action | confirm | evaluateUse,executeAction |
| memory_erase | device_storage | action | confirm | evaluateUse,executeAction,erase |
| feedback_record | feedback | attention | auto | evaluateUse,recordFeedback,recordSchemaApplication |
| learn_candidate | personal_ranker | structure,attention | auto | evaluateUse,prepareModel |
| model_activate | personal_ranker | structure,attention | confirm | evaluateUse,activateModel |
| projection_rebuild | dependency_network | structure | auto | evaluateUse |
| policy_grant | authority | action | confirm | evaluateUse,createGrant |
| policy_revoke | authority | action | auto | evaluateUse,revokeGrant |
| deployment_promote | authority | structure,attention | confirm | evaluateUse,promoteDeployment |
| deployment_suspend | authority | structure | auto | evaluateUse,suspendDeployment |
| prediction_record | prediction_loop | structure,epistemic | auto | recordPrediction |
| prediction_evaluate | prediction_loop | structure,epistemic | auto | evaluatePrediction |
| prediction_audit_read | prediction_loop | structure | auto | getPrediction,listOutcomes |
| outcome_record | feedback | structure | auto | recordOutcome |
| quality_assess | quality_checks | structure,epistemic | auto | recordAssessment,getAssessment |
| counterevidence_search | quality_checks | structure | auto |  |
| feature_enable | authority | action | confirm | changeFeatureControl |
| feature_disable | authority | action | auto | changeFeatureControl |
| feature_control_read | authority | structure | auto | getFeatureControl |

## 全API：読取・内部・外部候補

GETでも認証・vault・現在policy・消去/依存・scopeを省略しない。POSTは外部送信を意味しない。executeActionは外部/端末作用候補、recordDerivation等の内部生成が外部AIを使う場合も別の送信判定が先。空クラスは免認可ではなく既存noteの共通core検査を伴う。

| API | method | path | classes | 共通検査・note |
|---|---|---|---|---|
| importSource | POST | /v3/vaults/{vault_id}/sources/import | source_import | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| getSource | GET | /v3/vaults/{vault_id}/sources/{source_id} | recall_internal | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 共通read policy＋取込原文範囲を確認。Sourceがrawであることは客観的真実の宣言ではない。 |
| proposeChange | POST | /v3/vaults/{vault_id}/changes/propose |  | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 本人または許可済みmodel。採用せず固定候補。読取/生成許可は共通coreで検査。 |
| approveChange | POST | /v3/vaults/{vault_id}/changes/{change_id}/approve | profile_adopt | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| rejectChange | POST | /v3/vaults/{vault_id}/changes/{change_id}/reject |  | authenticated principal + same vault + current read/write policy + erasure/closure + scope / owner限定。採用済み変更はこの操作で書き換え不可。 |
| getItem | GET | /v3/vaults/{vault_id}/items/{item_id} | recall_internal | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| recordDerivation | POST | /v3/vaults/{vault_id}/derivations | boundary_generate,episode_group,gist_generate,interpretation_generate,schema_generate,semantic_link_generate,intention_generate,topic_generate | authenticated principal + same vault + current read/write policy + erasure/closure + scope / kindからコアが操作classを決める。CognitiveRoleはtopic_generateの仮分類契約を共有。class名のclient指定で下げない。 v0.4: cognitive_roleのproducer_featureはcognitive_role_study。評価専用の機能制御/利用目的も別に検査しliveへ混ぜない。 |
| getDerivation | GET | /v3/vaults/{vault_id}/derivations/{artifact_id} | recall_internal | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| evaluateUse | POST | /v3/vaults/{vault_id}/use-decisions | source_import,capture_start,capture_stop,transcribe_local,transcribe_remote,boundary_generate,episode_group,embedding_local,embedding_remote,topic_generate,semantic_link_generate,entity_merge,gist_generate,interpretation_generate,schema_generate,recall_internal,workspace_build,present_reflection,present_exact,profile_adopt,high_impact_advice,intention_generate,intention_activate,notification_schedule,calendar_create,calendar_delete,external_ai_send,message_send,memory_erase,feedback_record,learn_candidate,model_activate,projection_rebuild,policy_grant,policy_revoke,deployment_promote,deployment_suspend | authenticated principal + same vault + current read/write policy + erasure/closure + scope / operationはコアのUsePlanから再計算。DTOの操作名に権限はない。 |
| recordConfirmation | POST | /v3/vaults/{vault_id}/confirmations |  | authenticated principal + same vault + current read/write policy + erasure/closure + scope / owner session限定。コア保存済みdecision/binding/expiryを照合。認可の自作は不可。 |
| adoptDerivation | POST | /v3/vaults/{vault_id}/derivations/{artifact_id}/adopt | profile_adopt,entity_merge | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 意味変更の影響でowner採用またはentity_merge等を選ぶ。policy-adoptは別API。 |
| createGrant | POST | /v3/vaults/{vault_id}/policy/grants | policy_grant | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| revokeGrant | POST | /v3/vaults/{vault_id}/policy/grants/{grant_id}/revoke | policy_revoke | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| recall | POST | /v3/vaults/{vault_id}/recall | recall_internal | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| recordPresentation | POST | /v3/vaults/{vault_id}/presentations | present_reflection,present_exact | authenticated principal + same vault + current read/write policy + erasure/closure + scope / session modeからclassを決める。表示前にevaluateUse、実表示後のみevent保存。 |
| recordFeedback | POST | /v3/vaults/{vault_id}/feedback | feedback_record | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| recordObservation | POST | /v3/vaults/{vault_id}/observations |  | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 本人申告はowner、sensor/providerは登録adapterのsystem。originはadapterが設定。未認証入力を観測へしない。 |
| activateIntention | POST | /v3/vaults/{vault_id}/intentions | intention_activate | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| transitionIntention | POST | /v3/vaults/{vault_id}/intentions/{intention_id}/transition |  | authenticated principal + same vault + current read/write policy + erasure/closure + scope / ownerの明示した遷移、または固定ruleによるexpiry等の制限された更新。モデルは完了を確定できない。 |
| prepareAction | POST | /v3/vaults/{vault_id}/actions/prepare |  | authenticated principal + same vault + current read/write policy + erasure/closure + scope / ownerまたは許可済み計画器。保存可能でも実行可能ではない。executeで別途Gate。 |
| executeAction | POST | /v3/vaults/{vault_id}/actions/{action_id}/execute | notification_schedule,calendar_create,calendar_delete,external_ai_send,embedding_remote,transcribe_remote,message_send,memory_erase | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| getAction | GET | /v3/vaults/{vault_id}/actions/{action_id} |  | authenticated principal + same vault + current read/write policy + erasure/closure + scope / ownerまたは当該ジョブworkerのread scope。別vault/削除内容は返さない。 |
| recordSchemaApplication | POST | /v3/vaults/{vault_id}/schema-applications | feedback_record | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| prepareModel | POST | /v3/vaults/{vault_id}/models/candidates | learn_candidate | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 learner kindと全manifestからassociation_learning/personal_ranker等の必要featureをコアが確定。便宜的なregistryのfeature_id一つだけで判定しない。 |
| activateModel | POST | /v3/vaults/{vault_id}/models/{model_id}/activate | model_activate | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 learner kindと全manifestからassociation_learning/personal_ranker等の必要featureをコアが確定。便宜的なregistryのfeature_id一つだけで判定しない。 |
| erase | POST | /v3/vaults/{vault_id}/erasures | memory_erase | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| getJob | GET | /v3/vaults/{vault_id}/jobs/{job_id} |  | authenticated principal + same vault + current read/write policy + erasure/closure + scope / ownerまたは当該ジョブworkerのread scope。段階状態を返すのみ。 |
| promoteDeployment | POST | /v3/vaults/{vault_id}/deployments | deployment_promote | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| suspendDeployment | POST | /v3/vaults/{vault_id}/deployments/{deployment_id}/suspend | deployment_suspend | authenticated principal + same vault + current read/write policy + erasure/closure + scope / 用途と対象をコアが確定しoperation registryの必要全権限を適用する。 |
| recordPrediction | POST | /v3/vaults/{vault_id}/predictions | prediction_record | authenticated caller + same vault + current policy + dependency/feature closure + immutable versions + purpose / v0.4 docs/prediction-loop.md / quality-assessment.md / feature-control.md |
| getPrediction | GET | /v3/vaults/{vault_id}/predictions/{prediction_id} | prediction_audit_read | authenticated caller + same vault + current policy + dependency/feature closure + immutable versions + purpose / v0.4 docs/prediction-loop.md / quality-assessment.md / feature-control.md |
| recordOutcome | POST | /v3/vaults/{vault_id}/predictions/{prediction_id}/outcomes | outcome_record | authenticated caller + same vault + current policy + dependency/feature closure + immutable versions + purpose / v0.4 docs/prediction-loop.md / quality-assessment.md / feature-control.md |
| listOutcomes | GET | /v3/vaults/{vault_id}/predictions/{prediction_id}/outcomes | prediction_audit_read | authenticated caller + same vault + current policy + dependency/feature closure + immutable versions + purpose / v0.4 docs/prediction-loop.md / quality-assessment.md / feature-control.md |
| evaluatePrediction | POST | /v3/vaults/{vault_id}/predictions/{prediction_id}/evaluations | prediction_evaluate | authenticated caller + same vault + current policy + dependency/feature closure + immutable versions + purpose / v0.4 docs/prediction-loop.md / quality-assessment.md / feature-control.md |
| recordAssessment | POST | /v3/vaults/{vault_id}/assessments | quality_assess | authenticated caller + same vault + current policy + dependency/feature closure + immutable versions + purpose / v0.4 docs/prediction-loop.md / quality-assessment.md / feature-control.md |
| getAssessment | GET | /v3/vaults/{vault_id}/assessments/{assessment_id} | quality_assess | authenticated caller + same vault + current policy + dependency/feature closure + immutable versions + purpose / v0.4 docs/prediction-loop.md / quality-assessment.md / feature-control.md |
| changeFeatureControl | POST | /v3/vaults/{vault_id}/features/{feature_id}/control | feature_enable,feature_disable | authenticated caller + same vault + current policy + dependency/feature closure + immutable versions + purpose / v0.4 docs/prediction-loop.md / quality-assessment.md / feature-control.md |
| getFeatureControl | GET | /v3/vaults/{vault_id}/features/{feature_id}/control | feature_control_read | authenticated caller + same vault + current policy + dependency/feature closure + immutable versions + purpose / v0.4 docs/prediction-loop.md / quality-assessment.md / feature-control.md |

## 全機能：操作の有無

直接操作のない機能を新APIへ独断で割り当てない。分類・合意・実装状態・配備・認可は別軸。

| feature | tier | direct operations |
|---|---|---|
| source | core | source_import |
| ledger | core | profile_adopt |
| authority | core | high_impact_advice,external_ai_send,policy_grant,policy_revoke,deployment_promote,deployment_suspend,feature_enable,feature_disable,feature_control_read |
| episode_structure | core | boundary_generate,episode_group |
| semantic_network | core | topic_generate,semantic_link_generate,entity_merge |
| dependency_network | core | projection_rebuild |
| gist | core | gist_generate |
| schema | core | interpretation_generate,schema_generate |
| recall | core | embedding_local,embedding_remote,recall_internal,workspace_build |
| quality_checks | core | quality_assess,counterevidence_search |
| feedback | core | feedback_record,outcome_record |
| intentions | core | intention_generate,intention_activate |
| life_support | core | present_reflection,present_exact,notification_schedule,calendar_create,calendar_delete,message_send |
| device_storage | core | memory_erase |
| selected_media | core | capture_start,capture_stop,transcribe_local,transcribe_remote |
| prediction_loop | experimental | prediction_record,prediction_evaluate,prediction_audit_read |
| association_learning | experimental |  |
| personal_ranker | experimental | learn_candidate,model_activate |
| adaptive_attention | experimental |  |
| scoped_social_models | experimental |  |
| capability_calibration | evaluation_only |  |
| exposure_balance_study | evaluation_only |  |
| cognitive_role_study | evaluation_only |  |
| developmental_analogy | evaluation_only |  |
| continuous_capture_study | evaluation_only |  |

## 未対応・重複・保留（DRAFT）

- M1：evaluateUseは37クラスで、GateRequestの46クラスと差がある。不足はprediction_record,prediction_evaluate,prediction_audit_read,outcome_record,quality_assess,counterevidence_search,feature_enable,feature_disable,feature_control_read。提案は全クラスへ写像を同期する案、対案は管理/監査等を専用経路に限定する案。公開する評価用途と認可境界が変わるためcontract owner判断まで写像変更・実接続を停止。今回は差の検出のみ。
- M2：counterevidence_searchはAPI写像なし。内部検索に限定する案またはevaluateUseへ追加する案。内部/公開の責務と検査範囲に影響するため未決。
- M3：association_learning,adaptive_attention,scoped_social_models,capability_calibration,exposure_balance_study,cognitive_role_study,developmental_analogy,continuous_capture_studyは直接operationなし。既存共通処理の利用候補/評価研究を直接APIへ変換しない。具体操作の追加は未承認。
- 同じ内部クラスが複数APIへ現れることは重複サービスの指示ではない。API ID・各クラス列内の重複は拒否し、複数API対応は上表に保持。空クラスのproposeChange/rejectChange/recordConfirmation等は既存noteを上表に記載した。
- M4：予定作成委任は本人の明示意図と日時/対象/予算等の限定が必要。機微推論の提示対象と外部AIの宛先/payload/保持条件は未決。既存DRAFTとgate-and-delegationを維持し、包括委任は作らない。message_send/profile_adopt/entity_merge/memory_erase/policy_grantは委任一致だけで許可しない。

## 既存APIの迂回候補（実保護は未接続）

| 実repo相対ファイル | 検出対象 | 制限/引継ぎ |
|---|---|---|
| backend/app/api/task.py | /{task_id}/accept | 既存Task採用はv3確認receiptではない。W31/W33/W36 |
| backend/app/api/memory.py | /proposals/{proposal_id}/accept | 予定/Task採用と組織履歴の作用。W31/W33/W36 |
| backend/app/api/interaction.py | share_level | 共有度を外部送信Grantへ変換しない。W33-10 |
| backend/services/search/embedding.py | httpx.post | 索引生成の外部embeddingも送信許可が必要。W33-10 |

列挙はソース構造とW30-01 E1/E3/E6の監査であり、脆弱性の実証や迂回修正済みの証拠ではない。現/apiを保持し、新/v3の追加だけで保護できたと扱わない。未登録operationは既存Schema/参照Gateで拒否する。保存原文/ID/digestと役割・全由来を変更しない。
