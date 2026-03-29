import { apiFetch } from "../../api/client";
import type { VetoData } from "./types";

export interface GetTeamVetoDataParams {
  teamID: number;
  startDate: Date;
  endDate: Date;
}

export function getTeamVetoData(
  params: GetTeamVetoDataParams,
): Promise<VetoData[]> {
  const searchParams = new URLSearchParams({
    teamID: params.teamID.toString(),
    startDate: params.startDate.toString(),
    endDate: params.endDate.toString(),
  });

  return apiFetch<VetoData[]>(`/api/Vetos/Team?${searchParams.toString()}`);
}
