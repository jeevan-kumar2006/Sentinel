from pydantic import BaseModel
from typing import List, Optional


class KeySignal(BaseModel):
    """A single risk signal extracted from evidence."""
    signal: str
    evidence: str


class AIInvestigation(BaseModel):
    """
    AI-generated explanation fields ONLY.
    Authoritative fields (transaction_id, decision, risk_score, risk_probability)
    are added by the backend after validation.
    """
    summary: str
    key_signals: List[KeySignal]
    explanation_confidence: str  # "high", "medium", "low", "not_available"
    limitations: List[str]


class InvestigatorResponse(BaseModel):
    """
    Complete investigator response.
    Combines authoritative Sentinel fields with AI-generated explanation.
    """
    transaction_id: str
    available: bool
    decision: str
    risk_score: float
    risk_probability: float
    summary: str
    key_signals: List[KeySignal]
    recommended_action: str
    explanation_confidence: str
    limitations: List[str]
