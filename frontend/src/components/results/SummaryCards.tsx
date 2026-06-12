import React from "react";
import type { RunSummary } from "../../types";

interface SummaryCardsProps {
  summary: RunSummary;
}

interface StatCard {
  label: string;
  value: string | number;
  color: string;
  bg: string;
}

export function SummaryCards({ summary }: SummaryCardsProps) {
  const fmt = (v: string | number) =>
    typeof v === "string"
      ? new Intl.NumberFormat("en-IN", {
          style: "currency",
          currency: "INR",
          maximumFractionDigits: 0,
        }).format(parseFloat(v))
      : v.toLocaleString("en-IN");

  const cards: StatCard[] = [
    {
      label: "Total Invoices",
      value: summary.total_invoices,
      color: "text-gray-900",
      bg: "bg-gray-50",
    },
    {
      label: "Matched",
      value: summary.total_matched,
      color: "text-green-700",
      bg: "bg-green-50",
    },
    {
      label: "Missing in 2B",
      value: summary.missing_in_2b,
      color: "text-red-700",
      bg: "bg-red-50",
    },
    {
      label: "Missing in Books",
      value: summary.missing_in_books,
      color: "text-pink-700",
      bg: "bg-pink-50",
    },
    {
      label: "Tax Mismatch",
      value: summary.tax_mismatch,
      color: "text-yellow-700",
      bg: "bg-yellow-50",
    },
    {
      label: "Invoice Mismatch",
      value: summary.invoice_mismatch,
      color: "text-orange-700",
      bg: "bg-orange-50",
    },
    {
      label: "Date Mismatch",
      value: summary.date_mismatch,
      color: "text-purple-700",
      bg: "bg-purple-50",
    },
    {
      label: "Duplicates",
      value: summary.duplicates,
      color: "text-gray-700",
      bg: "bg-gray-100",
    },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div
            key={card.label}
            className={`${card.bg} rounded-lg p-4 flex flex-col gap-1`}
          >
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
              {card.label}
            </p>
            <p className={`text-2xl font-bold ${card.color}`}>
              {typeof card.value === "number" ? card.value.toLocaleString("en-IN") : card.value}
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
            ITC Available
          </p>
          <p className="text-xl font-bold text-green-700">{fmt(summary.itc_available)}</p>
        </div>
        <div className="bg-red-50 rounded-lg p-4">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
            ITC At Risk
          </p>
          <p className="text-xl font-bold text-red-700">{fmt(summary.itc_at_risk)}</p>
        </div>
      </div>
    </div>
  );
}
