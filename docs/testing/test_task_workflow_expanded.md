# test_task_workflow_expanded.py

## 概要

タスク候補抽出、タスクAPI、検索インデックス連携、候補の承認・却下、期限表現の解析、タイトル正規化を確認するテストです。

## テスト内容

### `test_extract_candidates_creates_task_and_links`

インタラクションからタスク候補を作成し、人物、コミュニティ、トピック、元インタラクションとのリンクが作られることを確認します。

### `test_extract_candidates_skips_existing_active_candidate`

同じインタラクションに対して既存の有効な候補がある場合、重複して候補を作成しないことを確認します。

### `test_extract_candidates_allows_dismissed_candidate_reproposal`

却下済み候補がある場合は、同じインタラクションから新しい候補を再提案できることを確認します。

### `test_list_tasks_filters_candidates_and_status`

タスク一覧APIで候補ステータスや候補を含めるかどうかの条件が正しく適用されることを確認します。

### `test_list_tasks_rejects_limit_outside_supported_range`

タスク一覧の `limit` が1未満または200超の場合、422で拒否されることを確認します。

### `test_create_manual_task_indexes_task_for_search`

手動タスク作成が成功し、通常タスクとして保存され、検索ドキュメントにも登録されることを確認します。

### `test_create_manual_task_rejects_blank_title`

空白のみのタイトルで手動タスクを作成した場合、400で拒否されることを確認します。

### `test_update_task_edits_fields_and_reindexes`

タスク更新でタイトル、説明、期限、優先度が変更され、検索ドキュメントも再インデックスされることを確認します。

### `test_complete_and_reopen_task_update_status`

タスクの完了APIでDONEになり、再オープンAPIでTODOに戻ることを確認します。

### `test_list_tasks_filters_open_status_and_search_text`

タスク一覧APIが未完了のみの絞り込みと検索文字列による絞り込みを同時に適用することを確認します。

### `test_update_task_rejects_invalid_status_and_priority`

不正なステータスや範囲外の優先度でタスク更新した場合、適切なエラーになることを確認します。

### `test_accept_task_candidate_marks_accepted`

タスク候補を承認すると通常タスク扱いになり、候補ステータスがacceptedになることを確認します。

### `test_dismiss_task_candidate_marks_dismissed_and_unindexes`

タスク候補を却下すると候補ステータスがdismissedになり、検索ドキュメントから除外されることを確認します。

### `test_task_candidate_status_endpoints_return_400_or_404`

候補ステータス変更APIで不正UUIDや存在しないIDを指定した場合、400または404になることを確認します。

### `test_extract_task_candidates_handles_iso_due_date`

ISO形式の日付を含む文章からタスク候補を抽出し、期限日が正しく設定されることを確認します。

### `test_extract_task_candidates_handles_today`

「今日」相当の期限表現を含む文章から、基準日当日の期限を持つ候補が抽出されることを確認します。

### `test_extract_task_candidates_handles_tomorrow`

「明日」相当の期限表現を含む文章から、基準日の翌日の期限を持つ候補が抽出されることを確認します。

### `test_extract_task_candidates_handles_next_week`

「来週」相当の期限表現を含む文章から、基準日の1週間後の期限を持つ候補が抽出されることを確認します。

### `test_extract_task_candidates_rolls_past_month_day_to_next_year`

すでに過ぎた月日を期限として解釈する場合、翌年の日付に繰り越されることを確認します。

### `test_extract_task_candidates_limits_to_five_results`

多数の候補文がある場合でも、抽出結果が最大5件に制限されることを確認します。

### `test_normalize_candidate_title_trims_prefix_and_caps_length`

候補タイトルの `TODO:` 接頭辞が除去され、長すぎるタイトルが120文字に丸められることを確認します。

### `test_split_candidate_sentences_handles_newlines_bullets_and_punctuation`

改行、箇条書き、句読点を含む文章がタスク候補抽出用の文に分割されることを確認します。

## 補助処理

### `_interaction_for_task`

タスク候補抽出テストで使う人物、コミュニティ、トピック、インタラクションをまとめて作成します。

### `setUpClass` / `tearDownClass`

共通TestClientを用意し、クラス終了時にタスク系テストデータを削除します。

### `setUp`

テストごとの一意なprefixとDBフィクスチャを作成します。
