import { useState } from "react";
import type { PointerEvent } from "react";

import type { HomeViewProps, InteractionRecord, PersonBubble, TopicTreeNode } from "./types";
import { formatDateTime } from "./utils";

export function NavItem({
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

export function SectionTabs<T extends string>({
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

export function MetricCard({
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

export function EmptyState({
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

export function SummaryRows({
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

export function TopicTree({
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

export function PersonBubbleCloud({
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

export function HistoryCard({ item }: { item: InteractionRecord }) {
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

export function DesktopHome({
  personBubbles,
  selectedPersonId,
  recentInteractions,
  onBubbleSelect,
  onOpenHistory,
  onOpenRecord,
}: HomeViewProps) {
  return (
    <section className="page-stack home-page home-page--desktop">
      <section className="page-card home-bubble-card">
        <div className="page-card__header">
          <div>
            <p className="eyebrow">Home</p>
            <h2>ホーム</h2>
          </div>
          <button
            type="button"
            className="home-record-button"
            onClick={onOpenRecord}
            aria-label="Open record"
            title="Record"
          >
            +
          </button>
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

export function MobileHome({
  personBubbles,
  selectedPersonId,
  recentInteractions,
  onBubbleSelect,
  onOpenHistory,
  onOpenRecord,
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
          <button
            type="button"
            className="home-record-button"
            onClick={onOpenRecord}
            aria-label="Open record"
            title="Record"
          >
            +
          </button>
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
