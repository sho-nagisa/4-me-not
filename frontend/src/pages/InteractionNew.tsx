import { useEffect, useState } from "react";

type Person = {
  id: string;
  name: string;
  primary_community_id: string | null;
  primary_community_path: string | null;
};

type Community = {
  id: string;
  name: string;
  parent_id: string | null;
  path: string;
};

type Topic = {
  id: string;
  name: string;
  parent_id: string | null;
  path: string;
};

type InteractionRecord = {
  id: string;
  person_id: string;
  person_name: string;
  community_id: string | null;
  community_name: string | null;
  community_path: string | null;
  topic_id: string | null;
  topic_name: string | null;
  topic_path: string | null;
  interaction_type: string;
  interaction_type_label: string;
  share_level: string;
  share_level_label: string;
  occurred_at: string | null;
  content: string | null;
  note: string | null;
  created_at: string;
};

type SummaryItem = {
  id: string;
  label: string;
  count: number;
  shared_count: number;
  partial_count: number;
  withheld_count: number;
};

type ShareSummary = {
  share_level: ShareLevel;
  label: string;
  count: number;
};

type PrepTopic = {
  topic: string;
  community: string;
  occurred_at: string | null;
};

type PrepNote = {
  text: string;
  topic: string;
  share_level: ShareLevel;
  share_level_label: string;
  occurred_at: string | null;
};

type PersonDashboard = {
  person: Person;
  overview: {
    interaction_count: number;
    latest_occurred_at: string | null;
    shared_count: number;
    partial_count: number;
    withheld_count: number;
  };
  share_summary: ShareSummary[];
  top_topics: SummaryItem[];
  top_communities: SummaryItem[];
  recent_interactions: InteractionRecord[];
  conversation_prep: {
    shared_topics: PrepTopic[];
    partial_topics: PrepTopic[];
    withheld_topics: PrepTopic[];
    recent_notes: PrepNote[];
  };
};

type InteractionType =
  | "MEETING"
  | "CHAT"
  | "CALL"
  | "MESSAGE"
  | "OBSERVATION";

type ShareLevel = "SHARED" | "PARTIAL" | "WITHHELD";
type ViewMode = "record" | "history" | "person" | "manage";

const interactionTypeOptions: Array<{
  value: InteractionType;
  label: string;
  description: string;
}> = [
  { value: "MEETING", label: "対面", description: "会って話した内容を記録" },
  { value: "CHAT", label: "会話", description: "雑談や立ち話を残す" },
  { value: "CALL", label: "通話", description: "電話やオンライン通話の記録" },
  { value: "MESSAGE", label: "メッセージ", description: "テキストでのやり取りを残す" },
  { value: "OBSERVATION", label: "出来事メモ", description: "場で見たことや感じたことを記録" },
];

const shareLevelOptions: Array<{
  value: ShareLevel;
  label: string;
  description: string;
}> = [
  { value: "SHARED", label: "話した", description: "そのまま伝えた内容" },
  { value: "PARTIAL", label: "一部だけ話した", description: "触れたが全部は話していない" },
  { value: "WITHHELD", label: "話していない", description: "今後のために控えた内容" },
];

const viewOptions: Array<{ value: ViewMode; label: string; description: string }> = [
  { value: "record", label: "記録する", description: "会話内容を残す" },
  { value: "history", label: "探して振り返る", description: "条件を絞って履歴を見る" },
  { value: "person", label: "人ごとに見る", description: "次の会話前に整理する" },
  { value: "manage", label: "階層を整える", description: "コミュニティと話題を管理する" },
];

const toDateTimeLocalValue = (date = new Date()) => {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
};

const formatDateTime = (isoText: string | null) => {
  if (!isoText) return "未設定";
  const date = new Date(isoText);
  if (Number.isNaN(date.getTime())) return isoText;
  return date.toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const buildDateQuery = (dateText: string, mode: "from" | "to") => {
  if (!dateText) return null;
  const suffix = mode === "from" ? "T00:00:00" : "T23:59:59";
  return new Date(`${dateText}${suffix}`).toISOString();
};

const summarizeCountLabel = (count: number, singular: string) =>
  count === 0 ? `まだ${singular}はありません` : `${count}件の${singular}`;

const truncate = (text: string | null | undefined, max = 90) => {
  if (!text) return "内容なし";
  if (text.length <= max) return text;
  return `${text.slice(0, max)}...`;
};

export default function InteractionNew() {
  const [viewMode, setViewMode] = useState<ViewMode>("record");
  const [persons, setPersons] = useState<Person[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [interactions, setInteractions] = useState<InteractionRecord[]>([]);
  const [historyItems, setHistoryItems] = useState<InteractionRecord[]>([]);

  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [recordDashboardLoading, setRecordDashboardLoading] = useState(false);
  const [detailDashboardLoading, setDetailDashboardLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isCreatingPerson, setIsCreatingPerson] = useState(false);
  const [isCreatingCommunity, setIsCreatingCommunity] = useState(false);
  const [isCreatingTopic, setIsCreatingTopic] = useState(false);

  const [feedback, setFeedback] = useState<{
    tone: "success" | "error" | "info";
    message: string;
  } | null>(null);

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

  const [historyPersonId, setHistoryPersonId] = useState<string>("");
  const [historyCommunityId, setHistoryCommunityId] = useState<string>("");
  const [historyTopicId, setHistoryTopicId] = useState<string>("");
  const [historyShareLevel, setHistoryShareLevel] = useState<ShareLevel | "">("");
  const [historySearch, setHistorySearch] = useState<string>("");
  const [historyDateFrom, setHistoryDateFrom] = useState<string>("");
  const [historyDateTo, setHistoryDateTo] = useState<string>("");

  const [detailPersonId, setDetailPersonId] = useState<string>("");
  const [recordDashboard, setRecordDashboard] = useState<PersonDashboard | null>(null);
  const [detailDashboard, setDetailDashboard] = useState<PersonDashboard | null>(null);

  const selectedPerson = persons.find((person) => person.id === personId);
  const selectedHistoryPerson = persons.find((person) => person.id === historyPersonId);
  const selectedDetailPerson = persons.find((person) => person.id === detailPersonId);
  const selectedType = interactionTypeOptions.find(
    (option) => option.value === interactionType
  );
  const selectedShareLevel = shareLevelOptions.find(
    (option) => option.value === shareLevel
  );

  const setError = (message: string) => {
    setFeedback({ tone: "error", message });
  };

  const setSuccess = (message: string) => {
    setFeedback({ tone: "success", message });
  };

  const fetchJson = async <T,>(url: string): Promise<T> => {
    const res = await fetch(url);
    if (!res.ok) {
      const message = await res.text();
      throw new Error(message || "データ取得に失敗しました");
    }
    return res.json() as Promise<T>;
  };

  const loadOptions = async () => {
    setLoading(true);
    try {
      const [personsJson, communitiesJson, topicsJson] = await Promise.all([
        fetchJson<Person[]>("/api/persons"),
        fetchJson<Community[]>("/api/communities"),
        fetchJson<Topic[]>("/api/topics"),
      ]);

      setPersons(personsJson);
      setCommunities(communitiesJson);
      setTopics(topicsJson);

      const firstPersonId = personsJson[0]?.id ?? "";
      const currentRecordPerson =
        personsJson.find((person) => person.id === personId) ?? personsJson[0] ?? null;
      const currentHistoryPerson =
        personsJson.find((person) => person.id === historyPersonId) ?? null;
      const currentDetailPerson =
        personsJson.find((person) => person.id === detailPersonId) ?? personsJson[0] ?? null;

      if (!personId || !currentRecordPerson) {
        setPersonId(firstPersonId);
        setCommunityId(currentRecordPerson?.primary_community_id ?? "");
        setCommunityTouched(false);
      }
      if (historyPersonId && !currentHistoryPerson) {
        setHistoryPersonId("");
      }
      if (!detailPersonId || !currentDetailPerson) {
        setDetailPersonId(currentDetailPerson?.id ?? "");
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "初期データの読み込みに失敗しました";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const loadOverviewInteractions = async () => {
    setSummaryLoading(true);
    try {
      const json = await fetchJson<InteractionRecord[]>("/api/interactions");
      setInteractions(json);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "全体の記録読み込みに失敗しました";
      setError(message);
    } finally {
      setSummaryLoading(false);
    }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const params = new URLSearchParams();
      if (historyPersonId) params.set("person_id", historyPersonId);
      if (historyCommunityId) params.set("community_id", historyCommunityId);
      if (historyTopicId) params.set("topic_id", historyTopicId);
      if (historyShareLevel) params.set("share_level", historyShareLevel);
      if (historySearch.trim()) params.set("search", historySearch.trim());

      const dateFromQuery = buildDateQuery(historyDateFrom, "from");
      const dateToQuery = buildDateQuery(historyDateTo, "to");
      if (dateFromQuery) params.set("date_from", dateFromQuery);
      if (dateToQuery) params.set("date_to", dateToQuery);

      const query = params.toString();
      const url = query ? `/api/interactions?${query}` : "/api/interactions";
      const json = await fetchJson<InteractionRecord[]>(url);
      setHistoryItems(json);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "履歴の読み込みに失敗しました";
      setError(message);
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadRecordDashboard = async (targetPersonId: string) => {
    if (!targetPersonId) {
      setRecordDashboard(null);
      return;
    }

    setRecordDashboardLoading(true);
    try {
      const json = await fetchJson<PersonDashboard>(
        `/api/persons/${targetPersonId}/dashboard`
      );
      setRecordDashboard(json);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "事前確認データの取得に失敗しました";
      setError(message);
    } finally {
      setRecordDashboardLoading(false);
    }
  };

  const loadDetailDashboard = async (targetPersonId: string) => {
    if (!targetPersonId) {
      setDetailDashboard(null);
      return;
    }

    setDetailDashboardLoading(true);
    try {
      const json = await fetchJson<PersonDashboard>(
        `/api/persons/${targetPersonId}/dashboard`
      );
      setDetailDashboard(json);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "人ごとの要約取得に失敗しました";
      setError(message);
    } finally {
      setDetailDashboardLoading(false);
    }
  };

  useEffect(() => {
    void loadOptions();
    void loadOverviewInteractions();
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [
    historyPersonId,
    historyCommunityId,
    historyTopicId,
    historyShareLevel,
    historySearch,
    historyDateFrom,
    historyDateTo,
  ]);

  useEffect(() => {
    void loadRecordDashboard(personId);
  }, [personId]);

  useEffect(() => {
    void loadDetailDashboard(detailPersonId);
  }, [detailPersonId]);

  const refreshAll = async () => {
    await loadOptions();
    await loadOverviewInteractions();
    await loadHistory();
    if (personId) {
      await loadRecordDashboard(personId);
    }
    if (detailPersonId) {
      await loadDetailDashboard(detailPersonId);
    }
  };

  const handleSubmit = async () => {
    if (!personId || !content.trim()) {
      setError("相手と内容は必須です");
      return;
    }

    setIsSaving(true);
    setFeedback({ tone: "info", message: "記録を保存しています..." });

    try {
      const res = await fetch("/api/interactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          occurred_at: occurredAt,
          person_id: personId,
          community_id: communityId || null,
          topic_id: topicId || null,
          interaction_type: interactionType,
          share_level: shareLevel,
          content,
          note,
        }),
      });

      if (!res.ok) {
        const message = await res.text();
        throw new Error(message || "保存に失敗しました");
      }

      setSuccess("やり取りを保存しました");
      setContent("");
      setNote("");
      setOccurredAt(toDateTimeLocalValue());
      setCommunityTouched(false);
      await loadOverviewInteractions();
      await loadHistory();
      await loadRecordDashboard(personId);
      if (detailPersonId === personId) {
        await loadDetailDashboard(personId);
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "記録の保存に失敗しました";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreatePerson = async () => {
    if (!newPersonName.trim()) {
      setError("追加する人の名前を入力してください");
      return;
    }

    setIsCreatingPerson(true);
    try {
      const res = await fetch("/api/persons", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newPersonName.trim(),
          primary_community_id: newPersonPrimaryCommunityId || null,
        }),
      });

      if (!res.ok) {
        const message = await res.text();
        throw new Error(message || "人の追加に失敗しました");
      }

      const person = (await res.json()) as Person;
      setNewPersonName("");
      setNewPersonPrimaryCommunityId("");
      await loadOptions();
      setPersonId(person.id);
      setHistoryPersonId(person.id);
      setDetailPersonId(person.id);
      setCommunityId(person.primary_community_id ?? "");
      setCommunityTouched(false);
      setSuccess("人を追加しました");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "人の追加に失敗しました";
      setError(message);
    } finally {
      setIsCreatingPerson(false);
    }
  };

  const handleCreateCommunity = async () => {
    if (!newCommunityName.trim()) {
      setError("追加するコミュニティ名を入力してください");
      return;
    }

    setIsCreatingCommunity(true);
    try {
      const res = await fetch("/api/communities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newCommunityName.trim(),
          parent_id: newCommunityParentId || null,
        }),
      });

      if (!res.ok) {
        const message = await res.text();
        throw new Error(message || "コミュニティ追加に失敗しました");
      }

      const community = (await res.json()) as Community;
      setNewCommunityName("");
      setNewCommunityParentId("");
      await refreshAll();
      setCommunityId(community.id);
      setSuccess("コミュニティを追加しました");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "コミュニティ追加に失敗しました";
      setError(message);
    } finally {
      setIsCreatingCommunity(false);
    }
  };

  const handleCreateTopic = async () => {
    if (!newTopicName.trim()) {
      setError("追加する話題名を入力してください");
      return;
    }

    setIsCreatingTopic(true);
    try {
      const res = await fetch("/api/topics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newTopicName.trim(),
          parent_id: newTopicParentId || null,
        }),
      });

      if (!res.ok) {
        const message = await res.text();
        throw new Error(message || "話題追加に失敗しました");
      }

      const topic = (await res.json()) as Topic;
      setNewTopicName("");
      setNewTopicParentId("");
      await refreshAll();
      setTopicId(topic.id);
      setSuccess("話題を追加しました");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "話題追加に失敗しました";
      setError(message);
    } finally {
      setIsCreatingTopic(false);
    }
  };

  const handlePersonChange = (nextPersonId: string) => {
    setPersonId(nextPersonId);
    const nextPerson = persons.find((person) => person.id === nextPersonId);
    setCommunityId(nextPerson?.primary_community_id ?? "");
    setCommunityTouched(false);
  };

  const clearHistoryFilters = () => {
    setHistoryPersonId("");
    setHistoryCommunityId("");
    setHistoryTopicId("");
    setHistoryShareLevel("");
    setHistorySearch("");
    setHistoryDateFrom("");
    setHistoryDateTo("");
  };

  const renderPrepList = (items: PrepTopic[], emptyLabel: string) => {
    if (items.length === 0) {
      return <p className="muted">{emptyLabel}</p>;
    }

    return (
      <div className="stack stack--compact">
        {items.map((item) => (
          <div
            key={`${item.topic}-${item.community}-${item.occurred_at ?? "none"}`}
            className="summary-row"
          >
            <strong>{item.topic}</strong>
            <span>
              {item.community} / {formatDateTime(item.occurred_at)}
            </span>
          </div>
        ))}
      </div>
    );
  };

  const renderRecentInteractionCard = (item: InteractionRecord) => (
    <article key={item.id} className="history-card">
      <div className="history-card__top">
        <div>
          <p className="history-card__date">{formatDateTime(item.occurred_at)}</p>
          <h3>{item.interaction_type_label}</h3>
        </div>
        <span className={`pill pill--${item.share_level.toLowerCase()}`}>
          {item.share_level_label}
        </span>
      </div>

      <div className="history-card__meta">
        <span>相手: {item.person_name}</span>
        <span>コミュニティ: {item.community_path ?? "未設定"}</span>
        <span>話題: {item.topic_path ?? "未設定"}</span>
      </div>

      <p className="history-card__content">{item.content ?? "内容なし"}</p>
      <p className="history-card__note">{item.note || "補足メモなし"}</p>
    </article>
  );

  const renderRecordView = () => (
    <section className="layout">
      <aside className="panel panel--soft">
        <div className="panel__header">
          <p className="eyebrow">入力の準備</p>
          <h2>候補を整えながらすばやく記録</h2>
          <p className="panel__lead">
            人を選ぶと主な所属コミュニティを初期値に入れます。必要ならその場だけ手動で
            上書きできます。
          </p>
        </div>

        <div className="stack">
          <article className="mini-card">
            <h3>人を追加</h3>
            <label className="field">
              <span className="field__label">名前</span>
              <input
                value={newPersonName}
                onChange={(e) => setNewPersonName(e.target.value)}
                placeholder="例: 田中さん"
              />
            </label>
            <label className="field">
              <span className="field__label">主な所属コミュニティ</span>
              <select
                value={newPersonPrimaryCommunityId}
                onChange={(e) => setNewPersonPrimaryCommunityId(e.target.value)}
              >
                <option value="">-- 未設定 --</option>
                {communities.map((community) => (
                  <option key={community.id} value={community.id}>
                    {community.path}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="button button--secondary"
              onClick={handleCreatePerson}
              disabled={isCreatingPerson}
            >
              {isCreatingPerson ? "追加中..." : "人を追加"}
            </button>
          </article>

          <article className="mini-card">
            <h3>コミュニティを追加</h3>
            <label className="field">
              <span className="field__label">コミュニティ名</span>
              <input
                value={newCommunityName}
                onChange={(e) => setNewCommunityName(e.target.value)}
                placeholder="例: 飲み"
              />
            </label>
            <label className="field">
              <span className="field__label">親コミュニティ</span>
              <select
                value={newCommunityParentId}
                onChange={(e) => setNewCommunityParentId(e.target.value)}
              >
                <option value="">-- なし --</option>
                {communities.map((community) => (
                  <option key={community.id} value={community.id}>
                    {community.path}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="button button--secondary"
              onClick={handleCreateCommunity}
              disabled={isCreatingCommunity}
            >
              {isCreatingCommunity ? "追加中..." : "コミュニティを追加"}
            </button>
          </article>

          <article className="mini-card">
            <h3>話題を追加</h3>
            <label className="field">
              <span className="field__label">話題名</span>
              <input
                value={newTopicName}
                onChange={(e) => setNewTopicName(e.target.value)}
                placeholder="例: 面接 / 自己紹介"
              />
            </label>
            <label className="field">
              <span className="field__label">親話題</span>
              <select
                value={newTopicParentId}
                onChange={(e) => setNewTopicParentId(e.target.value)}
              >
                <option value="">-- なし --</option>
                {topics.map((topic) => (
                  <option key={topic.id} value={topic.id}>
                    {topic.path}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="button button--secondary"
              onClick={handleCreateTopic}
              disabled={isCreatingTopic}
            >
              {isCreatingTopic ? "追加中..." : "話題を追加"}
            </button>
          </article>

          <article className="hint-card">
            <p className="hint-card__title">会話前の確認</p>
            {!selectedPerson ? (
              <p>相手を選ぶと、最近のやり取りや話した範囲をここで見られます。</p>
            ) : recordDashboardLoading ? (
              <p>確認メモを読み込み中です...</p>
            ) : recordDashboard ? (
              <div className="stack stack--compact">
                <p>
                  最後の記録: {formatDateTime(recordDashboard.overview.latest_occurred_at)}
                </p>
                <p>主な所属: {recordDashboard.person.primary_community_path ?? "未設定"}</p>
                <p>
                  話した: {recordDashboard.overview.shared_count}件 / 一部だけ話した:{" "}
                  {recordDashboard.overview.partial_count}件 / 話していない:{" "}
                  {recordDashboard.overview.withheld_count}件
                </p>
                <div className="hint-card__section">
                  <strong>まだ慎重に扱いたい話題</strong>
                  {renderPrepList(
                    recordDashboard.conversation_prep.withheld_topics.slice(0, 3),
                    "今のところ控えた話題はありません"
                  )}
                </div>
              </div>
            ) : (
              <p>この人の確認メモはまだありません。</p>
            )}
          </article>
        </div>
      </aside>

      <section className="panel panel--main">
        <div className="panel__header">
          <p className="eyebrow">新しい記録</p>
          <h2>人との接点を、あとで活きるメモに変える</h2>
          <p className="panel__lead">
            誰と、どの場で、どこまで話したかを分けて残すと、次の会話前の確認がぐっと
            しやすくなります。
          </p>
        </div>

        <div className="form-grid">
          <label className="field">
            <span className="field__label">日付</span>
            <input
              type="datetime-local"
              value={occurredAt}
              onChange={(e) => setOccurredAt(e.target.value)}
            />
          </label>

          <label className="field">
            <span className="field__label">相手</span>
            <select
              value={personId}
              onChange={(e) => handlePersonChange(e.target.value)}
              disabled={loading}
            >
              <option value="">-- 選択してください --</option>
              {persons.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field__label">コミュニティ</span>
            <select
              value={communityId}
              onChange={(e) => {
                setCommunityId(e.target.value);
                setCommunityTouched(true);
              }}
              disabled={loading}
            >
              <option value="">-- 未設定 --</option>
              {communities.map((community) => (
                <option key={community.id} value={community.id}>
                  {community.path}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field__label">話題</span>
            <select
              value={topicId}
              onChange={(e) => setTopicId(e.target.value)}
              disabled={loading}
            >
              <option value="">-- 未設定 --</option>
              {topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.path}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field__label">接点の種類</span>
            <select
              value={interactionType}
              onChange={(e) =>
                setInteractionType(e.target.value as InteractionType)
              }
            >
              {interactionTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <span className="field__hint">{selectedType?.description}</span>
          </label>

          <label className="field">
            <span className="field__label">どこまで話したか</span>
            <select
              value={shareLevel}
              onChange={(e) => setShareLevel(e.target.value as ShareLevel)}
            >
              {shareLevelOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <span className="field__hint">{selectedShareLevel?.description}</span>
          </label>

          <label className="field field--full">
            <span className="field__label">内容</span>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="何を話したか、どこまで共有したかを自然文で残します"
              rows={5}
            />
          </label>

          <label className="field field--full">
            <span className="field__label">補足メモ</span>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="次に話したいこと、気になった点、印象など"
              rows={4}
            />
          </label>
        </div>

        <div className="action-row">
          <button
            className="button button--primary"
            onClick={handleSubmit}
            disabled={isSaving || loading}
          >
            {isSaving ? "保存中..." : "記録を保存"}
          </button>
          <p className="action-row__hint">
            {loading
              ? "候補を読み込み中です"
              : communityTouched
                ? `${selectedShareLevel?.label ?? "記録"} として保存します。コミュニティは今回だけ手動で変更しています。`
                : `${selectedShareLevel?.label ?? "記録"} として保存します。${selectedPerson?.primary_community_path ?? "主な所属未設定"} を初期値にしています。`}
          </p>
        </div>
      </section>
    </section>
  );

  const renderHistoryView = () => (
    <section className="layout layout--history">
      <aside className="panel panel--soft">
        <div className="panel__header">
          <p className="eyebrow">検索と絞り込み</p>
          <h2>条件を組み合わせて履歴を見る</h2>
        </div>

        <div className="stack">
          <label className="field">
            <span className="field__label">人</span>
            <select
              value={historyPersonId}
              onChange={(e) => setHistoryPersonId(e.target.value)}
              disabled={loading}
            >
              <option value="">-- すべて --</option>
              {persons.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field__label">コミュニティ</span>
            <select
              value={historyCommunityId}
              onChange={(e) => setHistoryCommunityId(e.target.value)}
              disabled={loading}
            >
              <option value="">-- すべて --</option>
              {communities.map((community) => (
                <option key={community.id} value={community.id}>
                  {community.path}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field__label">話題</span>
            <select
              value={historyTopicId}
              onChange={(e) => setHistoryTopicId(e.target.value)}
              disabled={loading}
            >
              <option value="">-- すべて --</option>
              {topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.path}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field__label">共有レベル</span>
            <select
              value={historyShareLevel}
              onChange={(e) => setHistoryShareLevel(e.target.value as ShareLevel | "")}
            >
              <option value="">-- すべて --</option>
              {shareLevelOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field__label">キーワード</span>
            <input
              value={historySearch}
              onChange={(e) => setHistorySearch(e.target.value)}
              placeholder="内容や補足メモを検索"
            />
          </label>

          <div className="filter-grid">
            <label className="field">
              <span className="field__label">開始日</span>
              <input
                type="date"
                value={historyDateFrom}
                onChange={(e) => setHistoryDateFrom(e.target.value)}
              />
            </label>
            <label className="field">
              <span className="field__label">終了日</span>
              <input
                type="date"
                value={historyDateTo}
                onChange={(e) => setHistoryDateTo(e.target.value)}
              />
            </label>
          </div>

          <div className="button-row">
            <button
              type="button"
              className="button button--secondary"
              onClick={() => void loadHistory()}
              disabled={historyLoading}
            >
              {historyLoading ? "更新中..." : "再読み込み"}
            </button>
            <button
              type="button"
              className="button button--ghost"
              onClick={clearHistoryFilters}
            >
              条件をクリア
            </button>
          </div>

          <div className="hint-card">
            <p className="hint-card__title">現在の絞り込み</p>
            <p>人: {selectedHistoryPerson?.name ?? "すべて"}</p>
            <p>
              共有レベル:{" "}
              {shareLevelOptions.find((option) => option.value === historyShareLevel)?.label ??
                "すべて"}
            </p>
            <p>キーワード: {historySearch.trim() || "なし"}</p>
          </div>
        </div>
      </aside>

      <section className="panel panel--main">
        <div className="panel__header">
          <p className="eyebrow">履歴一覧</p>
          <h2>人・場・話題から横断して振り返る</h2>
          <p className="panel__lead">
            人だけでなく、コミュニティや話題単位でも見返せます。面接や日常会話の前の
            確認にも使える履歴ビューです。
          </p>
        </div>

        <div className="summary-strip">
          <div className="summary-chip">
            <strong>{historyItems.length}</strong>
            <span>表示件数</span>
          </div>
          <div className="summary-chip">
            <strong>{historyItems.filter((item) => item.share_level === "PARTIAL").length}</strong>
            <span>一部だけ話した</span>
          </div>
          <div className="summary-chip">
            <strong>{historyItems.filter((item) => item.share_level === "WITHHELD").length}</strong>
            <span>話していない</span>
          </div>
        </div>

        {historyItems.length === 0 ? (
          <div className="empty-state">
            <strong>条件に合う履歴はまだありません</strong>
            <p>フィルターを緩めるか、新しいやり取りを記録するとここに表示されます。</p>
          </div>
        ) : (
          <div className="history-list">
            {historyItems.map((item) => renderRecentInteractionCard(item))}
          </div>
        )}
      </section>
    </section>
  );

  const renderPersonView = () => (
    <section className="layout layout--person">
      <aside className="panel panel--soft">
        <div className="panel__header">
          <p className="eyebrow">人ごとの要約</p>
          <h2>次の会話前に把握する</h2>
        </div>

        <div className="stack">
          <label className="field">
            <span className="field__label">人を選ぶ</span>
            <select
              value={detailPersonId}
              onChange={(e) => setDetailPersonId(e.target.value)}
              disabled={loading}
            >
              <option value="">-- 選択してください --</option>
              {persons.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            className="button button--secondary"
            onClick={() => void loadDetailDashboard(detailPersonId)}
            disabled={detailDashboardLoading || !detailPersonId}
          >
            {detailDashboardLoading ? "更新中..." : "要約を更新"}
          </button>

          <div className="hint-card">
            <p className="hint-card__title">確認ポイント</p>
            {selectedDetailPerson ? (
              <>
                <p>相手: {selectedDetailPerson.name}</p>
                <p>主な所属: {selectedDetailPerson.primary_community_path ?? "未設定"}</p>
                <p>次の会話前に、何を話したかと何を控えたかを一度見直せます。</p>
              </>
            ) : (
              <p>人を選ぶと、要約と注意点を表示します。</p>
            )}
          </div>
        </div>
      </aside>

      <section className="panel panel--main">
        {!detailDashboard ? (
          <div className="empty-state">
            <strong>人を選ぶと詳細を表示します</strong>
            <p>最近の会話、よく出る話題、共有レベル別の傾向をまとめて確認できます。</p>
          </div>
        ) : (
          <>
            <div className="panel__header">
              <p className="eyebrow">人物ダッシュボード</p>
              <h2>{detailDashboard.person.name} さんの整理</h2>
              <p className="panel__lead">
                主な所属: {detailDashboard.person.primary_community_path ?? "未設定"} / 最後の記録:{" "}
                {formatDateTime(detailDashboard.overview.latest_occurred_at)}
              </p>
            </div>

            <div className="stats-grid">
              <article className="stat-box">
                <span>記録数</span>
                <strong>{detailDashboard.overview.interaction_count}</strong>
              </article>
              <article className="stat-box">
                <span>話した</span>
                <strong>{detailDashboard.overview.shared_count}</strong>
              </article>
              <article className="stat-box">
                <span>一部だけ話した</span>
                <strong>{detailDashboard.overview.partial_count}</strong>
              </article>
              <article className="stat-box">
                <span>話していない</span>
                <strong>{detailDashboard.overview.withheld_count}</strong>
              </article>
            </div>

            <section className="detail-section">
              <div className="section-title">
                <h3>共有レベルの内訳</h3>
                <span>{summarizeCountLabel(detailDashboard.share_summary.length, "区分")}</span>
              </div>
              <div className="summary-strip">
                {detailDashboard.share_summary.map((item) => (
                  <div key={item.share_level} className="summary-chip">
                    <strong>{item.count}</strong>
                    <span>{item.label}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="detail-columns">
              <article className="detail-card">
                <div className="section-title">
                  <h3>よく出る話題</h3>
                  <span>{detailDashboard.top_topics.length}件</span>
                </div>
                {detailDashboard.top_topics.length === 0 ? (
                  <p className="muted">まだ話題はまとまっていません。</p>
                ) : (
                  <div className="stack stack--compact">
                    {detailDashboard.top_topics.map((item) => (
                      <div key={item.id} className="summary-row">
                        <strong>{item.label}</strong>
                        <span>
                          {item.count}件 / 話した {item.shared_count} / 一部 {item.partial_count} /
                          控えた {item.withheld_count}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </article>

              <article className="detail-card">
                <div className="section-title">
                  <h3>よく関わる場</h3>
                  <span>{detailDashboard.top_communities.length}件</span>
                </div>
                {detailDashboard.top_communities.length === 0 ? (
                  <p className="muted">まだコミュニティ情報はまとまっていません。</p>
                ) : (
                  <div className="stack stack--compact">
                    {detailDashboard.top_communities.map((item) => (
                      <div key={item.id} className="summary-row">
                        <strong>{item.label}</strong>
                        <span>
                          {item.count}件 / 話した {item.shared_count} / 一部 {item.partial_count} /
                          控えた {item.withheld_count}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </article>
            </section>

            <section className="detail-section">
              <div className="section-title">
                <h3>会話前に見たい整理</h3>
                <span>共有状況のメモ</span>
              </div>
              <div className="prep-grid">
                <article className="prep-card">
                  <h4>すでに話した話題</h4>
                  {renderPrepList(
                    detailDashboard.conversation_prep.shared_topics,
                    "まだ十分に共有した話題はありません"
                  )}
                </article>
                <article className="prep-card">
                  <h4>一部だけ話した話題</h4>
                  {renderPrepList(
                    detailDashboard.conversation_prep.partial_topics,
                    "途中まで触れた話題はありません"
                  )}
                </article>
                <article className="prep-card">
                  <h4>まだ話していない話題</h4>
                  {renderPrepList(
                    detailDashboard.conversation_prep.withheld_topics,
                    "控えている話題はありません"
                  )}
                </article>
              </div>
            </section>

            <section className="detail-section">
              <div className="section-title">
                <h3>最近の補足メモ</h3>
                <span>{detailDashboard.conversation_prep.recent_notes.length}件</span>
              </div>
              {detailDashboard.conversation_prep.recent_notes.length === 0 ? (
                <p className="muted">補足メモはまだありません。</p>
              ) : (
                <div className="stack">
                  {detailDashboard.conversation_prep.recent_notes.map((item, index) => (
                    <div
                      key={`${item.topic}-${item.occurred_at ?? "none"}-${index}`}
                      className="note-row"
                    >
                      <div className="note-row__top">
                        <strong>{item.topic}</strong>
                        <span className={`pill pill--${item.share_level.toLowerCase()}`}>
                          {item.share_level_label}
                        </span>
                      </div>
                      <p>{truncate(item.text, 140)}</p>
                      <span className="note-row__date">
                        {formatDateTime(item.occurred_at)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="detail-section">
              <div className="section-title">
                <h3>最近の記録</h3>
                <span>{detailDashboard.recent_interactions.length}件</span>
              </div>
              {detailDashboard.recent_interactions.length === 0 ? (
                <p className="muted">まだ記録はありません。</p>
              ) : (
                <div className="history-list">
                  {detailDashboard.recent_interactions.map((item) =>
                    renderRecentInteractionCard(item)
                  )}
                </div>
              )}
            </section>
          </>
        )}
      </section>
    </section>
  );

  const renderManageView = () => (
    <section className="layout layout--manage">
      <section className="panel panel--main">
        <div className="panel__header">
          <p className="eyebrow">管理画面</p>
          <h2>コミュニティと話題の階層を整える</h2>
          <p className="panel__lead">
            大学 / サークル / 活動 のような構造を先に作っておくと、入力と検索が安定します。
          </p>
        </div>

        <div className="manage-grid">
          <article className="manage-block">
            <div className="manage-block__header">
              <h3>コミュニティ階層</h3>
              <span>{communities.length}件</span>
            </div>
            <div className="hierarchy-list">
              {communities.length === 0 ? (
                <p className="muted">コミュニティはまだありません。</p>
              ) : (
                communities.map((community) => (
                  <div key={community.id} className="hierarchy-row">
                    <strong>{community.name}</strong>
                    <span>{community.path}</span>
                  </div>
                ))
              )}
            </div>
          </article>

          <article className="manage-block">
            <div className="manage-block__header">
              <h3>話題階層</h3>
              <span>{topics.length}件</span>
            </div>
            <div className="hierarchy-list">
              {topics.length === 0 ? (
                <p className="muted">話題はまだありません。</p>
              ) : (
                topics.map((topic) => (
                  <div key={topic.id} className="hierarchy-row">
                    <strong>{topic.name}</strong>
                    <span>{topic.path}</span>
                  </div>
                ))
              )}
            </div>
          </article>
        </div>

        <div className="manage-grid manage-grid--forms">
          <article className="mini-card">
            <h3>新しいコミュニティを追加</h3>
            <label className="field">
              <span className="field__label">コミュニティ名</span>
              <input
                value={newCommunityName}
                onChange={(e) => setNewCommunityName(e.target.value)}
                placeholder="例: 活動"
              />
            </label>
            <label className="field">
              <span className="field__label">親コミュニティ</span>
              <select
                value={newCommunityParentId}
                onChange={(e) => setNewCommunityParentId(e.target.value)}
              >
                <option value="">-- なし --</option>
                {communities.map((community) => (
                  <option key={community.id} value={community.id}>
                    {community.path}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="button button--secondary"
              onClick={handleCreateCommunity}
              disabled={isCreatingCommunity}
            >
              {isCreatingCommunity ? "追加中..." : "コミュニティを追加"}
            </button>
          </article>

          <article className="mini-card">
            <h3>新しい話題を追加</h3>
            <label className="field">
              <span className="field__label">話題名</span>
              <input
                value={newTopicName}
                onChange={(e) => setNewTopicName(e.target.value)}
                placeholder="例: 自己紹介 / 価値観"
              />
            </label>
            <label className="field">
              <span className="field__label">親話題</span>
              <select
                value={newTopicParentId}
                onChange={(e) => setNewTopicParentId(e.target.value)}
              >
                <option value="">-- なし --</option>
                {topics.map((topic) => (
                  <option key={topic.id} value={topic.id}>
                    {topic.path}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="button button--secondary"
              onClick={handleCreateTopic}
              disabled={isCreatingTopic}
            >
              {isCreatingTopic ? "追加中..." : "話題を追加"}
            </button>
          </article>
        </div>
      </section>
    </section>
  );

  return (
    <main className="shell">
      <div className="shell__glow shell__glow--left" />
      <div className="shell__glow shell__glow--right" />

      <section className="hero">
        <div className="hero__copy">
          <p className="eyebrow">勿忘草</p>
          <h1>勿忘草</h1>
          <p className="hero__lead">
            面接でも日常会話でも、誰に何をどこまで話したかをあとからすぐ思い出せる
            形で残します。人、場、話題の階層をまとめて扱える会話ログです。
          </p>
        </div>

        <div className="hero__stats">
          <article className="stat-card">
            <span className="stat-card__label">記録数</span>
            <strong>{summaryLoading ? "..." : interactions.length}</strong>
            <p>保存されているやり取りの総数です。</p>
          </article>
          <article className="stat-card">
            <span className="stat-card__label">人 / コミュニティ / 話題</span>
            <strong>
              {persons.length} / {communities.length} / {topics.length}
            </strong>
            <p>候補を整えるほど入力と検索がしやすくなります。</p>
          </article>
          <article className="stat-card">
            <span className="stat-card__label">今の共有レベル</span>
            <strong>{selectedShareLevel?.label ?? "-"}</strong>
            <p>
              {selectedType?.description ??
                "やり取りの種類と共有レベルを分けて保存できます。"}
            </p>
          </article>
        </div>
      </section>

      <section className="view-switcher view-switcher--four">
        {viewOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`view-pill ${viewMode === option.value ? "view-pill--active" : ""}`}
            onClick={() => setViewMode(option.value)}
          >
            <strong>{option.label}</strong>
            <span>{option.description}</span>
          </button>
        ))}
      </section>

      {feedback ? (
        <section className={`banner banner--${feedback.tone}`}>
          <p>{feedback.message}</p>
        </section>
      ) : null}

      {viewMode === "record" ? renderRecordView() : null}
      {viewMode === "history" ? renderHistoryView() : null}
      {viewMode === "person" ? renderPersonView() : null}
      {viewMode === "manage" ? renderManageView() : null}
    </main>
  );
}
