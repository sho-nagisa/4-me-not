export type Person = {
  id: string;
  name: string;
  is_hidden: boolean;
  primary_community_id: string | null;
  primary_community_path: string | null;
};

export type Community = {
  id: string;
  name: string;
  is_hidden: boolean;
  parent_id: string | null;
  path: string;
};

export type Topic = {
  id: string;
  name: string;
  parent_id: string | null;
  path: string;
};

export type TopicTreeNode = Topic & {
  children: TopicTreeNode[];
};

export type PersonBubble = {
  person: Person;
  count: number;
  size: number;
  distance: number;
  x: number;
  y: number;
};

export type HomeViewProps = {
  personBubbles: PersonBubble[];
  selectedPersonId: string;
  recentInteractions: InteractionRecord[];
  onBubbleSelect: (personId: string) => void;
  onOpenHistory: () => void;
  onOpenRecord: () => void;
};

export type InteractionType =
  | "MEETING"
  | "CHAT"
  | "CALL"
  | "MESSAGE"
  | "OBSERVATION";

export type ShareLevel = "SHARED" | "PARTIAL" | "WITHHELD";
export type PageId = "home" | "record" | "history" | "person" | "manage";
export type PersonPanelId = "summary" | "topics" | "notes" | "recent";
export type ManagePanelId = "people" | "communities" | "topics";

export type InteractionRecord = {
  id: string;
  person_id: string;
  person_name: string;
  community_id: string | null;
  community_name: string | null;
  community_path: string | null;
  topic_id: string | null;
  topic_name: string | null;
  topic_path: string | null;
  interaction_type: string;
  interaction_type_label: string;
  share_level: ShareLevel;
  share_level_label: string;
  occurred_at: string | null;
  content: string | null;
  note: string | null;
  created_at: string;
};

export type PersonInteractionCount = {
  person_id: string;
  count: number;
};

export type InteractionOverview = {
  total_count: number;
  recent_interactions: InteractionRecord[];
  person_counts: PersonInteractionCount[];
};

export type SummaryItem = {
  id: string;
  label: string;
  count: number;
  shared_count: number;
  partial_count: number;
  withheld_count: number;
};

export type ShareSummary = {
  share_level: ShareLevel;
  label: string;
  count: number;
};

export type PrepTopic = {
  topic: string;
  community: string;
  occurred_at: string | null;
};

export type PrepNote = {
  text: string;
  topic: string;
  share_level: ShareLevel;
  share_level_label: string;
  occurred_at: string | null;
};

export type PersonDashboard = {
  person: Person;
  overview: {
    interaction_count: number;
    latest_occurred_at: string | null;
    shared_count: number;
    partial_count: number;
    withheld_count: number;
  };
  share_summary: ShareSummary[];
  top_topics: SummaryItem[];
  top_communities: SummaryItem[];
  recent_interactions: InteractionRecord[];
  conversation_prep: {
    shared_topics: PrepTopic[];
    partial_topics: PrepTopic[];
    withheld_topics: PrepTopic[];
    recent_notes: PrepNote[];
  };
};
