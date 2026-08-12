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
from studio_evalhub.golden_case import GoldenCase
from studio_evalhub.run_report import TraceAnswerError, answer_from_trace, score_run_from_trace

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


def test_answer_from_trace_thieu_key_refused_thi_raise_chu_khong_doan_False() -> None:
    """`llm-step` có `answer` nhưng **không có key `refused`** ⇒ raise, KHÔNG mặc định `False`.

    **Finding B2 của @DongAnh2704** (mutation chéo T7, `kb#17`): trước bài này, đổi default
    `False → True` làm **toàn suite vẫn xanh** — một nhánh có docstring mà 0 lớp test, vì mọi fixture
    đều set `refused` tường minh nên nhánh mặc định chưa từng chạy.

    Vá theo hướng **raise** chứ không theo hướng ghim `False`, ba lý do:

    1. **Đối xứng với chính hàm này.** Nó đã raise ở 4 nhánh không chứng minh được (rỗng · không
       `llm-step` · thiếu `answer` · nhiều `llm-step`). Riêng `refused` đoán im lặng là chỗ lệch, và
       chỗ lệch đó chính là thứ B2 chạm phải.
    2. **`refused` chưa freeze semantic** (breakpoint `#14`). Đoán một giá trị cho field mà nghĩa của
       nó còn đang tranh luận là đúng lớp lỗi cả file này viết ra để chống.
    3. **Mặc định `False` không phải phương án "an toàn", nó là phương án ĐO SAI.** Một ca đáng là
       *từ-chối* mà thiếu key sẽ bị đẩy sang nhánh trả-lời và báo FAIL — bảng điểm nói agent trả lời
       sai, trong khi sự thật là trace không đọc được.

    Producer thật luôn ghi key này (`engine:executors.py:265` — `"refused": not citations`), nên
    thiếu nó nghĩa là trace dị dạng hoặc đến từ producer lạ, không phải một ca vận hành bình thường.
    """
    events = [
        _event(node_type=NodeType.LLM_STEP, seq=0, outputs={"answer": "Nhân viên cần báo trước 3 ngày."}),
        _event(node_type=NodeType.END, seq=1, outputs={}),
    ]

    with pytest.raises(TraceAnswerError, match="refused"):
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


def test_score_run_from_trace_cham_bang_citation_TRACE_chu_khong_bang_agent_TU_KHAI() -> None:
    """`score_run_from_trace` phải lấy citation từ **TRACE**, KHÔNG từ `AgentAnswer.citations`.

    **Bài này được thêm sau khi mutation sweep D15 (M9) tìm ra một mutant SỐNG SÓT.** Đổi thân hàm
    thành `score_case(case, answer, answer.citations)` — tức chấm bằng citation agent **tự khai** —
    và toàn bộ suite vẫn xanh `69 passed`, vì `score_run_from_trace` khi đó chưa có bài nào gọi tới.
    Đó đúng là thứ D5 (`#24`) cấm: `AgentAnswer.citations` là *cái LLM nói nó đã trích*, trace là
    *mặt quan sát thật*. Một agent bịa citation sẽ tự chấm cho mình điểm tuyệt đối.

    Fixture cố ý dựng **bất đối xứng theo nguồn**: trace mang chunk ĐÚNG, còn `outputs["citations"]`
    (tức lời tự khai) mang chunk SAI. Hai nguồn cho hai kết quả khác nhau, nên bài này phân biệt
    được chúng — nếu hai nguồn trùng nhau thì bài không đo được gì.
    """
    case = GoldenCase(
        case_id="SC-01",
        query="Nhân viên xin nghỉ phép cần báo trước bao lâu?",
        tenant="ankor",
        section_roles=["public"],
        expected_tenant="ankor",
        expected_section_role="public",
        expected="3 ngày làm việc",
        expected_citation=["ankor-leave-001#c1"],
    )
    events = [
        _event(node_type=NodeType.KB_RETRIEVE, seq=0, outputs={"chunks": []}),
        _event(
            node_type=NodeType.LLM_STEP,
            seq=1,
            outputs={
                "answer": "Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
                "refused": False,
                # Agent TỰ KHAI một chunk không hề nằm trong trace — đây là lời khai, không phải
                # quan sát. Nếu bộ chấm tin nó thì `citation_accuracy` sẽ là 0.0 vì chunk sai...
                "citations": ["ankor-BIA-DAT-999#c9"],
            },
            # ...còn TRACE thì mang đúng chunk kỳ vọng ⇒ chấm đúng phải ra 1.0.
            citations=["ankor-leave-001#c1"],
        ),
        _event(node_type=NodeType.END, seq=2, outputs={}),
    ]

    result = score_run_from_trace(case, events)

    assert result.citation_accuracy == 1.0, (
        "chấm phải theo citation TRACE (đúng chunk) — ra 0.0 nghĩa là đang chấm theo lời agent tự khai"
    )
    assert result.success is True
    assert result.case_id == "SC-01"

    # Vế đối chứng: lời tự khai vẫn đọc được nguyên vẹn trên `AgentAnswer` — nó không bị xoá, chỉ là
    # không được dùng để chấm. Giữ nó để sau này cross-check hallucination (claimed ⊆ retrieved).
    assert answer_from_trace(events).citations == ["ankor-BIA-DAT-999#c9"]


def test_score_run_from_trace_khong_doc_gi_ngoai_events() -> None:
    """Vế thứ hai của M9: sửa TRACE thì điểm phải ĐỔI.

    Bài trên một mình chưa đủ — nó vẫn xanh nếu hàm hardcode `1.0`. Ở đây cùng một `case`, cùng một
    `answer`, chỉ đổi citation **trong trace**, và đòi điểm khác đi. Đây là bản thu nhỏ của negative
    control mà `test_spine_scored_from_postgres.py` (D7) chạy trên DB thật: *sửa nguồn mà điểm không
    đổi ⇒ điểm không đến từ nguồn đó*."""
    case = GoldenCase(
        case_id="SC-01",
        query="Nhân viên xin nghỉ phép cần báo trước bao lâu?",
        tenant="ankor",
        section_roles=["public"],
        expected_tenant="ankor",
        expected_section_role="public",
        expected="3 ngày làm việc",
        expected_citation=["ankor-leave-001#c1"],
    )
    outputs: dict[str, object] = {
        "answer": "Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
        "refused": False,
    }
    grounded = [
        _event(node_type=NodeType.LLM_STEP, seq=0, outputs=outputs, citations=["ankor-leave-001#c1"]),
        _event(node_type=NodeType.END, seq=1, outputs={}),
    ]
    tampered = [
        _event(node_type=NodeType.LLM_STEP, seq=0, outputs=outputs, citations=["chunk-khong-ton-tai#c999"]),
        _event(node_type=NodeType.END, seq=1, outputs={}),
    ]

    assert score_run_from_trace(case, grounded).citation_accuracy == 1.0
    assert score_run_from_trace(case, tampered).citation_accuracy == 0.0, (
        "đổi citation trong trace mà điểm không đổi ⇒ điểm KHÔNG đến từ trace"
    )


def test_answer_from_trace_khong_doi_event_dau_vao() -> None:
    """Hàm thuần: đọc xong, `events` và `outputs` bên trong giữ nguyên.

    `TraceEvent.outputs` là `dict` — một hàm `pop` key ra để đọc sẽ làm rỗng trace của caller, và
    caller kế tiếp (`citations_from_trace`) sẽ thấy một trace khác trace nó được đưa."""
    events = _answerable_run()
    before = [e.model_dump() for e in events]

    answer_from_trace(events)

    assert [e.model_dump() for e in events] == before


# ── T5 · `score_run_from_trace` nhận đường chunks (kit#118, nợ đến hạn D18) ───────────────────────
# Nợ D17: 6 call-site còn đi đường `citations` **vacuous**, và món nặng nhất là hàm này — vì
# `workbench/dev_playground_server.py:189` gọi nó, nên **số hiển thị trên Playground chưa hưởng bản
# vá F-6**. Nêu bởi SWE ở review `evalhub#18`.

_T5_ANKOR = uuid5(NAMESPACE_DNS, "ankor")
_T5_BOREA = uuid5(NAMESPACE_DNS, "borea")
_T5_TENANTS = {"ankor": _T5_ANKOR, "borea": _T5_BOREA}


def _t5_case() -> GoldenCase:
    """Case âm T1 chéo-tenant: người hỏi ở `ankor`, đáp án nằm ở `borea` ⇒ agent PHẢI từ chối."""
    return GoldenCase(
        case_id="T5-01",
        query="q",
        tenant="ankor",
        section_roles=["public"],
        expected_tenant="borea",
        expected_section_role="public",
        expected="refusal",
        expected_citation=[],
    )


def _t5_events(*, chunks: list[dict[str, object]]) -> list[TraceEvent]:
    """Agent từ chối, `citations` **rỗng**, nhưng retrieval ĐÃ kéo về `chunks`.

    Đây chính là hình dạng của bug `F-6`: nhìn từ `citations` thì trace *"không trích gì"* ⇒ hàng rào
    trông như chặn sạch; nhìn từ `outputs["chunks"]` thì thấy đã rò chunk của kho khác."""
    return [
        TraceEvent(
            event_id="e1",
            run_id="r1",
            agent_id="a",
            tenant_id=_T5_ANKOR,
            node_id="n1",
            node_type=NodeType.KB_RETRIEVE,
            ts="2026-08-12T00:00:00+00:00",
            inputs_hash="h",
            outputs={"chunks": chunks},
            tokens=Tokens(prompt=0, completion=0),
            cost=0.0,
            citations=[],
        ),
        TraceEvent(
            event_id="e2",
            run_id="r1",
            agent_id="a",
            tenant_id=_T5_ANKOR,
            node_id="n2",
            node_type=NodeType.LLM_STEP,
            ts="2026-08-12T00:00:01+00:00",
            inputs_hash="h",
            outputs={
                "answer": "Không tìm thấy thông tin trong phạm vi được phép, nên không thể trả lời.",
                "refused": True,
                "citations": [],
            },
            tokens=Tokens(prompt=0, completion=0),
            cost=0.0,
            citations=[],
        ),
    ]


def test_score_run_from_trace_khong_truyen_tenant_ids_giu_nguyen_duong_cu() -> None:
    """**Additive**: không truyền `tenant_ids` ⇒ đường CŨ y nguyên, không đổi một dòng hành vi.

    Điều kiện để `workbench/dev_playground_server.py:189` — gọi **2 tham số vị trí** — chạy nguyên khi
    chữ ký đổi. `tenant_ids` keyword-only + default `None` là hình duy nhất giữ được điều đó.

    Trace ở đây **rò chunk của `borea`** trong khi người hỏi ở `ankor`. Đường cũ chấm `no_leak` trên
    `citations` (rỗng) ⇒ `all(...)` trên tập rỗng ⇒ `True` ⇒ **PASS oan**. Bài này khoá chính hành vi
    vacuous đó — không phải vì nó đúng, mà vì **đổi nó mà không ai chọn** là phá hợp đồng của một API
    công khai có consumer ngoài quadrant."""
    events = _t5_events(chunks=[{"chunk_id": "borea-x#c1", "tenant_id": str(_T5_BOREA), "section_role": "public"}])

    ket_qua = score_run_from_trace(_t5_case(), events)

    assert ket_qua.success is True  # PASS oan — đường cũ, giữ nguyên có chủ đích


def test_score_run_from_trace_co_tenant_ids_thi_di_duong_chunks() -> None:
    """Truyền `tenant_ids` ⇒ đi đường **chunks**, và bắt được đúng cái đường cũ để lọt.

    Cùng một `case`, cùng một `events` với bài trên — **chỉ khác một tham số** — mà kết quả lật từ
    `True` sang `False`. Đó là cách duy nhất chứng minh nhánh mới **chạy thật** chứ không phải chạy
    rồi cho ra cùng số: nếu bài chỉ assert `success is False` mà không có bài đối chiếu ở trên, một
    bản vá làm hỏng cả hai đường vẫn xanh."""
    events = _t5_events(chunks=[{"chunk_id": "borea-x#c1", "tenant_id": str(_T5_BOREA), "section_role": "public"}])

    ket_qua = score_run_from_trace(_t5_case(), events, tenant_ids=_T5_TENANTS)

    assert ket_qua.success is False  # rò kho `borea` ⇒ FAIL, đúng luật F-6


def test_score_run_from_trace_co_tenant_ids_va_hang_rao_sach_thi_pass() -> None:
    """Bài đối trọng: cùng đường chunks, retrieval **không rò** ⇒ vẫn PASS.

    Không có bài này thì bài trên không phân biệt được *"đường chunks bắt đúng rò rỉ"* với *"đường
    chunks chấm FAIL mọi thứ"* — và một bản vá trả `success=False` cứng cũng cho nó xanh."""
    events = _t5_events(chunks=[{"chunk_id": "ankor-x#c1", "tenant_id": str(_T5_ANKOR), "section_role": "public"}])

    ket_qua = score_run_from_trace(_t5_case(), events, tenant_ids=_T5_TENANTS)

    assert ket_qua.success is True


def test_score_run_from_trace_co_tenant_ids_nhung_khong_co_kb_retrieve_thi_fail_closed() -> None:
    """Có `tenant_ids` mà trace **không có event `kb-retrieve`** ⇒ `chunks_from_trace` trả `None` ⇒
    **fail-closed**.

    `None` ≠ `[]`: `[]` là *"hàng rào chặn sạch"* — bằng chứng TỐT; `None` là *"không quan sát được"*
    — không chứng minh được gì. Một bản vá gộp hai cái đó sẽ biến mọi trace thiếu retrieval thành
    một hàng rào hoàn hảo."""
    events = [e for e in _t5_events(chunks=[]) if e.node_type is not NodeType.KB_RETRIEVE]

    ket_qua = score_run_from_trace(_t5_case(), events, tenant_ids=_T5_TENANTS)

    assert ket_qua.success is False
