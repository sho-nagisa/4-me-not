import type { Dispatch, FormEvent, SetStateAction } from "react";

import { EmptyState } from "./components";
import type { SearchResponse, SearchResultItem, SearchTargetType } from "./types";
import { formatDateTime } from "./utils";

export type SearchScope = "all" | SearchTargetType;

type SearchPageProps = {
  query: string;
  setQuery: Dispatch<SetStateAction<string>>;
  scope: SearchScope;
  setScope: Dispatch<SetStateAction<SearchScope>>;
  loading: boolean;
  result: SearchResponse | null;
  error: string | null;
  onSearch: (query?: string, scope?: SearchScope) => void | Promise<void>;
  onOpenPerson: (personId: string) => void;
  onOpenRecordForPerson: (personId: string) => void;
};

const scopeOptions: Array<{ id: SearchScope; label: string }> = [
  { id: "all", label: "すべて" },
  { id: "person", label: "人物" },
  { id: "interaction", label: "会話" },
  { id: "community", label: "所属" },
  { id: "topic", label: "話題" },
];

const exampleQueries = [
  "面接 志望動機",
  "アルバイト シフト 店長",
  "恋愛 返信頻度",
  "誰だっけ テニス 就活",
];

const targetTypeLabels: Record<SearchTargetType, string> = {
  person: "人物",
  interaction: "会話",
  community: "所属",
  topic: "話題",
};

export function SearchPage({
  query,
  setQuery,
  scope,
  setScope,
  loading,
  result,
  error,
  onSearch,
  onOpenPerson,
  onOpenRecordForPerson,
}: SearchPageProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void onSearch();
  };

  const peopleResults = result?.groups.people ?? [];
  const interactionResults = result?.groups.interactions ?? [];
  const communityResults = result?.groups.communities ?? [];
  const topicResults = result?.groups.topics ?? [];
  const hasResults = Boolean(result && result.results.length > 0);

  return (
    <section className="page-stack search-page">
      <section className="page-card search-panel">
        <div className="page-card__header search-panel__header">
          <div>
            <p className="eyebrow">Search</p>
            <h2>思い出す検索</h2>
          </div>
        </div>

        <form className="search-form" onSubmit={handleSubmit}>
          <label className="field search-form__field">
            <span className="field__label">覚えていること</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="例: 面接の志望動機を相談した人"
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

      {!result ? (
        <section className="page-card">
          <EmptyState
            title="まだ検索していません"
            description="人名が曖昧でも、話した内容・所属・話題をそのまま入力できます。"
          />
        </section>
      ) : !hasResults ? (
        <section className="page-card">
          <EmptyState
            title="候補が見つかりませんでした"
            description="単語を短くするか、所属や話題を入れて検索してみてください。"
          />
        </section>
      ) : (
        <section className="search-results-grid">
          <SearchGroup
            title="人物候補"
            items={peopleResults}
            emptyLabel="人物候補はまだありません。"
            onOpenPerson={onOpenPerson}
            onOpenRecordForPerson={onOpenRecordForPerson}
          />
          <SearchGroup
            title="関連する会話"
            items={interactionResults}
            emptyLabel="関連する会話はまだありません。"
            onOpenPerson={onOpenPerson}
            onOpenRecordForPerson={onOpenRecordForPerson}
          />
          <SearchGroup
            title="所属・話題"
            items={[...communityResults, ...topicResults]}
            emptyLabel="関連する所属・話題はまだありません。"
            compact
            onOpenPerson={onOpenPerson}
            onOpenRecordForPerson={onOpenRecordForPerson}
          />
        </section>
      )}
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
}: {
  title: string;
  items: SearchResultItem[];
  emptyLabel: string;
  compact?: boolean;
  onOpenPerson: (personId: string) => void;
  onOpenRecordForPerson: (personId: string) => void;
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
}: {
  item: SearchResultItem;
  onOpenPerson: (personId: string) => void;
  onOpenRecordForPerson: (personId: string) => void;
}) {
  const scoreLabel = Math.round(item.score * 100);
  const personId = item.person_id;

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
        {item.person_name ? <span>人物: {item.person_name}</span> : null}
        {item.community_path ? <span>所属: {item.community_path}</span> : null}
        {item.topic_path ? <span>話題: {item.topic_path}</span> : null}
        {item.occurred_at ? <span>{formatDateTime(item.occurred_at)}</span> : null}
      </div>

      {personId ? (
        <div className="search-result-card__actions">
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
        </div>
      ) : null}
    </article>
  );
}
