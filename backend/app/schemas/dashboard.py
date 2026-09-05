from pydantic import BaseModel
from typing import List, Any, Optional, Dict

class SummaryResponse(BaseModel):
    total_transactions: int
    fraud_detected: int
    precision: float
    recall: float
    f1_score: float
    pr_auc: Optional[float] = None
    roc_auc: Optional[float] = None
    net_economic_impact_inr: float
    baseline_fraud_loss_inr: float
    residual_fraud_loss_inr: float
    fraud_loss_prevented_inr: float
    false_positive_cost_inr: float
    routing_counts: Dict[str, int]

class EvaluationResponse(BaseModel):
    dataset: Dict[str, Any]
    splits: Dict[str, Any]
    features_used: List[str]
    validation_results: Dict[str, Any]
    selected_thresholds: Dict[str, Any]
    test_results: Dict[str, Any]
    economic_assumptions: Dict[str, Any]

class EconomicsResponse(BaseModel):
    review_threshold: float
    block_threshold: float
    economic_assumptions: Dict[str, Any]
    final_test_economic_result: Dict[str, Any]
    threshold_sweep: Optional[List[Dict[str, Any]]] = None