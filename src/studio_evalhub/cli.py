"""CLI smoke-eval — chạy `python -m studio_evalhub.cli` (weekly demo #1, D5 #24).

Dựng bộ 5 smoke-case Callisto (nguồn từ golden-set của DE, `callisto-smoke-5-v0`) + một runner mô
phỏng trả `CaseRun` (câu trả lời + **trace stub**), chạy qua `EvalHarness.run_smoke`, rồi in bảng
điểm 5 dòng (`case_id · success · citation_acc`). **citation_acc chấm từ TRACE** (event `kb-retrieve`
trong `CaseRun.events`), không từ `answer.citations` — đúng luật D5.

Chưa nối interpreter thật hay đọc file YAML của DE: case dựng in-code, runner + trace là mô phỏng —
đổi sang đồ thật khi có loader (`pyyaml` — mentor) + adapter luồng thật ở `apps/studio` (#29, adapter
đổ `RunResult.events` vào `CaseRun.events`, resolve slug→UUID qua `core.tenants`).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_DNS, UUID, uuid5

from studio_contracts import NodeType, Tokens, TraceEvent

from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.harness import EvalHarness, SmokeResult

_AGENT_ID = "agent-smoke-demo"

# Map slug → tenant_id UUID, dựng **tường minh ở tầng CLI** (composition layer) — stand-in cho
# `core.tenants` (D-13: seam nhận UUID, resolve slug→UUID phía trên seam, không giấu trong runner).
# `uuid5` cho ra UUID tất định theo slug (demo tái lập được); thật thì map đến từ DB `core.tenants`.
_DEMO_TENANT_IDS: dict[str, UUID] = {
    "ankor": uuid5(NAMESPACE_DNS, "ankor"),
    "borea": uuid5(NAMESPACE_DNS, "borea"),
}

# Mốc thời gian cố định cho trace stub — `ts` là chuỗi ISO-8601 tăng đơn điệu theo `seq`
# (timezone-aware). KHÔNG phải bằng chứng "0-gap"; chỉ minh hoạ đọc trace lấy citations.
_TRACE_BASE = datetime(2026, 7, 24, tzinfo=UTC)


def _demo_golden_set() -> GoldenSet:
    """Bộ 5 smoke-case Callisto — **nguồn từ golden-set của DE** (`callisto-smoke-5-v0`,
    `packages/kb/golden/smoke-5.yaml`; DE sinh + gán nhãn tay, AIE-2 chỉ đọc). Dựng in-code tạm vì
    loader hoãn (`pyyaml` chưa khai là dep — cần sửa `uv.lock` ở repo cha, mentor); đổi sang loader khi
    khai xong. Không suy diễn/đổi wording/bịa id.
    """
    return GoldenSet(
        golden_set_ref="callisto-smoke-5-v0",
        cases=[
            GoldenCase(
                case_id="SC-01",
                query="Nhân viên xin nghỉ phép cần báo trước bao lâu?",
                tenant="ankor",
                section_roles=["public"],
                expected_tenant="ankor",
                expected_section_role="public",
                expected="3 ngày làm việc",
                expected_citation=["ankor-leave-001#c1"],
            ),
            GoldenCase(
                case_id="SC-02",
                query="Nhân viên xin nghỉ phép cần báo trước bao lâu?",
                tenant="borea",
                section_roles=["public"],
                expected_tenant="borea",
                expected_section_role="public",
                expected="7 ngày làm việc",
                expected_citation=["borea-leave-001#c1"],
            ),
            GoldenCase(
                case_id="SC-03",
                query="Trưởng nhóm được duyệt chi tối đa bao nhiêu?",
                tenant="ankor",
                section_roles=["finance"],
                expected_tenant="ankor",
                expected_section_role="finance",
                expected="20 triệu đồng",
                expected_citation=["ankor-expense-001#c2"],
            ),
            GoldenCase(
                case_id="SC-04",
                query="Hạn mức chi của Borea là bao nhiêu?",
                tenant="ankor",
                section_roles=["public"],
                expected_tenant="borea",
                expected_section_role="finance",
                expected="refusal",
                expected_citation=[],
            ),
            GoldenCase(
                case_id="SC-05",
                query="Thang lương của công ty gồm những bậc nào?",
                tenant="ankor",
                section_roles=["engineering"],
                expected_tenant="ankor",
                expected_section_role="hr",
                expected="refusal",
                expected_citation=[],
            ),
        ],
    )


def _trace_event(
    *,
    run_id: str,
    tenant_id: UUID,
    node_id: str,
    node_type: NodeType,
    seq: int,
    citations: list[str] | None = None,
) -> TraceEvent:
    """Dựng một `TraceEvent` stub. `ts` = chuỗi ISO-8601 (`TraceEvent.ts: str`) tăng đơn điệu theo
    `seq` (timezone-aware). `tenant_id` là UUID (D-13). Chỉ event `kb-retrieve` mang `citations`."""
    return TraceEvent(
        event_id=f"{run_id}-{seq}",
        run_id=run_id,
        agent_id=_AGENT_ID,
        tenant_id=tenant_id,
        node_id=node_id,
        node_type=node_type,
        ts=(_TRACE_BASE + timedelta(seconds=seq)).isoformat(),
        inputs_hash="stub",
        outputs={},
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=citations,
    )


def _case_run(*, run_id: str, tenant_id: UUID, answer: str, refused: bool, retrieved: list[str]) -> CaseRun:
    """Một `CaseRun` demo = câu trả lời + **timeline trace** `kb-retrieve → llm-step → end`.

    `retrieved` là citations của node `kb-retrieve` (nguồn chấm điểm). `AgentAnswer.citations` để
    bằng `retrieved` (agent khai đúng cái đã trích) — nhưng bộ chấm bỏ qua field đó, chấm theo trace.
    """
    events = [
        _trace_event(
            run_id=run_id,
            tenant_id=tenant_id,
            node_id="n_kb",
            node_type=NodeType.KB_RETRIEVE,
            seq=0,
            citations=retrieved,
        ),
        _trace_event(
            run_id=run_id,
            tenant_id=tenant_id,
            node_id="n_llm",
            node_type=NodeType.LLM_STEP,
            seq=1,
        ),
        _trace_event(
            run_id=run_id,
            tenant_id=tenant_id,
            node_id="n_end",
            node_type=NodeType.END,
            seq=2,
        ),
    ]
    return CaseRun(
        answer=AgentAnswer(answer=answer, citations=retrieved, refused=refused),
        events=events,
    )


def _demo_runner() -> StubAgentRunner:
    """Runner mô phỏng agent, khoá theo **`(query, tenant_id)`** (D-13 + cặp SC-01/SC-02 chung
    `query`, khác tenant → khác đáp án). Trả-lời-được: answer CHỨA cụm `expected` + trace `kb-retrieve`
    trích đúng `chunk_id` của DE. Từ-chối: `refused=True`, trace `kb-retrieve` rỗng. Answer text do
    AIE-2 soạn; `chunk_id` chỉ tái dùng đúng của DE, KHÔNG bịa id mới.
    """
    ankor = _DEMO_TENANT_IDS["ankor"]
    borea = _DEMO_TENANT_IDS["borea"]
    return StubAgentRunner(
        {
            ("Nhân viên xin nghỉ phép cần báo trước bao lâu?", ankor): _case_run(
                run_id="run-sc01",
                tenant_id=ankor,
                answer="Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
                refused=False,
                retrieved=["ankor-leave-001#c1"],
            ),
            ("Nhân viên xin nghỉ phép cần báo trước bao lâu?", borea): _case_run(
                run_id="run-sc02",
                tenant_id=borea,
                answer="Nhân viên cần báo trước 7 ngày làm việc.",
                refused=False,
                retrieved=["borea-leave-001#c1"],
            ),
            ("Trưởng nhóm được duyệt chi tối đa bao nhiêu?", ankor): _case_run(
                run_id="run-sc03",
                tenant_id=ankor,
                answer="Trưởng nhóm được duyệt chi tối đa 20 triệu đồng.",
                refused=False,
                retrieved=["ankor-expense-001#c2"],
            ),
            ("Hạn mức chi của Borea là bao nhiêu?", ankor): _case_run(
                run_id="run-sc04",
                tenant_id=ankor,
                answer="Tôi không thể trả lời câu hỏi về dữ liệu của tổ chức khác.",
                refused=True,
                retrieved=[],
            ),
            ("Thang lương của công ty gồm những bậc nào?", ankor): _case_run(
                run_id="run-sc05",
                tenant_id=ankor,
                answer="Tôi không có quyền truy cập thông tin thang lương.",
                refused=True,
                retrieved=[],
            ),
        }
    )


def _render(results: list[SmokeResult]) -> str:
    """Bảng `case_id | success | citation_acc` — cột 'in success' theo issue #14/#19."""
    header = f"{'case_id':<20} {'success':<8} {'citation_acc':>12}"
    lines = [header, "-" * len(header)]
    for r in results:
        lines.append(f"{r.case_id:<20} {('PASS' if r.success else 'FAIL'):<8} {r.citation_accuracy:>12.2f}")
    passed = sum(1 for r in results if r.success)
    lines.append("-" * len(header))
    lines.append(f"{passed}/{len(results)} PASS")
    return "\n".join(lines)


async def _main() -> None:
    results = await EvalHarness().run_smoke(
        agent_id=_AGENT_ID,
        golden_set=_demo_golden_set(),
        runner=_demo_runner(),
        tenant_ids=_DEMO_TENANT_IDS,
    )
    print(_render(results))


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
