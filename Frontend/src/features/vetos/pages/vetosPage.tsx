import { useEffect, useState } from "react";
import { getTeamVetoData } from "../api";
import type { VetoData } from "../types";
import { DateRangePicker } from "../../../components/DateRangePicker";
import { TeamSelect } from "../../../components/TeamSelect";

export function VetosPage() {
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);

  const [vetoData, setVetoData] = useState<VetoData[]>([]);
  const [loadingVetoData, setLoadingVetoData] = useState(false);

  // Calculate default dates: fromDate = 4 months ago, toDate = today
  function getDefaultDates() {
    const dte = new Date();
    const toDate = dte.toISOString().split("T")[0];

    dte.setMonth(dte.getMonth() - 4);
    const fromDate = dte.toISOString().split("T")[0];
    return { fromDate, toDate };
  }

  const defaults = getDefaultDates();
  const [fromDate, setFromDate] = useState<string>(defaults.fromDate);
  const [toDate, setToDate] = useState<string>(defaults.toDate);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchVetoData() {
      try {
        if (selectedTeamId === null) return;

        setLoadingVetoData(true);
        const result = await getTeamVetoData({
          from_date: new Date(fromDate),
          to_date: new Date(toDate),
          team_id: selectedTeamId,
        });

        setVetoData(result);
      } catch {
        setError("Failed to load veto data");
      } finally {
        setLoadingVetoData(false);
      }
    }

    fetchVetoData();
  }, [selectedTeamId, fromDate, toDate]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Team veto data</h1>
      <div className="filter-controls">
        {error && <p>{error}</p>}

        <div className="flex gap-4 items-end">
          <TeamSelect value={selectedTeamId} onChange={setSelectedTeamId} />
          <DateRangePicker
            from={fromDate}
            to={toDate}
            onFromChange={setFromDate}
            onToChange={setToDate}
          />
        </div>
      </div>

      {loadingVetoData && <p>Loading veto data...</p>}

      {!loadingVetoData && vetoData.length > 0 && (
        <div className="bg-slate-800 rounded-sm border border-slate-700 overflow-hidden shadow-sm">
          <div className="max-h-125 overflow-y-auto">
            <table className="table-base">
              <thead className="table-header">
                <tr>
                  <th className="table-th">Map Name</th>
                  <th className="table-th">Times Played</th>
                  <th className="table-th">Pick Total</th>
                  <th className="table-th">Ban Total</th>
                  <th className="table-th">Remaining Total</th>
                  <th className="table-th">Round Dif</th>
                  <th className="table-th">CT Round Dif</th>
                  <th className="table-th">T Round Dif</th>
                  <th className="table-th">Win %</th>
                </tr>
              </thead>

              <tbody>
                {vetoData.map((map) => (
                  <tr key={map.map_name} className="table-row">
                    <td className="table-td">{map.map_name}</td>
                    <td className="table-td">{map.times_played}</td>
                    <td className="table-td">{map.pick_total}</td>
                    <td className="table-td">{map.ban_total}</td>
                    <td className="table-td">{map.remaining_total}</td>
                    <td className="table-td">{map.round_dif}</td>
                    <td className="table-td">{map.ct_round_dif}</td>
                    <td className="table-td">{map.t_round_dif}</td>
                    <td className="table-td">
                      {(map.win_pct * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
