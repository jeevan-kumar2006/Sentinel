import pandas as pd

class EconomicModel:
    def __init__(self, chargeback_fee=1500.0, customer_ltv=5000.0):
        self.chargeback_fee = chargeback_fee
        self.customer_ltv = customer_ltv
        
    def calculate_loss(self, df: pd.DataFrame, decisions: pd.Series) -> dict:
        # Decisions: 'ALLOW', 'REVIEW', 'BLOCK'
        y_true = df['is_fraud']
        amounts = df['transaction_amount']
        
        # Baseline: all fraud is allowed
        baseline_mask = y_true == 1
        baseline_loss = (amounts[baseline_mask] + self.chargeback_fee).sum()
        
        # Residual: fraud NOT blocked (Allowed or Reviewed)
        # Conservative: Only BLOCK counts as prevention
        residual_mask = (y_true == 1) & (decisions != 'BLOCK')
        residual_loss = (amounts[residual_mask] + self.chargeback_fee).sum()
        
        # FP Cost: Legit Blocked
        fp_mask = (y_true == 0) & (decisions == 'BLOCK')
        fp_cost = self.customer_ltv * fp_mask.sum()
        
        prevented = baseline_loss - residual_loss
        net_benefit = prevented - fp_cost
        
        return {
            'baseline_fraud_loss': float(baseline_loss),
            'residual_fraud_loss': float(residual_loss),
            'fraud_loss_prevented': float(prevented),
            'false_positive_cost': float(fp_cost),
            'net_economic_benefit': float(net_benefit)
        }