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
        setError(err instanceof Error ? err.message : "Unknown error");
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

      <div style={{ marginBottom: "1rem" }}>
        <label>
          Top X:{" "}
          <select
            value={topX}
            onChange={(e) => setTopX(Number(e.target.value))}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={30}>30</option>
            <option value={50}>50</option>
          </select>
        </label>

        <label style={{ marginLeft: "1rem" }}>
          <input
            type="checkbox"
            checked={vrsRanking}
            onChange={(e) => setVrsRanking(e.target.checked)}
          />{" "}
          VRS ranking
        </label>
      </div>

      {loading && <p>Loading rankings...</p>}
      {error && <p>Error: {error}</p>}

      {!loading && !error && rankings.length > 0 && (
        <>
          <p>Ranking date: {rankingDate}</p>

          <table>
            <thead>
              <tr>
                <th style={{ textAlign: "left", paddingRight: "1rem" }}>Rank</th>
                <th style={{ textAlign: "left", paddingRight: "1rem" }}>Team</th>
                <th style={{ textAlign: "left", paddingRight: "1rem" }}>Points</th>
              </tr>
            </thead>
            <tbody>
              {rankings.map((team) => (
                <tr key={`${team.team_name}-${team.rank}`}>
                  <td style={{ paddingRight: "1rem" }}>{team.rank}</td>
                  <td style={{ paddingRight: "1rem" }}>{team.team_name}</td>
                  <td style={{ paddingRight: "1rem" }}>{team.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {!loading && !error && rankings.length === 0 && <p>No rankings found.</p>}
    </div>
  );
}