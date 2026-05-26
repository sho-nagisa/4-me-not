# test_task_candidate_extraction.py

## 概要

会話文からタスク候補を抽出する処理について、日本語の期限表現を含むタスク検出と、タスクではない文章の除外を確認するテストです。

## テスト内容

### `test_extracts_task_candidate_with_japanese_due_date`

日本語文中の期限付き依頼からタスク候補を1件抽出し、タイトル、期限日、信頼度が期待通りになることを確認します。

### `test_ignores_sentences_without_task_signal`

タスク化すべき表現を含まない文章では、タスク候補が抽出されないことを確認します。
