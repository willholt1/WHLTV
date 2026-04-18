import type { Team } from "../models/common";
import { apiFetch } from "./client";

export function getTeams(): Promise<Team[]> {
  return apiFetch<Team[]>(`/api/Teams`);
}
