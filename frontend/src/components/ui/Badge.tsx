import React from "react";
import type { MatchCategory } from "../../types";

const categoryColors: Record<MatchCategory | string, string> = {
  EXACT_MATCH: "bg-green-100 text-green-800",
  FUZZY_MATCH: "bg-blue-100 text-blue-800",
  TAX_MISMATCH: "bg-yellow-100 text-yellow-800",
  INVOICE_MISMATCH: "bg-orange-100 text-orange-800",
  DATE_MISMATCH: "bg-purple-100 text-purple-800",
  MISSING_IN_2B: "bg-red-100 text-red-800",
  MISSING_IN_BOOKS: "bg-pink-100 text-pink-800",
  DUPLICATE: "bg-gray-100 text-gray-800",
};

const categoryLabels: Record<string, string> = {
  EXACT_MATCH: "Exact Match",
  FUZZY_MATCH: "Fuzzy Match",
  TAX_MISMATCH: "Tax Mismatch",
  INVOICE_MISMATCH: "Invoice Mismatch",
  DATE_MISMATCH: "Date Mismatch",
  MISSING_IN_2B: "Missing in 2B",
  MISSING_IN_BOOKS: "Missing in Books",
  DUPLICATE: "Duplicate",
};

interface BadgeProps {
  category: string;
  className?: string;
}

export function Badge({ category, className = "" }: BadgeProps) {
  const colorClass = categoryColors[category] ?? "bg-gray-100 text-gray-800";
  const label = categoryLabels[category] ?? category;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass} ${className}`}
    >
      {label}
    </span>
  );
}
