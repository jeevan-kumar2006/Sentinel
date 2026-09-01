from fastapi import APIRouter
from backend.app.api.endpoints import health, dashboard, transactions, risk, investigator

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(transactions.router, tags=["transactions"])
api_router.include_router(risk.router, tags=["risk"])
api_router.include_router(investigator.router, tags=["investigator"])