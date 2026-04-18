import React, { useEffect, useState } from "react";
import { getTeams as defaultGetTeams } from "../api/common";

export interface Team {
  team_id: number;
  team_name: string;
}

interface TeamSelectProps {
  teams?: Team[];
  value: number | null;
  onChange: (teamId: number | null) => void;
  loading?: boolean;
  label?: string;
  className?: string;
  fetchTeams?: () => Promise<Team[]>;
}

export function TeamSelect({
  teams,
  value,
  onChange,
  loading,
  label = "Team:",
  className = "",
  fetchTeams,
}: TeamSelectProps) {
  const [internalTeams, setInternalTeams] = useState<Team[]>([]);
  const [internalLoading, setInternalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If teams prop is not provided, fetch teams internally
  useEffect(() => {
    if (teams) return;
    setInternalLoading(true);
    (fetchTeams || defaultGetTeams)()
      .then((result) => {
        setInternalTeams(result);
        setError(null);
      })
      .catch(() => setError("Failed to load teams"))
      .finally(() => setInternalLoading(false));
  }, [teams, fetchTeams]);

  const isLoading = loading ?? (!teams && internalLoading);
  const teamList = teams ?? internalTeams;

  return (
    <label className={`filter-label ${className}`}>
      {label}
      {isLoading ? (
        <span className="ml-2 text-slate-400">Loading teams...</span>
      ) : error ? (
        <span className="ml-2 text-red-400">{error}</span>
      ) : (
        <select
          value={value ?? ""}
          onChange={(e) => {
            const val = e.target.value;
            onChange(val === "" ? null : Number(val));
          }}
          className="filter-select"
        >
          <option value="">Select a team...</option>
          {teamList.map((team) => (
            <option key={team.team_id} value={team.team_id}>
              {team.team_name}
            </option>
          ))}
        </select>
      )}
    </label>
  );
}
