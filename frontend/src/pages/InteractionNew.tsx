import { PointerEvent, useEffect, useRef, useState } from "react";

import { useIsMobile } from "../hooks/useIsMobile";

type Person = {
  id: string;
  name: string;
  is_hidden: boolean;
  primary_community_id: string | null;
  primary_community_path: string | null;
};

type Community = {
  id: string;
  name: string;
  is_hidden: boolean;
  parent_id: string | null;
  path: string;
};

type Topic = {
  id: string;
  name: string;
  parent_id: string | null;
  path: string;
};

type TopicTreeNode = Topic & {
  children: TopicTreeNode[];
};

type PersonBubble = {
  person: Person;
  count: number;
  size: number;
  distance: number;
  x: number;
  y: number;
};

type HomeViewProps = {
  personBubbles: PersonBubble[];
  selectedPersonId: string;
  recentInteractions: InteractionRecord[];
  onBubbleSelect: (personId: string) => void;
  onOpenHistory: () => void;
};

type InteractionType =
  | "MEETING"
  | "CHAT"
  | "CALL"
  | "MESSAGE"
  | "OBSERVATION";

type ShareLevel = "SHARED" | "PARTIAL" | "WITHHELD";
type PageId = "home" | "record" | "history" | "person" | "manage";
type PersonPanelId = "summary" | "topics" | "notes" | "recent";
type ManagePanelId = "people" | "communities" | "topics";

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
  share_level: ShareLevel;
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

const interactionTypeOptions: Array<{
  value: InteractionType;
  label: string;
  description: string;
}> = [
  { value: "MEETING", label: "対面", description: "直接会って話した内容を記録します。" },
  { value: "CHAT", label: "会話", description: "雑談や立ち話を残します。" },
  { value: "CALL", label: "通話", description: "電話やオンライン通話の内容をまとめます。" },
  { value: "MESSAGE", label: "メッセージ", description: "テキストのやり取りを記録します。" },
  { value: "OBSERVATION", label: "出来事メモ", description: "その場で見たことや感じたことを残します。" },
];

const shareLevelOptions: Array<{
  value: ShareLevel;
  label: string;
  description: string;
}> = [
  { value: "SHARED", label: "話した", description: "そのまま共有した内容です。" },
  { value: "PARTIAL", label: "一部だけ話した", description: "少し触れたが全部は話していません。" },
  { value: "WITHHELD", label: "話していない", description: "今回はまだ伏せた内容です。" },
];

const pageOptions: Array<{
  id: PageId;
  label: string;
  mobileLabel: string;
  description: string;
}> = [
  { id: "home", label: "ホーム", mobileLabel: "ホーム", description: "全体の様子を見る" },
  { id: "record", label: "記録", mobileLabel: "記録", description: "会話を記録する" },
  { id: "history", label: "履歴", mobileLabel: "履歴", description: "条件で絞って探す" },
  { id: "person", label: "人物", mobileLabel: "人物", description: "人ごとに整理する" },
  { id: "manage", label: "管理", mobileLabel: "管理", description: "候補と階層を整える" },
];

const mobilePageOrder: PageId[] = ["record", "history", "home", "person", "manage"];
const mobilePageOptions = mobilePageOrder
  .map((pageId) => pageOptions.find((page) => page.id === pageId))
  .filter((page): page is (typeof pageOptions)[number] => Boolean(page));

const personPanelOptions: Array<{
  id: PersonPanelId;
  label: string;
}> = [
  { id: "summary", label: "概要" },
  { id: "topics", label: "話題と場" },
  { id: "notes", label: "補足メモ" },
  { id: "recent", label: "最近の記録" },
];

const managePanelOptions: Array<{
  id: ManagePanelId;
  label: string;
}> = [
  { id: "people", label: "人" },
  { id: "communities", label: "コミュニティ" },
  { id: "topics", label: "話題" },
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

const truncate = (text: string | null | undefined, max = 120) => {
  if (!text) return "内容なし";
  if (text.length <= max) return text;
  return `${text.slice(0, max)}...`;
};

const buildTopicTree = (items: Topic[]): TopicTreeNode[] => {
  const nodes = new Map<string, TopicTreeNode>();
  const roots: TopicTreeNode[] = [];

  items.forEach((topic) => {
    nodes.set(topic.id, { ...topic, children: [] });
  });

  nodes.forEach((node) => {
    if (node.parent_id && nodes.has(node.parent_id)) {
      nodes.get(node.parent_id)?.children.push(node);
      return;
    }
    roots.push(node);
  });

  const sortNodes = (treeNodes: TopicTreeNode[]) => {
    treeNodes.sort((left, right) => left.name.localeCompare(right.name, "ja"));
    treeNodes.forEach((node) => sortNodes(node.children));
  };

  sortNodes(roots);
  return roots;
};

const buildPersonBubbles = (
  people: Person[],
  records: InteractionRecord[],
  communityId: string | null = null,
  maxVisible = 7
): PersonBubble[] => {
  const counts = new Map<string, number>();
  const layoutSlots = [
    { x: 50, y: 50 },
    { x: 31, y: 43 },
    { x: 69, y: 43 },
    { x: 39, y: 73 },
    { x: 61, y: 73 },
    { x: 18, y: 62 },
    { x: 82, y: 62 },
  ];

  records.forEach((record) => {
    if (communityId && record.community_id !== communityId) {
      return;
    }
    counts.set(record.person_id, (counts.get(record.person_id) ?? 0) + 1);
  });

  const maxCount = Math.max(1, ...people.map((person) => counts.get(person.id) ?? 0));

  const sortedBubbles = people
    .map((person) => {
      const count = counts.get(person.id) ?? 0;
      const ratio = count / maxCount;
      const size = Math.round(78 + ratio * 58);
      return {
        person,
        count,
        size,
        distance: 0,
        x: 50,
        y: 50,
      };
    })
    .sort((left, right) => {
      if (right.count !== left.count) return right.count - left.count;
      return left.person.name.localeCompare(right.person.name, "ja");
    })
    .slice(0, maxVisible);

  return sortedBubbles.map((bubble, index) => {
    if (index === 0) {
      return {
        ...bubble,
        distance: 0,
        ...layoutSlots[index],
      };
    }

    const sizePressure = bubble.size / sortedBubbles[0].size;
    const ringPressure = Math.min(1, index / Math.max(1, sortedBubbles.length - 1));
    const distance = 1 + sizePressure * 0.4 + ringPressure * 0.28;
    const slot = layoutSlots[index];

    return {
      ...bubble,
      distance,
      x: 50 + (slot.x - 50) * distance,
      y: 50 + (slot.y - 50) * distance,
    };
  });
};

function NavItem({
  active,
  compact,
  label,
  description,
  onClick,
}: {
  active: boolean;
  compact?: boolean;
  label: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`nav-item ${active ? "nav-item--active" : ""} ${compact ? "nav-item--compact" : ""}`}
      onClick={onClick}
    >
      <strong>{label}</strong>
      {description ? <span>{description}</span> : null}
    </button>
  );
}

function SectionTabs<T extends string>({
  items,
  activeId,
  onSelect,
}: {
  items: Array<{ id: T; label: string }>;
  activeId: T;
  onSelect: (id: T) => void;
}) {
  return (
    <div className="section-tabs">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          className={`section-tab ${activeId === item.id ? "section-tab--active" : ""}`}
          onClick={() => onSelect(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

function MetricCard({
  label,
  value,
  description,
}: {
  label: string;
  value: string | number;
  description: string;
}) {
  return (
    <article className="metric-card">
      <span className="metric-card__label">{label}</span>
      <strong>{value}</strong>
      <p>{description}</p>
    </article>
  );
}

function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}

function SummaryRows({
  items,
  emptyLabel,
}: {
  items: Array<{ title: string; subtitle: string }>;
  emptyLabel: string;
}) {
  if (items.length === 0) {
    return <p className="muted">{emptyLabel}</p>;
  }

  return (
    <div className="summary-list">
      {items.map((item) => (
        <div key={`${item.title}-${item.subtitle}`} className="summary-row">
          <strong>{item.title}</strong>
          <span>{item.subtitle}</span>
        </div>
      ))}
    </div>
  );
}

function TopicTree({
  nodes,
}: {
  nodes: TopicTreeNode[];
}) {
  return (
    <ul className="topic-tree">
      {nodes.map((node) => (
        <li key={node.id} className="topic-tree__item">
          <div className="topic-tree__node">
            <span className="topic-tree__dot" aria-hidden="true" />
            <div className="topic-tree__content">
              <strong>{node.name}</strong>
              <span>{node.path}</span>
            </div>
            {node.children.length > 0 ? (
              <span className="topic-tree__count">{node.children.length}</span>
            ) : null}
          </div>
          {node.children.length > 0 ? <TopicTree nodes={node.children} /> : null}
        </li>
      ))}
    </ul>
  );
}

function PersonBubbleCloud({
  bubbles,
  selectedPersonId,
  onSelect,
  className = "",
  bubbleScale = 1,
}: {
  bubbles: PersonBubble[];
  selectedPersonId: string;
  onSelect: (personId: string) => void;
  className?: string;
  bubbleScale?: number;
}) {
  const [dragging, setDragging] = useState<{
    personId: string;
    originX: number;
    originY: number;
    pointerX: number;
    pointerY: number;
  } | null>(null);

  if (bubbles.length === 0) {
    return (
      <EmptyState
        title="まだ人物がいません"
        description="人物を追加すると、ここに関係の濃さが泡で表示されます。"
      />
    );
  }

  const handlePointerDown = (
    event: PointerEvent<HTMLButtonElement>,
    bubble: PersonBubble
  ) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    setDragging({
      personId: bubble.person.id,
      originX: bubble.x,
      originY: bubble.y,
      pointerX: event.clientX,
      pointerY: event.clientY,
    });
  };

  const handlePointerMove = (event: PointerEvent<HTMLButtonElement>) => {
    if (!dragging) return;

    const parent = event.currentTarget.parentElement;
    if (!parent) return;

    const bounds = parent.getBoundingClientRect();
    const nextX =
      dragging.originX + ((event.clientX - dragging.pointerX) / bounds.width) * 100;
    const nextY =
      dragging.originY + ((event.clientY - dragging.pointerY) / bounds.height) * 100;

    setDragging({
      ...dragging,
      originX: Math.min(90, Math.max(10, nextX)),
      originY: Math.min(86, Math.max(14, nextY)),
      pointerX: event.clientX,
      pointerY: event.clientY,
    });
  };

  const handlePointerEnd = (event: PointerEvent<HTMLButtonElement>) => {
    event.currentTarget.releasePointerCapture(event.pointerId);
    setDragging(null);
  };

  return (
    <div className={`person-bubble-cloud ${className}`}>
      {bubbles.map((bubble, index) => {
        const isDragging = dragging?.personId === bubble.person.id;
        const left = isDragging ? dragging.originX : bubble.x;
        const top = isDragging ? dragging.originY : bubble.y;

        return (
          <button
            key={bubble.person.id}
            type="button"
            className={`person-bubble ${
              selectedPersonId === bubble.person.id ? "person-bubble--active" : ""
            } ${bubble.count === 0 ? "person-bubble--quiet" : ""} ${
              isDragging ? "person-bubble--dragging" : ""
            }`}
          style={{
            width: `${Math.round(bubble.size * bubbleScale)}px`,
            height: `${Math.round(bubble.size * bubbleScale)}px`,
            left: `${Math.min(88, Math.max(12, left))}%`,
            top: `${Math.min(84, Math.max(16, top))}%`,
            animationDelay: `${(index % 6) * -0.7}s`,
          }}
            onPointerDown={(event) => handlePointerDown(event, bubble)}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerEnd}
            onPointerCancel={handlePointerEnd}
            onClick={() => {
              if (!isDragging) onSelect(bubble.person.id);
            }}
            aria-label={`${bubble.person.name}、記録 ${bubble.count}件`}
          >
            <strong>{bubble.person.name}</strong>
            <span>{bubble.count}件</span>
          </button>
        );
      })}
    </div>
  );
}

function HistoryCard({ item }: { item: InteractionRecord }) {
  return (
    <article className="history-card">
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
}

function DesktopHome({
  personBubbles,
  selectedPersonId,
  recentInteractions,
  onBubbleSelect,
  onOpenHistory,
}: HomeViewProps) {
  return (
    <section className="page-stack home-page home-page--desktop">
      <section className="page-card home-bubble-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Home</p>
            <h2>ホーム</h2>
          </div>
          <p className="page-card__lead">
            よく話している人物を中心に、全体の状況を見ます。
          </p>
        </div>

        <PersonBubbleCloud
          bubbles={personBubbles}
          selectedPersonId={selectedPersonId}
          className="person-bubble-cloud--home person-bubble-cloud--desktop-home"
          bubbleScale={1.7}
          onSelect={onBubbleSelect}
        />
      </section>

      <section className="home-secondary-grid">
        <article className="page-card">
          <div className="page-card__header">
            <div>
              <p className="eyebrow">Recent</p>
              <h2>最近のやり取り</h2>
            </div>
            <button
              type="button"
              className="button button--ghost button--small"
              onClick={onOpenHistory}
            >
              履歴画面へ
            </button>
          </div>

          {recentInteractions.length === 0 ? (
            <EmptyState
              title="まだ記録がありません"
              description="記録画面で最初のやり取りを保存すると、ここに表示されます。"
            />
          ) : (
            <div className="history-carousel history-carousel--desktop">
              {recentInteractions.map((item) => (
                <HistoryCard key={item.id} item={item} />
              ))}
            </div>
          )}
        </article>
      </section>
    </section>
  );
}

function MobileHome({
  personBubbles,
  selectedPersonId,
  recentInteractions,
  onBubbleSelect,
  onOpenHistory,
}: HomeViewProps) {
  return (
    <section className="mobile-home-page">
      <div className="mobile-home-swiper" aria-label="Home slides">
        <section className="mobile-home-slide mobile-home-slide--home">
          <section className="page-card mobile-home-bubble-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Home</p>
            <h2>ホーム</h2>
          </div>
        </div>

        <PersonBubbleCloud
          bubbles={personBubbles}
          selectedPersonId={selectedPersonId}
          className="person-bubble-cloud--home person-bubble-cloud--mobile-home"
          bubbleScale={0.92}
          onSelect={onBubbleSelect}
        />
          </section>
        </section>

        <section className="mobile-home-slide mobile-home-slide--recent">
          <section className="mobile-home-recent">
        <article className="page-card">
          <div className="page-card__header mobile-home-recent__header">
            <div>
              <p className="eyebrow">Recent</p>
              <h2>最近のやり取り</h2>
            </div>
            <button
              type="button"
              className="button button--ghost button--small"
              onClick={onOpenHistory}
            >
              履歴へ
            </button>
          </div>

          {recentInteractions.length === 0 ? (
            <EmptyState
              title="まだ記録がありません"
              description="記録画面で最初のやり取りを保存すると、ここに表示されます。"
            />
          ) : (
            <div className="history-list history-list--mobile-home">
              {recentInteractions.map((item) => (
                <HistoryCard key={item.id} item={item} />
              ))}
            </div>
          )}
        </article>
          </section>
        </section>
      </div>
      <div className="mobile-home-pagination" aria-hidden="true">
        <span />
        <span />
      </div>
    </section>
  );
}

export default function InteractionNew() {
  const isMobile = useIsMobile(820);

  const [currentPage, setCurrentPage] = useState<PageId>("home");
  const [personPanel, setPersonPanel] = useState<PersonPanelId>("summary");
  const [managePanel, setManagePanel] = useState<ManagePanelId>("people");
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);
  const [mobileRecordPanel, setMobileRecordPanel] = useState<"input" | "check">("input");
  const mobileRecordSwipeRef = useRef<HTMLDivElement | null>(null);

  const [persons, setPersons] = useState<Person[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [managedPersons, setManagedPersons] = useState<Person[]>([]);
  const [managedCommunities, setManagedCommunities] = useState<Community[]>([]);
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
  const [personActionId, setPersonActionId] = useState<string | null>(null);
  const [communityActionId, setCommunityActionId] = useState<string | null>(null);

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
  const [detailCommunityId, setDetailCommunityId] = useState<string>("");
  const [recordDashboard, setRecordDashboard] = useState<PersonDashboard | null>(null);
  const [detailDashboard, setDetailDashboard] = useState<PersonDashboard | null>(null);

  const selectedPerson = persons.find((person) => person.id === personId);
  const selectedDetailPerson = persons.find((person) => person.id === detailPersonId);
  const selectedType = interactionTypeOptions.find(
    (option) => option.value === interactionType
  );
  const selectedShareLevel = shareLevelOptions.find(
    (option) => option.value === shareLevel
  );

  const fetchJson = async <T,>(url: string): Promise<T> => {
    const response = await fetch(url);
    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || "データ取得に失敗しました。");
    }
    return response.json() as Promise<T>;
  };

  const setError = (message: string) => {
    setFeedback({ tone: "error", message });
  };

  const setSuccess = (message: string) => {
    setFeedback({ tone: "success", message });
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

      const fallbackPerson = personsJson[0] ?? null;
      const currentRecordPerson =
        personsJson.find((person) => person.id === personId) ?? fallbackPerson;
      const currentDetailPerson =
        personsJson.find((person) => person.id === detailPersonId) ?? fallbackPerson;
      const currentHistoryPerson =
        personsJson.find((person) => person.id === historyPersonId) ?? null;

      if (!personId || !currentRecordPerson) {
        setPersonId(currentRecordPerson?.id ?? "");
        setCommunityId(currentRecordPerson?.primary_community_id ?? "");
        setCommunityTouched(false);
      }

      if (!detailPersonId || !currentDetailPerson) {
        setDetailPersonId(currentDetailPerson?.id ?? "");
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
        fetchJson<Person[]>("/api/persons?include_hidden=true"),
        fetchJson<Community[]>("/api/communities?include_hidden=true"),
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
    setSummaryLoading(true);
    try {
      const items = await fetchJson<InteractionRecord[]>("/api/interactions");
      setInteractions(items);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "全体の履歴取得に失敗しました。";
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

      const fromDate = buildDateQuery(historyDateFrom, "from");
      const toDate = buildDateQuery(historyDateTo, "to");
      if (fromDate) params.set("date_from", fromDate);
      if (toDate) params.set("date_to", toDate);

      const query = params.toString();
      const url = query ? `/api/interactions?${query}` : "/api/interactions";
      const items = await fetchJson<InteractionRecord[]>(url);
      setHistoryItems(items);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "履歴の取得に失敗しました。";
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
      const dashboard = await fetchJson<PersonDashboard>(
        `/api/persons/${targetPersonId}/dashboard`
      );
      setRecordDashboard(dashboard);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "会話前の確認情報を取得できませんでした。";
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
      const dashboard = await fetchJson<PersonDashboard>(
        `/api/persons/${targetPersonId}/dashboard`
      );
      setDetailDashboard(dashboard);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "人物ダッシュボードを取得できませんでした。";
      setError(message);
    } finally {
      setDetailDashboardLoading(false);
    }
  };

  useEffect(() => {
    void loadOptions();
    void loadManageData();
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
    await loadManageData();
    await loadOverviewInteractions();
    await loadHistory();

    if (personId) {
      await loadRecordDashboard(personId);
    }
    if (detailPersonId) {
      await loadDetailDashboard(detailPersonId);
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

  const handleSubmit = async () => {
    if (!personId || !content.trim()) {
      setError("相手と内容は必須です。");
      return;
    }

    setIsSaving(true);
    setFeedback({ tone: "info", message: "記録を保存しています..." });

    try {
      const response = await fetch("/api/interactions", {
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

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "保存に失敗しました。");
      }

      setSuccess("やり取りを保存しました。");
      setOccurredAt(toDateTimeLocalValue());
      setContent("");
      setNote("");
      setCommunityTouched(false);
      await loadOverviewInteractions();
      await loadHistory();
      await loadRecordDashboard(personId);
      if (detailPersonId === personId) {
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
      const response = await fetch("/api/persons", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newPersonName.trim(),
          primary_community_id: newPersonPrimaryCommunityId || null,
        }),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "人の追加に失敗しました。");
      }

      const person = (await response.json()) as Person;
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
      const response = await fetch("/api/communities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newCommunityName.trim(),
          parent_id: newCommunityParentId || null,
        }),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "コミュニティの追加に失敗しました。");
      }

      const community = (await response.json()) as Community;
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
      const response = await fetch("/api/topics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newTopicName.trim(),
          parent_id: newTopicParentId || null,
        }),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "話題の追加に失敗しました。");
      }

      const topic = (await response.json()) as Topic;
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
      const response = await fetch(`/api/persons/${person.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_hidden: !person.is_hidden }),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "人物状態の更新に失敗しました。");
      }

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
      const response = await fetch(`/api/persons/${person.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "人物削除に失敗しました。");
      }

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
      const response = await fetch(`/api/communities/${community.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_hidden: !community.is_hidden }),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "コミュニティ状態の更新に失敗しました。");
      }

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
      const response = await fetch(`/api/communities/${community.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "コミュニティ削除に失敗しました。");
      }

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

  const clearHistoryFilters = () => {
    setHistoryPersonId("");
    setHistoryCommunityId("");
    setHistoryTopicId("");
    setHistoryShareLevel("");
    setHistorySearch("");
    setHistoryDateFrom("");
    setHistoryDateTo("");
  };

  const homeRecentInteractions = interactions.slice(0, 4);
  const personMatchesDetailCommunity = (person: Person) => {
    if (!detailCommunityId) return true;
    if (person.primary_community_id === detailCommunityId) return true;
    return interactions.some(
      (item) => item.person_id === person.id && item.community_id === detailCommunityId
    );
  };
  const detailPersons = persons.filter(personMatchesDetailCommunity);
  const homePersonBubbles = buildPersonBubbles(persons, interactions);
  const detailPersonBubbles = buildPersonBubbles(
    detailPersons,
    interactions,
    detailCommunityId || null
  );
  const selectedHistoryLevelLabel =
    shareLevelOptions.find((option) => option.value === historyShareLevel)?.label ?? "すべて";

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
    };

    return isMobile ? <MobileHome {...props} /> : <DesktopHome {...props} />;
  };

  const renderRecordPage = () => {
    const recordFormCard = (
      <section className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Record</p>
            <h2>記録画面</h2>
          </div>
          <p className="page-card__lead">
            ここでは入力だけに集中します。候補の追加は管理画面に分けています。
          </p>
        </div>

        <div className="form-grid">
          <label className="field">
            <span className="field__label">日時</span>
            <input
              type="datetime-local"
              value={occurredAt}
              onChange={(event) => setOccurredAt(event.target.value)}
            />
          </label>

          <label className="field">
            <span className="field__label">相手</span>
            <select
              value={personId}
              onChange={(event) => handlePersonChange(event.target.value)}
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
              onChange={(event) => {
                setCommunityId(event.target.value);
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
              onChange={(event) => setTopicId(event.target.value)}
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
              onChange={(event) =>
                setInteractionType(event.target.value as InteractionType)
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
              onChange={(event) => setShareLevel(event.target.value as ShareLevel)}
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
              onChange={(event) => setContent(event.target.value)}
              placeholder="何を話したか、どこまで共有したかを自然文で残します。"
              rows={5}
            />
          </label>

          <label className="field field--full">
            <span className="field__label">補足メモ</span>
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="次に聞きたいこと、気になった点、注意したいことを残します。"
              rows={4}
            />
          </label>
        </div>

        <div className="action-row">
          <button
            type="button"
            className="button button--primary"
            onClick={handleSubmit}
            disabled={isSaving || loading}
          >
            {isSaving ? "保存中..." : "記録を保存"}
          </button>
          <p className="action-row__hint">
            {communityTouched
              ? "コミュニティは今回だけ手動で変更しています。"
              : `${selectedPerson?.primary_community_path ?? "主な所属未設定"} を初期値にしています。`}
          </p>
        </div>
      </section>
    );

    const beforeTalkCard = (
      <aside className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Before Talk</p>
            <h2>会話前の確認</h2>
          </div>
        </div>

        {!selectedPerson ? (
          <EmptyState
            title="相手を選ぶと確認できます"
            description="この相手について最近話した内容や、まだ伏せている話題を表示します。"
          />
        ) : recordDashboardLoading ? (
          <p className="muted">確認情報を読み込み中です...</p>
        ) : !recordDashboard ? (
          <EmptyState
            title="まだ確認情報がありません"
            description="この相手の記録が増えると、ここが埋まっていきます。"
          />
        ) : (
          <div className="page-stack page-stack--compact">
            <SummaryRows
              items={[
                {
                  title: "主な所属",
                  subtitle: recordDashboard.person.primary_community_path ?? "未設定",
                },
                {
                  title: "最後の記録",
                  subtitle: formatDateTime(recordDashboard.overview.latest_occurred_at),
                },
                {
                  title: "共有状況",
                  subtitle: `話した ${recordDashboard.overview.shared_count} / 一部 ${recordDashboard.overview.partial_count} / 伏せた ${recordDashboard.overview.withheld_count}`,
                },
              ]}
              emptyLabel="表示できる情報がありません。"
            />

            <section className="subsection">
              <h3>すでに話した話題</h3>
              <SummaryRows
                items={recordDashboard.conversation_prep.shared_topics.map((item) => ({
                  title: item.topic,
                  subtitle: `${item.community} / ${formatDateTime(item.occurred_at)}`,
                }))}
                emptyLabel="まだ十分に話した話題はありません。"
              />
            </section>

            <section className="subsection">
              <h3>まだ伏せている話題</h3>
              <SummaryRows
                items={recordDashboard.conversation_prep.withheld_topics.map((item) => ({
                  title: item.topic,
                  subtitle: `${item.community} / ${formatDateTime(item.occurred_at)}`,
                }))}
                emptyLabel="今のところ伏せている話題はありません。"
              />
            </section>
          </div>
        )}
      </aside>
    );

    if (isMobile) {
      return (
        <section className="mobile-record-page">
          <div className="mobile-record-tabs" aria-label="記録画面の切り替え">
            <button
              type="button"
              className={`mobile-record-tab ${
                mobileRecordPanel === "input" ? "mobile-record-tab--active" : ""
              }`}
              onClick={() => switchMobileRecordPanel("input")}
            >
              入力
            </button>
            <button
              type="button"
              className={`mobile-record-tab ${
                mobileRecordPanel === "check" ? "mobile-record-tab--active" : ""
              }`}
              onClick={() => switchMobileRecordPanel("check")}
            >
              確認
            </button>
          </div>
          <div
            ref={mobileRecordSwipeRef}
            className="mobile-record-swipe"
            aria-label="記録画面"
            onScroll={handleMobileRecordScroll}
          >
            <div className="mobile-record-panel">{recordFormCard}</div>
            <div className="mobile-record-panel">{beforeTalkCard}</div>
          </div>
        </section>
      );
    }

    return (
      <section className="page-grid page-grid--record">
        {recordFormCard}
        {beforeTalkCard}
      </section>
    );
  };

  const renderHistoryFilters = () => (
    <div className="page-stack page-stack--compact">
      <div className="filter-grid">
        <label className="field">
          <span className="field__label">人</span>
          <select
            value={historyPersonId}
            onChange={(event) => setHistoryPersonId(event.target.value)}
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
            onChange={(event) => setHistoryCommunityId(event.target.value)}
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
            onChange={(event) => setHistoryTopicId(event.target.value)}
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
            onChange={(event) =>
              setHistoryShareLevel(event.target.value as ShareLevel | "")
            }
          >
            <option value="">-- すべて --</option>
            {shareLevelOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="field field--full">
          <span className="field__label">キーワード</span>
          <input
            value={historySearch}
            onChange={(event) => setHistorySearch(event.target.value)}
            placeholder="内容や補足メモを検索"
          />
        </label>

        <label className="field">
          <span className="field__label">開始日</span>
          <input
            type="date"
            value={historyDateFrom}
            onChange={(event) => setHistoryDateFrom(event.target.value)}
          />
        </label>

        <label className="field">
          <span className="field__label">終了日</span>
          <input
            type="date"
            value={historyDateTo}
            onChange={(event) => setHistoryDateTo(event.target.value)}
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
        <button type="button" className="button button--ghost" onClick={clearHistoryFilters}>
          条件をクリア
        </button>
      </div>
    </div>
  );

  const renderHistoryPage = () => (
    <section className="page-grid page-grid--history">
      <aside className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Filter</p>
            <h2>履歴の絞り込み</h2>
          </div>
        </div>

        {isMobile ? (
          <>
            <div className="mobile-filter-summary">
              <span>人: {persons.find((person) => person.id === historyPersonId)?.name ?? "すべて"}</span>
              <span>共有レベル: {selectedHistoryLevelLabel}</span>
            </div>
            <button
              type="button"
              className="button button--ghost mobile-filter-toggle"
              onClick={() => setMobileFilterOpen((current) => !current)}
            >
              {mobileFilterOpen ? "フィルターを閉じる" : "フィルターを開く"}
            </button>
            {mobileFilterOpen ? <div className="mobile-filter-body">{renderHistoryFilters()}</div> : null}
          </>
        ) : (
          renderHistoryFilters()
        )}
      </aside>

      <section className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">History</p>
            <h2>履歴一覧</h2>
          </div>
          <div className="history-summary">
            <span>表示 {historyItems.length}件</span>
            <span>
              伏せた {historyItems.filter((item) => item.share_level === "WITHHELD").length}件
            </span>
          </div>
        </div>

        {historyItems.length === 0 ? (
          <EmptyState
            title="条件に合う履歴がありません"
            description="フィルターを緩めるか、新しい記録を追加してください。"
          />
        ) : (
          <div className="history-list">
            {historyItems.map((item) => (
              <HistoryCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </section>
    </section>
  );

  const renderPersonPage = () => {
    const topicRows =
      detailDashboard?.top_topics.map((item) => ({
        title: item.label,
        subtitle: `${item.count}件 / 話した ${item.shared_count} / 一部 ${item.partial_count} / 伏せた ${item.withheld_count}`,
      })) ?? [];

    const communityRows =
      detailDashboard?.top_communities.map((item) => ({
        title: item.label,
        subtitle: `${item.count}件 / 話した ${item.shared_count} / 一部 ${item.partial_count} / 伏せた ${item.withheld_count}`,
      })) ?? [];

    return (
      <section className="page-stack">
        <section className="page-card">
          <div className="page-card__header">
            <div>
              <p className="eyebrow">Person</p>
              <h2>よく話す人物</h2>
            </div>
            <p className="page-card__lead">
              話した回数が多い人物を中心に表示します。
            </p>
          </div>

          <PersonBubbleCloud
            bubbles={detailPersonBubbles}
            selectedPersonId={detailPersonId}
            onSelect={openRecordForPerson}
          />

          <div className="page-toolbar person-map-toolbar">
            <label className="field field--toolbar">
              <span className="field__label">コミュニティで絞る</span>
              <select
                value={detailCommunityId}
                onChange={(event) => {
                  const nextCommunityId = event.target.value;
                  setDetailCommunityId(nextCommunityId);
                  setPersonPanel("summary");

                  const nextPersons = persons.filter((person) => {
                    if (!nextCommunityId) return true;
                    if (person.primary_community_id === nextCommunityId) return true;
                    return interactions.some(
                      (item) =>
                        item.person_id === person.id &&
                        item.community_id === nextCommunityId
                    );
                  });

                  if (
                    detailPersonId &&
                    !nextPersons.some((person) => person.id === detailPersonId)
                  ) {
                    setDetailPersonId(nextPersons[0]?.id ?? "");
                  }
                }}
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
            <label className="field field--toolbar">
              <span className="field__label">人物を直接選ぶ</span>
              <select
                value={detailPersonId}
                onChange={(event) => {
                  setDetailPersonId(event.target.value);
                  setPersonPanel("summary");
                }}
                disabled={loading}
              >
                <option value="">-- 選択してください --</option>
                {detailPersons.map((person) => (
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
          </div>

          <SectionTabs
            items={personPanelOptions}
            activeId={personPanel}
            onSelect={setPersonPanel}
          />
        </section>

        {!detailDashboard ? (
          <EmptyState
            title="人物を選ぶと要約が出ます"
            description="主な所属、共有状況、最近の話題をここで分けて見られます。"
          />
        ) : null}

        {detailDashboard && personPanel === "summary" ? (
          <section className="page-grid page-grid--two">
            <article className="page-card">
              <div className="page-card__header">
                <div>
                  <p className="eyebrow">Summary</p>
                  <h2>{selectedDetailPerson?.name ?? detailDashboard.person.name}</h2>
                </div>
              </div>

              <div className="metric-grid metric-grid--compact">
                <MetricCard
                  label="記録数"
                  value={detailDashboard.overview.interaction_count}
                  description="この人に関する総記録数です。"
                />
                <MetricCard
                  label="話した"
                  value={detailDashboard.overview.shared_count}
                  description="しっかり共有した内容です。"
                />
                <MetricCard
                  label="一部だけ話した"
                  value={detailDashboard.overview.partial_count}
                  description="途中まで触れた内容です。"
                />
                <MetricCard
                  label="話していない"
                  value={detailDashboard.overview.withheld_count}
                  description="今は伏せている内容です。"
                />
              </div>
            </article>

            <article className="page-card">
              <div className="page-card__header">
                <div>
                  <p className="eyebrow">Basics</p>
                  <h2>基本情報</h2>
                </div>
              </div>

              <SummaryRows
                items={[
                  {
                    title: "主な所属",
                    subtitle: detailDashboard.person.primary_community_path ?? "未設定",
                  },
                  {
                    title: "最後の記録",
                    subtitle: formatDateTime(detailDashboard.overview.latest_occurred_at),
                  },
                  ...detailDashboard.share_summary.map((item) => ({
                    title: item.label,
                    subtitle: `${item.count}件`,
                  })),
                ]}
                emptyLabel="表示できる情報がありません。"
              />
            </article>
          </section>
        ) : null}

        {detailDashboard && personPanel === "topics" ? (
          <section className="page-grid page-grid--two">
            <article className="page-card">
              <div className="page-card__header">
                <div>
                  <p className="eyebrow">Topics</p>
                  <h2>よく出る話題</h2>
                </div>
              </div>
              <SummaryRows items={topicRows} emptyLabel="話題のまとまりはまだありません。" />
            </article>

            <article className="page-card">
              <div className="page-card__header">
                <div>
                  <p className="eyebrow">Communities</p>
                  <h2>よく関わる場</h2>
                </div>
              </div>
              <SummaryRows
                items={communityRows}
                emptyLabel="コミュニティのまとまりはまだありません。"
              />
            </article>

            <article className="page-card">
              <div className="page-card__header">
                <div>
                  <p className="eyebrow">Shared</p>
                  <h2>すでに話した話題</h2>
                </div>
              </div>
              <SummaryRows
                items={detailDashboard.conversation_prep.shared_topics.map((item) => ({
                  title: item.topic,
                  subtitle: `${item.community} / ${formatDateTime(item.occurred_at)}`,
                }))}
                emptyLabel="まだ十分に話した話題はありません。"
              />
            </article>

            <article className="page-card">
              <div className="page-card__header">
                <div>
                  <p className="eyebrow">Withheld</p>
                  <h2>まだ伏せている話題</h2>
                </div>
              </div>
              <SummaryRows
                items={detailDashboard.conversation_prep.withheld_topics.map((item) => ({
                  title: item.topic,
                  subtitle: `${item.community} / ${formatDateTime(item.occurred_at)}`,
                }))}
                emptyLabel="今のところ伏せている話題はありません。"
              />
            </article>
          </section>
        ) : null}

        {detailDashboard && personPanel === "notes" ? (
          <section className="page-card">
            <div className="page-card__header">
              <div>
                <p className="eyebrow">Notes</p>
                <h2>補足メモ</h2>
              </div>
            </div>
            {detailDashboard.conversation_prep.recent_notes.length === 0 ? (
              <EmptyState
                title="補足メモはまだありません"
                description="補足メモを残すと、この画面でまとめて確認できます。"
              />
            ) : (
              <div className="summary-list">
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
                    <p>{truncate(item.text, 160)}</p>
                    <span className="note-row__date">
                      {formatDateTime(item.occurred_at)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>
        ) : null}

        {detailDashboard && personPanel === "recent" ? (
          <section className="page-card">
            <div className="page-card__header">
              <div>
                <p className="eyebrow">Recent</p>
                <h2>最近の記録</h2>
              </div>
            </div>
            {detailDashboard.recent_interactions.length === 0 ? (
              <EmptyState
                title="まだ最近の記録はありません"
                description="記録が増えるとここに並びます。"
              />
            ) : (
              <div className="history-list">
                {detailDashboard.recent_interactions.map((item) => (
                  <HistoryCard key={item.id} item={item} />
                ))}
              </div>
            )}
          </section>
        ) : null}
      </section>
    );
  };

  const renderPeopleManagePanel = () => (
    <section className="page-grid page-grid--two">
      <article className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">People</p>
            <h2>人を追加</h2>
          </div>
        </div>

        <label className="field">
          <span className="field__label">名前</span>
          <input
            value={newPersonName}
            onChange={(event) => setNewPersonName(event.target.value)}
            placeholder="例: 田中さん"
          />
        </label>
        <label className="field">
          <span className="field__label">主な所属コミュニティ</span>
          <select
            value={newPersonPrimaryCommunityId}
            onChange={(event) => setNewPersonPrimaryCommunityId(event.target.value)}
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

      <article className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">People List</p>
            <h2>登録済みの人</h2>
          </div>
        </div>

        {persons.length === 0 ? (
          <EmptyState
            title="まだ人がいません"
            description="まずは数人だけ追加すると記録がしやすくなります。"
          />
        ) : (
          <SummaryRows
            items={persons.map((person) => ({
              title: person.name,
              subtitle: person.primary_community_path ?? "主な所属なし",
            }))}
            emptyLabel="人はまだいません。"
          />
        )}
      </article>
    </section>
  );

  const renderCommunitiesManagePanel = () => (
    <section className="page-grid page-grid--two">
      <article className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Community</p>
            <h2>コミュニティを追加</h2>
          </div>
        </div>

        <label className="field">
          <span className="field__label">コミュニティ名</span>
          <input
            value={newCommunityName}
            onChange={(event) => setNewCommunityName(event.target.value)}
            placeholder="例: 飲み"
          />
        </label>
        <label className="field">
          <span className="field__label">親コミュニティ</span>
          <select
            value={newCommunityParentId}
            onChange={(event) => setNewCommunityParentId(event.target.value)}
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

      <article className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Community Tree</p>
            <h2>コミュニティ階層</h2>
          </div>
        </div>

        {communities.length === 0 ? (
          <EmptyState
            title="コミュニティはまだありません"
            description="大学 / サークル / 活動 のような形で先に整理できます。"
          />
        ) : (
          <SummaryRows
            items={communities.map((community) => ({
              title: community.name,
              subtitle: community.path,
            }))}
            emptyLabel="コミュニティはまだありません。"
          />
        )}
      </article>
    </section>
  );

  const renderPeopleManagePanelV2 = () => {
    const sortedPeople = [...managedPersons].sort((left, right) =>
      left.name.localeCompare(right.name, "ja")
    );

    return (
      <section className="page-grid page-grid--two">
        <article className="page-card">
          <div className="page-card__header">
            <div>
              <p className="eyebrow">People</p>
              <h2>人物を追加</h2>
            </div>
          </div>

          <label className="field">
            <span className="field__label">名前</span>
            <input
              value={newPersonName}
              onChange={(event) => setNewPersonName(event.target.value)}
              placeholder="例: 田中 花子"
            />
          </label>
          <label className="field">
            <span className="field__label">主な所属コミュニティ</span>
            <select
              value={newPersonPrimaryCommunityId}
              onChange={(event) => setNewPersonPrimaryCommunityId(event.target.value)}
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
            {isCreatingPerson ? "追加中..." : "人物を追加"}
          </button>
        </article>

        <article className="page-card">
          <div className="page-card__header">
            <div>
              <p className="eyebrow">People List</p>
              <h2>人物の管理</h2>
            </div>
          </div>

          {sortedPeople.length === 0 ? (
            <EmptyState
              title="まだ人物がいません"
              description="まずは左側のフォームから人物を追加してください。"
            />
          ) : (
            <div className="manage-list">
              {sortedPeople.map((person) => {
                const isBusy = personActionId === person.id;

                return (
                  <div key={person.id} className="manage-entry">
                    <div className="manage-entry__main">
                      <div className="manage-entry__title">
                        <strong>{person.name}</strong>
                        {person.is_hidden ? (
                          <span className="status-tag">非表示</span>
                        ) : null}
                      </div>
                      <span>{person.primary_community_path ?? "主な所属なし"}</span>
                    </div>

                    <div className="manage-entry__actions">
                      <button
                        type="button"
                        className="button button--ghost button--small"
                        onClick={() => void handleTogglePersonHidden(person)}
                        disabled={isBusy}
                      >
                        {isBusy
                          ? "更新中..."
                          : person.is_hidden
                            ? "再表示"
                            : "非表示"}
                      </button>
                      <button
                        type="button"
                        className="button button--danger button--small"
                        onClick={() => void handleDeletePerson(person)}
                        disabled={isBusy}
                      >
                        {isBusy ? "削除中..." : "削除"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </article>
      </section>
    );
  };

  const renderCommunitiesManagePanelV2 = () => {
    const sortedCommunities = [...managedCommunities].sort((left, right) =>
      left.path.localeCompare(right.path, "ja")
    );

    return (
      <section className="page-grid page-grid--two">
        <article className="page-card">
          <div className="page-card__header">
            <div>
              <p className="eyebrow">Community</p>
              <h2>コミュニティを追加</h2>
            </div>
          </div>

          <label className="field">
            <span className="field__label">コミュニティ名</span>
            <input
              value={newCommunityName}
              onChange={(event) => setNewCommunityName(event.target.value)}
              placeholder="例: 飲み会"
            />
          </label>
          <label className="field">
            <span className="field__label">親コミュニティ</span>
            <select
              value={newCommunityParentId}
              onChange={(event) => setNewCommunityParentId(event.target.value)}
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

        <article className="page-card">
          <div className="page-card__header">
            <div>
              <p className="eyebrow">Community Tree</p>
              <h2>コミュニティの管理</h2>
            </div>
          </div>

          {sortedCommunities.length === 0 ? (
            <EmptyState
              title="まだコミュニティがありません"
              description="大学→サークル→活動のように階層で追加できます。"
            />
          ) : (
            <div className="manage-list">
              {sortedCommunities.map((community) => {
                const isBusy = communityActionId === community.id;

                return (
                  <div key={community.id} className="manage-entry">
                    <div className="manage-entry__main">
                      <div className="manage-entry__title">
                        <strong>{community.name}</strong>
                        {community.is_hidden ? (
                          <span className="status-tag">非表示</span>
                        ) : null}
                      </div>
                      <span>{community.path}</span>
                    </div>

                    <div className="manage-entry__actions">
                      <button
                        type="button"
                        className="button button--ghost button--small"
                        onClick={() => void handleToggleCommunityHidden(community)}
                        disabled={isBusy}
                      >
                        {isBusy
                          ? "更新中..."
                          : community.is_hidden
                            ? "再表示"
                            : "非表示"}
                      </button>
                      <button
                        type="button"
                        className="button button--danger button--small"
                        onClick={() => void handleDeleteCommunity(community)}
                        disabled={isBusy}
                      >
                        {isBusy ? "削除中..." : "削除"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </article>
      </section>
    );
  };

  const renderTopicsManagePanel = () => {
    const topicTree = buildTopicTree(topics);

    return (
      <section className="page-grid page-grid--two">
        <article className="page-card">
          <div className="page-card__header">
            <div>
              <p className="eyebrow">Topic</p>
              <h2>話題を追加</h2>
            </div>
          </div>

          <label className="field">
            <span className="field__label">話題名</span>
            <input
              value={newTopicName}
              onChange={(event) => setNewTopicName(event.target.value)}
              placeholder="例: 面接 / 自己紹介"
            />
          </label>
          <label className="field">
            <span className="field__label">親話題</span>
            <select
              value={newTopicParentId}
              onChange={(event) => setNewTopicParentId(event.target.value)}
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

        <article className="page-card">
          <div className="page-card__header">
            <div>
              <p className="eyebrow">Topic Tree</p>
              <h2>話題階層</h2>
            </div>
          </div>

          {topicTree.length === 0 ? (
            <EmptyState
              title="話題はまだありません"
              description="就活 / 面接 / 自己紹介 のような形で整理できます。"
            />
          ) : (
            <div className="topic-tree-panel">
              <TopicTree nodes={topicTree} />
            </div>
          )}
        </article>
      </section>
    );
  };

  const renderManagePage = () => (
    <section className="page-stack">
      <section className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Manage</p>
            <h2>管理画面</h2>
          </div>
          <p className="page-card__lead">
            管理画面の中も、人・コミュニティ・話題で分けてあります。
          </p>
        </div>

        <SectionTabs
          items={managePanelOptions}
          activeId={managePanel}
          onSelect={setManagePanel}
        />
      </section>

      {managePanel === "people" ? renderPeopleManagePanelV2() : null}
      {managePanel === "communities" ? renderCommunitiesManagePanelV2() : null}
      {managePanel === "topics" ? renderTopicsManagePanel() : null}
    </section>
  );

  const renderPage = () => {
    switch (currentPage) {
      case "record":
        return renderRecordPage();
      case "history":
        return renderHistoryPage();
      case "person":
        return renderPersonPage();
      case "manage":
        return renderManagePage();
      case "home":
      default:
        return renderHomePage();
    }
  };

  return (
    <main
      className={`app-shell ${isMobile ? "app-shell--mobile" : "app-shell--desktop"} ${
        currentPage === "home" ? "app-shell--home" : ""
      }`}
    >
      <div className="app-shell__glow app-shell__glow--left" />
      <div className="app-shell__glow app-shell__glow--right" />

      {!isMobile ? (
        <div className="desktop-frame">
          <aside className="desktop-sidebar">
            <div className="brand-card">
              <p className="eyebrow">勿忘草</p>
              <h1>勿忘草</h1>
              <p>
                PC では左ナビでページを切り替え、右側はその目的だけに集中できる構成です。
              </p>
            </div>

            <nav className="nav-list">
              {pageOptions.map((page) => (
                <NavItem
                  key={page.id}
                  active={currentPage === page.id}
                  label={page.label}
                  description={page.description}
                  onClick={() => setCurrentPage(page.id)}
                />
              ))}
            </nav>

            <div className="sidebar-summary">
              <div className="sidebar-summary__item">
                <strong>{interactions.length}</strong>
                <span>記録数</span>
              </div>
              <div className="sidebar-summary__item">
                <strong>{persons.length}</strong>
                <span>人</span>
              </div>
              <div className="sidebar-summary__item">
                <strong>{communities.length}</strong>
                <span>コミュニティ</span>
              </div>
            </div>
          </aside>

          <section className="desktop-content">
            {feedback ? (
              <section className={`banner banner--${feedback.tone}`}>
                <p>{feedback.message}</p>
              </section>
            ) : null}
            {renderPage()}
          </section>
        </div>
      ) : (
        <div className="mobile-frame">
          <header className="mobile-header">
            <div>
              <p className="eyebrow">勿忘草</p>
              <h1>勿忘草</h1>
            </div>
            <p>スマホでは 1 画面 1 目的に寄せて、下タブで切り替える構成です。</p>
          </header>

          {feedback ? (
            <section className={`banner banner--${feedback.tone}`}>
              <p>{feedback.message}</p>
            </section>
          ) : null}

          <section className="mobile-content">{renderPage()}</section>

          <nav className="mobile-dock">
            {mobilePageOptions.map((page) => (
              <NavItem
                key={page.id}
                active={currentPage === page.id}
                compact
                label={page.mobileLabel}
                description=""
                onClick={() => setCurrentPage(page.id)}
              />
            ))}
          </nav>
        </div>
      )}
    </main>
  );
}
