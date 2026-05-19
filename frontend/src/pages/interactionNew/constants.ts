import type {
  InteractionType,
  ManagePanelId,
  PageId,
  PersonPanelId,
  ShareLevel,
} from "./types";

export const interactionTypeOptions: Array<{
  value: InteractionType;
  label: string;
  description: string;
}> = [
  { value: "MEETING", label: "対面", description: "直接会って話した内容を記録します。" },
  { value: "CHAT", label: "会話", description: "雑談や立ち話を残します。" },
  { value: "CALL", label: "通話", description: "電話やオンライン通話の内容をまとめます。" },
  { value: "MESSAGE", label: "メッセージ", description: "テキストのやり取りを記録します。" },
  { value: "OBSERVATION", label: "出来事メモ", description: "その場で見たことや感じたことを残します。" },
];

export const shareLevelOptions: Array<{
  value: ShareLevel;
  label: string;
  description: string;
}> = [
  { value: "SHARED", label: "話した", description: "そのまま共有した内容です。" },
  { value: "PARTIAL", label: "一部だけ話した", description: "触れたが、全部は話していない内容です。" },
  { value: "WITHHELD", label: "話していない", description: "今回はまだ話していない内容です。" },
];

export const pageOptions: Array<{
  id: PageId;
  label: string;
  mobileLabel: string;
  description: string;
}> = [
  { id: "home", label: "ホーム", mobileLabel: "ホーム", description: "全体の様子を見る" },
  { id: "record", label: "記録", mobileLabel: "記録", description: "会話を記録する" },
  { id: "search", label: "思い出す検索", mobileLabel: "検索", description: "曖昧な記憶から探す" },
  { id: "history", label: "履歴", mobileLabel: "履歴", description: "条件で絞って探す" },
  { id: "person", label: "人物", mobileLabel: "人物", description: "人ごとに整理する" },
  { id: "manage", label: "管理", mobileLabel: "管理", description: "候補と階層を整える" },
];

export const mobilePageOrder: PageId[] = [
  "record",
  "search",
  "home",
  "person",
  "manage",
];
export const mobilePageOptions = mobilePageOrder
  .map((pageId) => pageOptions.find((page) => page.id === pageId))
  .filter((page): page is (typeof pageOptions)[number] => Boolean(page));

export const personPanelOptions: Array<{
  id: PersonPanelId;
  label: string;
}> = [
  { id: "summary", label: "概要" },
  { id: "topics", label: "話題と場" },
  { id: "notes", label: "補足メモ" },
  { id: "recent", label: "最近の記録" },
];

export const managePanelOptions: Array<{
  id: ManagePanelId;
  label: string;
}> = [
  { id: "people", label: "人" },
  { id: "communities", label: "コミュニティ" },
  { id: "topics", label: "話題" },
];
