# W30レビュー R1 修正報告

対象：R1［P2］棚卸し以降のコード差分を検出しても成功終了する。
状態：修正済み・合成回帰検査合格。独立レビューの再確認は未実施。

W30-07だけでなく、同じ終了判定を持つW30-02〜07の6入口を同じ意味で狭く修正した。changedSinceInventory.Countを終了1の条件へ追加し、件数と差分ファイル名を標準出力へ表示する。実行中の差分ファイル名も表示する。既存JSON形式・基準hash・テスト実行順を変更しない。差分の自動削除・巻戻し・基準更新は行わない。後続実装フェーズで別基準を使う場合は別途明示する。

## 変更ファイル

各validatorは結果表示7行追加＋終了条件1行変更（+8/-1）。

- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-02-validate.ps1:81
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-03-validate.ps1:84
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-04-validate.ps1:89
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-05-validate.ps1:94
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-06-validate.ps1:97
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-07-validate.ps1:106
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-R1-regression.py:1 — 再現可能な合成検査runner。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-R1-regression.json:1 — 18ケースのコマンド・cwd・終了コード・ログ本文・証拠JSON・validator hashと実ファイル保持証拠。
- C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-R1-report.md:1 — 本報告。

## 実行結果

起点cwd：C:/Users/keima/Desktop/4-me-not
コマンド：& 'C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 docs/implementation/W30-R1-regression.py
終了コード：0。18/18ケース合格。

| ケース（6本それぞれ） | 基準以降の差分 | 実行中の差分 | 終了コード |
|---|---:|---:|---:|
| 変更なし | 0 | 0 | 0 |
| 開始前にvalue=1→2 | 1 | 0 | 1 |
| テスト実行中にvalue=1→2 | 1 | 1 | 1 |

各入口スクリプトをバイト不変で合成repoへコピーし、その実スクリプトを別PowerShellプロセスで実行した。合成ZIPの小さなテストは全ケース成功させ、コード不変条件だけで終了判定が変わることを検証した。JSON件数・path・標準出力・終了コードを照合。変更された合成コードと基準JSONが自動復旧/更新されないことも確認した。実行中変更はテスト本体から発生させ、タイミング競合に頼らない。

検査開発中に合成ZIPのdocs/fixturesディレクトリ不足、およびWindows改行をLF固定hashと比較した検査側の誤りで失敗した。合成環境・比較方法を修正後、18ケース全てを再実行して合格。実repoのコードに失敗注入していない。

## 保持・検証範囲

実コード196ファイルはW30-01のhashと現在も一致。既存未コミット変更・modelsは保持。過去W30-01〜07の報告/ログ/証拠、19仕様作業版、既存コード、参照ZIPの合計246ファイルは検査前後hash一致。過去のvalidation.json/logを今回の結果で上書きしていない。

今回の18件は検査手順の合成回帰件数。実仕様114件/旧版25+11件の再実行や実アプリ受入ではない。仕様・アプリコードを変更していないため、本修正では全仕様試験は再実行していない。git diff --checkは終了0（既存追跡差分の検査）。

ユーザー提示の独立レビューを受領してR1へ対応した。修正自体の確認は実装担当による自己点検・回帰検査であり、独立再レビュー済みとはしない。M1〜M4・D1〜D9等の未承認状態は変更なし。Gate本体・実認証・DB/API/UI・外部送信・停止競合の実受入は未実施。

次の推奨IDはW43-01のまま。今回、次タスクには着手していない。
