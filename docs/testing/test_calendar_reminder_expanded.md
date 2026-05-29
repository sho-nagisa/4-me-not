# test_calendar_reminder_expanded.py

## 概要

カレンダーイベントとリマインダーAPIについて、作成、入力検証、一覧順序、検索インデックス連携、重複制御を確認するテストです。

## テスト内容

### `test_create_calendar_event_with_person_and_display_only_participants`

人物ID付き参加者と表示名のみの参加者を含むカレンダーイベントを作成でき、参加者情報がレスポンスに含まれることを確認します。

### `test_create_calendar_event_rejects_end_before_start`

終了日時が開始日時より前のカレンダーイベント作成が400で拒否されることを確認します。

### `test_create_calendar_event_rejects_end_equal_to_start`

終了日時が開始日時と同じゼロ長のカレンダーイベント作成が400で拒否されることを確認します。

### `test_create_calendar_event_rejects_missing_person`

存在しない人物IDを参加者に指定した場合、カレンダーイベント作成が404で拒否されることを確認します。

### `test_create_calendar_event_rejects_invalid_participant_uuid`

参加者の人物IDがUUID形式ではない場合、カレンダーイベント作成が400で拒否されることを確認します。

### `test_create_calendar_event_rejects_hidden_person`

非表示の人物を参加者に指定した場合、カレンダーイベント作成が404で拒否されることを確認します。

### `test_list_calendar_events_orders_by_start_desc_and_limits`

カレンダーイベント一覧が開始日時の降順で返り、取得件数の上限が適用されることを確認します。

### `test_list_calendar_events_rejects_limit_outside_supported_range`

カレンダーイベント一覧の `limit` が1未満または200超の場合、422で拒否されることを確認します。

### `test_create_calendar_event_indexes_event_for_search`

カレンダーイベント作成後に検索ドキュメントが作成され、説明文の検索対象テキストが保存されることを確認します。

### `test_create_calendar_event_duplicate_external_id_has_defined_error`

同じ `external_id` のカレンダーイベントを重複作成した場合、2回目が409で拒否されることを確認します。

### `test_calendar_event_required_fields_return_422`

必須項目なしでカレンダーイベントを作成した場合、422のバリデーションエラーになることを確認します。

### `test_create_reminder_accepts_iso_z_datetime_and_optional_message`

`Z` 付きISO日時と任意メッセージを指定したリマインダー作成が成功し、DBに保存されることを確認します。

### `test_create_reminder_rejects_invalid_remind_at`

不正な日時文字列を指定したリマインダー作成が400で拒否されることを確認します。

### `test_create_reminder_rejects_blank_title`

空白のみのタイトルでリマインダーを作成できないことを確認します。

### `test_create_reminder_required_fields_return_422`

必須項目なしでリマインダーを作成した場合、422のバリデーションエラーになることを確認します。

### `test_search_index_can_delete_missing_calendar_event_document`

削除済みカレンダーイベントを再インデックスしても検索ドキュメントが残らないことを確認します。

## 補助処理

### `setUpClass` / `tearDownClass`

共通TestClientを用意し、クラス終了時にカレンダー系テストデータを削除します。

### `setUp`

テストごとの一意なprefixとDBフィクスチャを作成します。
