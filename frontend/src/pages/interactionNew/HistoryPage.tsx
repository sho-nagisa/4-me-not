import type { Dispatch, SetStateAction } from "react";

import { EmptyState, HistoryCard } from "./components";
import { shareLevelOptions } from "./constants";
import type { Community, InteractionRecord, Person, ShareLevel, Topic } from "./types";

type HistoryPageProps = {
  persons: Person[];
  communities: Community[];
  topics: Topic[];
  historyPersonId: string;
  setHistoryPersonId: Dispatch<SetStateAction<string>>;
  historyCommunityId: string;
  setHistoryCommunityId: Dispatch<SetStateAction<string>>;
  historyTopicId: string;
  setHistoryTopicId: Dispatch<SetStateAction<string>>;
  historyShareLevel: ShareLevel | "";
  setHistoryShareLevel: Dispatch<SetStateAction<ShareLevel | "">>;
  historySearch: string;
  setHistorySearch: Dispatch<SetStateAction<string>>;
  historyDateFrom: string;
  setHistoryDateFrom: Dispatch<SetStateAction<string>>;
  historyDateTo: string;
  setHistoryDateTo: Dispatch<SetStateAction<string>>;
  historyLoading: boolean;
  onLoadHistory: (page?: number) => void | Promise<void>;
  historyPage: number;
  historyTotalCount: number;
  historyPageSize: number;
  onHistoryPageChange: (page: number) => void;
  onClearHistoryFilters: () => void;
  historyFilterOpen: boolean;
  setHistoryFilterOpen: Dispatch<SetStateAction<boolean>>;
  selectedHistoryLevelLabel: string;
  historyItems: InteractionRecord[];
};

export function HistoryPage(props: HistoryPageProps) {
  const {
    persons,
    communities,
    topics,
    historyPersonId,
    setHistoryPersonId,
    historyCommunityId,
    setHistoryCommunityId,
    historyTopicId,
    setHistoryTopicId,
    historyShareLevel,
    setHistoryShareLevel,
    historySearch,
    setHistorySearch,
    historyDateFrom,
    setHistoryDateFrom,
    historyDateTo,
    setHistoryDateTo,
    historyLoading,
    onLoadHistory: loadHistory,
    historyPage,
    historyTotalCount,
    historyPageSize,
    onHistoryPageChange,
    onClearHistoryFilters: clearHistoryFilters,
    historyFilterOpen,
    setHistoryFilterOpen,
    selectedHistoryLevelLabel,
    historyItems,
  } = props;

  const selectedHistoryPersonName =
    persons.find((person) => person.id === historyPersonId)?.name ?? "すべて";
  const selectedHistoryCommunityPath =
    communities.find((community) => community.id === historyCommunityId)?.path ?? "すべて";
  const selectedHistoryTopicPath =
    topics.find((topic) => topic.id === historyTopicId)?.path ?? "すべて";
  const trimmedHistorySearch = historySearch.trim();
  const historyFilterSummary = [
    historyPersonId ? `人: ${selectedHistoryPersonName}` : null,
    historyCommunityId ? `コミュニティ: ${selectedHistoryCommunityPath}` : null,
    historyTopicId ? `話題: ${selectedHistoryTopicPath}` : null,
    historyShareLevel ? `共有レベル: ${selectedHistoryLevelLabel}` : null,
    trimmedHistorySearch ? `キーワード: ${trimmedHistorySearch}` : null,
    historyDateFrom ? `開始日: ${historyDateFrom}` : null,
    historyDateTo ? `終了日: ${historyDateTo}` : null,
  ].filter((item): item is string => Boolean(item));
  const historyTotalPages = Math.max(
    1,
    Math.ceil(historyTotalCount / historyPageSize)
  );
  const historyStartIndex =
    historyTotalCount === 0 ? 0 : (historyPage - 1) * historyPageSize + 1;
  const historyEndIndex =
    historyTotalCount === 0
      ? 0
      : Math.min(historyTotalCount, historyStartIndex + historyItems.length - 1);
  const canMoveToPreviousHistoryPage = historyPage > 1 && !historyLoading;
  const canMoveToNextHistoryPage =
    historyPage < historyTotalPages && !historyLoading;

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
    <section
      className={`page-grid page-grid--history${
        historyFilterOpen ? " page-grid--history-filter-open" : ""
      }`}
    >
      {historyFilterOpen ? (
        <aside className="page-card history-filter-card">
          <div className="page-card__header">
            <div>
              <p className="eyebrow">Filter</p>
              <h2>履歴の絞り込み</h2>
            </div>
            <button
              type="button"
              className="button button--ghost filter-panel__toggle"
              onClick={() => setHistoryFilterOpen(false)}
              aria-expanded={historyFilterOpen}
              aria-controls="history-filter-body"
            >
              閉じる
            </button>
          </div>
          <div className="filter-panel__body" id="history-filter-body">
            {renderHistoryFilters()}
          </div>
        </aside>
      ) : null}

      <div className="history-main">
        <div className="history-summary history-summary--outside">
          <span>
            表示 {historyStartIndex}-{historyEndIndex}件 / 全{historyTotalCount}件
          </span>
          <span>
            {historyPage} / {historyTotalPages}ページ
          </span>
          <span>
            伏せた {historyItems.filter((item) => item.share_level === "WITHHELD").length}件
          </span>
        </div>

        <section className="page-card">
          <div className="page-card__header history-list-card__header">
            <div className="history-list-card__title">
              <p className="eyebrow">History</p>
              <h2>履歴一覧</h2>
            </div>
            <button
              type="button"
              className={`button button--ghost filter-panel__toggle filter-panel__icon-toggle${
                historyFilterOpen ? " filter-panel__icon-toggle--active" : ""
              }`}
              onClick={() => setHistoryFilterOpen((current) => !current)}
              aria-expanded={historyFilterOpen}
              aria-controls="history-filter-body"
              aria-label={historyFilterOpen ? "絞り込みを閉じる" : "絞り込みを開く"}
              title={historyFilterOpen ? "絞り込みを閉じる" : "絞り込みを開く"}
            >
              <span className="filter-panel__icon" aria-hidden="true" />
            </button>
          </div>
          {!historyFilterOpen && historyFilterSummary.length > 0 ? (
            <div className="filter-panel__summary filter-panel__summary--inline">
              {historyFilterSummary.map((item) => <span key={item}>{item}</span>)}
            </div>
          ) : null}

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
          {historyTotalCount > historyPageSize ? (
            <div className="history-pagination" aria-label="履歴ページ切り替え">
              <button
                type="button"
                className="button button--ghost"
                onClick={() => onHistoryPageChange(historyPage - 1)}
                disabled={!canMoveToPreviousHistoryPage}
              >
                前へ
              </button>
              <span>
                {historyPage} / {historyTotalPages}
              </span>
              <button
                type="button"
                className="button button--ghost"
                onClick={() => onHistoryPageChange(historyPage + 1)}
                disabled={!canMoveToNextHistoryPage}
              >
                次へ
              </button>
            </div>
          ) : null}
        </section>
      </div>
    </section>
  );



  return renderHistoryPage();
}
