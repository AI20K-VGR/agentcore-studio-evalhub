"""Integration — nạp **file golden-30 thật của DE**, không dựng fixture thay thế.

Tách khỏi `tests/test_golden_loader.py` có chủ đích: bài ở đó chứng minh **loader** đúng, bài ở đây
chứng minh **dữ liệu đi vào loader** đúng. Trộn hai loại vào một file thì một lần DE đổi tên file sẽ
làm đỏ cả hai, và người đọc suite không phân biệt được *"loader vỡ"* với *"dữ liệu đi chỗ khác"* —
hai sự cố cần hai phản ứng hoàn toàn khác nhau.

Đường dẫn đến từ fixture `golden_30_path` (`tests/conftest.py`) — composition layer biết đường dẫn,
`src/` không (`DEC-D16-01`).
"""

from __future__ import annotations

from pathlib import Path

from studio_evalhub.golden_loader import load_golden_set

# 8 case từ-chối DE tự khai trong header golden-30 — **nhãn độc lập**, không dẫn xuất từ code của
# quadrant này. Đó là toàn bộ giá trị của nó: nếu `expects_refusal` (dẫn xuất) lệch với ý định DE
# thì phải có một bên thứ hai để chỗ lệch lộ ra.
_REFUSAL_DE_KHAI = [f"HB-{i}" for i in range(23, 31)]


def test_golden_30_that_dung_30_case_va_ref(golden_30_path: Path, golden_30_ref: str) -> None:
    """Ô DoD 1 nói *"eval harness v1 chạy **30 case**"* — nên phải có một bài đối chiếu con số thật,
    không suy từ loader.

    Ba thứ khoá cùng lúc: tổng **30** · ref đúng `callisto-golden-30-v1` (đọc từ **nội dung**, trong
    khi tên file còn chữ `draft`) · tỷ lệ **22 trả-lời / 8 từ-chối**. Tỷ lệ là thứ mẫu số citation
    phụ thuộc trực tiếp (`DEC-04`: loại refusal khỏi mẫu số) — sai nó là sai `citation_accuracy` mà
    không lỗi nào nổi lên."""
    golden = load_golden_set(golden_30_path, expect_ref=golden_30_ref)

    assert golden.golden_set_ref == golden_30_ref
    assert len(golden.cases) == 30

    tu_choi = [c for c in golden.cases if c.expects_refusal]
    tra_loi = [c for c in golden.cases if not c.expects_refusal]
    assert len(tra_loi) == 22
    assert len(tu_choi) == 8


def test_golden_30_expects_refusal_khop_nhan_cua_DE(golden_30_path: Path, golden_30_ref: str) -> None:
    """**`expects_refusal` (dẫn xuất) phải khớp đúng 8 id DE khai là case âm.**

    Bài dễ bỏ sót nhất trong T1, và đắt nhất nếu thiếu. `GoldenCase.expects_refusal` không được lưu
    trong file — nó **tính lại** nhãn từ 4 field qua hai trục hàng rào (T1 chéo-tenant, T6 chéo-vai,
    `golden_case.py:88-109`). Nếu cách DE hiểu "case âm" lệch với công thức đó dù chỉ một case, thì
    case đó **bị chấm bằng luật của nhánh kia** và không lỗi nào nổi lên: nhánh trả-lời chấm
    token-contains, nhánh từ-chối chấm fail-closed + leak — hai luật khác nhau hoàn toàn, cùng trả
    về một `SmokeResult` trông bình thường.

    So bằng **danh sách id có thứ tự**, không bằng số đếm: `len(...) == 8` vẫn xanh khi hai case đổi
    chỗ cho nhau cho đủ số lượng."""
    golden = load_golden_set(golden_30_path, expect_ref=golden_30_ref)

    tu_dan_xuat = sorted(c.case_id for c in golden.cases if c.expects_refusal)

    assert tu_dan_xuat == _REFUSAL_DE_KHAI
