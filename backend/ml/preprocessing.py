import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXCLUDE_COLS = [
    'is_fraud', 'fraud_scenario', 'transaction_id', 'timestamp', 
    'user_id', 'merchant_id', 'device_fingerprint', 'ip_address',
    'account_creation_timestamp', 'currency', 'transaction_type',
    'payment_method', 'transaction_status'
]

def get_feature_list(df: pd.DataFrame) -> list:
    features = [c for c in df.columns if c not in EXCLUDE_COLS]
    # Save features for artifact safety
    with open(ROOT / 'artifacts' / 'selected_features.json', 'w') as f:
        json.dump(features, f, indent=2)
    return features

def build_preprocessor(features: list) -> ColumnTransformer:
    # HGB handles NaNs natively, but LogReg needs imputation.
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median', fill_value=0)),
        ('scaler', StandardScaler())
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, features)
        ],
        remainder='drop'
    )
    return preprocessor