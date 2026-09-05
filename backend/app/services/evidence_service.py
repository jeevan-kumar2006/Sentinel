"""
Evidence builder for AI Investigator.
Constructs deterministic, compact evidence objects from trusted Sentinel
transaction data. NEVER includes hidden labels or benchmark information.
"""
from typing import Any, Dict, Optional, List
import math


class EvidenceBuilder:
    @staticmethod
    def build_evidence(transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Strict allowlist-based evidence extraction."""
        evidence = {
            "transaction_id": transaction.get("transaction_id"),
            "timestamp": transaction.get("timestamp"),
            "transaction_amount": EvidenceBuilder._safe_float(transaction.get("transaction_amount")),
            "risk_score": EvidenceBuilder._safe_float(transaction.get("risk_score")),
            "risk_probability": EvidenceBuilder._safe_float(transaction.get("risk_probability")),
            "decision": transaction.get("decision"),
        }

        features = {}

        velocity_5m = EvidenceBuilder._safe_int(transaction.get("transaction_velocity_5m"))
        if velocity_5m is not None: features["transaction_velocity_5m"] = velocity_5m

        velocity_1h = EvidenceBuilder._safe_int(transaction.get("transaction_velocity_1h"))
        if velocity_1h is not None: features["transaction_velocity_1h"] = velocity_1h

        hist_avg = EvidenceBuilder._safe_float(transaction.get("historical_avg_amount"))
        if hist_avg is not None: features["historical_avg_amount"] = hist_avg

        amount_ratio = EvidenceBuilder._safe_float(transaction.get("amount_ratio_to_history"))
        if amount_ratio is not None: features["amount_ratio_to_history"] = amount_ratio

        device_count = EvidenceBuilder._safe_int(transaction.get("device_user_count"))
        if device_count is not None: features["device_user_count"] = device_count

        ip_count = EvidenceBuilder._safe_int(transaction.get("ip_user_count"))
        if ip_count is not None: features["ip_user_count"] = ip_count
        geo_velocity = EvidenceBuilder._safe_float(transaction.get("geographic_velocity"))
        if geo_velocity is not None: features["geo_velocity"] = geo_velocity

        failed_attempts = EvidenceBuilder._safe_int(transaction.get("failed_attempt_velocity"))
        if failed_attempts is not None: features["failed_attempt_velocity"] = failed_attempts

        # FIX: Include account_age_seconds as it is a critical risk-driving feature
        account_age = EvidenceBuilder._safe_float(transaction.get("account_age_seconds"))
        if account_age is not None: features["account_age_seconds"] = account_age

        is_first = transaction.get("is_first_transaction")
        if is_first is not None: features["is_first_transaction"] = bool(is_first)

        evidence["features"] = features

        reason_codes: List[str] = []
        if "reasons" in transaction and isinstance(transaction["reasons"], list):
            for reason in transaction["reasons"][:10]:
                if isinstance(reason, dict) and "detail" in reason:
                    reason_codes.append(str(reason["detail"]))
                elif hasattr(reason, "detail"):
                    reason_codes.append(str(reason.detail))

        evidence["reason_codes"] = reason_codes
        return evidence

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None: return None
        try:
            f = float(value)
            if math.isnan(f): return None
            return f
        except (ValueError, TypeError): return None

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        if value is None: return None
        try: return int(value)
        except (ValueError, TypeError): return None
