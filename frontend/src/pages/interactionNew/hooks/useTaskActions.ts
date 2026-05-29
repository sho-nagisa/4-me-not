import { useCallback, type Dispatch, type SetStateAction } from "react";

import {
  acceptTaskCandidate,
  completeTask,
  createTask,
  dismissTaskCandidate,
  reopenTask,
  updateTask,
} from "../interactionsApi";
import type { SearchScope } from "../SearchPage";
import type { CreateTaskPayload, UpdateTaskPayload } from "../types";

type UseTaskActionsParams = {
  setTaskActionId: Dispatch<SetStateAction<string | null>>;
  loadTaskCandidateList: () => Promise<void>;
  loadTaskList: () => Promise<void>;
  searchQuery: string;
  searchScope: SearchScope;
  runSearch: (query?: string, scope?: SearchScope) => Promise<void>;
  taskSearchQuery: string;
  runTaskSearch: (query?: string) => Promise<void>;
  onError: (message: string) => void;
  onSuccess: (message: string) => void;
};

export function useTaskActions({
  setTaskActionId,
  loadTaskCandidateList,
  loadTaskList,
  searchQuery,
  searchScope,
  runSearch,
  taskSearchQuery,
  runTaskSearch,
  onError,
  onSuccess,
}: UseTaskActionsParams) {
  const refreshTaskCandidateState = useCallback(async () => {
    await loadTaskCandidateList();
    await loadTaskList();
    if (searchQuery.trim()) {
      await runSearch(searchQuery, searchScope);
    }
    if (taskSearchQuery.trim()) {
      await runTaskSearch(taskSearchQuery);
    }
  }, [
    loadTaskCandidateList,
    loadTaskList,
    runSearch,
    runTaskSearch,
    searchQuery,
    searchScope,
    taskSearchQuery,
  ]);

  const handleAcceptTaskCandidate = useCallback(
    async (taskId: string) => {
      setTaskActionId(taskId);
      try {
        await acceptTaskCandidate(taskId);
        await refreshTaskCandidateState();
        onSuccess("タスク候補を採用しました。");
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "タスク候補の採用に失敗しました。";
        onError(message);
      } finally {
        setTaskActionId(null);
      }
    },
    [onError, onSuccess, refreshTaskCandidateState, setTaskActionId]
  );

  const handleDismissTaskCandidate = useCallback(
    async (taskId: string) => {
      setTaskActionId(taskId);
      try {
        await dismissTaskCandidate(taskId);
        await refreshTaskCandidateState();
        onSuccess("タスク候補を却下しました。");
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "タスク候補の却下に失敗しました。";
        onError(message);
      } finally {
        setTaskActionId(null);
      }
    },
    [onError, onSuccess, refreshTaskCandidateState, setTaskActionId]
  );

  const handleCreateTask = useCallback(
    async (payload: CreateTaskPayload) => {
      setTaskActionId("new-task");
      try {
        await createTask(payload);
        await refreshTaskCandidateState();
        onSuccess("タスクを作成しました。");
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "タスクの作成に失敗しました。";
        onError(message);
        throw error;
      } finally {
        setTaskActionId(null);
      }
    },
    [onError, onSuccess, refreshTaskCandidateState, setTaskActionId]
  );

  const handleUpdateTask = useCallback(
    async (taskId: string, payload: UpdateTaskPayload) => {
      setTaskActionId(taskId);
      try {
        await updateTask(taskId, payload);
        await refreshTaskCandidateState();
        onSuccess("タスクを更新しました。");
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "タスクの更新に失敗しました。";
        onError(message);
        throw error;
      } finally {
        setTaskActionId(null);
      }
    },
    [onError, onSuccess, refreshTaskCandidateState, setTaskActionId]
  );

  const handleCompleteTask = useCallback(
    async (taskId: string) => {
      setTaskActionId(taskId);
      try {
        await completeTask(taskId);
        await refreshTaskCandidateState();
        onSuccess("タスクを完了しました。");
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "タスクの完了に失敗しました。";
        onError(message);
      } finally {
        setTaskActionId(null);
      }
    },
    [onError, onSuccess, refreshTaskCandidateState, setTaskActionId]
  );

  const handleReopenTask = useCallback(
    async (taskId: string) => {
      setTaskActionId(taskId);
      try {
        await reopenTask(taskId);
        await refreshTaskCandidateState();
        onSuccess("タスクを未完了に戻しました。");
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "タスクの未完了化に失敗しました。";
        onError(message);
      } finally {
        setTaskActionId(null);
      }
    },
    [onError, onSuccess, refreshTaskCandidateState, setTaskActionId]
  );

  return {
    refreshTaskCandidateState,
    handleAcceptTaskCandidate,
    handleDismissTaskCandidate,
    handleCreateTask,
    handleUpdateTask,
    handleCompleteTask,
    handleReopenTask,
  };
}
