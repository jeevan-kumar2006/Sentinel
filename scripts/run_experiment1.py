#!/usr/bin/env python3
"""
SENTINEL — EXPERIMENT 1: GENUINE ML PERFORMANCE IMPROVEMENT (Strict Isolation)
"""
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, average_precision_score, roc_auc_score

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend" / "ml"))

from data import load_data
from preprocessing import build_preprocessor
from economics import EconomicModel
from thresholds import optimize_thresholds

ROOT = Path(__file__).resolve().parents[1]
MAX_FP_BLOCK_RATE = 0.05

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

def run_experiment():
    print("=" * 70)
    print("SENTINEL EXPERIMENT 1: STRICT TEST ISOLATION")
    print("=" * 70)
    
    print("\n[1/4] Loading data and initializing preprocessing...")
    splits, boundaries = load_data()
    
    train_df = splits['train'].reset_index(drop=True)
    val_df = splits['validation'].reset_index(drop=True)
    
    # READ features from artifact to avoid overwriting production config
    with open(ROOT / "artifacts" / "selected_features.json") as f:
        base_features = json.load(f)
        
    preprocessor = build_preprocessor(base_features)
    
    X_train = preprocessor.fit_transform(train_df[base_features])
    X_val = preprocessor.transform(val_df[base_features])
    
    y_train = train_df['is_fraud']
    y_val = val_df['is_fraud']
    
    econ_model = EconomicModel()
    
    # 2. Candidate Experimentation (VAL ONLY)
    print("\n[2/4] Training candidates (VALIDATION ONLY)...")
    hgb_configs = [
        {"name": "Baseline", "max_iter": 200, "learning_rate": 0.1, "max_depth": 8, "l2_regularization": 1.0, "random_state": 42},
        {"name": "Cand 1 (Deep)", "max_iter": 300, "learning_rate": 0.05, "max_depth": 10, "l2_regularization": 1.0, "random_state": 42},
        {"name": "Cand 2 (Leaves)", "max_iter": 250, "learning_rate": 0.1, "max_leaf_nodes": 63, "max_depth": None, "l2_regularization": 2.0, "random_state": 42},
        {"name": "Cand 3 (Conservative)", "max_iter": 150, "learning_rate": 0.1, "max_depth": 5, "l2_regularization": 1.0, "random_state": 42},
        {"name": "Cand 4 (Fast Learning)", "max_iter": 100, "learning_rate": 0.2, "max_depth": 6, "l2_regularization": 0.5, "random_state": 42},
    ]
    
    results = []
    
    for cfg in hgb_configs:
        model = HistGradientBoostingClassifier(**{k:v for k,v in cfg.items() if k != "name"})
        model.fit(X_train, y_train)
        
        probs_val = model.predict_proba(X_val)[:, 1]
        r_t, b_t = optimize_thresholds(val_df, probs_val, econ_model, max_fp_block_rate=MAX_FP_BLOCK_RATE)
        
        val_pred = (probs_val >= b_t).astype(int)
        val_metrics = evaluate_set(y_val, val_pred, probs_val)
        
        val_decisions = pd.Series('ALLOW', index=range(len(val_df)))
        val_decisions[probs_val >= r_t] = 'REVIEW'
        val_decisions[probs_val >= b_t] = 'BLOCK'
        val_econ = econ_model.calculate_loss(val_df, val_decisions)
        
        results.append({
            "config_name": cfg['name'],
            "block_t": b_t,
            "review_t": r_t,
            "val_f1": val_metrics['f1'],
            "val_pr_auc": val_metrics['pr_auc'],
            "val_econ": val_econ['net_economic_benefit'],
            "model": model,
            "preprocessor": preprocessor
        })
        print(f"  {cfg['name']:<25} | Val F1: {val_metrics['f1']:.4f} | Val PR-AUC: {val_metrics['pr_auc']:.4f}")

    # 3. Candidate Selection
    print("\n[3/4] Selecting best candidate (F1 -> PR-AUC)...")
    baseline_result = next(r for r in results if r['config_name'] == 'Baseline')
    best_candidate = baseline_result
    
    for res in results:
        if res['val_f1'] > best_candidate['val_f1']:
            best_candidate = res
        elif res['val_f1'] == best_candidate['val_f1'] and res['val_pr_auc'] > best_candidate['val_pr_auc']:
            best_candidate = res
            
    print(f"  Selected: {best_candidate['config_name']}")
    print("  Candidate frozen. Proceeding to final TEST evaluation.")

    # 4. Final TEST Evaluation (Single Pass)
    print("\n[4/4] Final Held-Out TEST Evaluation...")
    print("-" * 70)
    
    test_df = splits['test'].reset_index(drop=True)
    y_test = test_df['is_fraud']
    
    # Baseline eval (Frozen)
    with open(ROOT / "artifacts" / "threshold_config.json") as f:
        frozen_thresh = json.load(f)
        
    X_test_base = baseline_result['preprocessor'].transform(test_df[base_features])
    test_probs_base = baseline_result['model'].predict_proba(X_test_base)[:, 1]
    test_pred_base = (test_probs_base >= frozen_thresh['block_threshold']).astype(int)
    base_metrics = evaluate_set(y_test, test_pred_base, test_probs_base)
    
    base_decisions = pd.Series('ALLOW', index=range(len(test_df)))
    base_decisions[test_probs_base >= frozen_thresh['review_threshold']] = 'REVIEW'
    base_decisions[test_probs_base >= frozen_thresh['block_threshold']] = 'BLOCK'
    base_econ = econ_model.calculate_loss(test_df, base_decisions)
    
    # Candidate eval (Selected thresholds)
    X_test_cand = best_candidate['preprocessor'].transform(test_df[base_features])
    test_probs_cand = best_candidate['model'].predict_proba(X_test_cand)[:, 1]
    test_pred_cand = (test_probs_cand >= best_candidate['block_t']).astype(int)
    cand_metrics = evaluate_set(y_test, test_pred_cand, test_probs_cand)
    
    cand_decisions = pd.Series('ALLOW', index=range(len(test_df)))
    cand_decisions[test_probs_cand >= best_candidate['review_t']] = 'REVIEW'
    cand_decisions[test_probs_cand >= best_candidate['block_t']] = 'BLOCK'
    cand_econ = econ_model.calculate_loss(test_df, cand_decisions)
    
    print(f"{'Metric':<15} | {'Baseline':<15} | {'Candidate':<15}")
    print("-" * 50)
    for m in ['precision', 'recall', 'f1', 'pr_auc', 'roc_auc', 'tp', 'tn', 'fp', 'fn']:
        b_val = base_metrics[m]
        c_val = cand_metrics[m]
        fmt = ".4f" if m in ['precision', 'recall', 'f1', 'pr_auc', 'roc_auc'] else "d"
        print(f"{m.upper():<15} | {b_val:<15{fmt}} | {c_val:<15{fmt}}")
        
    print(f"{'NET BENEFIT':<15} | {base_econ['net_economic_benefit']:<15.2f} | {cand_econ['net_economic_benefit']:<15.2f}")
    print("-" * 50)
    
    # Determine outcome
    improved = False
    if cand_metrics['f1'] > base_metrics['f1']:
        improved = True
    elif cand_metrics['f1'] == base_metrics['f1'] and cand_metrics['pr_auc'] > base_metrics['pr_auc']:
        improved = True
        
    if best_candidate['config_name'] != 'Baseline' and improved:
        print("\nOUTCOME A — GENUINE IMPROVEMENT")
    else:
        print("\nOUTCOME B — NO GENUINE IMPROVEMENT")
        print("Experiment rejected; production baseline retained.")

if __name__ == "__main__":
    run_experiment()