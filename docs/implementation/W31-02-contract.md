# W31-02 局所保存契約

原ZIP＋docs/spec/v0.4作業版のImportRequest/ImportReceipt/Sourceを再利用。
SourceStorage.import_source/get_sourceはローカル操作。HTTP routeへ接続していない。

## 保存・再送

StoragePort.transactionはserializableな読取/書込と全体commit/rollbackを要求する。
Transaction.getはコピー、insertは既存キー上書き禁止、compare_exchangeは期待値比較と交換を一体に行う。
実adapterはcommit失敗を成功扱いにしてはならない。今回の実装adapterはtests/memory/storage_fakes.pyの決定的copy-on-write fakeだけ。
実PostgreSQL/端末保存/暗号化/復旧の方式を確定したものではない。

冪等キーは(vaultのUUID値、信頼するcaller識別キー、固定operation=importSource、キー文字列)。
ImportRequestの全フィールドを、オブジェクトのキー順だけ揃えたUTF-8 JSONとして比較する。
原文、改行、Unicode、ID文字列、配列順序は正規化しない。整数値の別JSON表現まで同一視するRFC canonical JSONではない。
同一キー・同一canonical requestなら初回receiptを返し、異内容はIDEMPOTENCY_CONFLICT。
異なるキーでの内容重複排除は今回の冪等契約ではない。

Sourceとreceiptを同じtransactionへinsertし、context exitのcommit成功後だけstatus=savedを返す。
schema_version=3、元Message ID/text、captured_at、初回imported_at/policy_revision/source_idを保持する。
Source全値のcanonical digestを内部保存し読取時に再検査。wireにdigestフィールドを追加しない。
HTTP受信前のJSON空白/エスケープのraw byte列は本dict入口には存在せず、保存保証はSource値と原文UTF-8。媒体/transport raw保存は別adapter。
解析・Prediction・結果照合を呼ばない。status=savedは解析完了を意味しない。結果リンクはSourceを書き換えない。

## 認証・消去

StorageContextのvault/caller/policyは座標で、本人認証や許可の証明ではない。
AccessPortが未接続ならAUTHORIZATION_NOT_CONNECTED。テストfakeはbackendへimportしない。
AccessPortは現在の認証/用途/ACL/消去/利用可能性を、transactionと同じ整合境界で検査する必要がある。
import時、初回返却時、再送時、getSource時に呼ぶ。過去receiptを使って現在の削除や撤回を迂回しない。
成功receiptに本文を入れず、拒否例外も本文を含まない。物理消去や認証競合の実装ではない。

## 既存DBとの境界・DRAFT

既存MemoryService.ingest_screenshotはaccount単位の画像hash重複排除とOCR。v3 Source/receiptとは別契約。
再利用したのは既存Python services配置、MemoryContracts/SourceEvidence、局所unittest基盤。
既存models・DB session・account fallbackには接続しない。D2 account/vault、D3 OCR→Source移行は未承認。
将来案は既存PostgreSQLへ明示的なSource/receipt表と一意制約を追加し、認証されたaccount→vault対応をadapterへ限定すること。
影響は保存スキーマ/ID写像/認証/移行/rollback。現段階では案のみで、DB実装と実データ移行は停止。
今回指定のport/fake局所試験はこの判断から独立して完結する。
