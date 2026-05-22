import type { Dispatch, SetStateAction } from "react";

import { EmptyState, HistoryCard, MetricCard, PersonBubbleCloud, SectionTabs, SummaryRows } from "./components";
import { personPanelOptions } from "./constants";
import type { Community, Person, PersonBubble, PersonDashboard, PersonPanelId } from "./types";
import { formatDateTime, truncate } from "./utils";

type PersonPageProps = {
  detailDashboard: PersonDashboard | null;
  selectedDetailPerson?: Person;
  detailPersonBubbles: PersonBubble[];
  detailPersonId: string;
  onOpenRecordForPerson: (personId: string) => void;
  detailCommunityId: string;
  setDetailCommunityId: Dispatch<SetStateAction<string>>;
  setPersonPanel: Dispatch<SetStateAction<PersonPanelId>>;
  setDetailPersonId: Dispatch<SetStateAction<string>>;
  loading: boolean;
  communities: Community[];
  detailPersons: Person[];
  detailDashboardLoading: boolean;
  onLoadDetailDashboard: (personId: string) => void | Promise<void>;
  personPanel: PersonPanelId;
};

export function PersonPage(props: PersonPageProps) {
  const {
    detailDashboard,
    selectedDetailPerson,
    detailPersonBubbles,
    detailPersonId,
    onOpenRecordForPerson: openRecordForPerson,
    detailCommunityId,
    setDetailCommunityId,
    setPersonPanel,
    setDetailPersonId,
    loading,
    communities,
    detailPersons,
    detailDashboardLoading,
    onLoadDetailDashboard: loadDetailDashboard,
    personPanel,
  } = props;

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
}
