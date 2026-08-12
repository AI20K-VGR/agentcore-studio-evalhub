"""Dòng cost trên bảng UI-test — `render_run_cases(run_cost=...)`, D19/T3.

## Vì sao lớp render cần bài riêng chứ không dựa vào bài của T2

`run_cost_from_trace` trả **đúng số** đã có 13 bài canh ở `test_run_cost_from_trace.py`. Bộ này canh
thứ khác hẳn: **con số đó có tới được mắt người đọc nguyên vẹn không**. Hai lớp hỏng độc lập nhau —
`E-1` trong failure-mode list của ngày là một bug **chỉ tồn tại ở tầng in** (`{:<6.2f}` biến
`0.000291` thành `0.00`), và không bài nào ở tầng tính nhìn thấy nó.

`DEC-D19-04` chốt tầng so là **giá trị sau `round(·, 6)`**, không phải chuỗi in ra. Hệ quả cho bề mặt
này: in `.6f`. Một renderer in ít chữ số hơn phải **ghi nhãn là bản rút gọn**; bề mặt evalhub không
rút gọn nên không có nhãn nào.
"""

from __future__ import annotations

import inspect
from uuid import UUID

from studio_contracts import Tokens, TraceEvent
from studio_evalhub.harness import SmokeResult
from studio_evalhub.render import render_run_cases
from studio_evalhub.run_report import RunCost, run_cost_from_trace

_RUN_ID = "run-d19-render"
_TENANT = UUID("11111111-1111-1111-1111-111111111111")
_GOLDEN_SET_REF = "golden-30@d19"
_TRACE_SOURCE = "obs.trace_events (test)"


def _results() -> list[SmokeResult]:
    return [
        SmokeResult(
            case_id="HB-01",
            expected="3 ngày làm việc",
            actual="Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
            success=True,
            citation_accuracy=1.0,
            expects_refusal=False,
        )
    ]


def _render(run_cost: RunCost | None) -> str:
    return render_run_cases(
        _results(),
        run_id=_RUN_ID,
        golden_set_ref=_GOLDEN_SET_REF,
        trace_source=_TRACE_SOURCE,
        run_cost=run_cost,
    )


def _dong_cost(out: str) -> str:
    """Rút đúng dòng `cost (Σ, USD)` ra khỏi output.

    Assert substring trên **cả** output là không đáng tin ở bề mặt này: bảng mang một khối caveat
    prose dài, nên `"chưa" in out` khớp `_WHY_RAW_COUNT` (*"`Aggregate` hôm nay **chưa** có chỗ cho
    `n_scored_citation`"*) — một câu không liên quan gì tới cost. Đã dính đúng bẫy đó một lần khi
    viết bộ này (xem docstring `test_in_mau_so_cost_ben_canh_tong`), nên mọi khẳng định về **nội
    dung** dòng cost đi qua đây.
    """
    dong = [d for d in out.splitlines() if d.startswith("cost (Σ, USD)")]
    assert len(dong) == 1, f"phải có đúng 1 dòng cost, thấy {len(dong)}"
    return dong[0]


def _cost(
    *,
    cost: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    event_count: int = 6,
    priced: bool = True,
) -> RunCost:
    return RunCost(
        run_id=_RUN_ID,
        tenant_id=_TENANT,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost=cost,
        event_count=event_count,
        priced=priced,
    )


# ── additive: đường cũ không đổi một byte ───────────────────────────────────────────────────────


def test_khong_truyen_run_cost_thi_output_y_HET_nhu_cu() -> None:
    """`run_cost` **keyword-only, default `None`** — luật additive, không phải phép lịch sự.

    `render_run_cases` là API công khai có consumer **ngoài quadrant**
    (`workbench/dev_playground_server.py:189` gọi `score_run_from_trace` bằng tham số vị trí, cùng
    đường), nên đổi hành vi mặc định là phá hợp đồng của người khác mà họ không chọn — cùng khuôn đã
    áp cho `score_run_from_trace(tenant_ids=...)` ở D18.

    So **toàn bộ chuỗi**, không so từng mảnh: chỉ cần thêm một dòng trắng cũng là đổi output của
    caller cũ.
    """
    cu = render_run_cases(
        _results(), run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE
    )

    assert _render(None) == cu


def test_khong_truyen_run_cost_thi_KHONG_dung_o_cost() -> None:
    """`None` ⇒ không in dòng cost, và cũng **không** in `todo:` (`DEC-D12-02`).

    Không có dữ liệu thì không dựng ô. Một ô `todo:` ở đây sẽ nói *"chỗ này sẽ có cost"* trong khi
    sự thật là caller **không hỏi** cost — hai chuyện khác nhau.
    """
    out = _render(None)

    assert "cost" not in out.lower()
    assert "todo:" not in out


def test_run_cost_la_keyword_only_va_default_None() -> None:
    """Ghim **cơ học**, không ghim bằng lời: gọi bằng tham số vị trí phải không được."""
    tham_so = inspect.signature(render_run_cases).parameters["run_cost"]

    assert tham_so.kind is inspect.Parameter.KEYWORD_ONLY
    assert tham_so.default is None


# ── DEC-D19-04: in .6f, không được làm tròn mất số ──────────────────────────────────────────────


def test_in_du_6_chu_so_khong_lam_tron_mat_cost_that() -> None:
    """`0.000291` phải hiện nguyên, **không** thành `0.00`.

    Đây là `E-1` dựng thành bài: `apps/studio/scripts/e2e_smoke_eval.py:250` in cost bằng
    `{e.cost:<6.2f}`, nên `cost_of(37, 12) = 0.000291` hiển thị thành `0.00` — bảng money-shot của
    demo sẽ nói *run này tốn 0 đồng* trong khi trace ghi có tốn.

    `DEC-D12-02` cấm in `0.00` cho ô **chưa đo**; đây là chiều ngược — in `0.00` cho ô **đã đo** — và
    hại ngang nhau vì người đọc nhận **cùng một chuỗi**.

    Khẳng định đi qua `_dong_cost` chứ không quét cả output: bản đầu viết `assert "0.000291" in out`
    và **xanh dưới mutant `M-C6`** (`.6f` → `.2f`), vì khối caveat `_WHY_COST_PRECISION` do chính
    mình viết có chứa chuỗi `0.000291` để giải thích lỗi này. Mutant tìm ra, không phải người đọc.
    """
    out = _render(_cost(cost=0.000291, prompt_tokens=37, completion_tokens=12))
    dong = _dong_cost(out)

    assert dong.endswith("0.000291"), f"cost thật bị làm tròn — E-1. Dòng: {dong!r}"
    assert dong.split()[-1] != "0.00"


def test_in_du_6_chu_so_cho_tong_le() -> None:
    """`0.011994` — số của bài conformance T2, đi hết đường tới chuỗi in ra.

    Bài này nối lớp tính với lớp in: cùng bộ số, cùng con số kỳ vọng viết tay. Nếu renderer làm tròn
    lại một lần nữa ở tầng in thì `DEC-D19-04` (*tầng so là giá trị*) mất nghĩa.

    Cũng đi qua `_dong_cost` vì cùng lý do bài trên: `_WHY_COST_PRECISION` chứa sẵn chuỗi `0.011994`.
    """
    out = _render(_cost(cost=0.011994, prompt_tokens=1538, completion_tokens=492))

    assert _dong_cost(out).endswith("0.011994")


def test_in_mau_so_cost_ben_canh_tong() -> None:
    """`E-6` — một `Σcost` không kèm mẫu số là bằng chứng dị dạng (`kit#134`).

    `RunCost.event_count` đã mang sẵn con số; mode là **quên in nó**. Bài này là chỗ chặn.

    ## Bản đầu của bài này XANH VACUOUS — giữ lại vết vì nó là bài học, không phải sự cố

    Nguyên văn assert cũ: `assert "6" in out` và `assert "event" in out.lower()`. Cả hai **xanh trên
    một renderer chưa in gì**:

    - `"event"` khớp chính chuỗi fixture `trace_source = "obs.trace_events (test)"`;
    - `"6"` khớp `"D16"` trong khối caveat có sẵn.

    Đúng lớp lỗi vừa gửi finding cho DE ở `kb#22` lượt 3 (*bài xanh im lặng khi ngừng canh*) — nên
    bài này khẳng định **đúng dòng**, với nhãn **và** giá trị dính liền, cộng một đối chứng âm.
    """
    out = _render(_cost(cost=0.011994, prompt_tokens=1538, completion_tokens=492, event_count=6))

    assert "mẫu số cost" in out
    assert "6 event" in out, "mẫu số phải in kèm đơn vị, không phải một số trần lẫn vào caveat"

    # Đối chứng âm: đổi mẫu số ⇒ chuỗi phải đổi theo. Thiếu vế này thì một renderer in hằng số
    # "6 event" vẫn xanh.
    khac = _render(_cost(cost=0.011994, prompt_tokens=1538, completion_tokens=492, event_count=42))
    assert "42 event" in khac
    assert "6 event" not in khac


# ── DEC-D19-05: hai trạng thái của số 0, phân biệt được TRONG output ────────────────────────────


def test_chua_noi_gia_khong_duoc_in_mot_so_0_tran() -> None:
    """`priced=False` ⇒ nhãn *chưa nối giá*, tuyệt đối **không** in `0.000000`.

    Đây là trạng thái của **mọi run thật trong hệ thống hôm nay** (`interpreter.py:438`
    `cost=_NO_COST`). In `0.000000` trần thì báo cáo D19 mang một con số đọc được thành *"chạy 30
    case tốn 0 đồng"*.

    Output phải mang được cả `Σtokens` (bằng chứng có việc đã chạy) lẫn chỗ đang tắc.
    """
    out = _render(_cost(cost=0.0, prompt_tokens=1538, completion_tokens=492, priced=False))
    dong = _dong_cost(out)

    assert "0.000000" not in dong, "chưa nối giá mà in như một phép đo"
    assert "chưa-nối-giá" in dong
    assert "Σtokens=2030" in dong, "phải in Σtokens — bằng chứng có việc đã chạy nhưng chưa ai áp giá"
    assert "kit#121" in dong, "phải trỏ chỗ đang tắc (kit#121 / Q-A), không để người đọc tự đoán"


def test_da_do_bang_0_thi_in_0_000000_chu_khong_phai_chua_do() -> None:
    """`priced=True` với `cost == 0` ⇒ in `0.000000`, **không** gán nhãn *chưa đo*.

    Nửa này hỏng vào đúng ngày emit nối giá: `kb-retrieve`/`tool-call` phát `Tokens(0, 0)` ⇒ giá của
    chúng đúng bằng `0` ⇒ đó là **một phép đo thật**. Gán nhãn *chưa đo* cho nó là lỗi
    `TraceViewer.tsx:50` (`cost === 0 ? "chưa đo"`) sẽ mắc — hôm nay đúng, mai sai.

    Cặp bài này là lý do output phân loại theo `tokens` chứ không theo riêng `cost`.
    """
    out = _render(_cost(cost=0.0, prompt_tokens=0, completion_tokens=0, priced=True))
    dong = _dong_cost(out)

    assert "0.000000" in dong
    assert "chưa" not in dong.lower(), "một phép đo thật bằng 0 bị gán nhãn chưa đo"


def test_hai_trang_thai_so_0_cho_ra_HAI_chuoi_khac_nhau() -> None:
    """Bất biến gộp: cùng `cost == 0`, hai trạng thái phải **phân biệt được trong chính output**.

    Hai bài trên khẳng định từng nhánh. Bài này khẳng định chúng **không hội tụ** — một cài đặt in
    cùng một chuỗi cho cả hai sẽ lọt cả hai bài kia nếu chuỗi đó tình cờ thoả từng assert.
    """
    chua_noi_gia = _render(_cost(cost=0.0, prompt_tokens=1538, completion_tokens=492, priced=False))
    do_that_bang_0 = _render(_cost(cost=0.0, prompt_tokens=0, completion_tokens=0, priced=True))

    assert chua_noi_gia != do_that_bang_0


# ── nối lớp tính ↔ lớp in: số đi hết đường ─────────────────────────────────────────────────────


def test_so_tu_run_cost_from_trace_di_thang_toi_chuoi_in_ra() -> None:
    """Không dựng `RunCost` bằng tay: lấy đúng số `run_cost_from_trace` trả ra rồi tìm nó trong output.

    Bài này bắt lớp lỗi mà `_cost(...)` thủ công không bắt được — renderer đọc **nhầm field** (ví dụ
    in `prompt_tokens` vào ô cost) vẫn qua được các bài trên nếu fixture tay tình cờ trùng số.
    """
    events = [
        TraceEvent(
            event_id=f"{_RUN_ID}-{i}",
            run_id=_RUN_ID,
            agent_id="a",
            tenant_id=_TENANT,
            node_id=f"n{i}",
            node_type="llm-step",
            ts=f"2026-08-13T09:00:0{i}+00:00",
            inputs_hash="stub",
            outputs={},
            tokens=Tokens(prompt=p, completion=c),
            cost=cost,
        )
        for i, (cost, p, c) in enumerate(
            [(0.000291, 37, 12), (0.001578, 211, 63), (0.010125, 1290, 417)], start=1
        )
    ]

    ket_qua = run_cost_from_trace(events)
    out = _render(ket_qua)

    assert ket_qua.cost == 0.011994
    assert f"{ket_qua.cost:.6f}" in out
    assert str(ket_qua.event_count) in out


# ── bề mặt công khai + wiring CLI ───────────────────────────────────────────────────────────────


def test_RunCost_va_run_cost_from_trace_import_duoc_tu_gói() -> None:
    """Bề mặt công khai: `from studio_evalhub import RunCost, run_cost_from_trace`.

    `kit#74` chấm bằng *fresh clone rồi chạy lệnh y nguyên*, nên một tên chỉ import được qua đường
    module con là một tên **không giao**. Đây là một nửa nợ `T9a` (nửa còn lại — 7 tên cũ + lưới
    quét phủ kín — thuộc T6).

    Assert cả ba vế: có trong `__all__`, import được, và **đúng object** (một `__all__` khai tên
    nhưng module không export sẽ chỉ vỡ lúc `from … import *`).
    """
    import studio_evalhub
    from studio_evalhub import RunCost as RunCostGoi
    from studio_evalhub import run_cost_from_trace as ham_goi

    assert "RunCost" in studio_evalhub.__all__
    assert "run_cost_from_trace" in studio_evalhub.__all__
    assert RunCostGoi is RunCost
    assert ham_goi is run_cost_from_trace


def test_all_khong_khai_ten_ma_goi_khong_co() -> None:
    """Mọi tên trong `__all__` phải thật sự tồn tại trên gói — khai suông không tính."""
    import studio_evalhub

    thieu = [ten for ten in studio_evalhub.__all__ if not hasattr(studio_evalhub, ten)]
    assert thieu == [], f"`__all__` khai tên gói không có: {thieu}"


def test_cli_doc_moi_run_dung_MOT_lan_khong_cong_doi_cost() -> None:
    """`--run R1:A --run R1:B` không được làm Σcost nhân đôi.

    Đây là `F-3` (replay double-count) sinh ra từ chính vòng lặp CLI: mỗi spec đọc lại cùng `run_id`
    thì `events` lặp, và `run_cost_from_trace` — vốn **không** có cách nào biết hai bản sao là cùng
    một event — sẽ cộng cả hai.

    Bài này canh helper chọn cost của CLI, không cần Postgres: nó nhận `dict[run_id, events]`, tức
    cấu trúc đã dedupe. Vế thật sự được khẳng định là **hình dạng đó là hình dạng đúng** — một
    `list[events]` phẳng sẽ không phân biệt được.
    """
    from studio_evalhub.run_report import _run_cost_cho_cli

    events = [
        TraceEvent(
            event_id=f"{_RUN_ID}-{i}",
            run_id=_RUN_ID,
            agent_id="a",
            tenant_id=_TENANT,
            node_id=f"n{i}",
            node_type="llm-step",
            ts=f"2026-08-13T09:00:0{i}+00:00",
            inputs_hash="stub",
            outputs={},
            tokens=Tokens(prompt=37, completion=12),
            cost=0.000291,
        )
        for i in (1, 2)
    ]

    mot_run = _run_cost_cho_cli({_RUN_ID: events})

    assert mot_run is not None
    assert mot_run.cost == 0.000582, "hai event × 0.000291 — không phải bốn"
    assert mot_run.event_count == 2


def test_cli_nhieu_run_thi_KHONG_dung_o_cost() -> None:
    """Nhiều run trong một lệnh ⇒ `None`, không phải một tổng gộp chéo run.

    `RunCost` là cost **của một run**. Trả `None` chứ không raise vì `--run` vốn nhận nhiều spec từ
    trước D19 — biến một lệnh đang chạy được thành lỗi là phá hợp đồng CLI để thêm một dòng hiển thị.
    Bảng nhiều run vì thế **không có** dòng cost, và đó là *không có dữ liệu thì không dựng ô*
    (`DEC-D12-02`), không phải cost bằng 0.
    """
    from studio_evalhub.run_report import _run_cost_cho_cli

    def _ev(run_id: str) -> TraceEvent:
        return TraceEvent(
            event_id=f"{run_id}-1",
            run_id=run_id,
            agent_id="a",
            tenant_id=_TENANT,
            node_id="n1",
            node_type="llm-step",
            ts="2026-08-13T09:00:01+00:00",
            inputs_hash="stub",
            outputs={},
            tokens=Tokens(prompt=37, completion=12),
            cost=0.000291,
        )

    assert _run_cost_cho_cli({"r1": [_ev("r1")], "r2": [_ev("r2")]}) is None
    assert _run_cost_cho_cli({}) is None
