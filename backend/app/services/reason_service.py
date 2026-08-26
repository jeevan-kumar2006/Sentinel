from typing import List, Dict, Any
from backend.app.schemas.risk import ReasonCode
import math

def generate_reasons(features: Dict[str, Any]) -> List[ReasonCode]:
    reasons = []
    
    # Helper to safely get float values
    def get_val(key):
        v = features.get(key)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return 0.0
        return float(v)
        
    if get_val('transaction_velocity_5m') > 3:
        reasons.append(ReasonCode(code="HIGH_VELOCITY_5M", detail=f"High transaction velocity ({int(get_val('transaction_velocity_5m'))} txns in 5m)"))
    elif get_val('transaction_velocity_1h') > 10:
        reasons.append(ReasonCode(code="HIGH_VELOCITY_1H", detail=f"High transaction velocity ({int(get_val('transaction_velocity_1h'))} txns in 1h)"))
        
    if get_val('amount_ratio_to_history') > 5:
        reasons.append(ReasonCode(code="AMOUNT_ANOMALY", detail=f"Amount is {get_val('amount_ratio_to_history'):.1f}x historical average"))
        
    if get_val('device_user_count') > 3:
        reasons.append(ReasonCode(code="DEVICE_SHARING", detail=f"Device used by {int(get_val('device_user_count'))} users"))
        
    if get_val('ip_user_count') > 5:
        reasons.append(ReasonCode(code="IP_SHARING", detail=f"IP used by {int(get_val('ip_user_count'))} users"))
        
    if get_val('geographic_velocity') > 1000:
        reasons.append(ReasonCode(code="GEO_ANOMALY", detail=f"Impossible travel speed ({get_val('geographic_velocity'):.0f} km/h)"))
        
    if get_val('is_first_transaction') == 1.0 or features.get('is_first_transaction') == True:
        reasons.append(ReasonCode(code="COLD_START", detail="First transaction for this user"))
        
    if get_val('failed_attempt_velocity') > 2:
        reasons.append(ReasonCode(code="HIGH_FAILED_ATTEMPTS", detail=f"{int(get_val('failed_attempt_velocity'))} failed attempts recently"))
        
    if not reasons:
        reasons.append(ReasonCode(code="NORMAL_BEHAVIOR", detail="Transaction behavior appears normal"))
        
    return reasons
