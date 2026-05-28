import { useCallback, useState } from "react";

import { listTaskCandidates, listTasks, searchMemory } from "../interactionsApi";
import type { SearchResponse, TaskRecord } from "../types";
import { buildDateQuery } from "../utils";

type UseTaskWorkspaceParams = {
  onError: (message: string) => void;
};

export function useTaskWorkspace({ onError }: UseTaskWorkspaceParams) {
  const [taskCandidates, setTaskCandidates] = useState<TaskRecord[]>([]);
  const [taskItems, setTaskItems] = useState<TaskRecord[]>([]);
  const [taskActionId, setTaskActionId] = useState<string | null>(null);
  const [taskCandidatesLoading, setTaskCandidatesLoading] = useState(false);
  const [taskItemsLoading, setTaskItemsLoading] = useState(false);
  const [taskSearchQuery, setTaskSearchQuery] = useState<string>("");
  const [taskSearchDateFrom, setTaskSearchDateFrom] = useState("");
  const [taskSearchDateTo, setTaskSearchDateTo] = useState("");
  const [taskSearchFuzzy, setTaskSearchFuzzy] = useState(true);
  const [taskSearchResult, setTaskSearchResult] =
    useState<SearchResponse | null>(null);
  const [taskSearchError, setTaskSearchError] = useState<string | null>(null);
  const [taskSearchLoading, setTaskSearchLoading] = useState(false);

  const loadTaskCandidateList = useCallback(async () => {
    setTaskCandidatesLoading(true);
    try {
      const items = await listTaskCandidates();
      setTaskCandidates(items);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "タスク候補の取得に失敗しました。";
      onError(message);
    } finally {
      setTaskCandidatesLoading(false);
    }
  }, [onError]);

  const loadTaskList = useCallback(async () => {
    setTaskItemsLoading(true);
    try {
      const items = await listTasks({ includeCandidates: false });
      setTaskItems(items);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "タスクの取得に失敗しました。";
      onError(message);
    } finally {
      setTaskItemsLoading(false);
    }
  }, [onError]);

  const runTaskSearch = useCallback(async (nextQuery = taskSearchQuery) => {
    const trimmedQuery = nextQuery.trim();
    if (!trimmedQuery) {
      setTaskSearchResult(null);
      setTaskSearchError(null);
      return;
    }

    setTaskSearchLoading(true);
    setTaskSearchError(null);
    try {
      const result = await searchMemory(trimmedQuery, ["task", "calendar_event"], {
        dateFrom: buildDateQuery(taskSearchDateFrom, "from"),
        dateTo: buildDateQuery(taskSearchDateTo, "to"),
        fuzzy: taskSearchFuzzy,
      });
      setTaskSearchResult(result);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "タスク検索に失敗しました。";
      setTaskSearchError(message);
    } finally {
      setTaskSearchLoading(false);
    }
  }, [taskSearchDateFrom, taskSearchDateTo, taskSearchFuzzy, taskSearchQuery]);

  return {
    taskCandidates,
    taskItems,
    taskActionId,
    setTaskActionId,
    taskCandidatesLoading,
    taskItemsLoading,
    taskSearchQuery,
    setTaskSearchQuery,
    taskSearchDateFrom,
    setTaskSearchDateFrom,
    taskSearchDateTo,
    setTaskSearchDateTo,
    taskSearchFuzzy,
    setTaskSearchFuzzy,
    taskSearchResult,
    taskSearchError,
    taskSearchLoading,
    loadTaskCandidateList,
    loadTaskList,
    runTaskSearch,
  };
}
