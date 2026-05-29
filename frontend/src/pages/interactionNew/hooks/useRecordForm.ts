import { useCallback, useEffect, useState } from "react";

import {
  clearRecordDraft,
  loadRecordDraft,
  saveRecordDraft,
} from "../offlineInteractions";
import type { CreateInteractionPayload, InteractionType, ShareLevel } from "../types";
import { toDateTimeLocalValue } from "../utils";

export function useRecordForm() {
  const [initialRecordDraft] = useState(loadRecordDraft);

  const [occurredAt, setOccurredAt] = useState<string>(
    initialRecordDraft?.occurred_at ?? toDateTimeLocalValue()
  );
  const [personId, setPersonId] = useState<string>(
    initialRecordDraft?.person_id ?? ""
  );
  const [communityId, setCommunityId] = useState<string>(
    initialRecordDraft?.community_id ?? ""
  );
  const [communityTouched, setCommunityTouched] = useState(false);
  const [topicId, setTopicId] = useState<string>(
    initialRecordDraft?.topic_id ?? ""
  );
  const [interactionType, setInteractionType] = useState<InteractionType>(
    initialRecordDraft?.interaction_type ?? "MEETING"
  );
  const [shareLevel, setShareLevel] = useState<ShareLevel>(
    initialRecordDraft?.share_level ?? "SHARED"
  );
  const [content, setContent] = useState<string>(
    initialRecordDraft?.content ?? ""
  );
  const [note, setNote] = useState<string>(initialRecordDraft?.note ?? "");

  const buildInteractionPayload = useCallback(
    (): CreateInteractionPayload => ({
      occurred_at: occurredAt,
      person_id: personId,
      community_id: communityId || null,
      topic_id: topicId || null,
      interaction_type: interactionType,
      share_level: shareLevel,
      content,
      note,
    }),
    [
      communityId,
      content,
      interactionType,
      note,
      occurredAt,
      personId,
      shareLevel,
      topicId,
    ]
  );

  const resetRecordForm = useCallback(() => {
    setOccurredAt(toDateTimeLocalValue());
    setContent("");
    setNote("");
    setCommunityTouched(false);
    clearRecordDraft();
  }, []);

  useEffect(() => {
    if (!content.trim() && !note.trim()) {
      clearRecordDraft();
      return;
    }

    saveRecordDraft(buildInteractionPayload());
  }, [buildInteractionPayload, content, note]);

  return {
    occurredAt,
    setOccurredAt,
    personId,
    setPersonId,
    communityId,
    setCommunityId,
    communityTouched,
    setCommunityTouched,
    topicId,
    setTopicId,
    interactionType,
    setInteractionType,
    shareLevel,
    setShareLevel,
    content,
    setContent,
    note,
    setNote,
    buildInteractionPayload,
    resetRecordForm,
  };
}
