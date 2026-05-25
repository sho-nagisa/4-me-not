import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "C:/Users/keima/Desktop/4-me-not/outputs/test-plan-20260523";
const outputPath = `${outputDir}/4-me-not-test-plan.xlsx`;

const tests = [
  ["T-001", "タスク", "TaskService.extract_candidates_from_interaction", "やり取り本文/メモから候補TaskとTaskLinkが作られる", "バックグラウンド処理後にDB上のタスク候補と関連リンクが欠けないことを保証する", "P0", "Service integration", "人物・コミュニティ・トピック付きのやり取りをfixtureで作成"],
  ["T-002", "タスク", "TaskService.extract_candidates_from_interaction", "既存の未dismissed候補がある場合は重複作成しない", "同じやり取りから同じタスクが増殖する回帰を防ぐ", "P0", "Service integration", "pending/acceptedを既存データとして用意"],
  ["T-003", "タスク", "TaskService.extract_candidates_from_interaction", "dismissed済み候補は再抽出対象にできる", "dismiss後に内容を見直した場合の再提案仕様を固定する", "P1", "Service integration", "現実装はcandidate_status != dismissedのみ重複扱い"],
  ["T-004", "タスクAPI", "GET /api/tasks", "include_candidates=false と candidate_status の絞り込み", "タスク画面が候補/確定/却下を正しく分けて表示できることを保証する", "P0", "API integration", "複数statusのTaskをfixture化"],
  ["T-005", "タスクAPI", "POST /api/tasks/{id}/accept", "候補承認で is_candidate=false / candidate_status=accepted になる", "候補を正式タスク化する主要操作の回帰を防ぐ", "P0", "API integration", "SearchService.index_taskは必要ならpatchで呼び出し検証"],
  ["T-006", "タスクAPI", "POST /api/tasks/{id}/dismiss", "候補却下で candidate_status=dismissed になり検索対象から外れる", "却下済みタスクが一覧/検索に残る事故を防ぐ", "P0", "API integration", "index_task後のSearchDocument削除も確認"],
  ["T-007", "タスクAPI", "POST /api/tasks/{id}/accept|dismiss", "不正UUIDは400、存在しないTaskは404", "API利用側がエラーを判別できる契約を固定する", "P1", "API integration", "FastAPI TestClientで検証"],

  ["S-001", "検索", "SearchService.index_interaction", "やり取り保存後にinteraction/person/community/topic文書を作る", "検索インデックスに必要な関連文書が作られることを保証する", "P0", "Service integration", "SearchDocumentを直接確認"],
  ["S-002", "検索", "SearchService.index_interaction", "非表示人物/非表示コミュニティの文書は作られない、既存文書は消える", "非表示データが検索結果へ漏れる回帰を防ぐ", "P0", "Service integration", "hidden切替後に再index"],
  ["S-003", "検索API", "GET /api/search", "target_type の単体/複数指定で結果種別が絞られる", "検索UIのタブ/フィルタが期待通りに動くことを保証する", "P1", "API integration", "person/task/interactionを同時にfixture化"],
  ["S-004", "検索", "SearchService.rebuild_account_index", "people/communities/topics/interactions/tasks/calendar_events の件数と文書作成", "再構築スクリプトの信頼性を担保する", "P0", "Service integration", "戻り値とSearchDocument数を照合"],
  ["S-005", "検索", "SearchService.search", "空白クエリでは空レスポンスを返す", "サービス層を直接呼んだ時の防御動作を固定する", "P2", "Unit", "APIはQuery min_length=1のためservice単体"],
  ["S-006", "検索", "SearchService.index_task/search", "dismissedタスクは検索対象から外れる", "タスク却下後の検索ノイズを防ぐ", "P0", "Service integration", "T-006と連携してもよい"],
  ["S-007", "検索回答", "build_rag_answer", "人物候補のconfidence/evidence/follow_up_queriesを組み立てる", "検索回答の決定的ロジックを小さく固定する", "P2", "Unit", "DB不要の辞書fixtureで検証"],

  ["C-001", "カレンダーAPI", "POST /api/calendar-events", "人物参加者と表示名のみ参加者を含む予定を作成できる", "予定と参加者の保存/シリアライズ契約を固定する", "P0", "API integration", "person_idあり/なしのparticipantを混在"],
  ["C-002", "カレンダーAPI", "POST /api/calendar-events", "end_at < start_at は400", "不正な予定データの保存を防ぐ", "P0", "API integration", "境界条件として同時刻も仕様確認"],
  ["C-003", "カレンダーAPI", "POST /api/calendar-events", "存在しない/非表示人物のparticipantは404", "非表示人物や別アカウント人物の参照漏れを防ぐ", "P1", "API integration", "hidden person fixture"],
  ["C-004", "カレンダーAPI", "GET /api/calendar-events", "start_at降順とlimitが効く", "予定一覧の表示順と件数制御を保証する", "P1", "API integration", "複数予定を異なる日時で作成"],
  ["C-005", "カレンダー検索", "CalendarService.create_event", "作成後にSearchService.index_calendar_eventが呼ばれ検索できる", "予定がメモリ検索に含まれることを保証する", "P0", "Service/API integration", "SearchDocumentまたは検索結果で確認"],

  ["R-001", "参照データ", "POST /api/persons", "primary_community_id が存在しない/hiddenなら404", "人物が無効な所属を持たないことを保証する", "P0", "API integration", "hidden community fixture"],
  ["R-002", "参照データ", "POST /api/persons", "canonical_name重複時のエラー仕様を固定する", "DB IntegrityErrorが500として漏れるリスクを検出する", "P1", "API integration", "期待は409に寄せるのが自然"],
  ["R-003", "参照データ", "POST /api/communities", "空白名は400", "管理画面から空のコミュニティが作られないことを保証する", "P0", "API integration", "name='   '"],
  ["R-004", "参照データ", "POST /api/communities", "同名コミュニティは別親なら作成できる", "兄弟内だけ重複拒否する仕様を固定する", "P1", "API integration", "root A/root B配下に同名child"],
  ["R-005", "参照データ", "POST /api/communities", "hidden親の配下には作成できない", "非表示階層への新規データ混入を防ぐ", "P1", "API integration", "親をpatchでhidden化してから作成"],
  ["R-006", "参照データ", "GET /api/communities|persons", "hidden祖先があるpathのinclude_hidden true/false差分", "管理画面と通常画面のパス表示差分を固定する", "P1", "API integration", "親子階層を3段用意"],
  ["R-007", "参照データ", "POST /api/topics", "不正/存在しない親topicは400/404、pathが親子順", "トピック階層の参照整合性を保証する", "P2", "API integration", "TopicService pathも確認"],

  ["I-001", "やり取りAPI", "POST /api/interactions", "不正/存在しない/hidden人物は400/404", "非表示人物への記録や不正IDを防ぐ", "P0", "API integration", "record/list両方で確認"],
  ["I-002", "やり取りAPI", "POST /api/interactions", "不正/存在しない/hiddenコミュニティ・トピック参照を拒否", "参照整合性の崩れを防ぐ", "P0", "API integration", "community/topic別々に確認"],
  ["I-003", "やり取りAPI", "POST /api/interactions", "未対応interaction_type/share_levelは400", "入力値の正規化契約を固定する", "P0", "API integration", "aliasの正常系とは分ける"],
  ["I-004", "やり取りAPI", "GET /api/interactions", "date_from/date_toで期間絞り込み", "履歴検索の期間フィルタ回帰を防ぐ", "P1", "API integration", "境界日時を含む/含まないを確認"],
  ["I-005", "やり取りAPI", "GET /api/interactions", "occurred_at desc、同値ならcreated_at desc", "履歴とダッシュボードの新着順を固定する", "P1", "API integration", "日時を制御した複数record"],
  ["I-006", "やり取りAPI", "POST /api/interactions", "CALL/CHAT/OBSERVATIONなどaliasが正規化される", "旧UIや入力揺れを受け入れる仕様を固定する", "P2", "API integration", "serialize後のinteraction_typeを確認"],
  ["I-007", "人物ダッシュボード", "GET /api/persons/{id}/dashboard", "share_summary/top_topics/top_communities/recent_notesの集計", "会話準備画面の根幹データを保証する", "P1", "API integration", "SHARED/PARTIAL/WITHHELDを混在"],
  ["I-008", "概要API", "GET /api/interactions/overview", "hidden人物を除外しrecent_limit/person_limitが効く", "ホーム概要の表示漏れ/過剰表示を防ぐ", "P1", "API integration", "hidden person fixture"],

  ["M-001", "リマインダーAPI", "POST /api/reminders", "ISO日時/Z付き日時とmessageあり/なしで作成できる", "リマインダー作成の基本契約を固定する", "P1", "API integration", "DB上のremind_at/messageも確認"],
  ["M-002", "リマインダーAPI", "POST /api/reminders", "無効なremind_atは400または422で返す", "ValueErrorが500として漏れるリスクを検出する", "P1", "API integration", "期待仕様を決めて実装修正込み"],

  ["A-001", "アカウント分離", "get_current_account_id + 各Service", "別account_idのデータが一覧/検索/参照で混ざらない", "将来のマルチアカウント化で最重要のデータ分離を保証する", "P1", "Service/API integration", "account_contextをpatchして2アカウント分fixture化"],
  ["A-002", "テスト基盤", "DB/TestClient lifecycle", "テスト実行後にpsycopg未クローズ接続warningが出ない", "テスト信頼性とCIログ品質を上げる", "P2", "Test infrastructure", "現状ResourceWarningあり"],
  ["A-003", "テスト基盤", "fixtures/cleanup", "prefix依存cleanupを共通fixture化する", "テスト追加時の重複とデータ残りを減らす", "P2", "Test infrastructure", "unittestのsetUp/tearDownまたはhelper"],

  ["F-001", "フロントエンド", "テスト基盤", "Vitest + React Testing Libraryを導入する", "UIロジックの自動テストを追加できる状態にする", "P2", "Frontend setup", "現状frontendにテスト設定なし"],
  ["F-002", "フロントエンド", "interactionsApi", "APIリクエスト/レスポンス整形をテストする", "画面側がAPI契約変更に気づけるようにする", "P2", "Frontend unit", "fetch mock"],
  ["F-003", "フロントエンド", "RecordPage", "必須入力・送信payload・送信後状態をテストする", "記録フォームの主要導線を保護する", "P2", "Frontend component", "人物/コミュニティ/トピック選択をmock"],
  ["F-004", "フロントエンド", "TaskPage", "候補のaccept/dismiss操作と一覧更新をテストする", "タスク候補ワークフローのUI回帰を防ぐ", "P2", "Frontend component", "API mock"],
  ["F-005", "フロントエンド", "PersonPage/usePersonExplorer", "コミュニティ絞り込みと件数表示をテストする", "人物探索UIの表示ズレを防ぐ", "P3", "Frontend unit/component", "hookまたは画面単位"],
  ["F-006", "フロントエンド", "HistoryPage/SearchPage", "検索条件・ページング・結果なし表示をテストする", "履歴/検索の操作回帰を防ぐ", "P3", "Frontend component", "API mock"],

  ["E-001", "E2E", "記録→検索→人物ダッシュボード", "やり取りを記録し、検索結果と人物ダッシュボードに反映される", "ユーザー主要導線をブラウザ操作で保証する", "P2", "E2E", "Playwright等の導入が前提"],
  ["E-002", "E2E", "記録→タスク候補→承認/却下", "タスク候補の抽出から操作までを通す", "AI/抽出後処理を含む主要価値を確認する", "P3", "E2E", "バックグラウンド処理待ちの設計が必要"],
  ["E-003", "E2E", "予定作成→検索", "カレンダー予定を作成しメモリ検索で見つかる", "予定情報が記憶検索に入る導線を保証する", "P3", "E2E", "検索インデックス反映待ちを考慮"],
];

const priorityOrder = ["P0", "P1", "P2", "P3"];
const areaOrder = [
  "タスク",
  "タスクAPI",
  "検索",
  "検索API",
  "検索回答",
  "カレンダーAPI",
  "カレンダー検索",
  "参照データ",
  "やり取りAPI",
  "人物ダッシュボード",
  "概要API",
  "リマインダーAPI",
  "アカウント分離",
  "テスト基盤",
  "フロントエンド",
  "E2E",
];

const headers = ["ID", "領域", "対象", "テスト内容", "目的", "優先度", "種別", "前提/備考"];
const workbook = Workbook.create();
const overview = workbook.worksheets.add("概要");
const summary = workbook.worksheets.add("優先度サマリ");
const list = workbook.worksheets.add("テスト一覧");

for (const sheet of [overview, summary, list]) {
  sheet.showGridLines = false;
}

function styleTitle(sheet, range, title) {
  const titleRange = sheet.getRange(range);
  titleRange.merge();
  titleRange.values = [[title]];
  titleRange.format = {
    fill: "#1F4E79",
    font: { bold: true, color: "#FFFFFF", size: 16 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
  titleRange.format.rowHeightPx = 34;
}

function styleHeader(range, fill = "#5B9BD5") {
  range.format = {
    fill,
    font: { bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
  };
}

styleTitle(overview, "A1:H1", "4-me-not テスト拡充計画");
overview.getRange("A3:H3").merge();
overview.getRange("A3:H3").values = [["目的: 現状のバックエンド中心スモークテストを、リスクの高い機能別テストへ拡張するための実装予定一覧です。"]];
overview.getRange("A3:H3").format = {
  fill: "#EAF2F8",
  font: { color: "#1F2937" },
  wrapText: true,
  verticalAlignment: "center",
};
overview.getRange("A3:H3").format.rowHeightPx = 38;

overview.getRange("A5:B9").values = [
  ["総テストケース数", null],
  ["P0 件数", null],
  ["P1 件数", null],
  ["P2 件数", null],
  ["P3 件数", null],
];
overview.getRange("B5:B9").formulas = [
  ["=COUNTA('テスト一覧'!$A$2:$A$200)"],
  ["=COUNTIF('テスト一覧'!$F$2:$F$200,\"P0\")"],
  ["=COUNTIF('テスト一覧'!$F$2:$F$200,\"P1\")"],
  ["=COUNTIF('テスト一覧'!$F$2:$F$200,\"P2\")"],
  ["=COUNTIF('テスト一覧'!$F$2:$F$200,\"P3\")"],
];
overview.getRange("A5:B5").format = { fill: "#D9EAF7", font: { bold: true } };
overview.getRange("A6:A9").format = { fill: "#F5F7FA", font: { bold: true } };
overview.getRange("B5:B9").format = { horizontalAlignment: "center", font: { bold: true } };

overview.getRange("D5:H5").values = [["推奨着手順", "狙い", "主な対象", "完了条件", "備考"]];
styleHeader(overview.getRange("D5:H5"), "#3B6EA8");
overview.getRange("D6:H11").values = [
  ["1. P0 API/Service", "主要データの保存・検索・状態変更を固める", "タスク、検索、カレンダー、参照、やり取り", "P0が全件通る", "CI化前の最小防衛線"],
  ["2. P1 境界条件", "hidden、日付、重複、アカウント分離を固める", "参照、やり取り、予定、リマインダー", "P1が全件通る", "仕様未確定箇所は先に期待値を決める"],
  ["3. P2 テスト基盤/UI", "追加しやすい構造と最低限のUI回帰を作る", "fixtures、frontend、E2E入口", "frontend test commandが通る", "まず小さいhook/API clientから"],
  ["4. P3 E2E拡張", "主要ワークフローをブラウザで確認する", "記録、検索、候補、予定", "代表導線が安定して通る", "バックグラウンド待ちの扱いを設計"],
  ["補足", "既存13件は全件成功", "unittest + TestClient", "ResourceWarningは残存", "接続クローズも別途改善候補"],
  ["対象外", "現時点では性能/負荷テストは優先外", "DB/検索負荷", "必要になった段階で追加", "まず機能回帰を固める"],
];
overview.getRange("D6:H11").format = { wrapText: true, verticalAlignment: "top" };

styleTitle(summary, "A1:E1", "優先度サマリ");
summary.getRange("A3:E3").values = [["優先度", "件数", "主な目的", "対象領域", "推奨タイミング"]];
styleHeader(summary.getRange("A3:E3"), "#3B6EA8");
summary.getRange("A4:E7").values = [
  ["P0", null, "主要機能の保存・状態変更・検索漏れを防ぐ", "タスク、検索、カレンダー、参照、やり取り", "最初に実装"],
  ["P1", null, "境界条件、hidden、重複、日付、アカウント分離を固める", "API全般、リマインダー、ダッシュボード", "P0後すぐ"],
  ["P2", null, "純粋ロジック、テスト基盤、UIテストの入口を整える", "検索回答、fixtures、frontend、E2E入口", "CI整備と同時"],
  ["P3", null, "E2E拡張とUI詳細の回帰を増やす", "フロントエンド、E2E", "主要API安定後"],
];
summary.getRange("B4:B7").formulas = priorityOrder.map((p) => [`=COUNTIF('テスト一覧'!$F$2:$F$200,"${p}")`]);
summary.getRange("A4:A7").format = { font: { bold: true }, horizontalAlignment: "center" };
summary.getRange("B4:B7").format = { horizontalAlignment: "center" };
summary.getRange("C4:E7").format = { wrapText: true, verticalAlignment: "top" };

summary.getRange("G3:H3").values = [["優先度", "件数"]];
summary.getRange("G4:H7").formulas = priorityOrder.map((p, idx) => [`=A${idx + 4}`, `=B${idx + 4}`]);
const chart = summary.charts.add("bar", summary.getRange("G3:H7"));
chart.title = "優先度別テスト件数";
chart.hasLegend = false;
chart.xAxis = { axisType: "textAxis" };
chart.yAxis = { numberFormatCode: "0" };
chart.setPosition("G9", "M24");

styleTitle(list, "A1:H1", "実装予定テスト一覧");
list.getRange("A2:H2").values = [headers];
styleHeader(list.getRange("A2:H2"), "#3B6EA8");
list.getRangeByIndexes(2, 0, tests.length, headers.length).values = tests;
list.tables.add(`A2:H${tests.length + 2}`, true, "PlannedTests");
list.freezePanes.freezeRows(2);

list.getRange(`A3:H${tests.length + 2}`).format = {
  wrapText: true,
  verticalAlignment: "top",
};
list.getRange(`A3:A${tests.length + 2}`).format = { font: { bold: true }, horizontalAlignment: "center" };
list.getRange(`F3:F${tests.length + 2}`).format = { horizontalAlignment: "center", font: { bold: true } };

for (const [priority, fill] of [
  ["P0", "#FCE4D6"],
  ["P1", "#FFF2CC"],
  ["P2", "#E2F0D9"],
  ["P3", "#EDEDED"],
]) {
  list.getRange(`F3:F${tests.length + 2}`).conditionalFormats.add("containsText", {
    text: priority,
    format: { fill },
  });
}

const areaCounts = areaOrder
  .map((area) => [area, tests.filter((row) => row[1] === area).length])
  .filter(([, count]) => count > 0);
summary.getRange("A10:B10").values = [["領域", "件数"]];
styleHeader(summary.getRange("A10:B10"), "#5B9BD5");
summary.getRangeByIndexes(10, 0, areaCounts.length, 2).values = areaCounts;
summary.getRange(`A11:B${10 + areaCounts.length}`).format = { wrapText: true };

const priorityNotes = [
  ["P0", "主要機能の回帰防止。先に追加する"],
  ["P1", "仕様の境界を固める。P0後に続ける"],
  ["P2", "保守性とUI回帰。基盤整備とセット"],
  ["P3", "安定後に広げるE2E/詳細UI"],
];
list.getRange("J2:K2").values = [["優先度", "意味"]];
styleHeader(list.getRange("J2:K2"), "#70AD47");
list.getRange("J3:K6").values = priorityNotes;
list.getRange("J3:K6").format = { wrapText: true };
list.getRange(`F3:F${tests.length + 2}`).dataValidation = {
  rule: { type: "list", values: priorityOrder },
};

for (const sheet of [overview, summary, list]) {
  const used = sheet.getUsedRange();
  used.format.font = { name: "Yu Gothic", size: 10 };
}

overview.getRange("A:A").format.columnWidthPx = 150;
overview.getRange("B:B").format.columnWidthPx = 90;
overview.getRange("C:C").format.columnWidthPx = 18;
overview.getRange("D:D").format.columnWidthPx = 150;
overview.getRange("E:E").format.columnWidthPx = 210;
overview.getRange("F:F").format.columnWidthPx = 190;
overview.getRange("G:G").format.columnWidthPx = 160;
overview.getRange("H:H").format.columnWidthPx = 190;
overview.getRange("D6:H11").format.rowHeightPx = 54;

summary.getRange("A:A").format.columnWidthPx = 90;
summary.getRange("B:B").format.columnWidthPx = 70;
summary.getRange("C:C").format.columnWidthPx = 300;
summary.getRange("D:D").format.columnWidthPx = 260;
summary.getRange("E:E").format.columnWidthPx = 150;
summary.getRange("G:H").format.columnWidthPx = 85;
summary.getRange("A4:E7").format.rowHeightPx = 48;
summary.getRange(`A11:B${10 + areaCounts.length}`).format.rowHeightPx = 24;

list.getRange("A:A").format.columnWidthPx = 70;
list.getRange("B:B").format.columnWidthPx = 120;
list.getRange("C:C").format.columnWidthPx = 220;
list.getRange("D:D").format.columnWidthPx = 330;
list.getRange("E:E").format.columnWidthPx = 340;
list.getRange("F:F").format.columnWidthPx = 70;
list.getRange("G:G").format.columnWidthPx = 130;
list.getRange("H:H").format.columnWidthPx = 260;
list.getRange("J:J").format.columnWidthPx = 80;
list.getRange("K:K").format.columnWidthPx = 260;
list.getRange(`A3:H${tests.length + 2}`).format.rowHeightPx = 46;

const overviewCheck = await workbook.inspect({
  kind: "table",
  range: "概要!A1:H11",
  include: "values,formulas",
  tableMaxRows: 15,
  tableMaxCols: 8,
  maxChars: 4000,
});
console.log(overviewCheck.ndjson);

const listCheck = await workbook.inspect({
  kind: "table",
  range: "テスト一覧!A1:H12",
  include: "values",
  tableMaxRows: 12,
  tableMaxCols: 8,
  maxChars: 5000,
});
console.log(listCheck.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "formula error scan",
  maxChars: 2000,
});
console.log(errors.ndjson);

for (const sheetName of ["概要", "優先度サマリ", "テスト一覧"]) {
  const preview = await workbook.render({
    sheetName,
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  await fs.writeFile(`${outputDir}/${sheetName}.png`, new Uint8Array(await preview.arrayBuffer()));
}

await fs.mkdir(outputDir, { recursive: true });
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(`saved ${outputPath}`);
