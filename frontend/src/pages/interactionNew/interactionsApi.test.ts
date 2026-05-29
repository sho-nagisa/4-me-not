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
});
