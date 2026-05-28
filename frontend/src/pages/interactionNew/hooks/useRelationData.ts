import { useCallback, useState, type Dispatch, type SetStateAction } from "react";

import {
  getInteractionOverview,
  listCommunities,
  listPersons,
  listTopics,
} from "../interactionsApi";
import type { Community, InteractionOverview, Person, Topic } from "../types";

type UseRelationDataParams = {
  personId: string;
  setPersonId: Dispatch<SetStateAction<string>>;
  setCommunityId: Dispatch<SetStateAction<string>>;
  setCommunityTouched: Dispatch<SetStateAction<boolean>>;
  historyPersonId: string;
  setHistoryPersonId: Dispatch<SetStateAction<string>>;
  onError: (message: string) => void;
};

export function useRelationData({
  personId,
  setPersonId,
  setCommunityId,
  setCommunityTouched,
  historyPersonId,
  setHistoryPersonId,
  onError,
}: UseRelationDataParams) {
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

  const loadOptions = useCallback(async () => {
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
      onError(message);
    } finally {
      setLoading(false);
    }
  }, [
    historyPersonId,
    onError,
    personId,
    setCommunityId,
    setCommunityTouched,
    setHistoryPersonId,
    setPersonId,
  ]);

  const loadManageData = useCallback(async () => {
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
      onError(message);
    }
  }, [onError]);

  const loadOverviewInteractions = useCallback(async () => {
    try {
      const items = await getInteractionOverview();
      setOverview(items);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "全体の履歴取得に失敗しました。";
      onError(message);
    }
  }, [onError]);

  return {
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
  };
}
