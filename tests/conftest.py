"""Fixture dùng chung — **chỗ DUY NHẤT trong quadrant biết golden-30 của DE nằm ở đâu**.

`DEC-D16-01` chia ba tầng: `load_golden_set` nhận `path`, `EvalHarness.run` nhận `golden_set_path`
keyword-only bắt buộc, và **composition root** (CLI arg · `apps/studio` · fixture test) là tầng duy
nhất được biết đường dẫn cụ thể. File này là composition root của suite — nên đường dẫn kb nằm ở
đây, và **chỉ** ở đây, chứ không phải trong `src/` (bất biến đó có bài cưỡng chế riêng:
`test_src_khong_hardcode_duong_dan_kb`).

Đường dẫn resolve từ **workspace root**, không từ cwd: `pytest` chạy được từ kit gốc lẫn từ trong
`packages/evalhub`, và một fixture phụ thuộc cwd sẽ skip im lặng ở một trong hai chỗ.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

# Tên file còn chữ `draft` trong khi `golden_set_ref` bên trong đã là `...-v1` — lệch có thật, và
# **KHÔNG đổi tên trong D16**: rename chỉ được quyết khi xác nhận caller dùng `golden_set_ref` chứ
# không hardcode tên file. Loader không suy ref từ tên file nên lệch này vô hại; hằng số ở đây là
# đường dẫn, không phải khoá.
_GOLDEN_30 = _WORKSPACE_ROOT / "packages" / "kb" / "golden" / "callisto-handbook-30-draft.yaml"


@pytest.fixture
def golden_30_ref() -> str:
    """Ref THẬT — nằm trong **nội dung** file, không suy từ tên file (`DEC-D16-01`)."""
    return "callisto-golden-30-v1"


@pytest.fixture
def golden_30_path() -> Path:
    """Đường dẫn tới golden-30 thật của DE (`kb@1e8774f`, 30 case). Thiếu file ⇒ **skip có lý do đọc
    được**, không phải một bài lặng lẽ biến mất.

    Skip ở tầng fixture chứ không phải `pytest.mark.skipif`: mark phải được **import** vào từng file
    test, mà `tests/` không có `__init__.py` nên đường import đó phụ thuộc thứ tự nạp conftest của
    pytest — một bài đỏ vì `ImportError` là đúng thứ bài này tồn tại để tránh.

    ⚠️ **Quan trọng cho mutation:** mutant `M-L3` (`expects_refusal` bỏ trục T6) **chỉ có lưới ở tầng
    integration**. Chạy suite trong môi trường không có `packages/kb` ⇒ mọi bài dùng fixture này skip
    ⇒ `M-L3` sống mà không ai biết. Vì thế môi trường chạy mutation phải được ghi lại — cùng lớp với
    chuyện `77 passed` của D15 đo trong shell không có `STUDIO_DATABASE_URL_ADMIN`."""
    if not _GOLDEN_30.is_file():
        pytest.skip(
            f"golden-30 của DE không có ở {_GOLDEN_30} — cần `git submodule update --init "
            "packages/kb` (chạy từ workspace root). Bài integration này nạp file thật, không dựng "
            "fixture thay thế."
        )
    return _GOLDEN_30
