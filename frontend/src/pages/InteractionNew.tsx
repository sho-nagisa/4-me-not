import { useCallback, useEffect, useRef, useState } from "react";

import { useIsMobile } from "../hooks/useIsMobile";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import {
  interactionTypeOptions,
  shareLevelOptions,
} from "./interactionNew/constants";
import type {
  AuthAccount,
  CreateInteractionPayload,
  HomeViewProps,
  ManagePanelId,
  PageId,
  PersonDashboard,
  PersonPanelId,
} from "./interactionNew/types";
import { DesktopHome, MobileHome } from "./interactionNew/components";
import { HistoryPage } from "./interactionNew/HistoryPage";
import {
  createInteraction,
  getPersonDashboard,
} from "./interactionNew/interactionsApi";
import { ManagePage } from "./interactionNew/ManagePage";
import {
  enqueuePendingInteraction,
  getPendingInteractionCount,
  getPendingInteractions,
  syncPendingInteractions,
} from "./interactionNew/offlineInteractions";
import {
  relationSearchScopeOptions,
  type WorkspaceMode,
} from "./interactionNew/navigation";
import { PersonPage } from "./interactionNew/PersonPage";
import { RecordPage } from "./interactionNew/RecordPage";
import { SearchPage } from "./interactionNew/SearchPage";
import { TaskPage, type TaskPanelId } from "./interactionNew/TaskPage";
import {
  InteractionNewLayout,
  type FeedbackState,
} from "./interactionNew/InteractionNewLayout";
import { buildPersonBubblesFromCounts } from "./interactionNew/utils";
import { useInteractionHistory } from "./interactionNew/hooks/useInteractionHistory";
import { useManageReferenceActions } from "./interactionNew/hooks/useManageReferenceActions";
import { useMemorySearch } from "./interactionNew/hooks/useMemorySearch";
import { usePersonExplorer } from "./interactionNew/hooks/usePersonExplorer";
import { useRecordForm } from "./interactionNew/hooks/useRecordForm";
import { useRelationData } from "./interactionNew/hooks/useRelationData";
import { useTaskActions } from "./interactionNew/hooks/useTaskActions";
import { useTaskWorkspace } from "./interactionNew/hooks/useTaskWorkspace";

export default function InteractionNew({
  account,
  onLogout,
}: {
  account: AuthAccount;
  onLogout: () => Promise<void>;
}) {
  const isMobile = useIsMobile(820);
  const isOnline = useOnlineStatus();

  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>("relations");
  const [currentPage, setCurrentPage] = useState<PageId>("home");
  const [taskPanel, setTaskPanel] = useState<TaskPanelId>("overview");
  const [personPanel, setPersonPanel] = useState<PersonPanelId>("summary");
  const [managePanel, setManagePanel] = useState<ManagePanelId>("people");
  const [mobileRecordPanel, setMobileRecordPanel] = useState<"input" | "check">("input");
  const mobileRecordSwipeRef = useRef<HTMLDivElement | null>(null);

  const {
    occurredAt,
    setOccurredAt,
    personId,
    setPersonId,
    communityId,
    setCommunityId,
    communityTouched,
    setCommunityTouched,
    topicId,
    setTopicId,
    interactionType,
    setInteractionType,
    shareLevel,
    setShareLevel,
    content,
    setContent,
    note,
    setNote,
    buildInteractionPayload,
    resetRecordForm,
  } = useRecordForm();

  const [recordDashboardLoading, setRecordDashboardLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const [feedback, setFeedback] = useState<FeedbackState>(null);
  const [pendingInteractionCount, setPendingInteractionCount] = useState(
    getPendingInteractionCount
  );
  const [isSyncingInteractions, setIsSyncingInteractions] = useState(false);
  const isSyncingInteractionsRef = useRef(false);

  const [recordDashboard, setRecordDashboard] = useState<PersonDashboard | null>(null);

  const setError = useCallback((message: string) => {
    setFeedback({ tone: "error", message });
  }, []);

  const setSuccess = useCallback((message: string) => {
    setFeedback({ tone: "success", message });
  }, []);

  const {
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
  } = useTaskWorkspace({ onError: setError });

  const {
    historyItems,
    historyPage,
    historyTotalCount,
    historyPageSize,
    historyLoading,
    historyFilterOpen,
    setHistoryFilterOpen,
    historyPersonId,
    setHistoryPersonId,
    historyCommunityId,
    setHistoryCommunityId,
    historyTopicId,
    setHistoryTopicId,
    historyShareLevel,
    setHistoryShareLevel,
    historySearch,
    setHistorySearch,
    historyDateFrom,
    setHistoryDateFrom,
    historyDateTo,
    setHistoryDateTo,
    loadHistory,
    clearHistoryFilters,
    selectedHistoryLevelLabel,
  } = useInteractionHistory({
    currentPage,
    onError: setError,
  });

  const {
    persons,
    communities,
    managedPersons,
    managedCommunities,
    topics,
    overview,
    loading,
    loadOptions,
    loadManageData,
    loadOverviewInteractions,
  } = useRelationData({
    personId,
    setPersonId,
    setCommunityId,
    setCommunityTouched,
    historyPersonId,
    setHistoryPersonId,
    onError: setError,
  });

  const {
    detailPersonId,
    setDetailPersonId,
    detailCommunityId,
    setDetailCommunityId,
    detailDashboard,
    detailDashboardLoading,
    detailPersonCountsLoading,
    detailPersonBubbles,
    detailPersons,
    selectedDetailPerson,
    loadDetailDashboard,
    loadDetailPersonCounts,
    refreshPersonExplorer,
  } = usePersonExplorer({
    currentPage,
    persons,
    onError: setError,
  });

  const {
    searchQuery,
    setSearchQuery,
    searchScope,
    setSearchScope,
    searchDateFrom,
    setSearchDateFrom,
    searchDateTo,
    setSearchDateTo,
    searchFuzzy,
    setSearchFuzzy,
    searchResult,
    searchError,
    searchLoading,
    runSearch,
  } = useMemorySearch({ workspaceMode });

  const {
    handleAcceptTaskCandidate,
    handleDismissTaskCandidate,
    handleCreateTask,
    handleUpdateTask,
    handleCompleteTask,
    handleReopenTask,
  } = useTaskActions({
    setTaskActionId,
    loadTaskCandidateList,
    loadTaskList,
    searchQuery,
    searchScope,
    runSearch,
    taskSearchQuery,
    runTaskSearch,
    onError: setError,
    onSuccess: setSuccess,
  });

  const selectedPerson = persons.find((person) => person.id === personId);
  const selectedType = interactionTypeOptions.find(
    (option) => option.value === interactionType
  );
  const selectedShareLevel = shareLevelOptions.find(
    (option) => option.value === shareLevel
  );

  const queueInteractionForLater = (payload: CreateInteractionPayload) => {
    enqueuePendingInteraction(payload);
    setPendingInteractionCount(getPendingInteractionCount());
    resetRecordForm();
  };

  const shouldQueueAfterSaveError = (error: unknown) =>
    !isOnline || error instanceof TypeError;

  const toggleWorkspaceMode = () => {
    setWorkspaceMode((currentMode) => {
      const nextMode: WorkspaceMode = currentMode === "relations" ? "tasks" : "relations";
      if (nextMode === "tasks") {
        setTaskPanel("overview");
      } else {
        setCurrentPage("home");
      }
      return nextMode;
    });
  };

  useEffect(() => {
    if (!feedback || feedback.tone === "info") return;

    const timer = window.setTimeout(
      () => setFeedback(null),
      feedback.tone === "error" ? 6000 : 3600
    );

    return () => window.clearTimeout(timer);
  }, [feedback]);

  const loadRecordDashboard = async (targetPersonId: string) => {
    if (!targetPersonId) {
      setRecordDashboard(null);
      return;
    }

    setRecordDashboardLoading(true);
    try {
      const dashboard = await getPersonDashboard(targetPersonId);
      setRecordDashboard(dashboard);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "会話前の確認情報を取得できませんでした。";
      setError(message);
    } finally {
      setRecordDashboardLoading(false);
    }
  };

  useEffect(() => {
    void loadOptions();
    void loadOverviewInteractions();
  }, []);

  useEffect(() => {
    if (currentPage === "manage") {
      void loadManageData();
    }
  }, [currentPage]);

  useEffect(() => {
    if (workspaceMode === "tasks") {
      void loadTaskCandidateList();
      void loadTaskList();
    }
  }, [workspaceMode]);

  useEffect(() => {
    if (currentPage === "record") {
      void loadRecordDashboard(personId);
    }
  }, [currentPage, personId]);

  const refreshAll = async () => {
    await loadOptions();
    await loadOverviewInteractions();

    if (currentPage === "manage") {
      await loadManageData();
    }
    if (currentPage === "history") {
      await loadHistory(historyPage);
    }
    if (currentPage === "record" && personId) {
      await loadRecordDashboard(personId);
    }
    if (currentPage === "person") {
      await refreshPersonExplorer();
    }
    if (currentPage === "search") {
      await loadTaskCandidateList();
    }
    if (workspaceMode === "tasks") {
      await loadTaskList();
    }
  };

  const {
    newPersonName,
    setNewPersonName,
    newPersonPrimaryCommunityId,
    setNewPersonPrimaryCommunityId,
    newCommunityName,
    setNewCommunityName,
    newCommunityParentId,
    setNewCommunityParentId,
    newTopicName,
    setNewTopicName,
    newTopicParentId,
    setNewTopicParentId,
    isCreatingPerson,
    isCreatingCommunity,
    isCreatingTopic,
    personActionId,
    communityActionId,
    handleCreatePerson,
    handleCreateCommunity,
    handleCreateTopic,
    handleTogglePersonHidden,
    handleDeletePerson,
    handleToggleCommunityHidden,
    handleDeleteCommunity,
  } = useManageReferenceActions({
    refreshAll,
    setPersonId,
    setDetailPersonId,
    setCurrentPage,
    setManagePanel,
    setCommunityId,
    setTopicId,
    onError: setError,
    onSuccess: setSuccess,
  });

  useEffect(() => {
    if (!isOnline || isSyncingInteractionsRef.current) {
      return;
    }

    const pendingItems = getPendingInteractions();
    setPendingInteractionCount(pendingItems.length);
    if (pendingItems.length === 0) {
      return;
    }

    let cancelled = false;

    const runPendingInteractionSync = async () => {
      isSyncingInteractionsRef.current = true;
      setIsSyncingInteractions(true);
      let sentCount = 0;

      try {
        sentCount = await syncPendingInteractions(
          async (payload) => {
            if (cancelled) {
              throw new Error("Sync cancelled");
            }

            await createInteraction(payload);
          },
          () => setPendingInteractionCount(getPendingInteractionCount())
        );

        if (!cancelled && sentCount > 0) {
          setSuccess(`未送信の記録 ${sentCount}件を送信しました。`);
          await refreshAll();
        }
      } catch {
        if (!cancelled && sentCount > 0) {
          await refreshAll();
        }
        if (!cancelled) {
          setError("未送信の自動送信に失敗しました。接続が安定したら再試行します。");
          setPendingInteractionCount(getPendingInteractionCount());
        }
      } finally {
        isSyncingInteractionsRef.current = false;
        if (!cancelled) {
          setIsSyncingInteractions(false);
        }
      }
    };

    void runPendingInteractionSync();

    return () => {
      cancelled = true;
    };
  }, [isOnline]);

  const handlePersonChange = (nextPersonId: string) => {
    setPersonId(nextPersonId);
    const nextPerson = persons.find((person) => person.id === nextPersonId);
    setCommunityId(nextPerson?.primary_community_id ?? "");
    setCommunityTouched(false);
  };

  const openRecordForPerson = (nextPersonId: string) => {
    handlePersonChange(nextPersonId);
    setCurrentPage("record");
  };

  const openPersonFromSearch = (nextPersonId: string) => {
    setDetailPersonId(nextPersonId);
    setPersonPanel("summary");
    setCurrentPage("person");
  };

  const handleSubmit = async () => {
    if (!personId || !content.trim()) {
      setError("相手と内容は必須です。");
      return;
    }

    const payload = buildInteractionPayload();

    if (!isOnline) {
      queueInteractionForLater(payload);
      setSuccess("オフラインのため未送信として保存しました。接続が戻ると自動送信します。");
      return;
    }

    setIsSaving(true);
    setFeedback({ tone: "info", message: "記録を保存しています..." });

    try {
      await createInteraction(payload);

      setSuccess("やり取りを保存しました。");
      resetRecordForm();
      await loadOverviewInteractions();
      if (currentPage === "history") {
        await loadHistory(historyPage);
      }
      if (currentPage === "person") {
        await loadDetailPersonCounts(detailCommunityId);
      }
      if (currentPage === "record") {
        await loadRecordDashboard(personId);
      }
      if (currentPage === "person" && detailPersonId === personId) {
        await loadDetailDashboard(personId);
      }
    } catch (error) {
      if (shouldQueueAfterSaveError(error)) {
        queueInteractionForLater(payload);
        setSuccess("通信できないため未送信として保存しました。接続が戻ると自動送信します。");
        return;
      }

      const message =
        error instanceof Error ? error.message : "保存に失敗しました。";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const homeRecentInteractions = overview.recent_interactions;
  const homePersonBubbles = buildPersonBubblesFromCounts(
    persons,
    overview.person_counts
  );

  const switchMobileRecordPanel = (panel: "input" | "check") => {
    setMobileRecordPanel(panel);
    const container = mobileRecordSwipeRef.current;
    if (!container) return;

    container.scrollTo({
      left: panel === "input" ? 0 : container.clientWidth,
      behavior: "smooth",
    });
  };

  const handleMobileRecordScroll = () => {
    const container = mobileRecordSwipeRef.current;
    if (!container) return;

    const nextPanel =
      container.scrollLeft > container.clientWidth * 0.5 ? "check" : "input";
    setMobileRecordPanel(nextPanel);
  };

  const renderHomePage = () => {
    const props: HomeViewProps = {
      personBubbles: homePersonBubbles,
      selectedPersonId: detailPersonId,
      recentInteractions: homeRecentInteractions,
      onBubbleSelect: openRecordForPerson,
      onOpenHistory: () => setCurrentPage("history"),
      onOpenRecord: () => setCurrentPage("record"),
    };

    return isMobile ? <MobileHome {...props} /> : <DesktopHome {...props} />;
  };

  const renderPage = () => {
    if (workspaceMode === "tasks") {
      return (
        <TaskPage
          panel={taskPanel}
          setPanel={setTaskPanel}
          tasks={taskItems}
          tasksLoading={taskItemsLoading}
          taskCandidates={taskCandidates}
          taskCandidatesLoading={taskCandidatesLoading}
          taskActionId={taskActionId}
          onAcceptTaskCandidate={handleAcceptTaskCandidate}
          onDismissTaskCandidate={handleDismissTaskCandidate}
          onCreateTask={handleCreateTask}
          onUpdateTask={handleUpdateTask}
          onCompleteTask={handleCompleteTask}
          onReopenTask={handleReopenTask}
          searchQuery={taskSearchQuery}
          setSearchQuery={setTaskSearchQuery}
          searchDateFrom={taskSearchDateFrom}
          setSearchDateFrom={setTaskSearchDateFrom}
          searchDateTo={taskSearchDateTo}
          setSearchDateTo={setTaskSearchDateTo}
          searchFuzzy={taskSearchFuzzy}
          setSearchFuzzy={setTaskSearchFuzzy}
          searchLoading={taskSearchLoading}
          searchResult={taskSearchResult}
          searchError={taskSearchError}
          onSearch={runTaskSearch}
        />
      );
    }

    switch (currentPage) {
      case "record":
        return (
          <RecordPage
            isMobile={isMobile}
            mobileRecordPanel={mobileRecordPanel}
            mobileRecordSwipeRef={mobileRecordSwipeRef}
            onMobileRecordScroll={handleMobileRecordScroll}
            onSwitchMobileRecordPanel={switchMobileRecordPanel}
            occurredAt={occurredAt}
            setOccurredAt={setOccurredAt}
            personId={personId}
            onPersonChange={handlePersonChange}
            loading={loading}
            persons={persons}
            communityId={communityId}
            setCommunityId={setCommunityId}
            setCommunityTouched={setCommunityTouched}
            communities={communities}
            topicId={topicId}
            setTopicId={setTopicId}
            topics={topics}
            interactionType={interactionType}
            setInteractionType={setInteractionType}
            selectedType={selectedType}
            shareLevel={shareLevel}
            setShareLevel={setShareLevel}
            selectedShareLevel={selectedShareLevel}
            content={content}
            setContent={setContent}
            note={note}
            setNote={setNote}
            onSubmit={handleSubmit}
            isSaving={isSaving}
            communityTouched={communityTouched}
            selectedPerson={selectedPerson}
            recordDashboardLoading={recordDashboardLoading}
            recordDashboard={recordDashboard}
            isOnline={isOnline}
            pendingInteractionCount={pendingInteractionCount}
          />
        );
      case "search":
        return (
          <SearchPage
            query={searchQuery}
            setQuery={setSearchQuery}
            scope={searchScope}
            setScope={setSearchScope}
            scopeOptions={relationSearchScopeOptions}
            dateFrom={searchDateFrom}
            setDateFrom={setSearchDateFrom}
            dateTo={searchDateTo}
            setDateTo={setSearchDateTo}
            fuzzy={searchFuzzy}
            setFuzzy={setSearchFuzzy}
            loading={searchLoading}
            result={searchResult}
            error={searchError}
            onSearch={runSearch}
            onOpenPerson={openPersonFromSearch}
            onOpenRecordForPerson={openRecordForPerson}
            taskCandidates={taskCandidates}
            taskCandidatesLoading={taskCandidatesLoading}
            taskActionId={taskActionId}
            onAcceptTaskCandidate={handleAcceptTaskCandidate}
            onDismissTaskCandidate={handleDismissTaskCandidate}
            showTaskCandidates={false}
          />
        );
      case "history":
        return (
          <HistoryPage
            persons={persons}
            communities={communities}
            topics={topics}
            historyPersonId={historyPersonId}
            setHistoryPersonId={setHistoryPersonId}
            historyCommunityId={historyCommunityId}
            setHistoryCommunityId={setHistoryCommunityId}
            historyTopicId={historyTopicId}
            setHistoryTopicId={setHistoryTopicId}
            historyShareLevel={historyShareLevel}
            setHistoryShareLevel={setHistoryShareLevel}
            historySearch={historySearch}
            setHistorySearch={setHistorySearch}
            historyDateFrom={historyDateFrom}
            setHistoryDateFrom={setHistoryDateFrom}
            historyDateTo={historyDateTo}
            setHistoryDateTo={setHistoryDateTo}
            historyLoading={historyLoading}
            onLoadHistory={loadHistory}
            historyPage={historyPage}
            historyTotalCount={historyTotalCount}
            historyPageSize={historyPageSize}
            onHistoryPageChange={(nextPage) => void loadHistory(nextPage)}
            onClearHistoryFilters={clearHistoryFilters}
            historyFilterOpen={historyFilterOpen}
            setHistoryFilterOpen={setHistoryFilterOpen}
            selectedHistoryLevelLabel={selectedHistoryLevelLabel}
            historyItems={historyItems}
          />
        );
      case "person":
        return (
          <PersonPage
            detailDashboard={detailDashboard}
            selectedDetailPerson={selectedDetailPerson}
            detailPersonBubbles={detailPersonBubbles}
            detailPersonId={detailPersonId}
            onOpenRecordForPerson={openRecordForPerson}
            detailCommunityId={detailCommunityId}
            setDetailCommunityId={setDetailCommunityId}
            setPersonPanel={setPersonPanel}
            setDetailPersonId={setDetailPersonId}
            loading={loading || detailPersonCountsLoading}
            communities={communities}
            detailPersons={detailPersons}
            detailDashboardLoading={detailDashboardLoading}
            onLoadDetailDashboard={loadDetailDashboard}
            personPanel={personPanel}
          />
        );
      case "manage":
        return (
          <ManagePage
            managePanel={managePanel}
            setManagePanel={setManagePanel}
            managedPersons={managedPersons}
            managedCommunities={managedCommunities}
            communities={communities}
            topics={topics}
            newPersonName={newPersonName}
            setNewPersonName={setNewPersonName}
            newPersonPrimaryCommunityId={newPersonPrimaryCommunityId}
            setNewPersonPrimaryCommunityId={setNewPersonPrimaryCommunityId}
            newCommunityName={newCommunityName}
            setNewCommunityName={setNewCommunityName}
            newCommunityParentId={newCommunityParentId}
            setNewCommunityParentId={setNewCommunityParentId}
            newTopicName={newTopicName}
            setNewTopicName={setNewTopicName}
            newTopicParentId={newTopicParentId}
            setNewTopicParentId={setNewTopicParentId}
            isCreatingPerson={isCreatingPerson}
            isCreatingCommunity={isCreatingCommunity}
            isCreatingTopic={isCreatingTopic}
            onCreatePerson={handleCreatePerson}
            onCreateCommunity={handleCreateCommunity}
            onCreateTopic={handleCreateTopic}
            personActionId={personActionId}
            communityActionId={communityActionId}
            onTogglePersonHidden={handleTogglePersonHidden}
            onDeletePerson={handleDeletePerson}
            onToggleCommunityHidden={handleToggleCommunityHidden}
            onDeleteCommunity={handleDeleteCommunity}
          />
        );
      case "home":
      default:
        return renderHomePage();
    }
  };

  const openTaskCount = taskItems.filter((task) => task.status === "TODO").length;
  const dueSoonTaskCount = taskItems.filter((task) => {
    if (!task.due_at) return false;
    const dueAt = new Date(task.due_at).getTime();
    const now = Date.now();
    return dueAt >= now && dueAt <= now + 7 * 24 * 60 * 60 * 1000;
  }).length;

  return (
    <InteractionNewLayout
      isMobile={isMobile}
      workspaceMode={workspaceMode}
      currentPage={currentPage}
      setCurrentPage={setCurrentPage}
      taskPanel={taskPanel}
      setTaskPanel={setTaskPanel}
      relationSummary={{
        totalCount: overview.total_count,
        personCount: persons.length,
        communityCount: communities.length,
      }}
      taskSummary={{
        candidateCount: taskCandidates.length,
        openCount: openTaskCount,
        dueSoonCount: dueSoonTaskCount,
      }}
      feedback={feedback}
      accountEmail={account.email}
      isOnline={isOnline}
      pendingInteractionCount={pendingInteractionCount}
      isSyncingInteractions={isSyncingInteractions}
      onDismissFeedback={() => setFeedback(null)}
      onLogout={onLogout}
      onToggleWorkspaceMode={toggleWorkspaceMode}
    >
      {renderPage()}
    </InteractionNewLayout>
  );
}
