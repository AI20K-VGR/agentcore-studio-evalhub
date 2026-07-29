"""Test `tenant_scope_ok` — sanity nhất quán tenant ở mức TRACE của một run (D8 #39).

KHÓA: mọi `TraceEvent` của một run mang cùng `tenant_id`, và `tenant_id` đó đúng bằng cái đã resolve
cho case. Đây là **tenant-consistency sanity (observe-only)**, KHÔNG phải leak-test T1
(`day-08.md`: *"chưa cần test T1 IDOR / T6 label-spoof — để Sprint 2"*).

Vì sao tách khỏi `test_smoke_runner.py`: file đó khoá LUẬT CHẤM (`score_case` 2 nhánh + `run_smoke`).
`tenant_scope_ok` cố ý nằm NGOÀI luật chấm — nó không gate `success`, và `score_case` không nhận
`events` nên cấu trúc mà nói không đọc được `tenant_id`. Giữ riêng file để ranh giới đó nhìn thấy
được từ cây thư mục, không phải suy từ docstring.

Bất biến này trước D8 chỉ tồn tại trong *script* `apps/studio/scripts/e2e_smoke_eval.py`. Script
không chạy thì bất biến không được kiểm — đây là chỗ nó trở thành test tự chạy.
"""

from __future__ import annotations

from uuid import NAMESPACE_DNS, UUID, uuid5

from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub import tenant_scope_ok

_ANKOR: UUID = uuid5(NAMESPACE_DNS, "ankor")
_BOREA: UUID = uuid5(NAMESPACE_DNS, "borea")


def _event(node_type: NodeType, tenant_id: UUID) -> TraceEvent:
    """`TraceEvent` stub — chỉ `tenant_id` và `node_type` là thứ test này quan tâm. `citations` để
    `None` có chủ đích: `tenant_scope_ok` không đọc citations, và để `None` chứng minh điều đó."""
    return TraceEvent(
        event_id="e",
        run_id="r",
        agent_id="a",
        tenant_id=tenant_id,
        node_id="n",
        node_type=node_type,
        ts="2026-07-29T00:00:00+00:00",
        inputs_hash="h",
        outputs={},
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=None,
    )


def test_moi_event_cung_tenant_thi_dat() -> None:
    """Chuỗi 4 node như một run thật (`kb-retrieve → llm-step → tool-call → end`), cùng tenant."""
    events = [
        _event(NodeType.KB_RETRIEVE, _ANKOR),
        _event(NodeType.LLM_STEP, _ANKOR),
        _event(NodeType.TOOL_CALL, _ANKOR),
        _event(NodeType.END, _ANKOR),
    ]

    assert tenant_scope_ok(events, _ANKOR) is True


def test_mot_event_lech_tenant_thi_khong_dat() -> None:
    """Chỉ node THỨ HAI lệch — ba node còn lại đúng.

    Đây là hình dạng thật của một lỗi threading: không phải cả run sai, mà một node quên inject rồi
    rơi về giá trị khác. Kiểm bằng một event lệch giữa chuỗi (không phải đầu, không phải cuối) vì
    một hiện thực chỉ xét `events[0]` hoặc `events[-1]` sẽ lọt."""
    events = [
        _event(NodeType.KB_RETRIEVE, _ANKOR),
        _event(NodeType.LLM_STEP, _BOREA),  # ← lệch
        _event(NodeType.TOOL_CALL, _ANKOR),
        _event(NodeType.END, _ANKOR),
    ]

    assert tenant_scope_ok(events, _ANKOR) is False


def test_toan_bo_run_sai_tenant_thi_khong_dat() -> None:
    """Nhất quán nội bộ nhưng sai so với `expected` — run tự nó đồng nhất mà chạy dưới danh tính
    khác. Nhất quán KHÔNG đủ; phải nhất quán ĐÚNG cái đã resolve cho case."""
    events = [_event(NodeType.KB_RETRIEVE, _BOREA), _event(NodeType.END, _BOREA)]

    assert tenant_scope_ok(events, _ANKOR) is False


def test_khong_co_event_thi_fail_closed() -> None:
    """`events` rỗng ⇒ `False`, không phải `True`.

    Đây là test quan trọng nhất trong file. `all([])` trong Python là `True`, nên một hiện thực viết
    thẳng `all(e.tenant_id == expected for e in events)` sẽ cho một run **không có event nào** điểm
    hợp lệ. Không có trace thì không chứng minh được scope đúng, và "không chứng minh được" phải đọc
    là chưa đạt. Xanh-giả tệ hơn đỏ."""
    assert tenant_scope_ok([], _ANKOR) is False
