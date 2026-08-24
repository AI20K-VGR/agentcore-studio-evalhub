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


# ── Ba trục phân loại case (`source` · `is_critical` · `tier`) ─────────────────────────────────
#
# Khai ở đây **TRƯỚC** khi DE emit, cùng lý lẽ nguyên văn đã ghi cho `manual_label`: *"nếu khai sau,
# `extra="forbid"` làm yaml của DE đỏ, còn không có `extra="forbid"` thì nhãn bị nuốt câm. Không có
# thứ tự thứ ba an toàn."* Ba field này là điều kiện của golden set lai (AI sinh + người sửa) và của
# cổng nhiều tầng — cả hai đều cần DE sinh case mang nhãn, nên schema phải đi trước một nhịp.


def test_ba_truc_moi_doc_ra_duoc_khi_yaml_khai() -> None:
    """**Bài đỏ-trước.** Case mang `source`/`is_critical`/`tier` phải dựng được và đọc lại đúng.

    Trên code trước khi vá, bài này đỏ với `ValidationError` từ `extra="forbid"` (3 extra fields) —
    đỏ vì **hành vi**, không phải `ImportError`."""
    case = GoldenCase(**_CASE_HOP_LE, source="human", is_critical=True, tier="core")

    assert case.source == "human"
    assert case.is_critical is True
    assert case.tier == "core"


def test_ba_truc_moi_vang_la_none_khong_phai_gia_tri_mac_dinh() -> None:
    """**Vắng ⇒ `None`, KHÔNG phải `"ai"`/`False`/`"full"`.** Đây là vế quan trọng nhất của cả nhóm.

    Cùng luật `manual_label` đã chốt (`DEC-D18-01`) và `DEC-D16-03` (`rate=None ≠ 0.0`): *chưa khai*
    khác *đã khai và bằng X*. Cụ thể từng trục, vì cái giá khác nhau:

    - `source` — mặc định `"ai"` sẽ **khai hộ nguồn gốc** cho 60 case golden hiện có mà không ai
      kiểm; bảng "AI sinh bao nhiêu / người sửa bao nhiêu" đọc từ đó là một con số bịa.
    - `is_critical` — mặc định `False` dán nhãn *"không quan trọng"* lên **mọi** case sẵn có. Cổng
      bảo mật zero-tolerance đọc trục này; một mặc định `False` làm cổng đó **rỗng** mà vẫn xanh.
      Đây là fail-open trên đúng trục nó gác.
    - `tier` — mặc định `"full"` (hoặc `"core"`) tự xếp tầng cho case chưa ai phân, và bộ Core dùng
      để gate lúc Publish sẽ chạy một tập không ai chọn.

    Nên cả ba là `| None = None`. Phía tiêu thụ phải hỏi `is True` / `== "core"` tường minh, và
    case `None` bị **loại khỏi mẫu số** thay vì rơi vào một nhánh mặc định."""
    case = GoldenCase(**_CASE_HOP_LE)

    assert case.source is None
    assert case.is_critical is None
    assert case.tier is None


@pytest.mark.parametrize(("field", "gia_tri"), [("source", "mentor"), ("tier", "medium")])
def test_gia_tri_ngoai_tap_dong_phai_do(field: str, gia_tri: str) -> None:
    """`source`/`tier` là tập ĐÓNG — giá trị lạ đỏ tại chỗ, không nuốt.

    Khác `manual_label` (cố ý để `str` mở vì trục nhãn là của DE và **chưa chốt**): hai trục này
    AIE-2 sở hữu và tập giá trị đã chốt ngay tại đây, nên đóng khung được mà không lấn `DEC-Q5`.
    Một `tier: "medium"` gõ nhầm mà lọt sẽ làm case đó rơi khỏi **cả** bộ Core lẫn bộ Full — biến
    mất khỏi mọi phép chấm, im lặng."""
    with pytest.raises(ValidationError) as bat:
        GoldenCase(**{**_CASE_HOP_LE, field: gia_tri})

    assert field in str(bat.value)


def test_is_critical_khong_nhan_chuoi() -> None:
    """`is_critical` là `bool` thật, không phải thứ pydantic ép từ chuỗi.

    Yaml của DE viết `is_critical: true` ra `bool` Python, nhưng một `"true"` **có dấu nháy** (lỗi
    gõ dễ gặp nhất trong yaml) phải đỏ chứ không được ép thành `True` — nếu ép, một case bị nháy
    nhầm vẫn vào bộ bảo mật và không ai biết chuỗi đó đã được diễn giải hộ."""
    with pytest.raises(ValidationError):
        GoldenCase(**{**_CASE_HOP_LE, "is_critical": "true"})
