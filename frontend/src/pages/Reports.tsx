import React, { useState } from "react";
import { downloadReport } from "../api/endpoints";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";

export function Reports() {
  const [runIdInput, setRunIdInput] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleDownload = async () => {
    const runId = parseInt(runIdInput);
    if (!runId) return;

    setDownloading(true);
    setError("");
    setSuccess("");

    try {
      const blob = await downloadReport(runId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `reconciliation_run_${runId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setSuccess(`Report for Run #${runId} downloaded successfully.`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to download report";
      setError(msg);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Reports</h2>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Download Excel Report</h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-gray-600">
            Download a comprehensive multi-sheet Excel report for a completed reconciliation run.
            The report includes: Summary, Exact Matches, Missing in 2B, Missing in Books,
            Tax Mismatches, Invoice Mismatches, and Vendor Summary.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reconciliation Run ID
            </label>
            <input
              type="number"
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={runIdInput}
              onChange={(e) => setRunIdInput(e.target.value)}
              placeholder="Enter run ID..."
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>
          )}
          {success && (
            <p className="text-sm text-green-700 bg-green-50 rounded px-3 py-2">{success}</p>
          )}

          <Button
            onClick={handleDownload}
            loading={downloading}
            disabled={!runIdInput || downloading}
          >
            Download Excel Report
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
