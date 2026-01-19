import { useEffect, useState } from "react";

type Person = {
  id: string;
  name: string;
};

type Community = {
  id: string;
  name: string;
};

type InteractionType =
  | "MEETING"
  | "CHAT"
  | "CALL"
  | "MESSAGE"
  | "OBSERVATION";

export default function InteractionNew() {
  // ---- state ----
  const [persons, setPersons] = useState<Person[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);

  const [occurredAt, setOccurredAt] = useState<string>(
    new Date().toISOString().slice(0, 16)
  );
  const [personId, setPersonId] = useState<string>("");
  const [communityId, setCommunityId] = useState<string>("");
  const [interactionType, setInteractionType] =
    useState<InteractionType>("MEETING");
  const [content, setContent] = useState<string>("");
  const [note, setNote] = useState<string>("");

  // ---- fetch initial data ----
  useEffect(() => {
    fetch("/api/persons")
      .then((res) => res.json())
      .then(setPersons);

    fetch("/api/communities")
      .then((res) => res.json())
      .then(setCommunities);
  }, []);

  // ---- submit ----
  const handleSubmit = async () => {
    if (!personId || !content) {
      alert("person と content は必須");
      return;
    }

    const res = await fetch("/api/interactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        occurred_at: occurredAt,
        person_id: personId,
        community_id: communityId || null,
        interaction_type: interactionType,
        content,
        note,
      }),
    });

    if (!res.ok) {
      alert("保存失敗");
      return;
    }

    alert("保存しました");
    setContent("");
    setNote("");
  };

  // ---- UI ----
  return (
    <div>
      <h1>Interaction New</h1>

      <div>
        <label>日時</label>
        <input
          type="datetime-local"
          value={occurredAt}
          onChange={(e) => setOccurredAt(e.target.value)}
        />
      </div>

      <div>
        <label>Person</label>
        <select
          value={personId}
          onChange={(e) => setPersonId(e.target.value)}
        >
          <option value="">-- select --</option>
          {persons.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label>Community（任意）</label>
        <select
          value={communityId}
          onChange={(e) => setCommunityId(e.target.value)}
        >
          <option value="">-- none --</option>
          {communities.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label>Type</label>
        <select
          value={interactionType}
          onChange={(e) =>
            setInteractionType(e.target.value as InteractionType)
          }
        >
          <option value="MEETING">MEETING</option>
          <option value="CHAT">CHAT</option>
          <option value="CALL">CALL</option>
          <option value="MESSAGE">MESSAGE</option>
          <option value="OBSERVATION">OBSERVATION</option>
        </select>
      </div>

      <div>
        <label>Content</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
      </div>

      <div>
        <label>Note（任意）</label>
        <textarea value={note} onChange={(e) => setNote(e.target.value)} />
      </div>

      <button onClick={handleSubmit}>保存</button>
    </div>
  );
}
