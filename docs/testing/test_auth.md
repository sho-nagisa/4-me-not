# test_auth.py

## 概要

認証APIの基本フローと、アカウントごとのデータ分離を確認するテストです。

## テスト内容

### `test_register_login_me_and_logout`

ユーザー登録、ログイン中ユーザー取得、ログアウト、再ログイン、誤ったパスワードでのログイン失敗を確認します。

### `test_register_rejects_duplicate_email`

大文字小文字の違いを含む重複メールアドレス登録が409で拒否されることを確認します。

### `test_register_rejects_invalid_email_and_password_boundaries`

不正なメールアドレス、短すぎるパスワード、長すぎるパスワードが登録時に拒否されることを確認します。

### `test_session_token_rejects_tampering_and_expiration`

署名を改ざんしたセッショントークンと期限切れセッショントークンが認証に使えないことを確認します。

### `test_authenticated_requests_use_account_scope`

別々のアカウントで作成したデータが分離され、一方の人物データがもう一方の一覧に表示されないことを確認します。

### `test_search_results_do_not_cross_account_boundary`

別アカウントで作成した記録が検索結果に混ざらないことを確認します。

## 補助処理

### `_register`

指定したメールアドレスでユーザー登録APIを呼び出し、作成されたアカウントIDを後片付け用に保存します。
