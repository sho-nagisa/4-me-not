# W30-01 現コード・v0.3/v0.4契約の棚卸し

調査日：2026-09-07 JST。状態：完了（棚卸し・静的参照検査のみ）。分類：core。
実装済み・実測済み・本人の契約判断・配備状態は独立。後続タスクの完了や製品受入の合格を意味しない。

## 1. 対象と出典

- REPO：`C:/Users/keima/Desktop/4-me-not`
- HEAD：`c872e462ac6abab7986107eabefe8dd8eceb83eb`。仕様が継承する固定コミットと一致。ただし作業ツリーには既存変更がある。
- PACK：`C:/Users/keima/.codex/.chatgpt-projects/g-p-696486f280d081918418aa6ea3658d1c/deliverables/4-me-not-v0.4-codex-task-pack`
- SPEC_ROOT：`C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4`
- SPEC_ROOTはPACKの `reference/4-me-not-collab-v0.4.zip` を参照用に展開したもの。一時領域消去時は同ZIPから再展開する。ZIPと参照元は変更していない。SHA-256は読取検査記録に保存。
- 旧107 IDの出典は同deliverablesの `4-me-not-v0.3-codex-task-pack/task-index.json`。内包 `archive/v0.3-original.zip` にはcodex catalogがないため、存在を仮定せず旧パックで照合した。旧68型／29 APIは内包旧ZIPから直接読んだ。
- ルート・配下のAGENTS.mdと、C:/、C:/Users、C:/Users/keima、C:/Users/keima/DesktopのAGENTS.mdは見つからない。実repoのAGENTSを読めたとは報告しない。仕様AGENTSは参照資料として読み、ルートへ配置・自動適用していない。
- 本文の相対コードパスはREPO相対、仕様パスはSPEC_ROOT相対。付録の仕様参照は絶対パスと行番号。実コードの根拠は下記E表のパス・行と付録の宣言一覧。
- 許可範囲はPACK `tasks/W30-01.md` の棚卸し文書・読取検査記録のみ。元仕様タスクの広い変更候補より今回の限定依頼を適用。仕様・アプリ・DB・models構造を変更しない。

### 版と件数

| 対象 | v0.3参照仕様 | v0.4参照仕様 | 今回の実repo確認 |
|---|---|---|---|
| 配布物／データ契約／HTTP案 | v0.3／2／v2 | v0.4／3／v3 | 配布版・契約3を宣言する実装なし。frontend/package.json:3は0.1.0 |
| JSON Schema $defs | 68 | 86 | v3契約に適合するDTOの接続なし。同名検索だけで適合を認定しない |
| API操作 | 29 | 38（9追加） | 37個の静的route宣言。HEAD参照の33個に未コミットmemory 4個が追加 |
| 内部操作／機能 | 旧契約と別途比較 | 46／25 | 同登録簿・Gate接続なし |
| タスク | 107 | 130＝107継承＋23追加 | ID別確認は付録。W30-01以外に契約準拠完了の証拠なし |
| 分類 | 旧タスクから継承 | core 108／experimental 20／evaluation_only 2 | 運用上のenabled/disabled/shadowは未計測 |
| テスト宣言 | 仕様継承値backend129/frontend16 | 資材の既報合格と別 | backend133/frontend16宣言。今回実行したアプリ試験は0件 |

docs/testing/README.md:67の111/15は現在の宣言数と異なる。仕様docs/repository-current.mdの129/16はHEAD時点の継承値。未追跡OCR試験4件を含む現在の133件は合格数ではない。

## 2. 現コードの責務・接続portと再利用方針

「部分あり」は従来機能を保持して利用できる候補という意味で、v3契約実装済みではない。「未接続」は静的経路・型・テストに該当契約を確認できないこと。稼働サーバーや外部CIは未調査。

| 根拠 | 実在ファイル:行 | 確認した責務／不足／後続 |
|---|---|---|
| E0 | backend/app/main.py:21、:35、:40、:81 | FastAPI、Cookie認証付き8ルーター、health。startupでDB接続するのでimport/起動しない。v3ルーターなし。W30/W33 |
| E1 | backend/app/account_context.py:40、backend/app/main.py:48 | 認証アカウントとdev fallback。本人sessionを再利用候補とするがActor DTOから権限を付けない。4権限・vault境界・Planは未接続。W30-04/W33 |
| E2 | backend/services/memory_service.py:41、:97、:136、:293、backend/models/memory/memory_entry.py:10、backend/models/memory/memory_artifact.py:9 | 画像byte/hashとOCRテキストを別保存、原画像commit後に解析、アカウント別hash重複抑制。Source/Message/EvidenceLocator汎用契約・取得同意・Revisionは不足。W31-01/02、W39 |
| E3 | backend/models/memory/memory_proposal.py:11、backend/services/memory_service.py:203、:234、:259、:402 | pending/accepted、アプリ内予定・Task作成、組織履歴の補完。既存提案UIを保持。作成と採用印は別取引でLedger/HEAD CAS/確認receiptなし。W31-05/09、W33-06、W36 |
| E4 | backend/models/task/task.py:12、backend/services/task_service.py:80、:305、:407、:540 | 候補抽出・承認/却下・完了/再開。TaskStatusとcandidate_statusを既に分離。ActiveIntention/Observation/Outboxではない。W36 |
| E5 | backend/services/interaction_processing_service.py:15、backend/services/ai_service.py:1、backend/services/insight_service.py:1、backend/services/relation_service.py:1 | 保存後索引・候補抽出。AI/Insight/RelationはNoneを返す仮実装。永続job、Episode/Gist/Schemaではない。W32、W36-08 |
| E6 | backend/services/search/query.py:28、:83、backend/services/search/embedding.py:17、:38、backend/services/search/operations.py:63 | 語句/意味/曖昧/新しさの固定重み、ローカルhashと任意外部embedding、却下Taskを索引除外。Recall v3のsnapshot/Gate/Exact-Reflection/依存検査なし。W34、W33-10 |
| E7 | frontend/src/pages/interactionNew/ScreenshotInboxPanel.tsx:1、frontend/src/pages/interactionNew/HistoryPage.tsx:1、frontend/src/pages/interactionNew/SearchPage.tsx:1 | OCR全文・候補・履歴と検索UIの既存部分を保持。Revision差分、Provenance役割、Plan確認、停止UI未接続。W35 |
| E8 | backend/services/calendar_service.py:35、backend/services/reminder_service.py:11、backend/models/calendar/calendar_event.py:1 | 予定・参加者・reminderをDBへ保存。OS通知/provider送信・取消・unknown管理ではない。W36-10/W38-09 |
| E9 | frontend/src/pages/interactionNew/offlineInteractions.ts:3、:31、backend/db/session.py:1、migrations/env.py:1 | localStorage下書き/未送信とサーバーPostgreSQL。端末正本、IndexedDB/OPFS/native、暗号鍵・復元ではない。共有キー/書込例外黙殺を継承課題とする。W38 |
| E10 | backend/services/memory_screenshot_analyzer.py:1、backend/services/memory_history.py:17、tools/ocr_image.ps1:1 | WindowsローカルOCRと文字列解析・履歴補完。音声・CaptureGap・TranscriptRevision・全由来closureなし。W39。新たに作り直さない |
| E11 | tests/test_support.py:1、scripts/run_tests.py:98、:174、scripts/run_tests_local.ps1:44、frontend/package.json:5 | unittest/TestClient/DB cleanup・AlembicとVitest。DB起動/変更を伴うrunnerは今回は実行しない。W40で実結合を検証 |
| E12 | backend/models/memory/memory_entity.py:10、backend/services/memory_service.py:402 | 採用した予定から組織名・場所・利用回数を更新。Prediction/Schema学習器ではない。用途同意・由来・撤回の追加判断が必要。W33/W37/W42 |

modelsの実ルートはbackend/models。GUIDE列挙のbase/person/community/membership/interaction/task/reminder/insight/network/tag/ai/calendar各構造は存在する。さらにaccount/auth/search/memory、task/task.py・task_link.py、calendar/event_participant.pyがある。relationship_task.pyも残る。改名・移動・TypeScript置換なし。packages/memory-core等は存在せず配置提案のまま。

### 境界と失敗時の現状（静的読取）

- E2：不正形式400、容量413、OCR解析失敗422。解析前に原画像はcommitされる。Source receiptや解析jobの汎用契約はない。DB障害の実挙動は未実測。
- E3：不正候補ID400、他account/不在404、pending以外409、accepted再送は保存target IDを返す。一方、並行acceptや予定作成後の中断に対する単一取引・再送安全性は未保証。Taskと組織履歴に二重作用し得る経路をW31-09/W36-08へ引継ぐ。
- E4：却下候補は検索索引から外すが、tests/test_task_workflow_expanded.py:91は却下後の再提案を許す。v3 rejectChangeの抑制と同じ意味にはしない。
- E6：OPENAI_API_KEYの有無で外部embeddingを選ぶ。用途・宛先・payloadに束縛した許可ではない。例外時にローカルfallback。今回は環境変数値・秘密・API送信を調べたり実行したりしていない。
- E9：localStorageの例外を無視するコードがある。端末保存成功・復旧試験合格とはしない。
- FeatureControl/Deployment/QualityAssessment/Predictionは実repoで未接続。停止・再ON・独立原本保持が動作するとの保証はない。未実装をdisabledと表示したことにもせず、配備不明と区別する。

## 3. 状態名・用語の対応案（DRAFT、未承認）

| 現行/仕様の差 | 対応案と変えてはいけない意味 | 判断担当／後続 |
|---|---|---|
| MemoryRevision.review_state=confirmed_by_user 対 ArtifactView.review_status=user_adopted | v3内にも両方残る。採用projectionへの明示adapter案。文字列の一括置換も真実認定もしない | contract owner＋本人、W30-02/06 |
| Actor.kind=user/model/importer/rule 対 Registry actors=owner/model/system/importer | user→ownerは認証本人一致時のみ、rule→systemは登録済処理時のみ。Actor申告だけでは不可。docs/api-semantics.md末尾にも境界写像を記載 | contract owner・認証担当、W30-04 |
| Task candidate_status=pending/accepted/dismissed と MemoryProposal pending/accepted | provisional/user_adopted/user_rejectedへの候補写像。ただし採用範囲は予定/Taskで、人物属性の採用ではない。既存手動Taskのacceptedも自動変換しない | 本人＋contract owner、W30-02、W31-05、W36-01 |
| TaskStatus TODO/DONE/SKIPPED | active/completed/cancelledの一対一対応を決めない。SKIPPEDの意味と再開意思を先に固定 | 本人、W30-02、W36-06 |
| MemoryEntry processing/review/stored/failed/accepted | 取込・解析・候補処理の集約状態。lifecycle/current/staleやrollout shadowとは別軸 | contract owner、W30-02/03 |
| ShareLevel SHARED/PARTIAL/WITHHELD、CommunityRole.OWNER | 会話の共有度・コミュニティ役割。外部送信許可やvault ownerへ転用しない | 権限担当、W30-04/05、W33-10 |
| memory_artifacts 対 ArtifactView | 前者は画像/OCR媒体、後者は版付き派生物＋採否・配備・由来投影。同名に近いだけでDTO互換なし | 保存担当、W31-01/03、W32-01、W39-01 |
| person_id/参加者/抽出evidence 対 ProvenanceRole | speaker/subject/claimant/relayを推測で埋めない。引用文字列と発言者本人の直接証拠は別 | 本人＋契約担当、W31-08/W35-05 |
| FeatureControl enabled/disabled、Deployment rollout、Gate outcome | 別型・別状態のまま。採用でrequired_featuresを消さず、信頼済producerと全由来から算出。continueはallowではない | W30-02/05、W42、W43-05 |
| Source本文/ID/digest、訂正Revision | 既存ID/byte/hashを保持する対応表とdry runが先。出所不明は保留・読取限定。新経験として再計上しない | 本人＋保存担当、W30-06/W31-06/W40-11 |

### 未解決・判断の割当

| ID | 具体案／影響 | 判断担当／後続 |
|---|---|---|
| D1 | contract3内の採否名の差はadapterで明示する案。変更時はSchema/API/fixture/受入を一組で更新。今回は正本を変更しない | contract owner、W30-02/06/07 |
| D2 | account→vaultと認証callerをDTOから分離する案。既存Cookie/CSRFを再利用し、dev fallbackを本番ownerの根拠にしない | 認証担当＋本人、W30-04/W33-03 |
| D3 | Source化は原画像・OCRのID/hashと取込時刻の由来を保持するadapter案。継承不能な由来を空配列で非依存扱いしない | 保存担当＋本人、W30-06/W31-01/02/W39-01 |
| D4 | 既存acceptと組織履歴更新を具体用途Planへ接続する案。予定承認を永続プロフィール学習への包括同意にしない | 本人＋権限担当、W31-05/W33-06/W37-02 |
| D5 | TaskStatusとIntentionの唯一の運用正本を決める。別サービスを二重に立てる前に既存Taskとのstable ID対応を決める | 本人＋実装担当、W36-01 |
| D6 | 外部embeddingの送信はGate/permission closureへ接続する案。現行/apiも保護対象の確認が必要で、新/v3追加だけでは解消しない | 本人＋権限担当、W33-10 |
| D7 | localStorageと端末正本の役割・キー/復旧・鍵を選定する。現サーバーDBを本人端末の暗号化DBと称さない | 本人＋端末担当、W38-01〜08 |
| D8 | 実験依存はimport/起動/応答/migrationとデータ由来を別監査する。未接続の現状を停止barrierの合格とはしない | 実装担当＋独立検証者、W42-01〜07 |
| D9 | アプリテスト件数文書は古い。後続の検証時に実行結果と宣言数を分離して更新する | 検証担当、W40-12 |

## 4. 今回の受入追跡と検証

| REQ／受入 | 仕様箇所 | 今回の達成／未達・引継ぎ |
|---|---|---|
| REQ-AUTO-006／AUTO-006 | acceptance/promotion.feature:35、Actor、api-semanticsのcaller規則 | owner/model境界不足をE1/E3とD2へ記録。モデル採用拒否の実API試験は未実施。W30-04/W33-03/W40-06 |
| REQ-AUTO-008／AUTO-008 | acceptance/promotion.feature:47、docs/state-model.md:25 | 採用と由来不変の契約差を記録。採用イベント/Revision未接続。W31-05/08/W40-03 |
| REQ-AUTO-003／AUTO-003 | acceptance/promotion.feature:17 | provisional/shadowを分けた対応案。実配備隔離の証明なし。W30-03/W34-07 |
| REQ-V04-004／V04-004 | acceptance/v04.feature:23、feature-catalog | 25機能のcore依存参照を静的検査。実コア構成・migration・停止実結合は未実施。W42-01/07 |
| REQ-V04-037／V04-037 | acceptance/v04.feature:221、docs/migration.md | 契約2→3と/apiを区別。v3 endpoint自体未接続で422試験合格とはしない。W30-06/07/W40-11 |

実行作業場所：`C:/Users/keima/Desktop/4-me-not`。
実コマンド：`& './docs/implementation/W30-01-inspect.ps1'`（PowerShell）。終了コード0、静的資材・参照照合28項目合格。
証拠：`docs/implementation/W30-01-evidence.json`。コード宣言・参照行・ファイルhash・HEAD・差分一覧、旧/新ID、実行時刻、各検査結果を収録。
失敗履歴：最初の読取はv0.3 ZIPにcatalogがある前提で終了1。実在する旧パックのtask-index.jsonに出典を訂正して再実行し合格。Python launcherもプロセスを作れず終了1だったため、必要な静的読取はPowerShellのZIP/JSON APIで完結。Python試験の合格記録ではない。最終表照合ではAPIとfeatureに共通するrecallを重複と数える検査側の問題、および表見出し境界の誤検出を修正し、節ごとの照合で28/28合格（最終終了0）を確認した。

今回の検査は参照先・件数・ID・依存順・Schema内参照・APIと権限/機能登録簿の対応のみ。JSON Schemaの全意味検証、参照Gate/予測モデルの動作試験は実施していない。
仕様は変更しておらず、指定の条件付き仕様unittest/check_baselinesは実行対象外。GUIDEの既報85/25/11件を今回の合格として引用しない。新しい鏡写しのアプリテストも追加していない。

既存の実行入口：backendは `scripts/run_tests_local.ps1` または `python -m scripts.run_tests`、frontendはfrontend配下の `npm test`、型/ビルドは `npm run build`。runnerを読取確認したのみ。前者はDB起動・migration・cleanupを伴い今回範囲外。実DB、実LLM、OCR実画像、UI操作、実機、配備状態、独立レビューは未実施。生データや.envは使用せず、コード・仕様・架空fixtureの参照情報だけを検査。外部payload生成/送信は0件。

レビュー：Codexによる自己点検のみ。独立レビュー未実施、DRAFT判断は未承認。今回のコード変更がないため移行・停止・取消・復旧操作はなし。将来のOFFは過去の外部送信や完了した行動を回収しない。

## 5. 付録の読み方

以下は全件の対応表。各行の後続IDは割当であり着手指示ではない。仕様catalogのnot_startedをそのまま実repoの状態に転記せず、E表・コード全体の宣言/ファイル調査と照合した。
未接続の行は「対応する契約実装を確認できない」。単なる同名不在だけでなくE表の近接サービスの責務との差を根拠にする。全関数の実行検証ではない。
型/APIの判断者はcontract ownerと後続担当、操作の許可・移行意味は本人と権限担当。機能分類・既定状態は仕様値であって実repoの配備実測ではない。

### A. JSON Schema 86定義

各型の「旧に有」は名前継承だけを表す。旧RecallV2/FeedbackV2名のV3への変更も「旧に無」へ含まれるため、新機能数ではない。現行Actor/MemoryRevision/ArtifactViewの詳細差は第3節。全行ともv3 DTOの実接続は未確認。

| 定義 | 旧に同名 | 仕様根拠:行 | 近接コードとの差／後続 |
|---|---|---|---|
| Actor | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:6 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| Message | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:29 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| ImportRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:82 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| Source | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:133 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| ImportReceipt | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:204 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| EvidenceInput | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:231 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| EvidenceSpan | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:255 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| EventTime | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:289 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| MemoryDraft | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:435 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| ProposeRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:527 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| ChangeRecord | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:615 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| ApproveRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:655 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| RejectRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:678 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| RejectReceipt | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:692 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| MemoryRevision | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:709 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| CommitReceipt | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:792 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| ItemView | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:834 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| RecallRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:856 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| RecallHit | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:891 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| RecallResult | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:922 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| FeedbackRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:964 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| FeedbackReceipt | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1004 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| Error | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1026 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| ShownRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1101 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| ShownReceipt | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1125 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| VersionRef | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1143 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| Snapshot | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1187 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| ProvenanceRole | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1232 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| EvidenceLocator | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1287 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| BoundaryPayload | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1362 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| EpisodePayload | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1412 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| LinkPayload | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1463 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| GistPayload | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1501 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| InterpretationPayload | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1557 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| CognitiveSchemaPayload | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1609 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| IntentionCandidatePayload | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1782 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| CognitiveRolePayload | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1842 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| DerivationRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:1874 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| ArtifactView | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2102 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| Receipt | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2218 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| GateRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2256 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| GateDecision | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2365 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| ConfirmationRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2446 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| ConfirmationReceipt | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2485 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| ApplyRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2531 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| AdoptRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2560 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| GrantRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2582 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| RevokeRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2691 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| RecallV3Request | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2705 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| RecallV3Hit | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2749 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| RecallV3Result | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2827 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| PresentationRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2873 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| FeedbackV3Request | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2930 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| ObservationRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:2971 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| IntentionCreateRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3026 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| IntentionView | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3059 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| IntentionTransitionRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3129 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| ActionPrepareRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3168 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| ActionView | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3303 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| ApplicationRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3371 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| ModelPrepareRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3466 | E12：履歴補完のみ、学習版なし; W37 |
| ErasureRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3512 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| Job | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3552 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| IdentifiedReceipt | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3605 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| Grade | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3635 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| DeploymentRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3686 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| DeploymentView | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3749 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| SuspendRequest | True | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3811 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| SchemaRole | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3830 | E5：該当型・点検なし; W43 |
| EvidenceGroup | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3839 | E5：該当型・点検なし; W43 |
| PredictionProtocol | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3875 | E5/E12：該当エンジンなし; W41/W43-06 |
| PredictionRequest | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:3946 | E5/E12：該当エンジンなし; W41/W43-06 |
| PredictionRecord | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4080 | E5/E12：該当エンジンなし; W41/W43-06 |
| PredictionView | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4144 | E5/E12：該当エンジンなし; W41/W43-06 |
| OutcomeRequest | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4215 | E5/E12：該当エンジンなし; W41/W43-06 |
| OutcomeRecord | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4382 | E5/E12：該当エンジンなし; W41/W43-06 |
| OutcomeList | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4443 | E5/E12：該当エンジンなし; W41/W43-06 |
| EvaluationRequest | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4465 | E5/E12：該当エンジンなし; W41/W43-06 |
| PredictionEvaluation | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4502 | E5/E12：該当エンジンなし; W41/W43-06 |
| QualityFinding | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4628 | E5：該当型・点検なし; W43 |
| QualityAssessmentRequest | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4674 | E5：該当型・点検なし; W43 |
| QualityAssessmentRecord | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4740 | E5：該当型・点検なし; W43 |
| FeatureControlRequest | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4785 | E0/E12：機能制御・全由来なし; W42/W37-02 |
| FeatureControlView | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4864 | E0/E12：機能制御・全由来なし; W42/W37-02 |
| LearningManifest | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:4926 | E0/E12：機能制御・全由来なし; W42/W37-02 |
| CalibrationReport | False | C:/Users/keima/AppData/Local/Temp/4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4/contracts/memory.schema.json:5010 | E5/E12：該当エンジンなし; W41/W43-06 |

### B. v3 API 38操作

HTTP案は全行未実装（現行37ルートに/v3宣言なし）。類似する処理を同じAPIと認定しない。request/responseは仕様型で、現行Pydantic DTOは付録D。

| operation | HTTP案 | request → response | 仕様根拠:行 | 現行との差／後続 |
|---|---|---|---|---|
| importSource | POST /v3/vaults/{vault_id}/sources/import | ImportRequest → ImportReceipt | contracts/api-inventory.json:5 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| getSource | GET /v3/vaults/{vault_id}/sources/{source_id} |  → Source | contracts/api-inventory.json:14 | E2：画像/OCR部分のみ、汎用Source/役割未接続; W31-01/02/08 |
| proposeChange | POST /v3/vaults/{vault_id}/changes/propose | ProposeRequest → ChangeRecord | contracts/api-inventory.json:23 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| approveChange | POST /v3/vaults/{vault_id}/changes/{change_id}/approve | ApproveRequest → CommitReceipt | contracts/api-inventory.json:32 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| rejectChange | POST /v3/vaults/{vault_id}/changes/{change_id}/reject | RejectRequest → RejectReceipt | contracts/api-inventory.json:41 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| getItem | GET /v3/vaults/{vault_id}/items/{item_id} |  → ItemView | contracts/api-inventory.json:50 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| recordDerivation | POST /v3/vaults/{vault_id}/derivations | DerivationRequest → ArtifactView | contracts/api-inventory.json:59 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| getDerivation | GET /v3/vaults/{vault_id}/derivations/{artifact_id} |  → ArtifactView | contracts/api-inventory.json:68 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| evaluateUse | POST /v3/vaults/{vault_id}/use-decisions | GateRequest → GateDecision | contracts/api-inventory.json:77 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| recordConfirmation | POST /v3/vaults/{vault_id}/confirmations | ConfirmationRequest → ConfirmationReceipt | contracts/api-inventory.json:86 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| adoptDerivation | POST /v3/vaults/{vault_id}/derivations/{artifact_id}/adopt | AdoptRequest → Receipt | contracts/api-inventory.json:95 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| createGrant | POST /v3/vaults/{vault_id}/policy/grants | GrantRequest → IdentifiedReceipt | contracts/api-inventory.json:104 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| revokeGrant | POST /v3/vaults/{vault_id}/policy/grants/{grant_id}/revoke | RevokeRequest → Receipt | contracts/api-inventory.json:113 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| recall | POST /v3/vaults/{vault_id}/recall | RecallV3Request → RecallV3Result | contracts/api-inventory.json:122 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| recordPresentation | POST /v3/vaults/{vault_id}/presentations | PresentationRequest → IdentifiedReceipt | contracts/api-inventory.json:131 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| recordFeedback | POST /v3/vaults/{vault_id}/feedback | FeedbackV3Request → Receipt | contracts/api-inventory.json:140 | E6/E7：検索・表示のみ、用途/版契約未接続; W34/W35/W37-01 |
| recordObservation | POST /v3/vaults/{vault_id}/observations | ObservationRequest → IdentifiedReceipt | contracts/api-inventory.json:149 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| activateIntention | POST /v3/vaults/{vault_id}/intentions | IntentionCreateRequest → IntentionView | contracts/api-inventory.json:158 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| transitionIntention | POST /v3/vaults/{vault_id}/intentions/{intention_id}/transition | IntentionTransitionRequest → IntentionView | contracts/api-inventory.json:167 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| prepareAction | POST /v3/vaults/{vault_id}/actions/prepare | ActionPrepareRequest → ActionView | contracts/api-inventory.json:176 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| executeAction | POST /v3/vaults/{vault_id}/actions/{action_id}/execute | ApplyRequest → Job | contracts/api-inventory.json:185 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| getAction | GET /v3/vaults/{vault_id}/actions/{action_id} |  → ActionView | contracts/api-inventory.json:194 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| recordSchemaApplication | POST /v3/vaults/{vault_id}/schema-applications | ApplicationRequest → IdentifiedReceipt | contracts/api-inventory.json:203 | E5/E10：抽出部分のみ、派生/Schema未接続; W32 |
| prepareModel | POST /v3/vaults/{vault_id}/models/candidates | ModelPrepareRequest → Job | contracts/api-inventory.json:212 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| activateModel | POST /v3/vaults/{vault_id}/models/{model_id}/activate | AdoptRequest → Receipt | contracts/api-inventory.json:221 | E2/E3：汎用Ledger/Revision/receipt未接続; W30-06/W31 |
| erase | POST /v3/vaults/{vault_id}/erasures | ErasureRequest → Job | contracts/api-inventory.json:230 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| getJob | GET /v3/vaults/{vault_id}/jobs/{job_id} |  → Job | contracts/api-inventory.json:239 | E4/E8：Task・DB予定のみ、outbox未接続; W36 |
| promoteDeployment | POST /v3/vaults/{vault_id}/deployments | DeploymentRequest → DeploymentView | contracts/api-inventory.json:248 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| suspendDeployment | POST /v3/vaults/{vault_id}/deployments/{deployment_id}/suspend | SuspendRequest → DeploymentView | contracts/api-inventory.json:257 | E1：認証のみ、4権限/Plan未接続; W30-04/W33 |
| recordPrediction | POST /v3/vaults/{vault_id}/predictions | PredictionRequest → PredictionView | contracts/api-inventory.json:266 | E5/E12：該当エンジンなし; W41/W43-06 |
| getPrediction | GET /v3/vaults/{vault_id}/predictions/{prediction_id} |  → PredictionView | contracts/api-inventory.json:274 | E5/E12：該当エンジンなし; W41/W43-06 |
| recordOutcome | POST /v3/vaults/{vault_id}/predictions/{prediction_id}/outcomes | OutcomeRequest → OutcomeRecord | contracts/api-inventory.json:282 | E5/E12：該当エンジンなし; W41/W43-06 |
| listOutcomes | GET /v3/vaults/{vault_id}/predictions/{prediction_id}/outcomes |  → OutcomeList | contracts/api-inventory.json:290 | E5/E12：該当エンジンなし; W41/W43-06 |
| evaluatePrediction | POST /v3/vaults/{vault_id}/predictions/{prediction_id}/evaluations | EvaluationRequest → PredictionEvaluation | contracts/api-inventory.json:298 | E5/E12：該当エンジンなし; W41/W43-06 |
| recordAssessment | POST /v3/vaults/{vault_id}/assessments | QualityAssessmentRequest → QualityAssessmentRecord | contracts/api-inventory.json:306 | E5：該当型・点検なし; W43 |
| getAssessment | GET /v3/vaults/{vault_id}/assessments/{assessment_id} |  → QualityAssessmentRecord | contracts/api-inventory.json:314 | E5：該当型・点検なし; W43 |
| changeFeatureControl | POST /v3/vaults/{vault_id}/features/{feature_id}/control | FeatureControlRequest → FeatureControlView | contracts/api-inventory.json:322 | E0/E12：機能制御・全由来なし; W42/W37-02 |
| getFeatureControl | GET /v3/vaults/{vault_id}/features/{feature_id}/control |  → FeatureControlView | contracts/api-inventory.json:330 | E0/E12：機能制御・全由来なし; W42/W37-02 |

### C. 内部操作46クラスと25機能

各操作の4権限・feature選択を現行/apiへ接続したRegistry/Gateは未実装。下表は仕様要求であり現アプリの許可ではない。featureから近接コード/後続へ引く。判断者は本人＋権限担当（W30-05/W33-01）。

| 操作クラス | feature | 必要権限 | gate規則 | 仕様根拠:行 |
|---|---|---|---|---|
| source_import | source | structure | auto | contracts/operation-registry.json:2 |
| capture_start | selected_media | action | confirm_or_delegate | contracts/operation-registry.json:17 |
| capture_stop | selected_media | action | auto | contracts/operation-registry.json:32 |
| transcribe_local | selected_media | structure | auto | contracts/operation-registry.json:47 |
| transcribe_remote | selected_media | structure, action | confirm_or_delegate | contracts/operation-registry.json:61 |
| boundary_generate | episode_structure | structure | auto | contracts/operation-registry.json:77 |
| episode_group | episode_structure | structure | auto | contracts/operation-registry.json:92 |
| embedding_local | recall | structure | auto | contracts/operation-registry.json:107 |
| embedding_remote | recall | structure, action | confirm_or_delegate | contracts/operation-registry.json:121 |
| topic_generate | semantic_network | structure | auto | contracts/operation-registry.json:137 |
| semantic_link_generate | semantic_network | structure | auto | contracts/operation-registry.json:152 |
| entity_merge | semantic_network | structure, epistemic | confirm | contracts/operation-registry.json:167 |
| gist_generate | gist | structure | auto | contracts/operation-registry.json:182 |
| interpretation_generate | schema | structure, epistemic | auto | contracts/operation-registry.json:197 |
| schema_generate | schema | structure, epistemic | auto | contracts/operation-registry.json:213 |
| recall_internal | recall | structure | auto | contracts/operation-registry.json:229 |
| workspace_build | recall | structure | auto | contracts/operation-registry.json:245 |
| present_reflection | life_support | attention | auto | contracts/operation-registry.json:260 |
| present_exact | life_support | attention | auto | contracts/operation-registry.json:275 |
| profile_adopt | ledger | epistemic | confirm | contracts/operation-registry.json:290 |
| high_impact_advice | authority | epistemic, attention | confirm | contracts/operation-registry.json:304 |
| intention_generate | intentions | structure | auto | contracts/operation-registry.json:319 |
| intention_activate | intentions | epistemic, action | confirm_or_delegate | contracts/operation-registry.json:334 |
| notification_schedule | life_support | attention, action | confirm_or_delegate | contracts/operation-registry.json:350 |
| calendar_create | life_support | action | confirm_or_delegate | contracts/operation-registry.json:366 |
| calendar_delete | life_support | action | confirm | contracts/operation-registry.json:381 |
| external_ai_send | authority | action | confirm_or_delegate | contracts/operation-registry.json:395 |
| message_send | life_support | attention, action | confirm | contracts/operation-registry.json:410 |
| memory_erase | device_storage | action | confirm | contracts/operation-registry.json:425 |
| feedback_record | feedback | attention | auto | contracts/operation-registry.json:439 |
| learn_candidate | personal_ranker | structure, attention | auto | contracts/operation-registry.json:453 |
| model_activate | personal_ranker | structure, attention | confirm | contracts/operation-registry.json:468 |
| projection_rebuild | dependency_network | structure | auto | contracts/operation-registry.json:483 |
| policy_grant | authority | action | confirm | contracts/operation-registry.json:497 |
| policy_revoke | authority | action | auto | contracts/operation-registry.json:511 |
| deployment_promote | authority | structure, attention | confirm | contracts/operation-registry.json:525 |
| deployment_suspend | authority | structure | auto | contracts/operation-registry.json:540 |
| prediction_record | prediction_loop | structure, epistemic | auto | contracts/operation-registry.json:555 |
| prediction_evaluate | prediction_loop | structure, epistemic | auto | contracts/operation-registry.json:572 |
| prediction_audit_read | prediction_loop | structure | auto | contracts/operation-registry.json:588 |
| outcome_record | feedback | structure | auto | contracts/operation-registry.json:603 |
| quality_assess | quality_checks | structure, epistemic | auto | contracts/operation-registry.json:619 |
| counterevidence_search | quality_checks | structure | auto | contracts/operation-registry.json:636 |
| feature_enable | authority | action | confirm | contracts/operation-registry.json:652 |
| feature_disable | authority | action | auto | contracts/operation-registry.json:666 |
| feature_control_read | authority | structure | auto | contracts/operation-registry.json:681 |

| feature | 分類 | 仕様既定control / stage | 現行対応・不足／後続（配備は全行未計測） |
|---|---|---|---|
| source | core | enabled / internal | E2 部分あり：画像/OCR受領を保持、汎用Source/同意/位置が不足。W31-01/02 |
| ledger | core | enabled / internal | E3 未接続：accepted更新はLedgerではない。W31-03〜09 |
| authority | core | enabled / internal | E1 部分あり：Cookie/CSRFを保持、4権限は不足。W30-04/W33 |
| episode_structure | core | enabled / internal | E5 未接続：階層helperはEpisodeではない。W32-02〜04 |
| semantic_network | core | enabled / internal | E5 部分あり：Person/Topic/Relationモデル、推論はstub。W32-09 |
| dependency_network | core | enabled / internal | E2/E3 未接続：版付きDAG/barrierなし。W31-07 |
| gist | core | enabled / internal | E5 未接続：summary文字列をGist契約と認定しない。W32-05/06 |
| schema | core | enabled / internal | E5 未接続：CognitiveSchemaなし。W32-07/08/W43-01/02 |
| recall | core | enabled / internal | E6 部分あり：固定検索を保持、snapshot/Gateが不足。W34 |
| quality_checks | core | enabled / internal | E5 未接続：advisory-only assessmentなし。W43-03〜05 |
| feedback | core | enabled / internal | E6 部分あり：検索ログは明示評価ではない。W34-11/W35-09/W37-01 |
| intentions | core | enabled / internal | E4 部分あり：Taskを保持、Cue/Observation/単一運用正本不足。W36-01〜07 |
| life_support | core | enabled / internal | E7/E8 部分あり：人物/予定UI・DBを保持、実行/取消不足。W36-08〜10 |
| device_storage | core | enabled / internal | E9 部分あり：下書きを保持、端末正本/暗号/復旧不足。W38 |
| selected_media | core | enabled / internal | E2/E10 部分あり：ローカルOCRを保持、音声/媒体契約不足。W39 |
| prediction_loop | experimental | disabled / shadow | E5/E12 未接続：予測・封印・結果・評価なし。W41 |
| association_learning | experimental | disabled / shadow | E6/E12 未接続：固定検索/履歴補完はEdge学習ではない。W37-03/04 |
| personal_ranker | experimental | disabled / shadow | E6 未接続：固定重みは個人rankerではない。W37-08〜11 |
| adaptive_attention | experimental | disabled / shadow | E8 未接続：DB reminderは提示時機学習ではない。将来判断、W37/W42で境界保持 |
| scoped_social_models | experimental | disabled / shadow | E5 未接続：人物モデル推論なし。将来判断、W32-07/W43-01で境界保持 |
| capability_calibration | evaluation_only | disabled / shadow | E11 未接続：一般単体試験は能力較正ではない。W43-06 |
| exposure_balance_study | evaluation_only | disabled / shadow | E6 未接続：用途別多様性評価なし。W40-09 |
| cognitive_role_study | evaluation_only | disabled / shadow | E11 未接続：研究計画・実測なし。将来本人判断 |
| developmental_analogy | evaluation_only | disabled / shadow | E5 実行モジュールなし：着想のみ、実装対象化しない |
| continuous_capture_study | evaluation_only | disabled / shadow | E10 未接続：連続録音研究なし。将来本人判断、W39で選択媒体境界保持 |

### D. 現行37 API・DTO宣言

現行URLはmain.pyの/api prefixと各APIRouter prefixを合成した静的値。サーバーへのHTTPアクセスはしていない。

| method | path | 根拠:行 |
|---|---|---|
| GET | /api/health | backend/app/main.py:76 |
| GET | /api/tasks | backend/app/api/task.py:12 |
| POST | /api/tasks | backend/app/api/task.py:32 |
| PATCH | /api/tasks/{task_id} | backend/app/api/task.py:43 |
| POST | /api/tasks/{task_id}/complete | backend/app/api/task.py:50 |
| POST | /api/tasks/{task_id}/reopen | backend/app/api/task.py:56 |
| POST | /api/tasks/{task_id}/accept | backend/app/api/task.py:62 |
| POST | /api/tasks/{task_id}/dismiss | backend/app/api/task.py:68 |
| GET | /api/search | backend/app/api/search.py:9 |
| POST | /api/reminders | backend/app/api/reminder.py:11 |
| GET | /api/persons | backend/app/api/reference.py:27 |
| POST | /api/persons | backend/app/api/reference.py:34 |
| PATCH | /api/persons/{person_id} | backend/app/api/reference.py:45 |
| DELETE | /api/persons/{person_id} | backend/app/api/reference.py:55 |
| GET | /api/persons/interaction-counts | backend/app/api/reference.py:62 |
| GET | /api/persons/{person_id}/interactions | backend/app/api/reference.py:68 |
| GET | /api/persons/{person_id}/dashboard | backend/app/api/reference.py:74 |
| GET | /api/communities | backend/app/api/reference.py:80 |
| POST | /api/communities | backend/app/api/reference.py:90 |
| PATCH | /api/communities/{community_id} | backend/app/api/reference.py:101 |
| DELETE | /api/communities/{community_id} | backend/app/api/reference.py:111 |
| GET | /api/topics | backend/app/api/reference.py:118 |
| POST | /api/topics | backend/app/api/reference.py:125 |
| POST | /api/memory/screenshots | backend/app/api/memory.py:15 |
| GET | /api/memory/entries | backend/app/api/memory.py:25 |
| GET | /api/memory/entities | backend/app/api/memory.py:30 |
| POST | /api/memory/proposals/{proposal_id}/accept | backend/app/api/memory.py:35 |
| GET | /api/interactions | backend/app/api/interaction.py:18 |
| GET | /api/interactions/overview | backend/app/api/interaction.py:46 |
| POST | /api/interactions | backend/app/api/interaction.py:58 |
| GET | /api/calendar-events | backend/app/api/calendar.py:10 |
| POST | /api/calendar-events | backend/app/api/calendar.py:16 |
| POST | /api/auth/register | backend/app/api/auth.py:62 |
| POST | /api/auth/login | backend/app/api/auth.py:77 |
| POST | /api/auth/logout | backend/app/api/auth.py:96 |
| POST | /api/auth/logout-all | backend/app/api/auth.py:104 |
| GET | /api/auth/me | backend/app/api/auth.py:118 |

| 現行DTO/型 | 根拠:行 | v3との関係 |
|---|---|---|
| IdResponse | backend/app/schemas/common.py:4 | 従来/apiの型。v3への暗黙互換なし |
| StatusResponse | backend/app/schemas/common.py:8 | 従来/apiの型。v3への暗黙互換なし |
| EventParticipantRequest | backend/app/schemas/calendar.py:6 | 従来/apiの型。v3への暗黙互換なし |
| CalendarEventCreateRequest | backend/app/schemas/calendar.py:15 | 従来/apiの型。v3への暗黙互換なし |
| AuthRequest | backend/app/schemas/auth.py:4 | 従来/apiの型。v3への暗黙互換なし |
| AuthAccountResponse | backend/app/schemas/auth.py:9 | 従来/apiの型。v3への暗黙互換なし |
| InteractionCreateRequest | backend/app/schemas/interaction.py:6 | 従来/apiの型。v3への暗黙互換なし |
| InteractionRecordedResponse | backend/app/schemas/interaction.py:17 | 従来/apiの型。v3への暗黙互換なし |
| ScreenshotMemoryCreateRequest | backend/app/schemas/memory.py:7 | 従来/apiの型。v3への暗黙互換なし |
| MemoryProposalResponse | backend/app/schemas/memory.py:14 | 従来/apiの型。v3への暗黙互換なし |
| MemoryEntryResponse | backend/app/schemas/memory.py:24 | 従来/apiの型。v3への暗黙互換なし |
| MemoryProposalAcceptResponse | backend/app/schemas/memory.py:40 | 従来/apiの型。v3への暗黙互換なし |
| MemoryEntityResponse | backend/app/schemas/memory.py:47 | 従来/apiの型。v3への暗黙互換なし |
| TaskCreateRequest | backend/app/schemas/task.py:4 | 従来/apiの型。v3への暗黙互換なし |
| TaskUpdateRequest | backend/app/schemas/task.py:11 | 従来/apiの型。v3への暗黙互換なし |
| ReminderCreateRequest | backend/app/schemas/reminder.py:4 | 従来/apiの型。v3への暗黙互換なし |
| PersonCreateRequest | backend/app/schemas/reference.py:4 | 従来/apiの型。v3への暗黙互換なし |
| CommunityCreateRequest | backend/app/schemas/reference.py:10 | 従来/apiの型。v3への暗黙互換なし |
| TopicCreateRequest | backend/app/schemas/reference.py:16 | 従来/apiの型。v3への暗黙互換なし |
| VisibilityUpdateRequest | backend/app/schemas/reference.py:22 | 従来/apiの型。v3への暗黙互換なし |
| PersonResponse | backend/app/schemas/reference.py:26 | 従来/apiの型。v3への暗黙互換なし |
| CommunityResponse | backend/app/schemas/reference.py:34 | 従来/apiの型。v3への暗黙互換なし |
| TopicResponse | backend/app/schemas/reference.py:42 | 従来/apiの型。v3への暗黙互換なし |
| Person | frontend/src/pages/interactionNew/types.ts:1 | 従来/apiの型。v3への暗黙互換なし |
| Community | frontend/src/pages/interactionNew/types.ts:9 | 従来/apiの型。v3への暗黙互換なし |
| CommunityTreeNode | frontend/src/pages/interactionNew/types.ts:17 | 従来/apiの型。v3への暗黙互換なし |
| Topic | frontend/src/pages/interactionNew/types.ts:21 | 従来/apiの型。v3への暗黙互換なし |
| TopicTreeNode | frontend/src/pages/interactionNew/types.ts:28 | 従来/apiの型。v3への暗黙互換なし |
| PersonBubble | frontend/src/pages/interactionNew/types.ts:32 | 従来/apiの型。v3への暗黙互換なし |
| HomeViewProps | frontend/src/pages/interactionNew/types.ts:41 | 従来/apiの型。v3への暗黙互換なし |
| InteractionType | frontend/src/pages/interactionNew/types.ts:50 | 従来/apiの型。v3への暗黙互換なし |
| ShareLevel | frontend/src/pages/interactionNew/types.ts:57 | 従来/apiの型。v3への暗黙互換なし |
| PageId | frontend/src/pages/interactionNew/types.ts:58 | 従来/apiの型。v3への暗黙互換なし |
| PersonPanelId | frontend/src/pages/interactionNew/types.ts:59 | 従来/apiの型。v3への暗黙互換なし |
| ManagePanelId | frontend/src/pages/interactionNew/types.ts:60 | 従来/apiの型。v3への暗黙互換なし |
| SearchTargetType | frontend/src/pages/interactionNew/types.ts:61 | 従来/apiの型。v3への暗黙互換なし |
| AuthAccount | frontend/src/pages/interactionNew/types.ts:69 | 従来/apiの型。v3への暗黙互換なし |
| HistoryFilters | frontend/src/pages/interactionNew/types.ts:75 | 従来/apiの型。v3への暗黙互換なし |
| CreateInteractionPayload | frontend/src/pages/interactionNew/types.ts:87 | 従来/apiの型。v3への暗黙互換なし |
| CreatePersonPayload | frontend/src/pages/interactionNew/types.ts:98 | 従来/apiの型。v3への暗黙互換なし |
| CreateCommunityPayload | frontend/src/pages/interactionNew/types.ts:104 | 従来/apiの型。v3への暗黙互換なし |
| CreateTopicPayload | frontend/src/pages/interactionNew/types.ts:110 | 従来/apiの型。v3への暗黙互換なし |
| CreateTaskPayload | frontend/src/pages/interactionNew/types.ts:116 | 従来/apiの型。v3への暗黙互換なし |
| UpdateTaskPayload | frontend/src/pages/interactionNew/types.ts:123 | 従来/apiの型。v3への暗黙互換なし |
| SearchOptions | frontend/src/pages/interactionNew/types.ts:127 | 従来/apiの型。v3への暗黙互換なし |
| InteractionRecord | frontend/src/pages/interactionNew/types.ts:134 | 従来/apiの型。v3への暗黙互換なし |
| InteractionPage | frontend/src/pages/interactionNew/types.ts:154 | 従来/apiの型。v3への暗黙互換なし |
| PersonInteractionCount | frontend/src/pages/interactionNew/types.ts:161 | 従来/apiの型。v3への暗黙互換なし |
| InteractionOverview | frontend/src/pages/interactionNew/types.ts:166 | 従来/apiの型。v3への暗黙互換なし |
| SummaryItem | frontend/src/pages/interactionNew/types.ts:172 | 従来/apiの型。v3への暗黙互換なし |
| ShareSummary | frontend/src/pages/interactionNew/types.ts:181 | 従来/apiの型。v3への暗黙互換なし |
| PrepTopic | frontend/src/pages/interactionNew/types.ts:187 | 従来/apiの型。v3への暗黙互換なし |
| PrepNote | frontend/src/pages/interactionNew/types.ts:193 | 従来/apiの型。v3への暗黙互換なし |
| PersonDashboard | frontend/src/pages/interactionNew/types.ts:201 | 従来/apiの型。v3への暗黙互換なし |
| SearchResultItem | frontend/src/pages/interactionNew/types.ts:222 | 従来/apiの型。v3への暗黙互換なし |
| TaskLinkRecord | frontend/src/pages/interactionNew/types.ts:254 | 従来/apiの型。v3への暗黙互換なし |
| TaskRecord | frontend/src/pages/interactionNew/types.ts:262 | 従来/apiの型。v3への暗黙互換なし |
| MemoryProposal | frontend/src/pages/interactionNew/types.ts:279 | 従来/apiの型。v3への暗黙互換なし |
| MemoryEntry | frontend/src/pages/interactionNew/types.ts:305 | 従来/apiの型。v3への暗黙互換なし |
| MemoryProposalAcceptResult | frontend/src/pages/interactionNew/types.ts:321 | 従来/apiの型。v3への暗黙互換なし |
| MemoryEntity | frontend/src/pages/interactionNew/types.ts:328 | 従来/apiの型。v3への暗黙互換なし |
| SearchResponse | frontend/src/pages/interactionNew/types.ts:339 | 従来/apiの型。v3への暗黙互換なし |
| SearchAnswerPerson | frontend/src/pages/interactionNew/types.ts:354 | 従来/apiの型。v3への暗黙互換なし |
| SearchAnswerPrimaryPerson | frontend/src/pages/interactionNew/types.ts:362 | 従来/apiの型。v3への暗黙互換なし |
| SearchAnswer | frontend/src/pages/interactionNew/types.ts:369 | 従来/apiの型。v3への暗黙互換なし |

### E. 旧107 IDと新23 IDの個別照合

全行の仕様根拠はSPEC_ROOT/codex/tasks/ID.md:1とcatalog（同ID）。検証状況はW30-01以外すべて実行未実施。部分ありの試験入口を示すが、それは当該Wタスク全体の合格証拠ではない。未接続は旧実装の全面作り直し指示ではなく、表題の未充足責務だけを将来確認する割当。

| ID | 世代／分類 | 現行タイトル | 実装確認／差分だけ進める部分 | 根拠・試験入口（未実行） |
|---|---|---|---|---|
| W30-01 | 旧107 / core | 現在のDTO・状態・用語・実コードを棚卸しする | 今回完了：棚卸しと28静的照合のみ | E0/E1; 契約・独立状態軸の実repo固定記録なし; W30-01-inspect.ps1（本棚卸しのみ） |
| W30-02 | 旧107 / core | 採否・ライフサイクル・配備・認可・機能分類の独立軸を固定する | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E0/E1; 契約・独立状態軸の実repo固定記録なし; W30-01-inspect.ps1（本棚卸しのみ） |
| W30-03 | 旧107 / core | shadowとprovisionalの利用条件を固定する | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E0/E1; 契約・独立状態軸の実repo固定記録なし; W30-01-inspect.ps1（本棚卸しのみ） |
| W30-04 | 旧107 / core | 4権限と信頼済みcallerの境界を型にする | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E0/E1; 契約・独立状態軸の実repo固定記録なし; W30-01-inspect.ps1（本棚卸しのみ） |
| W30-05 | 旧107 / core | 全operationとfeatureをAuthority Matrixへ写像する | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E0/E1; 契約・独立状態軸の実repo固定記録なし; W30-01-inspect.ps1（本棚卸しのみ） |
| W30-06 | 旧107 / core | 契約versionと互換・移行・原文不変を固定する | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E0/E1; 契約・独立状態軸の実repo固定記録なし; W30-01-inspect.ps1（本棚卸しのみ） |
| W30-07 | 旧107 / core | contract test・文書・fixture・図の一致を確認する | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E0/E1; 契約・独立状態軸の実repo固定記録なし; W30-01-inspect.ps1（本棚卸しのみ） |
| W31-01 | 旧107 / core | Source・Message・EvidenceLocatorの型と境界検証 | 部分あり：画像/OCRのDTO・hashを保持。Message/位置/汎用Source型を追加対象へ。v0.4差分のみで完了とする根拠なし | E2/E3; Source/Ledger/Revision/DAG契約未接続; tests/test_memory_screenshot_analyzer.py:19は解析のみ |
| W31-02 | 旧107 / core | Source保存adapterと冪等な取り込み | 部分あり：画像保存・account/hash重複抑制を保持。汎用冪等receipt・許可が不足。v0.4差分のみで完了とする根拠なし | E2/E3; Source/Ledger/Revision/DAG契約未接続; tests/test_memory_screenshot_analyzer.py:19は解析のみ |
| W31-03 | 旧107 / core | MemoryItem・Revisionとcurrent pointer | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E3; Source/Ledger/Revision/DAG契約未接続; tests/test_memory_screenshot_analyzer.py:19は解析のみ |
| W31-04 | 旧107 / core | Commit・parent・headとContent Ledger | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E3; Source/Ledger/Revision/DAG契約未接続; tests/test_memory_screenshot_analyzer.py:19は解析のみ |
| W31-05 | 旧107 / core | proposeからapprove/rejectへの状態遷移 | 部分あり：Task/画像候補acceptを保持。Ledger/owner receipt・却下抑制を接続。v0.4差分のみで完了とする根拠なし | E2/E3; Source/Ledger/Revision/DAG契約未接続; tests/test_memory_screenshot_analyzer.py:19は解析のみ |
| W31-06 | 旧107 / core | 本人訂正を新Revisionとして保存する | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E3; Source/Ledger/Revision/DAG契約未接続; tests/test_memory_screenshot_analyzer.py:19は解析のみ |
| W31-07 | 旧107 / core | Dependency DAGと推移的stale/barrier | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E3; Source/Ledger/Revision/DAG契約未接続; tests/test_memory_screenshot_analyzer.py:19は解析のみ |
| W31-08 | 旧107 / core | speaker・subject・claimant・relayのProvenance | 部分あり：person/evidence/source_idを保持。話者/対象/主張者/伝達者を別契約へ。v0.4差分のみで完了とする根拠なし | E2/E3; Source/Ledger/Revision/DAG契約未接続; tests/test_memory_screenshot_analyzer.py:19は解析のみ |
| W31-09 | 旧107 / core | transaction・HEAD競合・再送の結合試験 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E3; Source/Ledger/Revision/DAG契約未接続; tests/test_memory_screenshot_analyzer.py:19は解析のみ |
| W32-01 | 旧107 / core | AI-derived objectの生成元・版・根拠の共通契約 | 部分あり：OCR analysis_model/evidenceを保持。生成版/入力版/全依存契約が不足。v0.4差分のみで完了とする根拠なし | E5/E10; AIはstub、OCR抽出はEpisode/Gist/Schemaでない; tests/test_interaction_background_processing.py:43はmock呼出 |
| W32-02 | 旧107 / core | Event Boundary候補生成adapter | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E5/E10; AIはstub、OCR抽出はEpisode/Gist/Schemaでない; tests/test_interaction_background_processing.py:43はmock呼出 |
| W32-03 | 旧107 / core | EpisodeContextの作成・分割・統合候補 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E5/E10; AIはstub、OCR抽出はEpisode/Gist/Schemaでない; tests/test_interaction_background_processing.py:43はmock呼出 |
| W32-04 | 旧107 / core | 任意粒度の階層とcontains循環禁止 | 部分あり：既存backend/services/hierarchy_path.py:11とtests/test_hierarchy_path.py:50の循環停止helperを再利用候補。Episode contains契約が不足。v0.4差分のみで完了とする根拠なし | E5/E10; AIはstub、OCR抽出はEpisode/Gist/Schemaでない; tests/test_interaction_background_processing.py:43はmock呼出 |
| W32-05 | 旧107 / core | Gist生成とSource/Detailへの参照 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E5/E10; AIはstub、OCR抽出はEpisode/Gist/Schemaでない; tests/test_interaction_background_processing.py:43はmock呼出 |
| W32-06 | 旧107 / core | Gistの条件・否定・不確実性の検証 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E5/E10; AIはstub、OCR抽出はEpisode/Gist/Schemaでない; tests/test_interaction_background_processing.py:43はmock呼出 |
| W32-07 | 旧107 / core | CognitiveSchema候補生成 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E5/E10; AIはstub、OCR抽出はEpisode/Gist/Schemaでない; tests/test_interaction_background_processing.py:43はmock呼出 |
| W32-08 | 旧107 / core | Schemaの構造対応・支持例・反例・適用範囲 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E5/E10; AIはstub、OCR抽出はEpisode/Gist/Schemaでない; tests/test_interaction_background_processing.py:43はmock呼出 |
| W32-09 | 旧107 / core | 意味Edge・想起Edge・Dependency Edgeの分離検証 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E5/E10; AIはstub、OCR抽出はEpisode/Gist/Schemaでない; tests/test_interaction_background_processing.py:43はmock呼出 |
| W33-01 | 旧107 / core | Operation Registryとfeature対応の実装 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W33-02 | 旧107 / core | UsePlanの主体・対象版・用途・最終payload | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W33-03 | 旧107 / core | 4権限Gate Engineの判定順 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W33-04 | 旧107 / core | 影響・可逆性・不確実性の信頼済み入力 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W33-05 | 旧107 / core | Confirmation on Promotionの要求 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W33-06 | 旧107 / core | ConfirmationReceiptと具体Planへのbinding | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W33-07 | 旧107 / core | 限定Grantのscope・宛先・TTL・予算 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W33-08 | 旧107 / core | Grant撤回と失効 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W33-09 | 旧107 / core | 実行直前の再検査とTOCTOU対策 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W33-10 | 旧107 / core | 外部送信のpermission closureと最小化 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E1/E3/E6; session認証あり、4権限/UsePlan/Gateなし; tests/test_auth.py:1は従来認証 |
| W34-01 | 旧107 / core | Recall共通契約と固定baseline | 部分あり：固定検索重みをbaseline候補として保持。RecallV3型/再現snapshotが不足。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-02 | 旧107 / core | 語句・人物・別名の直接検索 | 部分あり：語句・人物・別名検索を保持。Source/RevisionとACL/Gate接続が不足。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-03 | 旧107 / core | 時間・場所・Goal・Intention検索 | 部分あり：日付・場所検索を保持。Goal/Intention/Cueの契約が不足。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-04 | 旧107 / core | Embedding意味検索adapter | 部分あり：embedding providerを保持。許可境界/入力版/品質比較が不足。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-05 | 旧107 / core | 型付きGraph探索とvisited/予算 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-06 | 旧107 / core | 複数経路の合流・再順位付け | 部分あり：固定重み合流を保持。Graph等の新経路・snapshot統合が不足。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-07 | 旧107 / core | provisionalを候補拡張だけへ使う規則 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-08 | 旧107 / core | ExactとReflectionの分離 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-09 | 旧107 / core | GistからDetail/Sourceへの段階取得 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-10 | 旧107 / core | Active Memory / Workspaceの構築 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W34-11 | 旧107 / core | Presentation Historyと用途限定Exposure設定 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6; v3 snapshot/用途/Gate/依存closure未接続; tests/test_search_expanded.py:43は従来検索 |
| W35-01 | 旧107 / core | Sourceと原文を閲覧する画面 | 部分あり：履歴/スクショOCR表示を保持。汎用Sourceと原文位置への導線不足。v0.4差分のみで完了とする根拠なし | E7; v3原文/Revision/Plan/停止UI未接続; frontend/src/pages/interactionNew/interactionsApi.test.ts:1はHTTP helper |
| W35-02 | 旧107 / core | MemoryItemとRevision履歴 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E7; v3原文/Revision/Plan/停止UI未接続; frontend/src/pages/interactionNew/interactionsApi.test.ts:1はHTTP helper |
| W35-03 | 旧107 / core | Episode・意味関係・Schema表示 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E7; v3原文/Revision/Plan/停止UI未接続; frontend/src/pages/interactionNew/interactionsApi.test.ts:1はHTTP helper |
| W35-04 | 旧107 / core | provisional/採用/失効/停止の状態表示 | 部分あり：候補/accepted/処理失敗表示を保持。lifecycle/配備/機能停止を追加対象へ。v0.4差分のみで完了とする根拠なし | E7; v3原文/Revision/Plan/停止UI未接続; frontend/src/pages/interactionNew/interactionsApi.test.ts:1はHTTP helper |
| W35-05 | 旧107 / core | 役割付きProvenanceと出典確認 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E7; v3原文/Revision/Plan/停止UI未接続; frontend/src/pages/interactionNew/interactionsApi.test.ts:1はHTTP helper |
| W35-06 | 旧107 / core | 訂正と差分のUI | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E7; v3原文/Revision/Plan/停止UI未接続; frontend/src/pages/interactionNew/interactionsApi.test.ts:1はHTTP helper |
| W35-07 | 旧107 / core | 具体PlanへのPromotion確認UI | 部分あり：候補登録ボタンを保持。対象版/用途/最終payload receipt bindingが不足。v0.4差分のみで完了とする根拠なし | E7; v3原文/Revision/Plan/停止UI未接続; frontend/src/pages/interactionNew/interactionsApi.test.ts:1はHTTP helper |
| W35-08 | 旧107 / core | 限定委任と撤回Policyの設定画面 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E7; v3原文/Revision/Plan/停止UI未接続; frontend/src/pages/interactionNew/interactionsApi.test.ts:1はHTTP helper |
| W35-09 | 旧107 / core | あとで・不要・違う・役立ったの低負担Feedback | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E7; v3原文/Revision/Plan/停止UI未接続; frontend/src/pages/interactionNew/interactionsApi.test.ts:1はHTTP helper |
| W36-01 | 旧107 / core | ActiveIntentionの一意な運用モデル | 部分あり：Taskモデルを唯一の運用正本候補として調査。ActiveIntentionとの対応はDRAFT。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W36-02 | 旧107 / core | Action・Cue・Context・Stateの契約 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W36-03 | 旧107 / core | 時間Cueとtimezoneの判定 | 部分あり：日付抽出/timezone検証を保持。時間Cue・元発言時刻の契約不足。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W36-04 | 旧107 / core | 人物・場所・Event・ActivityのCue | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W36-05 | 旧107 / core | 予定と実観測と本人申告を分離 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W36-06 | 旧107 / core | Intentionのactive/completed/cancelled lifecycle | 部分あり：complete/reopenと候補軸を保持。cancelled/再開意思の意味固定が不足。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W36-07 | 旧107 / core | 完了/中止Intentionが要約で復活しない抑制 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W36-08 | 旧107 / core | ActionPlanとoutbox | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W36-09 | 旧107 / core | Gate再検査後の外部実行とunknown結果 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W36-10 | 旧107 / core | Calendar/Reminder adapterと取消 | 部分あり：Calendar/ReminderのDB保存を保持。OS/provider adapter・取消不足。v0.4差分のみで完了とする根拠なし | E4/E8; Task/DB予定あり、Intention/ActionPlan/outbox未接続; tests/test_task_workflow_expanded.py:29、tests/test_calendar_reminder_expanded.py:1 |
| W37-01 | 旧107 / experimental | Presentation・Feedback・Application/Outcomeのイベント | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-02 | 旧107 / experimental | Training Manifestと同意・撤回 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-03 | 旧107 / experimental | 想起Edgeの結合学習を任意adapterにする | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-04 | 旧107 / experimental | AI自身の共検索だけで自己強化しない制約 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-05 | 旧107 / experimental | Schemaの別Episodeへの適用履歴 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-06 | 旧107 / experimental | 実行・有用性・反例・未観測の記録 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-07 | 旧107 / experimental | Schema適用範囲の改訂候補 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-08 | 旧107 / experimental | 固定baselineと個人ranker特徴量 | 部分あり：固定検索重みを保持。個人ranker特徴量/学習契約は未接続。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-09 | 旧107 / experimental | pairwise rankerの候補学習 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-10 | 旧107 / experimental | 時系列Shadow比較 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W37-11 | 旧107 / experimental | 学習版の昇格・Rollback・依存停止 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E6/E12; 組織履歴補完と固定重みだけ、学習manifest/同意/Shadowなし; tests/test_memory_screenshot_analyzer.py:38は補完helper |
| W38-01 | 旧107 / core | PWA保存・起動・offlineの実現性Spike | 部分あり：offline下書き/再送を保持。PWA/iPhone実現性の実測なし。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W38-02 | 旧107 / core | IndexedDB/OPFS等の選定とadapter検証 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W38-03 | 旧107 / core | native bridgeの小さな実証 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W38-04 | 旧107 / core | ローカルDB方式とmigration選定 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W38-05 | 旧107 / core | 暗号化・鍵・索引・一時領域の保護 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W38-06 | 旧107 / core | エクスポートと暗号化Backup | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W38-07 | 旧107 / core | Restoreと機種変更・削除台帳の検証 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W38-08 | 旧107 / core | 容量不足・crash・途中書込みの復旧 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W38-09 | 旧107 / core | OS通知adapterと再予約・取消 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W38-10 | 旧107 / core | iPhone実機の性能・容量・電池測定 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E9; localStorage/サーバーDBのみ、native/端末保護/復旧なし; frontend/src/pages/interactionNew/offlineInteractions.test.ts:1 |
| W39-01 | 旧107 / core | CaptureSession/MediaAsset/保持と媒体契約 | 部分あり：画像byte/hash/mime保存を保持。CaptureSession/保持同意の媒体契約不足。v0.4差分のみで完了とする根拠なし | E2/E10; OCRあり、音声/媒体版/保持停止未接続; tests/test_memory_screenshot_analyzer.py:19（実画像は条件付き） |
| W39-02 | 旧107 / core | 音声取得の許可・明示開始・停止 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E10; OCRあり、音声/媒体版/保持停止未接続; tests/test_memory_screenshot_analyzer.py:19（実画像は条件付き） |
| W39-03 | 旧107 / core | 中断・CaptureGapの記録 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E10; OCRあり、音声/媒体版/保持停止未接続; tests/test_memory_screenshot_analyzer.py:19（実画像は条件付き） |
| W39-04 | 旧107 / core | 音声区間のEvidenceLocator | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E10; OCRあり、音声/媒体版/保持停止未接続; tests/test_memory_screenshot_analyzer.py:19（実画像は条件付き） |
| W39-05 | 旧107 / core | TranscriptRevisionと原音対応 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E10; OCRあり、音声/媒体版/保持停止未接続; tests/test_memory_screenshot_analyzer.py:19（実画像は条件付き） |
| W39-06 | 旧107 / core | 話者ラベルと人物同定の分離 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E10; OCRあり、音声/媒体版/保持停止未接続; tests/test_memory_screenshot_analyzer.py:19（実画像は条件付き） |
| W39-07 | 旧107 / core | 画像入力・EXIF・時刻・位置の出典 | 部分あり：画像入力とcaptured_atを保持。EXIF/時刻/位置の由来区別不足。v0.4差分のみで完了とする根拠なし | E2/E10; OCRあり、音声/媒体版/保持停止未接続; tests/test_memory_screenshot_analyzer.py:19（実画像は条件付き） |
| W39-08 | 旧107 / core | 音声/画像からMemory候補を作るadapter | 部分あり：Windows OCRと予定/Task候補抽出を保持。音声とSource/Ledger/Gate接続不足。v0.4差分のみで完了とする根拠なし | E2/E10; OCRあり、音声/媒体版/保持停止未接続; tests/test_memory_screenshot_analyzer.py:19（実画像は条件付き） |
| W39-09 | 旧107 / core | Media削除・保持期限・派生停止 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E2/E10; OCRあり、音声/媒体版/保持停止未接続; tests/test_memory_screenshot_analyzer.py:19（実画像は条件付き） |
| W40-01 | 旧107 / core | Source→Ledger→訂正のアプリE2E | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-02 | 旧107 / core | Episode/Gist/Schema生成品質 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-03 | 旧107 / core | 主体・伝聞・Provenanceの誤り検証 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-04 | 旧107 / core | Recall@k等の時系列比較 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-05 | 旧107 / core | Schema転用の評価セット | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-06 | 旧107 / core | 4権限/Gateの固定安全テスト | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-07 | 旧107 / core | Prompt Injectionと外部送信境界 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-08 | 旧107 / core | Confirmation負担・誤承認の評価 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-09 | 旧107 / evaluation_only | 提示偏り/Exposureの用途別評価 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-10 | 旧107 / core | iPhone/PWAの実機E2E | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-11 | 旧107 / core | 移行・Rollback・停止復元の検証 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W40-12 | 旧107 / core | 最終仕様・実装・報告・引継ぎの整合 | 未接続/完了証拠なし：表題の責務を後続で確認。v0.4差分のみで完了とする根拠なし | E11; 従来単体/DB試験あり、v3統合/E2E/評価証拠なし; docs/testing/README.md:1 |
| W41-01 | 新23 / experimental | 予測プロトコル・観測可能対象・時点の契約 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5/E12; 予測・独立結果・封印評価なし; 実アプリ試験入口なし |
| W41-02 | 新23 / experimental | Predictionの不変封印・再送・未来文脈拒否 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5/E12; 予測・独立結果・封印評価なし; 実アプリ試験入口なし |
| W41-03 | 新23 / experimental | Outcomeの対応・欠測・条件変更・訂正 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5/E12; 予測・独立結果・封印評価なし; 実アプリ試験入口なし |
| W41-04 | 新23 / experimental | 事前基準の評価と二値スコア・競合 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5/E12; 予測・独立結果・封印評価なし; 実アプリ試験入口なし |
| W41-05 | 新23 / experimental | EvaluationからSchema改訂候補へつなぐ | 未接続/完了証拠なし：表題の責務を後続で確認 | E5/E12; 予測・独立結果・封印評価なし; 実アプリ試験入口なし |
| W41-06 | 新23 / experimental | 時系列再生・未来漏れ・コピー重複の検査 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5/E12; 予測・独立結果・封印評価なし; 実アプリ試験入口なし |
| W41-07 | 新23 / experimental | 予測提示/実行とOutcomeの関係を記録 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5/E12; 予測・独立結果・封印評価なし; 実アプリ試験入口なし |
| W41-08 | 新23 / experimental | 予測拡張を任意adapterとして接続・外す | 未接続/完了証拠なし：表題の責務を後続で確認 | E5/E12; 予測・独立結果・封印評価なし; 実アプリ試験入口なし |
| W41-09 | 新23 / experimental | baseline比較で継続/改善/停止を判断する | 未接続/完了証拠なし：表題の責務を後続で確認 | E5/E12; 予測・独立結果・封印評価なし; 実アプリ試験入口なし |
| W42-01 | 新23 / core | 3分類のfeature registryとコア依存制約 | 未接続/完了証拠なし：表題の責務を後続で確認 | E0/E3/E12; registry/epoch/barrier/停止projectionなし; 実アプリ試験入口なし |
| W42-02 | 新23 / core | FeatureControlの取得・有効化/停止の契約 | 未接続/完了証拠なし：表題の責務を後続で確認 | E0/E3/E12; registry/epoch/barrier/停止projectionなし; 実アプリ試験入口なし |
| W42-03 | 新23 / core | required_featuresの推移計算と依存印継承 | 未接続/完了証拠なし：表題の責務を後続で確認 | E0/E3/E12; registry/epoch/barrier/停止projectionなし; 実アプリ試験入口なし |
| W42-04 | 新23 / core | epochと利用停止barrierを原子的に保存 | 未接続/完了証拠なし：表題の責務を後続で確認 | E0/E3/E12; registry/epoch/barrier/停止projectionなし; 実アプリ試験入口なし |
| W42-05 | 新23 / core | worker/outboxの直前機能再検査 | 未接続/完了証拠なし：表題の責務を後続で確認 | E0/E3/E12; registry/epoch/barrier/停止projectionなし; 実アプリ試験入口なし |
| W42-06 | 新23 / core | 依存Schema/学習版の隔離と固定baseline復帰 | 未接続/完了証拠なし：表題の責務を後続で確認 | E0/E3/E12; registry/epoch/barrier/停止projectionなし; 実アプリ試験入口なし |
| W42-07 | 新23 / core | 未登録/途中停止/再起動/復元のfallback試験 | 未接続/完了証拠なし：表題の責務を後続で確認 | E0/E3/E12; registry/epoch/barrier/停止projectionなし; 実アプリ試験入口なし |
| W42-08 | 新23 / core | 機能状態・監査履歴・再ONの確認UI | 未接続/完了証拠なし：表題の責務を後続で確認 | E0/E3/E12; registry/epoch/barrier/停止projectionなし; 実アプリ試験入口なし |
| W43-01 | 新23 / core | Pattern/Principle/Model/未分類の型と移行 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5; SchemaRole/独立証拠/QualityAssessmentなし; 実アプリ試験入口なし |
| W43-02 | 新23 / core | 独立証拠群・適用範囲・反例・代替仮説の契約 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5; SchemaRole/独立証拠/QualityAssessmentなし; 実アプリ試験入口なし |
| W43-03 | 新23 / core | QualityAssessmentの保存・現在版・出典 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5; SchemaRole/独立証拠/QualityAssessmentなし; 実アプリ試験入口なし |
| W43-04 | 新23 / core | 反例探索と範囲/条件/矛盾点検 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5; SchemaRole/独立証拠/QualityAssessmentなし; 実アプリ試験入口なし |
| W43-05 | 新23 / core | 品質助言とGate認可を分離して接続 | 未接続/完了証拠なし：表題の責務を後続で確認 | E5; SchemaRole/独立証拠/QualityAssessmentなし; 実アプリ試験入口なし |
| W43-06 | 新23 / evaluation_only | AI能力較正を評価系の報告として作る | 未接続/完了証拠なし：表題の責務を後続で確認 | E5; SchemaRole/独立証拠/QualityAssessmentなし; 実アプリ試験入口なし |

## 6. 引継ぎ

EXECUTION_ORDER.mdの1番W30-01をここで完了。次に進める推奨IDは **W30-02**（2番、最小前提W30-01）。W30-02以降には着手していない。D1〜D9と既存portを引き継ぎ、独立状態軸の固定の際にも既存models・未コミット機能を保持する。

