# test_search_expanded.py

## 概要

検索機能について、インデックス作成、検索APIの絞り込み、検索ログ、RAG回答、埋め込みフォールバック、スコア計算、キャッシュ無効化を確認するテストです。

## テスト内容

### `test_index_interaction_creates_related_search_documents`

インタラクションのインデックス作成時に、関連する人物、コミュニティ、トピックの検索ドキュメントも作成されることを確認します。

### `test_index_interaction_removes_hidden_or_invisible_documents`

人物を非表示にした後に再インデックスすると、対象インタラクションや人物の検索ドキュメントが削除されることを確認します。

### `test_search_endpoint_filters_single_and_multiple_target_types`

検索APIで単一または複数の対象種別を指定した場合、指定種別だけの結果が返ることを確認します。

### `test_search_endpoint_records_search_log`

検索実行時にクエリ、対象種別、結果件数、上位結果情報が検索ログに保存されることを確認します。

### `test_search_endpoint_filters_results_by_date_range`

検索APIが指定した日付範囲内のインタラクションだけを返すことを確認します。

### `test_search_endpoint_rejects_invalid_date_range`

開始日が終了日より後の日付範囲を指定した場合、400で拒否されることを確認します。

### `test_search_endpoint_returns_fuzzy_matches_for_typo_query`

タイプミスを含む検索語でもファジースコアにより該当インタラクションがヒットすることを確認します。

### `test_search_endpoint_can_disable_fuzzy_score`

`fuzzy=false` を指定した場合、検索結果のファジースコアが0になることを確認します。

### `test_rebuild_account_index_indexes_all_supported_targets`

アカウント全体のインデックス再構築で、人物、コミュニティ、トピック、インタラクション、タスク、カレンダーイベントが対象になることを確認します。
このテストは専用アカウントで実行し、ローカルDB内の既存データ量に影響されないようにします。

### `test_search_service_returns_empty_response_for_blank_query`

空白のみの検索クエリでは結果が空になり、回答の信頼度がnoneになることを確認します。

### `test_index_task_excludes_dismissed_tasks_from_search`

却下済みタスクを再インデックスすると、検索ドキュメントから除外されることを確認します。

### `test_build_rag_answer_aggregates_person_confidence_and_evidence`

RAG回答生成が主要人物、根拠、フォローアップクエリを組み立て、信頼度を高く評価することを確認します。

### `test_embedding_provider_uses_local_fallback_without_api_key`

OpenAI APIキーがない場合、埋め込み生成がローカルハッシュ実装にフォールバックすることを確認します。

### `test_embedding_provider_falls_back_when_openai_request_fails`

OpenAI埋め込み取得が失敗した場合、例外ログを出しつつローカルハッシュ実装にフォールバックすることを確認します。

### `test_search_utils_parse_embedding_handles_invalid_json`

埋め込み文字列のJSONパースで、不正なJSONや不正形式を空配列または数値配列へ安全に変換することを確認します。

### `test_search_utils_scores_keyword_exact_title_and_partial_matches`

キーワードスコアがタイトル完全一致や部分一致を高く評価することを確認します。

### `test_search_utils_scores_fuzzy_typo_matches`

ファジースコアがタイプミスを含む検索語でも高い一致度を返すことを確認します。

### `test_search_utils_extract_snippet_prefers_query_neighborhood`

スニペット抽出が検索語の周辺を優先し、長文では省略記号付きで返すことを確認します。

### `test_search_result_grouping_groups_by_supported_target_types`

検索結果のグルーピングが対応する対象種別ごとの配列に分類されることを確認します。

### `test_search_endpoint_rejects_unknown_target_type`

未知の対象種別を検索APIに指定した場合、400で拒否されることを確認します。

### `test_search_normalize_target_types_deduplicates_and_sorts`

対象種別の正規化で重複が除去され、安定した順序に並ぶことを確認します。

### `test_search_normalize_target_types_raises_for_unknown`

対象種別の正規化で未知の種別が指定された場合、400のHTTPExceptionが発生することを確認します。

### `test_search_cache_is_invalidated_after_person_mutation`

人物作成後に検索ドキュメントキャッシュが無効化されることを確認します。

### `test_search_cache_is_invalidated_after_supported_target_mutations`

コミュニティ、トピック、タスク、カレンダーイベントの変更後に検索ドキュメントキャッシュが無効化されることを確認します。

### `test_search_utils_vector_and_text_helpers`

ベクトル正規化、コサイン類似度、テキスト圧縮、空値選択、検索文字列結合の基本動作を確認します。

### `test_search_utils_recency_prefers_recent_documents`

新しい日時のドキュメントほど高いrecencyスコアになることを確認します。

## 補助処理

### `setUpClass` / `tearDownClass`

共通TestClientを用意し、クラス終了時に検索系テストデータを削除します。

### `setUp`

テストごとの一意なprefixとDBフィクスチャを作成します。
