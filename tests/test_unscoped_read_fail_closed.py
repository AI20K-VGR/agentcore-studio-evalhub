"""GAP-1 (`evalhub#37`): hai hàm đọc-xuyên-tenant phải KÊU TO, không trả rỗng im lặng.

`app#40` bật `ENABLE`+`FORCE ROW LEVEL SECURITY` trên `obs.trace_events` với policy
`tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid`. Hai hàm bộ chấm —
`read_run_unscoped` và `list_runs_all_tenants` — CỐ Ý không set `app.tenant_id` (đó là việc của
chúng: đọc xuyên tenant). Dưới policy đó, mỗi câu SELECT của chúng khớp **0 dòng** và trả `[]`.

Vì sao đây là lỗi mức chặn chứ không phải bất tiện: chế độ hỏng là **im lặng**.
`list_runs_all_tenants` trả `[]` thì `--list` in ra một bảng rỗng trông y hệt "chưa có run nào";
`read_run_unscoped` trả `[]` thì `run_cost_from_trace` raise `RunCostError("events rỗng")` — một
câu ĐÚNG NGỮ PHÁP nhưng SAI NGUYÊN NHÂN, nó nói "không có gì để đo" trong khi sự thật là "RLS
đang giấu dòng khỏi role này". Người đọc lỗi đó sẽ đi tìm nhầm chỗ.

**Vì sao không sửa bằng cách set `app.tenant_id` rồi lặp từng tenant** (hướng B trong `evalhub#37`):
`read_run_unscoped` tồn tại để `tenant_scope_ok` (`harness.py:187`) bắt được run mà *"node đầu mang
ankor còn node sau mang borea"*. Lọc theo một tenant sẽ khiến RLS **giấu đi đúng những event lạ mà
phép kiểm đó đi tìm** — `tenant_scope_ok` trả `True` cho một run hỏng thật. Hướng đó không phải bản
vá, nó là hồi quy bảo mật. Nên hàm phải đọc được mọi dòng (role có `BYPASSRLS`), hoặc phải từ chối
trả lời.

Bài này khoá vế thứ hai: **từ chối trả lời**. Vế thứ nhất (cấp role `BYPASSRLS`) chạm
`docker/postgres-init` + compose ở repo kit và grant ở `apps/studio` — PR riêng.

Bài tự dựng tiền đề RLS chứ không dựa vào con trỏ `apps/studio` đang ghim ở kit: con trỏ đó hiện
còn **trước** GAP-1, nên `ensure_all_schemas()` của fixture chưa bật RLS. Tự bật + tự khôi phục làm
bài này cho cùng một kết quả ở cả hai phía lần bump con trỏ.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from studio_app.obs.trace_writer import PgTraceWriter
from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.run_report import (
    UnscopedReadUnavailable,
    list_runs_all_tenants,
    read_run_unscoped,
)

_RUN_ID = "run-gap1-fail-closed"
_TENANT_A = UUID("a0000000-0000-0000-0000-000000000001")
_TENANT_B = UUID("b0000000-0000-0000-0000-000000000002")

_BAT_RLS = """
ALTER TABLE obs.trace_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE obs.trace_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS obs_trace_events_tenant_isolation ON obs.trace_events;
CREATE POLICY obs_trace_events_tenant_isolation ON obs.trace_events
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
"""

_TAT_RLS = """
DROP POLICY IF EXISTS obs_trace_events_tenant_isolation ON obs.trace_events;
ALTER TABLE obs.trace_events NO FORCE ROW LEVEL SECURITY;
ALTER TABLE obs.trace_events DISABLE ROW LEVEL SECURITY;
"""


def _event(seq: int, tenant: UUID) -> TraceEvent:
    return TraceEvent(
        event_id=f"{_RUN_ID}-e{seq}",
        run_id=_RUN_ID,
        agent_id="agent-gap1",
        tenant_id=tenant,
        node_id=f"n{seq}",
        node_type=NodeType.LLM_STEP,
        ts=f"2026-08-22T09:00:0{seq}+00:00",
        inputs_hash="stub",
        outputs={},
        tokens=Tokens(prompt=1, completion=1),
        cost=0.0,
    )


async def _gieo_run_tron_tenant(pool: Any) -> None:
    """Một run có event của HAI tenant — đúng hình dạng mà `tenant_scope_ok` tồn tại để bắt.

    Ghi qua `PgTraceWriter` (sink thật của `apps/studio`) chứ không INSERT tự chế: writer tự
    `SET LOCAL app.tenant_id` trên chính connection của nó, nên nó ghi được kể cả khi RLS đang bật —
    đó chính là lý do GAP-1 không làm chết đường GHI, chỉ làm chết đường ĐỌC-xuyên-tenant.
    """
    writer = PgTraceWriter(pool)
    await writer.write(_event(1, _TENANT_A))
    await writer.write(_event(2, _TENANT_B))


async def _dat_rls(pool: Any, sql_text: str) -> None:
    async with pool.connection() as conn:
        await conn.execute(sql_text)


async def _trang_thai_rls(pool: Any) -> tuple[bool, bool]:
    """`(enabled, forced)` của `obs.trace_events` — để khôi phục ĐÚNG trạng thái tìm thấy.

    Không hardcode "khôi phục = tắt": trạng thái ban đầu phụ thuộc con trỏ `apps/studio` đang ghim ở
    kit (trước GAP-1 thì tắt, sau thì bật). Một bài test để lại DB dùng chung ở trạng thái YẾU HƠN
    lúc nó tìm thấy là một bài test tự tạo lỗ — kể cả khi fixture `admin_pool` chạy lại
    `ensure_all_schemas()` ở bài sau và vô tình dọn hộ.
    """
    async with pool.connection() as conn:
        cur = await conn.execute(
            "SELECT c.relrowsecurity, c.relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'obs' AND c.relname = 'trace_events'"
        )
        row = await cur.fetchone()
    return (False, False) if row is None else (bool(row[0]), bool(row[1]))


async def _khoi_phuc_rls(pool: Any, trang_thai: tuple[bool, bool]) -> None:
    enabled, forced = trang_thai
    if enabled:
        await _dat_rls(
            pool, _BAT_RLS if forced else _BAT_RLS.replace("FORCE ROW LEVEL SECURITY", "NO FORCE ROW LEVEL SECURITY")
        )
    else:
        await _dat_rls(pool, _TAT_RLS)


async def test_read_run_unscoped_raise_thay_vi_tra_rong_khi_RLS_dang_che(admin_pool: Any) -> None:
    """KHÓA: RLS bật + role không `BYPASSRLS` ⇒ `read_run_unscoped` phải raise.

    Trước bản vá hàm trả `[]` — im lặng, và cái `[]` đó đi thẳng vào `run_cost_from_trace` để biến
    thành `RunCostError("events rỗng")`, đổ lỗi cho dữ liệu thay vì cho quyền đọc.
    """
    ban_dau = await _trang_thai_rls(admin_pool)
    await _dat_rls(admin_pool, _TAT_RLS)
    await _gieo_run_tron_tenant(admin_pool)
    await _dat_rls(admin_pool, _BAT_RLS)
    try:
        with pytest.raises(UnscopedReadUnavailable, match="obs.trace_events"):
            await read_run_unscoped(admin_pool, _RUN_ID)
    finally:
        await _khoi_phuc_rls(admin_pool, ban_dau)


async def test_list_runs_all_tenants_raise_thay_vi_tra_rong_khi_RLS_dang_che(admin_pool: Any) -> None:
    """KHÓA: cùng lý do, nhưng đường này còn im hơn — `--list` in bảng rỗng, không ai raise hộ."""
    ban_dau = await _trang_thai_rls(admin_pool)
    await _dat_rls(admin_pool, _TAT_RLS)
    await _gieo_run_tron_tenant(admin_pool)
    await _dat_rls(admin_pool, _BAT_RLS)
    try:
        with pytest.raises(UnscopedReadUnavailable, match="obs.trace_events"):
            await list_runs_all_tenants(admin_pool)
    finally:
        await _khoi_phuc_rls(admin_pool, ban_dau)


async def test_khong_raise_va_van_thay_ca_2_tenant_khi_RLS_khong_ap_dung(admin_pool: Any) -> None:
    """KHÓA mặt còn lại — guard KHÔNG được nổ nhầm, và khi nó không nổ thì hàm phải thật sự đọc
    xuyên tenant.

    Không có bài này thì một guard `raise` vô điều kiện cũng làm 2 bài trên xanh. Bài này cũng khoá
    luôn giá trị nghiệp vụ: đọc được CẢ HAI tenant của cùng một run — thứ mà `tenant_scope_ok` cần
    để bắt run trộn tenant, và thứ mà hướng "lặp từng tenant" sẽ phá.
    """
    ban_dau = await _trang_thai_rls(admin_pool)
    await _dat_rls(admin_pool, _TAT_RLS)
    await _gieo_run_tron_tenant(admin_pool)
    try:
        events = await read_run_unscoped(admin_pool, _RUN_ID)
        assert [e.tenant_id for e in events] == [_TENANT_A, _TENANT_B]

        runs = await list_runs_all_tenants(admin_pool)
        assert (_RUN_ID, 2) in runs
    finally:
        await _khoi_phuc_rls(admin_pool, ban_dau)
