from fastapi import APIRouter
import json
from pathlib import Path
from backend.app.core.config import EVALUATION_REPORT_PATH, THRESHOLD_CONFIG_PATH
from backend.app.schemas.dashboard import SummaryResponse, EvaluationResponse, EconomicsResponse

router = APIRouter()

def load_report():
    with open(EVALUATION_REPORT_PATH, 'r') as f:
        return json.load(f)

@router.get("/dashboard/summary", response_model=SummaryResponse)
async def summary():
    report = load_report()
    test_metrics = report['test_results']['metrics']
    test_econ = report['test_results']['economics']
    routing = report['test_results']['routing']
    
    return SummaryResponse(
        total_transactions=report['dataset']['total_rows'],
        fraud_detected=test_metrics['tp'],
        precision=test_metrics['precision'],
        recall=test_metrics['recall'],
        f1_score=test_metrics['f1'],
        pr_auc=test_metrics.get('pr_auc', 0.0),
        roc_auc=test_metrics.get('roc_auc', 0.0),
        net_economic_impact_inr=test_econ['net_economic_benefit'],
        baseline_fraud_loss_inr=test_econ['baseline_fraud_loss'],
        residual_fraud_loss_inr=test_econ['residual_fraud_loss'],
        fraud_loss_prevented_inr=test_econ['fraud_loss_prevented'],
        false_positive_cost_inr=test_econ['false_positive_cost'],
        routing_counts=routing
    )

@router.get("/dashboard/evaluation", response_model=EvaluationResponse)
async def evaluation():
    return load_report()

@router.get("/dashboard/economics", response_model=EconomicsResponse)
async def economics():
    report = load_report()
    with open(THRESHOLD_CONFIG_PATH, 'r') as f:
        thresholds = json.load(f)
        
    return EconomicsResponse(
        review_threshold=thresholds['review_threshold'],
        block_threshold=thresholds['block_threshold'],
        economic_assumptions=report['economic_assumptions'],
        final_test_economic_result=report['test_results']['economics']
    )
