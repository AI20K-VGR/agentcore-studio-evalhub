"""Nạp golden-set từ file YAML — nửa còn thiếu giữa *giá trị* của DE và *bộ chấm* của AIE-2.

`DEC-Q5` chốt phân vai: **DE sở hữu giá trị** (nội dung case), **AIE-2 sở hữu nơi lưu + loader**.
Module này là vế thứ hai. Trước D16 nó không tồn tại — case được dựng **in-code** ở `cli.py:46`, tức
mọi thứ chạy trên dữ liệu bịa, và bộ 30 case thật của DE không có đường vào harness.

**`DEC-D16-01` — đường dẫn do CALLER truyền, không hằng số trong `src/`.** Không dòng nào trong
module này (hay bất kỳ file nào của `src/studio_evalhub/`) được biết `packages/kb/...` nằm ở đâu:

1. **Layering** — `.importlinter` xếp 4 quadrant là sibling, `studio_evalhub` không import
   `studio_kb`. Một đường dẫn file chéo repo là **cùng một** sự phụ thuộc, chỉ né được lint chứ
   không né được thực tế.
2. **Fresh clone** — `kit#74` chấm bằng *"clone sạch rồi chạy lệnh y nguyên"*. Clone **riêng** repo
   evalhub thì `packages/kb/` không tồn tại ⇒ một hằng số đường dẫn là `FileNotFoundError` được đảm
   bảo trước, không phải rủi ro.

Bất biến này được **cưỡng chế bằng test** (`test_src_khong_hardcode_duong_dan_kb`), không bằng câu
docstring này — nó quét mọi file `src/*.py` nên bắt được cả lần vi phạm **tương lai**.

`pyyaml` khai ở `[project].dependencies` của **package này** (`DEC-D16-02`), không ăn ké dev-group
của kit gốc: đây là runtime code của một package được cài, và bản vá D8 đã ghi sẵn tên lớp lỗi —
*"ai đổi `uvicorn[standard]` → `uvicorn` là mọi `import yaml` trong workspace chết IM LẶNG"*.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Hai error-code có chủ đích, và nó là bản vá TƯƠNG THÍCH HAI CHIỀU:
#   - `import-untyped`  — khi workspace CHƯA có `types-PyYAML` (trạng thái của kit main hôm nay)
#   - `unused-ignore`   — khi đã có stub, lúc đó dòng ignore thành thừa và mypy báo lỗi ngược lại
# Thiếu code thứ hai thì dòng này chỉ hợp lệ ở đúng MỘT trong hai trạng thái, và ngày kit thêm stub
# là ngày nó đỏ — đúng lớp lỗi `embed_harness.py:66` bên engine đang mắc.
#
# Vì sao KHÔNG chờ `types-PyYAML` (DEC-D16-02): stub không mua thêm gì ở đây — `yaml.safe_load` trả
# `Any` dù có stub hay không, và giá trị đó đã được khai `raw: Any` ngay dưới. Đổi lại, chờ nó kéo
# theo hai vòng merge (kit thêm stub ⇒ engine đỏ `unused-ignore` ⇒ phải vá engine trước). Khai stub
# ở kit vẫn là việc nên làm, nhưng là việc của D17 cùng bản vá engine — không phải điều kiện của #108.
import yaml  # type: ignore[import-untyped, unused-ignore]

from studio_evalhub.golden_case import GoldenSet


def load_golden_set(path: Path, *, expect_ref: str) -> GoldenSet:
    """Nạp `GoldenSet` từ file YAML ở `path`; `golden_set_ref` trong **nội dung** file phải khớp
    `expect_ref`, lệch ⇒ `ValueError`.

    **`expect_ref` bắt buộc, không default** (`DEC-D16-01`). Nó trả lời một câu hỏi khác với `path`:
    `path` là *"đọc file nào"*, `expect_ref` là *"file đó có đúng là bộ case tôi định chấm không"*.

    **Bằng chứng cho việc hai câu đó tách rời — và cho việc tên file KHÔNG ổn định:** bộ 30 của DE
    land ở `callisto-handbook-30-draft.yaml` trong khi `golden_set_ref` bên trong đã là
    `callisto-golden-30-v1`; `kb#18` sau đó đổi tên file thành `callisto-golden-30-v1.yaml`. Tức
    **cùng một bộ case, hai tên file, ref không đổi một ký tự** — đúng thứ bất biến này bảo vệ.
    Một loader suy ref từ tên file sẽ chạy đúng ở một trong hai thời điểm và sai ở thời điểm kia,
    mà không dòng code nào phải đổi để lỗi xuất hiện.

    Ghi lại lịch sử thay vì chỉ mô tả trạng thái hôm nay: tên hiện tại **trùng** với ref, nên một ví
    dụ lấy trạng thái hôm nay làm minh hoạ sẽ đọc thành *"ref suy được từ tên file"* — ngược hẳn
    điều cần nói.

    **Không nuốt lỗi.** `ValidationError` của pydantic bay thẳng lên caller: một loader trả
    `cases=[]` khi file hỏng là loader biến *"dữ liệu sai"* thành *"bộ rỗng"*, và một bộ rỗng thì
    `success_rate` không có mẫu số, `verdict` mất ý nghĩa — hỏng ở tầng dưới, biểu hiện ở tầng trên,
    đúng lớp xanh-giả `kit#134` mô tả.

    Thứ tự kiểm có chủ đích: **ref trước, shape sau**. Trỏ nhầm sang một file YAML hoàn toàn khác thì
    câu trả lời hữu ích là *"sai bộ case"*, không phải một trang `ValidationError` về các field mà
    file đó chưa bao giờ định có.
    """
    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: golden-set phải là một mapping YAML, đọc được {type(raw).__name__}")

    ref_trong_file = raw.get("golden_set_ref")
    if ref_trong_file != expect_ref:
        raise ValueError(
            f"{path}: golden_set_ref không khớp — file khai {ref_trong_file!r}, caller đòi "
            f"{expect_ref!r}. Ref là khoá, tên file chỉ là đường dẫn (DEC-D16-01)."
        )

    return GoldenSet.model_validate(raw)
