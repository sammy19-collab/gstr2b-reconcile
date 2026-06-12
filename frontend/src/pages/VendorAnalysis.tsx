import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { getRunVendors } from "../api/endpoints";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Table, Thead, Tbody, Tr, Th, Td } from "../components/ui/Table";
import { VendorBar } from "../components/charts/VendorBar";
import type { VendorAnalytics } from "../types";

export function VendorAnalysis() {
  const [searchParams] = useSearchParams();
  const runId = searchParams.get("run") ? parseInt(searchParams.get("run")!) : null;
  const [runIdInput, setRunIdInput] = useState(runId ? String(runId) : "");
  const [vendors, setVendors] = useState<VendorAnalytics[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadVendors = async (id: number) => {
    setLoading(true);
    setError("");
    try {
      const data = await getRunVendors(id);
      setVendors(data);
    } catch {
      setError("Failed to load vendor analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (runId) loadVendors(runId);
  }, [runId]);

  const fmt = (v: string | number) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(parseFloat(String(v)));

  const sorted = [...vendors].sort(
    (a, b) => parseFloat(b.itc_at_risk) - parseFloat(a.itc_at_risk)
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Vendor Analysis</h2>

      <div className="flex gap-3 items-end">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Run ID</label>
          <input
            type="number"
            className="rounded-md border border-gray-300 px-3 py-2 text-sm w-32"
            value={runIdInput}
            onChange={(e) => setRunIdInput(e.target.value)}
          />
        </div>
        <button
          onClick={() => runIdInput && loadVendors(parseInt(runIdInput))}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
        >
          Load
        </button>
      </div>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>
      )}

      {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}

      {!loading && vendors.length > 0 && (
        <>
          <Card>
            <CardContent>
              <VendorBar vendors={vendors} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">
                Vendor Risk Table ({sorted.length} vendors)
              </h3>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <Thead>
                  <Tr>
                    <Th>Supplier</Th>
                    <Th>GSTIN</Th>
                    <Th>Total</Th>
                    <Th>Matched</Th>
                    <Th>Missing 2B</Th>
                    <Th>Missing Books</Th>
                    <Th>Tax Mis.</Th>
                    <Th>ITC Available</Th>
                    <Th>ITC At Risk</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {sorted.map((v) => (
                    <Tr key={v.id}>
                      <Td className="font-medium max-w-xs truncate">{v.supplier_name || "—"}</Td>
                      <Td className="font-mono text-xs">{v.supplier_gstin || "—"}</Td>
                      <Td>{v.total_invoices}</Td>
                      <Td className="text-green-700">{v.matched}</Td>
                      <Td className="text-red-700">{v.missing_in_2b}</Td>
                      <Td className="text-pink-700">{v.missing_in_books}</Td>
                      <Td className="text-yellow-700">{v.tax_mismatch}</Td>
                      <Td className="text-green-700">{fmt(v.itc_available)}</Td>
                      <Td className="text-red-700 font-medium">{fmt(v.itc_at_risk)}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
