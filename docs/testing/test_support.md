# test_support.py

## 概要

各テストで使うDBフィクスチャ、テストデータ作成、検索ドキュメント取得、テストデータ削除をまとめた補助モジュールです。

## 補助処理

### `unique_prefix`

テストデータを識別するための一意なprefixを生成します。

### `ensure_default_account`

現在のテストアカウントが存在することを確認し、接続エラー時はリトライします。

### `_ensure_default_account_once`

DBを直接確認し、既定アカウントが存在しなければ作成します。

### `cleanup_test_data`

指定prefixに一致するテストデータを削除し、接続エラー時はリトライします。

### `_cleanup_test_data_once`

人物、コミュニティ、トピック、リマインダー、カレンダーイベント、タスク、検索関連データをDBから削除します。

### `DbFixture.__init__`

フィクスチャ用prefixとアカウントIDを保持し、テストデータ作成の準備をします。

### `DbFixture.create_community`

テスト用コミュニティを作成し、必要に応じて親コミュニティや非表示状態を設定します。

### `DbFixture.create_topic`

テスト用トピックを作成し、必要に応じて親トピックを設定します。

### `DbFixture.create_person`

テスト用人物を作成し、主コミュニティ、非表示状態、canonical nameを設定します。

### `DbFixture.create_interaction`

テスト用インタラクションを作成し、人物、コミュニティ、トピック、内容、共有レベルなどを設定します。

### `DbFixture.create_task`

テスト用タスクを作成し、候補状態、ステータス、期限、リンク情報を設定します。

### `DbFixture.load_task`

指定IDのタスクをリンク情報付きで読み込みます。

### `DbFixture.create_calendar_event`

テスト用カレンダーイベントを作成し、開始終了日時や外部IDを設定します。

### `DbFixture.search_documents`

現在のprefixに一致する検索ドキュメントを取得し、必要に応じて対象種別で絞り込みます。
