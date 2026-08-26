from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import (
    FEATURES_PATH,
    MODEL_PATH,
    PREPROCESSOR_PATH,
    THRESHOLD_CONFIG_PATH,
    SELECTED_FEATURES_PATH,
)
from backend.app.services.model_service import model_service
from backend.app.services.transaction_service import transaction_service
from backend.app.api.router import api_router

app = FastAPI(title="Sentinel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Load model artifacts
    model_service.load(
        model_path=MODEL_PATH,
        preprocessor_path=PREPROCESSOR_PATH,
        threshold_path=THRESHOLD_CONFIG_PATH,
        features_path=SELECTED_FEATURES_PATH
    )
    
    # Load transactions and precompute scores
    transaction_service.load(features_path=FEATURES_PATH)

app.include_router(api_router, prefix="/api/v1")