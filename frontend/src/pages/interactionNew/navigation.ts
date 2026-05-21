import type { SearchScope } from "./SearchPage";
import type { TaskPanelId } from "./TaskPage";
import type { SearchTargetType } from "./types";

export const HISTORY_DEFAULT_LIMIT = 30;

export type WorkspaceMode = "relations" | "tasks";

export const relationSearchScopeOptions: Array<{ id: SearchScope; label: string }> = [
  { id: "all", label: "すべて" },
  { id: "interaction", label: "会話" },
  { id: "person", label: "人物" },
  { id: "community", label: "団体" },
  { id: "topic", label: "話題" },
];

export const relationSearchTargetTypes: SearchTargetType[] = [
  "interaction",
  "person",
  "community",
  "topic",
];

export const taskPageOptions: Array<{
  id: TaskPanelId;
  label: string;
  mobileLabel: string;
  description: string;
}> = [
  {
    id: "overview",
    label: "タスク",
    mobileLabel: "タスク",
    description: "候補と未完了を見る",
  },
  {
    id: "search",
    label: "タスク検索",
    mobileLabel: "検索",
    description: "タスクと予定を探す",
  },
];
