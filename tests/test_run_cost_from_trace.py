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


def test_prompt_va_completion_khong_bi_hoan_vi() -> None:
    """`prompt_tokens` và `completion_tokens` phải về **đúng field của nó**.

    ## Finding của người ngoài, không phải của tôi

    @DongAnh2704 gieo mutation chéo khi review `evalhub#22` và tìm ra: hoán vị hai dòng

        prompt_tokens     = sum(e.tokens.prompt ...)
        completion_tokens = sum(e.tokens.completion ...)

    thì **toàn bộ 218 bài vẫn xanh**. Đã gieo lại độc lập để xác nhận thay vì tin bảng — mutant
    **SỐNG** thật.

    Lý do lưới hụt, và nó đúng lớp lỗi PR này lấy làm luận đề: hai field chỉ lộ ra dưới dạng
    **tổng** (`Σtokens` ở renderer), còn chỗ duy nhất assert riêng từng field —
    `test_cost_doc_tu_trace_khong_tinh_lai_tu_tokens` — lại dùng fixture `1000/1000`. **Đối xứng
    nên nuốt câm hoán vị.** Cùng họ với bốn lần xanh-giả khác của ngày: bài xanh vì thứ nó đi tìm
    tình cờ trùng ở chỗ khác.

    Đáng vá chứ không phải nit thẩm mỹ: `RunCost` là **export công khai**, và `DEC-D19-02` lấy
    *"tên field khớp `RunCost` của `kb#22` nên review chéo nhận ra ngay"* làm lý lẽ. Field bị chéo
    đúng là loại **lệch âm thầm** mà lý lẽ đó sinh ra để chặn.

    Fixture **bất đối xứng** `37/12` — cùng kỹ thuật `DEC-D19-01` dùng khắp bộ này: một cặp số mà
    hoán vị cho ra kết quả khác.
    """
    ket_qua = run_cost_from_trace([_event(seq=1, cost=0.5, tokens=Tokens(prompt=37, completion=12))])

    assert ket_qua.prompt_tokens == 37
    assert ket_qua.completion_tokens == 12

    # Đối chứng: tổng vẫn đúng ở CẢ HAI chiều, nên một bài chỉ assert tổng không thay được bài này.
    assert ket_qua.prompt_tokens + ket_qua.completion_tokens == 49


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


def test_luat_cong_ghim_ndigits_ca_HAI_phia() -> None:
    """`_COST_ROUND_NDIGITS` phải bị ghim ở **cả hai chiều** — nhiều chữ số cũng sai như ít chữ số.

    ## Vì sao cần bài này ngoài bài conformance ở trên

    Bài trên dùng bộ số `0.011994...` và ghim `round(·, 6)`. Đo bằng mutation:

        6 → 5 : 6 bài đỏ   ← chết
        6 → 7 : 219 passed ← SỐNG
        6 → 8 : 219 passed ← SỐNG

    Hằng số bị canh **một phía**. Lý do: `round(0.011994000000000001, 8)` vẫn ra `0.011994` — giá trị
    đó không có chữ số thập phân thứ 7 khác 0, nên tăng `ndigits` không đổi kết quả.

    ## Vì sao đây không phải nit tùy chọn

    Docstring của `_COST_ROUND_NDIGITS` khai thẳng rủi ro là *"không lint/type/test nào bắt được ngày
    `kb` đổi `6` thành **`8`**"*. Tức trước bài này, hằng số **có cam kết canh kịch bản `6→8` mà
    không có lưới nào đỏ khi nó thành `8`** — doc nói mạnh hơn test.

    Hai đường xử: thêm bài, hoặc xoá câu trong docstring. Chọn thêm bài, vì cam kết đó **đúng** —
    `round(·, 6)` là hằng số dùng chung với `kb/src/studio_kb/cost.py` và hai repo không import được
    nhau, nên đây đúng là chỗ duy nhất có thể cưỡng chế được gì đó.

    Phát hiện qua mutation vét cạn của @DongAnh2704 khi review `evalhub#22` (xếp mục B *"tùy chọn"*);
    đo lại cho thấy nó chạm vào một cam kết đã ghi nên không tùy chọn.

    ## Fixture — một số phân biệt được cả bốn `ndigits`

        round(0.12345678, 5) = 0.12346
        round(0.12345678, 6) = 0.123457     ← luật hiện hành
        round(0.12345678, 7) = 0.1234568
        round(0.12345678, 8) = 0.12345678

    Bốn giá trị khác nhau ⇒ mọi mutation của `ndigits` đều đỏ, không chỉ chiều giảm.
    """
    ket_qua = run_cost_from_trace([_event(seq=1, cost=0.12345678, tokens=Tokens(prompt=1, completion=1))])

    assert ket_qua.cost == 0.123457


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


def test_priced_false_khi_chi_co_prompt_token() -> None:
    """`Σprompt > 0`, `Σcompletion == 0`, `Σcost == 0` ⇒ vẫn **chưa nối giá**, `priced is False`.

    ## Đây là ca miền THẬT, không phải ca biên

    Đo ở `engine` `origin/main` (`bfa19cc`, `executors.py:362-364`):

        "tokens":  Tokens(prompt=len(prompt.split()), completion=len(answer.split())),
        "refused": not citations,

    `answer` rỗng ⇒ `len("".split()) == 0` ⇒ **`completion = 0`**. Và `answer` rỗng ⇒ không trích được
    citation nào ⇒ **`refused = True`**. Tức `(prompt > 0, completion = 0)` chính là **nhánh từ-chối
    với câu trả lời rỗng** — không phải một giá trị biên bịa ra cho test, mà là nhánh trung tâm của
    bộ chấm này (D17 đo: 8/30 case golden là case từ-chối).

    ## Lỗ nó bịt — finding review chéo của @DongAnh2704 (`evalhub#22`)

    Mutation vét cạn tìm ra ba mutant sống qua **cả 219 bài**, cùng một gốc:

        priced drop-completion   `prompt_tokens > 0`
        priced drop-prompt       `completion_tokens > 0`
        priced (+ → -)           `prompt_tokens - completion_tokens > 0`

    Chúng sống vì **mọi** fixture `priced=False` trước đây có **cả hai** nửa token khác 0 (`37/12`,
    `211/63`) — đối xứng nên nuốt câm việc mất một nửa. Bài này bất đối xứng theo đúng chiều còn
    thiếu, và nó giết `drop-prompt` cùng `(+ → -)` phía dương.

    Đây là nửa mà `DEC-D19-05` tự gọi là *"dễ mất nhất, hỏng đúng ngày emit nối giá"* — nên một
    mutant sống ở đây không phải vệ sinh, nó là lỗ ở đúng chỗ đắt nhất.
    """
    ket_qua = run_cost_from_trace([_event(seq=1, cost=0.0, tokens=Tokens(prompt=100, completion=0))])

    assert ket_qua.priced is False, "run có prompt token mà chưa áp giá vẫn là *chưa nối giá*"
    assert ket_qua.prompt_tokens == 100
    assert ket_qua.completion_tokens == 0


def test_priced_false_khi_chi_co_completion_token() -> None:
    """`Σprompt == 0`, `Σcompletion > 0`, `Σcost == 0` ⇒ `priced is False`.

    ## Nói thẳng: bài này là VỆ SINH MUTATION, không phải ca miền tới được

    Khác bài trên. `prompt` dựng từ câu hỏi + chunk đã truy xuất, nên `len(prompt.split()) == 0`
    thực tế **không xảy ra** trong flow hiện tại — một run có completion mà không có prompt là trạng
    thái không tới được.

    Giữ nó vì nó là bài **duy nhất** giết mutant `priced drop-completion`
    (`prompt_tokens > 0`): với fixture chỉ-prompt ở trên, mutant đó vẫn cho `priced=False` đúng, nên
    không bị bắt. Cần đúng chiều còn lại mới bịt được.

    Ghi rõ nhãn *vệ sinh* thay vì để trống, vì một bài canh trạng thái không tới được mà **trông
    như** ca vận hành sẽ khiến người sau đọc sai miền đầu vào của hàm — và nếu ngày nào đó `prompt`
    thật sự có thể bằng 0 thì đó là một thay đổi đáng phải nhận ra, không phải một bài test đã lo hộ.
    """
    ket_qua = run_cost_from_trace([_event(seq=1, cost=0.0, tokens=Tokens(prompt=0, completion=100))])

    assert ket_qua.priced is False
    assert ket_qua.prompt_tokens == 0
    assert ket_qua.completion_tokens == 100


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
