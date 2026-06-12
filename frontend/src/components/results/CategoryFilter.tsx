import React from "react";
import type { MatchCategory } from "../../types";

interface CategoryFilterProps {
  selected: string | null;
  onChange: (category: string | null) => void;
}

const CATEGORIES: { value: MatchCategory; label: string; color: string }[] = [
  { value: "EXACT_MATCH", label: "Exact Match", color: "bg-green-100 text-green-800" },
  { value: "FUZZY_MATCH", label: "Fuzzy Match", color: "bg-blue-100 text-blue-800" },
  { value: "TAX_MISMATCH", label: "Tax Mismatch", color: "bg-yellow-100 text-yellow-800" },
  { value: "INVOICE_MISMATCH", label: "Invoice Mismatch", color: "bg-orange-100 text-orange-800" },
  { value: "DATE_MISMATCH", label: "Date Mismatch", color: "bg-purple-100 text-purple-800" },
  { value: "MISSING_IN_2B", label: "Missing in 2B", color: "bg-red-100 text-red-800" },
  { value: "MISSING_IN_BOOKS", label: "Missing in Books", color: "bg-pink-100 text-pink-800" },
  { value: "DUPLICATE", label: "Duplicate", color: "bg-gray-100 text-gray-800" },
];

export function CategoryFilter({ selected, onChange }: CategoryFilterProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onChange(null)}
        className={[
          "px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
          selected === null
            ? "bg-gray-800 text-white"
            : "bg-gray-100 text-gray-700 hover:bg-gray-200",
        ].join(" ")}
      >
        All
      </button>
      {CATEGORIES.map((cat) => (
        <button
          key={cat.value}
          onClick={() => onChange(selected === cat.value ? null : cat.value)}
          className={[
            "px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
            selected === cat.value ? `${cat.color} ring-2 ring-offset-1 ring-current` : cat.color,
          ].join(" ")}
        >
          {cat.label}
        </button>
      ))}
    </div>
  );
}
