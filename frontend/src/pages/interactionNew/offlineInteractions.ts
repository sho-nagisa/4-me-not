import type { CreateInteractionPayload } from "./interactionsApi";

const RECORD_DRAFT_KEY = "4-me-not:record-draft:v1";
const PENDING_INTERACTIONS_KEY = "4-me-not:pending-interactions:v1";

export type PendingInteraction = {
  id: string;
  payload: CreateInteractionPayload;
  createdAt: string;
};

const canUseStorage = () => {
  try {
    return typeof window !== "undefined" && Boolean(window.localStorage);
  } catch {
    return false;
  }
};

const readJson = <T,>(key: string, fallback: T): T => {
  if (!canUseStorage()) return fallback;

  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : fallback;
  } catch {
    return fallback;
  }
};

const writeJson = (key: string, value: unknown) => {
  if (!canUseStorage()) return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // If storage is unavailable or full, keep the app usable and let normal save errors surface.
  }
};

const createLocalId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

export const loadRecordDraft = () =>
  readJson<Partial<CreateInteractionPayload> | null>(RECORD_DRAFT_KEY, null);

export const saveRecordDraft = (draft: Partial<CreateInteractionPayload>) => {
  writeJson(RECORD_DRAFT_KEY, draft);
};

export const clearRecordDraft = () => {
  if (!canUseStorage()) return;
  try {
    window.localStorage.removeItem(RECORD_DRAFT_KEY);
  } catch {
    // Ignore storage cleanup failures.
  }
};

export const getPendingInteractions = () =>
  readJson<PendingInteraction[]>(PENDING_INTERACTIONS_KEY, []);

export const getPendingInteractionCount = () => getPendingInteractions().length;

export const enqueuePendingInteraction = (payload: CreateInteractionPayload) => {
  const queue = getPendingInteractions();
  const nextItem: PendingInteraction = {
    id: createLocalId(),
    payload,
    createdAt: new Date().toISOString(),
  };
  writeJson(PENDING_INTERACTIONS_KEY, [...queue, nextItem]);
  return nextItem;
};

export const removePendingInteraction = (id: string) => {
  writeJson(
    PENDING_INTERACTIONS_KEY,
    getPendingInteractions().filter((item) => item.id !== id)
  );
};

export const syncPendingInteractions = async (
  sendInteraction: (payload: CreateInteractionPayload) => Promise<void>,
  onSent?: () => void
) => {
  const pendingItems = getPendingInteractions();
  let sentCount = 0;

  for (const item of pendingItems) {
    await sendInteraction(item.payload);
    removePendingInteraction(item.id);
    sentCount += 1;
    onSent?.();
  }

  return sentCount;
};
