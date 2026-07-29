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
from collections.abc import Mapping
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from studio_contracts import Scorecard, TraceEvent

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


def citations_from_trace(events: list[TraceEvent]) -> list[str]:
    """Tập chunk **quan sát được** của một run: gom `.citations` từ **mọi** trace event có
    (bỏ `None`), **không phụ thuộc `node_type`** (D5 #24 — chấm điểm theo trace, mặt quan sát thật).

    **API công khai từ D7** (trước là `_retrieved_citations`). Lý do đổi: nó là *phép đo* mà mọi
    consumer của scorecard cần — `apps/studio` dùng ở cả script e2e lẫn test chấm-từ-Postgres, và
    `scripts/smoke_eval_d6.py` ở repo cha import nó **xuyên repo**. Một hàm có người ngoài quadrant
    phụ thuộc thì không còn là chi tiết nội bộ; giữ dấu gạch dưới chỉ khiến người dùng phải phá
    quy ước để làm việc đúng. Alias `_retrieved_citations` giữ lại ở cuối module nên không consumer
    nào vỡ khi đổi.

    Vì sao tên là `citations_from_trace` chứ không phải `retrieved_citations`: `score_case` đã có
    **tham số** tên `retrieved_citations`, và 14 call-site truyền nó bằng keyword nên tên tham số
    không đổi được. Đặt hàm cùng tên sẽ che tham số trong thân `score_case` — ai sau này gọi
    `retrieved_citations(events)` ở đó sẽ gặp `list is not callable`. Tên hiện tại nói đúng việc
    (trích citation TỪ trace) và không đụng gì.

    Node nào mang citations là do engine quyết: thực tế (interpreter AIE-1, branch day5) nâng
    citations từ output **`llm-step`** lên trace event của node đó (chunk agent thực sự trích —
    grounded ∩ retrieved); event `kb-retrieve` để `citations=None` (output là list, không có key).
    Contract lại chú thích `TraceEvent.citations  # from kb-retrieve`. Vì thế gom **node-agnostic** để
    robust với cả hai (đã xác nhận qua thread-check franken-workspace 2026-07-24); v0 smoke chỉ một
    node mang citations nên không trộn retrieved/cited. Chốt carrier chính xác với AIE-1 → siết theo
    node cụ thể nếu cần. Đây là nguồn cho citation-accuracy (nhánh trả-lời-được) và leak-check (nhánh
    từ-chối), thay cho `AgentAnswer.citations` mà agent tự khai."""
    retrieved: list[str] = []
    for event in events:
        if event.citations is not None:
            retrieved.extend(event.citations)
    return retrieved


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


def score_case(
    case: GoldenCase, answer: AgentAnswer, retrieved_citations: list[str]
) -> SmokeResult:
    """Chấm một case theo luật v0 (`docs/scorecard-v0.md` §2.3), rẽ nhánh qua
    `GoldenCase.expects_refusal` (xét cả T1 chéo-tenant lẫn T6 chéo-vai).

    `retrieved_citations` = chunk đã trích **theo TRACE** (event `kb-retrieve`, từ
    `citations_from_trace`) — nguồn chấm citation, KHÔNG dùng `answer.citations` (agent tự khai):

    - **trả-lời-được**: `success` khi agent KHÔNG từ chối VÀ `answer` CHỨA cụm `expected`
      (`_contains_phrase` — so token liên tiếp, không bắt khớp cả câu/chính tả). `citation_accuracy`
      = |`expected_citation` ∩ `retrieved_citations`| / |`expected_citation`| (set-semantics, ≤1.0
      kể cả trace trùng; rỗng ⇒ 1.0). **`citation_accuracy` là metric riêng, KHÔNG gate `success`** —
      trace sai/rỗng ⇒ accuracy 0.0 nhưng vẫn PASS nếu answer đúng. Giới hạn: token-contains không
      bắt phủ định/ngữ cảnh — chỉ judge (S3).
    - **từ-chối**: **fail-closed** — `success` chỉ khi cả ba: agent thực sự từ chối (`refused`), mọi
      citation TRACE parse được tenant, và không citation TRACE nào thuộc `expected_tenant`. Vi phạm
      bất kỳ ⇒ fail. Đây là **leak SANITY theo chunk-id slug** (D-13): KHÔNG chứng minh fence RLS-UUID
      (fence thật do KB/RLS UUID server-side; `TraceEvent.citations` là `list[str]`, không mang
      tenant_id per-chunk). `citation_accuracy` = 1.0 (Q2 chưa chốt — chỉ hiển thị skeleton).
    """
    if not case.expects_refusal:
        success = (answer.refused is False) and _contains_phrase(answer.answer, case.expected)
        expected = set(case.expected_citation)
        citation_accuracy = (
            len(expected & set(retrieved_citations)) / len(expected) if expected else 1.0
        )
    else:
        all_parseable = all(_citation_tenant(c) is not None for c in retrieved_citations)
        no_leak = all(_citation_tenant(c) != case.expected_tenant for c in retrieved_citations)
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
        tenant_ids: Mapping[str, UUID],
    ) -> list[SmokeResult]:
        """Phác skeleton smoke-eval (D3 #14; D5 #24 đọc trace): duyệt `golden_set.cases`, chạy mỗi
        case qua `runner` (seam `AgentRunner`), chấm bằng `score_case` với citations lấy từ TRACE
        (`citations_from_trace` trên `CaseRun.events`), trả danh sách `SmokeResult`.

        `tenant_ids` map slug (`GoldenCase.tenant`) → `tenant_id` UUID: **resolve tường minh ở đây,
        phía trên seam** (D-13) — golden giữ slug làm nhãn, runner nhận UUID; thiếu slug ⇒ `KeyError`
        (fail-closed). Thật thì map đến từ `core.tenants` (`studio_app`); CLI/test dựng map stand-in.

        Nhận `golden_set` in-memory + `runner` tiêm vào (chưa đọc từ DB, chưa gọi interpreter thật):
        đây là chỗ nối sẽ thay stub bằng adapter engine của AIE-1 (D5–6, #29). KHÔNG dựng `Scorecard`
        (cần `compute_scorecard`, Q1 treo)."""
        results: list[SmokeResult] = []
        for case in golden_set.cases:
            tenant_id = tenant_ids[case.tenant]
            case_run = await runner.run_case(
                agent_id=agent_id,
                query=case.query,
                tenant_id=tenant_id,
                section_roles=case.section_roles,
            )
            retrieved = citations_from_trace(case_run.events)
            results.append(score_case(case, case_run.answer, retrieved))
        return results


# ── Alias tương thích ngược ─────────────────────────────────────────────────────────────────────
# `retrieved_citations` đổi tên từ `_retrieved_citations` ở D7 (xem docstring hàm). Giữ tên cũ vì có
# consumer NGOÀI quadrant đang import nó: `scripts/smoke_eval_d6.py` ở repo cha (bút DE) và
# `apps/studio` (script e2e + test chấm-từ-Postgres). Đổi tên mà không giữ alias sẽ làm vỡ một file
# đã merge vào `main` của repo cha — đúng loại vỡ mà `workbench#4` vừa gây ra khi xoá
# `builder_d4.py`, và bài học rút ra là: bề mặt có người ngoài dùng thì không xoá cùng lúc với đổi.
#
# Không đánh dấu deprecated bằng warning: `run_smoke` chạy trong CI của 3 repo, một `DeprecationWarning`
# ở đó chỉ tạo tiếng ồn mà không ai hành động. Dọn alias khi 3 consumer trên đã chuyển hết — theo dõi
# ở #34, KHÔNG dọn trước D11 freeze.
_retrieved_citations = citations_from_trace
