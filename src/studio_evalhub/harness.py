"""Eval-harness seam — spec AIE-2 (R-SPEC A7).

Runs the 30-case golden set (produced by DE's doc-factory, consumed here — AIE-2 does NOT
generate golden sets) through an agent recipe's DAG (executed by AIE-1's interpreter, consumed
here — AIE-2 does NOT own the interpreter), scores each case (subjective cases via `judge.py`,
exact-match cases directly), then hands the per-case results to `compute.py` to aggregate into a
`Scorecard` (P2 contract). P9's SWE-owned publish/rollback pipeline is the consumer of the
resulting `Scorecard.gate.verdict` — this module produces the verdict, never wires the gate
itself (R-SPEC A4 ownership fence).

`EvalHarness.run()` (đích cuối `-> Scorecard`) vẫn `NotImplementedError`: nó cần `compute_scorecard`
(Day 4–5) và nguồn golden-set thật (Q5, `docs/scorecard-v0.md`). Building-block skeleton D3 nằm ở
`run_smoke()` + `score_case()` bên dưới — chạy case qua seam `AgentRunner`, chấm 2 nhánh, trả
`SmokeResult` (kiểu nội bộ, chưa lên `CaseResult` vì Q1 chưa chốt).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict
from studio_contracts import Scorecard

from studio_evalhub.agent_runner import AgentAnswer, AgentRunner
from studio_evalhub.golden_case import GoldenCase, GoldenSet


class SmokeResult(BaseModel):
    """Kết quả chấm một case ở tầng skeleton — output của `score_case`/`run_smoke`.

    Cố ý KHÔNG phải `studio_contracts.CaseResult`: `CaseResult.judge` là trường bắt buộc, còn
    smoke-case toàn exact-match/refusal nên không có judge (Q1, `docs/scorecard-v0.md`). Điền một
    `Judge` hằng số là thứ `judge.py` cấm; sửa contract cho `judge` optional cần mentor-approval —
    cả hai để D11. Đến lúc đó, `SmokeResult` là kiểu riêng của quadrant (như `RunResult` của engine),
    đổi shape không cần mini-RFC.
    """

    model_config = ConfigDict(frozen=True)

    case_id: str
    expected: str
    actual: str
    success: bool
    citation_accuracy: float


def _citation_tenant(chunk_id: str) -> str | None:
    """Tenant của chunk suy từ tiền tố id (định dạng DE `ankor-leave-001#c1` → `ankor`).

    Trả `None` khi id không đúng dạng (thiếu dấu `-` hoặc tiền tố rỗng) — nhánh từ-chối coi
    None là fail-closed (không parse được ⇒ không chứng minh được là an toàn)."""
    prefix, sep, _rest = chunk_id.partition("-")
    if not sep or not prefix:
        return None
    return prefix


def _tokenize(text: str) -> list[str]:
    r"""Tách `text` thành token cho so token-contains: lowercase + cắt theo `\w+` (unicode — chữ có
    dấu tiếng Việt và chữ số giữ nguyên thành một token). So theo token nguyên vẹn nên `"1 ngày"`
    KHÔNG khớp `"11 ngày"` (token `"11"` ≠ `"1"`) như substring thô sẽ mắc."""
    return re.findall(r"\w+", text.lower())


def _contains_phrase(answer_text: str, expected_phrase: str) -> bool:
    """True khi token của `expected_phrase` xuất hiện LIÊN TIẾP trong token của `answer_text`.

    Luật nhánh trả-lời-được (`docs/scorecard-v0.md` §2.3): `answer` CHỨA cụm `expected` là đúng, không
    bắt khớp cả câu / đúng chính tả / dấu câu. So token (không substring thô) để `"1 ngày"` không lọt
    vào `"11 ngày"`, mà `"1 ngày/tuần"`, `"...1 ngày."`, đầu/cuối câu vẫn khớp.

    Fail-closed: `expected_phrase` token hoá ra rỗng ⇒ False (không coi "cụm rỗng" là luôn khớp)."""
    expected_tokens = _tokenize(expected_phrase)
    if not expected_tokens:
        return False
    answer_tokens = _tokenize(answer_text)
    n = len(expected_tokens)
    return any(
        answer_tokens[i : i + n] == expected_tokens for i in range(len(answer_tokens) - n + 1)
    )


def score_case(case: GoldenCase, answer: AgentAnswer) -> SmokeResult:
    """Chấm một case theo luật v0 (`docs/scorecard-v0.md` §2.3), rẽ nhánh qua
    `GoldenCase.expects_refusal` (xét cả T1 chéo-tenant lẫn T6 chéo-vai):

    - **trả-lời-được**: `success` khi agent KHÔNG từ chối VÀ `answer` CHỨA cụm `expected`
      (`_contains_phrase` — so token liên tiếp, không bắt khớp cả câu/chính tả); `citation_accuracy`
      = tỉ lệ `expected_citation` xuất hiện trong `citations` (rỗng ⇒ 1.0, không yêu cầu trích). Giới
      hạn: token-contains không bắt phủ định/ngữ cảnh ("không ... 1 ngày" vẫn khớp) — chỉ judge (S3).
    - **từ-chối**: **fail-closed** — `success` chỉ khi cả ba: agent thực sự từ chối (`refused`), mọi
      citation parse được tenant, và không citation nào thuộc `expected_tenant`. Vi phạm bất kỳ điều
      nào ⇒ fail. `citation_accuracy` = 1.0 (Q2 chưa chốt — chỉ để hiển thị skeleton).
    """
    if not case.expects_refusal:
        success = (answer.refused is False) and _contains_phrase(answer.answer, case.expected)
        if case.expected_citation:
            hit = sum(1 for c in case.expected_citation if c in answer.citations)
            citation_accuracy = hit / len(case.expected_citation)
        else:
            citation_accuracy = 1.0
    else:
        all_parseable = all(_citation_tenant(c) is not None for c in answer.citations)
        no_leak = all(_citation_tenant(c) != case.expected_tenant for c in answer.citations)
        success = (answer.refused is True) and all_parseable and no_leak
        citation_accuracy = 1.0

    return SmokeResult(
        case_id=case.case_id,
        expected=case.expected,
        actual=answer.answer,
        success=success,
        citation_accuracy=citation_accuracy,
    )


class EvalHarness:
    """Runs the golden-set eval loop for one agent recipe.

    Contract (fill at implementation time):
    - `run()` fetches the 30 cases for `golden_set_ref` from `eval.golden_sets` (schema.py),
      executes each case's input through the agent's recipe DAG, and collects a `CaseResult`
      per case (P2 `studio_contracts.CaseResult` — success/citation_accuracy/judge fields).
    - Subjective cases (no exact string match) delegate scoring to `judge.py`'s `LLMJudge`;
      exact-match cases score directly, and are also the descope-guard fallback (INV-7) when the
      judge's daily cap is hit.
    - The collected results are handed to `compute.compute_scorecard()` to produce the final
      `Scorecard`, including `gate.verdict` (PASS|FAIL) against the recipe's `ScorecardThreshold`.
    """

    async def run(self, agent_id: str, golden_set_ref: str) -> Scorecard:
        """Run every case in `golden_set_ref` against `agent_id`'s recipe and return the
        resulting `Scorecard`. Spec AIE-2 — not yet implemented.

        Skeleton D3 nằm ở `run_smoke()`: bản `-> Scorecard` này còn chờ `compute_scorecard`
        (Day 4–5) và nguồn golden-set thật (Q5), nên vẫn raise `NotImplementedError`."""
        raise NotImplementedError("EvalHarness.run — spec AIE-2, not yet implemented")

    async def run_smoke(
        self,
        agent_id: str,
        golden_set: GoldenSet,
        runner: AgentRunner,
    ) -> list[SmokeResult]:
        """Phác skeleton smoke-eval (D3, issue #14): duyệt `golden_set.cases`, chạy mỗi case qua
        `runner` (seam `AgentRunner`), chấm bằng `score_case`, trả danh sách `SmokeResult`.

        Nhận `golden_set` in-memory + `runner` tiêm vào (chưa đọc từ DB, chưa gọi interpreter thật):
        đây là chỗ nối sẽ thay stub bằng adapter engine của AIE-1 (D4–6). KHÔNG dựng `Scorecard`
        (cần `compute_scorecard`, Day 4–5)."""
        return [
            score_case(
                case,
                await runner.run_case(
                    agent_id=agent_id,
                    query=case.query,
                    tenant=case.tenant,
                    section_roles=case.section_roles,
                ),
            )
            for case in golden_set.cases
        ]
