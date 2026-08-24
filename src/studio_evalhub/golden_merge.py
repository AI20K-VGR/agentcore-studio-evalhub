"""Hợp nhất nhiều `GoldenSet` thành một, cưỡng chế *"human ground-truth always wins"*.

## Vì sao module này tồn tại

Luật đã được khai từ khi `source` ra đời (`golden_case.py`): *"khi dedup thấy hai case cùng nội
dung, bản `source="human"` **ghi đè** bản `"ai"`, không phải bản nào tới sau thắng."* Nhưng nó chỉ
sống trong docstring — **không có hàm nào cưỡng chế**, nên nó là một lời hứa, không phải một cái
cổng. Cùng lớp lỗi mà `DEC-D28-01` vừa đóng cho `price_mismatches`: điều kiện viết ra từ lâu, chưa
ai từng chạy.

Golden set lai có hai nguồn thật từ 24/08: `studio_kb.golden_from_kb` sinh diện rộng
(`source="ai"`), và `POST /api/admin/golden-sets` nhận bộ người dùng tự viết. Không có bước hợp
nhất, hai nguồn chỉ **thay thế** nhau (`write_golden_set` upsert cả bộ) — nghĩa là hoặc mất diện
phủ của AI, hoặc mất phần người đã sửa. Đúng thứ trục `source` sinh ra để tránh.

## Khoá dedup — vì sao KHÔNG phải `query`, và vì sao KHÔNG phải `case_id`

`case_id` không dùng được: hai nguồn đặt id độc lập nhau (`golden_from_kb` tự sinh id theo chunk),
nên cùng một câu hỏi sẽ mang hai id khác nhau và không bao giờ gặp nhau.

`query` **một mình** thì nguy hiểm hơn — đây là chỗ đáng đo trước khi viết, và số đo đổi hẳn thiết
kế. Đếm trên 5 bộ đóng gói sẵn (`studio_kb/golden/`):

| bộ | n | trùng theo `query` | trùng theo khoá đủ |
|---|---|---|---|
| `callisto-2.0-golden-30-v1` | 30 | **7** | 0 |
| `callisto-golden-30-v1` | 30 | **7** | 0 |
| `callisto-grid-queries-v0` | 20 | **5** | 0 |
| `smoke-10` | 10 | **2** | 0 |
| `smoke-5` | 5 | **1** | 0 |

Những cặp trùng `query` đó **không phải bản sao** — chúng là các case hàng rào T1/T6: *cùng một câu
hỏi, hỏi dưới danh nghĩa tenant khác hoặc bộ vai hẹp hơn*, và đáp án đúng là **bị từ chối**. Dedup
theo `query` sẽ gộp mỗi cặp đó làm một, tức **xoá lặng lẽ đúng các case bảo mật** mà bộ golden tồn
tại để kiểm — và `success_rate` sau đó vẫn ra một con số trông bình thường.

Nên khoá là bộ ba `(tenant, query đã chuẩn hoá, tập section_roles)`. Trên dữ liệu thật nó cho **0**
trùng ở cả 5 bộ, tức nó phân biệt được đúng những gì cần phân biệt.

`section_roles` vào khoá dưới dạng `frozenset`, không phải list: `["public", "hr"]` và
`["hr", "public"]` là cùng một phạm vi đọc, và thứ tự khai trong YAML không phải thông tin.

## Chuẩn hoá `query` — dừng ở đâu

`NFC` + gộp khoảng trắng + `casefold`. Ba phép này bắt các biến thể **không mang nghĩa**:

- **`NFC` là bắt buộc với corpus tiếng Việt**, không phải trang trí. Cùng một chữ *"nghỉ"* có thể
  được lưu dạng dựng sẵn (một code point) hay tổ hợp (chữ cái + dấu rời). Hai chuỗi đó **hiển thị y
  hệt nhau** nhưng `==` trả `False` — nên hai case người và máy viết cùng một câu sẽ không bao giờ
  gặp nhau, và luật *"human thắng"* im lặng không áp dụng. Một lỗi không thể thấy bằng mắt khi đọc
  diff.
- Gộp khoảng trắng: xuống dòng trong YAML block scalar là chuyện định dạng.
- `casefold`: khác biệt hoa/thường trong câu hỏi tự nhiên không tạo ra case khác.

**Dừng ở đó — cố ý không bỏ dấu câu, không bỏ dấu thanh.** *"Trưởng nhóm được duyệt chi tối đa bao
nhiêu?"* và *"…tối đa bao nhiêu"* (không dấu hỏi) gần như chắc chắn là một case; nhưng một bộ chuẩn
hoá mạnh tay hơn sẽ bắt đầu gộp những câu **thật sự khác nhau**, và hậu quả của gộp nhầm ở đây là
mất case, im lặng — cùng hạng với việc dedup theo `query`. Chuẩn hoá thiếu thì cùng lắm là bỏ sót
một lần hợp nhất (thấy được: case còn nguyên hai bản); chuẩn hoá thừa thì mất dữ liệu (không thấy
được). Hai loại sai không cùng giá.

## Vì sao va chạm không phân xử được thì RAISE, chứ không chọn bừa

Luật chỉ định nghĩa **một** cặp: `human` thắng `ai`. Mọi cặp còn lại — `None` với bất kỳ thứ gì,
`ai` với `ai`, `human` với `human` — luật **không nói**, và module này không được tự bịa ra phần
còn lại.

Đặc biệt không được coi `None` là `human`: 60 case golden hiện có đều mang `source=None` (*chưa
khai nguồn*, xem docstring `source`), và diễn giải chúng thành "người viết" là khai hộ nguồn gốc cho
cả 60 — đúng thứ mà giá trị mặc định `None` được chọn để tránh.

`GoldenSetMergeConflict` liệt kê **mọi** va chạm trong một lần ném, không dừng ở cái đầu tiên: người
sửa cần thấy đủ danh sách để sửa một lượt, chứ không phải chạy lại 12 lần để phát hiện 12 chỗ.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from studio_evalhub.golden_case import GoldenCase, GoldenSet

_WHITESPACE = re.compile(r"\s+")

CaseKey = tuple[str, str, frozenset[str]]
"""`(tenant, query đã chuẩn hoá, tập section_roles)` — xem docstring module."""


@dataclass(frozen=True, slots=True)
class MergeConflict:
    """Một khoá có từ hai case mà luật `source` không chọn được bản thắng."""

    key: CaseKey
    case_ids: tuple[str, ...]
    sources: tuple[str | None, ...]

    def __str__(self) -> str:
        tenant, query, roles = self.key
        vai = ",".join(sorted(roles)) or "(không vai)"
        cap = ", ".join(f"{cid}(source={src!r})" for cid, src in zip(self.case_ids, self.sources, strict=True))
        return f"tenant={tenant!r} vai=[{vai}] query={query[:60]!r} — {cap}"


class GoldenSetMergeConflict(ValueError):
    """Hợp nhất gặp va chạm mà luật `source` không phân xử được.

    Mang **toàn bộ** danh sách va chạm (`.conflicts`), không chỉ cái đầu tiên. `ValueError` vì đây là
    dữ liệu đầu vào sai, cùng hạng với `load_golden_set` ném khi ref lệch — không phải lỗi hệ thống.
    """

    def __init__(self, conflicts: tuple[MergeConflict, ...]) -> None:
        self.conflicts = conflicts
        chi_tiet = "\n  - ".join(str(c) for c in conflicts)
        super().__init__(
            f"golden_merge: {len(conflicts)} va chạm không phân xử được bằng luật `source` "
            f"(chỉ `human` thắng `ai`; mọi cặp khác phải do người quyết):\n  - {chi_tiet}"
        )


def normalize_query(query: str) -> str:
    """Dạng chuẩn của `query` dùng để so khớp. Xem mục *"Chuẩn hoá `query`"* ở docstring module."""
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFC", query).strip()).casefold()


def case_key(case: GoldenCase) -> CaseKey:
    """Khoá dedup của một case: `(tenant, query chuẩn hoá, tập section_roles)`."""
    return (case.tenant, normalize_query(case.query), frozenset(case.section_roles))


def _thang(a: GoldenCase, b: GoldenCase) -> GoldenCase | None:
    """Bản thắng giữa hai case cùng khoá, hoặc `None` khi luật không phân xử được.

    Lấy case **nguyên vẹn**, không trộn từng field: một bản lai giữa câu hỏi của người và đáp án
    mong đợi của máy là một case **chưa ai từng viết**, và không ai rà được nó.
    """
    if a.source == "human" and b.source == "ai":
        return a
    if a.source == "ai" and b.source == "human":
        return b
    return None


def merge_golden_sets(*sets: GoldenSet, golden_set_ref: str) -> GoldenSet:
    """Hợp nhất các bộ thành một bộ tên `golden_set_ref`, `source="human"` thắng `source="ai"`.

    `golden_set_ref` là tham số **bắt buộc, keyword-only**, không suy từ các bộ đầu vào. Hợp nhất
    một bộ `"ai"` với một bộ `"human"` cho ra thứ khác cả hai; mượn tên của một trong hai sẽ làm bộ
    kết quả **tự khai** là bộ nguồn, và `recipe.golden_set_ref` trỏ vào đó sẽ chấm trên một tập khác
    hẳn tập mà tên kia mô tả. Cùng lý lẽ `DEC-D16-01` đã dùng cho `expect_ref`.

    Thứ tự đầu ra: theo **lần xuất hiện đầu tiên của khoá** trên toàn bộ chuỗi đầu vào. Tất định
    (chạy lại cho cùng kết quả) và giữ nguyên trật tự của bộ đầu tiên — quan trọng vì `Scorecard.
    results` xếp theo thứ tự case, và một thứ tự nhảy theo `set` sẽ làm hai lượt chấm cùng dữ liệu
    cho ra hai báo cáo khác nhau về hình thức.

    Thứ tự **tham số** cố ý KHÔNG quyết định bản thắng — chỉ `source` quyết. Đó là toàn bộ khác biệt
    giữa hàm này và một phép `dict.update()`, và là phần luật `golden_case.py` khai bằng đúng chữ
    *"không phải bản nào tới sau thắng"*.

    Raises:
        GoldenSetMergeConflict: có ít nhất một khoá mà luật không chọn được (xem docstring module).
        ValueError: không truyền bộ nào — hợp nhất rỗng gần như luôn là lỗi gọi hàm, và trả về một
            bộ 0 case sẽ đẩy nó xuống `compute_scorecard` để thành một mẫu số 0.
    """
    if not sets:
        raise ValueError("merge_golden_sets: cần ít nhất một GoldenSet")

    giu: dict[CaseKey, GoldenCase] = {}
    va_cham: list[MergeConflict] = []
    for bo in sets:
        for case in bo.cases:
            khoa = case_key(case)
            dang_giu = giu.get(khoa)
            if dang_giu is None:
                giu[khoa] = case
                continue
            thang = _thang(dang_giu, case)
            if thang is None:
                va_cham.append(
                    MergeConflict(
                        key=khoa,
                        case_ids=(dang_giu.case_id, case.case_id),
                        sources=(dang_giu.source, case.source),
                    )
                )
                continue
            giu[khoa] = thang

    if va_cham:
        raise GoldenSetMergeConflict(tuple(va_cham))

    return GoldenSet(golden_set_ref=golden_set_ref, cases=list(giu.values()))
