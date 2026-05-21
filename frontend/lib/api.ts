export type BackendHealth = {
  status: "healthy" | "degraded" | "unhealthy" | string;
  timestamp?: string;
  service?: string;
  version?: string;
};

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status?: number };

export type Transaction = {
  id: string;
  buyer_agent_id: string;
  seller_agent_id: string;
  property_id: string;
  earnest_money: string;
  total_purchase_price: string;
  state: string;
  wallet_id?: string | null;
  initiated_at: string;
  target_closing_date: string;
  actual_closing_date?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type TransactionList = {
  transactions: Transaction[];
  total: number;
  page: number;
  page_size: number;
};

export type VerificationReport = {
  id: string;
  task_id?: string | null;
  agent_id: string;
  report_type: string;
  status: string;
  findings: Record<string, unknown>;
  documents: string[];
  submitted_at: string;
  reviewed_at?: string | null;
  reviewer_notes?: string | null;
  created_at: string;
};

export type VerificationTask = {
  id: string;
  transaction_id: string;
  verification_type: string;
  assigned_agent_id: string;
  status: string;
  deadline: string;
  payment_amount: string;
  report_id?: string | null;
  assigned_at: string;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
  report?: VerificationReport | null;
};

export type VerificationTaskList = {
  tasks: VerificationTask[];
  total: number;
};

export type Payment = {
  id: string;
  transaction_id: string;
  wallet_id: string;
  payment_type: string;
  recipient_id: string;
  amount: string;
  status: string;
  blockchain_tx_hash?: string | null;
  initiated_at: string;
  completed_at?: string | null;
  created_at: string;
};

export type PaymentList = {
  payments: Payment[];
  total: number;
};

export type BlockchainEvent = {
  id: string;
  transaction_id: string;
  event_type: string;
  event_data: Record<string, unknown>;
  blockchain_tx_hash?: string | null;
  block_number?: string | null;
  timestamp: string;
  created_at: string;
};

export type EventList = {
  events: BlockchainEvent[];
  total: number;
};

export type PropertyResult = {
  address: string;
  price: number;
  beds: number;
  baths: number;
  sqft?: number | null;
  summary: string;
  listing_url?: string | null;
  property_id: string;
};

export type SearchResponse = {
  properties: PropertyResult[];
  total_found: number;
  cached: boolean;
};

export type RiskFlag = {
  severity: string;
  category: string;
  message: string;
  details?: Record<string, unknown> | null;
};

export type RiskResponse = {
  flags: RiskFlag[];
  overall_risk: string;
  data_sources: Record<string, boolean>;
};

export type SearchPayload = {
  location: string;
  max_price?: number;
  min_price?: number;
  min_beds?: number;
  min_baths?: number;
  property_type?: string;
  user_id: string;
};

export type RiskPayload = {
  property_id: string;
  address: string;
  list_price: number;
  user_id: string;
};

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const body = (await response.json()) as { detail?: string };
        detail = body.detail ?? detail;
      } catch {
        detail = response.statusText || detail;
      }

      return { ok: false, error: detail, status: response.status };
    }

    if (response.status === 204) {
      return { ok: true, data: undefined as T };
    }

    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Network request failed",
    };
  }
}

export async function getBackendHealth(): Promise<BackendHealth | null> {
  const result = await apiFetch<BackendHealth>("/health/live");
  return result.ok ? result.data : null;
}

export async function listTransactions() {
  return apiFetch<TransactionList>("/api/escrow/transactions?page=1&page_size=20");
}

export async function getTransaction(transactionId: string) {
  return apiFetch<Transaction>(`/api/escrow/transactions/${transactionId}`);
}

export async function listVerificationTasks(transactionId: string) {
  return apiFetch<VerificationTaskList>(
    `/api/escrow/transactions/${transactionId}/verifications`,
  );
}

export async function listPayments(transactionId: string) {
  return apiFetch<PaymentList>(`/api/escrow/transactions/${transactionId}/payments`);
}

export async function listEvents(transactionId: string) {
  return apiFetch<EventList>(`/api/escrow/transactions/${transactionId}/events`);
}

export async function getDependencyHealth() {
  return apiFetch<Record<string, unknown>>("/health/dependencies");
}

export async function getReadinessHealth() {
  return apiFetch<Record<string, unknown>>("/health/ready");
}
