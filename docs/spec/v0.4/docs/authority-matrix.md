# v0.4 権限・自動化一覧（46処理）

機械可読正本：contracts/operation-registry.json。CSVも同じ内容。46処理クラスは38APIへ写像され、別々のサービスや画面を要求するものではない。

Structure=整理、Epistemic=本人/他者についての採用、Attention=提示・注意への介入、Action=外部/端末機能への作用。生成・採用・提示・送信・学習を別のUsePlanとして検査する。

**Provisionalは未採用状態、Shadowは配備段階、Auto/Confirmは今回の判定、Pre-authorizedは限定委任という根拠**。一つのenumに混ぜない。機能分類core/experimental/evaluation_onlyはさらに別軸。

| operation | 処理 | 必要権限 | 規則 | 生成物状態 | 必須の条件 |
|---|---|---|---|---|---|
| `source_import` | 原文・メモ受領 | structure | auto | recorded | 取得・保管の同意。保存成功と解析成功を分離 |
| `capture_start` | 音声取得開始 | action | confirm_or_delegate | none | OS許可・取得同意・開始表示・対象時間・保持期間 |
| `capture_stop` | 音声取得停止 | action | auto | none | 停止を承認待ちにしない。欠落も記録 |
| `transcribe_local` | 端末内文字起こし | structure | auto | provisional | 原音の読取許可・媒体版・区間を固定 |
| `transcribe_remote` | 外部文字起こし | structure, action | confirm_or_delegate | provisional | 外部送信先・目的・原音範囲を許可 |
| `boundary_generate` | 出来事境界推定 | structure | auto | provisional | 原本を分割上書きしない。生成版を残す |
| `episode_group` | Episode階層・分割統合の候補 | structure | auto | provisional | 任意粒度・循環禁止。本人の境界訂正を維持 |
| `embedding_local` | 端末埋め込み・索引 | structure | auto | derived | 同じmodel/dimensionで比較。元と同じACL |
| `embedding_remote` | 外部埋め込み | structure, action | confirm_or_delegate | derived | 検索前の索引作成も外部送信。失敗時無断fallback禁止 |
| `topic_generate` | 話題・別名候補 | structure | auto | provisional | 敏感な分類と人物同一性を確定しない |
| `semantic_link_generate` | about/related_to等の候補 | structure | auto | provisional | same_as・因果確定とは別操作 |
| `entity_merge` | 同一人物・同一対象の採用 | structure, epistemic | confirm | user_adopted | 類似度で自動mergeしない。差分と影響範囲 |
| `gist_generate` | Gist・段階要約 | structure | auto | provisional | 条件・否定・不確実性と原文位置を保存 |
| `interpretation_generate` | 本人の受け止め方の推測候補 | structure, epistemic | auto | provisional | 本人の属性へ自動反映しない。用途上限internal |
| `schema_generate` | 体験から転用Schema候補 | structure, epistemic | auto | provisional | 対応構造・適用条件・反例・根拠を持つ |
| `recall_internal` | 複数経路の検索・Cue識別 | structure | auto | none | 検索対象/内部利用許可。採用済み経路も必ず残す |
| `workspace_build` | 作業スペースを組み立てる | structure | auto | provisional | 参照版・仮説・不明・操作の検討状態を分離 |
| `present_reflection` | 探索的振り返りの提示 | attention | auto | provisional | 提示同意・機微性・目的を判定。仮説ラベル。多様性はこの用途だけ |
| `present_exact` | 日時等の正確な回答提示 | attention | auto | recorded | 確かな原文根拠に戻る。表示履歴で正答を減点しない |
| `profile_adopt` | 人物属性・価値観・長期目標の採用 | epistemic | confirm | user_adopted | 範囲/期限/差分を確認。objective_truthへ変換しない |
| `high_impact_advice` | 高影響な判断への採用 | epistemic, attention | confirm | user_adopted | 根拠の詳細検証。不十分なら確認以前に保留 |
| `intention_generate` | 行動・約束の候補 | structure | auto | provisional | 候補を通知・外部taskに直結しない |
| `intention_activate` | 意図をactiveにする | epistemic, action | confirm_or_delegate | active | 委任可は本人の明示行為意図に限定。AI推測は個別確認 |
| `notification_schedule` | 通知予約 | attention, action | confirm_or_delegate | none | active intention・通知設定・上限・内容非表示を確認 |
| `calendar_create` | 外部予定を作成 | action | confirm_or_delegate | none | 本人の明示意図、日時/zone/対象calendar確定、重複・競合なし |
| `calendar_delete` | 予定削除 | action | confirm | none | 対象予定と版を確認。日時一致だけで削除しない |
| `external_ai_send` | 外部AIへ文脈を送信 | action | confirm_or_delegate | none | 宛先・目的・依存元ACL・payloadを固定。プロフィール採用権限は渡さない |
| `message_send` | メール・他者への連絡/共有 | attention, action | confirm | none | 宛先と最終本文を固定した本人意思。包括委任は本版で不可 |
| `memory_erase` | 記憶と指定派生物の消去 | action | confirm | none | 削除範囲・復旧限界を提示。利用停止は直ちに、物理処理はjob |
| `feedback_record` | 本人評価・提示履歴 | attention | auto | recorded | shown≠helpful。systemによる表示ログと本人評価の主体を分離 |
| `learn_candidate` | 結合・ranker候補の学習 | structure, attention | auto | derived | 学習同意・撤回・manifest。shadow学習は本番へ混ぜない |
| `model_activate` | 学習版/機能利用段階を有効化 | structure, attention | confirm | none | 品質・安全・負担評価を通す。false confidenceで代替しない |
| `projection_rebuild` | 表示・索引の再構築 | structure | auto | derived | 権限・削除・現在版検証、generation切替は原子的 |
| `policy_grant` | 事前委任・権限拡大 | action | confirm | none | 期限・対象・回数/byte上限、本人だけが設定 |
| `policy_revoke` | 許可・委任の撤回 | action | auto | none | 撤回をAI判断や確認待ちで遅らせない |
| `deployment_promote` | 機能・生成器・用途の配備昇格 | structure, attention | confirm | none | 固定評価と本人確認。未採用仮説の真実化ではない |
| `deployment_suspend` | 配備の停止・緊急差戻し | structure | auto | none | 停止だけ。新たな権限を増やさない。安全装置からも可 |
| `prediction_record` | 事前予測の封印保存 | structure, epistemic | auto | provisional | 機能opt-in・配備・未来情報排除。本文/判定基準を結果前に固定 |
| `prediction_evaluate` | 予測と観測の照合評価 | structure, epistemic | auto | provisional | 対応・観測窓・欠測・実行条件・独立性を検査。Schemaへ直接適用しない |
| `prediction_audit_read` | 停止後も可能な予測監査閲覧 | structure | auto | recorded | 本人の監査用途のみ。通常想起/外部送信へ混入させない |
| `outcome_record` | 結果の報告・観測記録 | structure | auto | recorded | 予測結果を捏造しない。停止中も原記録/照合待ちを保持し学習しない |
| `quality_assess` | 根拠/反例/条件/適用範囲の横断点検 | structure, epistemic | auto | provisional | 点検結果は助言。続行推奨でGateを迂回しない |
| `counterevidence_search` | 反例と代替説明の探索 | structure | auto | provisional | 反例が見つからないことを反例がない証拠にしない。検索予算を分ける |
| `feature_enable` | 任意機能へのopt-in | action | confirm | none | opt-inはShadow開始まで。配備昇格/外部送信は別確認。必須機能を外す操作ではない |
| `feature_disable` | 任意機能の停止/依存隔離 | action | auto | none | 停止を確認待ちにしない。epoch更新と依存利用停止、queue拒否、baselineへ |
| `feature_control_read` | 機能状態の表示 | structure | auto | recorded | 状態と未実装/停止の理由を明示 |

## v0.4の追加境界

Predictionがenabledでも結果の本人表示にはAttention、外部AIへの入力にはAction、人物属性への採用にはEpistemicの別判定が必要。生音の取得許可は外部文字起こし許可ではない。

QualityAssessmentは権限を発行しない。高い成績や『問題なし』だけで確認/委任を不要にしない。Evidence評価での機能配備と本人の用途許可を独立に扱う。

停止・撤回は即時だが、信頼済み本人/system/vaultの検査は必要。実験停止後のgetPrediction/listOutcomesは本人の監査向けで、ライブ参照の抜け道ではない。

この表は通常条件の既定。全依存の許可、消去/訂正、配備、FeatureControl、対象Plan、予算、機微/高影響をUse-siteで再判定する。LLM出力のconfidenceやActor宣言は認可情報にならない。

## W30-03：provisionalの利用許可と提示許可

state-modelの配備表はfeature × producer_version × purposeごとの上限。autoもenabledも包括許可ではない。allow_provisionalは利用結果であり採否を更新しない。

| 操作 | 内部利用から追加で必要な条件 | 禁止する短絡 |
|---|---|---|
| recall_internal / workspace_build | 許可済み検索対象、現行依存、仮説・根拠経路・不明の保持 | 内部処理なのでshadowでも実検索へ混ぜる |
| interpretation_generate | 本人属性へ自動反映せず、用途上限internalを保持 | present_reflectionを経由して私的解釈の上限を外す |
| present_reflection | 対象用途のpresentation以上、Attention、提示同意・機微性・目的、仮説ラベル | ラベルがあれば機微な人物評価を無条件表示する |
| present_exact | 対象用途のpresentation以上、Attention、確かな原文詳細 | provisional候補を確定した事実として提示する |
| profile_adopt / high_impact_advice | 登録簿のEpistemic/Attention、本人確認と具体根拠。根拠不足は保留 | 検索で使えた、enabled、本人無反応を採用と扱う |
| external_ai_send / 行動 | 対象用途enabledに加え、Actionと最終Planに束縛した確認/許された委任 | 保存・内部利用・提示の同意を転用する |

参照規則のsensitive=Trueは提示でも確認を要求し、attention_permitted=Falseは保留する。これは具体的な機微分類器の完成や本人合意を意味しない。core/experimental/evaluation_only、FeatureControl、配備、採否、Gateを独立して確認し、evaluation_onlyをlive用途へ流用しない。

### DRAFTのまま残す判断

- 機微/高影響の具体分類と仮説提示対象：提案は固定ルールと本人再確認を組み合わせ、私的解釈のinternal上限を維持する。対象を広げる案は提示頻度・人物評価・同意UIに影響するため、本人と権限担当の判断が必要。今回、分類や包括提示許可を追加しない。
- W30-02のActor user/rule→認証owner/system接続：既存session/account/vaultからtrusted factsを作る案を維持。誤接続はshadow隔離と本人確認を迂回する。DTOを信頼せず未接続としてW30-04/W33へ渡す。
- confirmed_by_user/user_adoptedの統一、Task採否/SKIPPEDの写像、予定採用→組織学習同意は引き続き未承認。前者はgetItemの互換、後二者は採否・利用目的に影響する。今回の表を根拠に既存データを変換しない。

既存reference/policy_model.pyはtrusted factsを受ける判定例であり、配備の組照合・provisional経路継承・interpretationの用途上限・getItem投影を実装しない。SchemaもACLや意味支持を保証しない。これらの実接続はW31/W33/W34/W42の担当範囲。局所検査を実アプリ受入合格にしない。
