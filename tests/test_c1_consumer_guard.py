"""Lưới **phía tiêu thụ** cho clause C-1 của engine.

C-1 (`packages/engine/docs/contracts/trace-citations.v0.md`, chốt `DL-11.A1-10`): **chỉ node
`llm-step` được mang `TraceEvent.citations`**. Cổng cưỡng chế nằm ở `interpreter.py` — phía **sản
xuất**.

## Vì sao file này tồn tại

Mutation của tôi (`docs/evidence/260824-mutation-s3/`) đo được: gỡ cổng C-1 ⇒ **đúng 1** bài đỏ
trên toàn workspace **1699** bài — lưới mỏng nhất trong 5 hàng rào, và nằm **hết** ở phía sản
xuất. Báo cáo đó kết bằng đúng đề nghị này: *"thêm một bài ở evalhub khoá phía consumer"*.

Lỗ mà C-1 chặn có thật: `ToolCallExecutor` trả **thẳng** dict của `ToolDispatch.dispatch()`
(`executors.py:576`), nên một tool bên thứ ba đặt key `"citations"` là giá trị đó vào trace **như
trích dẫn thật** rồi ăn điểm `citation_accuracy`. Hỏng theo chiều **cao hơn sự thật** — cổng trả
một con số trông đạt trong khi nó không đo cái nó tưởng.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.harness import C1ViolationError, c1_violations

_TENANT = uuid4()


def _event(node_type: NodeType, citations: list[str] | None) -> TraceEvent:
    return TraceEvent(
        event_id=str(uuid4()),
        run_id="r1",
        agent_id="a1",
        tenant_id=_TENANT,
        node_id="n",
        node_type=node_type,
        ts="2026-08-25T00:00:00+00:00",
        inputs_hash="h",
        outputs={},
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=citations,
    )


def test_detects_forged_citations_on_tool_call_node() -> None:
    """Đúng vector tấn công mà C-1 dựng ra để chặn: một tool tự khai `citations`."""
    events = [
        _event(NodeType.LLM_STEP, ["that#c1"]),
        _event(NodeType.TOOL_CALL, ["gia#c1", "gia#c2"]),
    ]
    assert c1_violations(events) == ["gia#c1", "gia#c2"]


def test_compliant_trace_reports_nothing() -> None:
    """Chốt chống rỗng-nghĩa. Không có bài này thì một `c1_violations` luôn trả `[]` cũng xanh, và
    lưới thành trang trí."""
    events = [
        _event(NodeType.KB_RETRIEVE, None),
        _event(NodeType.LLM_STEP, ["that#c1"]),
        _event(NodeType.END, None),
    ]
    assert c1_violations(events) == []


def test_empty_citations_on_other_nodes_is_NOT_a_violation() -> None:
    """`[]` là *"đã xét, không có gì"*, khác `["x"]` là *"có giá trị lọt vào"*. Coi list rỗng là vi
    phạm sẽ làm cổng đỏ trên trace hợp lệ — và một cổng kêu oan thì người ta tắt nó."""
    assert c1_violations([_event(NodeType.TOOL_CALL, [])]) == []


def test_collects_from_EVERY_non_llm_step_node_not_just_tool_call() -> None:
    """C-1 phát biểu theo chiều *"chỉ `llm-step` được mang"*, không phải *"`tool-call` bị cấm"*.
    Viết theo chiều cấm-danh-sách là bỏ sót mọi loại node thêm sau này."""
    events = [_event(NodeType.KB_RETRIEVE, ["a#c1"]), _event(NodeType.CONDITION, ["b#c1"])]
    assert sorted(c1_violations(events)) == ["a#c1", "b#c1"]


def test_C1ViolationError_is_RuntimeError_not_ValueError() -> None:
    """Phân biệt có chủ đích với `CoreSelectionError`/`GoldenSetNotFound` (đều là `ValueError`).

    `routes/publish.py` map `ValueError → 400` (*"đầu vào của client sai"*). Một trace vi phạm C-1
    **không** phải lỗi của người bấm Publish — nó là engine sinh ra trace sai luật, tức lỗi hệ
    thống, và phải rơi vào nhánh 500 chứ không đổ cho người dùng."""
    assert issubclass(C1ViolationError, RuntimeError)
    assert not issubclass(C1ViolationError, ValueError)


def test_message_names_the_chunk_ids_that_leaked_in() -> None:
    """Người đọc lỗi cần biết CÁI GÌ lọt vào để đi tìm tool nào khai bậy — một câu 'vi phạm C-1'
    trần không hành động được."""
    with pytest.raises(C1ViolationError, match="gia#c1"):
        raise C1ViolationError(
            f"case 'X': citation lạ {sorted(c1_violations([_event(NodeType.TOOL_CALL, ['gia#c1'])]))}"
        )


def test_tenant_id_does_not_affect_the_measurement() -> None:
    """Lưới này đo **loại node**, không đo tenant — `tenant_scope_ok` là hàng rào khác, và trộn hai
    trục vào một hàm là cách làm cả hai cùng mờ."""
    other: UUID = uuid4()
    ev = _event(NodeType.TOOL_CALL, ["gia#c1"])
    assert c1_violations([ev.model_copy(update={"tenant_id": other})]) == ["gia#c1"]


async def test_gate_STOPS_when_a_trace_violates_C1() -> None:
    """Vế đắt: `EvalHarness.run` phải **ném**, không phải chấm rồi trả một con số.

    Đây là chỗ hậu quả xảy ra. Một citation giả lọt qua làm `citation_accuracy` **cao hơn** sự
    thật — cổng Publish đọc con số đó rồi cho qua một agent chưa đạt. Trả số kèm cảnh báo cũng
    không đủ: không ai đọc cảnh báo của một lượt chấm đã PASS.
    """
    from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
    from studio_evalhub.golden_case import GoldenCase, GoldenSet
    from studio_evalhub.harness import EvalHarness

    tenant_ids = {"ankor": _TENANT}
    case = GoldenCase(
        case_id="C1-01",
        query="q?",
        tenant="ankor",
        section_roles=["hr"],
        expected_tenant="ankor",
        expected_section_role="hr",
        expected="đáp",
        expected_citation=["that#c1"],
    )
    # Trace hợp lệ ở mọi mặt khác — chỉ đúng một citation nằm sai node. Nếu bài này dựng một trace
    # hỏng toàn diện thì nó không phân biệt được "cổng bắt C-1" với "cổng bắt một thứ khác".
    forged = CaseRun(
        answer=AgentAnswer(answer="đáp theo tài liệu", citations=["that#c1"], refused=False),
        events=[_event(NodeType.LLM_STEP, ["that#c1"]), _event(NodeType.TOOL_CALL, ["gia#c1"])],
    )
    runner = StubAgentRunner({(case.query, _TENANT, ("hr",)): forged})

    with pytest.raises(C1ViolationError, match="gia#c1"):
        await EvalHarness().run(
            "agent-c1",
            "ref",
            golden_set=GoldenSet(golden_set_ref="ref", cases=[case]),
            runner=runner,
            tenant_ids=tenant_ids,
            threshold_success=0.9,
            threshold_citation_accuracy=0.95,
        )
