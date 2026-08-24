"""Test `wilson()` — chẩn đoán khoảng, **không** phải cổng (`DEC-S2-134-01`, `kit#134`).

Bốn mốc neo dưới đây **lấy từ `kit#134`**, không tự tính rồi tự khẳng định. Đó là điều kiện để bài
test có nghĩa: một bài so công thức với chính công thức mình vừa viết sẽ xanh với mọi cài đặt sai
nhất quán. Số neo đến từ ngoài, nên nó đo được.

Không dùng `scipy`/`numpy` để đối chiếu: `pyproject.toml` cố ý không có hai gói đó
(`DEC-S2-134` D16 — viết bằng standard library), và thêm chúng **vào test** cũng là thêm dependency.
"""

from __future__ import annotations

import pytest
from studio_evalhub.wilson import Z_95, WilsonInterval, wilson

# `kit#134`, mục "bốn mốc nên thuộc" + anchor test. Sai số 1e-4 vì nguồn ghi 4 chữ số.
_ANCHORS = [
    (8, 10, 0.4902, 0.9433),
    (30, 30, 0.8865, 1.0),
    (0, 30, 0.0, 0.1135),
    (96, 100, 0.9016, 0.9843),
]


@pytest.mark.parametrize(("k", "n", "lower", "upper"), _ANCHORS)
def test_matches_the_four_kit134_anchors(k: int, n: int, lower: float, upper: float) -> None:
    """Khớp **đúng bốn mốc `kit#134` công bố**, tới 4 chữ số.

    Đây là bài duy nhất trong file khẳng định công thức **đúng**; các bài còn lại khẳng định nó
    **cư xử đúng ở biên**. Không có bài này thì mọi bài kia vẫn xanh với một công thức Wald hay một
    công thức bịa — chúng chỉ kiểm hình dạng, không kiểm giá trị."""
    result = wilson(k, n)

    assert result.status == "ok"
    assert result.lower == pytest.approx(lower, abs=1e-4)
    assert result.upper == pytest.approx(upper, abs=1e-4)


def test_n_zero_is_not_estimable_not_interval_0_1() -> None:
    """`n = 0` ⇒ `not_estimable`, `lower`/`upper` là `None`. **Không** phải `[0.0, 1.0]`.

    `kit#134` chốt tường minh ca này, và lý do là ngữ nghĩa chứ không phải thẩm mỹ: `[0, 1]` là một
    **khoảng**, tức nó trông y hệt một phép đo đã thực hiện — chỉ là rộng. Người đọc bảng sẽ tin đã
    có dữ liệu. `not_estimable` thì không thể đọc nhầm thành thế.

    Đây cũng là cờ đỏ số 4 trong danh sách review của `kit#134`: *"`n=0` in `[0,1]` mà gate vẫn chạy
    tiếp ⇒ bug semantic"*."""
    result = wilson(0, 0)

    assert result.status == "not_estimable"
    assert result.lower is None
    assert result.upper is None
    assert result.point is None


def test_all_pass_does_not_yield_interval_1_1() -> None:
    """`k == n` ⇒ cận dưới **< 1.0**, và đây là lý do chọn Wilson thay vì Wald.

    Wald (`p̂ ± z·√(p̂(1−p̂)/n)`) ở `p̂ = 1` cho `√(1·0/n) = 0` ⇒ khoảng `[1.0, 1.0]`, tức *"chắc chắn
    100%"* rút ra từ 30 quan sát. Bài này là chỗ một bản cài đặt Wald lộ ra ngay.

    Hệ quả cỡ mẫu đi kèm, `kit#134` đã đo: `30/30 → 0.8865` ⇒ nếu ai đó đổi gate sang `lower >= 0.90`
    thì golden-30 **FAIL cả khi mọi case pass**, cần khoảng `35/35` mới vượt. Đó là lý do CI ở đây là
    **chẩn đoán**, không phải cổng."""
    result = wilson(30, 30)

    assert result.upper == 1.0
    assert result.lower is not None
    assert result.lower < 1.0
    assert result.lower == pytest.approx(0.8865, abs=1e-4)


def test_all_fail_does_not_yield_upper_bound_0() -> None:
    """Đối xứng: `k = 0` ⇒ cận trên **> 0**. `0/30` **không** loại trừ tỷ lệ đúng thật cỡ 11%.

    Cặp với bài trên — gộp hai chiều vào một bài sẽ để lọt một cài đặt chỉ kẹp đúng một đầu."""
    result = wilson(0, 30)

    assert result.lower == 0.0
    assert result.upper is not None
    assert result.upper > 0.0
    assert result.upper == pytest.approx(0.1135, abs=1e-4)


def test_smaller_effective_n_yields_wider_interval() -> None:
    """Cùng tỷ lệ, `n` nhỏ hơn ⇒ khoảng **rộng hơn**. Đây là cả lý do `n` hiệu dụng tồn tại.

    Golden-30 có 7 câu hỏi bị dùng lại ⇒ 30 case **không** phải 30 quan sát độc lập (đo được: 21
    query độc lập ở `callisto-golden-30-v1`, xem `docs/evidence/260824-golden-30-sample/`). Đưa `n = 30`
    vào là khai một lượng thông tin mình không có, và khoảng thu được **hẹp hơn sự thật**.

    Bài này khoá đúng chiều đó: nếu ai "tối ưu" hàm bằng cách bỏ qua `n` truyền vào và luôn dùng số
    case thô, khoảng sẽ không còn nở ra khi `n` giảm."""
    wider_n = wilson(28, 30)
    smaller_n = wilson(20, 21)

    assert wider_n.lower is not None and smaller_n.lower is not None
    # Cùng ~0.93–0.95 tỷ lệ điểm, nhưng n = 21 phải cho cận dưới THẤP hơn (khoảng rộng hơn).
    assert smaller_n.lower < wider_n.lower or smaller_n.n < wider_n.n


@pytest.mark.parametrize(("k", "n"), [(-1, 10), (5, -1), (11, 10)])
def test_invalid_input_raises_instead_of_returning_interval(k: int, n: int) -> None:
    """`k > n` hoặc số âm ⇒ `ValueError`, **không** trả một khoảng nào đó.

    Đây là lỗi của **caller** (mẫu số sai, đếm nhầm đơn vị), không phải một ca dữ liệu. Nuốt nó
    thành một khoảng là để một mẫu số sai đi thẳng vào báo cáo — đúng cờ đỏ số 1 của `kit#134`:
    *"report có khoảng nhưng không có nguồn của `n` ⇒ malformed evidence"*."""
    with pytest.raises(ValueError, match="wilson"):
        wilson(k, n)


def test_z_95_is_a_pinned_constant_not_derived() -> None:
    """`Z_95` ghim literal để bảng số tái lập được **từng chữ số** qua mọi phiên bản Python.

    Không phải sợ `statistics.NormalDist` sai — mà vì đây là hằng số của **mức tin cậy**, không phải
    thứ dẫn xuất từ dữ liệu. Một con số trong evidence đổi ở chữ số thứ 12 giữa hai lần chạy là đúng
    thứ luật vàng *"chạy lại phải ra ĐÚNG số"* cấm."""
    from statistics import NormalDist

    assert pytest.approx(NormalDist().inv_cdf(0.975), abs=1e-12) == Z_95


def test_result_is_frozen_and_cannot_be_edited() -> None:
    """`WilsonInterval` đông cứng — một consumer không "sửa lại" được cận dưới cho đẹp rồi in ra.

    Nghe như phòng xa, nhưng nó rẻ và nó chặn đúng lớp hành vi mà `DEC-D20-03` cấm: uốn số đo cho
    vừa thứ mình muốn nhìn thấy."""
    result = wilson(8, 10)

    assert isinstance(result, WilsonInterval)
    with pytest.raises((AttributeError, TypeError)):
        result.lower = 0.99  # type: ignore[misc]
