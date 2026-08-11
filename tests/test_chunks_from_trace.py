"""`chunks_from_trace` — nguồn dữ liệu mới của `no_leak` nhánh từ-chối (`F-6`, `DEC-D17-02`).

Vì sao có file riêng thay vì nhét vào `test_smoke_runner.py`: file kia khoá **LUẬT CHẤM**. Hàm này
là **phép đọc trace**, cùng tầng với `citations_from_trace` — hỏng ở đây thì mọi luật chấm bên trên
đều đọc sai, nên nó phải đỏ **vì nó hỏng**, không lẫn với "luật chấm sai".

Ba giá trị trả về mang ba nghĩa khác nhau (`None` ≠ `[]` ≠ non-empty) và đó là chỗ dễ chọn sai nhất
của bản vá — mỗi nghĩa có một bài riêng ở đây.
"""

from __future__ import annotations

from uuid import NAMESPACE_DNS, UUID, uuid5

from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.harness import chunks_from_trace

_ANKOR: UUID = uuid5(NAMESPACE_DNS, "ankor")


def _event(node_type: NodeType, outputs: dict[str, object]) -> TraceEvent:
    """`TraceEvent` stub — chỉ `node_type` và `outputs` là thứ bài này quan tâm. `citations` để
    `None` CÓ CHỦ ĐÍCH: hàm không được đọc field đó, và để `None` chứng minh điều ấy."""
    return TraceEvent(
        event_id="e",
        run_id="r",
        agent_id="a",
        tenant_id=_ANKOR,
        node_id="n",
        node_type=node_type,
        ts="2026-08-11T00:00:00+00:00",
        inputs_hash="h",
        outputs=outputs,
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=None,
    )


def _chunk(chunk_id: str, section_role: str = "public") -> dict[str, object]:
    return {
        "chunk_id": chunk_id,
        "tenant_id": str(_ANKOR),
        "section_role": section_role,
        "score": 0.5,
        "text": "nội dung",
    }


def test_khong_co_kb_retrieve_thi_None_khong_phai_rong() -> None:
    """KHÔNG event `kb-retrieve` nào ⇒ `None` = *không quan sát được*, fail-closed.

    Bài này khoá đúng chỗ dễ sai nhất: trả `[]` ở đây sẽ bị tầng trên đọc thành *"hàng rào chặn
    sạch"* — biến một ca không-chứng-minh-được thành một bằng chứng TỐT giả."""
    events = [_event(NodeType.LLM_STEP, {"refused": True}), _event(NodeType.END, {})]

    assert chunks_from_trace(events) is None


def test_co_kb_retrieve_nhung_rong_thi_rong_khong_phai_None() -> None:
    """Có event nhưng retrieval trả 0 chunk ⇒ `[]` = *hàng rào chặn sạch*. Chiều ngược của bài trên;
    thiếu nó thì một cài đặt trả `None` cho cả hai ca vẫn xanh."""
    events = [_event(NodeType.KB_RETRIEVE, {"chunks": []})]

    assert chunks_from_trace(events) == []


def test_giu_du_5_khoa_khong_rut_thanh_chunk_id() -> None:
    """Trả **bản ghi đầy đủ**. `tenant_id` + `section_role` là hai field `no_leak` chấm trên đó
    (`DEC-D17-03`); rút thành `chunk_id` là quay lại heuristic tiền tố slug mà `F-6` bỏ đi."""
    events = [_event(NodeType.KB_RETRIEVE, {"chunks": [_chunk("ankor-leave-001#c1", "hr")]})]

    got = chunks_from_trace(events)

    assert got is not None
    assert got[0]["chunk_id"] == "ankor-leave-001#c1"
    assert got[0]["tenant_id"] == str(_ANKOR)
    assert got[0]["section_role"] == "hr"


def test_chi_doc_node_kb_retrieve() -> None:
    """`outputs["chunks"]` là khoá của riêng `kb-retrieve` (`interpreter.py:218`). Một node khác
    mang khoá trùng tên KHÔNG được gom vào — nếu không, `no_leak` chấm trên dữ liệu của node lạ.

    Fixture **bất đối xứng** có chủ đích (1 chunk thật + 2 chunk giả ở node khác): tỷ lệ cân là chỗ
    một cài đặt gom-tất-cả vẫn ra cùng số lượng."""
    events = [
        _event(NodeType.KB_RETRIEVE, {"chunks": [_chunk("ankor-leave-001#c1")]}),
        _event(NodeType.LLM_STEP, {"chunks": [_chunk("gia-001#c1"), _chunk("gia-002#c1")]}),
    ]

    got = chunks_from_trace(events)

    assert got is not None
    assert [c["chunk_id"] for c in got] == ["ankor-leave-001#c1"]


def test_nhieu_kb_retrieve_thi_gom_het_theo_thu_tu() -> None:
    """Một run có thể có nhiều node `kb-retrieve`. Gom hết, giữ thứ tự — bỏ sót một node là bỏ sót
    đúng chỗ chunk rò có thể nấp."""
    events = [
        _event(NodeType.KB_RETRIEVE, {"chunks": [_chunk("ankor-a-001#c1")]}),
        _event(NodeType.LLM_STEP, {}),
        _event(NodeType.KB_RETRIEVE, {"chunks": [_chunk("ankor-b-001#c1")]}),
    ]

    got = chunks_from_trace(events)

    assert got is not None
    assert [c["chunk_id"] for c in got] == ["ankor-a-001#c1", "ankor-b-001#c1"]
