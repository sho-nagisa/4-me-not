import { useMemo, useState, type Dispatch, type FormEvent, type SetStateAction } from "react";

import { EmptyState, MetricCard, SectionTabs } from "./components";
import type { CreateTaskPayload, UpdateTaskPayload } from "./interactionsApi";
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
  onCreateTask: (payload: CreateTaskPayload) => void | Promise<void>;
  onUpdateTask: (taskId: string, payload: UpdateTaskPayload) => void | Promise<void>;
  onCompleteTask: (taskId: string) => void | Promise<void>;
  onReopenTask: (taskId: string) => void | Promise<void>;
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
  onCreateTask,
  onUpdateTask,
  onCompleteTask,
  onReopenTask,
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

        <div className="metric-grid metric-grid--compact task-metric-grid task-overview-metrics">
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
        <section className="page-grid page-grid--two task-overview-grid">
          <div className="task-overview-column">
            <TaskCreatePanel
              busy={taskActionId === "new-task"}
              onCreateTask={onCreateTask}
            />
            <TaskCandidatePanel
              candidates={taskCandidates}
              loading={taskCandidatesLoading}
              taskActionId={taskActionId}
              onAcceptTaskCandidate={onAcceptTaskCandidate}
              onDismissTaskCandidate={onDismissTaskCandidate}
            />
          </div>
          <TaskList
            tasks={tasks}
            loading={tasksLoading}
            taskActionId={taskActionId}
            onUpdateTask={onUpdateTask}
            onCompleteTask={onCompleteTask}
            onReopenTask={onReopenTask}
          />
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

function TaskCreatePanel({
  busy,
  onCreateTask,
}: {
  busy: boolean;
  onCreateTask: (payload: CreateTaskPayload) => void | Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedTitle = title.trim();
    if (!trimmedTitle) return;

    await onCreateTask({
      title: trimmedTitle,
      description: description.trim() || null,
      due_at: toDueAtIso(dueDate),
      priority: priority ? Number(priority) : null,
    });
    setTitle("");
    setDescription("");
    setDueDate("");
    setPriority("");
  };

  return (
    <section className="page-card task-create-panel">
      <div className="page-card__header">
        <div>
          <p className="eyebrow">New Task</p>
          <h2>タスクを追加</h2>
        </div>
      </div>

      <form className="task-edit-form" onSubmit={handleSubmit}>
        <label className="field">
          <span className="field__label">タイトル</span>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="例: 企画書を送る"
            maxLength={200}
          />
        </label>
        <label className="field">
          <span className="field__label">メモ</span>
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="必要な補足を入力"
          />
        </label>
        <div className="task-edit-form__row">
          <label className="field">
            <span className="field__label">締め切り</span>
            <input
              type="date"
              value={dueDate}
              onChange={(event) => setDueDate(event.target.value)}
            />
          </label>
          <label className="field">
            <span className="field__label">優先度</span>
            <select
              value={priority}
              onChange={(event) => setPriority(event.target.value)}
            >
              <option value="">未設定</option>
              <option value="1">1 低</option>
              <option value="2">2</option>
              <option value="3">3 標準</option>
              <option value="4">4</option>
              <option value="5">5 高</option>
            </select>
          </label>
        </div>
        <button
          type="submit"
          className="button button--primary"
          disabled={busy || !title.trim()}
        >
          {busy ? "追加中..." : "追加"}
        </button>
      </form>
    </section>
  );
}

function TaskList({
  tasks,
  loading,
  taskActionId,
  onUpdateTask,
  onCompleteTask,
  onReopenTask,
}: {
  tasks: TaskRecord[];
  loading: boolean;
  taskActionId: string | null;
  onUpdateTask: (taskId: string, payload: UpdateTaskPayload) => void | Promise<void>;
  onCompleteTask: (taskId: string) => void | Promise<void>;
  onReopenTask: (taskId: string) => void | Promise<void>;
}) {
  const [filterText, setFilterText] = useState("");
  const [statusFilter, setStatusFilter] = useState<"open" | "done" | "all">("open");
  const visibleTasks = useMemo(
    () =>
      tasks.filter((task) => {
        if (statusFilter === "open" && task.status !== "TODO") return false;
        if (statusFilter === "done" && task.status !== "DONE") return false;
        if (!matchesTaskFilter(task, filterText)) return false;
        return true;
      }),
    [filterText, statusFilter, tasks]
  );

  return (
    <section className="page-card task-list-panel">
      <div className="page-card__header">
        <div>
          <p className="eyebrow">Open Tasks</p>
          <h2>未完了タスク</h2>
        </div>
        <span className="task-candidate-badge">
          {loading ? "読込中" : `${visibleTasks.length}件`}
        </span>
      </div>
      <div className="task-list-toolbar">
        <label className="field field--toolbar">
          <span className="field__label">タスク検索</span>
          <input
            value={filterText}
            onChange={(event) => setFilterText(event.target.value)}
            placeholder="タイトル、メモ、関連人物で絞り込み"
          />
        </label>
        <div className="task-status-filter" aria-label="タスク状態">
          <button
            type="button"
            className={`search-scope__item ${
              statusFilter === "open" ? "search-scope__item--active" : ""
            }`}
            onClick={() => setStatusFilter("open")}
          >
            未完了
          </button>
          <button
            type="button"
            className={`search-scope__item ${
              statusFilter === "done" ? "search-scope__item--active" : ""
            }`}
            onClick={() => setStatusFilter("done")}
          >
            完了
          </button>
          <button
            type="button"
            className={`search-scope__item ${
              statusFilter === "all" ? "search-scope__item--active" : ""
            }`}
            onClick={() => setStatusFilter("all")}
          >
            すべて
          </button>
        </div>
      </div>

      {loading ? (
        <p className="muted">タスクを読み込んでいます。</p>
      ) : visibleTasks.length === 0 ? (
        <EmptyState
          title="表示できるタスクがありません"
          description="タスクを追加するか、検索条件を変えてください。"
        />
      ) : (
        <div className="task-list">
          {visibleTasks.map((task) => (
            <EditableTaskCard
              key={task.id}
              task={task}
              busy={taskActionId === task.id}
              onUpdateTask={onUpdateTask}
              onCompleteTask={onCompleteTask}
              onReopenTask={onReopenTask}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function EditableTaskCard({
  task,
  busy,
  onUpdateTask,
  onCompleteTask,
  onReopenTask,
}: {
  task: TaskRecord;
  busy: boolean;
  onUpdateTask: (taskId: string, payload: UpdateTaskPayload) => void | Promise<void>;
  onCompleteTask: (taskId: string) => void | Promise<void>;
  onReopenTask: (taskId: string) => void | Promise<void>;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description ?? "");
  const [dueDate, setDueDate] = useState(toDateInputValue(task.due_at));
  const [priority, setPriority] = useState(task.priority ? String(task.priority) : "");
  const [status, setStatus] = useState<"TODO" | "DONE" | "SKIPPED">(
    normalizeTaskStatus(task.status)
  );

  const resetForm = () => {
    setTitle(task.title);
    setDescription(task.description ?? "");
    setDueDate(toDateInputValue(task.due_at));
    setPriority(task.priority ? String(task.priority) : "");
    setStatus(normalizeTaskStatus(task.status));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedTitle = title.trim();
    if (!trimmedTitle) return;

    await onUpdateTask(task.id, {
      title: trimmedTitle,
      description: description.trim() || null,
      due_at: toDueAtIso(dueDate),
      priority: priority ? Number(priority) : null,
      status,
    });
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <article className="task-list-card">
        <form className="task-edit-form" onSubmit={handleSubmit}>
          <label className="field">
            <span className="field__label">タイトル</span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              maxLength={200}
            />
          </label>
          <label className="field">
            <span className="field__label">メモ</span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
          <div className="task-edit-form__row">
            <label className="field">
              <span className="field__label">締め切り</span>
              <input
                type="date"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
              />
            </label>
            <label className="field">
              <span className="field__label">優先度</span>
              <select
                value={priority}
                onChange={(event) => setPriority(event.target.value)}
              >
                <option value="">未設定</option>
                <option value="1">1 低</option>
                <option value="2">2</option>
                <option value="3">3 標準</option>
                <option value="4">4</option>
                <option value="5">5 高</option>
              </select>
            </label>
            <label className="field">
              <span className="field__label">状態</span>
              <select
                value={status}
                onChange={(event) =>
                  setStatus(event.target.value as "TODO" | "DONE" | "SKIPPED")
                }
              >
                <option value="TODO">未完了</option>
                <option value="DONE">完了</option>
                <option value="SKIPPED">見送り</option>
              </select>
            </label>
          </div>
          <div className="task-card-actions">
            <button
              type="submit"
              className="button button--primary button--small"
              disabled={busy || !title.trim()}
            >
              {busy ? "保存中..." : "保存"}
            </button>
            <button
              type="button"
              className="button button--ghost button--small"
              disabled={busy}
              onClick={() => {
                resetForm();
                setIsEditing(false);
              }}
            >
              キャンセル
            </button>
          </div>
        </form>
      </article>
    );
  }

  return (
    <article className="task-list-card">
      <div className="task-list-card__top">
        <div>
          <span>{sourceTypeLabels[task.source_type] ?? task.source_type}</span>
          <h3>{task.title}</h3>
        </div>
        <strong>{taskStatusLabels[task.status] ?? task.status}</strong>
      </div>
      {task.description ? <p>{task.description}</p> : null}
      <TaskMeta task={task} />
      <div className="task-card-actions">
        {task.status === "TODO" ? (
          <button
            type="button"
            className="button button--primary button--small"
            disabled={busy}
            onClick={() => {
              void onCompleteTask(task.id);
            }}
          >
            完了
          </button>
        ) : (
          <button
            type="button"
            className="button button--secondary button--small"
            disabled={busy}
            onClick={() => {
              void onReopenTask(task.id);
            }}
          >
            未完了へ戻す
          </button>
        )}
        <button
          type="button"
          className="button button--ghost button--small"
          disabled={busy}
          onClick={() => {
            resetForm();
            setIsEditing(true);
          }}
        >
          編集
        </button>
      </div>
    </article>
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
      {task.priority ? <span>優先度: {task.priority}</span> : null}
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

function toDueAtIso(value: string) {
  return value ? `${value}T23:59:00+00:00` : null;
}

function toDateInputValue(value: string | null) {
  return value ? value.slice(0, 10) : "";
}

function normalizeTaskStatus(value: string): "TODO" | "DONE" | "SKIPPED" {
  if (value === "DONE" || value === "SKIPPED") return value;
  return "TODO";
}

function matchesTaskFilter(task: TaskRecord, filterText: string) {
  const query = filterText.trim().toLocaleLowerCase();
  if (!query) return true;

  const haystack = [
    task.title,
    task.description ?? "",
    task.due_at ?? "",
    task.priority ? String(task.priority) : "",
    ...task.links.map((link) => link.target_label ?? ""),
  ]
    .join("\n")
    .toLocaleLowerCase();

  return haystack.includes(query);
}
