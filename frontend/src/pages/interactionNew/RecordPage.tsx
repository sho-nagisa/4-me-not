import type { Dispatch, RefObject, SetStateAction } from "react";

import { CommunityCascadeSelector, EmptyState, SummaryRows } from "./components";
import { interactionTypeOptions, shareLevelOptions } from "./constants";
import type { Community, InteractionType, Person, PersonDashboard, ShareLevel, Topic } from "./types";
import { formatDateTime } from "./utils";

type RecordPageProps = {
  isMobile: boolean;
  mobileRecordPanel: "input" | "check";
  mobileRecordSwipeRef: RefObject<HTMLDivElement>;
  onMobileRecordScroll: () => void;
  onSwitchMobileRecordPanel: (panel: "input" | "check") => void;
  occurredAt: string;
  setOccurredAt: Dispatch<SetStateAction<string>>;
  personId: string;
  onPersonChange: (personId: string) => void;
  loading: boolean;
  persons: Person[];
  communityId: string;
  setCommunityId: Dispatch<SetStateAction<string>>;
  setCommunityTouched: Dispatch<SetStateAction<boolean>>;
  communities: Community[];
  topicId: string;
  setTopicId: Dispatch<SetStateAction<string>>;
  topics: Topic[];
  interactionType: InteractionType;
  setInteractionType: Dispatch<SetStateAction<InteractionType>>;
  selectedType?: { description: string };
  shareLevel: ShareLevel;
  setShareLevel: Dispatch<SetStateAction<ShareLevel>>;
  selectedShareLevel?: { description: string };
  content: string;
  setContent: Dispatch<SetStateAction<string>>;
  note: string;
  setNote: Dispatch<SetStateAction<string>>;
  onSubmit: () => void | Promise<void>;
  isSaving: boolean;
  communityTouched: boolean;
  selectedPerson?: Person;
  recordDashboardLoading: boolean;
  recordDashboard: PersonDashboard | null;
};

export function RecordPage(props: RecordPageProps) {
  const {
    isMobile,
    mobileRecordPanel,
    mobileRecordSwipeRef,
    onMobileRecordScroll: handleMobileRecordScroll,
    onSwitchMobileRecordPanel: switchMobileRecordPanel,
    occurredAt,
    setOccurredAt,
    personId,
    onPersonChange: handlePersonChange,
    loading,
    persons,
    communityId,
    setCommunityId,
    setCommunityTouched,
    communities,
    topicId,
    setTopicId,
    topics,
    interactionType,
    setInteractionType,
    selectedType,
    shareLevel,
    setShareLevel,
    selectedShareLevel,
    content,
    setContent,
    note,
    setNote,
    onSubmit: handleSubmit,
    isSaving,
    communityTouched,
    selectedPerson,
    recordDashboardLoading,
    recordDashboard,
  } = props;

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

        <div className="field field--full">
          <span className="field__label">コミュニティ</span>
          <CommunityCascadeSelector
            communities={communities}
            selectedId={communityId}
            disabled={loading}
            onSelect={(nextCommunityId) => {
              setCommunityId(nextCommunityId);
              setCommunityTouched(true);
            }}
          />
          <span className="field__hint">
            クリックで選択、長押しで子コミュニティを開きます。
          </span>
        </div>

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
}
