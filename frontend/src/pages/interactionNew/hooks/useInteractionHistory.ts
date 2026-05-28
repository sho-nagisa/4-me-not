import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { listInteractionPage } from "../interactionsApi";
import { shareLevelOptions } from "../constants";
import { HISTORY_DEFAULT_LIMIT } from "../navigation";
import type { InteractionRecord, PageId, ShareLevel } from "../types";

type UseInteractionHistoryParams = {
  currentPage: PageId;
  onError: (message: string) => void;
};

export function useInteractionHistory({
  currentPage,
  onError,
}: UseInteractionHistoryParams) {
  const [historyItems, setHistoryItems] = useState<InteractionRecord[]>([]);
  const [historyPage, setHistoryPage] = useState(1);
  const historyPageRef = useRef(historyPage);
  const [historyTotalCount, setHistoryTotalCount] = useState(0);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyFilterOpen, setHistoryFilterOpen] = useState(false);

  const [historyPersonId, setHistoryPersonId] = useState<string>("");
  const [historyCommunityId, setHistoryCommunityId] = useState<string>("");
  const [historyTopicId, setHistoryTopicId] = useState<string>("");
  const [historyShareLevel, setHistoryShareLevel] = useState<ShareLevel | "">("");
  const [historySearch, setHistorySearch] = useState<string>("");
  const [historyDateFrom, setHistoryDateFrom] = useState<string>("");
  const [historyDateTo, setHistoryDateTo] = useState<string>("");

  useEffect(() => {
    historyPageRef.current = historyPage;
  }, [historyPage]);

  const loadHistory = useCallback(
    async (page?: number) => {
      const nextPage = Math.max(1, page ?? historyPageRef.current);
      setHistoryLoading(true);
      try {
        const result = await listInteractionPage({
          personId: historyPersonId,
          communityId: historyCommunityId,
          topicId: historyTopicId,
          shareLevel: historyShareLevel,
          search: historySearch,
          dateFrom: historyDateFrom,
          dateTo: historyDateTo,
          limit: HISTORY_DEFAULT_LIMIT,
          offset: (nextPage - 1) * HISTORY_DEFAULT_LIMIT,
        });
        setHistoryItems(result.items);
        setHistoryPage(nextPage);
        setHistoryTotalCount(result.total_count);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "履歴の取得に失敗しました。";
        onError(message);
      } finally {
        setHistoryLoading(false);
      }
    },
    [
      historyCommunityId,
      historyDateFrom,
      historyDateTo,
      historyPersonId,
      historySearch,
      historyShareLevel,
      historyTopicId,
      onError,
    ]
  );

  useEffect(() => {
    if (currentPage === "history") {
      setHistoryPage(1);
      void loadHistory(1);
    }
  }, [
    currentPage,
    historyPersonId,
    historyCommunityId,
    historyTopicId,
    historyShareLevel,
    historySearch,
    historyDateFrom,
    historyDateTo,
    loadHistory,
  ]);

  const clearHistoryFilters = () => {
    setHistoryPersonId("");
    setHistoryCommunityId("");
    setHistoryTopicId("");
    setHistoryShareLevel("");
    setHistorySearch("");
    setHistoryDateFrom("");
    setHistoryDateTo("");
  };

  const selectedHistoryLevelLabel = useMemo(
    () =>
      shareLevelOptions.find((option) => option.value === historyShareLevel)
        ?.label ?? "すべて",
    [historyShareLevel]
  );

  return {
    historyItems,
    historyPage,
    historyTotalCount,
    historyPageSize: HISTORY_DEFAULT_LIMIT,
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
  };
}
