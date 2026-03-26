import { apiFetch } from "../../api/client";
import type { RankingEntry } from "./types";

export interface GetCurrentRankingsParams {
  topX: number;
  vrsRanking: boolean;
}

export function getCurrentRankings(
  params: GetCurrentRankingsParams
): Promise<RankingEntry[]> {
  const searchParams = new URLSearchParams({
    topX: params.topX.toString(),
    vrsRanking: params.vrsRanking.toString(),
  });

  return apiFetch<RankingEntry[]>(`/api/Rankings/current?${searchParams.toString()}`);
}