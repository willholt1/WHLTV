import React from "react";

interface DateRangePickerProps {
  from: string;
  to: string;
  onFromChange: (value: string) => void;
  onToChange: (value: string) => void;
  min?: string;
  max?: string;
  className?: string;
}

export function DateRangePicker({
  from,
  to,
  onFromChange,
  onToChange,
  min,
  max,
  className = "",
}: DateRangePickerProps) {
  return (
    <div className={`flex gap-4 ${className}`}>
      <label className="filter-label">
        From:
        <input
          type="date"
          value={from}
          min={min}
          max={max}
          onChange={(e) => onFromChange(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 hover:border-slate-500 transition"
        />
      </label>
      <label className="filter-label">
        To:
        <input
          type="date"
          value={to}
          min={min}
          max={max}
          onChange={(e) => onToChange(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 hover:border-slate-500 transition"
        />
      </label>
    </div>
  );
}
