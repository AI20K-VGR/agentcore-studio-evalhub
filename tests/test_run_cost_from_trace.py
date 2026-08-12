"""Đường đọc cost: `run_cost_from_trace` cộng `cost` **đã lưu**, không suy từ `tokens` — D19/T2.

## Vì sao bộ bài này phải bất đối xứng, không phải vì khẩu vị

`cost` của mọi event trong hệ thống hôm nay là hằng số `0.0` (`engine:interpreter.py:73` `_NO_COST`,
`:438` `cost=_NO_COST`). Trên một trace như thế, một bài khẳng định *"số đọc ra bằng số trong trace"*
xanh với **bốn** cài đặt khác nhau — đọc đúng, tính lại từ tokens, trả hằng số 0, và không đọc gì.
Ba trong bốn là sai.

Nên mọi fixture ở đây **bắt buộc**: `cost` khác 0, bất đối xứng giữa các event, và ở ít nhất một
event `cost` **mâu thuẫn có chủ đích** với `cost_of(tokens)`. Bản đọc đúng và bản tính-lại ra hai số
khác nhau; không cài đặt nào đúng cả hai.

Đơn giá dùng để dựng mâu thuẫn (`0.003`/`0.015` per 1K, luật của `kb#22`) **cố ý không** xuất hiện
trong file này dưới dạng hằng số — §7 xếp *"một hằng số đơn giá trong `studio_evalhub/`"* vào thứ
KHÔNG được tính là xong, kể cả trong test. Các con số kỳ vọng dưới đây là **số viết tay**, tính sẵn
ngoài code và ghim thẳng.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.run_report import RunCost, RunCostError, run_cost_from_trace

_RUN_ID = "run-d19-cost"
_TENANT = UUID("11111111-1111-1111-1111-111111111111")
_TENANT_KHAC = UUID("22222222-2222-2222-2222-222222222222")
_BASE_TS = datetime(2026, 8, 13, 9, 0, tzinfo=UTC)


def _event(
    *,
    seq: int,
    cost: float,
    tokens: Tokens | None = None,
    node_type: NodeType = NodeType.LLM_STEP,
    run_id: str = _RUN_ID,
    tenant_id: UUID = _TENANT,
) -> TraceEvent:
    return TraceEvent(
        event_id=f"{run_id}-{seq}",
        run_id=run_id,
        agent_id="agent-d19",
        tenant_id=tenant_id,
        node_id=f"n{seq}",
        node_type=node_type,
        ts=(_BASE_TS + timedelta(seconds=seq)).isoformat(),
        inputs_hash="stub",
        outputs={},
        tokens=tokens or Tokens(prompt=0, completion=0),
        cost=cost,
    )


# ── 1 · bất đối xứng: đọc ≠ tính lại (DEC-D19-01) ───────────────────────────────────────────────


def test_cost_doc_tu_trace_khong_tinh_lai_tu_tokens() -> None:
    """Bài khoá `DEC-D19-01`. Fixture cố ý dựng `cost` MÂU THUẪN `tokens`.

    | event | tokens | `cost` đã lưu | `cost_of(tokens)` |
    |---|---|---|---|
    | `e1` `llm-step` | 1000 / 1000 | **0.5** | 0.018 |
    | `e2` `tool-call` | 1000 / 1000 | **0.25** | 0.018 |

    Bản **đọc** ra `0.75`. Bản **tính lại** ra `0.036`. Không cài đặt nào đúng cả hai — đó là toàn bộ
    lý do fixture bất đối xứng tồn tại, thay vì một trace `cost = 0.0` (tức trace thật hôm nay) làm
    bài này xanh với mọi cài đặt.

    Dùng **cùng khuôn** `test_aggregate_cong_cost_da_luu_khong_tinh_lai` của `kb#22` có chủ đích: hai
    repo canh cùng một bất biến và người review chéo phải nhận ra ngay.
    """
    events = [
        _event(seq=1, cost=0.5, tokens=Tokens(prompt=1000, completion=1000)),
        _event(seq=2, cost=0.25, tokens=Tokens(prompt=1000, completion=1000), node_type=NodeType.TOOL_CALL),
    ]

    ket_qua = run_cost_from_trace(events)

    assert ket_qua.cost == 0.75, "phải CỘNG cost đã lưu; 0.036 nghĩa là đang nhân tokens × đơn giá"
    assert ket_qua.prompt_tokens == 2000
    assert ket_qua.completion_tokens == 2000
    assert ket_qua.event_count == 2
    assert ket_qua.run_id == _RUN_ID
    assert ket_qua.tenant_id == _TENANT


def test_tokens_khong_he_tham_gia_vao_con_so_cost() -> None:
    """Cùng `cost`, `tokens` khác nhau hoàn toàn ⇒ `cost` ra **y hệt**.

    Bài trên chứng minh bản tính-lại ra SỐ KHÁC. Bài này chứng minh chiều ngược: `tokens` không có
    **đường nào** đi vào con số `cost`. Hai bài cần cả hai vì một cài đặt lai (đọc `cost` rồi cộng
    thêm một hạng nhỏ từ `tokens`) sẽ lọt bài trên nếu con số tình cờ khớp.
    """
    it_token = [
        _event(seq=1, cost=0.5, tokens=Tokens(prompt=1, completion=1)),
        _event(seq=2, cost=0.25, tokens=Tokens(prompt=0, completion=0)),
    ]
    nhieu_token = [
        _event(seq=1, cost=0.5, tokens=Tokens(prompt=99999, completion=88888)),
        _event(seq=2, cost=0.25, tokens=Tokens(prompt=77777, completion=66666)),
    ]

    assert run_cost_from_trace(it_token).cost == run_cost_from_trace(nhieu_token).cost == 0.75


# ── 2 · conformance luật cộng (DEC-D19-03) ──────────────────────────────────────────────────────


def test_conformance_luat_cong_round_6() -> None:
    """Luật cộng là `round(sum, 6)` — số kỳ vọng **viết tay**, không tính bằng chính hàm đang test.

    Bảng ghim, đo trên một run 6 node có 3 bước LLM (37/12 · 211/63 · 1290/417 token, đơn giá
    `kb#22`):

        per-event cost : [0.000291, 0.001578, 0.010125, 0.0, 0.0, 0.0]
        sum(...)       : 0.011994000000000001     ← KHÔNG làm tròn
        round(sum, 6)  : 0.011994                 ← luật của kb#22
                         bằng nhau?  False

    Vế `!= 0.011994000000000001` mới là vế có răng: `== 0.011994` một mình vẫn xanh nếu ai đó bỏ
    `round` **và** float tình cờ ra chẵn. Ở bộ số này nó KHÔNG chẵn, và đó là lý do chọn đúng bộ số
    này chứ không phải một bộ tròn cho đẹp.

    Số kỳ vọng đến từ **ngoài** cài đặt ⇒ bài này tautology-proof. Cùng bộ số được dán sang review
    `kb#22` để DE ghim đối xứng — hai repo không import được nhau nên bảng số viết tay giống hệt là
    lưới chung duy nhất có được (`DEC-D19-03`).
    """
    events = [
        _event(seq=1, cost=0.000291, tokens=Tokens(prompt=37, completion=12)),
        _event(seq=2, cost=0.001578, tokens=Tokens(prompt=211, completion=63)),
        _event(seq=3, cost=0.010125, tokens=Tokens(prompt=1290, completion=417)),
        _event(seq=4, cost=0.0, node_type=NodeType.KB_RETRIEVE),
        _event(seq=5, cost=0.0, node_type=NodeType.TOOL_CALL),
        _event(seq=6, cost=0.0, node_type=NodeType.END),
    ]

    ket_qua = run_cost_from_trace(events)

    assert ket_qua.cost == 0.011994
    assert ket_qua.cost != 0.011994000000000001, "thiếu round(·, 6) — lệch luật cộng của kb#22"
    assert ket_qua.event_count == 6, "Σcost không được in mà thiếu mẫu số (E-6, kit#134)"


# ── 3 · fail-closed (kiểu lỗi riêng, không ValueError trần) ─────────────────────────────────────


def test_events_rong_thi_raise_RunCostError() -> None:
    """Rỗng ⇒ không có run nào để nói về. Fail-closed, không trả `RunCost(cost=0)`.

    Trả một `RunCost` rỗng sẽ tạo ra đúng thứ `F-6`/`no_leak`-trên-tập-rỗng đã cắn nhóm ở D17: một
    con số **trông như phép đo** mà thực ra là *không có gì để đo*.
    """
    with pytest.raises(RunCostError, match="rỗng"):
        run_cost_from_trace([])


def test_tron_run_id_thi_raise_RunCostError() -> None:
    """Trộn `run_id` ⇒ "cost của run này" mất nghĩa."""
    events = [
        _event(seq=1, cost=0.5),
        _event(seq=2, cost=0.25, run_id="run-khac"),
    ]
    with pytest.raises(RunCostError, match="run_id"):
        run_cost_from_trace(events)


def test_tron_tenant_id_thi_raise_RunCostError() -> None:
    """Trộn `tenant_id` ⇒ hở `INV-1`.

    `obs.trace_events` **không có RLS** (`kb#24` hạng mục B, chưa ký đủ), nên `tenant_id` trên từng
    event là hàng rào **duy nhất**. Một tổng trộn tenant là số của tenant này rò sang tenant kia, và
    nó rò dưới dạng một con số trông hoàn toàn bình thường.
    """
    events = [
        _event(seq=1, cost=0.5),
        _event(seq=2, cost=0.25, tenant_id=_TENANT_KHAC),
    ]
    with pytest.raises(RunCostError, match="tenant_id"):
        run_cost_from_trace(events)


def test_kieu_loi_rieng_chu_khong_phai_ValueError_tran() -> None:
    """`RunCostError` là `ValueError` nhưng phải có **danh tính riêng**.

    Cùng lý lẽ `TraceAnswerError` (`run_report.py:66`): một bài `pytest.raises(ValueError)` xanh cả
    khi hàm vỡ vì lý do khác hoàn toàn.
    """
    assert issubclass(RunCostError, ValueError)
    assert RunCostError is not ValueError


# ── 4 · priced: hai trạng thái của số 0 (DEC-D19-05) ────────────────────────────────────────────


def test_priced_false_khi_co_tokens_ma_cost_bang_0() -> None:
    """`Σtokens > 0` **và** `Σcost == 0` ⇒ **chưa nối giá**, `priced is False`.

    Đây là trạng thái của **mọi run thật trong hệ thống hôm nay** — `tokens` đã thật từ
    `engine:executors.py:362`, nhưng `interpreter.py:438` vẫn ghi `cost=_NO_COST`.

    Assert **giá trị** `is False`, không assert không-raise: một bài chỉ gọi hàm rồi không kiểm gì
    sẽ xanh với mọi cài đặt của `priced`.
    """
    events = [
        _event(seq=1, cost=0.0, tokens=Tokens(prompt=37, completion=12)),
        _event(seq=2, cost=0.0, tokens=Tokens(prompt=211, completion=63)),
    ]

    ket_qua = run_cost_from_trace(events)

    assert ket_qua.priced is False
    assert ket_qua.cost == 0.0
    assert ket_qua.prompt_tokens + ket_qua.completion_tokens > 0


def test_priced_true_khi_tokens_bang_0_la_do_that_bang_khong() -> None:
    """`Σtokens == 0` **và** `Σcost == 0` ⇒ **đã đo, bằng 0**, `priced is True`.

    Nửa này là nửa dễ mất nhất, và mất nó thì hỏng vào đúng ngày emit nối giá: node `kb-retrieve` /
    `tool-call` phát `Tokens(0, 0)` ⇒ giá của chúng đúng bằng `0` ⇒ đó là **một phép đo thật**, không
    phải *chưa đo*. Gán nhãn *chưa đo* cho nó là lỗi mà `TraceViewer.tsx:50` (`cost === 0 ? "chưa
    đo"`) sẽ mắc — hôm nay đúng, mai sai.

    Cặp bài này là lý do `priced` phải phân loại theo `tokens` chứ không theo riêng `cost`.
    """
    events = [
        _event(seq=1, cost=0.0, node_type=NodeType.KB_RETRIEVE),
        _event(seq=2, cost=0.0, node_type=NodeType.END),
    ]

    ket_qua = run_cost_from_trace(events)

    assert ket_qua.priced is True
    assert ket_qua.cost == 0.0
    assert ket_qua.prompt_tokens == ket_qua.completion_tokens == 0


def test_priced_true_khi_co_cost_that() -> None:
    """`Σcost > 0` ⇒ đã đo, bất kể `tokens` — nhánh còn lại của bảng `DEC-D19-05`."""
    events = [_event(seq=1, cost=0.000291, tokens=Tokens(prompt=37, completion=12))]

    assert run_cost_from_trace(events).priced is True


# ── ranh giới: KHÔNG có đơn giá trong studio_evalhub ────────────────────────────────────────────


def test_src_khong_chua_hang_so_don_gia() -> None:
    """Quét `src/` bắt cả vi phạm **tương lai** — §7 và `DEC-D19-01`.

    Rủi ro thật, không phải giả định: evalhub **không import được** `studio_kb.cost`
    (`.importlinter` xếp 4 quadrant cùng layer), nên đường "tiện tay" là tự chép `0.003`/`0.015` vào
    đây. Hai nơi giữ giá thì ngày đơn giá đổi một chỗ, ba mặt lệch nhau mà **không mặt nào biết mặt
    nào đúng**.

    Cùng khuôn `test_src_khong_hardcode_duong_dan_kb`. Quét **từng nguồn riêng** chứ không quét một
    tổng — đúng finding mình vừa gửi `kb#22` lượt 3 (`len(surfaces) > 5` chứng minh tổng khác rỗng,
    không chứng minh từng nguồn còn sống); áp cho người khác thì phải áp cho mình.
    """
    from pathlib import Path

    from studio_evalhub import run_report

    src_dir = Path(run_report.__file__).parent
    files = sorted(src_dir.rglob("*.py"))
    assert len(files) >= 10, f"quét được {len(files)} file — nghi resolve sai gốc, bài này xanh giả"

    pham: list[str] = []
    for path in files:
        for so_dong, dong in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "0.003" in dong or "0.015" in dong:
                pham.append(f"{path.relative_to(src_dir)}:{so_dong}")

    assert pham == [], f"đơn giá không được sống trong studio_evalhub (DEC-D19-01, §7): {pham}"


def test_run_cost_khong_nhan_cost_qua_tham_so() -> None:
    """Nguồn là `events`, và **chỉ** `events` — chặn nhánh "tiện tay" của `DEC-D19-01`.

    Cấm: đọc `cost` từ `AgentAnswer`, nhận `cost` qua tham số của caller, cache `cost` từ lần chạy
    trước. Chữ ký một-tham-số là thứ làm cả ba nhánh đó **không diễn đạt được**, nên ghim nó lại.
    """
    import inspect

    tham_so = list(inspect.signature(run_cost_from_trace).parameters)
    assert tham_so == ["events"], f"chữ ký mở thêm đường cấp cost từ ngoài: {tham_so}"


def test_RunCost_bat_bien_khong_sua_duoc() -> None:
    """`RunCost` frozen — một con số đã đọc từ trace không được sửa sau khi trả ra."""
    ket_qua = run_cost_from_trace([_event(seq=1, cost=0.5, tokens=Tokens(prompt=1, completion=1))])

    with pytest.raises((AttributeError, TypeError)):
        ket_qua.cost = 999.0  # type: ignore[misc]

    assert isinstance(ket_qua, RunCost)
