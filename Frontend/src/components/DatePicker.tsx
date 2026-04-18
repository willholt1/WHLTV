import React from "react";

interface DatePickerProps {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  min?: string;
  max?: string;
  className?: string;
}

export function DatePicker({
  label,
  value,
  onChange,
  min,
  max,
  className = "",
}: DatePickerProps) {
  return (
    <label className={`filter-label ${className}`}>
      {label && <span className="block mb-1">{label}</span>}
      <input
        type="date"
        value={value}
        min={min}
        max={max}
        onChange={(e) => onChange(e.target.value)}
        className="bg-slate-800 border border-slate-700 text-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 hover:border-slate-500 transition"
      />
    </label>
  );
}
