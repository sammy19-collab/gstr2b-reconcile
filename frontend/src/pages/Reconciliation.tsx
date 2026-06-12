import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import apiClient from "../api/client";
import { getClients, startRun } from "../api/endpoints";
import { useRun } from "../hooks/useRun";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { SummaryCards } from "../components/results/SummaryCards";
import { ResultsTable } from "../components/results/ResultsTable";
import { ItcDonut } from "../components/charts/ItcDonut";
import type { Client, Upload } from "../types";

export function Reconciliation() {
  const [searchParams] = useSearchParams();
  const [clients, setClients] = useState<Client[]>([]);
  const [clientId, setClientId] = useState<number | "">(() => {
    const c = searchParams.get("client");
    return c ? parseInt(c) : "";
  });
  const [period, setPeriod] = useState(searchParams.get("period") || "");
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [prUploadId, setPrUploadId] = useState<number | "">(
    searchParams.get("pr") ? parseInt(searchParams.get("pr")!) : ""
  );
  const [g2bUploadId, setG2bUploadId] = useState<number | "">(
    searchParams.get("g2b") ? parseInt(searchParams.get("g2b")!) : ""
  );
  const [taxTolerance, setTaxTolerance] = useState("1.00");
  const [fuzzyThreshold, setFuzzyThreshold] = useState("80");
  const [runId, setRunId] = useState<number | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  const { run } = useRun(runId);

  useEffect(() => {
    getClients().then(setClients).catch(() => {});
  }, []);

  // Load uploads when client changes
  useEffect(() => {
    if (!clientId) { setUploads([]); return; }
    apiClient.get<Upload[]>(`/uploads/?client_id=${clientId}`)
      .then(r => setUploads(r.data))
      .catch(() => setUploads([]));
  }, [clientId]);

  const prUploads = uploads.filter(u => u.upload_type === "PURCHASE_REGISTER");
  const g2bUploads = uploads.filter(u => u.upload_type === "GSTR2B");

  const handleStart = async () => {
    if (!clientId || !period || !prUploadId || !g2bUploadId) return;
    setError("");
    setStarting(true);
    try {
      const result = await startRun({
        client_id: Number(clientId),
        period,
        pr_upload_id: Number(prUploadId),
        g2b_upload_id: Number(g2bUploadId),
        tax_tolerance: parseFloat(taxTolerance),
        fuzzy_threshold: parseInt(fuzzyThreshold),
      });
      setRunId(result.id);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to start reconciliation";
      setError(msg);
    } finally {
      setStarting(false);
    }
  };

  const statusColor: Record<string, string> = {
    QUEUED: "text-gray-600",
    RUNNING: "text-blue-600",
    COMPLETED: "text-green-600",
    FAILED: "text-red-600",
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <h2 className="text-2xl font-bold text-gray-900">Reconciliation</h2>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Start Reconciliation Run</h3>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Client */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Client *</label>
              <select
                className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={clientId}
                onChange={(e) => { setClientId(e.target.value ? parseInt(e.target.value) : ""); setPrUploadId(""); setG2bUploadId(""); }}
              >
                <option value="">Select client...</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>{c.name} — {c.gstin}</option>
                ))}
              </select>
            </div>

            {/* Period */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Period (MMYYYY) *</label>
              <input
                type="text"
                className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                placeholder="042024"
                maxLength={6}
              />
            </div>

            {/* PR Upload dropdown */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Register *</label>
              <select
                className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={prUploadId}
                onChange={(e) => setPrUploadId(e.target.value ? parseInt(e.target.value) : "")}
              >
                <option value="">Select upload...</option>
                {prUploads.map((u) => (
                  <option key={u.id} value={u.id}>
                    #{u.id} — {u.filename} ({u.period})
                  </option>
                ))}
              </select>
              {clientId && prUploads.length === 0 && (
                <p className="text-xs text-gray-500 mt-1">No PR uploads found. <a href={`/upload?client=${clientId}`} className="text-blue-600 underline">Upload one</a></p>
              )}
            </div>

            {/* G2B Upload dropdown */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">GSTR-2B *</label>
              <select
                className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={g2bUploadId}
                onChange={(e) => setG2bUploadId(e.target.value ? parseInt(e.target.value) : "")}
              >
                <option value="">Select upload...</option>
                {g2bUploads.map((u) => (
                  <option key={u.id} value={u.id}>
                    #{u.id} — {u.filename} ({u.period})
                  </option>
                ))}
              </select>
              {clientId && g2bUploads.length === 0 && (
                <p className="text-xs text-gray-500 mt-1">No GSTR-2B uploads found. <a href={`/upload?client=${clientId}`} className="text-blue-600 underline">Upload one</a></p>
              )}
            </div>

            {/* Tax tolerance */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tax Tolerance (₹)</label>
              <input
                type="number" step="0.01"
                className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={taxTolerance}
                onChange={(e) => setTaxTolerance(e.target.value)}
              />
            </div>

            {/* Fuzzy threshold */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fuzzy Threshold (0-100)</label>
              <input
                type="number" min={0} max={100}
                className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={fuzzyThreshold}
                onChange={(e) => setFuzzyThreshold(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <p className="mt-4 text-sm text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>
          )}

          <div className="mt-4">
            <Button
              onClick={handleStart}
              loading={starting}
              disabled={!clientId || !period || !prUploadId || !g2bUploadId || starting}
            >
              Start Reconciliation
            </Button>
          </div>
        </CardContent>
      </Card>

      {run && (
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Run #{run.id}</span>
            <span className={`text-sm font-bold ${statusColor[run.status] ?? "text-gray-600"}`}>
              {run.status}
              {run.status === "RUNNING" && <span className="ml-2 inline-block animate-pulse">...</span>}
            </span>
          </div>

          {run.status === "COMPLETED" && run.summary && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <Card>
                    <CardHeader><h3 className="text-lg font-semibold">Summary</h3></CardHeader>
                    <CardContent><SummaryCards summary={run.summary} /></CardContent>
                  </Card>
                </div>
                <div>
                  <Card><CardContent><ItcDonut summary={run.summary} /></CardContent></Card>
                </div>
              </div>
              <Card>
                <CardHeader><h3 className="text-lg font-semibold">Results</h3></CardHeader>
                <CardContent><ResultsTable runId={run.id} /></CardContent>
              </Card>
            </>
          )}

          {run.status === "FAILED" && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              Reconciliation failed. Please check your files and try again.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
