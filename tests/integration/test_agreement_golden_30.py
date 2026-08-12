"""Integration — agreement trên **golden-30 THẬT của DE**, không dựng fixture thay thế.

Tách khỏi `tests/test_agreement.py` cùng lý lẽ đã tách loader: bài ở đó chứng minh **hàm** đúng, bài
ở đây chứng minh **hàm chạy được trên dữ liệu đang có** và báo đúng trạng thái của dữ liệu đó.

**Con số ở đây là `kb ↔ evalhub semantic-fence agreement`, KHÔNG phải human–machine agreement.** Xem
docstring `studio_evalhub.agreement` cho lý do đầy đủ; tóm tắt: `manual_label` (kb) và
`expects_refusal` (evalhub) trùng nhau về ngữ nghĩa nhưng được tính bằng hai bản cài đặt độc lập ở
hai repo, nên phép so là **regression detector cho semantic drift**, không phải phép đo người-máy.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from studio_evalhub.agreement import agreement, nhan_tu_golden_set
from studio_evalhub.golden_loader import load_golden_set


def test_agreement_tren_golden_30_khop_so_nhan_thuc_te(golden_30_path: Path, golden_30_ref: str) -> None:
    """Mẫu số phải khớp **số case thực sự có `manual_label` trong file**, đếm độc lập với loader.

    Đếm lại bằng `yaml.safe_load` thô thay vì tin `GoldenCase`: đó là **oracle độc lập**, cùng vai với
    `_REFUSAL_DE_KHAI` ở `test_golden_30_that.py`. Nếu `extra="forbid"`/`manual_label` của T1 hỏng
    theo hướng nuốt câm trở lại, mẫu số sẽ tụt về 0 trong khi file vẫn có nhãn — và bài này bắt được
    đúng chỗ đó, còn một bài chỉ đọc qua loader thì không.

    **Luật `None` được khoá cả hai chiều**, nên bài sống qua ngày `kb#21` merge:

    - chưa case nào có nhãn ⇒ `rate is None`, **không** phải `0.0` (*chưa đo* ≠ *đo được và bằng 0*);
    - có nhãn ⇒ `rate` là số thật trong `[0, 1]`, và mẫu số đúng bằng số nhãn đếm được.

    **Trạng thái đo được lúc viết bài (12/08, D18):** `kb#21` còn OPEN, con trỏ `packages/kb` chưa
    bump ⇒ **0/30** case có nhãn ⇒ `n_compared = 0`, `rate = None`. Đó là lý do ô DoD *"agreement có
    số vs nhãn tay"* **chưa đóng bằng số THẬT** hôm nay — và bài này là chỗ trạng thái đó được ghi
    bằng phép đo thay vì bằng một câu trong báo cáo.
    """
    raw = yaml.safe_load(golden_30_path.read_text(encoding="utf-8"))
    so_nhan_trong_file = sum(1 for case in raw["cases"] if case.get("manual_label") is not None)

    golden = load_golden_set(golden_30_path, expect_ref=golden_30_ref)
    ket_qua = agreement(*nhan_tu_golden_set(golden))

    assert ket_qua.n_compared == so_nhan_trong_file

    if so_nhan_trong_file == 0:
        assert ket_qua.rate is None
        assert ket_qua.lech == []
    else:
        assert ket_qua.rate is not None
        assert 0.0 <= ket_qua.rate <= 1.0
        # Số case lệch phải giải thích được chính con số: rate = (mẫu số − lệch) / mẫu số.
        assert ket_qua.rate == (so_nhan_trong_file - len(ket_qua.lech)) / so_nhan_trong_file
