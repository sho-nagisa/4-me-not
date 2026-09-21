# W30-04 詳細報告・4権限と呼出主体境界

タスクID：W30-04
状態：完了
分類・運用状態：core。型・局所契約・仕様検証の範囲で完了。アプリ配備なし、実運用のdisabled/shadow等は未確認。

## 今回の責務とv0.4差分

W30-03-use-contract.md、変更した状態/権限文書、validation.jsonと検査ログを確認した。既存7 overlayファイルはW30-03証拠のhashと一致。実repoに適用するAGENTS.mdは従来確認済みの不在を維持し、新規作成なし。タスクパックGUIDE.md/tasks/W30-04.mdを参照した。

既存GateDecisionの4権限、outcome、basis、GateRequest、ActorをJSON Schema参照で再利用し、局所境界型を追加した。操作の必要権限は既存operation-registry.jsonから求め、複数集合の欠落を検査する。認証adapterの出力位置を示すCallerFieldsと候補DTOを別入力にした。Actor.userとtrusted ownerの対応は認証側から監査表現への一方向で、kindと解決済みIDが不一致なら拒否する。

局所コードは必要権限を返すだけで、許可・確認receipt・GateDecisionを発行しない。modelが必要権限を照会できても採用権限を得ない。既存参照Gateのmodel拒否も回帰確認した。Gate本体は実装していない。

既存packages/memory-coreは今回作らず、仕様作業版docs/spec/v0.4/contractsへ局所契約を配置。既存modelsや稼働/apiを変更しない。配布物v0.4、データ契約3、HTTP案/v3を区別する。

## 対応REQ/AUTO/V04・仕様箇所

| 要求・受入 | 根拠 | 今回の検証と限界 |
|---|---|---|
| REQ-AUTO-006 / AUTO-006 | promotion.feature:35、Actor、api-semantics:7/22 | caller→監査Actorの16組、別ID拒否、参照modelのprofile_adopt拒否。実採用endpointは未接続 |
| REQ-AUTO-007 / AUTO-007 | promotion.feature:41、gate-and-delegation:9 | confidence0.99でもmodel拒否、ownerは確認要求。実receipt照合なし |
| REQ-AUTO-017 / AUTO-017 | promotion.feature:101、GateRequest | actor/risk/approved等10種の追加property拒否。委任の実保存なし |
| REQ-AUTO-003 / AUTO-003 | state-model、W30-03契約 | 既存shadow/provisional回帰維持 |
| REQ-V04-004 / V04-004 | feature-registry、v04.feature:23 | test_v04_assetsを含む全資材検査。実験必須依存を追加しない |
| REQ-V04-037 / V04-037 | migration、v04.feature:221 | 既存wire制約比較と旧版回帰。実データ移行なし |

## 変更ファイル

全て今回新規追加、削除0行。既存memory.schema.json、operation-registry、OpenAPI、REQ、受入本文は変更不要で保持。新しい内部補助Schemaは86個の既存wire定義を増減するものではない。

| 絶対パス:行 | 内容 | 追加/削除 |
|---|---|---|
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/contracts/authority-boundary.schema.json:1 | 既存型参照・内部複数集合・caller項目 | +26/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/contracts/authority_boundary.py:1 | 別入力・監査Actor対応・必要集合の局所検査 | +79/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/docs/authority-boundary.md:1 | 信頼境界・対応表・DRAFT・未接続条件 | +39/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/fixtures/w30-04-authority-cases.json:1 | 合成caller・偽装・複合操作例 | +11/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/spec/v0.4/tests/test_w30_04_authority_boundary.py:1 | 新6局所テスト | +100/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-04-validate.ps1:1 | ZIP＋12 overlay再現・検査 | +91/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-04-validation.json:1 | 実行環境・終了・hash | +110/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-04-active.log:1 | 105件の実行記録 | +110/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-04-baselines.log:1 | 旧版25＋11件の実行記録 | +48/-0 |
| C:/Users/keima/Desktop/4-me-not/docs/implementation/W30-04-authority-contract.md:1 | 本報告・再現入口 | +82/-0 |

## 不変条件の確認根拠

W30-03の7 overlay hash一致、既存コード196ファイルはW30-01時点および検査前後から変更0。既存15追跡ファイルの未コミット差分331追加/5削除と未追跡機能、models構成を保持。既存Schemaの全制約比較が合格し、86定義・38 API・46操作・25機能を保持。4権限の複合4操作では各要素の欠落を拒否し、46操作の集合を検査した。未知権限、重複、空集合、追加property、model→ownerの不一致を局所拒否する。

原文/ID/digestと人物役割、採用≠真実、provisional≠shadow、FeatureControl≠Deployment≠Gate、全由来required_features、保存/学習/提示/送信/行動の別許可を維持。品質continue・検索回数・無反応から認可しない。実アプリでこれら全てを強制済みとは主張しない。

契約/API/DTO・互換/移行：既存wireとAPIの変更なし。内部AuthoritySetのみ重複を拒否し、既存GateDecision配列の受理集合は狭めない。Actor/Callerの対応に既存account＝Actor＝vaultという同一ID仮定を入れず、DB変換はしない。

停止・取消・復旧：今回実行作用なし。局所型は停止barrierや取消を実装しない。現在の撤回/失効を確認する実Gateが未接続なら実行許可を発行しない。既送信情報や完了済み行動を型変更で回収できるとは扱わない。

## テスト

起点cwd：C:/Users/keima/Desktop/4-me-not
実起点コマンド：& './docs/implementation/W30-04-validate.ps1'（終了0）。
SPEC_ROOT：C:/Users/keima/AppData/Local/Temp/4-me-not-W30-04-run-1111401031524b70b477e901b5731e9c/4-me-not-collab-v0.4
Python実パス：C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
Python 3.12.14、jsonschema 4.26.0。PYTHONUTF8=1、PYTHONDONTWRITEBYTECODE=1、PYTHONPATH=C:/Users/keima/AppData/Local/Temp/4-me-not-W30-02-depsを使用し、終了時に環境を戻す。アプリ依存変更なし。

| 検証層 | cwd | 実子コマンド（pythonは上記実パス） | 終了 | 合否・件数 | 証拠（絶対パスは上表） |
|---|---|---|---:|---|---|
| 仕様資材・型・局所契約・参照規則 | 上記SPEC_ROOT | python -X utf8 -m unittest discover -s tests -p "test_*.py" -v | 0 | 105/105（既存99＋新6） | W30-04-active.log、validation.json |
| 旧版資材・参照規則 | 上記SPEC_ROOT | python scripts/check_baselines.py | 0 | v0.3 25/25、v0.1 11/11 | W30-04-baselines.log |

初回で全件合格。subTestを件数へ加算しない。型検査はJSON Schema自己検査・参照解決・正負入力の実行検査であり、Python静的型チェッカーの実行とは区別する。git diff --checkも終了0（既存追跡差分が対象）。

再現時は参照ZIPを新規一時領域へ展開して12 overlayを上書きする。永続入口はdocs/spec/v0.4の部分作業版と本runner。その他の仕様は参照ZIPを使用。W30-01〜03の報告・証拠は当時の履歴として保持する。ZIP SHA-256は811A9B2E19FE4CFF7C3AE106D4B2115D40B83A67E429D3F8C8509B64FA307C5Eで不変。SourceZip/Python/Dependenciesはrunner引数で指定可能。

## 未実装・未実施・未決

実認証adapter・Gate本体・確認/委任receipt・実DB/API/UI受入・端末・実LLM・停止競合は未実施。今回は局所型の担当範囲であり、これらを成功として数えない。CallerFieldsはコードから構築できる内部型であり、Schema適合・constructor成功を認証証拠としてはいけない。HTTP/LLMのJSONをそこへ変換するfactoryは提供していない。実接続がなければ実行許可は発行できない。

DRAFTは未承認のまま。具体案・影響はauthority-boundary.md:25以降：既存account認証を再利用しvault/Actor対応を明示する案は本人・認証担当の判断が必要。dev fallbackは本人確認の証明にならない。system/ruleは登録service principalへの条件付き対応で、実登録/失効方式はworker停止・監査に影響するため未決。GateDecisionのwire重複禁止やoutcome/basis制約追加案はconsumer互換に影響するので今回は変更しない。従来の機微表示、採否名称、Task/SKIPPED、予定採用→学習同意のDRAFTも承認へ変えない。

レビュー：Codex自己点検、独立レビュー未実施。必要権限集合を許可集合と混同しない命名・説明とし、Actorからownerへの逆変換を作らず、帰属と認証の違いを明記した。Gate本体への拡張は行っていない。

情報境界：合成fixtureのみ、通常ログは検査結果のみ。実原文・.env値・秘密を読まず、外部payload/ネットワーク送信・本番DB・公開・pushなし。

引継ぎ：既存E1 account portとE3採用候補portは未接続条件とDRAFTを保持して再利用候補とする。次の推奨IDはEXECUTION_ORDER.md:17の **W30-05**。次タスクには着手していない。
