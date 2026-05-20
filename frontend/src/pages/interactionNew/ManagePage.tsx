import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, Dispatch, PointerEvent, SetStateAction } from "react";

import { EmptyState, SectionTabs, TopicTree } from "./components";
import { managePanelOptions } from "./constants";
import type { Community, CommunityTreeNode, ManagePanelId, Person, Topic } from "./types";
import { buildCommunityTree, buildTopicTree } from "./utils";

type ManagePageProps = {
  managePanel: ManagePanelId;
  setManagePanel: Dispatch<SetStateAction<ManagePanelId>>;
  managedPersons: Person[];
  managedCommunities: Community[];
  communities: Community[];
  topics: Topic[];
  newPersonName: string;
  setNewPersonName: Dispatch<SetStateAction<string>>;
  newPersonPrimaryCommunityId: string;
  setNewPersonPrimaryCommunityId: Dispatch<SetStateAction<string>>;
  newCommunityName: string;
  setNewCommunityName: Dispatch<SetStateAction<string>>;
  newCommunityParentId: string;
  setNewCommunityParentId: Dispatch<SetStateAction<string>>;
  newTopicName: string;
  setNewTopicName: Dispatch<SetStateAction<string>>;
  newTopicParentId: string;
  setNewTopicParentId: Dispatch<SetStateAction<string>>;
  isCreatingPerson: boolean;
  isCreatingCommunity: boolean;
  isCreatingTopic: boolean;
  onCreatePerson: () => void | Promise<void>;
  onCreateCommunity: () => void | Promise<void>;
  onCreateTopic: () => void | Promise<void>;
  personActionId: string | null;
  communityActionId: string | null;
  onTogglePersonHidden: (person: Person) => void | Promise<void>;
  onDeletePerson: (person: Person) => void | Promise<void>;
  onToggleCommunityHidden: (community: Community) => void | Promise<void>;
  onDeleteCommunity: (community: Community) => void | Promise<void>;
};

const findCommunityNode = (
  nodes: CommunityTreeNode[],
  targetId: string | null
): CommunityTreeNode | null => {
  if (!targetId) return null;

  for (const node of nodes) {
    if (node.id === targetId) return node;
    const child = findCommunityNode(node.children, targetId);
    if (child) return child;
  }

  return null;
};

const findCommunityPath = (
  nodes: CommunityTreeNode[],
  targetId: string | null
): CommunityTreeNode[] => {
  if (!targetId) return [];

  for (const node of nodes) {
    if (node.id === targetId) return [node];
    const childPath = findCommunityPath(node.children, targetId);
    if (childPath.length > 0) return [node, ...childPath];
  }

  return [];
};

const getCarouselOffset = (index: number, selectedIndex: number, total: number) => {
  let offset = index - selectedIndex;
  if (total > 2 && offset > total / 2) offset -= total;
  if (total > 2 && offset < -total / 2) offset += total;
  return offset;
};

const clampCarouselOffset = (offset: number) =>
  Math.max(-2, Math.min(2, offset));

const getCommunityBubblePosition = (
  offset: number,
  hasParent: boolean
): CSSProperties => {
  const positions: Record<number, { left: number; top: number; size: number; scale: number }> =
    hasParent
      ? {
          "-2": { left: 35, top: 28, size: 96, scale: 0.82 },
          "-1": { left: 24, top: 48, size: 122, scale: 0.92 },
          0: { left: 50, top: 75, size: 154, scale: 1 },
          1: { left: 76, top: 48, size: 122, scale: 0.92 },
          2: { left: 65, top: 28, size: 96, scale: 0.82 },
        }
      : {
          "-2": { left: 36, top: 25, size: 96, scale: 0.82 },
          "-1": { left: 24, top: 50, size: 122, scale: 0.92 },
          0: { left: 50, top: 57, size: 166, scale: 1 },
          1: { left: 76, top: 50, size: 122, scale: 0.92 },
          2: { left: 64, top: 25, size: 96, scale: 0.82 },
        };
  const position = positions[offset] ?? positions[0];

  return {
    left: `${position.left}%`,
    top: `${position.top}%`,
    width: `${position.size}px`,
    height: `${position.size}px`,
    transform: `translate(-50%, -50%) scale(${position.scale})`,
  };
};

export function ManagePage(props: ManagePageProps) {
  const {
    managePanel,
    setManagePanel,
    managedPersons,
    managedCommunities,
    communities,
    topics,
    newPersonName,
    setNewPersonName,
    newPersonPrimaryCommunityId,
    setNewPersonPrimaryCommunityId,
    newCommunityName,
    setNewCommunityName,
    newCommunityParentId,
    setNewCommunityParentId,
    newTopicName,
    setNewTopicName,
    newTopicParentId,
    setNewTopicParentId,
    isCreatingPerson,
    isCreatingCommunity,
    isCreatingTopic,
    onCreatePerson: handleCreatePerson,
    onCreateCommunity: handleCreateCommunity,
    onCreateTopic: handleCreateTopic,
    personActionId,
    communityActionId,
    onTogglePersonHidden: handleTogglePersonHidden,
    onDeletePerson: handleDeletePerson,
    onToggleCommunityHidden: handleToggleCommunityHidden,
    onDeleteCommunity: handleDeleteCommunity,
  } = props;
  const [personAddOpen, setPersonAddOpen] = useState(false);
  const [communityAddOpen, setCommunityAddOpen] = useState(false);
  const [topicAddOpen, setTopicAddOpen] = useState(false);
  const [communityExplorerParentId, setCommunityExplorerParentId] =
    useState<string | null>(null);
  const [communityExplorerIndex, setCommunityExplorerIndex] = useState(0);
  const [communityViewMode, setCommunityViewMode] = useState<"explore" | "list">(
    "explore"
  );
  const [communityActionMenuId, setCommunityActionMenuId] = useState<string | null>(null);
  const communityLongPressTimer = useRef<number | null>(null);
  const communityLongPressTriggered = useRef(false);
  const communityTree = useMemo(
    () => buildCommunityTree(managedCommunities),
    [managedCommunities]
  );
  const communityExplorerParent = useMemo(
    () => findCommunityNode(communityTree, communityExplorerParentId),
    [communityExplorerParentId, communityTree]
  );
  const communityExplorerPath = useMemo(
    () => findCommunityPath(communityTree, communityExplorerParentId),
    [communityExplorerParentId, communityTree]
  );
  const communityExplorerItems =
    communityExplorerParent?.children ?? communityTree;
  const communityActionMenuNode = useMemo(
    () => findCommunityNode(communityTree, communityActionMenuId),
    [communityActionMenuId, communityTree]
  );

  useEffect(() => {
    if (communityExplorerParentId && !communityExplorerParent) {
      setCommunityExplorerParentId(null);
      setCommunityExplorerIndex(0);
      return;
    }

    setCommunityExplorerIndex((currentIndex) =>
      Math.min(Math.max(currentIndex, 0), Math.max(communityExplorerItems.length - 1, 0))
    );
  }, [communityExplorerItems.length, communityExplorerParent, communityExplorerParentId]);

  const renderPeoplePanel = () => {
    const sortedPeople = [...managedPersons].sort((left, right) =>
      left.name.localeCompare(right.name, "ja")
    );

    return (
      <section className="page-grid">
        <article className="page-card">
          <div className="page-card__header manage-community-header">
            <div>
              <p className="eyebrow">People List</p>
              <h2>人物の管理</h2>
            </div>
            <button
              type="button"
              className="home-record-button"
              onClick={() => setPersonAddOpen((isOpen) => !isOpen)}
              aria-controls="person-add-form"
              aria-expanded={personAddOpen}
              aria-label={personAddOpen ? "人物追加を閉じる" : "人物を追加"}
              title={personAddOpen ? "Close" : "Add person"}
            >
              {personAddOpen ? "×" : "+"}
            </button>
          </div>

          {personAddOpen ? (
            <div className="manage-inline-form" id="person-add-form">
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
              <div className="button-row manage-inline-form__actions">
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={handleCreatePerson}
                  disabled={isCreatingPerson}
                >
                  {isCreatingPerson ? "追加中..." : "人物を追加"}
                </button>
                <button
                  type="button"
                  className="button button--ghost"
                  onClick={() => setPersonAddOpen(false)}
                  disabled={isCreatingPerson}
                >
                  閉じる
                </button>
              </div>
            </div>
          ) : null}

          {sortedPeople.length === 0 ? (
            <EmptyState
              title="まだ人物がいません"
              description="右上の追加ボタンから人物を追加できます。"
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



  const renderCommunitiesPanel = () => {
    const sortedCommunities = [...managedCommunities].sort((left, right) =>
      left.path.localeCompare(right.path, "ja")
    );
    const hasMultipleCommunities = communityExplorerItems.length > 1;
    const carouselCommunities = communityExplorerItems
      .map((community, index) => ({
        community,
        index,
        offset: getCarouselOffset(
          index,
          communityExplorerIndex,
          communityExplorerItems.length
        ),
      }))
      .sort((left, right) => left.offset - right.offset);

    const renderCommunityListActions = (community: Community) => {
      const isBusy = communityActionId === community.id;

      return (
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
      );
    };

    const moveCommunityCarousel = (direction: -1 | 1) => {
      if (communityExplorerItems.length === 0) return;

      setCommunityExplorerIndex((currentIndex) => {
        const total = communityExplorerItems.length;
        return (currentIndex + direction + total) % total;
      });
    };

    const goBackCommunityLevel = () => {
      const nextParentId =
        communityExplorerPath[communityExplorerPath.length - 2]?.id ?? null;
      setCommunityExplorerParentId(nextParentId);
      setCommunityExplorerIndex(0);
      setCommunityActionMenuId(null);
    };

    const clearCommunityLongPress = () => {
      if (communityLongPressTimer.current !== null) {
        window.clearTimeout(communityLongPressTimer.current);
        communityLongPressTimer.current = null;
      }
    };

    const handleCommunityBubblePointerDown = (
      event: PointerEvent<HTMLButtonElement>,
      community: CommunityTreeNode
    ) => {
      event.currentTarget.setPointerCapture(event.pointerId);
      communityLongPressTriggered.current = false;
      clearCommunityLongPress();

      communityLongPressTimer.current = window.setTimeout(() => {
        communityLongPressTriggered.current = true;
        setCommunityActionMenuId(community.id);
      }, 520);
    };

    const handleCommunityBubblePointerEnd = (
      event: PointerEvent<HTMLButtonElement>,
      community: CommunityTreeNode,
      index: number
    ) => {
      if (event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }
      clearCommunityLongPress();

      if (communityLongPressTriggered.current) {
        communityLongPressTriggered.current = false;
        return;
      }

      setCommunityActionMenuId(null);
      if (community.children.length > 0) {
        setCommunityExplorerParentId(community.id);
        setCommunityExplorerIndex(0);
        return;
      }
      if (index !== communityExplorerIndex) {
        setCommunityExplorerIndex(index);
      }
    };

    const handleCommunityBubblePointerCancel = (
      event: PointerEvent<HTMLButtonElement>
    ) => {
      if (event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }
      clearCommunityLongPress();
      communityLongPressTriggered.current = false;
    };

    const renderCommunityList = () => {
      if (sortedCommunities.length === 0) {
        return (
          <EmptyState
            title="まだコミュニティがありません"
            description="右上の追加ボタンから階層を作れます。"
          />
        );
      }

      return (
        <div className="manage-list">
          {sortedCommunities.map((community) => (
            <div key={community.id} className="manage-entry">
              <div className="manage-entry__main">
                <div className="manage-entry__title">
                  <strong>{community.name}</strong>
                  {community.is_hidden ? <span className="status-tag">非表示</span> : null}
                </div>
                <span>{community.path}</span>
              </div>
              {renderCommunityListActions(community)}
            </div>
          ))}
        </div>
      );
    };

    const renderCommunityExplorer = () => {
      if (communityExplorerItems.length === 0) {
        return (
          <EmptyState
            title={
              communityExplorerParent
                ? "この中にはまだコミュニティがありません"
                : "まだコミュニティがありません"
            }
            description="右上の追加ボタンから階層を作れます。"
          />
        );
      }

      return (
        <div className="community-explorer">
          <div className="community-explorer__toolbar">
            <div className="community-explorer__crumbs" aria-label="表示中の階層">
              <button
                type="button"
                className={`community-explorer__crumb ${
                  !communityExplorerParentId ? "community-explorer__crumb--active" : ""
                }`}
                onClick={() => {
                  setCommunityExplorerParentId(null);
                  setCommunityExplorerIndex(0);
                }}
              >
                すべて
              </button>
              {communityExplorerPath.map((community) => (
                <button
                  key={community.id}
                  type="button"
                  className={`community-explorer__crumb ${
                    community.id === communityExplorerParentId
                      ? "community-explorer__crumb--active"
                      : ""
                  }`}
                  onClick={() => {
                    setCommunityExplorerParentId(community.id);
                    setCommunityExplorerIndex(0);
                  }}
                >
                  {community.name}
                </button>
              ))}
            </div>
            <span className="community-explorer__count">
              {communityExplorerIndex + 1} / {communityExplorerItems.length}
            </span>
          </div>

          <div className="community-explorer__stage" aria-live="polite">
            {hasMultipleCommunities ? (
              <button
                type="button"
                className="community-explorer__nav community-explorer__nav--prev"
                onClick={() => moveCommunityCarousel(-1)}
                aria-label="前のコミュニティ"
              >
                &lt;
              </button>
            ) : null}

            {carouselCommunities.map(({ community, index, offset }) => {
              const isSelected = index === communityExplorerIndex;
              const distance = Math.abs(offset);
              const visualOffset = clampCarouselOffset(offset);
              const isVisible = distance <= 2;
              const style: CSSProperties = {
                ...getCommunityBubblePosition(
                  visualOffset,
                  Boolean(communityExplorerParent)
                ),
                opacity: !isVisible ? 0 : distance === 0 ? 1 : distance === 1 ? 0.78 : 0.42,
                pointerEvents: isVisible ? "auto" : "none",
                transitionDelay: `${Math.min(distance, 2) * 24}ms`,
                zIndex: isVisible ? 10 - distance : 0,
              };

              return (
                <button
                  key={community.id}
                  type="button"
                  className={`person-bubble community-explorer-bubble ${
                    isSelected ? "person-bubble--active community-explorer-bubble--active" : ""
                  } ${community.is_hidden ? "person-bubble--quiet" : ""}`}
                  style={style}
                  onPointerDown={(event) =>
                    handleCommunityBubblePointerDown(event, community)
                  }
                  onPointerUp={(event) =>
                    handleCommunityBubblePointerEnd(event, community, index)
                  }
                  onPointerCancel={handleCommunityBubblePointerCancel}
                  aria-label={`${community.name}${
                    isSelected && community.children.length > 0
                      ? "、タップで子コミュニティを表示"
                      : ""
                  }、長押しで操作`}
                >
                  <strong>{community.name}</strong>
                  <span>
                    {community.children.length > 0
                      ? `${community.children.length}件`
                      : "子なし"}
                  </span>
                </button>
              );
            })}

            {communityExplorerParent ? (
              <button
                type="button"
                className="community-explorer__return"
                onClick={goBackCommunityLevel}
                aria-label={`${communityExplorerParent.name}へ戻る`}
              >
                <span aria-hidden="true">↑</span>
              </button>
            ) : null}

            {communityActionMenuNode ? (
              <div className="community-action-menu" role="dialog" aria-label="コミュニティ操作">
                <strong>{communityActionMenuNode.name}</strong>
                <div className="button-row community-action-menu__actions">
                  <button
                    type="button"
                    className="button button--ghost button--small"
                    onClick={() => {
                      void handleToggleCommunityHidden(communityActionMenuNode);
                      setCommunityActionMenuId(null);
                    }}
                    disabled={communityActionId === communityActionMenuNode.id}
                  >
                    {communityActionMenuNode.is_hidden ? "再表示" : "非表示"}
                  </button>
                  <button
                    type="button"
                    className="button button--danger button--small"
                    onClick={() => {
                      void handleDeleteCommunity(communityActionMenuNode);
                      setCommunityActionMenuId(null);
                    }}
                    disabled={communityActionId === communityActionMenuNode.id}
                  >
                    削除
                  </button>
                  <button
                    type="button"
                    className="button button--ghost button--small"
                    onClick={() => setCommunityActionMenuId(null)}
                  >
                    閉じる
                  </button>
                </div>
              </div>
            ) : null}

            {hasMultipleCommunities ? (
              <button
                type="button"
                className="community-explorer__nav community-explorer__nav--next"
                onClick={() => moveCommunityCarousel(1)}
                aria-label="次のコミュニティ"
              >
                &gt;
              </button>
            ) : null}
          </div>

          <div className="community-explorer__dots" aria-hidden="true">
            {communityExplorerItems.map((community, index) => (
              <span
                key={community.id}
                className={
                  index === communityExplorerIndex
                    ? "community-explorer__dot community-explorer__dot--active"
                    : "community-explorer__dot"
                }
              />
            ))}
          </div>
        </div>
      );
    };

    return (
      <section className="page-grid">
        <article className="page-card">
          <div className="page-card__header manage-community-header">
            <div>
              <p className="eyebrow">Community Tree</p>
              <h2>コミュニティの管理</h2>
            </div>
            <div className="manage-header-actions">
              <button
                type="button"
                className="community-view-toggle"
                onClick={() =>
                  setCommunityViewMode((mode) =>
                    mode === "explore" ? "list" : "explore"
                  )
                }
                aria-label={
                  communityViewMode === "explore"
                    ? "一覧表示に切り替える"
                    : "探索表示に切り替える"
                }
                title={
                  communityViewMode === "explore"
                    ? "Switch to list"
                    : "Switch to explore"
                }
              >
                {communityViewMode === "explore" ? "◎" : "☰"}
              </button>
              <button
                type="button"
                className="home-record-button"
                onClick={() => setCommunityAddOpen((isOpen) => !isOpen)}
                aria-controls="community-add-form"
                aria-expanded={communityAddOpen}
                aria-label={
                  communityAddOpen ? "コミュニティ追加を閉じる" : "コミュニティを追加"
                }
                title={communityAddOpen ? "Close" : "Add community"}
              >
                {communityAddOpen ? "×" : "+"}
              </button>
            </div>
          </div>

          {communityAddOpen ? (
            <div className="manage-inline-form" id="community-add-form">
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
              <div className="button-row manage-inline-form__actions">
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={handleCreateCommunity}
                  disabled={isCreatingCommunity}
                >
                  {isCreatingCommunity ? "追加中..." : "コミュニティを追加"}
                </button>
                <button
                  type="button"
                  className="button button--ghost"
                  onClick={() => setCommunityAddOpen(false)}
                  disabled={isCreatingCommunity}
                >
                  閉じる
                </button>
              </div>
            </div>
          ) : null}

          {communityViewMode === "explore"
            ? renderCommunityExplorer()
            : renderCommunityList()}
        </article>
      </section>
    );
  };



  const renderTopicsManagePanel = () => {
    const topicTree = buildTopicTree(topics);

    return (
      <section className="page-grid">
        <article className="page-card">
          <div className="page-card__header manage-community-header">
            <div>
              <p className="eyebrow">Topic Tree</p>
              <h2>話題の管理</h2>
            </div>
            <button
              type="button"
              className="home-record-button"
              onClick={() => setTopicAddOpen((isOpen) => !isOpen)}
              aria-controls="topic-add-form"
              aria-expanded={topicAddOpen}
              aria-label={topicAddOpen ? "話題追加を閉じる" : "話題を追加"}
              title={topicAddOpen ? "Close" : "Add topic"}
            >
              {topicAddOpen ? "×" : "+"}
            </button>
          </div>

          {topicAddOpen ? (
            <div className="manage-inline-form" id="topic-add-form">
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
              <div className="button-row manage-inline-form__actions">
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={handleCreateTopic}
                  disabled={isCreatingTopic}
                >
                  {isCreatingTopic ? "追加中..." : "話題を追加"}
                </button>
                <button
                  type="button"
                  className="button button--ghost"
                  onClick={() => setTopicAddOpen(false)}
                  disabled={isCreatingTopic}
                >
                  閉じる
                </button>
              </div>
            </div>
          ) : null}

          {topicTree.length === 0 ? (
            <EmptyState
              title="話題はまだありません"
              description="右上の追加ボタンから話題を追加できます。"
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
      <section className="page-card manage-tabs-card">
        <div className="page-card__header">
          {/* <div>
            <p className="eyebrow">Manage</p>
            <h2>管理画面</h2>
          </div> */}
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

      {managePanel === "people" ? renderPeoplePanel() : null}
      {managePanel === "communities" ? renderCommunitiesPanel() : null}
      {managePanel === "topics" ? renderTopicsManagePanel() : null}
    </section>
  );



  return renderManagePage();
}
