import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const workbook = Workbook.create();

const summarySheet = workbook.worksheets.add("Summary");
const coreSheet = workbook.worksheets.add("CoreTables");
const supportingSheet = workbook.worksheets.add("SupportingTables");
const enumSheet = workbook.worksheets.add("Enums");

const outputDir = path.resolve("outputs", "phase1-db-design");
const outputPath = path.join(outputDir, "phase1-db-design.xlsx");

const headerFormat = {
  fill: "#1F5C4B",
  font: { bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
};

const sectionHeaderFormat = {
  fill: "#D9EDE6",
  font: { bold: true, color: "#16372D" },
};

summarySheet.showGridLines = false;
coreSheet.showGridLines = false;
supportingSheet.showGridLines = false;
enumSheet.showGridLines = false;

summarySheet.getRange("A1:H1").merge();
summarySheet.getRange("A1").values = [["勿忘草 Phase 1 DB Design"]];
summarySheet.getRange("A1").format = {
  fill: "#F0F7F3",
  font: { bold: true, size: 18, color: "#1A332A" },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};
summarySheet.getRange("A2:H3").merge();
summarySheet.getRange("A2").values = [[
  "Phase 1 では、話題の階層管理、コミュニティの階層活用、Interaction の構造化、共有レベルの明示を追加する。入力負荷を増やしすぎず、後から『誰に・どこまで話したか』を追える設計を目指す。"
]];
summarySheet.getRange("A2").format.wrapText = true;
summarySheet.getRange("A2").format.verticalAlignment = "top";

summarySheet.getRange("A5:C5").values = [["Scope", "Design Direction", "Key Change"]];
summarySheet.getRange("A5:C5").format = headerFormat;
summarySheet.getRange("A6:C10").values = [
  ["Topics", "親子構造", "topic.name / topic.parent_id による階層話題"],
  ["Communities", "親子構造の活用", "community.parent_id を使ってパス表示"],
  ["Interactions", "構造化", "community_id / topic_id / share_level / occurred_at / note を追加"],
  ["Frontend", "入力は軽量", "選択式で階層と共有レベルを扱う"],
  ["API", "参照系拡張", "/api/topics と階層パス付き一覧を追加"],
];

summarySheet.getRange("E5:H5").values = [["Relationship", "From", "To", "Notes"]];
summarySheet.getRange("E5:H5").format = headerFormat;
summarySheet.getRange("E6:H12").values = [
  ["1:N", "persons", "interactions", "1人に対して複数のやり取り"],
  ["1:N", "communities", "communities", "親コミュニティを持つ自己参照"],
  ["1:N", "topics", "topics", "親話題を持つ自己参照"],
  ["N:1", "interactions", "communities", "文脈として任意で紐づける"],
  ["N:1", "interactions", "topics", "話題として任意で紐づける"],
  ["N:1", "memberships", "persons / communities", "所属を保持"],
  ["N:1", "relations", "persons", "人同士の関係性を保持"],
];

summarySheet.getRange("A13:C13").values = [["Phase 1 Deliverables", "Status", "Comment"]];
summarySheet.getRange("A13:C13").format = headerFormat;
summarySheet.getRange("A14:C19").values = [
  ["Topic hierarchy", "Implemented", "Topic model / API / frontend input を追加"],
  ["Community hierarchy path", "Implemented", "一覧・入力候補をパス表示"],
  ["Share level", "Implemented", "話した / ぼかして話した / 話していない"],
  ["Interaction schema update", "Implemented", "構造化列へ変更"],
  ["Migration", "Prepared", "Alembic revision を追加"],
  ["History screens", "Future", "Phase 2 以降で実装"],
];

const coreRows = [
  ["persons", "id", "UUID", "Y", "", "N", "人の主キー", "BaseModel により自動生成"],
  ["persons", "name", "VARCHAR(100)", "", "", "N", "表示名", "入力画面で必須"],
  ["persons", "canonical_name", "VARCHAR(100)", "", "", "Y", "正規化名", "将来の重複管理用"],
  ["persons", "description", "TEXT", "", "", "Y", "補足説明", "人物メモ"],
  ["communities", "id", "UUID", "Y", "", "N", "コミュニティ主キー", ""],
  ["communities", "name", "VARCHAR(100)", "", "", "N", "コミュニティ名", ""],
  ["communities", "description", "TEXT", "", "", "Y", "補足説明", ""],
  ["communities", "parent_id", "UUID", "", "communities.id", "Y", "親コミュニティ", "大学 / サークル / 活動 のような階層"],
  ["topics", "id", "UUID", "Y", "", "N", "話題主キー", ""],
  ["topics", "name", "VARCHAR(100)", "", "", "N", "話題名", "転職理由 / 趣味 / 体調 など"],
  ["topics", "description", "TEXT", "", "", "Y", "補足説明", ""],
  ["topics", "parent_id", "UUID", "", "topics.id", "Y", "親話題", "就活 / 面接 / 転職理由 のような階層"],
  ["interactions", "id", "UUID", "Y", "", "N", "やり取り主キー", ""],
  ["interactions", "person_id", "UUID", "", "persons.id", "N", "相手", "必須"],
  ["interactions", "community_id", "UUID", "", "communities.id", "Y", "文脈コミュニティ", "任意"],
  ["interactions", "topic_id", "UUID", "", "topics.id", "Y", "話題", "任意"],
  ["interactions", "type", "INTEGER", "", "", "N", "やり取り種別", "InteractionType enum"],
  ["interactions", "share_level", "INTEGER", "", "", "N", "共有レベル", "ShareLevel enum"],
  ["interactions", "occurred_at", "TIMESTAMPTZ", "", "", "Y", "実際の日時", "未入力時は作成時刻で補完"],
  ["interactions", "content", "TEXT", "", "", "Y", "内容", "何を話したか"],
  ["interactions", "note", "TEXT", "", "", "Y", "補足メモ", "方便・言い回し・注意点"],
  ["reminders", "id", "UUID", "Y", "", "N", "リマインダ主キー", ""],
  ["reminders", "title", "VARCHAR(100)", "", "", "N", "タイトル", ""],
  ["reminders", "message", "TEXT", "", "", "Y", "メッセージ", ""],
  ["reminders", "remind_at", "TIMESTAMPTZ", "", "", "N", "通知予定日時", ""],
];

coreSheet.getRange("A1:H1").values = [[
  "Table",
  "Column",
  "Type",
  "PK",
  "FK",
  "Nullable",
  "Description",
  "Notes",
]];
coreSheet.getRange("A1:H1").format = headerFormat;
coreSheet.getRange(`A2:H${coreRows.length + 1}`).values = coreRows;
coreSheet.tables.add(`A1:H${coreRows.length + 1}`, true, "CoreTablesDictionary");

const supportingRows = [
  ["memberships", "人とコミュニティの所属関係", "person_id / community_id / role"],
  ["relations", "人同士の関係性", "from_person_id / to_person_id / type / strength"],
  ["person_profiles", "人物ごとのプロフィール補助", "first_impression / intuition / notes"],
  ["tags", "横断的なラベル管理", "person / interaction へ付与"],
  ["person_tags", "人物とタグの中間テーブル", "person_id / tag_id"],
  ["interaction_tags", "やり取りとタグの中間テーブル", "interaction_id / tag_id"],
  ["relationship_tasks", "次回行動の管理", "person_id / title / status"],
  ["task_histories", "タスク状態の履歴", "task_id / status"],
  ["insights", "AI や手動抽出の示唆", "person_id / type / content"],
  ["ai_metadata", "AI 処理のメタデータ", "model_name / confidence / source"],
  ["parsed_notes", "AI による解釈メモ", "source_id / metadata_id / content"],
  ["calendar_events", "外部カレンダー予定", "external_id / title / start_at / end_at"],
  ["meeting_snapshots", "会議要約の保存", "calendar_event_id / summary"],
  ["reminder_triggers", "リマインダの発火条件", "reminder_id / trigger_type"],
  ["community_trees", "コミュニティ階層の補助表", "現状は parent_id 中心、将来最適化候補"],
];

supportingSheet.getRange("A1:C1").values = [["Table", "Role", "Notes"]];
supportingSheet.getRange("A1:C1").format = headerFormat;
supportingSheet.getRange(`A2:C${supportingRows.length + 1}`).values = supportingRows;
supportingSheet.tables.add(
  `A1:C${supportingRows.length + 1}`,
  true,
  "SupportingTablesCatalog",
);

const enumRows = [
  ["InteractionType", "1", "TALK", "雑談・会話"],
  ["InteractionType", "2", "MEETING", "打ち合わせ"],
  ["InteractionType", "3", "MESSAGE", "通話 / メッセージ"],
  ["InteractionType", "4", "EVENT", "出来事・観察メモ"],
  ["ShareLevel", "1", "SHARED", "そのまま話した"],
  ["ShareLevel", "2", "PARTIAL", "ぼかして話した"],
  ["ShareLevel", "3", "WITHHELD", "話していない"],
  ["CommunityRole", "1", "OWNER", "作成者 / 所有者"],
  ["CommunityRole", "2", "ADMIN", "管理者"],
  ["CommunityRole", "3", "MEMBER", "通常メンバー"],
  ["CommunityRole", "4", "GUEST", "ゲスト"],
  ["RelationType", "1", "FRIEND", "友人"],
  ["RelationType", "2", "COLLEAGUE", "同僚"],
  ["RelationType", "3", "FAMILY", "家族"],
  ["RelationType", "4", "SUPERIOR", "上位関係"],
  ["RelationType", "5", "SUBORDINATE", "下位関係"],
  ["TaskStatus", "1", "TODO", "未着手"],
  ["TaskStatus", "2", "DONE", "完了"],
  ["TaskStatus", "3", "SKIPPED", "見送り"],
];

enumSheet.getRange("A1:D1").values = [["Enum", "Value", "Key", "Meaning"]];
enumSheet.getRange("A1:D1").format = headerFormat;
enumSheet.getRange(`A2:D${enumRows.length + 1}`).values = enumRows;
enumSheet.tables.add(`A1:D${enumRows.length + 1}`, true, "EnumCatalog");

for (const sheet of [summarySheet, coreSheet, supportingSheet, enumSheet]) {
  const used = sheet.getUsedRange();
  used.format.wrapText = true;
  used.format.verticalAlignment = "center";
  used.format.autofitColumns();
}

summarySheet.freezePanes.freezeRows(5);
coreSheet.freezePanes.freezeRows(1);
supportingSheet.freezePanes.freezeRows(1);
enumSheet.freezePanes.freezeRows(1);

coreSheet.getRange("A:A").format.columnWidthPx = 110;
coreSheet.getRange("B:B").format.columnWidthPx = 120;
coreSheet.getRange("C:C").format.columnWidthPx = 115;
coreSheet.getRange("D:F").format.columnWidthPx = 80;
coreSheet.getRange("G:G").format.columnWidthPx = 190;
coreSheet.getRange("H:H").format.columnWidthPx = 260;

supportingSheet.getRange("A:A").format.columnWidthPx = 150;
supportingSheet.getRange("B:B").format.columnWidthPx = 240;
supportingSheet.getRange("C:C").format.columnWidthPx = 320;

enumSheet.getRange("A:A").format.columnWidthPx = 130;
enumSheet.getRange("B:C").format.columnWidthPx = 90;
enumSheet.getRange("D:D").format.columnWidthPx = 220;

summarySheet.getRange("A5:C5").format = headerFormat;
summarySheet.getRange("E5:H5").format = headerFormat;
summarySheet.getRange("A13:C13").format = headerFormat;
summarySheet.getRange("A6:C10").format = { ...sectionHeaderFormat };
summarySheet.getRange("A14:C19").format = { ...sectionHeaderFormat };

await workbook.inspect({
  kind: "table",
  range: "CoreTables!A1:H26",
  include: "values",
  tableMaxRows: 26,
  tableMaxCols: 8,
});
await workbook.inspect({
  kind: "table",
  range: "Enums!A1:D20",
  include: "values",
  tableMaxRows: 20,
  tableMaxCols: 4,
});

await workbook.render({ sheetName: "Summary", range: "A1:H19", scale: 1.5, format: "png" });
await workbook.render({ sheetName: "CoreTables", range: "A1:H26", scale: 1.2, format: "png" });
await workbook.render({ sheetName: "SupportingTables", range: "A1:C16", scale: 1.2, format: "png" });
await workbook.render({ sheetName: "Enums", range: "A1:D20", scale: 1.2, format: "png" });

await fs.mkdir(outputDir, { recursive: true });
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);

console.log(outputPath);
