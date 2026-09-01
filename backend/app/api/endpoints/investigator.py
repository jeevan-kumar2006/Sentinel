"""
Investigator API endpoint.

POST /api/v1/investigator/{transaction_id}
"""
from fastapi import APIRouter, HTTPException
from backend.app.schemas.investigator import InvestigatorResponse, KeySignal
from backend.app.services.transaction_service import transaction_service
from backend.app.services.evidence_service import EvidenceBuilder
from backend.app.services.investigator_service import get_investigator_provider
from backend.app.services.reason_service import generate_reasons

router = APIRouter()


@router.post("/investigator/{transaction_id}", response_model=InvestigatorResponse)
async def investigate_transaction(transaction_id: str):
    """
    Investigate a transaction using the AI Investigator.
    """
    txn = transaction_service.get_transaction(transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    evidence = EvidenceBuilder.build_evidence(txn)
    reasons = generate_reasons(txn)
    evidence["reasons"] = reasons
    
    decision = txn.get("decision", "UNKNOWN")
    risk_score = txn.get("risk_score", 0.0)
    risk_probability = txn.get("risk_probability", 0.0)
    
    provider = get_investigator_provider()
    
    # Catch exceptions to safely return the deterministic fallback
    try:
        investigation = await provider.investigate(evidence)
    except Exception:
        investigation = None
    
    recommended_action = _get_recommended_action(decision)
    
    if investigation:
        return InvestigatorResponse(
            transaction_id=transaction_id,
            available=True,
            decision=decision,
            risk_score=risk_score,
            risk_probability=risk_probability,
            summary=investigation.summary,
            key_signals=investigation.key_signals,
            recommended_action=recommended_action,
            explanation_confidence=investigation.explanation_confidence,
            limitations=investigation.limitations
        )
    else:
        return InvestigatorResponse(
            transaction_id=transaction_id,
            available=False,
            decision=decision,
            risk_score=risk_score,
            risk_probability=risk_probability,
            summary="AI investigation is temporarily unavailable.",
            key_signals=[
                KeySignal(
                    signal=reason.detail,
                    evidence="Deterministic Sentinel reason code"
                )
                for reason in reasons
            ],
            recommended_action=recommended_action,
            explanation_confidence="not_available",
            limitations=[
                "LLM explanation unavailable. Deterministic Sentinel reason codes are shown."
            ]
        )


def _get_recommended_action(decision: str) -> str:
    """Generate deterministic recommended action from Sentinel decision."""
    decision = decision.upper().strip()
    
    if decision == "ALLOW":
        return "Allow the transaction."
    elif decision == "REVIEW":
        return "Review the transaction and supporting account activity."
    elif decision == "BLOCK":
        return "Reject the transaction according to the configured Sentinel routing policy."
    else:
        return "Process according to configured routing policy."