import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier

class RuleBaseline:
    def __init__(self):
        self.rules = [
            lambda df: df['transaction_velocity_5m'] > 3,
            lambda df: df['amount_ratio_to_history'].fillna(0) > 5,
            lambda df: df['device_user_count'] > 3,
            lambda df: df['ip_user_count'] > 5,
            lambda df: df['geographic_velocity'].fillna(0) > 1000
        ]
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = np.zeros(len(X))
        for rule in self.rules:
            preds = np.logical_or(preds, rule(X))
        # Return as 2D array [prob_0, prob_1]
        return np.column_stack([1 - preds, preds])

def train_logreg(X_train, y_train):
    model = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    model.fit(X_train, y_train)
    return model

def train_hgb(X_train, y_train):
    model = HistGradientBoostingClassifier(
        max_iter=200, 
        learning_rate=0.1,
        max_depth=8,
        l2_regularization=1.0,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model