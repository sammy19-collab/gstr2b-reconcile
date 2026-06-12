import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { RunSummary } from "../../types";

interface ItcDonutProps {
  summary: RunSummary;
}

const COLORS = ["#22c55e", "#ef4444"];

export function ItcDonut({ summary }: ItcDonutProps) {
  const available = parseFloat(summary.itc_available) || 0;
  const atRisk = parseFloat(summary.itc_at_risk) || 0;

  const data = [
    { name: "ITC Available", value: available },
    { name: "ITC At Risk", value: atRisk },
  ];

  const fmt = (v: number) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(v);

  return (
    <div className="flex flex-col items-center">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">ITC Summary</h3>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={4}
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => fmt(value)}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex gap-6 mt-2 text-sm">
        <div className="text-center">
          <p className="font-semibold text-green-600">{fmt(available)}</p>
          <p className="text-gray-500 text-xs">Available</p>
        </div>
        <div className="text-center">
          <p className="font-semibold text-red-600">{fmt(atRisk)}</p>
          <p className="text-gray-500 text-xs">At Risk</p>
        </div>
      </div>
    </div>
  );
}
