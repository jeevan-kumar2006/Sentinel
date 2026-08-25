import numpy as np
import pandas as pd
from typing import Tuple


def optimize_thresholds(
    val_df: pd.DataFrame,
    probs: np.ndarray,
    econ_model,
    max_fp_block_rate: float = 0.05
) -> Tuple[float, float]:
    """
    Optimize REVIEW and BLOCK thresholds using validation data.

    The max_fp_block_rate constraint is a Sentinel synthetic benchmark
    assumption. It is NOT a Razorpay requirement or policy.
    """

    if not 0.0 <= max_fp_block_rate <= 1.0:
        raise ValueError(
            "max_fp_block_rate must be between 0 and 1."
        )

    best_benefit = -float('inf')
    best_review = 0.5
    best_block = 0.8

    y_val = val_df['is_fraud'].reset_index(drop=True)
    amounts = val_df['transaction_amount'].reset_index(drop=True)

    probs = np.asarray(probs)

    if len(val_df) != len(probs):
        raise ValueError(
            "Validation data and probabilities must have the same length: "
            f"{len(val_df)} != {len(probs)}"
        )

    # Cleaner deterministic threshold grids.
    review_thresholds = np.linspace(0.20, 0.80, 13)
    block_thresholds = np.linspace(0.50, 0.90, 9)

    # Sentinel synthetic benchmark assumption:
    # legitimate transactions blocked by the policy must remain
    # at or below max_fp_block_rate.
    for block_t in block_thresholds:
        for review_t in review_thresholds:

            if review_t >= block_t:
                continue

            decisions = pd.Series(
                'ALLOW',
                index=range(len(probs))
            )

            decisions[probs >= review_t] = 'REVIEW'
            decisions[probs >= block_t] = 'BLOCK'

            # Use real validation data for economic calculation.
            econ_df = pd.DataFrame({
                'is_fraud': y_val,
                'transaction_amount': amounts
            })

            econ = econ_model.calculate_loss(
                econ_df,
                decisions
            )

            # False-positive BLOCK rate among legitimate transactions.
            legitimate = econ_df['is_fraud'] == 0

            false_positive_blocks = (
                legitimate & (decisions == 'BLOCK')
            )

            legitimate_count = legitimate.sum()

            if legitimate_count == 0:
                continue

            fp_rate = (
                false_positive_blocks.sum()
                / legitimate_count
            )

            if (
                econ['net_economic_benefit'] > best_benefit
                and fp_rate <= max_fp_block_rate
            ):
                best_benefit = econ['net_economic_benefit']
                best_review = float(review_t)
                best_block = float(block_t)

    return best_review, best_block