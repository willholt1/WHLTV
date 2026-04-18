import React, { useState } from "react";

export interface SortableTableColumn<T> {
  key: keyof T;
  label: string;
  align?: "left" | "right";
  render?: (row: T) => React.ReactNode;
}

interface SortableTableProps<T> {
  columns: SortableTableColumn<T>[];
  data: T[];
  initialSortKey?: keyof T;
  initialSortDir?: "asc" | "desc";
  rowKey: (row: T) => string | number;
  className?: string;
}

export function SortableTable<T>({
  columns,
  data,
  initialSortKey,
  initialSortDir = "asc",
  rowKey,
  className = "",
}: SortableTableProps<T>) {
  const [sortBy, setSortBy] = useState<keyof T>(
    initialSortKey || columns[0].key,
  );
  const [sortDir, setSortDir] = useState<"asc" | "desc">(initialSortDir);

  function handleSort(col: keyof T) {
    if (sortBy === col) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortBy(col);
      setSortDir("asc");
    }
  }

  function getSortedData() {
    const sorted = [...data];
    sorted.sort((a, b) => {
      let cmp = 0;
      if (typeof a[sortBy] === "string" && typeof b[sortBy] === "string") {
        cmp = String(a[sortBy]).localeCompare(String(b[sortBy]));
      } else {
        cmp = (a[sortBy] as any) - (b[sortBy] as any);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return sorted;
  }

  return (
    <table className={`table-base ${className}`}>
      <thead className="table-header">
        <tr>
          {columns.map((col) => (
            <th
              key={String(col.key)}
              className={`table-th${col.align === "right" ? "-right" : ""} cursor-pointer select-none`}
              onClick={() => handleSort(col.key)}
            >
              {col.label}
              {sortBy === col.key && (
                <span className="ml-1">{sortDir === "asc" ? "▲" : "▼"}</span>
              )}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {getSortedData().map((row) => (
          <tr key={rowKey(row)} className="table-row">
            {columns.map((col) => (
              <td
                key={String(col.key)}
                className={`table-td${col.align === "right" ? "-right" : ""}`}
              >
                {col.render
                  ? col.render(row)
                  : (row[col.key] as React.ReactNode)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
