import type {
  Community,
  CommunityTreeNode,
  InteractionRecord,
  Person,
  PersonBubble,
  PersonInteractionCount,
  Topic,
  TopicTreeNode,
} from "./types";

export const toDateTimeLocalValue = (date = new Date()) => {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
};

export const formatDateTime = (isoText: string | null) => {
  if (!isoText) return "未設定";
  const date = new Date(isoText);
  if (Number.isNaN(date.getTime())) return isoText;
  return date.toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const buildDateQuery = (dateText: string, mode: "from" | "to") => {
  if (!dateText) return null;
  const suffix = mode === "from" ? "T00:00:00" : "T23:59:59";
  return new Date(`${dateText}${suffix}`).toISOString();
};

export const truncate = (text: string | null | undefined, max = 120) => {
  if (!text) return "内容なし";
  if (text.length <= max) return text;
  return `${text.slice(0, max)}...`;
};

export const buildTopicTree = (items: Topic[]): TopicTreeNode[] => {
  const nodes = new Map<string, TopicTreeNode>();
  const roots: TopicTreeNode[] = [];

  items.forEach((topic) => {
    nodes.set(topic.id, { ...topic, children: [] });
  });

  nodes.forEach((node) => {
    if (node.parent_id && nodes.has(node.parent_id)) {
      nodes.get(node.parent_id)?.children.push(node);
      return;
    }
    roots.push(node);
  });

  const sortNodes = (treeNodes: TopicTreeNode[]) => {
    treeNodes.sort((left, right) => left.name.localeCompare(right.name, "ja"));
    treeNodes.forEach((node) => sortNodes(node.children));
  };

  sortNodes(roots);
  return roots;
};

export const buildCommunityTree = (items: Community[]): CommunityTreeNode[] => {
  const nodes = new Map<string, CommunityTreeNode>();
  const roots: CommunityTreeNode[] = [];

  items.forEach((community) => {
    nodes.set(community.id, { ...community, children: [] });
  });

  nodes.forEach((node) => {
    if (node.parent_id && nodes.has(node.parent_id)) {
      nodes.get(node.parent_id)?.children.push(node);
      return;
    }
    roots.push(node);
  });

  const sortNodes = (treeNodes: CommunityTreeNode[]) => {
    treeNodes.sort((left, right) => left.name.localeCompare(right.name, "ja"));
    treeNodes.forEach((node) => sortNodes(node.children));
  };

  sortNodes(roots);
  return roots;
};

export const buildPersonBubbles = (
  people: Person[],
  records: InteractionRecord[],
  communityId: string | null = null,
  maxVisible = 7
): PersonBubble[] => {
  const counts = new Map<string, number>();

  records.forEach((record) => {
    if (communityId && record.community_id !== communityId) {
      return;
    }
    counts.set(record.person_id, (counts.get(record.person_id) ?? 0) + 1);
  });

  return buildPersonBubblesFromCountMap(people, counts, maxVisible);
};

export const buildPersonBubblesFromCounts = (
  people: Person[],
  counts: PersonInteractionCount[],
  maxVisible = 7
): PersonBubble[] => {
  return buildPersonBubblesFromCountMap(
    people,
    new Map(counts.map((item) => [item.person_id, item.count])),
    maxVisible
  );
};

const buildPersonBubblesFromCountMap = (
  people: Person[],
  counts: Map<string, number>,
  maxVisible = 7
): PersonBubble[] => {
  const layoutSlots = [
    { x: 50, y: 50 },
    { x: 31, y: 43 },
    { x: 69, y: 43 },
    { x: 39, y: 73 },
    { x: 61, y: 73 },
    { x: 18, y: 62 },
    { x: 82, y: 62 },
  ];

  const maxCount = Math.max(1, ...people.map((person) => counts.get(person.id) ?? 0));

  const sortedBubbles = people
    .map((person) => {
      const count = counts.get(person.id) ?? 0;
      const ratio = count / maxCount;
      const size = Math.round(40 + ratio * 58);
      return {
        person,
        count,
        size,
        distance: 0,
        x: 50,
        y: 50,
      };
    })
    .sort((left, right) => {
      if (right.count !== left.count) return right.count - left.count;
      return left.person.name.localeCompare(right.person.name, "ja");
    })
    .slice(0, maxVisible);

  return sortedBubbles.map((bubble, index) => {
    if (index === 0) {
      return {
        ...bubble,
        distance: 0,
        ...layoutSlots[index],
      };
    }

    const sizePressure = bubble.size / sortedBubbles[0].size;
    const ringPressure = Math.min(1, index / Math.max(1, sortedBubbles.length - 1));
    const distance = 1 + sizePressure * 0.4 + ringPressure * 0.28;
    const slot = layoutSlots[index];

    return {
      ...bubble,
      distance,
      x: 50 + (slot.x - 50) * distance,
      y: 50 + (slot.y - 50) * distance,
    };
  });
};
