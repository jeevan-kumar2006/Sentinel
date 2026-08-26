from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from .model_service import model_service


class TransactionService:
    def __init__(self):
        self.df = None

    def load(self, features_path: Path):
        if not model_service.is_loaded:
            raise RuntimeError(
                "Model service must be loaded before transaction service"
            )

        self.df = pd.read_csv(features_path)

        # Convert timestamps to JSON-safe ISO strings.
        if "timestamp" in self.df.columns:
            self.df["timestamp"] = (
                pd.to_datetime(
                    self.df["timestamp"],
                    format="ISO8601",
                ).dt.strftime("%Y-%m-%dT%H:%M:%S")
            )

        if "account_creation_timestamp" in self.df.columns:
            self.df["account_creation_timestamp"] = (
                pd.to_datetime(
                    self.df["account_creation_timestamp"],
                    format="ISO8601",
                ).dt.strftime("%Y-%m-%dT%H:%M:%S")
            )

        # Use exactly the selected Phase 2 features.
        X = self.df[model_service.features]

        # Apply frozen preprocessing.
        X_proc = model_service.preprocessor.transform(X)

        # Generate fraud probabilities.
        probs = model_service.model.predict_proba(X_proc)[:, 1]

        self.df["risk_probability"] = probs
        self.df["risk_score"] = probs * 100

        review_threshold = model_service.thresholds[
            "review_threshold"
        ]

        block_threshold = model_service.thresholds[
            "block_threshold"
        ]

        decisions = []

        for probability in probs:
            if probability >= block_threshold:
                decisions.append("BLOCK")
            elif probability >= review_threshold:
                decisions.append("REVIEW")
            else:
                decisions.append("ALLOW")

        self.df["decision"] = decisions

        # Make NaN values JSON-safe.
        self.df = self.df.replace({np.nan: None})

    def get_transactions(
        self,
        page: int,
        limit: int,
        risk_decision: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:

        if self.df is None:
            raise RuntimeError(
                "Transaction service has not been loaded"
            )

        df = self.df

        if risk_decision:
            df = df[df["decision"] == risk_decision]

        if search:
            mask = (
                df["transaction_id"].str.contains(
                    search,
                    case=False,
                    na=False,
                )
                |
                df["user_id"].str.contains(
                    search,
                    case=False,
                    na=False,
                )
            )

            df = df[mask]

        total = len(df)

        start = (page - 1) * limit
        end = start + limit

        items = df.iloc[start:end].to_dict(
            orient="records"
        )

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (
                (total + limit - 1) // limit
                if limit > 0
                else 0
            ),
        }

    def get_transaction(
        self,
        transaction_id: str,
    ) -> Optional[Dict[str, Any]]:

        if self.df is None:
            raise RuntimeError(
                "Transaction service has not been loaded"
            )

        row = self.df[
            self.df["transaction_id"] == transaction_id
        ]

        if len(row) == 0:
            return None

        return row.iloc[0].to_dict()


transaction_service = TransactionService()