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


def _golden(*cases: GoldenCase) -> GoldenSet:
    return GoldenSet(golden_set_ref="golden-thu", cases=list(cases))


# ---------------------------------------------------------------------------
# 1. Luật ba tầng
# ---------------------------------------------------------------------------


def test_declared_critical_cases_are_never_trimmed_to_fit_budget() -> None:
    """**Bài đắt nhất file.** 30 case critical với `max_cases=5` ⇒ cả 30 vẫn vào, và bộ khai vượt.

    `is_critical` nghĩa là *"sai case này thì cả lượt chấm hỏng"*. Cắt nó cho vừa ngân sách là bỏ
    đúng thứ mà ngân sách tồn tại để bảo vệ. Một bản cài đặt `chon[:max_cases]` sẽ xanh ở mọi bài
    khác trong file và chỉ đỏ ở đây."""
    golden = _golden(*[_refusal(f"BAY-{i:02d}") for i in range(30)], *[_answer(f"TL-{i:02d}") for i in range(20)])

    result = select_core(golden, max_cases=5, min_answer=2)

    assert sum(1 for c in result.golden.cases if c.expects_refusal) == 30, "case critical bị cắt bớt"
    assert result.over_budget is True, "vượt ngân sách phải được KHAI, không im lặng"
    assert result.n_declared == 30


def test_guarantees_enough_answer_cases_even_when_tier_one_fills_budget() -> None:
    """40 case bẫy đã khai + `max_cases=40` ⇒ vẫn phải kéo thêm case trả-lời vào.

    Đây đúng hình dạng bộ **sinh máy**: `build_cases` gán `tier="core"` cho toàn bộ case bẫy. Không
    có tầng 2, Core sẽ là 40 case bẫy và cổng đo **một trục**, `success_rate` nói về chuyện khác."""
    golden = _golden(*[_refusal(f"BAY-{i:02d}") for i in range(40)], *[_answer(f"TL-{i:02d}") for i in range(30)])

    result = select_core(golden, max_cases=40, min_answer=10)

    assert result.n_answer == 10
    assert result.n_refusal == 40
    assert result.over_budget is True


def test_set_smaller_than_budget_is_taken_whole() -> None:
    """Bộ người viết (30 case, 0 khai `tier`) phải vào trọn — không rơi vào nhánh rỗng."""
    golden = _golden(
        *[_answer(f"TL-{i:02d}") for i in range(22)],
        *[_refusal(f"BAY-{i:02d}", is_critical=None, tier=None) for i in range(8)],
    )

    result = select_core(golden, max_cases=DEFAULT_MAX_CASES)

    assert len(result.golden.cases) == 30
    assert result.n_declared == 0, "bộ này không case nào khai critical/core — đúng như bộ thật"
    assert result.over_budget is False


def test_order_follows_original_set_and_is_deterministic() -> None:
    """Cùng bộ vào ⇒ cùng Core ra, và theo thứ tự GỐC chứ không thứ tự nhặt.

    Core nhảy giữa hai lượt nghĩa là hai lần bấm Publish trên cùng dữ liệu chấm trên hai tập khác
    nhau — và chênh lệch đó không phân biệt được với chênh lệch do agent."""
    golden = _golden(
        _answer("TL-01"),
        _refusal("BAY-01"),
        _answer("TL-02"),
        _refusal("BAY-02"),
        *[_answer(f"TL-{i:02d}") for i in range(3, 15)],
    )

    first = select_core(golden, max_cases=8, min_answer=3)
    second = select_core(golden, max_cases=8, min_answer=3)

    ids = [c.case_id for c in first.golden.cases]
    assert ids == [c.case_id for c in second.golden.cases], "không tất định"
    original = [c.case_id for c in golden.cases]
    assert ids == [i for i in original if i in set(ids)], f"lệch thứ tự gốc: {ids}"


def test_two_core_declaration_axes_are_independent_critical_needs_no_tier() -> None:
    """`is_critical=True` **không kèm** `tier` vẫn phải vào Core, và ngược lại.

    Hai trục khai hai chuyện khác nhau (`GoldenCase`): `is_critical` là *"sai case này thì cả lượt
    chấm hỏng"*, `tier` là *"chạy lúc gate hay chạy nền"*. Một bản cài đặt chỉ đọc **một** trục vẫn
    xanh ở mọi bài khác trong file, vì fixture `_refusal()` mặc định khai CẢ HAI — đo được: mutant
    bỏ vế `is_critical` sống sót 8/8 bài trước khi có bài này. Fixture đối xứng không phân biệt được
    hai vế của một phép `or`.
    """
    only_critical = _refusal("CHI-CRIT", is_critical=True, tier=None)
    only_tier = _refusal("CHI-TIER", is_critical=None, tier="core")
    undeclared = _refusal("KHONG-KHAI", is_critical=None, tier=None)
    golden = _golden(only_critical, only_tier, undeclared, *[_answer(f"TL-{i:02d}") for i in range(30)])

    result = select_core(golden, max_cases=3, min_answer=1)
    in_core = {c.case_id for c in result.golden.cases}

    assert "CHI-CRIT" in in_core, "case khai is_critical mà không khai tier vẫn phải vào Core"
    assert "CHI-TIER" in in_core, "case khai tier=core mà không khai is_critical vẫn phải vào Core"
    assert result.n_declared == 2, f"đúng 2 case đã khai, thấy {result.n_declared}"
    assert "KHONG-KHAI" not in in_core, (
        "case KHÔNG khai trục nào mà vẫn vào tầng 1 thì `n_declared` mất nghĩa — ngân sách đã đầy "
        "bởi 2 case khai + 1 case trả-lời bảo đảm"
    )


# ---------------------------------------------------------------------------
# 2. Fail-closed
# ---------------------------------------------------------------------------


def test_all_trap_set_raises_instead_of_gating_on_one_axis() -> None:
    """Bộ không có case trả-lời nào ⇒ `CoreSelectionError`, và thông điệp chỉ đúng chỗ hỏng.

    Ném chứ không trả bộ lệch: cổng Publish fail-closed (`INV-6`), và `success_rate` trên tập
    chỉ-toàn-bẫy là *"một giá trị trông hợp lệ"* — đúng thứ `GoldenSetNotFound` được dựng để từ chối."""
    golden = _golden(*[_refusal(f"BAY-{i:02d}") for i in range(12)])

    with pytest.raises(CoreSelectionError) as raised:
        select_core(golden)

    message = str(raised.value)
    assert "0 case trả-lời" in message
    assert "thiếu ở chính bộ golden" in message, "phải chỉ ra hỏng ở BỘ, không phải ở luật chọn"


def test_empty_set_raises() -> None:
    with pytest.raises(CoreSelectionError, match="mẫu số 0"):
        select_core(GoldenSet(golden_set_ref="rong", cases=[]))


def test_invalid_max_cases_raises_ValueError() -> None:
    with pytest.raises(ValueError, match="max_cases"):
        select_core(_golden(_answer("TL-01")), max_cases=0)


# ---------------------------------------------------------------------------
# 3. Neo vào bộ THẬT — lý do module này tồn tại
# ---------------------------------------------------------------------------


def _corpus() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2] / "kb" / "src" / "studio_kb" / "golden"


def test_real_human_set_declares_no_tier_so_naive_filtering_yields_EMPTY() -> None:
    """Neo số đo đã dùng để chọn thiết kế: bộ production **0 case khai `tier`**.

    Nếu ai đó thay `select_core` bằng `[c for c in golden.cases if c.tier == "core"]`, bộ này cho
    Core **rỗng** và cổng chấm trên mẫu số 0. Bài này giữ cho lập luận đó neo vào dữ liệu, không
    vào trí nhớ."""
    thu_muc = _corpus()
    if not thu_muc.is_dir():  # pragma: no cover — chỉ khi chạy evalhub tách khỏi workspace
        pytest.skip(f"không thấy corpus golden ở {thu_muc}")
    ref = "callisto-2.0-golden-30-v1"
    golden = load_golden_set(thu_muc / f"{ref}.yaml", expect_ref=ref)

    assert [c for c in golden.cases if c.tier == "core"] == [], (
        "bộ người viết mà có case khai tier=core thì lập luận 'lọc thẳng sẽ rỗng' đã hết đúng — "
        "đọc lại docstring module trước khi sửa bài này"
    )

    result = select_core(golden)

    assert len(result.golden.cases) == 30, "bộ 30 case phải vào trọn, không rơi vào nhánh rỗng"
    assert result.n_answer == 22
    assert result.n_refusal == 8


def test_duplicate_case_id_in_core_raises_instead_of_reaching_the_gate() -> None:
    """`GoldenSet` KHÔNG ép `case_id` duy nhất — bộ sinh máy và bộ người nộp đặt id độc lập nhau nên
    đụng được (xem `golden_merge.py`). Hai case cùng id mà khác CHẤT (một từ-chối, một trả-lời) là
    bộ không chấm đúng được: `EvalHarness.run` chỉ thêm case không-từ-chối vào `scored_case_ids`,
    còn `compute_scorecard` lọc bằng `r.case_id in scored_case_ids` — nên `CaseResult` của case
    từ-chối bị kéo vào mẫu `citation_accuracy` của nhánh trả-lời và làm hỏng đúng con số cổng đọc.

    Nén nó ở đây thay vì để cổng trả một số trông hợp lệ (review evalhub#52, Dozyboy).
    """
    golden = _golden(
        _refusal("DUP-1", is_critical=True),
        _answer("DUP-1"),
        *[_answer(f"TL-{i:02d}") for i in range(12)],
    )

    with pytest.raises(CoreSelectionError, match="case_id trùng"):
        select_core(golden, max_cases=40, min_answer=10)


def test_unique_case_ids_are_not_rejected() -> None:
    """Chốt chống rỗng-nghĩa cho bài trên: cùng hình dạng bộ, chỉ khác mỗi id, phải đi lọt."""
    golden = _golden(
        _refusal("BAY-1", is_critical=True),
        _answer("TL-RIENG"),
        *[_answer(f"TL-{i:02d}") for i in range(12)],
    )

    result = select_core(golden, max_cases=40, min_answer=10)

    ids = [c.case_id for c in result.golden.cases]
    assert len(ids) == len(set(ids))


def test_invalid_min_answer_raises_ValueError() -> None:
    """`min_answer < 1` làm điều kiện `n_answer < min_answer` không bao giờ đúng được — tức tắt hẳn
    chốt fail-closed của module, một Core 0 case trả-lời sẽ đi lọt. `select_core` là symbol công
    khai nên phải tự chặn, không dựa vào `EvalHarness.run` luôn truyền mặc định."""
    golden = _golden(*[_refusal(f"BAY-{i:02d}") for i in range(12)])

    for bad in (0, -1):
        with pytest.raises(ValueError, match="min_answer"):
            select_core(golden, min_answer=bad)
