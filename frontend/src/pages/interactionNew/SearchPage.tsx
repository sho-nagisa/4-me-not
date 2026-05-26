import type { Dispatch, FormEvent, SetStateAction } from "react";

import { EmptyState } from "./components";
import type {
  SearchAnswer,
  SearchResponse,
  SearchResultItem,
  SearchTargetType,
  TaskRecord,
} from "./types";
import { formatDateTime } from "./utils";

export type SearchScope = "all" | SearchTargetType;

type SearchPageProps = {
  query: string;
  setQuery: Dispatch<SetStateAction<string>>;
  scope: SearchScope;
  setScope: Dispatch<SetStateAction<SearchScope>>;
  scopeOptions?: Array<{ id: SearchScope; label: string }>;
  dateFrom: string;
  setDateFrom: Dispatch<SetStateAction<string>>;
  dateTo: string;
  setDateTo: Dispatch<SetStateAction<string>>;
  fuzzy: boolean;
  setFuzzy: Dispatch<SetStateAction<boolean>>;
  loading: boolean;
  result: SearchResponse | null;
  error: string | null;
  onSearch: (query?: string, scope?: SearchScope) => void | Promise<void>;
  onOpenPerson: (personId: string) => void;
  onOpenRecordForPerson: (personId: string) => void;
  taskCandidates: TaskRecord[];
  taskCandidatesLoading: boolean;
  taskActionId: string | null;
  onAcceptTaskCandidate: (taskId: string) => void | Promise<void>;
  onDismissTaskCandidate: (taskId: string) => void | Promise<void>;
  showTaskCandidates?: boolean;
};

export const defaultSearchScopeOptions: Array<{ id: SearchScope; label: string }> = [
  { id: "all", label: "すべて" },
  { id: "interaction", label: "会話" },
  { id: "task", label: "タスク" },
  { id: "calendar_event", label: "予定" },
  { id: "person", label: "人物" },
  { id: "community", label: "団体" },
  { id: "topic", label: "話題" },
];

const exampleQueries = [
  "発表資料 期限",
  "山田さん 返信",
  "研究室 来週",
  "面接 志望動機",
];

const targetTypeLabels: Record<SearchTargetType, string> = {
  interaction: "会話",
  task: "タスク",
  calendar_event: "予定",
  person: "人物",
  community: "団体",
  topic: "話題",
};

const sourceTypeLabels: Record<string, string> = {
  interaction: "会話から抽出",
  calendar_event: "予定から抽出",
  manual_note: "手入力",
  manual: "手入力",
};

const taskStatusLabels: Record<string, string> = {
  TODO: "未完了",
  DONE: "完了",
  SKIPPED: "見送り",
};

export function SearchPage({
  query,
  setQuery,
  scope,
  setScope,
  scopeOptions = defaultSearchScopeOptions,
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
  fuzzy,
  setFuzzy,
  loading,
  result,
  error,
  onSearch,
  onOpenPerson,
  onOpenRecordForPerson,
  taskCandidates,
  taskCandidatesLoading,
  taskActionId,
  onAcceptTaskCandidate,
  onDismissTaskCandidate,
  showTaskCandidates = true,
}: SearchPageProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void onSearch();
  };

  const peopleResults = result?.groups.people ?? [];
  const interactionResults = result?.groups.interactions ?? [];
  const taskResults = result?.groups.tasks ?? [];
  const calendarEventResults = result?.groups.calendar_events ?? [];
  const relationResults = [
    ...(result?.groups.communities ?? []),
    ...(result?.groups.topics ?? []),
  ];
  const hasResults = Boolean(result && result.results.length > 0);

  return (
    <section className="page-stack search-page">
      <section className="page-card search-panel">
        <div className="page-card__header search-panel__header">
          <div>
            <p className="eyebrow">Search</p>
            <h2>記憶検索</h2>
          </div>
        </div>

        <form className="search-form" onSubmit={handleSubmit}>
          <label className="field search-form__field">
            <span className="field__label">思い出したいこと</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="例: 来週までに山田さんへ送る資料"
            />
          </label>

          <div className="search-scope" aria-label="検索対象">
            {scopeOptions.map((option) => (
              <button
                key={option.id}
                type="button"
                className={`search-scope__item ${
                  scope === option.id ? "search-scope__item--active" : ""
                }`}
                onClick={() => {
                  setScope(option.id);
                  if (query.trim()) {
                    void onSearch(query, option.id);
                  }
                }}
              >
                {option.label}
              </button>
            ))}
          </div>

          <div className="search-date-filter">
            <label className="field">
              <span className="field__label">開始日</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(event) => setDateFrom(event.target.value)}
              />
            </label>
            <label className="field">
              <span className="field__label">終了日</span>
              <input
                type="date"
                value={dateTo}
                onChange={(event) => setDateTo(event.target.value)}
              />
            </label>
            <label className="search-fuzzy-toggle">
              <input
                type="checkbox"
                checked={fuzzy}
                onChange={(event) => setFuzzy(event.target.checked)}
              />
              <span>あいまい一致</span>
            </label>
          </div>

          <div className="button-row search-form__actions">
            <button
              type="submit"
              className="button button--primary"
              disabled={loading || !query.trim()}
            >
              {loading ? "検索中..." : "検索する"}
            </button>
            <div className="search-examples">
              {exampleQueries.map((example) => (
                <button
                  key={example}
                  type="button"
                  className="button button--ghost button--small"
                  onClick={() => {
                    setQuery(example);
                    void onSearch(example, scope);
                  }}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </form>

        {error ? <p className="search-error">{error}</p> : null}
      </section>

      {showTaskCandidates ? (
        <TaskCandidatePanel
          candidates={taskCandidates}
          loading={taskCandidatesLoading}
          taskActionId={taskActionId}
          onAcceptTaskCandidate={onAcceptTaskCandidate}
          onDismissTaskCandidate={onDismissTaskCandidate}
        />
      ) : null}

      {result?.answer ? (
        <SearchAnswerCard
          answer={result.answer}
          setQuery={setQuery}
          onOpenPerson={onOpenPerson}
          onSearch={onSearch}
        />
      ) : null}

      {!result ? (
        <section className="page-card">
          <EmptyState
            title="まだ検索していません"
            description="人物名、予定、締め切り、話した内容をそのまま入力できます。"
          />
        </section>
      ) : !hasResults ? (
        <section className="page-card">
          <EmptyState
            title="候補が見つかりませんでした"
            description="単語を短くするか、人物名・日付・タスク名を入れて検索してみてください。"
          />
        </section>
      ) : (
        <section className="search-results-grid search-results-grid--memory">
          <SearchGroup
            title="会話"
            items={interactionResults}
            emptyLabel="関連する会話はまだありません。"
            onOpenPerson={onOpenPerson}
            onOpenRecordForPerson={onOpenRecordForPerson}
            taskActionId={taskActionId}
            onAcceptTaskCandidate={onAcceptTaskCandidate}
            onDismissTaskCandidate={onDismissTaskCandidate}
          />
          <SearchGroup
            title="タスク"
            items={taskResults}
            emptyLabel="関連するタスクはまだありません。"
            onOpenPerson={onOpenPerson}
            onOpenRecordForPerson={onOpenRecordForPerson}
            taskActionId={taskActionId}
            onAcceptTaskCandidate={onAcceptTaskCandidate}
            onDismissTaskCandidate={onDismissTaskCandidate}
          />
          <SearchGroup
            title="予定"
            items={calendarEventResults}
            emptyLabel="関連する予定はまだありません。"
            onOpenPerson={onOpenPerson}
            onOpenRecordForPerson={onOpenRecordForPerson}
            taskActionId={taskActionId}
            onAcceptTaskCandidate={onAcceptTaskCandidate}
            onDismissTaskCandidate={onDismissTaskCandidate}
          />
          <SearchGroup
            title="人物"
            items={peopleResults}
            emptyLabel="関連する人物はまだありません。"
            onOpenPerson={onOpenPerson}
            onOpenRecordForPerson={onOpenRecordForPerson}
            taskActionId={taskActionId}
            onAcceptTaskCandidate={onAcceptTaskCandidate}
            onDismissTaskCandidate={onDismissTaskCandidate}
          />
          <SearchGroup
            title="団体・話題"
            items={relationResults}
            emptyLabel="関連する団体・話題はまだありません。"
            compact
            onOpenPerson={onOpenPerson}
            onOpenRecordForPerson={onOpenRecordForPerson}
            taskActionId={taskActionId}
            onAcceptTaskCandidate={onAcceptTaskCandidate}
            onDismissTaskCandidate={onDismissTaskCandidate}
          />
        </section>
      )}
    </section>
  );
}

export function TaskCandidatePanel({
  candidates,
  loading,
  taskActionId,
  onAcceptTaskCandidate,
  onDismissTaskCandidate,
}: {
  candidates: TaskRecord[];
  loading: boolean;
  taskActionId: string | null;
  onAcceptTaskCandidate: (taskId: string) => void | Promise<void>;
  onDismissTaskCandidate: (taskId: string) => void | Promise<void>;
}) {
  return (
    <section className="page-card task-candidate-panel">
      <div className="page-card__header task-candidate-panel__header">
        <div>
          <p className="eyebrow">Task Candidates</p>
          <h2>タスク候補</h2>
        </div>
        <span className="task-candidate-badge">
          {loading ? "読込中" : `${candidates.length}件`}
        </span>
      </div>

      {loading ? (
        <p className="muted">タスク候補を読み込んでいます。</p>
      ) : candidates.length === 0 ? (
        <p className="muted">
          未確認のタスク候補はありません。会話を記録すると、期限や対応が含まれる文から候補を作ります。
        </p>
      ) : (
        <div className="task-candidate-list">
          {candidates.map((task) => {
            const isBusy = taskActionId === task.id;
            const metaItems = getTaskCandidateMetaItems(task);

            return (
              <article key={task.id} className="task-candidate-card">
                <div className="task-candidate-card__top">
                  <div>
                    <span className="task-candidate-card__type">
                      {sourceTypeLabels[task.source_type] ?? task.source_type}
                    </span>
                    <h3>{task.title}</h3>
                  </div>
                  <strong>{formatConfidence(task.confidence)}</strong>
                </div>

                {task.description ? (
                  <p className="task-candidate-card__description">
                    {task.description}
                  </p>
                ) : null}

                <div className="task-candidate-card__meta">
                  {metaItems.map((meta) => (
                    <span key={`${task.id}:${meta.label}:${meta.value}`}>
                      {meta.label}: {meta.value}
                    </span>
                  ))}
                </div>

                <div className="task-candidate-card__actions">
                  <button
                    type="button"
                    className="button button--primary button--small"
                    disabled={isBusy}
                    onClick={() => {
                      void onAcceptTaskCandidate(task.id);
                    }}
                  >
                    採用
                  </button>
                  <button
                    type="button"
                    className="button button--ghost button--small"
                    disabled={isBusy}
                    onClick={() => {
                      void onDismissTaskCandidate(task.id);
                    }}
                  >
                    却下
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function SearchAnswerCard({
  answer,
  setQuery,
  onOpenPerson,
  onSearch,
}: {
  answer: SearchAnswer;
  setQuery: Dispatch<SetStateAction<string>>;
  onOpenPerson: (personId: string) => void;
  onSearch: (query?: string, scope?: SearchScope) => void | Promise<void>;
}) {
  const confidenceLabel =
    answer.confidence === "high"
      ? "高"
      : answer.confidence === "medium"
        ? "中"
        : answer.confidence === "low"
          ? "低"
          : "-";

  return (
    <section className="page-card search-answer-card">
      <div className="page-card__header search-answer-card__header">
        <div>
          <p className="eyebrow">Answer</p>
          <h2>検索からの整理</h2>
        </div>
        <span className={`search-answer-card__confidence search-answer-card__confidence--${answer.confidence}`}>
          確度 {confidenceLabel}
        </span>
      </div>

      <p className="search-answer-card__summary">{answer.summary}</p>

      {answer.primary_person ? (
        <div className="search-answer-card__primary">
          <div>
            <strong>{answer.primary_person.person_name}</strong>
            <span>{answer.primary_person.community_path ?? "主な所属なし"}</span>
          </div>
          <button
            type="button"
            className="button button--secondary button--small"
            onClick={() => onOpenPerson(answer.primary_person!.person_id)}
          >
            人物を見る
          </button>
        </div>
      ) : null}

      {answer.people.length > 0 ? (
        <div className="search-answer-card__people">
          {answer.people.map((person) => (
            <article key={person.person_id} className="search-answer-person">
              <div>
                <strong>{person.person_name}</strong>
                <span>{person.community_path ?? "所属情報なし"}</span>
              </div>
              <ul>
                {person.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      ) : null}

      {answer.evidence.length > 0 ? (
        <div className="search-answer-card__evidence">
          <span>根拠</span>
          {answer.evidence.slice(0, 3).map((item) => (
            <p key={item.id}>
              {item.title}: {item.snippet}
            </p>
          ))}
        </div>
      ) : null}

      {answer.follow_up_queries.length > 0 ? (
        <div className="search-answer-card__followups">
          {answer.follow_up_queries.map((queryText) => (
            <button
              key={queryText}
              type="button"
              className="button button--ghost button--small"
              onClick={() => {
                setQuery(queryText);
                void onSearch(queryText);
              }}
            >
              {queryText}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function SearchGroup({
  title,
  items,
  emptyLabel,
  compact = false,
  onOpenPerson,
  onOpenRecordForPerson,
  taskActionId,
  onAcceptTaskCandidate,
  onDismissTaskCandidate,
}: {
  title: string;
  items: SearchResultItem[];
  emptyLabel: string;
  compact?: boolean;
  onOpenPerson: (personId: string) => void;
  onOpenRecordForPerson: (personId: string) => void;
  taskActionId: string | null;
  onAcceptTaskCandidate: (taskId: string) => void | Promise<void>;
  onDismissTaskCandidate: (taskId: string) => void | Promise<void>;
}) {
  return (
    <section className="page-card search-group">
      <div className="page-card__header">
        <div>
          <p className="eyebrow">{title}</p>
          <h2>{title}</h2>
        </div>
        <span className="search-group__count">{items.length}件</span>
      </div>

      {items.length === 0 ? (
        <p className="muted">{emptyLabel}</p>
      ) : (
        <div
          className={
            compact
              ? "search-result-list search-result-list--compact"
              : "search-result-list"
          }
        >
          {items.map((item) => (
            <SearchResultCard
              key={item.id}
              item={item}
              onOpenPerson={onOpenPerson}
              onOpenRecordForPerson={onOpenRecordForPerson}
              taskActionId={taskActionId}
              onAcceptTaskCandidate={onAcceptTaskCandidate}
              onDismissTaskCandidate={onDismissTaskCandidate}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function SearchResultCard({
  item,
  onOpenPerson,
  onOpenRecordForPerson,
  taskActionId,
  onAcceptTaskCandidate,
  onDismissTaskCandidate,
}: {
  item: SearchResultItem;
  onOpenPerson: (personId: string) => void;
  onOpenRecordForPerson: (personId: string) => void;
  taskActionId: string | null;
  onAcceptTaskCandidate: (taskId: string) => void | Promise<void>;
  onDismissTaskCandidate: (taskId: string) => void | Promise<void>;
}) {
  const scoreLabel = Math.round(item.score * 100);
  const personId = item.person_id;
  const metaItems = getMetaItems(item);
  const canActOnTaskCandidate =
    item.target_type === "task" &&
    item.is_candidate &&
    item.candidate_status === "pending";
  const isTaskBusy = taskActionId === item.target_id;

  return (
    <article className="search-result-card">
      <div className="search-result-card__top">
        <div>
          <span className="search-result-card__type">
            {targetTypeLabels[item.target_type]}
          </span>
          <h3>{item.title}</h3>
        </div>
        <strong className="search-result-card__score">{scoreLabel}</strong>
      </div>

      <p className="search-result-card__snippet">{item.snippet}</p>

      <div className="search-result-card__meta">
        {metaItems.map((meta) => (
          <span key={`${meta.label}:${meta.value}`}>
            {meta.label}: {meta.value}
          </span>
        ))}
      </div>

      {personId || canActOnTaskCandidate ? (
        <div className="search-result-card__actions">
          {personId ? (
            <>
              <button
                type="button"
                className="button button--secondary button--small"
                onClick={() => onOpenPerson(personId)}
              >
                人物を見る
              </button>
              <button
                type="button"
                className="button button--ghost button--small"
                onClick={() => onOpenRecordForPerson(personId)}
              >
                この人で記録
              </button>
            </>
          ) : null}
          {canActOnTaskCandidate ? (
            <>
              <button
                type="button"
                className="button button--primary button--small"
                disabled={isTaskBusy}
                onClick={() => {
                  void onAcceptTaskCandidate(item.target_id);
                }}
              >
                候補を採用
              </button>
              <button
                type="button"
                className="button button--ghost button--small"
                disabled={isTaskBusy}
                onClick={() => {
                  void onDismissTaskCandidate(item.target_id);
                }}
              >
                却下
              </button>
            </>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

function getTaskCandidateMetaItems(task: TaskRecord) {
  const meta: Array<{ label: string; value: string }> = [];

  if (task.due_at) {
    meta.push({ label: "締め切り", value: formatDateTime(task.due_at) });
  }
  meta.push({
    label: "状態",
    value: taskStatusLabels[task.status] ?? task.status,
  });

  task.links
    .filter((link) => link.role === "related" && link.target_label)
    .slice(0, 4)
    .forEach((link) => {
      meta.push({
        label: targetTypeLabels[link.target_type] ?? link.target_type,
        value: link.target_label!,
      });
    });

  return meta;
}

function formatConfidence(value: number | null) {
  if (value === null) return "-";
  return `${Math.round(value * 100)}%`;
}

function getMetaItems(item: SearchResultItem) {
  const meta: Array<{ label: string; value: string }> = [];

  if (item.target_type === "task") {
    if (item.due_at) meta.push({ label: "締め切り", value: formatDateTime(item.due_at) });
    if (item.status_label) meta.push({ label: "状態", value: item.status_label });
    if (item.is_candidate) meta.push({ label: "扱い", value: "候補" });
    addCommonTargets(meta, item);
    if (item.source_type) {
      meta.push({
        label: "元データ",
        value: sourceTypeLabels[item.source_type] ?? item.source_type,
      });
    }
    return meta;
  }

  if (item.target_type === "calendar_event") {
    if (item.start_at) meta.push({ label: "開始", value: formatDateTime(item.start_at) });
    if (item.end_at) meta.push({ label: "終了", value: formatDateTime(item.end_at) });
    if (item.location) meta.push({ label: "場所", value: item.location });
    if (item.target_label) meta.push({ label: "参加者", value: item.target_label });
    addCommonTargets(meta, item);
    return meta;
  }

  if (item.target_type === "interaction") {
    if (item.occurred_at) meta.push({ label: "記録日", value: formatDateTime(item.occurred_at) });
    addCommonTargets(meta, item);
    return meta;
  }

  if (item.target_type === "person") {
    if (item.community_path) meta.push({ label: "所属", value: item.community_path });
    if (item.occurred_at) meta.push({ label: "最近の記録", value: formatDateTime(item.occurred_at) });
    return meta;
  }

  addCommonTargets(meta, item);
  if (item.occurred_at) meta.push({ label: "関連日", value: formatDateTime(item.occurred_at) });
  return meta;
}

function addCommonTargets(
  meta: Array<{ label: string; value: string }>,
  item: SearchResultItem
) {
  if (item.person_name) meta.push({ label: "人物", value: item.person_name });
  if (item.community_path) meta.push({ label: "団体", value: item.community_path });
  if (item.topic_path) meta.push({ label: "話題", value: item.topic_path });
}
