from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
    transaction_count: int