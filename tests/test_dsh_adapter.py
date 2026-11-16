"""
Unit and Integration Tests for BHU LOKA DeepSeek Harness (dsh) Cordis Adapter
Author: Prince Kumar (IIT Patna) & Payal Priyadarshini (IIITDMJ)
"""

import sys
from pathlib import Path
import pytest

BHU_ROOT = Path(__file__).resolve().parent.parent
if str(BHU_ROOT) not in sys.path:
    sys.path.insert(0, str(BHU_ROOT))

from Pipelines.bhu_loka_dsh_adapter import (
    BhuLokaCordisPlugin,
    BhuSessionTree,
    PtcGeospatialExecutor,
    SandboxedActionGate,
    run_dsh_benchmark,
)


def test_dsh_benchmark_pass_rate():
    results = run_dsh_benchmark()
    assert results["status"] == "PASSED"
    assert results["pass_at_1_pct"] >= 90.0
    assert results["total_tests"] >= 10


def test_ptc_executor_sandbox_security():
    # Attempt prohibited subprocess execution
    forbidden_script = "import os; result = os.listdir('.')"
    res = PtcGeospatialExecutor.execute_ptc_script(forbidden_script, {})
    assert res["success"] is False
    assert "Security violation" in res["error"]

    # Safe mathematical computation
    safe_script = "result = math.sqrt(144) + context.get('elevation', 40.0)"
    res2 = PtcGeospatialExecutor.execute_ptc_script(safe_script, {"elevation": 55.2})
    assert res2["success"] is True
    assert res2["output"] == 67.2


def test_sandboxed_action_gate():
    gate = SandboxedActionGate()

    # Read-only query: immediately allowed
    allowed, prop = gate.inspect_and_gate("bhu_set_viewport", {"view_mode": "world"})
    assert allowed is True
    assert prop is None

    # Critical municipal action: gated
    allowed, prop = gate.inspect_and_gate("dispatch_relief_convoy", {"location": "Bihta Depot"})
    assert allowed is False
    assert prop is not None
    assert prop.status == "PENDING"
    assert prop.risk_level == "CRITICAL"

    # Approval with token
    approved = gate.approve_proposal(prop.proposal_id, "TOKEN_NDMA_AUTH_99")
    assert approved is True
    assert gate.active_proposals[prop.proposal_id].status == "APPROVED"


def test_session_tree_branching():
    tree = BhuSessionTree()
    tree.record_turn("Turn 1 Baseline", [], [], "Resp 1", {"year": 2026})
    tree.record_turn("Turn 2 Baseline", [], [], "Resp 2", {"year": 2026})

    # Fork branch for 2028 cloudburst simulation
    tree.fork_branch("scenario_2028_cloudburst")
    tree.record_turn("Turn 3 Cloudburst", [], [], "Resp 3 Cloudburst", {"year": 2028})

    assert len(tree.branches["main"]) == 2
    assert len(tree.branches["scenario_2028_cloudburst"]) == 3
    assert tree.active_branch == "scenario_2028_cloudburst"

    tree.switch_branch("main")
    assert len(tree.get_history()) == 2
