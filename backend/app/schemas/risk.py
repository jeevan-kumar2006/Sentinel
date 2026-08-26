import json
from pathlib import Path
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, create_model


ROOT = Path(__file__).resolve().parents[3]
FEATURES_PATH = ROOT / "artifacts" / "selected_features.json"

with open(FEATURES_PATH, "r") as f:
    features = json.load(f)


class ReasonCode(BaseModel):
    code: str
    detail: str


class RiskScoreResponse(BaseModel):
    transaction_id: Optional[str] = None
    risk_probability: float
    risk_score: float
    decision: str
    reasons: List[ReasonCode]


# Dynamically create the request schema from the frozen
# Phase 2 selected_features.json.
#
# Features are required, but we don't force them to float because
# the selected feature set may contain different numeric-compatible
# Python values such as int, float, or bool.
fields = {
    "transaction_id": (Optional[str], None)
}

for feat in features:
    fields[feat] = (Any, ...)


RiskScoreRequest = create_model(
    "RiskScoreRequest",
    __config__=ConfigDict(extra="forbid"),
    **fields,
)