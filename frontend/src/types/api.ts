export interface HealthResponse {
  status: string;
  version: string;
  model_loaded: boolean;
  transaction_count: number;
}

export interface SummaryResponse {
  total_transactions: number;
  fraud_detected: number;
  precision: number;
  recall: number;
  f1_score: number;
  pr_auc: number | null;
  roc_auc: number | null;
  net_economic_impact_inr: number;
  baseline_fraud_loss_inr: number;
  residual_fraud_loss_inr: number;
  fraud_loss_prevented_inr: number;
  false_positive_cost_inr: number;
  routing_counts: Record<string, number>;
}

export interface EvaluationResponse {
  dataset: Record<string, any>;
  splits: Record<string, any>;
  features_used: string[];
  validation_results: Record<string, any>;
  selected_thresholds: Record<string, any>;
  test_results: {
    metrics: {
      precision: number;
      recall: number;
      f1: number;
      pr_auc?: number;
      roc_auc?: number;
      tn: number;
      fp: number;
      fn: number;
      tp: number;
    };
    routing: Record<string, number>;
    economics: Record<string, number>;
    scenario_recall: Record<string, { count: number; recall: number }>;
  };
  economic_assumptions: Record<string, any>;
}

export interface EconomicsResponse {
  review_threshold: number;
  block_threshold: number;
  economic_assumptions: Record<string, any>;
  final_test_economic_result: Record<string, number>;
}

export interface TransactionBase {
  transaction_id: string;
  timestamp: string;
  user_id: string;
  merchant_id: string;
  device_fingerprint: string;
  ip_address: string;
  payment_method: string;
  transaction_amount: number;
  currency: string;
  latitude: number;
  longitude: number;
  transaction_status: string;
  account_creation_timestamp: string;
  payment_attempt_number: number;
  transaction_type: string;
  is_first_transaction: boolean;
  has_historical_amount: boolean;
  has_previous_location: boolean;
  historical_transaction_count: number;
  historical_avg_amount: number | null;
  amount_ratio_to_history: number | null;
  transaction_velocity_5m: number;
  transaction_velocity_1h: number;
  time_since_previous_transaction: number | null;
  unique_devices_seen_before: number;
  unique_ips_seen_before: number;
  device_user_count: number;
  ip_user_count: number;
  failed_attempt_velocity: number;
  geographic_distance_from_previous: number | null;
  geographic_velocity: number | null;
  account_age_seconds: number;
  is_fraud: boolean;
  risk_probability: number;
  risk_score: number;
  decision: string;
}

export interface ReasonCode {
  code: string;
  detail: string;
}

export interface TransactionDetail extends TransactionBase {
  reasons: ReasonCode[];
}

export interface PaginatedTransactions {
  items: TransactionBase[];
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface KeySignal {
  signal: string;
  evidence: string;
}

export interface InvestigatorResponse {
  transaction_id: string;
  available: boolean;
  decision: string;
  risk_score: number;
  risk_probability: number;
  summary: string;
  key_signals: KeySignal[];
  recommended_action: string;
  explanation_confidence: string;
  limitations: string[];
}