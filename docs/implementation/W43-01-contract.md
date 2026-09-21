# W43-01 局所契約

正本は参照ZIPに docs/spec/v0.4 を重ねた contracts/memory.schema.json。
MemoryContractsへそのSchemaを明示注入し、既存のSchemaRole/CognitiveSchemaPayload/EventTimeをそのまま検証する。
アプリ起動時の読込・DB/API接続はまだない。配布物v0.4とデータ契約3は別。

## 明示移行map（データ契約2 → 3）

|入力|出力|
|---|---|
|stable_id|同じ文字列。UUIDとして検証|
|hypothesis、structural_mapping、applicable_when、avoid_when、supporting_refs、counterexample_refs|値を深いコピーで保持|
|旧契約に存在しないschema_role|unclassified|
|model_scope|None|
|valid_time|precision=unknown、他フィールド=None|
|alternative_refs / independent_evidence_groups|空配列（不存在の証明ではない）|
|unresolved_questions|legacy role/time/evidence grouping unknown|

入力を旧契約で検証してから新契約で出力を検証。既に役割等を持つpayloadを旧データとして上書きしない。
原文hypothesisのUTF-8 SHA-256を返す。Sourceの原文/digestはこの処理へ渡さず、変更しない。
架空fixtureを使う純粋な変換で、実DB移行ではない。再実行は同じ結果、入力変更なし。
入力版は信頼する保存adapterの責務。AIが申告したsource_contractを実データの版証明と解釈しない。
3→2は常に拒否。項目を削ったpayloadだけでは由来版を判別できないため、版メタデータを保持して呼び出すこと。

## 役割・失敗境界

pattern/principle/unclassifiedではmodel_scope=null、modelでは既存enumのscopeが必須。
直接principleを作れ、pattern/model履歴や予測器を要求しない。分類の推論・固定段階・本人像の推定はない。
valid_timeは既存EventTime制約だけを適用。不明を時刻へ補完しない。
正負fixtureはtest_schema_roles.pyで配布fixtureから合成し、各役割・scope・時刻・旧版拒否を検査する。
検証成功は採用、真実、認可、FeatureControl有効化を意味しない。

## 接続待ち

保存adapter、Revision、Gate、実認証、品質判断、予測、UI、実機受入は未実施。
既存modelsを移動/置換しない。M1〜M4/D1〜D9は未承認のまま。
局所層の利用にはjsonschema[format]と完全な作業版Schemaを注入する。
