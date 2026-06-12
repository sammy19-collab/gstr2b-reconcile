import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { VendorAnalytics } from "../../types";

interface VendorBarProps {
  vendors: VendorAnalytics[];
  topN?: number;
}

export function VendorBar({ vendors, topN = 10 }: VendorBarProps) {
  const sorted = [...vendors]
    .sort((a, b) => parseFloat(b.itc_at_risk) - parseFloat(a.itc_at_risk))
    .slice(0, topN);

  const data = sorted.map((v) => ({
    name: v.supplier_name || v.supplier_gstin || "Unknown",
    itcAtRisk: parseFloat(v.itc_at_risk) || 0,
    itcAvailable: parseFloat(v.itc_available) || 0,
  }));

  const fmt = (v: number) =>
    new Intl.NumberFormat("en-IN", {
      maximumFractionDigits: 0,
    }).format(v);

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Top Vendors by ITC at Risk
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ left: 20, right: 20, top: 5, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11 }}
            angle={-30}
            textAnchor="end"
            interval={0}
          />
          <YAxis tickFormatter={fmt} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v: number) => `₹${fmt(v)}`} />
          <Legend />
          <Bar dataKey="itcAtRisk" name="ITC At Risk" fill="#ef4444" radius={[4, 4, 0, 0]} />
          <Bar dataKey="itcAvailable" name="ITC Available" fill="#22c55e" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
