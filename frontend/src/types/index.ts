export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "ADMIN" | "MANAGER" | "USER";
  is_active: boolean;
  created_at: string;
}

export interface Client {
  id: number;
  name: string;
  gstin: string;
  pan?: string;
  contact_email?: string;
  contact_phone?: string;
  created_at: string;
}

export interface Upload {
  id: number;
  client_id: number;
  upload_type: "PURCHASE_REGISTER" | "GSTR2B";
  filename: string;
  file_size: number;
  row_count?: number;
  period?: string;
  status: "PENDING" | "PROCESSING" | "READY" | "FAILED";
  error_message?: string;
  created_at: string;
}

export interface ColumnMappingDetect {
  detected: Record<string, string>;
  unresolved: string[];
  sample_columns: string[];
}

export interface RunSummary {
  total_invoices: number;
  total_matched: number;
  missing_in_2b: number;
  missing_in_books: number;
  tax_mismatch: number;
  invoice_mismatch: number;
  date_mismatch: number;
  duplicates: number;
  itc_available: string;
  itc_at_risk: string;
}

export type RunStatus = "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";

export interface ReconciliationRun {
  id: number;
  status: RunStatus;
  summary?: RunSummary;
  created_at: string;
}

export type MatchCategory =
  | "EXACT_MATCH"
  | "FUZZY_MATCH"
  | "TAX_MISMATCH"
  | "INVOICE_MISMATCH"
  | "DATE_MISMATCH"
  | "MISSING_IN_2B"
  | "MISSING_IN_BOOKS"
  | "DUPLICATE";

export interface ResultRow {
  id: number;
  category: MatchCategory;
  confidence?: number;
  purchase?: Record<string, unknown>;
  gstr2b?: Record<string, unknown>;
  tax_delta?: number;
  date_delta_days?: number;
}

export interface ResultsPage {
  total: number;
  page: number;
  page_size: number;
  items: ResultRow[];
}

export interface VendorAnalytics {
  id: number;
  run_id: number;
  supplier_gstin?: string;
  supplier_name?: string;
  total_invoices: number;
  matched: number;
  missing_in_2b: number;
  missing_in_books: number;
  tax_mismatch: number;
  itc_available: string;
  itc_at_risk: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
