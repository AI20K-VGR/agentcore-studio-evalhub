"""Đọc/ghi golden-set ở `eval.golden_sets` — nửa DB của cutover **file → DB**.

## Vì sao cần, và vì sao không phải "thêm một nguồn nữa"

`golden_loader.load_golden_set(path, expect_ref=…)` đọc YAML trên đĩa. Đường đó **không mang khái
niệm tenant**: `routes/publish.py::_resolve_golden_set_path` glob cả thư mục rồi khớp theo
`golden_set_ref` khai bên trong file, nên **mọi tenant bị chấm bằng cùng một bộ Callisto tĩnh**. Bảng
`eval.golden_sets` đã có `tenant_id NOT NULL` + RLS `FORCE` từ `DEC-D20-05` nhưng chưa ai đọc/ghi —
một cột shell.

Module này **không** thay `golden_loader`: YAML vẫn là thứ DE tác giả và review qua git. Nó là
**đường nạp** (`write_golden_set`) và **đường đọc lúc chạy** (`read_golden_set`). YAML → tác giả;
DB → phục vụ, theo tenant.

## Nhận `conn`, KHÔNG nhận `pool` — và đó là quyết định bảo mật

`eval.golden_sets` bật `ENABLE`+`FORCE ROW LEVEL SECURITY` với policy
`tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid`. Một hàm nhận `pool` sẽ tự mở
connection **mới**, và connection mới **không có** `app.tenant_id` ⇒ policy so `NULL` ⇒ mọi dòng bị
lọc ⇒ `SELECT` **thành công**, trả rỗng, không cảnh báo. Đó là chế độ hỏng tệ nhất: *"tenant này
chưa có bộ"* và *"tôi quên bind tenant"* đọc ra cùng một kết quả.

Nhận `conn` buộc caller đưa **đúng** connection đã bind — ở production là connection của
`tenant_context_middleware`, cùng khuôn `studio_workbench.publish.publish(recipe, scorecard, conn)`.

Và vì "đã bind" vẫn có thể sai, hai hàm dưới đây **tự kiểm** `app.tenant_id` khớp `tenant_id` được
truyền, rồi mới chạm bảng — xem `GoldenSetScopeError`.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from studio_evalhub.golden_case import GoldenCase, GoldenSet


class GoldenSetNotFound(ValueError):
    """Không có bộ `(tenant_id, golden_set_ref)` nào trong `eval.golden_sets`.

    Kiểu riêng thay vì trả `GoldenSet` rỗng: một bộ **0 case** đi tiếp vào `EvalHarness.run()` sẽ cho
    `success_rate` trên mẫu số 0 — hoặc `ZeroDivisionError`, hoặc tệ hơn, một con số. Cùng lý lẽ
    `RunCostError`/`TraceAnswerError`: fail-closed ở chỗ không chứng minh được, không đoán."""


class GoldenSetScopeError(RuntimeError):
    """Connection **chưa bind** `app.tenant_id`, hoặc bind một tenant KHÁC `tenant_id` được truyền.

    Tách khỏi `GoldenSetNotFound` là điểm chính của module này. Dưới RLS `FORCE`, cả hai ca đều cho
    `SELECT` trả **0 dòng** — nhưng chúng là hai chuyện khác hẳn:

    - *chưa có bộ nào cho tenant này* — trạng thái hợp lệ, caller xử lý được (nạp bộ, hoặc từ chối
      publish với thông điệp đúng);
    - *connection sai scope* — **lỗi lập trình**, và nếu nuốt thành "chưa có bộ" thì nó im lặng mãi.

    Cùng khuôn `UnscopedReadUnavailable` (`DEC-D26-01`): thà từ chối trả lời còn hơn trả một giá trị
    trông hợp lệ."""


_READ = """
SELECT golden_set_ref, cases
FROM eval.golden_sets
WHERE golden_set_ref = %s
"""

_WRITE = """
INSERT INTO eval.golden_sets (tenant_id, golden_set_ref, cases, kb_id)
VALUES (%s, %s, %s::jsonb, %s)
ON CONFLICT (tenant_id, golden_set_ref) DO UPDATE
    SET cases = EXCLUDED.cases, kb_id = EXCLUDED.kb_id
"""


async def _assert_scope(conn: Any, tenant_id: UUID) -> None:
    """Khẳng định connection đang bind ĐÚNG `tenant_id`, trước khi chạm bảng.

    `current_setting('app.tenant_id', true)` trả `NULL` khi chưa set và `''` khi set rỗng — cả hai
    đều làm policy lọc sạch. Kiểm ở đây để lỗi nói đúng nguyên nhân, thay vì để RLS trả rỗng rồi
    caller đoán."""
    cur = await conn.execute("SELECT NULLIF(current_setting('app.tenant_id', true), '')")
    row = await cur.fetchone()
    bound = row[0] if row else None
    if bound is None:
        raise GoldenSetScopeError(
            "golden_store: connection chưa bind `app.tenant_id` — dưới RLS FORCE mọi SELECT sẽ trả "
            "rỗng và im lặng; refusing"
        )
    if UUID(str(bound)) != tenant_id:
        raise GoldenSetScopeError(
            f"golden_store: connection bind tenant {bound} nhưng caller hỏi {tenant_id} — "
            "phiên và tham số phải khai cùng một tenant; refusing"
        )


async def read_golden_set(conn: Any, ref: str, tenant_id: UUID) -> GoldenSet:
    """Bộ case của `(tenant_id, ref)`. Không có ⇒ `GoldenSetNotFound`, **không** trả bộ rỗng.

    Không lọc `tenant_id` trong `WHERE`: RLS đã lọc, và câu `_assert_scope` ở trên đã khẳng định
    phiên đúng tenant. Thêm mệnh đề `WHERE tenant_id = …` ở đây sẽ là lớp thứ hai — nhưng nó cũng
    che mất ca *"RLS tắt"*, biến một cấu hình hỏng thành một truy vấn trông vẫn đúng. Ở
    `obs.trace_events` hai lớp là có chủ đích vì bảng đó từng **không** có RLS; ở đây RLS có từ ngày
    đầu nên lớp thứ hai chỉ mua thêm sự im lặng.

    `cases` đi qua `GoldenCase` (`extra="forbid"`) chứ không `model_construct`: dữ liệu trong JSONB
    do một lần ghi trước đó tạo ra, và giữa hai lần đó schema có thể đã đổi — đúng ca mà
    `extra="forbid"` tồn tại để bắt."""
    await _assert_scope(conn, tenant_id)
    cur = await conn.execute(_READ, (ref,))
    row = await cur.fetchone()
    if row is None:
        raise GoldenSetNotFound(
            f"golden_store: không có golden set {ref!r} cho tenant {tenant_id} trong eval.golden_sets"
        )
    return GoldenSet(golden_set_ref=row[0], cases=[GoldenCase(**c) for c in row[1]])


async def write_golden_set(conn: Any, golden: GoldenSet, tenant_id: UUID, *, kb_id: UUID | None = None) -> None:
    """Nạp/cập nhật bộ case cho `tenant_id`. `ON CONFLICT` theo cặp `(tenant_id, golden_set_ref)`.

    Upsert chứ không insert-only: đường dùng chính là **nạp lại** một bộ đã sửa (DE cập nhật YAML rồi
    seed lại), và một `INSERT` trần sẽ bắt caller tự xoá trước — hai câu cho một ý, và cửa sổ giữa
    chúng là lúc bộ **không tồn tại**, tức publish của tenant đó vỡ.

    `ON CONFLICT (tenant_id, golden_set_ref)` dùng được vì `evalhub#46` đổi ràng buộc sang unique
    ghép; với `UNIQUE(golden_set_ref)` toàn cục cũ, câu này sẽ nhắm sai khoá.

    `model_dump(mode="json")` cho từng case — không `model_dump_json()` trên cả `GoldenSet`, vì cột
    chỉ chứa `cases`, không chứa `golden_set_ref` (nó là cột riêng)."""
    await _assert_scope(conn, tenant_id)
    payload = json.dumps([c.model_dump(mode="json") for c in golden.cases], ensure_ascii=False)
    await conn.execute(_WRITE, (tenant_id, golden.golden_set_ref, payload, kb_id))
