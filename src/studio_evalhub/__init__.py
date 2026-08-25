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
from studio_evalhub.golden_merge import (
    CaseKey,
    GoldenSetMergeConflict,
    MergeConflict,
    case_key,
    merge_golden_sets,
    normalize_query,
)
from studio_evalhub.golden_store import (
    GoldenSetNotFound,
    GoldenSetScopeError,
    read_golden_set,
    write_golden_set,
)
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
from studio_evalhub.wilson import Z_95, WilsonInterval, wilson

__all__ = [
    "AgentAnswer",
    "AgentRunner",
    "agreement",
    "AgreementResult",
    "answer_from_trace",
    "call_key",
    "case_key",
    "CaseKey",
    "CaseRun",
    "chunks_from_trace",
    "citations_from_trace",
    "compute_scorecard",
    "ddl",
    "EvalHarness",
    "FixtureUnreadable",
    "GoldenCase",
    "GoldenSet",
    "GoldenSetMergeConflict",
    "GoldenSetNotFound",
    "GoldenSetScopeError",
    "JudgeUnavailable",
    "JudgeUnavailableReason",
    "list_runs_all_tenants",
    "LLMJudge",
    "load_golden_set",
    "merge_golden_sets",
    "MergeConflict",
    "nhan_tu_golden_set",
    "normalize_query",
    "read_golden_set",
    "read_run_unscoped",
    "RecordingLLM",
    "render_run_cases",
    "render_scorecard",
    "ReplayError",
    "ReplayLLM",
    "ReplayMiss",
    "RetrievedChunk",
    "run_cost_from_trace",
    "RunCost",
    "RunCostError",
    "score_case",
    "score_run_from_trace",
    "SmokeResult",
    "StubAgentRunner",
    "tenant_scope_ok",
    "TRACE_SOURCE_POSTGRES",
    "TraceAnswerError",
    "UnscopedReadUnavailable",
    "wilson",
    "WilsonInterval",
    "write_golden_set",
    "Z_95",
]
