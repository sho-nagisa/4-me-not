import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getPersonDashboard,
  listPersonInteractionCounts,
} from "./interactionsApi";
import type {
  PageId,
  Person,
  PersonDashboard,
  PersonInteractionCount,
} from "./types";
import { buildPersonBubblesFromCounts } from "./utils";

type UsePersonExplorerParams = {
  currentPage: PageId;
  persons: Person[];
  onError: (message: string) => void;
};

export function usePersonExplorer({
  currentPage,
  persons,
  onError,
}: UsePersonExplorerParams) {
  const [detailPersonId, setDetailPersonId] = useState<string>("");
  const [detailCommunityId, setDetailCommunityId] = useState<string>("");
  const [detailDashboard, setDetailDashboard] =
    useState<PersonDashboard | null>(null);
  const [detailDashboardLoading, setDetailDashboardLoading] = useState(false);
  const [detailPersonCounts, setDetailPersonCounts] = useState<
    PersonInteractionCount[]
  >([]);
  const [detailPersonCountsLoading, setDetailPersonCountsLoading] =
    useState(false);

  useEffect(() => {
    if (persons.length === 0) {
      setDetailPersonId("");
      return;
    }

    if (detailPersonId && persons.some((person) => person.id === detailPersonId)) {
      return;
    }

    setDetailPersonId(persons[0].id);
  }, [detailPersonId, persons]);

  const loadDetailPersonCounts = useCallback(
    async (communityId = detailCommunityId) => {
      setDetailPersonCountsLoading(true);
      try {
        const counts = await listPersonInteractionCounts(communityId);
        setDetailPersonCounts(counts);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "人物ごとの記録数を取得できませんでした。";
        onError(message);
      } finally {
        setDetailPersonCountsLoading(false);
      }
    },
    [detailCommunityId, onError]
  );

  const loadDetailDashboard = useCallback(
    async (targetPersonId: string) => {
      if (!targetPersonId) {
        setDetailDashboard(null);
        return;
      }

      setDetailDashboardLoading(true);
      try {
        const dashboard = await getPersonDashboard(targetPersonId);
        setDetailDashboard(dashboard);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "人物ダッシュボードを取得できませんでした。";
        onError(message);
      } finally {
        setDetailDashboardLoading(false);
      }
    },
    [onError]
  );

  useEffect(() => {
    if (currentPage === "person") {
      void loadDetailPersonCounts(detailCommunityId);
    }
  }, [currentPage, detailCommunityId, loadDetailPersonCounts]);

  useEffect(() => {
    if (currentPage === "person") {
      void loadDetailDashboard(detailPersonId);
    }
  }, [currentPage, detailPersonId, loadDetailDashboard]);

  const detailPersonCountMap = useMemo(
    () => new Map(detailPersonCounts.map((item) => [item.person_id, item.count])),
    [detailPersonCounts]
  );

  const detailPersons = useMemo(() => {
    if (!detailCommunityId) return persons;

    // Community filtering uses aggregate counts instead of fetching all
    // interactions into the parent page.
    return persons.filter((person) => {
      if (person.primary_community_id === detailCommunityId) return true;
      return (detailPersonCountMap.get(person.id) ?? 0) > 0;
    });
  }, [detailCommunityId, detailPersonCountMap, persons]);

  useEffect(() => {
    if (currentPage !== "person" || detailPersonCountsLoading) return;
    if (
      detailPersonId &&
      detailPersons.some((person) => person.id === detailPersonId)
    ) {
      return;
    }

    setDetailPersonId(detailPersons[0]?.id ?? "");
  }, [
    currentPage,
    detailPersonCountsLoading,
    detailPersonId,
    detailPersons,
  ]);

  const detailPersonBubbles = useMemo(
    () => buildPersonBubblesFromCounts(detailPersons, detailPersonCounts),
    [detailPersonCounts, detailPersons]
  );

  const selectedDetailPerson = useMemo(
    () => persons.find((person) => person.id === detailPersonId),
    [detailPersonId, persons]
  );

  const refreshPersonExplorer = useCallback(async () => {
    await loadDetailPersonCounts(detailCommunityId);
    if (detailPersonId) {
      await loadDetailDashboard(detailPersonId);
    }
  }, [
    detailCommunityId,
    detailPersonId,
    loadDetailDashboard,
    loadDetailPersonCounts,
  ]);

  return {
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
  };
}
