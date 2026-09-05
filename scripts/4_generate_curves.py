#!/usr/bin/env python3
"""
Generates evaluation curves (PR, ROC) and validation threshold sweep
using the frozen model and updates the evaluation report.
Does NOT retrain the model or alter TEST metrics.
"""
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import precision_recall_curve, roc_curve, precision_score, recall_score, f1_score, confusion_matrix
import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend" / "ml"))

from data import load_data
from economics import EconomicModel

def generate_curves():
    print("Loading data and frozen model...")
    splits, _ = load_data()
    val_df = splits['validation']
    test_df = splits['test']
    
    with open(ROOT / "artifacts" / "selected_features.json") as f:
        features = json.load(f)
        
    preprocessor = joblib.load(ROOT / "artifacts" / "preprocessing.joblib")
    model = joblib.load(ROOT / "artifacts" / "selected_model.joblib")
    
    X_val = preprocessor.transform(val_df[features])
    X_test = preprocessor.transform(test_df[features])
    
    probs_val = model.predict_proba(X_val)[:, 1]
    probs_test = model.predict_proba(X_test)[:, 1]
    
    y_val = val_df['is_fraud']
    y_test = test_df['is_fraud']
    
    print("Generating TEST PR/ROC curves...")
    precision, recall, _ = precision_recall_curve(y_test, probs_test)
    pr_curve = [{"precision": float(p), "recall": float(r)} for p, r in zip(precision, recall)]
    
    fpr, tpr, _ = roc_curve(y_test, probs_test)
    roc_curve_data = [{"fpr": float(f), "tpr": float(t)} for f, t in zip(fpr, tpr)]
    
    print("Generating VALIDATION threshold sweep...")
    econ_model = EconomicModel()
    
    with open(ROOT / "artifacts" / "threshold_config.json") as f:
        frozen_thresh = json.load(f)
    review_t = frozen_thresh["review_threshold"]
    
    threshold_sweep = []
    for t in np.linspace(0.05, 0.95, 20):
        val_pred = (probs_val >= t).astype(int)

        val_decisions = pd.Series('ALLOW', index=val_df.index)
        val_decisions[probs_val >= review_t] = 'REVIEW'
        val_decisions[probs_val >= t] = 'BLOCK'

        val_econ = econ_model.calculate_loss(val_df, val_decisions)

        tn, fp, fn, tp = confusion_matrix(y_val, val_pred).ravel()

        routing_counts = val_decisions.value_counts()
        precision_value = precision_score(y_val, val_pred, zero_division=0)
        recall_value = recall_score(y_val, val_pred, zero_division=0)
        f1_value = f1_score(y_val, val_pred, zero_division=0)

        threshold_sweep.append({
            "threshold": float(t),

            # Existing flat fields retained for frontend compatibility.
            "precision": float(precision_value),
            "recall": float(recall_value),
            "f1": float(f1_value),
            "tp": int(tp),
            "fp": int(fp),
            "fn": int(fn),
            "tn": int(tn),
            "net_economic_benefit": float(
                val_econ['net_economic_benefit']
            ),

            # Explicit audit information.
            "routing": {
                "allow": int(routing_counts.get("ALLOW", 0)),
                "review": int(routing_counts.get("REVIEW", 0)),
                "block": int(routing_counts.get("BLOCK", 0))
            },
            "classification": {
                "basis": "BLOCK vs NOT-BLOCK",
                "precision": float(precision_value),
                "recall": float(recall_value),
                "f1": float(f1_value),
                "tp": int(tp),
                "fp": int(fp),
                "fn": int(fn),
                "tn": int(tn)
            },
            "economics": {
                "baseline_fraud_loss": float(
                    val_econ['baseline_fraud_loss']
                ),
                "residual_fraud_loss": float(
                    val_econ['residual_fraud_loss']
                ),
                "fraud_loss_prevented": float(
                    val_econ['fraud_loss_prevented']
                ),
                "false_positive_cost": float(
                    val_econ['false_positive_cost']
                ),
                "net_economic_benefit": float(
                    val_econ['net_economic_benefit']
                )
            }
        })
        
    report_path = ROOT / "reports" / "phase2_evaluation.json"
    with open(report_path, 'r') as f:
        report = json.load(f)
        
    report['test_results']['pr_curve'] = pr_curve
    report['test_results']['roc_curve'] = roc_curve_data
    report['validation_results']['threshold_sweep'] = threshold_sweep
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
        
    print("Curves generated and saved to phase2_evaluation.json")

if __name__ == "__main__":
    generate_curves()