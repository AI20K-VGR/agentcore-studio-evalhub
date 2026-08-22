"""AgentCore Studio Evalhub — eval harness, LLM-judge, scorecard, golden-set. Owner: AIE-2.

Phase 8: `schema.ddl()` fills `eval.golden_sets`/`eval.scorecards` (P1 stub). `LLMJudge` không còn là
spec seam rỗng — điền ở D18/T2 (`kit#118`): seam `LLM` tiêm vào + cache `(case_id, actual)` + cap
≤100/ngày fail-closed + sentinel `JudgeUnavailable(reason=...)`. Xem harness.py/judge.py/compute.py
docstrings cho hợp đồng của từng seam.
"""

from studio_evalhub.agent_runner import AgentAnswer, AgentRunner, CaseRun, StubAgentRunner
from studio_evalhub.agreement import AgreementResult, agreement, nhan_tu_golden_set
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
from studio_evalhub.judge import JudgeUnavailable, JudgeUnavailableReason, LLMJudge
from studio_evalhub.render import render_run_cases, render_scorecard
from studio_evalhub.replay import (
    FixtureUnreadable,
    RecordingLLM,
    ReplayError,
    ReplayLLM,
    ReplayMiss,
    call_key,
)
from studio_evalhub.run_report import (
    TRACE_SOURCE_POSTGRES,
    RunCost,
    RunCostError,
    TraceAnswerError,
    UnscopedReadUnavailable,
    answer_from_trace,
    list_runs_all_tenants,
    read_run_unscoped,
    run_cost_from_trace,
    score_run_from_trace,
)
from studio_evalhub.schema import ddl

__all__ = [
    "TRACE_SOURCE_POSTGRES",
    "FixtureUnreadable",
    "AgentAnswer",
    "AgentRunner",
    "AgreementResult",
    "CaseRun",
    "EvalHarness",
    "GoldenCase",
    "GoldenSet",
    "JudgeUnavailable",
    "JudgeUnavailableReason",
    "LLMJudge",
    "RecordingLLM",
    "ReplayError",
    "ReplayLLM",
    "ReplayMiss",
    "RetrievedChunk",
    "RunCost",
    "RunCostError",
    "SmokeResult",
    "StubAgentRunner",
    "TraceAnswerError",
    "agreement",
    "answer_from_trace",
    "call_key",
    "chunks_from_trace",
    "citations_from_trace",
    "compute_scorecard",
    "ddl",
    "UnscopedReadUnavailable",
    "list_runs_all_tenants",
    "load_golden_set",
    "nhan_tu_golden_set",
    "read_run_unscoped",
    "render_run_cases",
    "render_scorecard",
    "run_cost_from_trace",
    "score_case",
    "score_run_from_trace",
    "tenant_scope_ok",
]
