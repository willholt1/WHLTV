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
    async function loadRankings() {
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
        setError(err instanceof Error ? err.message : "Unknown error")
      } finally {
        setLoading(false);
      }
    }

    void loadRankings();
  }, [topX, vrsRanking]);

  const rankingDate =
    rankings.length > 0
      ? new Date(rankings[0].ranking_date).toLocaleString()
      : "";

  return (
    <div>
      <h1>Current Rankings</h1>

      <div className="flex flex-wrap items-end gap-6 mb-4">

        {/* Top X */}
        <div>
          <label className="block text-xs text-slate-400 mb-1">
            Top X
          </label>

          <select
            value={topX}
            onChange={(e) => setTopX(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 text-slate-200 rounded-md px-3 py-2 text-sm 
                 focus:outline-none focus:ring-2 focus:ring-blue-500 hover:border-slate-500 transition"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={30}>30</option>
            <option value={50}>50</option>
          </select>
        </div>

        {/* Checkbox */}
        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={vrsRanking}
            onChange={(e) => setVrsRanking(e.target.checked)}
            className="w-4 h-4 accent-green-500"
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
            <div className="max-h-[500px] overflow-y-auto">
              <table className="w-full">
                <thead className="bg-slate-700 text-slate-300 text-xs uppercase sticky top-0 z-10">
                  <tr>
                    <th className="px-4 py-3 text-left">Rank</th>
                    <th className="px-4 py-3 text-left">Team</th>
                    <th className="px-4 py-3 text-right">Points</th>
                  </tr>
                </thead>
                <tbody>
                  {rankings.map((team) => (
                    <tr
                      key={`${team.team_name}-${team.rank}`}
                      className="border-t border-slate-700 hover:bg-slate-700/40 transition"
                    >
                      <td className="px-4 py-3 font-semibold text-white">
                        {team.rank}
                      </td>
                      <td className="px-4 py-3 text-slate-200">
                        {team.team_name}
                      </td>
                      <td className="px-4 py-3 text-right text-green-400 font-medium">
                        {team.points}
                      </td>
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