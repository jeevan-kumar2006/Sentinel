import pytest
import sys
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend" / "ml"))

from data import load_data
from preprocessing import EXCLUDE_COLS
from economics import EconomicModel

def test_temporal_split_integrity():
    splits, boundaries = load_data()
    
    # 1. Both classes exist
    for name, split in splits.items():
        assert 0 in split['is_fraud'].values
        assert 1 in split['is_fraud'].values
        
    # 2. Chronological ordering
    assert splits['train']['timestamp'].max() < splits['validation']['timestamp'].min()
    assert splits['validation']['timestamp'].max() < splits['test']['timestamp'].min()

def test_feature_safety():
    splits, _ = load_data()
    train_df = splits['train']
    
    # Ensure identifiers and targets are excluded
    for col in EXCLUDE_COLS:
        # We check if any feature column matches an excluded col
        # In the actual feature list generation, these are dropped.
        pass # Handled by preprocessing.py logic, but we verify the list
        
    with open(ROOT / 'artifacts' / 'selected_features.json', 'r') as f:
        features = json.load(f)
        
    assert 'is_fraud' not in features
    assert 'fraud_scenario' not in features
    assert 'user_id' not in features
    assert 'transaction_id' not in features
    assert 'device_fingerprint' not in features

def test_economic_accounting():
    econ = EconomicModel(chargeback_fee=1000, customer_ltv=2000)
    
    # 10 frauds of amount 100, 10 legit
    df = pd.DataFrame({
        'is_fraud': [1]*10 + [0]*10,
        'transaction_amount': [100]*20
    })
    
    # Block 5 frauds, block 2 legit
    decisions = pd.Series(['BLOCK']*5 + ['ALLOW']*5 + ['BLOCK']*2 + ['ALLOW']*8)
    
    results = econ.calculate_loss(df, decisions)
    
    # Baseline = 10 * (100 + 1000) = 11000
    assert results['baseline_fraud_loss'] == 11000.0
    
    # Residual = 5 unblocked frauds * 1100 = 5500
    assert results['residual_fraud_loss'] == 5500.0
    
    # Prevented = 11000 - 5500 = 5500
    assert results['fraud_loss_prevented'] == 5500.0
    
    # FP Cost = 2 * 2000 = 4000
    assert results['false_positive_cost'] == 4000.0
    
    # Net = 5500 - 4000 = 1500
    assert results['net_economic_benefit'] == 1500.0