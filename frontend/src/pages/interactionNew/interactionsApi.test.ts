import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, fetchJson, searchMemory } from "./interactionsApi";

const emptySearchResponse = {
  query: "alpha",
  embedding_model: null,
  results: [],
  answer: {
    answer_model: "none",
    summary: "",
    confidence: "none",
    primary_person: null,
    people: [],
    evidence: [],
    follow_up_queries: [],
  },
  groups: {
    people: [],
    interactions: [],
    tasks: [],
    calendar_events: [],
    communities: [],
    topics: [],
  },
};

describe("interactions API client", () => {
  afterEach(() => {
    document.cookie = "forme_not_csrf=; Max-Age=0; path=/";
    vi.unstubAllGlobals();
  });

  it("throws an ApiError with backend detail text", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ detail: "Not found" }), { status: 404 }))
    );

    await expect(fetchJson("/api/missing")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      message: "Not found",
    } satisfies Partial<ApiError>);
  });

  it("surfaces validation errors returned as detail arrays", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              detail: [{ msg: "Field required" }, { msg: "Input should be valid" }],
            }),
            { status: 422 }
          )
      )
    );

    await expect(fetchJson("/api/bad")).rejects.toThrow(
      "Field required\nInput should be valid"
    );
  });

  it("trims search text and sends repeat target_type parameters", async () => {
    const fetchMock = vi.fn<[RequestInfo | URL, RequestInit?], Promise<Response>>(
      async () => new Response(JSON.stringify(emptySearchResponse), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    await searchMemory("  alpha  ", ["person", "task"], {
      limit: 5,
      dateFrom: "2026-05-01T00:00:00.000Z",
      fuzzy: false,
    });

    const [url, init] = fetchMock.mock.calls[0];
    const params = new URLSearchParams(String(url).split("?")[1]);

    expect(init).toMatchObject({ credentials: "include" });
    expect(params.get("q")).toBe("alpha");
    expect(params.get("limit")).toBe("5");
    expect(params.get("date_from")).toBe("2026-05-01T00:00:00.000Z");
    expect(params.get("fuzzy")).toBe("false");
    expect(params.getAll("target_type")).toEqual(["person", "task"]);
  });

  it("adds the CSRF token header to unsafe requests", async () => {
    document.cookie = "forme_not_csrf=token-123; path=/";
    const fetchMock = vi.fn<[RequestInfo | URL, RequestInit?], Promise<Response>>(
      async () => new Response(JSON.stringify({ status: "ok" }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchJson<{ status: string }>("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });

    const init = fetchMock.mock.calls[0][1];
    const headers = new Headers(init?.headers);
    expect(init).toMatchObject({ credentials: "include" });
    expect(headers.get("X-CSRF-Token")).toBe("token-123");
    expect(headers.get("Content-Type")).toBe("application/json");
  });
});
