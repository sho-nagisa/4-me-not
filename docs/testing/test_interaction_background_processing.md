# test_interaction_background_processing.py

## 概要

インタラクション保存後のバックグラウンド処理について、タスク登録とAI分析・検索インデックス・タスク候補抽出などの後続処理が呼ばれることを確認するテストです。

## テスト内容

### `test_record_interaction_queues_post_processing`

インタラクション記録APIの内部処理が成功レスポンスを返し、保存後処理をBackgroundTasksへ1件登録することを確認します。

### `test_process_interaction_after_save_runs_ai_and_followups`

保存後処理がAI分析、インサイト作成、検索インデックス更新、タスク候補抽出、関係更新を順に呼び出すことを確認します。
