# v0.3 → v0.4 の互換性と移行

## 版を混同しない

配布物v0.3はデータ契約2・HTTP案/v2、配布物v0.4は契約3・HTTP案/v3。実repoの`/api/*`とは別。稼働中APIを改変したわけではない。archive/v0.3-original.zipは元ZIPそのもの、archive/v0.1は既存の旧資材。

## 変更一覧

| 対象 | v0.4の差分 | 移行の規則 |
|---|---|---|
| ImportRequest/Source/DerivationRequest/GateRequest | schema_version=3 | v2をv3endpointへ無変換で投入しない |
| Snapshot | feature_epoch追加 | 新たに制御世代0を作る。過去に実験機能が存在したと捏造しない |
| CognitiveSchemaPayload | role/scope/valid_time/alternatives/unknowns/evidence groups | 不明ならunclassified、unknown。旧Schemaの内容から本人の人物モデルを確定しない |
| DerivationRequest | revision_of | 旧版で分からない場合null。関係が既に確認できるときだけ対応を保存 |
| MemoryDraft | additional_dependency_refs | 旧derived_from_revision_idsを維持し、新たなArtifact依存を必要時に追加 |
| ArtifactView/MemoryRevision | required_features、Artifactのproducer_feature | 信頼済み生成/全依存から求める。旧履歴の出所不明は保留し、空を『実験非依存の証明』にしない |
| VersionRef | prediction/outcome/evaluation/assessment/feature_control/learning_manifest | 旧IDは維持、別リソースに同じIDを流用しない |
| RecallV2/FeedbackV2という型名 | RecallV3/FeedbackV3へ名称更新 | 現行のAPI inventoryをコード生成元にする |
| 9つの新API | 予測・結果・評価・点検・機能制御 | 旧のSchemaApplicationと二重結果正本を作らず参照でつなぐ |

## 実データの移行は未実装

このZIPで行ったのは**架空fixtureの明示変換**であり、ユーザーのDB移行ではない。実装時はdry run→件数/ID/原文ハッシュ/出典/時刻/採否/ACL/依存の比較→本人確認→トランザクションまたは二重領域から切替。source文字列を正規化して上書きしない。

旧モデルに依存情報が足りず安全な移行が判定できなければ、仮の空依存にせず読取限定で残す。再取り込みで新しい経験と誤計上しない。元の採否・伝聞・不確実性を保持する。

## Rollback

v3からv2へ、新フィールドを落として逆変換しない。予測由来の仮説が一般の事実へ化ける危険がある。旧アプリを残す場合は旧snapshotと旧保存領域へ戻し、新規v3データは別領域で保管。現在の削除・同意撤回は巻き戻さない。

機能OFFはv3全体のrollbackではない。prediction_loopだけ停止しcore v3は継続できる。旧版のarchive文書は設計の履歴であり、Codexがactive仕様を過去へ戻す指示ではない。

## W30-06：入口・明示変換・差戻しの境界

| 入口 | 互換・拒否/adapter | 移行証拠・差戻し |
|---|---|---|
| 契約2 / v0.3 / v2 | v3へそのまま渡さず旧Schema検証後に明示変換。本文のschema_versionだけを信用しない | 出典の契約版、元ファイルhash、変換器版、入力/出力hash、ID対応、原文byte/hash・主体比較、件数/衝突を記録。旧領域保持 |
| v0.1の旧v1試案 | 同名型をv3へcastしない。具体adapter未承認 | 元ID・原文・share_level/approveの意味を履歴として保持し、用途許可は新たに検査。対応不明は読取限定 |
| 稼働/api | account・Task/MemoryProposal・OCRのDTOをv3と同一視しない | W30-01 D1〜D6と既存E1/E2/E3/E6。既存ID対応と本人判断が前提。今回DB変更なし |
| 新規v3 | v3型に加え現在の認証/対象/vault/依存/消去を検査 | 過去の承認・policy_revision・digestは現在の新用途許可ではない |
| v3→v2 | 新フィールドを削るだけの逆変換は拒否 | 旧snapshot/領域へ戻す案のみ。v3データは別保管し、最新の消去/撤回台帳は巻き戻さない |

Source/ImportRequestには旧v2と版番号以外が同形の例がある。Schemaは出所を認証できず、3へ付け替えた値の由来をJSON単体で見破れるとはしない。信頼済み取込経路が確定した元契約版と照合し、旧領域からの入力は明示移行以外で受理しない。現在のアプリにはそのadapterが未接続である。

局所contracts/migration_examples.pyは元ZIPの架空Sourceを旧Schema検証→契約3候補へ明示変換する純粋な例。Sourceの他フィールドは丸ごと保持し、同一入力から同一候補と監査digestを返す。保存・新ID発行・重複排除DB・移行許可・確認receiptは実装しない。原文にはUTF-8の同じ文字列を用い、正規化・改行変更をしない。Sourceにはdigestフィールドがないため、新しいwireフィールドを作らず移行証拠側で全内容hashを照合する。

MemoryRevision/Artifactのrequired_features不明は、空を非依存の証明にせず旧領域の読取限定・通常利用停止とする。非依存を証明する全由来検査、producer照合、対応表が揃うまでv3の利用可能投影にしない。Source化の単純例を全Memory/Schema移行へ拡張しない。source訂正は新Source/Revisionであり移行中の上書きではない。

旧approve/accepted/share_levelは歴史上の記録として保持するが、新用途のallow/interactive/delegatedへ写像しない。旧APIの迂回候補はW30-05監査に記録済みで、実保護はW33等の接続待ち。今回、旧APIを修正したとは扱わない。型エラーと境界拒否は既存Errorのコードへ将来adapterで対応する。局所ValueErrorを新しいHTTPエラー契約としない。

DRAFT：D1採否wire統一、D2 account/vault/Actor対応、D3媒体Source化、D4採用→学習同意、D5 Task/Intention正本、D6旧API外部送信の具体接続は未承認。提案は明示対応表とdry-run比較を本人が確認してから切替。ID/時刻/出自/許可範囲・再開意思に影響するため自動変換しない。W30-05 M1〜M4の写像判断はこの移行例で解決しない。

差戻しに必要な最新の消去/撤回台帳が得られなければ通常利用を保留する。停止は既送信の情報や完了済み行動を回収しない。AUTO-015の局所冪等例、AUTO-019の参照拒否、V04-037の版検査は実移行transaction/復元受入とは別。
