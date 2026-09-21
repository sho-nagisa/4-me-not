# W31-01 Source・根拠位置の局所契約

正本は原ZIP＋docs/spec/v0.4のcontracts/memory.schema.json。
SourceEvidenceはMemoryContractsを再利用し、契約3 Source/Message、EvidenceInput/Span/Locator、VersionRefを検証する。
既存のaccount/OCR/MemoryProposalとは同一視しない。既存Python servicesとunittestを使用し、別package/DBモデルを作らない。

## 原文・識別

Sourceを検証後に深いコピーとして保持。公開snapshotもコピーで返し、原文bytes/IDの更新APIはない。
Message IDはSource内で一意。参照はsource_id/message_idの複合で照合し、UUIDの同一性で比較する。
別Sourceの同一Message IDは合法だが、別Sourceの根拠を当該Sourceとして扱わない。
expected_vaultとの一致を検査する。expected_vaultとsource_contractは信頼する取込adapterが供給する座標であり、
AIから渡した文字列を本人認証や許可の証明にしない。契約2のSourceは拒否し、3へ付け替えても由来版2なら明示移行を要求する。
元版が偽って3と申告されたJSON単体の出自は証明できない。実取込/認証接続は未実施。

原文は正規化/改行変換せずUTF-8へ符号化。孤立surrogateはINVALID_UTF8。
message_digestは元Message textのUTF-8 SHA-256で、wireに新digestフィールドを追加しない。
JSONファイル自体の空白/エスケープを含むbyte保存やSource全体の永続digestはW31-02で扱う。
発言者情報は保持するだけで、speaker/subject/claimant/relayを自動的に写像しない。

## 根拠位置

locate(EvidenceInput)は原文byte列を完全一致検索し、0一致はEVIDENCE_NOT_FOUND、複数一致はEVIDENCE_AMBIGUOUS。
重なった一致（aaa中のaa）も複数。曖昧時に最初を自動採用しない。
一意な一致はUTF-8 [start_byte,end_byte)のtext locatorへ戻す。
verify_text_locatorは指定範囲・UTF-8境界・quoteのbyte一致を確認する。重複時の明示選択範囲も検査できるが、本人選択の証明ではない。
整数値4.0もJSON Schemaのintegerに適合するため、検証後にPython slice用intへ変換する。非整数/booleanは拒否する。
byte一致を意味支持・採用・真実・認可へ昇格しない。例外に原文/quoteを含めない。

## 未接続境界

audio/imageは既存EvidenceLocator unionの形状だけ検証し、text解決入口ではMEDIA_RESOLUTION_NOT_IMPLEMENTED。
媒体の存在・時刻順序・画像領域の実範囲・読取はW39。未知locatorは拒否する。
VersionRefの追加resource_typeは形状だけ検証し、対象の存在/現在版/ACL/媒体実装を保証しない。
Prediction/Outcomeを必須とせず、独立した結果のSource原文へ直接戻れる。依存印の算出/除去は行わない。
W31-02保存adapter、W31-08人物役割、W33認証/Gate、W39媒体の結合は未実施。
AUTO-001の型/原文保持の局所責務だけを検証し、解析失敗時のDB保存受入はW31-02等へ引き継ぐ。

## 再検証

今回の隔離SPEC_ROOTと全子コマンドはW31-01-validation-7rrf2ayv.json。
最終局所試験は同SPEC_ROOTでpython -X utf8 -m unittest discover -s tests/memory -p test_*.py -v。
必要環境はPYTHONUTF8=1、PYTHONDONTWRITEBYTECODE=1、PYTHONPATHにrepoとjsonschema[format]の配置、MEMORY_SPEC_ROOTに完全作業版。
validate_local_tasks.pyは新タスク開始時に--beginで不変基準を作り、最初の総合検査に使う。
既存開始基準は更新せず、追試は新しい名前のログと明示した差分一覧で記録する。過去証拠を上書きして再使用しない。
