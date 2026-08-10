"""Test tầng RENDER — `_render` (bảng smoke) + `render_scorecard` (khung Scorecard). D12, `kit#88`.

KHÓA hai luật, cả hai đều là *"không được in một con số mà mình không đo"*:

1. **Dòng từ-chối in `n/a`, không in `1.00`** — clause §3 phần 3 `scorecard.v1.md` (DEC-04, D11) tự
   hẹn land D12. Giá trị `1.0` trên object **giữ nguyên** (pin test D11 khoá nó); chỉ hiển thị đổi.
2. **Ô chưa đo được in `todo:`, không in `0.00`** (DEC-D12-02). `0.00` đọc thành *"đã đo, và bằng 0"*
   ⇒ người xem demo tưởng gate đang chặn. Cùng lớp lỗi với hằng số `Judge` mà `judge.py:6-9` cấm.

Bài ở đây **không** gọi `compute_scorecard` (mốc D16) — có một bài khoá đúng chuyện đó.
"""

from __future__ import annotations

import pytest
from studio_contracts import Aggregate, CaseResult, Gate, GateThreshold, Scorecard
from studio_evalhub.cli import _render
from studio_evalhub.compute import compute_scorecard
from studio_evalhub.harness import SmokeResult
from studio_evalhub.render import render_scorecard


def _answered(*, case_id: str = "SC-01", accuracy: float = 0.5, success: bool = True) -> SmokeResult:
    return SmokeResult(
        case_id=case_id,
        expected="12 ngày",
        actual="Được nghỉ 12 ngày.",
        success=success,
        citation_accuracy=accuracy,
        expects_refusal=False,
    )


def _refused(*, case_id: str = "SC-04", success: bool = True) -> SmokeResult:
    """Case từ-chối — `citation_accuracy` LUÔN 1.0 theo quy ước (`harness.py:172`), kể cả khi FAIL."""
    return SmokeResult(
        case_id=case_id,
        expected="refusal",
        actual="Tôi không có quyền truy cập.",
        success=success,
        citation_accuracy=1.0,
        expects_refusal=True,
    )


# ---------------------------------------------------------------------------
# 1. `_render` — dòng từ-chối `n/a` (DEC-04 phần 3, hạn D12)
# ---------------------------------------------------------------------------


def test_render_dong_tra_loi_van_in_so_hai_chu_so() -> None:
    """HAPPY: nhánh trả-lời **phải** in số. Bài này là vế đối chứng của bài `n/a` bên dưới — thiếu nó
    thì một bản vá in `n/a` cho MỌI dòng cũng xanh, và lúc đó bảng điểm mất toàn bộ thông tin."""
    out = _render([_answered(accuracy=0.5)])

    assert "0.50" in out
    assert "trả-lời" in out
    assert "n/a" in out  # chỉ trong dòng chú thích cuối
    body = [ln for ln in out.splitlines() if ln.startswith("SC-01")]
    assert len(body) == 1
    assert "n/a" not in body[0], "dòng trả-lời KHÔNG được in n/a"


def test_render_dong_tu_choi_in_n_a_chu_khong_in_1_00() -> None:
    """NEGATIVE (bài chính của D12): dòng từ-chối in `n/a`; `1.00` **không** xuất hiện trên dòng đó.

    Đây là chỗ clause §3 phần 3 của hợp đồng FROZEN đổ bộ vào code. Bài này đỏ nghĩa là bảng
    người-đọc lại mời người đọc cộng một con số không đo được vào trung bình đầu — cơ chế thổi phồng
    `aggregate` mà GUIDE-C Q8 chỉ ra (`0.90` báo vs `0.833` thật).

    Vế đắt: case từ-chối **đã FAIL** cũng in `n/a`. Trước đây nó in `1.00` — một dòng đỏ mang theo
    con số đẹp nhất bảng."""
    out = _render([_refused(success=True), _refused(case_id="SC-07", success=False)])

    for case_id in ("SC-04", "SC-07"):
        row = next(ln for ln in out.splitlines() if ln.startswith(case_id))
        assert "n/a" in row, f"{case_id}: dòng từ-chối phải in n/a"
        assert "1.00" not in row, f"{case_id}: dòng từ-chối KHÔNG được in 1.00"
        assert "từ-chối" in row

    assert "FAIL" in out and "PASS" in out


def test_render_khong_doi_gia_tri_tren_object_chi_doi_hien_thi() -> None:
    """`citation_accuracy` trên object **vẫn là `float` 1.0** sau khi render.

    Vì sao khoá: cách sửa "hiển nhiên" cho `n/a` là đổi kiểu field sang `float | None`. Làm vậy sẽ
    `TypeError` ở 3 renderer format `:.2f` (`smoke_eval_d6.py:219` — file của DE ·
    `e2e_smoke_eval.py:294` · `cli.py`), và phá pin test D11
    `test_refusal_citation_accuracy_is_pinned_convention_not_measurement`. Bài này khoá rằng D12 đổi
    **tầng render**, không đổi **tầng dữ liệu**."""
    r = _refused()
    _render([r])

    assert r.citation_accuracy == 1.0
    assert isinstance(r.citation_accuracy, float)


def test_render_co_dong_chu_thich_noi_n_a_nghia_la_gi() -> None:
    """`n/a` không tự giải thích ⇒ bảng phải nói nó nghĩa gì, kèm hệ quả (không cộng vào mẫu số).

    Một ký hiệu không có chú thích thì người đọc sẽ tự đoán, và đoán phổ biến nhất là *"đo được 0"* —
    đúng thứ `n/a` sinh ra để tránh."""
    out = _render([_refused()])

    assert "quy ước" in out
    assert "aggregate" in out
    assert "DEC-04" in out


# ---------------------------------------------------------------------------
# 2. `render_scorecard` — khung TRỐNG có `todo:` (DEC-D12-02)
# ---------------------------------------------------------------------------


def test_render_scorecard_trong_in_todo_va_khong_in_bat_ky_0_00() -> None:
    """Bài chính của DEC-D12-02: chưa có golden-set ⇒ in `todo:`, và **0 lần** xuất hiện `0.00`.

    `0.00` đọc thành *"đã đo, và bằng 0"*: người xem demo sẽ tưởng gate đang chặn thật. Bài này đỏ
    nghĩa là ai đó đã điền một giá trị mặc định vào ô chưa đo được — cùng lớp lỗi với hằng số
    `Judge(agreement=1.0)` mà `judge.py:6-9` cấm."""
    out = render_scorecard(None)

    assert "0.00" not in out, "ô chưa đo được KHÔNG được in 0.00"
    assert "PASS" not in out and "FAIL" not in out, "chưa đo thì chưa có verdict"
    assert out.count("todo:") >= 5


def test_render_scorecard_trong_van_in_du_TEN_moi_o_D16_phai_dien() -> None:
    """Khung trống vẫn phải nêu **tên** mọi ô, vì giá trị của deliverable D12 là khoá **hình dạng
    output trước khi có dataset** (GUIDE-C §3.2: ngưỡng phải có trước dataset).

    Thiếu bài này thì "render trống" có thể được thoả bằng một chuỗi rỗng — và một chuỗi rỗng không
    khoá gì cho D16.

    **D15/T4 — H5: bất biến cưỡng chế bằng CODE, không bằng chữ.** Bản D12 của bài này gõ tay 6 tên
    ô. Bài khai *"mọi ô"* mà danh sách do người viết nhớ ra thì nó chỉ khoá được đúng những ô người
    viết nhớ — thêm ô thứ 7 vào hợp đồng là nó rơi im lặng, và không có bài nào đỏ. Đó đúng cái bẫy
    đã dính ở D12 khi `SmokeResult` được thêm field thứ 6.

    Chỗ này đắt hơn bình thường vì **ô thứ 7 đã có tên và có hạn**: `DEC-04` (D11) và
    `DEC-S2-134-03` nợ `Aggregate.n_scored_citation`, hạn **D16 — ngày mai**. Với bản gõ tay, ngày
    thêm field đó vào contract là ngày khung trống lặng lẽ thiếu một ô. Với bản này, nó đỏ ngay và
    người thêm buộc phải quyết khung trống hiển thị nó thế nào.

    Danh sách lấy từ `model_fields` của chính hợp đồng. `results` cố ý không nằm trong tập kiểm: nó
    là danh sách per-case, khung trống báo nó bằng dòng đếm *"case đã chấm"* chứ không bằng tên
    field — nên nó được khai là **ngoại lệ có lý do**, không phải bị quên."""
    out = render_scorecard(None)

    # Ô nào không in TÊN field, kèm lý do. Khai tường minh để "ngoại lệ" khác hẳn "bỏ sót":
    # thêm field mới mà muốn miễn thì phải viết lý do vào đây, không im lặng bỏ qua được.
    khong_in_ten_field = {
        "golden_set_ref": "in ở dòng tiêu đề (`SCORECARD — ...`), không in dưới dạng tên ô",
        "results": "danh sách per-case — báo bằng dòng đếm `case đã chấm`, không bằng tên field",
    }

    for field in Scorecard.model_fields:
        if field in khong_in_ten_field:
            continue
        assert field in out, f"khung trống thiếu tên ô {field}"

    for field in Aggregate.model_fields:
        assert f"aggregate.{field}" in out, f"khung trống thiếu tên ô aggregate.{field}"

    for field in Gate.model_fields:
        assert f"gate.{field}" in out, f"khung trống thiếu tên ô gate.{field}"

    # Và tập miễn phải thật sự là field của hợp đồng — một lý do viết cho field không tồn tại nghĩa
    # là field đã bị đổi tên và cái miễn này đang che một ô thật.
    assert set(khong_in_ten_field) <= set(Scorecard.model_fields), (
        f"khai miễn cho field không có trong Scorecard: {set(khong_in_ten_field) - set(Scorecard.model_fields)}"
    )


def test_render_scorecard_trong_noi_ro_VI_SAO_trong() -> None:
    """Một bảng trống không có lý do sẽ bị đọc là *"chạy lỗi"*. Phải nói: chưa có golden-set thật, và
    `compute_scorecard` là mốc D16 — tức trống **có chủ ý**, không phải hỏng."""
    out = render_scorecard(None)

    assert "chưa có golden-set" in out
    assert "D16" in out
    assert "kit#88" in out


def test_render_scorecard_KHONG_goi_compute_scorecard() -> None:
    """DEC-D12-03: render **không** tự tính. Khoá bằng chứng cứng: `compute_scorecard` vẫn raise.

    Nếu một bản vá sau này cho render gọi `compute_scorecard`, thì hoặc bài này đỏ (vì raise), hoặc
    `compute_scorecard` đã được hiện thực sớm — cả hai đều là thứ phải nhìn thấy, không được trôi."""
    with pytest.raises(NotImplementedError):
        compute_scorecard(
            agent_id="a",
            golden_set_ref="g",
            results=[],
            threshold_success=0.9,
            threshold_citation_accuracy=0.95,
            # D16: tham số mới của `compute_scorecard` (DEC-D16-03 đường (b)) — caller nói nhánh nào
            # được chấm citation. `results=[]` nên tập rỗng là giá trị đúng; bài này không đổi mục
            # đích, vẫn chỉ khoá "renderer KHÔNG gọi sang tầng tính".
            scored_case_ids=set(),
        )

    assert "todo:" in render_scorecard(None)


def test_render_scorecard_co_so_thi_in_dung_so_cua_no() -> None:
    """HAPPY của nhánh có dữ liệu: `Scorecard` dựng **bằng tay** (không qua `compute_scorecard`) ⇒ in
    đúng số của nó, kèm dấu `*` + chú thích rằng `aggregate` không tính lại được từ `results`.

    Chú thích đó là nợ D16 đã ghi trong hợp đồng (DEC-04): `CaseResult` không mang cờ nhánh từ-chối
    nên ở tầng hợp đồng không phân biệt được `1.0` là quy ước hay phép đo. Không nói ra thì người đọc
    sẽ tưởng có thể tự cộng lại và đối chiếu."""
    sc = Scorecard(
        agent_id="agent-x",
        golden_set_ref="callisto-smoke-5-v0",
        results=[
            CaseResult(case_id="SC-01", expected="12 ngày", actual="12 ngày", success=True, citation_accuracy=1.0)
        ],
        aggregate=Aggregate(success_rate=0.8, citation_accuracy=0.833),
        gate=Gate(threshold=GateThreshold(success=0.9, citation_accuracy=0.95), verdict="FAIL"),
    )

    out = render_scorecard(sc)

    assert "agent-x" in out
    assert "callisto-smoke-5-v0" in out
    assert "0.80" in out and "0.83" in out
    assert "FAIL" in out
    assert "0.90" in out and "0.95" in out  # ngưỡng in ra được, không giấu
    assert "todo:" in out  # recipe_hash None ⇒ vẫn là todo, KHÔNG in "None"
    assert "fail-closed" in out
    assert "tính lại được" in out
