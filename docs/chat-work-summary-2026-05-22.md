# Chat Work Summary - 2026-05-22

このチャットで実施した作業の簡潔なまとめです。

## README / Docs

- デモデータ入りの画面スクリーンショットを4枚追加。
- READMEを短く整理し、概要、スクリーンショット、機能、構成、セットアップに絞った。
- 詳細な設計メモは `docs/technical-notes.md` に分離。

## Refactoring

- `backend/services/search_service.py` から検索定数、埋め込み、補助処理、回答生成を分離。
- `frontend/src/pages/InteractionNew.tsx` からブランド切り替え、レイアウト、ナビゲーション処理を分離。

## 確認

- Backend tests passed.
- Frontend build passed.
- 分割した Python モジュールの compile check passed.

## Commits

- `eafa168` `docs: refresh README and add screenshots`
- `89dfb8b` `refactor: split search service and app layout`
