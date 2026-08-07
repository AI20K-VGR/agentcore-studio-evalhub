"""Test `answer_from_trace` — dựng lại `AgentAnswer` từ TRACE đã bền hoá. D15, `kit#103`.

Viết **trước** khi `run_report.py` tồn tại (T3 bước 1).

## Vì sao hàm này cần tồn tại

`score_case` cần hai thứ: `retrieved_citations` (đã có `citations_from_trace` từ D5) và một
`AgentAnswer`. Vế thứ hai tới nay **luôn đến từ RAM** — `CaseRun.answer` do runner trả về trong cùng
tiến trình. Kể cả `test_spine_scored_from_postgres.py` (D7), bài đọc trace từ Postgres, vẫn lấy
`case_run.answer` từ bộ nhớ.

Nghĩa là chưa từng có case nào được chấm **hoàn toàn** từ dữ liệu đã bền hoá. Đó chính là khoảng
trống mà dòng 🎯 của `#103` — *"scorecard skeleton đọc trace của run THẬT"* — nói tới: một bộ chấm
còn phải giữ object trong RAM thì không đọc được run của người khác, không đọc lại được run hôm qua,
và không nối được vào playground của `#102`.

## Fail-closed ở mọi nhánh không chứng minh được

Trace thiếu `llm-step`, thiếu key `answer`, hoặc có **nhiều** `llm-step` ⇒ **raise**, không đoán.
Chọn đại một event khi có nhiều ứng viên là đúng lớp lỗi breakpoint `#14`: một giá trị được suy ra
im lặng rồi được chấm như thể đã đo.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_DNS, uuid5

import pytest
from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.run_report import TraceAnswerError, answer_from_trace

_TENANT = uuid5(NAMESPACE_DNS, "ankor")
_RUN_ID = "run-d15-answer"
_BASE_TS = datetime(2026, 8, 7, tzinfo=UTC)


def _event(
    *,
    node_type: NodeType,
    seq: int,
    outputs: dict[str, object] | None = None,
    citations: list[str] | None = None,
) -> TraceEvent:
    return TraceEvent(
        event_id=f"{_RUN_ID}-{seq}",
        run_id=_RUN_ID,
        agent_id="agent-d15",
        tenant_id=_TENANT,
        node_id=f"n{seq}",
        node_type=node_type,
        ts=(_BASE_TS + timedelta(seconds=seq)).isoformat(),
        inputs_hash="stub",
        outputs=outputs or {},
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=citations,
    )


def _answerable_run() -> list[TraceEvent]:
    """Timeline 4 node đúng như interpreter emit: `kb-retrieve → llm-step → tool-call → end`.

    Cố ý **bất đối xứng**: chỉ `llm-step` mang `answer`, chỉ `kb-retrieve` mang `chunks`, và chỉ
    `llm-step` mang `citations` (clause C-1). Một hàm nhặt bừa event đầu/cuối sẽ lộ ra ngay."""
    return [
        _event(node_type=NodeType.KB_RETRIEVE, seq=0, outputs={"chunks": [{"chunk_id": "ankor-leave-001#c1"}]}),
        _event(
            node_type=NodeType.LLM_STEP,
            seq=1,
            outputs={
                "answer": "Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
                "refused": False,
                "citations": ["ankor-leave-001#c1"],
            },
            citations=["ankor-leave-001#c1"],
        ),
        _event(node_type=NodeType.TOOL_CALL, seq=2, outputs={"ok": True}),
        _event(node_type=NodeType.END, seq=3, outputs={"done": True}),
    ]


def test_answer_from_trace_lay_dung_answer_cua_node_llm_step() -> None:
    """HAPPY: `answer` đọc từ `outputs` của event `llm-step`, không phải event đầu hay event cuối.

    Fixture đặt `chunks` ở `kb-retrieve` và `done` ở `end` — nếu hàm nhặt event đầu/cuối thì nó
    không tìm thấy `answer` và bài này đỏ, chứ không âm thầm trả chuỗi rỗng."""
    answer = answer_from_trace(_answerable_run())

    assert answer.answer == "Nhân viên cần báo trước tối thiểu 3 ngày làm việc."
    assert answer.refused is False
    assert answer.citations == ["ankor-leave-001#c1"]


def test_answer_from_trace_nhanh_tu_choi_doc_duoc_refused_true() -> None:
    """Nhánh từ-chối: `refused=True` đọc ra từ `outputs["refused"]` của `llm-step`.

    Vế đối chứng của bài trên — thiếu nó thì một bản vá hardcode `refused=False` vẫn xanh, và mọi
    case từ-chối sẽ bị chấm FAIL oan (`score_case` đòi `answer.refused is True`).

    Ghi rõ giới hạn: **semantic của `refused` CHƯA freeze** (Breakpoint `#14`) — ở đây nó được dùng
    đúng nghĩa *carrier*, tức đọc lại giá trị mà producer đã ghi, chứ không phải một oracle độc lập
    khẳng định run này thật sự an toàn."""
    events = [
        _event(node_type=NodeType.KB_RETRIEVE, seq=0, outputs={"chunks": []}),
        _event(
            node_type=NodeType.LLM_STEP,
            seq=1,
            outputs={"answer": "Tôi không thể trả lời câu hỏi về dữ liệu của tổ chức khác.", "refused": True},
        ),
        _event(node_type=NodeType.END, seq=2, outputs={}),
    ]

    answer = answer_from_trace(events)

    assert answer.refused is True
    assert "không thể trả lời" in answer.answer
    assert answer.citations == [], "llm-step không khai citations ⇒ rỗng, KHÔNG phải None"


def test_answer_from_trace_thieu_llm_step_thi_raise_chu_khong_tra_chuoi_rong() -> None:
    """Fail-closed: không có `llm-step` ⇒ `TraceAnswerError`.

    Trả `AgentAnswer(answer="")` ở đây sẽ cho ra một case FAIL trông hợp lệ — và một run **không đọc
    được** bị đếm vào mẫu số như một run đã đo. Đó đúng là cơ chế mà `tenant_scope_ok` từ chối khi
    nó trả `False` cho `events` rỗng thay vì để `all([])` cho điểm miễn phí."""
    events = [
        _event(node_type=NodeType.KB_RETRIEVE, seq=0, outputs={"chunks": []}),
        _event(node_type=NodeType.END, seq=1, outputs={}),
    ]

    with pytest.raises(TraceAnswerError, match="llm-step"):
        answer_from_trace(events)


def test_answer_from_trace_thieu_key_answer_thi_raise() -> None:
    """`llm-step` có mặt nhưng `outputs` không có key `answer` ⇒ raise.

    Khác bài trên ở chỗ hỏng: node đúng, payload thiếu. Hai lý do vỡ khác nhau phải phân biệt được,
    nếu không thì lúc gỡ lỗi người đọc không biết nên đi sửa recipe hay sửa executor."""
    events = [
        _event(node_type=NodeType.LLM_STEP, seq=0, outputs={"refused": False}),
        _event(node_type=NodeType.END, seq=1, outputs={}),
    ]

    with pytest.raises(TraceAnswerError, match="answer"):
        answer_from_trace(events)


def test_answer_from_trace_nhieu_llm_step_thi_raise_chu_khong_chon_bua() -> None:
    """Nhiều `llm-step` ⇒ raise, KHÔNG tự chọn cái đầu hay cái cuối.

    Một recipe nhiều bước LLM là chuyện sẽ tới (`#102` playground dựng recipe tự do). Lúc đó *"câu
    trả lời của run"* là cái nào phải do hợp đồng nói, không do thứ tự dòng trong bảng nói. Chọn im
    lặng sẽ cho ra một bảng điểm trông vẫn đúng trong khi nó đang chấm nhầm bước."""
    events = [
        _event(node_type=NodeType.LLM_STEP, seq=0, outputs={"answer": "bước 1", "refused": False}),
        _event(node_type=NodeType.LLM_STEP, seq=1, outputs={"answer": "bước 2", "refused": False}),
        _event(node_type=NodeType.END, seq=2, outputs={}),
    ]

    with pytest.raises(TraceAnswerError, match="2"):
        answer_from_trace(events)


def test_answer_from_trace_events_rong_thi_raise() -> None:
    """`events` rỗng ⇒ raise. Không có trace thì không có gì để chấm, và im lặng trả về một answer
    rỗng là biến *"chưa đo"* thành *"đã đo và trượt"* — cùng lỗi mà `DEC-D12-02` cấm ở tầng render."""
    with pytest.raises(TraceAnswerError):
        answer_from_trace([])


def test_answer_from_trace_khong_doi_event_dau_vao() -> None:
    """Hàm thuần: đọc xong, `events` và `outputs` bên trong giữ nguyên.

    `TraceEvent.outputs` là `dict` — một hàm `pop` key ra để đọc sẽ làm rỗng trace của caller, và
    caller kế tiếp (`citations_from_trace`) sẽ thấy một trace khác trace nó được đưa."""
    events = _answerable_run()
    before = [e.model_dump() for e in events]

    answer_from_trace(events)

    assert [e.model_dump() for e in events] == before
