import { apiFetch } from "../../api/client";
import type { VetoData } from "./types";

export interface GetTeamVetoDataParams {
  from_date: Date;
  to_date: Date;
  team_id: number;
}

export function getTeamVetoData(
  params: GetTeamVetoDataParams,
): Promise<VetoData[]> {
  const searchParams = new URLSearchParams({
    from_date: params.from_date.toISOString(),
    to_date: params.to_date.toISOString(),
    team_id: params.team_id.toString(),
  });

  return apiFetch<VetoData[]>(`/api/Team/veto-data?${searchParams.toString()}`);
}
