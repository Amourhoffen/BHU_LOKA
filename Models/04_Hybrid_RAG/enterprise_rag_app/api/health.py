import time
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    service: str
    target: str
    documents_indexed: int
    uptime_seconds: float

start_time = time.time()

def get_health_status(doc_count: int) -> dict:
    return {
        "status": "HEALTHY",
        "service": "BHU LOKA Enterprise Hybrid RAG",
        "target": "Patna (25.594° N, 85.137° E)",
        "documents_indexed": doc_count,
        "uptime_seconds": round(time.time() - start_time, 2)
    }

