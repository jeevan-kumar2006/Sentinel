import json
from pathlib import Path
from typing import Tuple

import joblib
import pandas as pd


class ModelService:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.thresholds = None
        self.features = None
        self.is_loaded = False

    def load(
        self,
        model_path: Path,
        preprocessor_path: Path,
        threshold_path: Path,
        features_path: Path,
    ):
        # Load the frozen Phase 2 artifacts.
        model = joblib.load(model_path)
        preprocessor = joblib.load(preprocessor_path)

        with open(threshold_path, "r") as f:
            thresholds = json.load(f)

        with open(features_path, "r") as f:
            features = json.load(f)

        # Prevent accidental retraining.
        def frozen_fit(*args, **kwargs):
            raise RuntimeError(
                "fit() cannot be called on frozen model artifacts"
            )

        model.fit = frozen_fit
        preprocessor.fit = frozen_fit

        self.model = model
        self.preprocessor = preprocessor
        self.thresholds = thresholds
        self.features = features
        self.is_loaded = True

    def predict(
        self,
        features_df: pd.DataFrame,
    ) -> Tuple[float, float, str]:

        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        # Use exactly the selected Phase 2 features.
        X = features_df[self.features]

        # Apply the frozen preprocessing artifact.
        X_proc = self.preprocessor.transform(X)

        # Predict fraud probability.
        prob = self.model.predict_proba(X_proc)[0, 1]

        score = prob * 100

        review_threshold = self.thresholds["review_threshold"]
        block_threshold = self.thresholds["block_threshold"]

        if prob >= block_threshold:
            decision = "BLOCK"
        elif prob >= review_threshold:
            decision = "REVIEW"
        else:
            decision = "ALLOW"

        return (
            float(prob),
            float(score),
            decision,
        )


model_service = ModelService()