"""Bất biến **cưỡng chế** cho §7 mục 4-5 của thẩm định VinSOC (`kit#129`).

Bộ quét báo `read_run` (AV-203050 · AV-203743) và `list_runs` (AV-203742) đọc `obs.trace_events`
**không lọc tenant**. Thẩm định kết luận **Won't Fix (as designed)** — và lập luận đó đúng: với một
bộ chấm, `WHERE tenant_id = %s` không chỉ yếu hơn mà **có hại**, vì một run bị lẫn hai tenant (đúng
dấu hiệu rò rỉ cần bắt) sẽ bị mệnh đề `WHERE` lặng lẽ giấu đi bằng cách trả về nửa số event.
`tenant_scope_ok` làm ngược lại: lấy hết rồi đối chiếu **mọi** event phải cùng một tenant.

Nhưng thẩm định cũng nói thẳng chỗ yếu, và đó là lý do file này tồn tại:

    "Công bằng với VinSOC: hàm này quả thật KHÔNG tự bảo vệ được — nó dựa vào bên gọi nhớ gọi
     `tenant_scope_ok`. Đó là hợp đồng bằng lời, không phải bằng mã."

Và §6 Điều 2 đặt đúng câu hỏi phải trả lời: *"Có phép kiểm tự động không, hay chỉ là trí nhớ? Nếu
ngày mai có người thêm đường thứ tư, thứ gì sẽ chặn họ?"*

**Đổi tên một mình vẫn là trí nhớ.** `read_run_unscoped` cảnh báo người ĐỌC nó, nhưng không chặn ai
thêm `read_latest_run()` không hậu tố vào tháng sau. Bài này biến quy ước tên thành bất biến kiểm
được: **mọi coroutine chạy SQL trên `obs.trace_events` mà không lọc tenant thì tên bắt buộc mang hậu
tố cảnh báo.** Rủi ro thật mà mentor nêu — *"hôm nay nó nằm sau cờ `--list`; ngày mai ai đó thấy nó
tiện và gọi từ một route"* — bắt đầu bằng việc một hàm như thế **không tự khai** nó là loại gì.

Mutant khai trước khi viết bài:
  M-R1  trả tên về `read_run`/`list_runs`                     -> bài này ĐỎ
  M-R2  thêm coroutine mới đọc `_LIST_RUNS` với tên trơn      -> bài này ĐỎ
  M-R3  bỏ assert "phải tìm thấy ít nhất 1 SQL không-tenant"  -> bài xanh GIẢ, nên assert đó ở lại
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

# Hậu tố tự-khai. `_unscoped` cho "không lọc gì", `_all_tenants` cho "cố ý vượt mọi tenant" — hai
# nghĩa khác nhau nên giữ hai từ, không gộp thành một hậu tố chung cho tiện.
_WARNING_SUFFIXES = ("_unscoped", "_all_tenants")

# Lọc tenant nghĩa là tenant_id nằm trong MỘT VỊ TRÍ VỊ TỪ, không phải chỉ xuất hiện đâu đó: `_READ_RUN`
# có `tenant_id` trong danh sách SELECT mà `WHERE` thì chỉ có `run_id`. Một phép kiểm "có chuỗi
# tenant_id" sẽ xếp nó là đã-lọc và bỏ qua đúng hàm cần canh.
_TENANT_PREDICATE = re.compile(r"tenant_id\s*(=|IN\b)", re.IGNORECASE)

_TRACE_TABLE = "obs.trace_events"

# Phải là một CÂU TRUY VẤN, không phải bất kỳ chuỗi có nhắc tên bảng. Lần chạy đầu bài này bắt oan
# `TRACE_SOURCE_POSTGRES` — một nhãn người-đọc (`"obs.trace_events (Postgres — …)"`), không phải SQL.
# Bắt oan còn tệ hơn bỏ sót: một bài đỏ vì lý do sai là một bài sắp bị ai đó nới lỏng cho hết đỏ.
_LOOKS_LIKE_QUERY = re.compile(r"\bSELECT\b.*\bFROM\b", re.IGNORECASE | re.DOTALL)


def _module() -> ast.Module:
    src = Path(__file__).resolve().parent.parent / "src" / "studio_evalhub" / "run_report.py"
    assert src.is_file(), f"không thấy {src} — bài này sẽ xanh giả nếu im lặng bỏ qua"
    return ast.parse(src.read_text(encoding="utf-8"))


def _sql_khong_loc_tenant(tree: ast.Module) -> dict[str, str]:
    """Hằng SQL cấp module chạm `obs.trace_events` mà KHÔNG có vị từ tenant."""
    found: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
            continue
        value = node.value.value
        if not isinstance(value, str) or _TRACE_TABLE not in value:
            continue
        if not _LOOKS_LIKE_QUERY.search(value):
            continue
        if _TENANT_PREDICATE.search(value):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                found[target.id] = value
    return found


def test_reader_khong_loc_tenant_phai_tu_khai_trong_ten() -> None:
    tree = _module()
    unscoped_sql = _sql_khong_loc_tenant(tree)

    # M-R3: không có dòng này, ngày ai đó đổi tên hằng SQL là bài tự xanh trên tập rỗng.
    assert unscoped_sql, (
        "không tìm thấy hằng SQL nào đọc obs.trace_events mà thiếu vị từ tenant — "
        "hoặc mã đã đổi hình, hoặc phép kiểm này đã hỏng. Xanh trên tập rỗng không phải bằng chứng."
    )

    vi_pham: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        dung: set[str] = {
            inner.id for inner in ast.walk(node) if isinstance(inner, ast.Name) and inner.id in unscoped_sql
        }
        if dung and not node.name.endswith(_WARNING_SUFFIXES):
            vi_pham.append(f"{node.name}() chạy {sorted(dung)}")

    assert not vi_pham, (
        "Coroutine đọc obs.trace_events không lọc tenant nhưng tên không tự khai "
        f"(cần hậu tố {' hoặc '.join(_WARNING_SUFFIXES)}): {vi_pham}"
    )
