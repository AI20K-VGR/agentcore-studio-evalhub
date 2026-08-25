"""`core_set.select_core` — tập con mà cổng Publish chạy trong một request.

Ba nhóm, ba kiểu hỏng khác nhau:

1. **luật ba tầng** — case đã khai critical/core không bao giờ bị cắt cho vừa ngân sách;
2. **fail-closed** — Core không đo nổi cả hai trục thì ném, không trả một bộ lệch;
3. **neo vào bộ THẬT** — hai loại bộ đang tồn tại (sinh máy · người viết) hỏng theo hai kiểu
   ngược nhau nếu chỉ lọc `tier == "core"`, và đó là lý do module này tồn tại.
"""

from __future__ import annotations

import pathlib

import pytest
from studio_evalhub.core_set import (
    DEFAULT_MAX_CASES,
    CoreSelectionError,
    select_core,
)
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.golden_loader import load_golden_set


def _answer(case_id: str, *, is_critical: bool | None = None, tier: str | None = None) -> GoldenCase:
    """Case **trả-lời được**: `expected_tenant == tenant` và vai khớp ⇒ `expects_refusal is False`."""
    return GoldenCase(
        case_id=case_id,
        query=f"Câu hỏi {case_id}?",
        tenant="ankor",
        section_roles=["hr"],
        expected_tenant="ankor",
        expected_section_role="hr",
        expected="Đáp án.",
        expected_citation=["ankor-hr-001#c1"],
        is_critical=is_critical,
        tier=tier,
    )


def _refusal(case_id: str, *, is_critical: bool | None = True, tier: str | None = "core") -> GoldenCase:
    """Case **hàng rào**: hỏi dưới `hr` mà đáp án ở `finance` ⇒ `expects_refusal is True`."""
    return GoldenCase(
        case_id=case_id,
        query=f"Câu bẫy {case_id}?",
        tenant="ankor",
        section_roles=["hr"],
        expected_tenant="ankor",
        expected_section_role="finance",
        expected="refusal",
        expected_citation=[],
        is_critical=is_critical,
        tier=tier,
    )


def _bo(*cases: GoldenCase) -> GoldenSet:
    return GoldenSet(golden_set_ref="bo-thu", cases=list(cases))


# ---------------------------------------------------------------------------
# 1. Luật ba tầng
# ---------------------------------------------------------------------------


def test_case_da_khai_critical_khong_bao_gio_bi_cat_cho_vua_ngan_sach() -> None:
    """**Bài đắt nhất file.** 30 case critical với `max_cases=5` ⇒ cả 30 vẫn vào, và bộ khai vượt.

    `is_critical` nghĩa là *"sai case này thì cả lượt chấm hỏng"*. Cắt nó cho vừa ngân sách là bỏ
    đúng thứ mà ngân sách tồn tại để bảo vệ. Một bản cài đặt `chon[:max_cases]` sẽ xanh ở mọi bài
    khác trong file và chỉ đỏ ở đây."""
    bo = _bo(*[_refusal(f"BAY-{i:02d}") for i in range(30)], *[_answer(f"TL-{i:02d}") for i in range(20)])

    ket_qua = select_core(bo, max_cases=5, min_answer=2)

    assert sum(1 for c in ket_qua.golden.cases if c.expects_refusal) == 30, "case critical bị cắt bớt"
    assert ket_qua.vuot_ngan_sach is True, "vượt ngân sách phải được KHAI, không im lặng"
    assert ket_qua.n_declared == 30


def test_bao_dam_du_case_tra_loi_ke_ca_khi_tang_mot_da_lap_day_ngan_sach() -> None:
    """40 case bẫy đã khai + `max_cases=40` ⇒ vẫn phải kéo thêm case trả-lời vào.

    Đây đúng hình dạng bộ **sinh máy**: `build_cases` gán `tier="core"` cho toàn bộ case bẫy. Không
    có tầng 2, Core sẽ là 40 case bẫy và cổng đo **một trục**, `success_rate` nói về chuyện khác."""
    bo = _bo(*[_refusal(f"BAY-{i:02d}") for i in range(40)], *[_answer(f"TL-{i:02d}") for i in range(30)])

    ket_qua = select_core(bo, max_cases=40, min_answer=10)

    assert ket_qua.n_answer == 10
    assert ket_qua.n_refusal == 40
    assert ket_qua.vuot_ngan_sach is True


def test_bo_nho_hon_ngan_sach_thi_lay_het() -> None:
    """Bộ người viết (30 case, 0 khai `tier`) phải vào trọn — không rơi vào nhánh rỗng."""
    bo = _bo(
        *[_answer(f"TL-{i:02d}") for i in range(22)],
        *[_refusal(f"BAY-{i:02d}", is_critical=None, tier=None) for i in range(8)],
    )

    ket_qua = select_core(bo, max_cases=DEFAULT_MAX_CASES)

    assert len(ket_qua.golden.cases) == 30
    assert ket_qua.n_declared == 0, "bộ này không case nào khai critical/core — đúng như bộ thật"
    assert ket_qua.vuot_ngan_sach is False


def test_thu_tu_giu_nguyen_theo_bo_goc_va_tat_dinh() -> None:
    """Cùng bộ vào ⇒ cùng Core ra, và theo thứ tự GỐC chứ không thứ tự nhặt.

    Core nhảy giữa hai lượt nghĩa là hai lần bấm Publish trên cùng dữ liệu chấm trên hai tập khác
    nhau — và chênh lệch đó không phân biệt được với chênh lệch do agent."""
    bo = _bo(
        _answer("TL-01"),
        _refusal("BAY-01"),
        _answer("TL-02"),
        _refusal("BAY-02"),
        *[_answer(f"TL-{i:02d}") for i in range(3, 15)],
    )

    lan_1 = select_core(bo, max_cases=8, min_answer=3)
    lan_2 = select_core(bo, max_cases=8, min_answer=3)

    ids = [c.case_id for c in lan_1.golden.cases]
    assert ids == [c.case_id for c in lan_2.golden.cases], "không tất định"
    goc = [c.case_id for c in bo.cases]
    assert ids == [i for i in goc if i in set(ids)], f"lệch thứ tự gốc: {ids}"


def test_hai_truc_khai_core_doc_lap_nhau_critical_khong_can_kem_tier() -> None:
    """`is_critical=True` **không kèm** `tier` vẫn phải vào Core, và ngược lại.

    Hai trục khai hai chuyện khác nhau (`GoldenCase`): `is_critical` là *"sai case này thì cả lượt
    chấm hỏng"*, `tier` là *"chạy lúc gate hay chạy nền"*. Một bản cài đặt chỉ đọc **một** trục vẫn
    xanh ở mọi bài khác trong file, vì fixture `_refusal()` mặc định khai CẢ HAI — đo được: mutant
    bỏ vế `is_critical` sống sót 8/8 bài trước khi có bài này. Fixture đối xứng không phân biệt được
    hai vế của một phép `or`.
    """
    chi_critical = _refusal("CHI-CRIT", is_critical=True, tier=None)
    chi_tier = _refusal("CHI-TIER", is_critical=None, tier="core")
    khong_khai = _refusal("KHONG-KHAI", is_critical=None, tier=None)
    bo = _bo(chi_critical, chi_tier, khong_khai, *[_answer(f"TL-{i:02d}") for i in range(30)])

    ket_qua = select_core(bo, max_cases=3, min_answer=1)
    trong_core = {c.case_id for c in ket_qua.golden.cases}

    assert "CHI-CRIT" in trong_core, "case khai is_critical mà không khai tier vẫn phải vào Core"
    assert "CHI-TIER" in trong_core, "case khai tier=core mà không khai is_critical vẫn phải vào Core"
    assert ket_qua.n_declared == 2, f"đúng 2 case đã khai, thấy {ket_qua.n_declared}"
    assert "KHONG-KHAI" not in trong_core, (
        "case KHÔNG khai trục nào mà vẫn vào tầng 1 thì `n_declared` mất nghĩa — ngân sách đã đầy "
        "bởi 2 case khai + 1 case trả-lời bảo đảm"
    )


# ---------------------------------------------------------------------------
# 2. Fail-closed
# ---------------------------------------------------------------------------


def test_bo_toan_bay_thi_nem_chu_khong_tra_mot_cong_do_mot_truc() -> None:
    """Bộ không có case trả-lời nào ⇒ `CoreSelectionError`, và thông điệp chỉ đúng chỗ hỏng.

    Ném chứ không trả bộ lệch: cổng Publish fail-closed (`INV-6`), và `success_rate` trên tập
    chỉ-toàn-bẫy là *"một giá trị trông hợp lệ"* — đúng thứ `GoldenSetNotFound` được dựng để từ chối."""
    bo = _bo(*[_refusal(f"BAY-{i:02d}") for i in range(12)])

    with pytest.raises(CoreSelectionError) as bat:
        select_core(bo)

    loi = str(bat.value)
    assert "0 case trả-lời" in loi
    assert "thiếu ở chính bộ golden" in loi, "phải chỉ ra hỏng ở BỘ, không phải ở luật chọn"


def test_bo_rong_thi_nem() -> None:
    with pytest.raises(CoreSelectionError, match="mẫu số 0"):
        select_core(GoldenSet(golden_set_ref="rong", cases=[]))


def test_max_cases_khong_hop_le_thi_nem_ValueError() -> None:
    with pytest.raises(ValueError, match="max_cases"):
        select_core(_bo(_answer("TL-01")), max_cases=0)


# ---------------------------------------------------------------------------
# 3. Neo vào bộ THẬT — lý do module này tồn tại
# ---------------------------------------------------------------------------


def _corpus() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2] / "kb" / "src" / "studio_kb" / "golden"


def test_bo_nguoi_viet_that_khong_case_nao_khai_tier_nen_loc_thang_se_RONG() -> None:
    """Neo số đo đã dùng để chọn thiết kế: bộ production **0 case khai `tier`**.

    Nếu ai đó thay `select_core` bằng `[c for c in golden.cases if c.tier == "core"]`, bộ này cho
    Core **rỗng** và cổng chấm trên mẫu số 0. Bài này giữ cho lập luận đó neo vào dữ liệu, không
    vào trí nhớ."""
    thu_muc = _corpus()
    if not thu_muc.is_dir():  # pragma: no cover — chỉ khi chạy evalhub tách khỏi workspace
        pytest.skip(f"không thấy corpus golden ở {thu_muc}")
    ref = "callisto-2.0-golden-30-v1"
    bo = load_golden_set(thu_muc / f"{ref}.yaml", expect_ref=ref)

    assert [c for c in bo.cases if c.tier == "core"] == [], (
        "bộ người viết mà có case khai tier=core thì lập luận 'lọc thẳng sẽ rỗng' đã hết đúng — "
        "đọc lại docstring module trước khi sửa bài này"
    )

    ket_qua = select_core(bo)

    assert len(ket_qua.golden.cases) == 30, "bộ 30 case phải vào trọn, không rơi vào nhánh rỗng"
    assert ket_qua.n_answer == 22
    assert ket_qua.n_refusal == 8
