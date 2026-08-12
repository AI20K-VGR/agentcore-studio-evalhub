"""AgentCore Studio Evalhub — eval harness, LLM-judge, scorecard, golden-set. Owner: AIE-2.

Phase 8: `schema.ddl()` fills `eval.golden_sets`/`eval.scorecards` (P1 stub). `LLMJudge` không còn là
spec seam rỗng — điền ở D18/T2 (`kit#118`): seam `LLM` tiêm vào + cache `(case_id, actual)` + cap
≤100/ngày fail-closed + sentinel `JudgeUnavailable(reason=...)`. Xem harness.py/judge.py/compute.py
docstrings cho hợp đồng của từng seam.
"""

from studio_evalhub.agent_runner import AgentAnswer, AgentRunner, CaseRun, StubAgentRunner
from studio_evalhub.compute import compute_scorecard
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.golden_loader import load_golden_set
from studio_evalhub.harness import (
    EvalHarness,
    RetrievedChunk,
    SmokeResult,
    chunks_from_trace,
    citations_from_trace,
    score_case,
    tenant_scope_ok,
)
from studio_evalhub.judge import LLMJudge
from studio_evalhub.render import render_scorecard

__all__ = [
    "AgentAnswer",
    "AgentRunner",
    "CaseRun",
    "EvalHarness",
    "GoldenCase",
    "GoldenSet",
    "LLMJudge",
    "SmokeResult",
    "StubAgentRunner",
    "RetrievedChunk",
    "chunks_from_trace",
    "citations_from_trace",
    "compute_scorecard",
    "load_golden_set",
    "render_scorecard",
    "score_case",
    "tenant_scope_ok",
]
