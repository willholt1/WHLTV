import { useEffect, useState } from "react";
import { getTeamVetoData } from "../api";
import type { VetoData } from "../types";
import { DateRangePicker } from "../../../components/DateRangePicker";
import { TeamSelect } from "../../../components/TeamSelect";
import { SortableTable } from "../../../components/SortableTable";
import type { SortableTableColumn } from "../../../components/SortableTable";

export function VetosPage() {
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);

  const [vetoData, setVetoData] = useState<VetoData[]>([]);
  const [loadingVetoData, setLoadingVetoData] = useState(false);

  // Define columns for the sortable table
  const vetoColumns: SortableTableColumn<VetoData>[] = [
    { key: "map_name", label: "Map Name" },
    { key: "times_played", label: "Times Played" },
    { key: "pick_total", label: "Pick Total" },
    { key: "ban_total", label: "Ban Total" },
    { key: "remaining_total", label: "Remaining Total" },
    {
      key: "round_dif",
      label: "Round Dif",
      render: (row) => (
        <span
          className={
            row.round_dif > 0
              ? "text-green-400"
              : row.round_dif < 0
                ? "text-red-400"
                : undefined
          }
        >
          {row.round_dif}
        </span>
      ),
    },
    {
      key: "ct_round_dif",
      label: "CT Round Dif",
      render: (row) => (
        <span
          className={
            row.ct_round_dif > 0
              ? "text-green-400"
              : row.ct_round_dif < 0
                ? "text-red-400"
                : undefined
          }
        >
          {row.ct_round_dif}
        </span>
      ),
    },
    {
      key: "t_round_dif",
      label: "T Round Dif",
      render: (row) => (
        <span
          className={
            row.t_round_dif > 0
              ? "text-green-400"
              : row.t_round_dif < 0
                ? "text-red-400"
                : undefined
          }
        >
          {row.t_round_dif}
        </span>
      ),
    },
    {
      key: "win_pct",
      label: "Win %",
      render: (row) => `${(row.win_pct * 100).toFixed(2)}%`,
    },
  ];

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
            <SortableTable
              columns={vetoColumns}
              data={vetoData}
              rowKey={(row) => row.map_name}
              initialSortKey="map_name"
            />
          </div>
        </div>
      )}
    </div>
  );
}
