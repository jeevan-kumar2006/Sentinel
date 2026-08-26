from fastapi import APIRouter
import pandas as pd
from backend.app.schemas.risk import RiskScoreRequest, RiskScoreResponse
from backend.app.services.model_service import model_service
from backend.app.services.reason_service import generate_reasons

router = APIRouter()

@router.post("/risk/score", response_model=RiskScoreResponse)
async def score_transaction(request: RiskScoreRequest):
    data = request.dict()
    txn_id = data.pop('transaction_id', None)
    
    # Convert to DataFrame for preprocessor
    features_df = pd.DataFrame([data])
    
    prob, score, decision = model_service.predict(features_df)
    reasons = generate_reasons(data)
    
    return RiskScoreResponse(
        transaction_id=txn_id,
        risk_probability=prob,
        risk_score=score,
        decision=decision,
        reasons=reasons
    )
