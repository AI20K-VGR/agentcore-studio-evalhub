"""Test **shape** của `GoldenCase` — dựng kiểu trực tiếp, không qua loader.

Tách khỏi `tests/test_golden_loader.py` cùng lý lẽ đã dùng để tách `tests/integration/`: bài ở đó
chứng minh **loader** đúng, bài ở đây chứng minh **kiểu** nhận đúng thứ được khai và từ chối thứ
không được khai. Trộn vào nhau thì một lần đổi shape sẽ làm đỏ cả hai, và người đọc suite không phân
biệt được *"kiểu sai"* với *"loader sai"*.

KHÓA `DEC-D18-01`: `extra="forbid"` và `manual_label: str | None = None` là **một** thay đổi, không
phải hai. Lý do hai vế không tách được, đo trên code trước khi vá:

```text
GoldenCase(..., manual_label='REFUSE')  →  hasattr(c, 'manual_label') = False
                                          c.model_extra              = None
                                          model_config extra         = <unset → ignore>
```

`extra="forbid"` một mình sẽ làm yaml của DE đỏ ngay khi họ emit nhãn — biến lỗi câm thành lỗi ồn,
đúng hướng, nhưng chặn DE. Khai `manual_label` một mình thì nhãn đúng tên vào được, nhưng **mọi typo
tương lai vẫn câm** (`manual_labels`, `manaul_label` — nuốt sạch). Đi cùng nhau thì nhãn đúng tên đi
được, nhãn sai tên đỏ tại chỗ với tên field sai in ra.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError
from studio_evalhub.golden_case import GoldenCase

# Case tối thiểu hợp lệ — nhánh trả-lời-được (`expected_tenant == tenant`, vai đáp án nằm trong vai
# người hỏi). Mọi bài dưới đây chỉ đổi ĐÚNG một thứ so với nền này, để chỗ đỏ chỉ có một cách đọc.
_CASE_HOP_LE: dict[str, Any] = {
    "case_id": "U-01",
    "query": "Nghỉ phép năm được bao nhiêu ngày?",
    "tenant": "ankor",
    "section_roles": ["hr"],
    "expected_tenant": "ankor",
    "expected_section_role": "hr",
    "expected": "12 ngày",
    "expected_citation": ["ankor-leave-001#c1"],
}


def test_manual_label_sai_ten_phai_do() -> None:
    """**Bài đỏ-trước của `DEC-D18-01`.** Gieo `manaul_label` (typo của `manual_label`) ⇒
    `ValidationError` **nêu đúng tên field sai**, không nuốt câm.

    Trên code trước khi vá, bài này đỏ vì `DID NOT RAISE` — pydantic mặc định `extra="ignore"` nên
    constructor chạy thành công và field bị vứt. Đỏ vì **hành vi**, không phải vì `ImportError`: đó
    là điều kiện để gọi là đỏ-trước ở repo này.

    Vì sao bài này quan trọng hơn vẻ ngoài của nó: chuỗi hệ quả của việc nuốt câm không dừng ở
    "mất một field". Nó là ⇒ DE emit nhãn vào yaml ⇒ `load_golden_set` nạp **thành công**, không
    cảnh báo ⇒ `GoldenCase` vứt field ⇒ agreement-check đọc được không có gì rồi báo *"0 case có
    nhãn tay"* ⇒ một **con số** đi thẳng vào báo cáo ngày thay vì một lỗi. Không test nào đỏ, vì
    không test nào biết field lẽ ra phải có.

    Assert cả **nội dung** thông báo, không chỉ loại exception: một `pytest.raises(ValidationError)`
    trần sẽ xanh kể cả khi pydantic báo về một field khác hẳn, và người sửa yaml cần đọc được **tên
    nào** sai để sửa — không phải mở lại `golden_case.py` mà dò."""
    with pytest.raises(ValidationError) as excinfo:
        GoldenCase(**{**_CASE_HOP_LE, "manaul_label": "REFUSE"})

    assert "manaul_label" in str(excinfo.value)


def test_manual_label_dung_ten_doc_ra_duoc() -> None:
    """Chiều ngược của bài trên: nhãn **đúng tên** đi vào được và đọc ra đúng giá trị đã gieo.

    Không có bài này thì `extra="forbid"` một mình vẫn xanh — và đó là trạng thái chặn DE: nhãn nào
    cũng đỏ, kể cả nhãn đúng."""
    case = GoldenCase(**{**_CASE_HOP_LE, "manual_label": "ANSWER"})

    assert case.manual_label == "ANSWER"


def test_manual_label_vang_la_none_khong_phai_loi() -> None:
    """Nhãn **vắng** ⇒ `None`, KHÔNG phải `ValidationError`.

    Nhãn tay được gán cho một **subset**, không phải cả 30 case (`kb` `DL-16.1`). Bắt buộc field này
    sẽ làm đỏ toàn bộ golden-30 hiện tại — 0/30 case có nhãn — và biến một field phụ thành một đợt
    migration của DE.

    Bài assert `is None` chứ không assert falsy: `""` cũng falsy, mà chuỗi rỗng là một nhãn **đã
    gán** trị rỗng — khác hẳn *chưa gán*. Đây đúng chỗ phân biệt mà docstring của field ghi ra."""
    case = GoldenCase(**_CASE_HOP_LE)

    assert case.manual_label is None


def test_field_la_khong_lien_quan_cung_phai_do() -> None:
    """`extra="forbid"` chặn **mọi** field lạ, không riêng typo của `manual_label`.

    Bất biến được canh không phải *"tên `manual_label` phải đúng"* mà là *"field lạ phải ồn"*. Một
    bản vá chỉ đặc cách riêng `manual_label` (vd `model_validator` bắt đúng một tên) sẽ xanh với ba
    bài trên mà vẫn nuốt câm mọi field khác DE thêm sau này — bài này là chỗ cách vá đó lộ ra."""
    with pytest.raises(ValidationError) as excinfo:
        GoldenCase(**{**_CASE_HOP_LE, "ghi_chu_cua_de": "x"})

    assert "ghi_chu_cua_de" in str(excinfo.value)
