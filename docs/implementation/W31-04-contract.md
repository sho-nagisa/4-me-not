# W31-04 Content Ledger・原子的更新の局所契約

ContentLedgerはStoragePort.transactionとMemoryRevisions.project_inを再利用する。
backendの実DB/session/HTTP/Gitへ接続しない。認可と実失効portは既定未接続で拒否する。

## 最小内部Commit

|フィールド|内部契約|
|---|---|
|kind|genesis / content。外部の新しいwire型ではない|
|commit_id / vault_id|UUID。commit_idは不変・vault内一意|
|parent_head|contentでは直前の同vaultのHEAD。genesisだけNone|
|item_id / revision_id|contentでは同一取引で格納した版。genesisはNone|
|snapshot|そのCommit時点の完全な既存Snapshot|
|receipt|contentでは既存CommitReceipt。genesisはNone|

genesisは全Snapshot座標を信頼する保存adapterから明示してinitializeする内部bootstrap。
既存vaultを再初期化しない。policy/erasure/feature epochを勝手に0へリセットするAPIではない。
実DBの初期化・旧履歴取込/復元は未接続。内部root表現であり、既存CommitReceipt.parent_headの非null契約は変更しない。

## 取引

1. 現在の認証/確認/具体planをAccessPortで検査。DTOのapproved_by等を許可にしない。
2. (vault,caller,固定contentCommit,冪等キー)で再送照合。再送にも現在の版読取/消去/利用条件を検査。
3. 現在SnapshotとそのHEADのCommit存在を読み、expected_headを照合。
4. Revision/Item/currentを同じTransactionに格納。親はexpected_currentと整合させる。
5. InvalidationPortが同じ取引に利用停止を準備する。未接続はrollbackして拒否。
6. Commit、Snapshot HEADのCAS、receiptを格納し、返却時条件を再検査。
7. transaction exitが成功してから返却。どこで失敗しても部分更新を残さない。

InvalidationPort.applyはW31-07へ残す取引参加port。今回のFakeInvalidationはtest用印のみ。
実依存探索・停止barrierを実装したとしない。stale_derived_revision_idsはこの信頼するportから受ける。
ContentLedger.commitはapproveChange/receipt認証を実装しない。W31-05にはまだ進まない。

## HEADと他の座標

Snapshotは既存6座標をすべて検証し、部分snapshotは拒否。
Content Commitではcontent_headだけを更新し、その取引で読んだfeature_epoch等を保持する。
期待値比較はexpected_head。無関係な派生/Operation追加や機能epochをHEADの代わりにしない。
feature停止transaction本体はW42-04。fake試験でのepoch変更はその実装ではない。
過去Commit.snapshotは上書きせず、現在epochを過去値へ戻さない。

get_itemは現在vault HEADとcurrent Revisionを同じ取引から読み、projectionの由来Commitも照合する。
MemoryRevisions.get_itemは局所projection基準の読取、vault全体HEADと合わせる入口はContentLedger.get_item。
具体Commit/Revisionの履歴読取にも現在のACL/消去/依存利用を適用する。古いreceipt/snapshotは許可ではない。
Derivation/Operationは別系列。今回それらのログサービスを実装せず、fakeの別collection追加で非干渉を検査する。

## 制約と引継ぎ

StoragePort実装はserializableな整合境界とCAS/unique/rollbackを提供する必要がある。
今回FakeStorageのRLock＋copy-on-writeで2thread競合と各段階rollbackを検査した。実DB・複数process・電源断・commit結果不明を検証していない。
既存PostgreSQLへのadapter/DDL/移行、account/vault/Actor写像、暗号化/鍵/復元は未決の案のまま。
receipt内部のcanonical request/planにも本文が含まれるため、将来の物理消去では原本だけでなくこの保存先も対象にする必要がある。通常返却は本文なしのreceiptのみ。
認証/Gate/確認receiptはW33-01〜03以降、実失効はW31-07、推移feature計算はW42-03へ。
W30のM1〜M4・D1〜D9等は承認しない。局所部品の合格は実アプリ/保存配備の承認ではない。
