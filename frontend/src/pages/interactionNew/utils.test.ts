import { describe, expect, it } from "vitest";

import type { Community, InteractionRecord, Person, Topic } from "./types";
import {
  buildCommunityTree,
  buildDateQuery,
  buildPersonBubbles,
  buildPersonBubblesFromCounts,
  buildTopicTree,
  truncate,
} from "./utils";

const person = (id: string, name: string): Person => ({
  id,
  name,
  is_hidden: false,
  primary_community_id: null,
  primary_community_path: null,
});

const interaction = (
  id: string,
  personId: string,
  communityId: string | null = null
): InteractionRecord => ({
  id,
  person_id: personId,
  person_name: personId,
  community_id: communityId,
  community_name: communityId,
  community_path: communityId,
  topic_id: null,
  topic_name: null,
  topic_path: null,
  interaction_type: "MEETING",
  interaction_type_label: "対面",
  share_level: "SHARED",
  share_level_label: "話した",
  occurred_at: "2026-05-23T10:00:00+00:00",
  content: "content",
  note: null,
  created_at: "2026-05-23T10:00:00+00:00",
});

describe("interaction page utilities", () => {
  it("builds day boundary query values and ignores empty dates", () => {
    expect(buildDateQuery("", "from")).toBeNull();
    expect(buildDateQuery("2026-05-23", "from")).toBe(
      new Date("2026-05-23T00:00:00").toISOString()
    );
    expect(buildDateQuery("2026-05-23", "to")).toBe(
      new Date("2026-05-23T23:59:59").toISOString()
    );
  });

  it("truncates long text while preserving short and empty labels", () => {
    expect(truncate(null)).toBe("内容なし");
    expect(truncate("短い", 10)).toBe("短い");
    expect(truncate("abcdef", 3)).toBe("abc...");
  });

  it("builds sorted topic and community trees with orphans as roots", () => {
    const topics: Topic[] = [
      { id: "child-b", name: "B", parent_id: "root", path: "root / B" },
      { id: "orphan", name: "Orphan", parent_id: "missing", path: "Orphan" },
      { id: "root", name: "Root", parent_id: null, path: "Root" },
      { id: "child-a", name: "A", parent_id: "root", path: "root / A" },
    ];
    const communities: Community[] = [
      { id: "root", name: "Root", parent_id: null, path: "Root", is_hidden: false },
      { id: "child", name: "Child", parent_id: "root", path: "Root / Child", is_hidden: false },
    ];

    const topicTree = buildTopicTree(topics);
    const communityTree = buildCommunityTree(communities);

    expect(topicTree.map((item) => item.id)).toEqual(["orphan", "root"]);
    expect(topicTree.find((item) => item.id === "root")?.children.map((item) => item.id)).toEqual([
      "child-a",
      "child-b",
    ]);
    expect(communityTree[0].children[0].id).toBe("child");
  });

  it("orders person bubbles by interaction count then name and respects max visible", () => {
    const people = [person("p1", "B"), person("p2", "A"), person("p3", "C")];

    const bubbles = buildPersonBubblesFromCounts(
      people,
      [
        { person_id: "p1", count: 2 },
        { person_id: "p2", count: 2 },
        { person_id: "p3", count: 1 },
      ],
      2
    );

    expect(bubbles.map((item) => item.person.id)).toEqual(["p2", "p1"]);
    expect(bubbles).toHaveLength(2);
    expect(bubbles[0].size).toBeGreaterThanOrEqual(bubbles[1].size);
  });

  it("counts person bubbles within the selected community only", () => {
    const people = [person("p1", "A"), person("p2", "B")];
    const records = [
      interaction("i1", "p1", "c1"),
      interaction("i2", "p1", "c2"),
      interaction("i3", "p2", "c1"),
    ];

    const bubbles = buildPersonBubbles(people, records, "c1");
    const counts = new Map(bubbles.map((item) => [item.person.id, item.count]));

    expect(counts.get("p1")).toBe(1);
    expect(counts.get("p2")).toBe(1);
  });
});
