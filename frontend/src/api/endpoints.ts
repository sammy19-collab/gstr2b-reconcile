import apiClient from "./client";
import type {
  Client,
  Upload,
  ColumnMappingDetect,
  ReconciliationRun,
  ResultsPage,
  VendorAnalytics,
  TokenResponse,
} from "../types";

// ============================================================
// Auth
// ============================================================

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>("/auth/login", { email, password });
  return res.data;
}

export async function register(
  email: string,
  password: string,
  full_name: string
): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>("/auth/register", {
    email,
    password,
    full_name,
  });
  return res.data;
}

export async function refreshToken(refresh_token: string): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>("/auth/refresh", { refresh_token });
  return res.data;
}

// ============================================================
// Clients
// ============================================================

export async function getClients(): Promise<Client[]> {
  const res = await apiClient.get<Client[]>("/clients/");
  return res.data;
}

export async function createClient(data: {
  name: string;
  gstin: string;
  pan?: string;
  contact_email?: string;
  contact_phone?: string;
}): Promise<Client> {
  const res = await apiClient.post<Client>("/clients/", data);
  return res.data;
}

export async function deleteClient(clientId: number): Promise<void> {
  await apiClient.delete(`/clients/${clientId}`);
}

// ============================================================
// Uploads
// ============================================================

export async function uploadFile(
  clientId: number,
  uploadType: string,
  period: string,
  file: File,
  onProgress?: (pct: number) => void
): Promise<Upload> {
  const form = new FormData();
  form.append("client_id", String(clientId));
  form.append("upload_type", uploadType);
  form.append("period", period);
  form.append("file", file);

  const res = await apiClient.post<Upload>("/uploads/", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (evt.total && onProgress) {
        onProgress(Math.round((evt.loaded / evt.total) * 100));
      }
    },
  });
  return res.data;
}

export async function getUploadMapping(uploadId: number): Promise<ColumnMappingDetect> {
  const res = await apiClient.get<ColumnMappingDetect>(`/uploads/${uploadId}/mapping`);
  return res.data;
}

export async function saveMapping(
  uploadId: number,
  mapping: Record<string, string>
): Promise<void> {
  await apiClient.post(`/uploads/${uploadId}/mapping`, { mapping });
}

// ============================================================
// Reconciliation
// ============================================================

export async function startRun(params: {
  client_id: number;
  period: string;
  pr_upload_id: number;
  g2b_upload_id: number;
  tax_tolerance?: number;
  fuzzy_threshold?: number;
}): Promise<ReconciliationRun> {
  const res = await apiClient.post<ReconciliationRun>("/reconcile/run", params);
  return res.data;
}

export async function getRun(runId: number): Promise<ReconciliationRun> {
  const res = await apiClient.get<ReconciliationRun>(`/reconcile/${runId}`);
  return res.data;
}

export async function getRunResults(
  runId: number,
  page: number = 1,
  pageSize: number = 50,
  category?: string
): Promise<ResultsPage> {
  const params: Record<string, unknown> = { page, page_size: pageSize };
  if (category) params.category = category;
  const res = await apiClient.get<ResultsPage>(`/reconcile/${runId}/results`, { params });
  return res.data;
}

export async function getRunVendors(runId: number): Promise<VendorAnalytics[]> {
  const res = await apiClient.get<VendorAnalytics[]>(`/reconcile/${runId}/vendors`);
  return res.data;
}

// ============================================================
// Reports
// ============================================================

export async function downloadReport(runId: number): Promise<Blob> {
  const res = await apiClient.get(`/reports/${runId}/excel`, {
    responseType: "blob",
  });
  return res.data;
}
