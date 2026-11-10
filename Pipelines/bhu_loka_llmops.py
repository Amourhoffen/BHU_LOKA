"""
BHU LOKA LLMOps & LangSmith Observability Engine
Tracks evaluation metrics, latency, token usage, guardrail verdicts, and traces.
Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "Data" / "08_Processed_Outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
TRACES_JSONL_PATH = OUTPUTS_DIR / "llmops_eval_traces.jsonl"

# Check LangSmith availability
HAS_LANGSMITH = False
try:
    import langsmith
    from langsmith import Client as LangSmithClient
    HAS_LANGSMITH = True
except ImportError:
    pass


class BhuLokaLLMOps:
    """
    LLMOps Controller providing continuous evaluation, telemetry logging,
    and optional LangSmith / Langfuse cloud synchronization.
    """

    _IN_MEMORY_TRACES: List[Dict[str, Any]] = []

    @classmethod
    def log_evaluation_trace(
        cls,
        query: str,
        answer: str,
        retrieved_sources: List[Dict[str, Any]],
        faithfulness: float,
        answer_relevance: float,
        context_precision: float,
        guardrail_passed: bool,
        latency_ms: float,
        user_language: str = "en",
        encoder_backend: str = "MiniLM-384d"
    ) -> Dict[str, Any]:
        """
        Record a complete evaluation trace into persistent storage and LangSmith.
        """
        trace_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()

        trace_record = {
            "trace_id": trace_id,
            "timestamp_utc": now_utc,
            "query": query,
            "answer_preview": answer[:180] + ("..." if len(answer) > 180 else ""),
            "retrieved_count": len(retrieved_sources),
            "retrieved_titles": [s.get("title") for s in retrieved_sources],
            "metrics": {
                "faithfulness": round(faithfulness, 3),
                "answer_relevance": round(answer_relevance, 3),
                "context_precision": round(context_precision, 3),
                "context_groundedness_pct": round(faithfulness * 100.0, 1),
                "agent_self_ratio_pct": round((1.0 - faithfulness) * 100.0, 1)
            },
            "guardrails": {
                "passed": guardrail_passed,
                "status": "APPROVED" if guardrail_passed else "FLAGGED"
            },
            "system": {
                "latency_ms": round(latency_ms, 1),
                "user_language": user_language,
                "encoder_backend": encoder_backend,
                "langsmith_active": bool(HAS_LANGSMITH and os.environ.get("LANGCHAIN_API_KEY"))
            }
        }

        # 1. Append to in-memory ring buffer
        cls._IN_MEMORY_TRACES.append(trace_record)
        if len(cls._IN_MEMORY_TRACES) > 500:
            cls._IN_MEMORY_TRACES.pop(0)

        # 2. Append to persistent JSONL on disk
        try:
            with open(TRACES_JSONL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace_record, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[LLMOps] Failed to write trace to disk: {e}")

        # 3. Stream to LangSmith if API Key is configured
        if HAS_LANGSMITH and os.environ.get("LANGCHAIN_API_KEY"):
            try:
                client = LangSmithClient()
                client.create_run(
                    name="bhu_loka_rag_evaluation",
                    run_type="chain",
                    inputs={"query": query},
                    outputs={"answer": answer, "metrics": trace_record["metrics"]},
                    extra={"metadata": trace_record["system"]},
                    project_name=os.environ.get("LANGCHAIN_PROJECT", "bhu-loka-geospatial-rag")
                )
            except Exception as ls_err:
                # Never crash if LangSmith network fails
                pass

        return trace_record

    @classmethod
    def get_cumulative_metrics(cls) -> Dict[str, Any]:
        """
        Compute real-time aggregate LLMOps statistics across all recorded runs.
        """
        # Load from disk if in-memory is empty
        records = list(cls._IN_MEMORY_TRACES)
        if not records and TRACES_JSONL_PATH.exists():
            try:
                with open(TRACES_JSONL_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            records.append(json.loads(line))
            except Exception:
                pass

        if not records:
            return {
                "total_evaluations": 0,
                "mean_faithfulness": 0.0,
                "mean_answer_relevance": 0.0,
                "mean_context_precision": 0.0,
                "hallucination_rate_pct": 0.0,
                "guardrail_pass_rate_pct": 100.0,
                "avg_latency_ms": 0.0,
                "langsmith_installed": HAS_LANGSMITH
            }

        total = len(records)
        faith_vals = [r["metrics"]["faithfulness"] for r in records if "metrics" in r]
        rel_vals = [r["metrics"]["answer_relevance"] for r in records if "metrics" in r]
        prec_vals = [r["metrics"]["context_precision"] for r in records if "metrics" in r]
        lat_vals = [r["system"]["latency_ms"] for r in records if "system" in r]
        guard_passed = sum(1 for r in records if r.get("guardrails", {}).get("passed", False))
        hallucinations = sum(1 for f in faith_vals if f < 0.70)

        return {
            "total_evaluations": total,
            "mean_faithfulness": round(sum(faith_vals) / max(1, len(faith_vals)), 3),
            "mean_answer_relevance": round(sum(rel_vals) / max(1, len(rel_vals)), 3),
            "mean_context_precision": round(sum(prec_vals) / max(1, len(prec_vals)), 3),
            "hallucination_rate_pct": round((hallucinations / total) * 100.0, 1),
            "guardrail_pass_rate_pct": round((guard_passed / total) * 100.0, 1),
            "avg_latency_ms": round(sum(lat_vals) / max(1, len(lat_vals)), 1),
            "langsmith_installed": HAS_LANGSMITH
        }

