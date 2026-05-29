import type {
  AuthAccount,
  Community,
  CreateCommunityPayload,
  CreateInteractionPayload,
  CreatePersonPayload,
  CreateTaskPayload,
  CreateTopicPayload,
  HistoryFilters,
  InteractionOverview,
  InteractionPage,
  InteractionRecord,
  Person,
  PersonDashboard,
  PersonInteractionCount,
  SearchOptions,
  SearchResponse,
  SearchTargetType,
  TaskRecord,
  Topic,
  UpdateTaskPayload,
} from "./types";
import { buildDateQuery } from "./utils";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const jsonHeaders = { "Content-Type": "application/json" };

const parseErrorMessage = (responseText: string, fallbackMessage: string) => {
  if (!responseText) {
    return fallbackMessage;
  }

  try {
    const payload = JSON.parse(responseText) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item) =>
          typeof item === "object" && item !== null && "msg" in item
            ? String(item.msg)
            : String(item)
        )
        .join("\n");
    }
  } catch {
    // Fall through to the raw response text.
  }

  return responseText;
};

export const fetchJson = async <T,>(
  url: string,
  init?: RequestInit,
  fallbackMessage = "データ取得に失敗しました。"
): Promise<T> => {
  const response = await fetch(url, { credentials: "include", ...init });
  if (!response.ok) {
    const message = parseErrorMessage(await response.text(), fallbackMessage);
    throw new ApiError(message, response.status);
  }

  const responseText = await response.text();
  if (!responseText) {
    return undefined as T;
  }

  return JSON.parse(responseText) as T;
};

export const getCurrentAccount = () =>
  fetchJson<AuthAccount>("/api/auth/me", undefined, "ログイン状態を確認できませんでした。");

export const loginAccount = (email: string, password: string) =>
  fetchJson<AuthAccount>(
    "/api/auth/login",
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ email, password }),
    },
    "ログインに失敗しました。"
  );

export const registerAccount = (email: string, password: string) =>
  fetchJson<AuthAccount>(
    "/api/auth/register",
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ email, password }),
    },
    "登録に失敗しました。"
  );

export const logoutAccount = () =>
  fetchJson<{ status: string }>(
    "/api/auth/logout",
    {
      method: "POST",
      headers: jsonHeaders,
    },
    "ログアウトに失敗しました。"
  );

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

export const listPersonInteractionCounts = (communityId = "") => {
  const params = new URLSearchParams();
  if (communityId) {
    params.set("community_id", communityId);
  }
  const query = params.toString();
  return fetchJson<PersonInteractionCount[]>(
    query
      ? `/api/persons/interaction-counts?${query}`
      : "/api/persons/interaction-counts"
  );
};

export const searchMemory = (
  queryText: string,
  targetTypes: SearchTargetType[] = [],
  limitOrOptions: number | SearchOptions = 24
) => {
  const options =
    typeof limitOrOptions === "number" ? { limit: limitOrOptions } : limitOrOptions;
  const params = new URLSearchParams();
  params.set("q", queryText.trim());
  params.set("limit", String(options.limit ?? 24));
  if (options.dateFrom) {
    params.set("date_from", options.dateFrom);
  }
  if (options.dateTo) {
    params.set("date_to", options.dateTo);
  }
  if (options.fuzzy !== undefined) {
    params.set("fuzzy", String(options.fuzzy));
  }
  targetTypes.forEach((targetType) => params.append("target_type", targetType));
  return fetchJson<SearchResponse>(`/api/search?${params.toString()}`);
};

export const listTaskCandidates = (limit = 20) =>
  fetchJson<TaskRecord[]>(
    `/api/tasks?candidate_status=pending&limit=${limit}`
  );

export const listTasks = ({
  includeCandidates = false,
  candidateStatus,
  status,
  openOnly,
  search,
  limit = 100,
}: {
  includeCandidates?: boolean;
  candidateStatus?: string;
  status?: string;
  openOnly?: boolean;
  search?: string;
  limit?: number;
} = {}) => {
  const params = new URLSearchParams();
  params.set("include_candidates", String(includeCandidates));
  params.set("limit", String(limit));
  if (candidateStatus) {
    params.set("candidate_status", candidateStatus);
  }
  if (status) {
    params.set("status", status);
  }
  if (openOnly !== undefined) {
    params.set("open_only", String(openOnly));
  }
  if (search?.trim()) {
    params.set("search", search.trim());
  }

  return fetchJson<TaskRecord[]>(`/api/tasks?${params.toString()}`);
};

export const createTask = (payload: CreateTaskPayload) =>
  fetchJson<TaskRecord>(
    "/api/tasks",
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    },
    "タスクの作成に失敗しました。"
  );

export const updateTask = (taskId: string, payload: UpdateTaskPayload) =>
  fetchJson<TaskRecord>(
    `/api/tasks/${taskId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    },
    "タスクの更新に失敗しました。"
  );

export const completeTask = (taskId: string) =>
  fetchJson<TaskRecord>(
    `/api/tasks/${taskId}/complete`,
    {
      method: "POST",
      headers: jsonHeaders,
    },
    "タスクの完了に失敗しました。"
  );

export const reopenTask = (taskId: string) =>
  fetchJson<TaskRecord>(
    `/api/tasks/${taskId}/reopen`,
    {
      method: "POST",
      headers: jsonHeaders,
    },
    "タスクの未完了化に失敗しました。"
  );

export const acceptTaskCandidate = (taskId: string) =>
  fetchJson<TaskRecord>(
    `/api/tasks/${taskId}/accept`,
    {
      method: "POST",
      headers: jsonHeaders,
    },
    "タスク候補の採用に失敗しました。"
  );

export const dismissTaskCandidate = (taskId: string) =>
  fetchJson<TaskRecord>(
    `/api/tasks/${taskId}/dismiss`,
    {
      method: "POST",
      headers: jsonHeaders,
    },
    "タスク候補の却下に失敗しました。"
  );

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
