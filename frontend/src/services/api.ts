import { HealthResponse, SummaryResponse, EvaluationResponse, EconomicsResponse, PaginatedTransactions, TransactionDetail } from '../types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, options);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const getHealth = () => fetchAPI<HealthResponse>('/health');
export const getDashboardSummary = () => fetchAPI<SummaryResponse>('/dashboard/summary');
export const getEvaluation = () => fetchAPI<EvaluationResponse>('/dashboard/evaluation');
export const getEconomics = () => fetchAPI<EconomicsResponse>('/dashboard/economics');

export const getTransactions = (params: { page: number; limit: number; risk_decision?: string; search?: string }, signal?: AbortSignal) => {
  const query = new URLSearchParams();
  query.append('page', String(params.page));
  query.append('limit', String(params.limit));
  if (params.risk_decision) query.append('risk_decision', params.risk_decision);
  if (params.search) query.append('search', params.search);
  
  return fetchAPI<PaginatedTransactions>(`/transactions?${query.toString()}`, { signal });
};

export const getTransaction = (id: string) => fetchAPI<TransactionDetail>(`/transactions/${id}`);