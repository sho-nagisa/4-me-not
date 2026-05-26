# test_reference_interaction_expanded.py

## 概要

人物、コミュニティ、トピック、インタラクションAPIについて、入力検証、非表示データの扱い、一覧・集計・削除時の関連データ挙動、アカウント分離を確認するテストです。

## テスト内容

### `test_create_person_rejects_missing_primary_community`

存在しない主コミュニティIDを指定した人物作成が404で拒否されることを確認します。

### `test_create_person_rejects_hidden_primary_community`

非表示コミュニティを主コミュニティに指定した人物作成が404で拒否されることを確認します。

### `test_create_person_duplicate_canonical_name_has_defined_error`

同じ `canonical_name` の人物を重複作成した場合、2回目が409で拒否されることを確認します。

### `test_create_person_rejects_blank_name`

空白のみの人物名で作成した場合、400で拒否されることを確認します。

### `test_create_community_rejects_blank_name`

空白のみのコミュニティ名で作成した場合、400で拒否されることを確認します。

### `test_create_community_allows_same_name_under_different_parent`

同じ名前の子コミュニティでも、親が異なれば作成できることを確認します。

### `test_create_community_rejects_hidden_parent`

非表示コミュニティを親に指定した子コミュニティ作成が404で拒否されることを確認します。

### `test_create_community_rejects_invalid_parent_uuid`

不正なUUID形式の親IDを指定したコミュニティ作成が400で拒否されることを確認します。

### `test_reference_paths_respect_include_hidden`

非表示コミュニティを含めるかどうかで、コミュニティパスと人物の主コミュニティパスの表示が変わることを確認します。

### `test_create_topic_rejects_invalid_parent_uuid`

不正なUUID形式の親IDを指定したトピック作成が400で拒否されることを確認します。

### `test_create_topic_rejects_missing_parent`

存在しない親トピックIDを指定したトピック作成が404で拒否されることを確認します。

### `test_create_topic_builds_parent_child_path`

親トピックを指定して子トピックを作成した場合、レスポンスのパスに親子の名前が含まれることを確認します。

### `test_record_interaction_rejects_invalid_person_uuid`

不正なUUID形式の人物IDを指定したインタラクション記録が400で拒否されることを確認します。

### `test_record_interaction_rejects_missing_person`

存在しない人物IDを指定したインタラクション記録が404で拒否されることを確認します。

### `test_record_interaction_rejects_hidden_person`

非表示の人物を指定したインタラクション記録が404で拒否されることを確認します。

### `test_record_interaction_rejects_invalid_missing_or_hidden_community`

不正、存在しない、または非表示のコミュニティIDを指定したインタラクション記録が適切に拒否されることを確認します。

### `test_record_interaction_rejects_invalid_or_missing_topic`

不正または存在しないトピックIDを指定したインタラクション記録が適切に拒否されることを確認します。

### `test_record_interaction_rejects_unsupported_type_or_share_level`

未対応のインタラクション種別や共有レベルを指定した場合、400で拒否されることを確認します。

### `test_list_interactions_filters_by_date_range`

インタラクション一覧が指定した日時範囲内のデータだけを返すことを確認します。

### `test_list_interactions_orders_by_occurred_at_then_created_at_desc`

インタラクション一覧が発生日、作成日の降順で並ぶことを確認します。

### `test_record_interaction_normalizes_type_aliases`

`CALL`、`CHAT`、`OBSERVATION` などの種別エイリアスが正規の種別に変換されることを確認します。

### `test_person_dashboard_aggregates_share_topics_communities_and_notes`

人物ダッシュボードが件数、共有サマリー、上位トピック、上位コミュニティ、最近のメモを集計することを確認します。

### `test_interaction_overview_excludes_hidden_people_and_applies_limits`

インタラクション概要が非表示人物のデータを除外し、最近の履歴と人物別件数の上限を適用することを確認します。

### `test_delete_person_removes_related_interactions_from_lists`

人物削除後、その人物に紐づくインタラクションが一覧検索に表示されないことを確認します。

### `test_delete_community_preserves_interaction_with_null_community_reference`

コミュニティ削除後もインタラクション自体は残り、コミュニティ参照だけがnullになることを確認します。

### `test_required_api_fields_return_422`

人物、インタラクション、コミュニティ作成APIで必須項目がない場合、422になることを確認します。

### `test_person_interaction_counts_include_zero_primary_community_members`

インタラクションがない人物でも、対象コミュニティの人物別件数に0件として含まれることを確認します。

### `test_services_scope_queries_by_current_account_id`

別アカウントの人物データが、現在アカウントの人物一覧に混ざらないことを確認します。

## 補助処理

### `setUpClass` / `tearDownClass`

共通TestClientを用意し、クラス終了時に参照・インタラクション系テストデータを削除します。

### `setUp`

テストごとの一意なprefixとDBフィクスチャを作成します。
