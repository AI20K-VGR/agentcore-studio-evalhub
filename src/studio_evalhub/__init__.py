"""AgentCore Studio Evalhub — eval harness, LLM-judge, scorecard, golden-set. Owner: AIE-2.

Phase 8: `schema.ddl()` fills `eval.golden_sets`/`eval.scorecards` (P1 stub); `EvalHarness`,
`LLMJudge`, `compute_scorecard` are the empty (`NotImplementedError`) OJT spec seams AIE-2 fills
next — see harness.py/judge.py/compute.py docstrings for each seam's contract.
"""

from studio_evalhub.agent_runner import AgentAnswer, AgentRunner, CaseRun, StubAgentRunner
from studio_evalhub.compute import compute_scorecard
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.harness import EvalHarness, SmokeResult, citations_from_trace, score_case
from studio_evalhub.judge import LLMJudge

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
    "citations_from_trace",
    "compute_scorecard",
    "score_case",
]
