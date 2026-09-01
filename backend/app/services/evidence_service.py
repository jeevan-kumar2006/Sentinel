"""
Evidence builder for AI Investigator.

Constructs deterministic, compact evidence objects from trusted Sentinel
transaction data. NEVER includes hidden labels or benchmark information.
"""
from typing import Any, Dict, Optional, List
import math


class EvidenceBuilder:
    """
    Builds compact evidence for the AI Investigator.
    
    NEVER includes:
    - is_fraud
    - fraud_scenario
    - train/validation/test membership
    - ground truth labels
    """
    
    @staticmethod
    def build_evidence(transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build deterministic evidence from transaction data.
        
        Args:
            transaction: Transaction dictionary from transaction_service
            
        Returns:
            Compact evidence dictionary for Gemini
        """
        # Extract core authoritative fields
        evidence = {
            "transaction_id": transaction.get("transaction_id"),
            "timestamp": transaction.get("timestamp"),
            "transaction_amount": EvidenceBuilder._safe_float(
                transaction.get("transaction_amount")
            ),
            "risk_score": EvidenceBuilder._safe_float(
                transaction.get("risk_score")
            ),
            "risk_probability": EvidenceBuilder._safe_float(
                transaction.get("risk_probability")
            ),
            "decision": transaction.get("decision"),
        }
        
        # Build features dictionary with only approved fields
        features = {}
        
        # Velocity features
        velocity_5m = EvidenceBuilder._safe_int(
            transaction.get("transaction_velocity_5m")
        )
        if velocity_5m is not None:
            features["transaction_velocity_5m"] = velocity_5m
            
        velocity_1h = EvidenceBuilder._safe_int(
            transaction.get("transaction_velocity_1h")
        )
        if velocity_1h is not None:
            features["transaction_velocity_1h"] = velocity_1h
        
        # Amount features
        hist_avg = EvidenceBuilder._safe_float(
            transaction.get("historical_avg_amount")
        )
        if hist_avg is not None:
            features["historical_avg_amount"] = hist_avg
            
        amount_ratio = EvidenceBuilder._safe_float(
            transaction.get("amount_ratio_to_history")
        )
        if amount_ratio is not None:
            features["amount_ratio"] = amount_ratio
        
        # Device/IP sharing
        device_count = EvidenceBuilder._safe_int(
            transaction.get("device_user_count")
        )
        if device_count is not None:
            features["device_user_count"] = device_count
            
        ip_count = EvidenceBuilder._safe_int(
            transaction.get("ip_user_count")
        )
        if ip_count is not None:
            features["ip_user_count"] = ip_count
        
        # Geographic velocity
        geo_velocity = EvidenceBuilder._safe_float(
            transaction.get("geographic_velocity")
        )
        if geo_velocity is not None:
            features["geo_velocity"] = geo_velocity
        
        # Failed attempts
        failed_attempts = EvidenceBuilder._safe_int(
            transaction.get("failed_attempt_velocity")
        )
        if failed_attempts is not None:
            features["failed_attempt_velocity"] = failed_attempts
        
        # First transaction flag
        is_first = transaction.get("is_first_transaction")
        if is_first is not None:
            features["is_first_transaction"] = bool(is_first)
        
        evidence["features"] = features
        
        # Add deterministic reason codes (from the transaction reasons)
        reason_codes: List[str] = []
        if "reasons" in transaction and isinstance(transaction["reasons"], list):
            for reason in transaction["reasons"][:10]:  # Max 10 items
                if isinstance(reason, dict) and "detail" in reason:
                    reason_codes.append(reason["detail"])
                elif hasattr(reason, "detail"):
                    reason_codes.append(reason.detail)
        
        evidence["reason_codes"] = reason_codes
        
        return evidence
    
    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert value to float, handling NaN and None."""
        if value is None:
            return None
        try:
            f = float(value)
            if math.isnan(f):
                return None
            return f
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        """Safely convert value to int, handling None."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
