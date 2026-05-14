import type {
  Community,
  InteractionOverview,
  InteractionPage,
  InteractionRecord,
  InteractionType,
  Person,
  PersonDashboard,
  ShareLevel,
  Topic,
} from "./types";
import { buildDateQuery } from "./utils";

type HistoryFilters = {
  personId: string;
  communityId: string;
  topicId: string;
  shareLevel: ShareLevel | "";
  search: string;
  dateFrom: string;
  dateTo: string;
  limit?: number;
  offset?: number;
};

type CreateInteractionPayload = {
  occurred_at: string;
  person_id: string;
  community_id: string | null;
  topic_id: string | null;
  interaction_type: InteractionType;
  share_level: ShareLevel;
  content: string;
  note: string;
};

type CreatePersonPayload = {
  name: string;
  primary_community_id: string | null;
};

type CreateCommunityPayload = {
  name: string;
  parent_id: string | null;
};

type CreateTopicPayload = {
  name: string;
  parent_id: string | null;
};

const jsonHeaders = { "Content-Type": "application/json" };

export const fetchJson = async <T,>(
  url: string,
  init?: RequestInit,
  fallbackMessage = "データ取得に失敗しました。"
): Promise<T> => {
  const response = await fetch(url, init);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || fallbackMessage);
  }

  const responseText = await response.text();
  if (!responseText) {
    return undefined as T;
  }

  return JSON.parse(responseText) as T;
};

export const listPersons = (includeHidden = false) =>
  fetchJson<Person[]>(
    includeHidden ? "/api/persons?include_hidden=true" : "/api/persons"
  );

export const listCommunities = (includeHidden = false) =>
  fetchJson<Community[]>(
    includeHidden ? "/api/communities?include_hidden=true" : "/api/communities"
  );

export const listTopics = () => fetchJson<Topic[]>("/api/topics");

export const listInteractions = (filters?: HistoryFilters) => {
  const params = new URLSearchParams();

  if (filters?.personId) params.set("person_id", filters.personId);
  if (filters?.communityId) params.set("community_id", filters.communityId);
  if (filters?.topicId) params.set("topic_id", filters.topicId);
  if (filters?.shareLevel) params.set("share_level", filters.shareLevel);
  if (filters?.search.trim()) params.set("search", filters.search.trim());
  if (filters?.limit) params.set("limit", String(filters.limit));
  if (filters?.offset) params.set("offset", String(filters.offset));

  const fromDate = filters ? buildDateQuery(filters.dateFrom, "from") : null;
  const toDate = filters ? buildDateQuery(filters.dateTo, "to") : null;
  if (fromDate) params.set("date_from", fromDate);
  if (toDate) params.set("date_to", toDate);

  const query = params.toString();
  return fetchJson<InteractionRecord[]>(
    query ? `/api/interactions?${query}` : "/api/interactions"
  );
};

export const listInteractionPage = (filters: HistoryFilters) => {
  const params = new URLSearchParams();

  if (filters.personId) params.set("person_id", filters.personId);
  if (filters.communityId) params.set("community_id", filters.communityId);
  if (filters.topicId) params.set("topic_id", filters.topicId);
  if (filters.shareLevel) params.set("share_level", filters.shareLevel);
  if (filters.search.trim()) params.set("search", filters.search.trim());
  if (filters.limit) params.set("limit", String(filters.limit));
  if (filters.offset) params.set("offset", String(filters.offset));
  params.set("include_total", "true");

  const fromDate = buildDateQuery(filters.dateFrom, "from");
  const toDate = buildDateQuery(filters.dateTo, "to");
  if (fromDate) params.set("date_from", fromDate);
  if (toDate) params.set("date_to", toDate);

  return fetchJson<InteractionPage>(`/api/interactions?${params.toString()}`);
};

export const getInteractionOverview = () =>
  fetchJson<InteractionOverview>("/api/interactions/overview");

export const getPersonDashboard = (personId: string) =>
  fetchJson<PersonDashboard>(`/api/persons/${personId}/dashboard`);

export const createInteraction = (payload: CreateInteractionPayload) =>
  fetchJson<void>(
    "/api/interactions",
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    },
    "保存に失敗しました。"
  );

export const createPerson = (payload: CreatePersonPayload) =>
  fetchJson<Person>(
    "/api/persons",
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    },
    "人の追加に失敗しました。"
  );

export const createCommunity = (payload: CreateCommunityPayload) =>
  fetchJson<Community>(
    "/api/communities",
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    },
    "コミュニティの追加に失敗しました。"
  );

export const createTopic = (payload: CreateTopicPayload) =>
  fetchJson<Topic>(
    "/api/topics",
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    },
    "話題の追加に失敗しました。"
  );

export const updatePersonHidden = (personId: string, isHidden: boolean) =>
  fetchJson<void>(
    `/api/persons/${personId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify({ is_hidden: isHidden }),
    },
    "人物状態の更新に失敗しました。"
  );

export const deletePerson = (personId: string) =>
  fetchJson<void>(
    `/api/persons/${personId}`,
    { method: "DELETE" },
    "人物削除に失敗しました。"
  );

export const updateCommunityHidden = (communityId: string, isHidden: boolean) =>
  fetchJson<void>(
    `/api/communities/${communityId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify({ is_hidden: isHidden }),
    },
    "コミュニティ状態の更新に失敗しました。"
  );

export const deleteCommunity = (communityId: string) =>
  fetchJson<void>(
    `/api/communities/${communityId}`,
    { method: "DELETE" },
    "コミュニティ削除に失敗しました。"
  );
