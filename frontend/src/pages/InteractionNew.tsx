import { useCallback, useEffect, useRef, useState } from "react";

import { useIsMobile } from "../hooks/useIsMobile";
import {
  interactionTypeOptions,
  shareLevelOptions,
} from "./interactionNew/constants";
import type {
  Community,
  HomeViewProps,
  InteractionOverview,
  InteractionType,
  ManagePanelId,
  PageId,
  Person,
  PersonDashboard,
  PersonPanelId,
  SearchResponse,
  SearchTargetType,
  ShareLevel,
  Topic,
} from "./interactionNew/types";
import { DesktopHome, MobileHome } from "./interactionNew/components";
import { HistoryPage } from "./interactionNew/HistoryPage";
import {
  acceptTaskCandidate,
  createCommunity,
  createInteraction,
  createPerson,
  createTopic,
  deleteCommunity,
  deletePerson,
  dismissTaskCandidate,
  getInteractionOverview,
  getPersonDashboard,
  listCommunities,
  listPersons,
  listTopics,
  searchMemory,
  updateCommunityHidden,
  updatePersonHidden,
} from "./interactionNew/interactionsApi";
import { ManagePage } from "./interactionNew/ManagePage";
import {
  relationSearchScopeOptions,
  relationSearchTargetTypes,
  type WorkspaceMode,
} from "./interactionNew/navigation";
import { PersonPage } from "./interactionNew/PersonPage";
import { RecordPage } from "./interactionNew/RecordPage";
import { SearchPage, type SearchScope } from "./interactionNew/SearchPage";
import { TaskPage, type TaskPanelId } from "./interactionNew/TaskPage";
import {
  InteractionNewLayout,
  type FeedbackState,
} from "./interactionNew/InteractionNewLayout";
import {
  buildPersonBubblesFromCounts,
  toDateTimeLocalValue,
} from "./interactionNew/utils";
import { useInteractionHistory } from "./interactionNew/useInteractionHistory";
import { usePersonExplorer } from "./interactionNew/usePersonExplorer";
import { useTaskWorkspace } from "./interactionNew/useTaskWorkspace";

export default function InteractionNew() {
  const isMobile = useIsMobile(820);

  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>("relations");
  const [currentPage, setCurrentPage] = useState<PageId>("home");
  const [taskPanel, setTaskPanel] = useState<TaskPanelId>("overview");
  const [personPanel, setPersonPanel] = useState<PersonPanelId>("summary");
  const [managePanel, setManagePanel] = useState<ManagePanelId>("people");
  const [mobileRecordPanel, setMobileRecordPanel] = useState<"input" | "check">("input");
  const mobileRecordSwipeRef = useRef<HTMLDivElement | null>(null);

  const [persons, setPersons] = useState<Person[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [managedPersons, setManagedPersons] = useState<Person[]>([]);
  const [managedCommunities, setManagedCommunities] = useState<Community[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [overview, setOverview] = useState<InteractionOverview>({
    total_count: 0,
    recent_interactions: [],
    person_counts: [],
  });

  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [recordDashboardLoading, setRecordDashboardLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isCreatingPerson, setIsCreatingPerson] = useState(false);
  const [isCreatingCommunity, setIsCreatingCommunity] = useState(false);
  const [isCreatingTopic, setIsCreatingTopic] = useState(false);
  const [personActionId, setPersonActionId] = useState<string | null>(null);
  const [communityActionId, setCommunityActionId] = useState<string | null>(null);

  const [feedback, setFeedback] = useState<FeedbackState>(null);

  const [occurredAt, setOccurredAt] = useState<string>(toDateTimeLocalValue());
  const [personId, setPersonId] = useState<string>("");
  const [communityId, setCommunityId] = useState<string>("");
  const [communityTouched, setCommunityTouched] = useState(false);
  const [topicId, setTopicId] = useState<string>("");
  const [interactionType, setInteractionType] =
    useState<InteractionType>("MEETING");
  const [shareLevel, setShareLevel] = useState<ShareLevel>("SHARED");
  const [content, setContent] = useState<string>("");
  const [note, setNote] = useState<string>("");

  const [newPersonName, setNewPersonName] = useState("");
  const [newPersonPrimaryCommunityId, setNewPersonPrimaryCommunityId] = useState("");
  const [newCommunityName, setNewCommunityName] = useState("");
  const [newCommunityParentId, setNewCommunityParentId] = useState("");
  const [newTopicName, setNewTopicName] = useState("");
  const [newTopicParentId, setNewTopicParentId] = useState("");

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchScope, setSearchScope] = useState<SearchScope>("all");
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
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

  const selectedPerson = persons.find((person) => person.id === personId);
  const selectedType = interactionTypeOptions.find(
    (option) => option.value === interactionType
  );
  const selectedShareLevel = shareLevelOptions.find(
    (option) => option.value === shareLevel
  );

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

  const loadOptions = async () => {
    setLoading(true);
    try {
      const [personsJson, communitiesJson, topicsJson] = await Promise.all([
        listPersons(),
        listCommunities(),
        listTopics(),
      ]);

      setPersons(personsJson);
      setCommunities(communitiesJson);
      setTopics(topicsJson);

      const fallbackPerson = personsJson[0] ?? null;
      const currentRecordPerson =
        personsJson.find((person) => person.id === personId) ?? fallbackPerson;
      const currentHistoryPerson =
        personsJson.find((person) => person.id === historyPersonId) ?? null;

      if (!personId || !currentRecordPerson) {
        setPersonId(currentRecordPerson?.id ?? "");
        setCommunityId(currentRecordPerson?.primary_community_id ?? "");
        setCommunityTouched(false);
      }

      if (historyPersonId && !currentHistoryPerson) {
        setHistoryPersonId("");
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "初期データの読み込みに失敗しました。";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const loadManageData = async () => {
    try {
      const [personsJson, communitiesJson] = await Promise.all([
        listPersons(true),
        listCommunities(true),
      ]);

      setManagedPersons(personsJson);
      setManagedCommunities(communitiesJson);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "管理データの読み込みに失敗しました。";
      setError(message);
    }
  };

  const loadOverviewInteractions = async () => {
    try {
      const items = await getInteractionOverview();
      setOverview(items);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "全体の履歴取得に失敗しました。";
      setError(message);
    }
  };

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

  const runSearch = async (
    nextQuery = searchQuery,
    nextScope = searchScope
  ) => {
    const trimmedQuery = nextQuery.trim();
    if (!trimmedQuery) {
      setSearchResult(null);
      setSearchError(null);
      return;
    }

    const relationScope = relationSearchScopeOptions.some(
      (option) => option.id === nextScope
    )
      ? nextScope
      : "all";
    const targetTypes: SearchTargetType[] =
      relationScope === "all" ? relationSearchTargetTypes : [relationScope];

    setSearchLoading(true);
    setSearchError(null);
    try {
      const result = await searchMemory(trimmedQuery, targetTypes);
      setSearchResult(result);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "検索に失敗しました。";
      setSearchError(message);
    } finally {
      setSearchLoading(false);
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
    if (
      workspaceMode === "relations" &&
      !relationSearchScopeOptions.some((option) => option.id === searchScope)
    ) {
      setSearchScope("all");
    }
  }, [workspaceMode, searchScope]);

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

  const refreshTaskCandidateState = async () => {
    await loadTaskCandidateList();
    await loadTaskList();
    if (searchQuery.trim()) {
      await runSearch(searchQuery, searchScope);
    }
    if (taskSearchQuery.trim()) {
      await runTaskSearch(taskSearchQuery);
    }
  };

  const handleAcceptTaskCandidate = async (taskId: string) => {
    setTaskActionId(taskId);
    try {
      await acceptTaskCandidate(taskId);
      await refreshTaskCandidateState();
      setSuccess("タスク候補を採用しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "タスク候補の採用に失敗しました。";
      setError(message);
    } finally {
      setTaskActionId(null);
    }
  };

  const handleDismissTaskCandidate = async (taskId: string) => {
    setTaskActionId(taskId);
    try {
      await dismissTaskCandidate(taskId);
      await refreshTaskCandidateState();
      setSuccess("タスク候補を却下しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "タスク候補の却下に失敗しました。";
      setError(message);
    } finally {
      setTaskActionId(null);
    }
  };

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

    setIsSaving(true);
    setFeedback({ tone: "info", message: "記録を保存しています..." });

    try {
      await createInteraction({
        occurred_at: occurredAt,
        person_id: personId,
        community_id: communityId || null,
        topic_id: topicId || null,
        interaction_type: interactionType,
        share_level: shareLevel,
        content,
        note,
      });

      setSuccess("やり取りを保存しました。");
      setOccurredAt(toDateTimeLocalValue());
      setContent("");
      setNote("");
      setCommunityTouched(false);
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
      const message =
        error instanceof Error ? error.message : "保存に失敗しました。";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreatePerson = async () => {
    if (!newPersonName.trim()) {
      setError("追加する人の名前を入力してください。");
      return;
    }

    setIsCreatingPerson(true);
    try {
      const person = await createPerson({
        name: newPersonName.trim(),
        primary_community_id: newPersonPrimaryCommunityId || null,
      });
      setNewPersonName("");
      setNewPersonPrimaryCommunityId("");
      await refreshAll();
      setPersonId(person.id);
      setDetailPersonId(person.id);
      setCurrentPage("manage");
      setManagePanel("people");
      setSuccess("人を追加しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "人の追加に失敗しました。";
      setError(message);
    } finally {
      setIsCreatingPerson(false);
    }
  };

  const handleCreateCommunity = async () => {
    if (!newCommunityName.trim()) {
      setError("追加するコミュニティ名を入力してください。");
      return;
    }

    setIsCreatingCommunity(true);
    try {
      const community = await createCommunity({
        name: newCommunityName.trim(),
        parent_id: newCommunityParentId || null,
      });
      setNewCommunityName("");
      setNewCommunityParentId("");
      await refreshAll();
      setCommunityId(community.id);
      setSuccess("コミュニティを追加しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "コミュニティの追加に失敗しました。";
      setError(message);
    } finally {
      setIsCreatingCommunity(false);
    }
  };

  const handleCreateTopic = async () => {
    if (!newTopicName.trim()) {
      setError("追加する話題名を入力してください。");
      return;
    }

    setIsCreatingTopic(true);
    try {
      const topic = await createTopic({
        name: newTopicName.trim(),
        parent_id: newTopicParentId || null,
      });
      setNewTopicName("");
      setNewTopicParentId("");
      await refreshAll();
      setTopicId(topic.id);
      setSuccess("話題を追加しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "話題の追加に失敗しました。";
      setError(message);
    } finally {
      setIsCreatingTopic(false);
    }
  };

  const handleTogglePersonHidden = async (person: Person) => {
    setPersonActionId(person.id);
    try {
      await updatePersonHidden(person.id, !person.is_hidden);

      await refreshAll();
      setSuccess(
        person.is_hidden ? "人物を再表示しました。" : "人物を非表示にしました。"
      );
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "人物状態の更新に失敗しました。";
      setError(message);
    } finally {
      setPersonActionId(null);
    }
  };

  const handleDeletePerson = async (person: Person) => {
    if (!window.confirm(`${person.name} を削除しますか？ この人の関連記録も削除されます。`)) {
      return;
    }

    setPersonActionId(person.id);
    try {
      await deletePerson(person.id);

      await refreshAll();
      setSuccess("人物を削除しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "人物削除に失敗しました。";
      setError(message);
    } finally {
      setPersonActionId(null);
    }
  };

  const handleToggleCommunityHidden = async (community: Community) => {
    setCommunityActionId(community.id);
    try {
      await updateCommunityHidden(community.id, !community.is_hidden);

      await refreshAll();
      setSuccess(
        community.is_hidden
          ? "コミュニティを再表示しました。"
          : "コミュニティを非表示にしました。"
      );
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "コミュニティ状態の更新に失敗しました。";
      setError(message);
    } finally {
      setCommunityActionId(null);
    }
  };

  const handleDeleteCommunity = async (community: Community) => {
    if (
      !window.confirm(
        `${community.name} を削除しますか？ 関連する所属やコミュニティ参照が外れる場合があります。`
      )
    ) {
      return;
    }

    setCommunityActionId(community.id);
    try {
      await deleteCommunity(community.id);

      await refreshAll();
      setSuccess("コミュニティを削除しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "コミュニティ削除に失敗しました。";
      setError(message);
    } finally {
      setCommunityActionId(null);
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
          searchQuery={taskSearchQuery}
          setSearchQuery={setTaskSearchQuery}
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
      onDismissFeedback={() => setFeedback(null)}
      onToggleWorkspaceMode={toggleWorkspaceMode}
    >
      {renderPage()}
    </InteractionNewLayout>
  );
}
