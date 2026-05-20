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

  const positionedBubbles = sortedBubbles.map((bubble, index) => {
    const noiseA = getStableNoise(bubble.person.id, "angle");
    const noiseB = getStableNoise(bubble.person.id, "radius");

    if (index === 0) {
      const angle = noiseA * Math.PI * 2;
      const radius = 2 + noiseB * 4;

      return {
        ...bubble,
        distance: 0,
        x: 50 + Math.cos(angle) * radius,
        y: 51 + Math.sin(angle) * radius * 0.72,
      };
    }

    const ringPressure = Math.min(1, index / Math.max(1, sortedBubbles.length - 1));
    const countPressure = 1 - bubble.count / maxCount;
    const angle = index * 2.399963229728653 + (noiseA - 0.5) * 1.2;
    const radius = 14 + ringPressure * 26 + countPressure * 5 + (noiseB - 0.5) * 8;
    const x = 50 + Math.cos(angle) * radius;
    const y = 52 + Math.sin(angle) * radius * 0.76;

    return {
      ...bubble,
      distance: radius / 30,
      x: Math.min(85, Math.max(15, x)),
      y: Math.min(82, Math.max(20, y)),
    };
  });

  return resolveBubbleCollisions(positionedBubbles);
};

const resolveBubbleCollisions = (bubbles: PersonBubble[]) => {
  const resolved = bubbles.map((bubble) => ({ ...bubble }));

  for (let iteration = 0; iteration < 12; iteration += 1) {
    for (let leftIndex = 0; leftIndex < resolved.length; leftIndex += 1) {
      for (
        let rightIndex = leftIndex + 1;
        rightIndex < resolved.length;
        rightIndex += 1
      ) {
        const left = resolved[leftIndex];
        const right = resolved[rightIndex];
        const rawDx = right.x - left.x;
        const rawDy = right.y - left.y;
        const distance = Math.hypot(rawDx, rawDy) || 0.001;
        const minimumDistance =
          getBubbleCollisionRadius(left) + getBubbleCollisionRadius(right);

        if (distance >= minimumDistance) continue;

        const fallbackAngle =
          (getStableNoise(`${left.person.id}:${right.person.id}`, "collision") *
            Math.PI *
            2);
        const directionX = distance > 0.01 ? rawDx / distance : Math.cos(fallbackAngle);
        const directionY = distance > 0.01 ? rawDy / distance : Math.sin(fallbackAngle);
        const push = (minimumDistance - distance) / 2;

        resolved[leftIndex] = {
          ...left,
          x: left.x - directionX * push,
          y: left.y - directionY * push,
        };
        resolved[rightIndex] = {
          ...right,
          x: right.x + directionX * push,
          y: right.y + directionY * push,
        };
      }
    }

    resolved.forEach((bubble) => {
      bubble.x = Math.min(86, Math.max(14, bubble.x));
      bubble.y = Math.min(83, Math.max(18, bubble.y));
    });
  }

  return resolved;
};

const getBubbleCollisionRadius = (bubble: PersonBubble) => {
  const sizeRatio = (bubble.size - 40) / 58;
  return 9.5 + Math.max(0, Math.min(1, sizeRatio)) * 4.2;
};

const getStableNoise = (value: string, salt: string) => {
  let hash = 2166136261;
  const text = `${value}:${salt}`;

  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }

  return (hash >>> 0) / 4294967295;
};
