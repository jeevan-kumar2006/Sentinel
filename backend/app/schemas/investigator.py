from pydantic import BaseModel
from typing import List, Optional


class EvidenceFeatures(BaseModel):
    """Compact structured evidence features for Gemini."""
    transaction_velocity_5m: Optional[float] = None
    transaction_velocity_1h: Optional[float] = None
    historical_avg_amount: Optional[float] = None
    amount_ratio: Optional[float] = None
    device_user_count: Optional[float] = None
    ip_user_count: Optional[float] = None
    geo_velocity: Optional[float] = None
    is_first_transaction: Optional[bool] = None
    failed_attempt_velocity: Optional[float] = None


class TransactionEvidence(BaseModel):
    """Verified, compact evidence object sent to Gemini.
    
    This object contains ONLY explicitly allowlisted fields from verified
    Sentinel transaction data. It does NOT include is_fraud, fraud_scenario,
    or any hidden ground truth.
    """
    transaction_id: str
    timestamp: str
    transaction_amount: float
    risk_score: float
    risk_probability: float
    decision: str
    
    features: EvidenceFeatures
    reason_codes: List[str]  # Deterministic reason code descriptions (max 10)


class KeySignal(BaseModel):
    """A single AI-generated signal from the investigation."""
    signal: str
    evidence: str


class AIInvestigation(BaseModel):
    """Gemini-generated investigation explanation fields.
    
    This schema contains ONLY explanation fields.
    Authoritative fields (transaction_id, decision, risk_score, risk_probability)
    are added by the backend.
    """
    summary: str
    key_signals: List[KeySignal]
    explanation_confidence: str  # high, medium, low, not_available
    limitations: List[str]


class InvestigatorResponse(BaseModel):
    """Complete Investigator API response.
    
    Combines authoritative Sentinel fields with AI-generated explanation.
    The Sentinel fields can NEVER be overridden by Gemini.
    """
    transaction_id: str
    available: bool  # True if Gemini was available and generated explanation
    
    # Authoritative Sentinel fields (NOT from Gemini)
    decision: str
    risk_score: float
    risk_probability: float
    
    # AI-generated explanation fields
    summary: str
    key_signals: List[KeySignal]
    recommended_action: str  # Deterministically generated from decision
    explanation_confidence: str
    limitations: List[str]
