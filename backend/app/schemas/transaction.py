from pydantic import BaseModel
from typing import List, Optional, Any
from backend.app.schemas.risk import ReasonCode

class TransactionBase(BaseModel):
    transaction_id: str
    timestamp: str
    user_id: str
    merchant_id: str
    device_fingerprint: str
    ip_address: str
    payment_method: str
    transaction_amount: float
    currency: str
    latitude: float
    longitude: float
    transaction_status: str
    account_creation_timestamp: str
    payment_attempt_number: int
    transaction_type: str
    is_first_transaction: bool
    has_historical_amount: bool
    has_previous_location: bool
    historical_transaction_count: int
    historical_avg_amount: Optional[float]
    amount_ratio_to_history: Optional[float]
    transaction_velocity_5m: int
    transaction_velocity_1h: int
    time_since_previous_transaction: Optional[float]
    unique_devices_seen_before: int
    unique_ips_seen_before: int
    device_user_count: int
    ip_user_count: int
    failed_attempt_velocity: int
    geographic_distance_from_previous: Optional[float]
    geographic_velocity: Optional[float]
    account_age_seconds: float
    is_fraud: bool
    risk_probability: float
    risk_score: float
    decision: str

class TransactionDetail(TransactionBase):
    reasons: List[ReasonCode]

class PaginatedTransactions(BaseModel):
    items: List[TransactionBase]
    page: int
    limit: int
    total: int
    total_pages: int
