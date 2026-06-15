import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  getClients,
  uploadFile,
  getUploadMapping,
  saveMapping,
} from "../api/endpoints";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { FileDropzone } from "../components/upload/FileDropzone";
import { ColumnMappingModal } from "../components/upload/ColumnMappingModal";
import type { Client, Upload as UploadType, ColumnMappingDetect } from "../types";

export function Upload() {
  const [searchParams] = useSearchParams();
  const [clients, setClients] = useState<Client[]>([]);
  const [clientId, setClientId] = useState<number | "">(() => {
    const c = searchParams.get("client");
    return c ? parseInt(c) : "";
  });
  const [period, setPeriod] = useState("");
  const [prFile, setPrFile] = useState<File | null>(null);
  const [g2bFile, setG2bFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [prUpload, setPrUpload] = useState<UploadType | null>(null);
  const [g2bUpload, setG2bUpload] = useState<UploadType | null>(null);

  const [mappingData, setMappingData] = useState<ColumnMappingDetect | null>(null);
  const [mappingUploadId, setMappingUploadId] = useState<number | null>(null);
  const [showMapping, setShowMapping] = useState(false);

  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    getClients().then(setClients).catch(() => {});
  }, []);

  const handleUpload = async () => {
    if (!clientId || !period || !prFile || !g2bFile) return;

    setUploading(true);
    setStatus("Uploading purchase register...");
    try {
      const pr = await uploadFile(Number(clientId), "PURCHASE_REGISTER", period, prFile);
      setPrUpload(pr);
      setStatus("Uploading GSTR-2B...");

      const g2b = await uploadFile(Number(clientId), "GSTR2B", period, g2bFile);
      setG2bUpload(g2b);

      setStatus("Detecting column mapping for Purchase Register...");
      const prMapping = await getUploadMapping(pr.id);
      await saveMapping(pr.id, prMapping.detected);

      setStatus("Detecting column mapping for GSTR-2B...");
      const g2bMapping = await getUploadMapping(g2b.id);
      await saveMapping(g2b.id, g2bMapping.detected);

      setStatus("Files uploaded successfully!");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Upload failed";
      setStatus(`Error: ${msg}`);
    } finally {
      setUploading(false);
    }
  };

  const handleMappingSave = async (mapping: Record<string, string>) => {
    if (!mappingUploadId) return;
    await saveMapping(mappingUploadId, mapping);
    setShowMapping(false);
    setStatus("Column mapping saved.");
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Upload Files</h2>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Upload Purchase Register & GSTR-2B</h3>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Client selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Client *</label>
            <select
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={clientId}
              onChange={(e) => setClientId(e.target.value ? parseInt(e.target.value) : "")}
            >
              <option value="">Select client...</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — {c.gstin}
                </option>
              ))}
            </select>
          </div>

          {/* Period */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Period (MMYYYY) *
            </label>
            <input
              type="text"
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              placeholder="042024"
              maxLength={6}
            />
          </div>

          {/* PR upload */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Purchase Register *</p>
            <FileDropzone
              label="Upload Purchase Register (.xlsx or .csv)"
              onFile={setPrFile}
              disabled={uploading}
            />
            {prUpload && (
              <p className="text-xs text-green-600 mt-1">
                ✓ {prUpload.filename} ({prUpload.row_count} rows)
              </p>
            )}
          </div>

          {/* 2B upload */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">GSTR-2B *</p>
            <FileDropzone
              label="Upload GSTR-2B (.xlsx or .csv)"
              onFile={setG2bFile}
              disabled={uploading}
            />
            {g2bUpload && (
              <p className="text-xs text-green-600 mt-1">
                ✓ {g2bUpload.filename} ({g2bUpload.row_count} rows)
              </p>
            )}
          </div>

          {status && (
            <p
              className={`text-sm px-3 py-2 rounded ${
                status.startsWith("Error")
                  ? "bg-red-50 text-red-700"
                  : "bg-blue-50 text-blue-700"
              }`}
            >
              {status}
            </p>
          )}

          <Button
            onClick={handleUpload}
            disabled={!clientId || !period || !prFile || !g2bFile || uploading}
            loading={uploading}
            className="w-full"
          >
            Upload Files
          </Button>
        </CardContent>
      </Card>

      {mappingData && (
        <ColumnMappingModal
          open={showMapping}
          onClose={() => setShowMapping(false)}
          mapping={mappingData}
          onSave={handleMappingSave}
        />
      )}
    </div>
  );
}
