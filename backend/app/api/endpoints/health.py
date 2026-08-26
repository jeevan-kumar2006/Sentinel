from fastapi import APIRouter
from backend.app.schemas.health import HealthResponse
from backend.app.services.transaction_service import transaction_service
from backend.app.services.model_service import model_service

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model_loaded=model_service.is_loaded,
        transaction_count=len(transaction_service.df) if transaction_service.df is not None else 0
    )