import { useEffect, useState } from "react";
import { getCurrentRankings } from "../api";
import type { RankingEntry } from "../types";

export function RankingsPage() {
  const [rankings, setRankings] = useState<RankingEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [topX, setTopX] = useState(10);
  const [vrsRanking, setVrsRanking] = useState(true);

  useEffect(() => {
    async function fetchRankings() {
      try {
        setLoading(true);
        setError("");

        const data = await getCurrentRankings({
          topX,
          vrsRanking,
        });

        const sorted = [...data].sort((a, b) => a.rank - b.rank);
        setRankings(sorted);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    void fetchRankings();
  }, [topX, vrsRanking]);

  const rankingDate =
    rankings.length > 0
      ? new Date(rankings[0].ranking_date).toLocaleString()
      : "";

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Current Rankings</h1>

      <div className="filter-controls">
        {/* Top X */}
        <div>
          <label className="filter-label">Top X</label>
          <select
            value={topX}
            onChange={(e) => setTopX(Number(e.target.value))}
            className="filter-select"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={30}>30</option>
            <option value={50}>50</option>
          </select>
        </div>

        {/* Checkbox */}
        <label className="filter-checkbox-label">
          <input
            type="checkbox"
            checked={vrsRanking}
            onChange={(e) => setVrsRanking(e.target.checked)}
            className="filter-checkbox"
          />
          VRS ranking
        </label>
      </div>

      {loading && <p>Loading rankings...</p>}
      {error && <p>Error: {error}</p>}

      {!loading && !error && rankings.length > 0 && (
        <>
          <p>Ranking date: {rankingDate}</p>
          <div className="bg-slate-800 rounded-sm border border-slate-700 overflow-hidden shadow-sm">
            <div className="max-h-125 overflow-y-auto">
              <table className="table-base">
                <thead className="table-header">
                  <tr>
                    <th className="table-th">Rank</th>
                    <th className="table-th">Team</th>
                    <th className="table-th-right">Points</th>
                  </tr>
                </thead>

                <tbody>
                  {rankings.map((team) => (
                    <tr key={team.team_name} className="table-row">
                      <td className="table-td-strong">{team.rank}</td>
                      <td className="table-td">{team.team_name}</td>
                      <td className="table-td-right">{team.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!loading && !error && rankings.length === 0 && <p>No rankings found.</p>}
    </div>
  );
}
