import { useCallback, useEffect, useState } from "react";

import { searchMemory } from "../interactionsApi";
import {
  relationSearchScopeOptions,
  relationSearchTargetTypes,
  type WorkspaceMode,
} from "../navigation";
import type { SearchScope } from "../SearchPage";
import type { SearchResponse, SearchTargetType } from "../types";
import { buildDateQuery } from "../utils";

type UseMemorySearchParams = {
  workspaceMode: WorkspaceMode;
};

export function useMemorySearch({ workspaceMode }: UseMemorySearchParams) {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchScope, setSearchScope] = useState<SearchScope>("all");
  const [searchDateFrom, setSearchDateFrom] = useState("");
  const [searchDateTo, setSearchDateTo] = useState("");
  const [searchFuzzy, setSearchFuzzy] = useState(true);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  const runSearch = useCallback(
    async (nextQuery = searchQuery, nextScope = searchScope) => {
      const trimmedQuery = nextQuery.trim();
      if (!trimmedQuery) {
        setSearchResult(null);
        setSearchError(null);
        return;
      }

      const relationScope = relationSearchScopeOptions.some(
        (option) => option.id === nextScope
      )
        ? nextScope
        : "all";
      const targetTypes: SearchTargetType[] =
        relationScope === "all" ? relationSearchTargetTypes : [relationScope];
      const dateFrom = buildDateQuery(searchDateFrom, "from");
      const dateTo = buildDateQuery(searchDateTo, "to");

      setSearchLoading(true);
      setSearchError(null);
      try {
        const result = await searchMemory(trimmedQuery, targetTypes, {
          dateFrom,
          dateTo,
          fuzzy: searchFuzzy,
        });
        setSearchResult(result);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "検索に失敗しました。";
        setSearchError(message);
      } finally {
        setSearchLoading(false);
      }
    },
    [searchDateFrom, searchDateTo, searchFuzzy, searchQuery, searchScope]
  );

  useEffect(() => {
    if (
      workspaceMode === "relations" &&
      !relationSearchScopeOptions.some((option) => option.id === searchScope)
    ) {
      setSearchScope("all");
    }
  }, [workspaceMode, searchScope]);

  return {
    searchQuery,
    setSearchQuery,
    searchScope,
    setSearchScope,
    searchDateFrom,
    setSearchDateFrom,
    searchDateTo,
    setSearchDateTo,
    searchFuzzy,
    setSearchFuzzy,
    searchResult,
    searchError,
    searchLoading,
    runSearch,
  };
}
