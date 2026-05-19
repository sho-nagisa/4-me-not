import { useState } from "react";
import type { Dispatch, SetStateAction } from "react";

import { EmptyState, SectionTabs, TopicTree } from "./components";
import { managePanelOptions } from "./constants";
import type { Community, ManagePanelId, Person, Topic } from "./types";
import { buildTopicTree } from "./utils";

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
  const [communityAddOpen, setCommunityAddOpen] = useState(false);

  const renderPeoplePanel = () => {
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



  const renderCommunitiesPanel = () => {
    const sortedCommunities = [...managedCommunities].sort((left, right) =>
      left.path.localeCompare(right.path, "ja")
    );

    return (
      <section className="page-grid">
        <article className="page-card">
          <div className="page-card__header manage-community-header">
            <div>
              <p className="eyebrow">Community Tree</p>
              <h2>コミュニティの管理</h2>
            </div>
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
