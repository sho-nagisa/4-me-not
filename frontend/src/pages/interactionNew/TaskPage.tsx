import type { Dispatch, FormEvent, SetStateAction } from "react";

import { EmptyState, MetricCard, SectionTabs } from "./components";
import type { SearchResponse, SearchResultItem, TaskRecord } from "./types";
import { formatDateTime } from "./utils";
import { TaskCandidatePanel } from "./SearchPage";

export type TaskPanelId = "overview" | "search";

type TaskPageProps = {
  panel: TaskPanelId;
  setPanel: Dispatch<SetStateAction<TaskPanelId>>;
  tasks: TaskRecord[];
  tasksLoading: boolean;
  taskCandidates: TaskRecord[];
  taskCandidatesLoading: boolean;
  taskActionId: string | null;
  onAcceptTaskCandidate: (taskId: string) => void | Promise<void>;
  onDismissTaskCandidate: (taskId: string) => void | Promise<void>;
  searchQuery: string;
  setSearchQuery: Dispatch<SetStateAction<string>>;
  searchLoading: boolean;
  searchResult: SearchResponse | null;
  searchError: string | null;
  onSearch: (query?: string) => void | Promise<void>;
};

const taskPanelOptions: Array<{ id: TaskPanelId; label: string }> = [
  { id: "overview", label: "タスク" },
  { id: "search", label: "タスク検索" },
];

const taskStatusLabels: Record<string, string> = {
  TODO: "未完了",
  DONE: "完了",
  SKIPPED: "見送り",
};

const sourceTypeLabels: Record<string, string> = {
  interaction: "会話",
  calendar_event: "予定",
  manual_note: "手入力",
  manual: "手入力",
};

export function TaskPage({
  panel,
  setPanel,
  tasks,
  tasksLoading,
  taskCandidates,
  taskCandidatesLoading,
  taskActionId,
  onAcceptTaskCandidate,
  onDismissTaskCandidate,
  searchQuery,
  setSearchQuery,
  searchLoading,
  searchResult,
  searchError,
  onSearch,
}: TaskPageProps) {
  const activeTasks = tasks.filter((task) => task.status === "TODO");
  const completedTasks = tasks.filter((task) => task.status === "DONE");
  const dueSoonTasks = activeTasks.filter(isDueSoon);

  return (
    <section className="page-stack task-page">
      <section className="page-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Tasks</p>
            <h2>タスク管理</h2>
          </div>
        </div>
        <SectionTabs items={taskPanelOptions} activeId={panel} onSelect={setPanel} />

        <div className="metric-grid metric-grid--compact task-metric-grid">
          <MetricCard
            label="候補"
            value={taskCandidates.length}
            description="会話から抽出された未確認の候補"
          />
          <MetricCard
            label="未完了"
            value={activeTasks.length}
            description="採用済みで未完了のタスク"
          />
          <MetricCard
            label="期限間近"
            value={dueSoonTasks.length}
            description="7日以内に締め切りが来るタスク"
          />
          <MetricCard
            label="完了"
            value={completedTasks.length}
            description="完了済みのタスク"
          />
        </div>
      </section>

      {panel === "overview" ? (
        <section className="page-grid page-grid--two">
          <TaskCandidatePanel
            candidates={taskCandidates}
            loading={taskCandidatesLoading}
            taskActionId={taskActionId}
            onAcceptTaskCandidate={onAcceptTaskCandidate}
            onDismissTaskCandidate={onDismissTaskCandidate}
          />
          <TaskList tasks={tasks} loading={tasksLoading} />
        </section>
      ) : (
        <TaskSearchPanel
          query={searchQuery}
          setQuery={setSearchQuery}
          loading={searchLoading}
          result={searchResult}
          error={searchError}
          taskActionId={taskActionId}
          onSearch={onSearch}
          onAcceptTaskCandidate={onAcceptTaskCandidate}
          onDismissTaskCandidate={onDismissTaskCandidate}
        />
      )}
    </section>
  );
}

function TaskList({
  tasks,
  loading,
}: {
  tasks: TaskRecord[];
  loading: boolean;
}) {
  const activeTasks = tasks.filter((task) => task.status !== "DONE");

  return (
    <section className="page-card task-list-panel">
      <div className="page-card__header">
        <div>
          <p className="eyebrow">Accepted Tasks</p>
          <h2>採用済みタスク</h2>
        </div>
        <span className="task-candidate-badge">
          {loading ? "読込中" : `${activeTasks.length}件`}
        </span>
      </div>

      {loading ? (
        <p className="muted">タスクを読み込んでいます。</p>
      ) : activeTasks.length === 0 ? (
        <EmptyState
          title="採用済みタスクはまだありません"
          description="タスク候補を採用すると、ここに表示されます。"
        />
      ) : (
        <div className="task-list">
          {activeTasks.map((task) => (
            <article key={task.id} className="task-list-card">
              <div className="task-list-card__top">
                <div>
                  <span>{sourceTypeLabels[task.source_type] ?? task.source_type}</span>
                  <h3>{task.title}</h3>
                </div>
                <strong>{taskStatusLabels[task.status] ?? task.status}</strong>
              </div>
              {task.description ? <p>{task.description}</p> : null}
              <TaskMeta task={task} />
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function TaskSearchPanel({
  query,
  setQuery,
  loading,
  result,
  error,
  taskActionId,
  onSearch,
  onAcceptTaskCandidate,
  onDismissTaskCandidate,
}: {
  query: string;
  setQuery: Dispatch<SetStateAction<string>>;
  loading: boolean;
  result: SearchResponse | null;
  error: string | null;
  taskActionId: string | null;
  onSearch: (query?: string) => void | Promise<void>;
  onAcceptTaskCandidate: (taskId: string) => void | Promise<void>;
  onDismissTaskCandidate: (taskId: string) => void | Promise<void>;
}) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void onSearch();
  };
  const items = [
    ...(result?.groups.tasks ?? []),
    ...(result?.groups.calendar_events ?? []),
  ];

  return (
    <section className="page-card task-search-panel">
      <div className="page-card__header">
        <div>
          <p className="eyebrow">Task Search</p>
          <h2>タスク検索</h2>
        </div>
      </div>

      <form className="search-form" onSubmit={handleSubmit}>
        <label className="field search-form__field">
          <span className="field__label">探したいタスクや予定</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="例: 来週までの提出物"
          />
        </label>
        <div className="button-row">
          <button
            type="submit"
            className="button button--primary"
            disabled={loading || !query.trim()}
          >
            {loading ? "検索中..." : "検索する"}
          </button>
        </div>
      </form>

      {error ? <p className="search-error">{error}</p> : null}

      {!result ? (
        <EmptyState
          title="まだ検索していません"
          description="タスク名、締め切り、人物名、予定の内容で探せます。"
        />
      ) : items.length === 0 ? (
        <EmptyState
          title="候補が見つかりませんでした"
          description="単語を短くするか、締め切りや人物名を入れて検索してみてください。"
        />
      ) : (
        <div className="task-search-results">
          {items.map((item) => (
            <TaskSearchResultCard
              key={item.id}
              item={item}
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

function TaskSearchResultCard({
  item,
  taskActionId,
  onAcceptTaskCandidate,
  onDismissTaskCandidate,
}: {
  item: SearchResultItem;
  taskActionId: string | null;
  onAcceptTaskCandidate: (taskId: string) => void | Promise<void>;
  onDismissTaskCandidate: (taskId: string) => void | Promise<void>;
}) {
  const canActOnTaskCandidate =
    item.target_type === "task" &&
    item.is_candidate &&
    item.candidate_status === "pending";
  const isBusy = taskActionId === item.target_id;

  return (
    <article className="search-result-card">
      <div className="search-result-card__top">
        <div>
          <span className="search-result-card__type">
            {item.target_type === "calendar_event" ? "予定" : "タスク"}
          </span>
          <h3>{item.title}</h3>
        </div>
        <strong className="search-result-card__score">
          {Math.round(item.score * 100)}
        </strong>
      </div>
      <p className="search-result-card__snippet">{item.snippet}</p>
      <div className="search-result-card__meta">
        {item.due_at ? <span>締め切り: {formatDateTime(item.due_at)}</span> : null}
        {item.start_at ? <span>開始: {formatDateTime(item.start_at)}</span> : null}
        {item.person_name ? <span>人物: {item.person_name}</span> : null}
        {item.community_path ? <span>団体: {item.community_path}</span> : null}
        {item.location ? <span>場所: {item.location}</span> : null}
      </div>
      {canActOnTaskCandidate ? (
        <div className="search-result-card__actions">
          <button
            type="button"
            className="button button--primary button--small"
            disabled={isBusy}
            onClick={() => {
              void onAcceptTaskCandidate(item.target_id);
            }}
          >
            候補を採用
          </button>
          <button
            type="button"
            className="button button--ghost button--small"
            disabled={isBusy}
            onClick={() => {
              void onDismissTaskCandidate(item.target_id);
            }}
          >
            却下
          </button>
        </div>
      ) : null}
    </article>
  );
}

function TaskMeta({ task }: { task: TaskRecord }) {
  const relatedLinks = task.links.filter(
    (link) => link.role === "related" && link.target_label
  );

  return (
    <div className="task-list-card__meta">
      {task.due_at ? <span>締め切り: {formatDateTime(task.due_at)}</span> : null}
      {relatedLinks.slice(0, 3).map((link) => (
        <span key={`${task.id}:${link.target_type}:${link.target_id}`}>
          {link.target_label}
        </span>
      ))}
    </div>
  );
}

function isDueSoon(task: TaskRecord) {
  if (!task.due_at) return false;
  const dueAt = new Date(task.due_at).getTime();
  const now = Date.now();
  const sevenDays = 7 * 24 * 60 * 60 * 1000;
  return dueAt >= now && dueAt <= now + sevenDays;
}
