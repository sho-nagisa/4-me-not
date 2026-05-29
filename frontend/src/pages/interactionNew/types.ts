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

export type CommunityTreeNode = Community & {
  children: CommunityTreeNode[];
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
export type PageId = "home" | "record" | "search" | "history" | "person" | "manage";
export type PersonPanelId = "summary" | "topics" | "notes" | "recent";
export type ManagePanelId = "people" | "communities" | "topics";
export type SearchTargetType =
  | "interaction"
  | "person"
  | "task"
  | "calendar_event"
  | "community"
  | "topic";

export type AuthAccount = {
  id: string;
  email: string;
  is_active: boolean;
};

export type HistoryFilters = {
  personId: string;
  communityId: string;
  topicId: string;
  shareLevel: ShareLevel | "";
  search: string;
  dateFrom: string;
  dateTo: string;
  limit?: number;
  offset?: number;
};

export type CreateInteractionPayload = {
  occurred_at: string;
  person_id: string;
  community_id: string | null;
  topic_id: string | null;
  interaction_type: InteractionType;
  share_level: ShareLevel;
  content: string;
  note: string;
};

export type CreatePersonPayload = {
  name: string;
  canonical_name?: string | null;
  primary_community_id: string | null;
};

export type CreateCommunityPayload = {
  name: string;
  description?: string | null;
  parent_id: string | null;
};

export type CreateTopicPayload = {
  name: string;
  description?: string | null;
  parent_id: string | null;
};

export type CreateTaskPayload = {
  title: string;
  description?: string | null;
  due_at?: string | null;
  priority?: number | null;
};

export type UpdateTaskPayload = Partial<CreateTaskPayload> & {
  status?: "TODO" | "DONE" | "SKIPPED";
};

export type SearchOptions = {
  limit?: number;
  dateFrom?: string | null;
  dateTo?: string | null;
  fuzzy?: boolean;
};

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

export type InteractionPage = {
  items: InteractionRecord[];
  total_count: number;
  limit: number | null;
  offset: number;
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

export type SearchResultItem = {
  id: string;
  target_type: SearchTargetType;
  target_id: string;
  title: string;
  summary: string | null;
  snippet: string;
  score: number;
  semantic_score: number;
  keyword_score: number;
  fuzzy_score: number;
  recency_score: number;
  person_id: string | null;
  person_name: string | null;
  community_id: string | null;
  community_path: string | null;
  topic_id: string | null;
  topic_path: string | null;
  due_at: string | null;
  status: string | null;
  status_label: string | null;
  source_type: string | null;
  is_candidate: boolean;
  candidate_status: string | null;
  start_at: string | null;
  end_at: string | null;
  location: string | null;
  target_label: string | null;
  occurred_at: string | null;
  indexed_at: string;
};

export type TaskLinkRecord = {
  target_type: SearchTargetType;
  target_id: string;
  target_label: string | null;
  role: string;
  confidence: number | null;
};

export type TaskRecord = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  due_at: string | null;
  priority: number | null;
  source_type: string;
  source_id: string | null;
  is_candidate: boolean;
  candidate_status: string;
  confidence: number | null;
  links: TaskLinkRecord[];
  created_at: string;
  updated_at: string;
};

export type SearchResponse = {
  query: string;
  embedding_model: string | null;
  results: SearchResultItem[];
  answer: SearchAnswer;
  groups: {
    people: SearchResultItem[];
    interactions: SearchResultItem[];
    tasks: SearchResultItem[];
    calendar_events: SearchResultItem[];
    communities: SearchResultItem[];
    topics: SearchResultItem[];
  };
};

export type SearchAnswerPerson = {
  person_id: string;
  person_name: string;
  community_path: string | null;
  score: number;
  reasons: string[];
};

export type SearchAnswerPrimaryPerson = {
  person_id: string;
  person_name: string;
  community_path: string | null;
  score: number;
};

export type SearchAnswer = {
  answer_model: string;
  summary: string;
  confidence: "none" | "low" | "medium" | "high";
  primary_person: SearchAnswerPrimaryPerson | null;
  people: SearchAnswerPerson[];
  evidence: SearchResultItem[];
  follow_up_queries: string[];
};
