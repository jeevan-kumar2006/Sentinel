import numpy as np
import pandas as pd
from typing import Tuple
from sklearn.metrics import precision_score, recall_score, f1_score

def optimize_thresholds(y_val: pd.Series, probs: np.ndarray, econ_model) -> Tuple[float, float]:
    best_benefit = -float('inf')
    best_review = 0.5
    best_block = 0.8
    
    # Grid search block and review thresholds
    for block_t in np.arange(0.50, 0.95, 0.05):
        for review_t in np.arange(0.20, block_t, 0.05):
            decisions = pd.Series('ALLOW', index=range(len(probs)))
            decisions[probs >= review_t] = 'REVIEW'
            decisions[probs >= block_t] = 'BLOCK'
            
            # Dummy df for econ calculation
            dummy_df = pd.DataFrame({'is_fraud': y_true.values})
            econ = econ_model.calculate_loss(dummy_df, decisions)
            
            # Constraint: FP block rate < 5%
            fp_rate = (dummy_df['is_fraud'] == 0) & (decisions == 'BLOCK').sum() / (dummy_df['is_fraud'] == 0).sum()
            
            if econ['net_economic_benefit'] > best_benefit and fp_rate < 0.05:
                best_benefit = econ['net_economic_benefit']
                best_review = review_t
                best_block = block_t
                
    return best_review, best_block