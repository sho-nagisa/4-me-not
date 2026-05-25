// @vitest-environment jsdom

import { beforeEach, describe, expect, it, vi } from "vitest";

import type { CreateInteractionPayload } from "./interactionsApi";
import {
  clearRecordDraft,
  enqueuePendingInteraction,
  getPendingInteractionCount,
  getPendingInteractions,
  loadRecordDraft,
  removePendingInteraction,
  saveRecordDraft,
  syncPendingInteractions,
} from "./offlineInteractions";

const payload = (title = "話した内容"): CreateInteractionPayload => ({
  occurred_at: "2026-05-25T09:30",
  person_id: "person-1",
  community_id: "community-1",
  topic_id: null,
  interaction_type: "MEETING",
  share_level: "SHARED",
  content: title,
  note: "補足",
});

describe("offline interaction storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("keeps and clears the record draft", () => {
    saveRecordDraft(payload());

    expect(loadRecordDraft()).toEqual(payload());

    clearRecordDraft();

    expect(loadRecordDraft()).toBeNull();
  });

  it("queues interactions while offline and removes sent items", () => {
    const first = enqueuePendingInteraction(payload("1件目"));
    const second = enqueuePendingInteraction(payload("2件目"));

    expect(getPendingInteractionCount()).toBe(2);
    expect(getPendingInteractions().map((item) => item.payload.content)).toEqual([
      "1件目",
      "2件目",
    ]);

    removePendingInteraction(first.id);

    expect(getPendingInteractionCount()).toBe(1);
    expect(getPendingInteractions()[0].id).toBe(second.id);
  });

  it("syncs queued interactions in order after reconnecting", async () => {
    enqueuePendingInteraction(payload("先に送る"));
    enqueuePendingInteraction(payload("後で送る"));
    const sendInteraction = vi.fn<[CreateInteractionPayload], Promise<void>>(
      async () => undefined
    );
    const onSent = vi.fn();

    const sentCount = await syncPendingInteractions(sendInteraction, onSent);

    expect(sentCount).toBe(2);
    expect(sendInteraction.mock.calls.map(([item]) => item.content)).toEqual([
      "先に送る",
      "後で送る",
    ]);
    expect(onSent).toHaveBeenCalledTimes(2);
    expect(getPendingInteractionCount()).toBe(0);
  });

  it("keeps remaining queued interactions when reconnect sync fails", async () => {
    const first = enqueuePendingInteraction(payload("送信できる"));
    const second = enqueuePendingInteraction(payload("残す"));
    const sendInteraction = vi
      .fn()
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce(new Error("network"));

    await expect(syncPendingInteractions(sendInteraction)).rejects.toThrow("network");

    expect(getPendingInteractions().map((item) => item.id)).toEqual([second.id]);
    expect(getPendingInteractions().map((item) => item.id)).not.toContain(first.id);
  });
});
