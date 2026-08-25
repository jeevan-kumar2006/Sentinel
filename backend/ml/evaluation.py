import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, average_precision_score, roc_auc_score
import joblib

from data import load_data
from preprocessing import get_feature_list, build_preprocessor
from models import RuleBaseline, train_logreg, train_hgb
from economics import EconomicModel
from thresholds import optimize_thresholds

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"
REPORTS = ROOT / "reports"

def evaluate_set(y_true, y_pred, y_prob=None):
    metrics = {
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1': f1_score(y_true, y_pred, zero_division=0),
        'tn': int(confusion_matrix(y_true, y_pred)[0][0]),
        'fp': int(confusion_matrix(y_true, y_pred)[0][1]),
        'fn': int(confusion_matrix(y_true, y_pred)[1][0]),
        'tp': int(confusion_matrix(y_true, y_pred)[1][1]),
    }
    if y_prob is not None:
        metrics['pr_auc'] = average_precision_score(y_true, y_prob)
        metrics['roc_auc'] = roc_auc_score(y_true, y_prob)
    return metrics

def run_phase2():
    ARTIFACTS.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    
    print("Loading data...")
    splits, boundaries = load_data()
    
    train_df = splits['train']
    val_df = splits['validation']
    test_df = splits['test']
    
    features = get_feature_list(train_df)
    preprocessor = build_preprocessor(features)
    
    # Fit preprocessor on TRAIN ONLY
    X_train_proc = preprocessor.fit_transform(train_df[features])
    X_val_proc = preprocessor.transform(val_df[features])
    X_test_proc = preprocessor.transform(test_df[features])
    
    joblib.dump(preprocessor, ARTIFACTS / "preprocessing.joblib")
    
    y_train = train_df['is_fraud']
    y_val = val_df['is_fraud']
    y_test = test_df['is_fraud']
    
    # 1. Rule Baseline
    print("Evaluating Rule Baseline...")
    rule_model = RuleBaseline()
    rule_probs_val = rule_model.predict_proba(val_df[features])[:, 1]
    rule_val_metrics = evaluate_set(y_val, (rule_probs_val > 0.5).astype(int), rule_probs_val)
    
    # 2. Logistic Regression
    print("Training Logistic Regression...")
    logreg = train_logreg(X_train_proc, y_train)
    logreg_probs_val = logreg.predict_proba(X_val_proc)[:, 1]
    logreg_val_metrics = evaluate_set(y_val, (logreg_probs_val > 0.5).astype(int), logreg_probs_val)
    
    # 3. HistGradientBoosting
    print("Training HistGradientBoosting...")
    hgb = train_hgb(X_train_proc, y_train)
    hgb_probs_val = hgb.predict_proba(X_val_proc)[:, 1]
    hgb_val_metrics = evaluate_set(y_val, (hgb_probs_val > 0.5).astype(int), hgb_probs_val)
    
    # Model Selection (HGB typically superior for tabular fraud)
    selected_model = hgb
    selected_probs_val = hgb_probs_val
    joblib.dump(selected_model, ARTIFACTS / "selected_model.joblib")
    
    # Economics & Threshold Optimization
    econ_model = EconomicModel()
    review_t, block_t = optimize_thresholds(y_val, selected_probs_val, econ_model)
    
    threshold_config = {"review_threshold": review_t, "block_threshold": block_t}
    with open(ARTIFACTS / "threshold_config.json", 'w') as f:
        json.dump(threshold_config, f, indent=2)
        
    # TEST EVALUATION
    print("Evaluating on TEST set...")
    test_probs = selected_model.predict_proba(X_test_proc)[:, 1]
    
    test_decisions = pd.Series('ALLOW', index=test_df.index)
    test_decisions[test_probs >= review_t] = 'REVIEW'
    test_decisions[test_probs >= block_t] = 'BLOCK'
    
    test_pred = (test_probs >= block_t).astype(int) # For standard confusion matrix
    test_metrics = evaluate_set(y_test, test_pred, test_probs)
    test_econ = econ_model.calculate_loss(test_df, test_decisions)
    
    # Scenario evaluation
    scenarios = test_df[test_df['is_fraud'] == 1]['fraud_scenario'].unique()
    scenario_results = {}
    for sc in scenarios:
        sc_mask = test_df['fraud_scenario'] == sc
        sc_y = y_test[sc_mask]
        sc_pred = test_pred[sc_mask]
        if len(sc_y) > 0:
            scenario_results[sc] = {
                'count': int(len(sc_y)),
                'recall': float(recall_score(sc_y, sc_pred, zero_division=0))
            }
            
    # Assemble Report
    report = {
        "dataset": {"total_rows": len(train_df) + len(val_df) + len(test_df), "fraud_rate": float(y_train.mean())},
        "splits": {
            "train": {"start": str(train_df.timestamp.min()), "end": str(train_df.timestamp.max()), "rows": len(train_df), "fraud_rate": float(y_train.mean())},
            "validation": {"start": str(val_df.timestamp.min()), "end": str(val_df.timestamp.max()), "rows": len(val_df), "fraud_rate": float(y_val.mean())},
            "test": {"start": str(test_df.timestamp.min()), "end": str(test_df.timestamp.max()), "rows": len(test_df), "fraud_rate": float(y_test.mean())}
        },
        "features_used": features,
        "validation_results": {
            "Rule Baseline": rule_val_metrics,
            "Logistic Regression": logreg_val_metrics,
            "HistGradientBoosting": hgb_val_metrics
        },
        "selected_thresholds": threshold_config,
        "test_results": {
            "metrics": test_metrics,
            "routing": {
                "ALLOW": int((test_decisions == 'ALLOW').sum()),
                "REVIEW": int((test_decisions == 'REVIEW').sum()),
                "BLOCK": int((test_decisions == 'BLOCK').sum())
            },
            "economics": test_econ,
            "scenario_recall": scenario_results
        },
        "economic_assumptions": {"chargeback_fee": 1500, "customer_ltv": 5000}
    }
    
    with open(REPORTS / "phase2_evaluation.json", 'w') as f:
        json.dump(report, f, indent=2, default=str)
        
    with open(REPORTS / "phase2_evaluation.md", 'w') as f:
        f.write("# Sentinel Phase 2 Evaluation Report\n\n")
        f.write("## Final Test Metrics\n")
        f.write(json.dumps(test_metrics, indent=2))
        f.write("\n\n## Test Economics\n")
        f.write(json.dumps(test_econ, indent=2))
        
    print("Phase 2 complete. Reports saved to reports/phase2_evaluation.json")

if __name__ == "__main__":
    run_phase2()