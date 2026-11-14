from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    language: Optional[str] = None
    agri_context: Optional[Dict[str, Any]] = None
    geo_context: Optional[Dict[str, Any]] = None
    historical_epoch: Optional[Dict[str, Any]] = None
    active_layers: Optional[List[str]] = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    retrieved_sources: list
    language: Optional[str] = "en"
    encoder_backend: Optional[str] = None
    reranker: Optional[str] = None
    source_provenance: Optional[List[str]] = None
    agent2_map_actions: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None
    eval_metrics: Optional[Dict[str, Any]] = None
    guardrails: Optional[Dict[str, Any]] = None
    grounding_payload: Optional[Dict[str, Any]] = None
