"""Khoảng Wilson 95% — **chẩn đoán**, không phải cổng (`DEC-S2-134-01`, `kit#134`).

## Cái module này KHÔNG làm, và đó là nội dung chính của nó

- **Không** vào `studio_contracts.Scorecard`. Nhét `ci_lower`/`ci_upper`/`n_eff` vào contract chạm
  renderer, DB, consumer và roundtrip test — `kit#134` ghi thẳng là phải qua RFC/decision, không làm
  âm thầm. Hàm ở đây là hàm thuần, caller nào cần thì gọi.
- **Không** thành cổng publish. `DEC-S2-134-01` chốt CI là **diagnostic trước**. Hệ quả cỡ mẫu đã
  đo: với cận dưới `0.90`, golden-30 **FAIL cả khi 30/30 pass** (`30/30 → 0.8865`), cần khoảng
  `35/35` mới vượt. Đổi gate sang `lower >= 0.90` là làm hỏng gate vì một tính chất của **cỡ mẫu**,
  không phải vì agent tệ.
- **Không** hiệu chỉnh cụm bằng ICC. `kit#134` xếp route ICC/cluster vào *"sau S2, chỉ khi có
  decision và đủ data"*, và cấm đích danh việc tự đặt `ICC = 0.3` làm mặc định. Thay vào đó, cách
  đúng và rẻ là **chọn đúng đơn vị độc lập** rồi đưa `n` đó vào — xem `n` hiệu dụng dưới.
- **Không** thêm dependency. `DEC-S2-134` D16 chốt viết bằng **standard library**;
  `pyproject.toml` chưa có `scipy`/`numpy` và không được thêm.

## `n` hiệu dụng — chỗ dễ sai nhất, và nó là chuyện đơn vị chứ không phải chuyện công thức

Golden-30 **không** phải 30 quan sát độc lập: 7 câu hỏi bị dùng lại (một câu tới 4 lần trên bộ
`callisto-golden-30-v1`). Đưa `n = 30` vào công thức cho khoảng **hẹp hơn sự thật** — nó khai một
lượng thông tin mình không có. `kit#134` nói đúng nguyên tắc đó: *"`n` đếm dòng log thay vì item
độc lập (50 item chạy 10 lần vẫn là `n = 50`)"* là một cờ đỏ.

Module này **không tự đoán** `n` hiệu dụng — caller truyền vào, vì chỉ caller biết đơn vị độc lập là
gì (query? tài liệu? tenant?). Đo thật cho hai bộ hiện có ở
`docs/evidence/260824-golden-30-sample/`.

## Câu chữ bắt buộc khi báo cáo

Viết *"khoảng Wilson 95%"* / *"cận dưới theo Wilson 95%"*. **Không** viết *"95% khả năng tỷ lệ đúng
nằm trong khoảng này"* — sai theo frequentist: Wilson nói về **coverage của quy trình khi lặp lại**,
không nói về xác suất của một khoảng cụ thể. Và coverage thật với `n` nhỏ có thể **dưới** mức danh
nghĩa (`n=10, p=0.3` → ~0.9244), nên đừng quảng bá "95%" như một bảo đảm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

Z_95 = 1.959963984540054
"""z cho mức 95% hai phía. Viết literal thay vì gọi `statistics.NormalDist().inv_cdf(0.975)` mỗi lần:
giá trị này là **hằng số của mức tin cậy**, không phải thứ dẫn xuất từ dữ liệu, và ghim nó làm bảng
số tái lập được từng chữ số qua mọi phiên bản Python."""


@dataclass(frozen=True)
class WilsonInterval:
    """Kết quả một phép ước lượng khoảng — mang cả `status`, không chỉ hai đầu mút.

    `status` tồn tại vì `n = 0` **không** phải một khoảng `[0, 1]`. `kit#134` chốt: `n = 0` ⇒
    `not_estimable`, lower/upper là `null`, **không** in `[0,1]` và **không** để gate đọc thành
    PASS/FAIL thống kê. Trả `[0.0, 1.0]` ở ca đó là mời người đọc tin rằng đã đo — một khoảng rộng
    trông vẫn giống một phép đo, còn `not_estimable` thì không.
    """

    k: int
    n: int
    lower: float | None
    upper: float | None
    status: Literal["ok", "not_estimable"]

    @property
    def point(self) -> float | None:
        """Ước lượng điểm `k/n`. `None` khi `not_estimable` — cùng lý do với `lower`/`upper`."""
        return None if self.status == "not_estimable" else self.k / self.n


def wilson(k: int, n: int, *, z: float = Z_95) -> WilsonInterval:
    """Khoảng Wilson (score interval) cho tỷ lệ `k/n`.

    Chọn Wilson chứ không phải Wald (`p̂ ± z·√(p̂(1−p̂)/n)`) vì Wald sụp đúng ở chỗ bộ chấm này hay
    đứng nhất: `k = n` (mọi case pass) cho `p̂ = 1` ⇒ `√(1·0/n) = 0` ⇒ khoảng `[1.0, 1.0]`, tức
    *"chắc chắn 100%"* từ 30 quan sát. Wilson cho `30/30 → [0.8865, 1.0]`, đọc đúng hơn nhiều: 30
    lần đúng liên tiếp **không** loại trừ một tỷ lệ lỗi thật cỡ 11%.

    Bốn mốc dùng làm bài test neo (`kit#134`):

        Wilson(8, 10)   ≈ [0.4902, 0.9433]
        Wilson(30, 30)  ≈ [0.8865, 1.0]
        Wilson(0, 30)   ≈ [0.0, 0.1135]
        Wilson(96, 100) ≈ [0.9016, 0.9843]

    `n = 0` ⇒ `not_estimable` chứ **không** phải `[0, 1]`. `k > n` hoặc số âm ⇒ `ValueError`: đó là
    lỗi của caller, không phải một ca dữ liệu — nuốt nó thành một khoảng nào đó là để một mẫu số sai
    đi thẳng vào báo cáo.
    """
    if k < 0 or n < 0:
        raise ValueError(f"wilson: k và n phải không âm, nhận k={k}, n={n}")
    if k > n:
        raise ValueError(f"wilson: k không được lớn hơn n, nhận k={k}, n={n}")
    if n == 0:
        return WilsonInterval(k=k, n=n, lower=None, upper=None, status="not_estimable")

    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1.0 - p) / n + z2 / (4 * n * n))
    lower = max(0.0, center - half)
    upper = min(1.0, center + half)

    # Hai biên có giá trị ĐÚNG theo giải tích, và dấu phẩy động trượt khỏi chúng ~1e-16.
    #
    #   k == n:  center + half = (1 + z²/2n + z²/2n) / (1 + z²/n) = (1 + z²/n)/(1 + z²/n) = 1  (đúng)
    #   k == 0:  center - half = 0                                                             (đúng)
    #
    # Đo được: `wilson(30, 30).upper` ra `0.9999999999999999`. Không phải sai số cần bao dung — nó
    # là một con số ĐÚNG bị in sai, và một cận trên `0.9999999999999999` trong evidence sẽ làm người
    # đọc nghi ngờ đúng chỗ không có gì sai. Gán thẳng giá trị giải tích ở hai biên đó, không nới
    # assert của bài test để "chấp nhận sai số" — luật vàng của sổ bằng chứng là chạy lại ra ĐÚNG số.
    if k == n:
        upper = 1.0
    if k == 0:
        lower = 0.0

    return WilsonInterval(k=k, n=n, lower=lower, upper=upper, status="ok")
