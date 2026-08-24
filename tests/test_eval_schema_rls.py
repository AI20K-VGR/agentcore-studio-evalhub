"""`eval.golden_sets` + `eval.scorecards` — `tenant_id` + RLS. `DEC-D20-05`.

`kb#24` đã lật `eval.scorecards` từ *KHÔNG CẦN* sang **CẦN RLS**, và tiêu chí là **bản chất data**,
không phải *ai đọc*: `harness.py:463` đổ `actual`/`expected` vào `results JSONB`, tức bảng chứa
**answer-text của tenant**. Một bảng chứa nội dung tài liệu của khách hàng thì hàng rào không phải
tuỳ chọn, bất kể hôm nay có ai đọc nó hay chưa.

## Vì sao land HÔM NAY chứ không phải "khi có writer"

Đây là lập luận về **chi phí**, không phải về sự chỉn chu:

- land **trước** writer đầu tiên ⇒ một dòng DDL trên bảng rỗng;
- land **sau** ⇒ migration trên bảng đã có dữ liệu của nhiều tenant, **cộng** một câu hỏi không trả
  lời được: *"dữ liệu đã ghi trước đó thuộc tenant nào"*. Không có cột thì không có câu trả lời, và
  đoán là cách tạo ra một fence tin được nhưng sai.

Hôm nay là ngày `Scorecard` **thật** đầu tiên tồn tại (T3) ⇒ đây là **ngày cuối món này còn rẻ**.
Tự khai của design-note D11 `§5`: workspace có RLS trên **1/11** bảng, hai bảng của AIE-2 là **0/2**.

## Phạm vi — chỉ `schema.py` của evalhub

`ensure_all_schemas` (`apps/studio/core/schema.py`) **direct-import** `ddl()` của quadrant này, nên
thêm cột + policy ở đây là đủ; **không** đụng `apps/studio` (antichain, plan.md *"Dependency matrix &
file-ownership"*).

## Hai tầng bài, và tầng hai mới là tầng đo

`ddl()` là một **chuỗi**. Một bài chỉ `assert "ENABLE ROW LEVEL SECURITY" in ddl()` chứng minh chuỗi
có chữ đó — **không** chứng minh Postgres chấp nhận nó, càng không chứng minh hàng rào cắn. Đúng lớp
lỗi D19: *state chạy ≠ state khai*. Nên file này có cả bài chạy DDL thật rồi thử đọc/ghi chéo tenant.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from studio_evalhub.schema import ddl

ANKOR_ID = UUID("a0000000-0000-0000-0000-000000000001")
BOREA_ID = UUID("b0000000-0000-0000-0000-000000000001")

_BANG = ("eval.golden_sets", "eval.scorecards")


def test_ddl_bat_rls_va_co_policy_cho_ca_hai_bang() -> None:
    """**Bài `M-G6`.** `ddl()` phải bật `ENABLE` **và** `FORCE ROW LEVEL SECURITY` + có policy cho
    **cả hai** bảng.

    `FORCE` không phải phần thêm: không có nó, policy **không cắn `studio_owner`** — mà
    `ensure_all_schemas()` chạy đúng bằng admin pool. Một fence bỏ qua chính vai đang chạy migration
    là fence có lỗ đúng ở chỗ dễ dùng nhất.

    Kiểm **cả hai** bảng riêng lẻ thay vì đếm tổng: `golden_sets` là bảng dễ bị bỏ quên vì nó "chỉ
    chứa đề bài" — nhưng golden-set mang `query` + `expected` của tenant, tức cũng là nội dung của
    khách hàng."""
    sql = ddl()

    for bang in _BANG:
        assert f"ALTER TABLE {bang} ENABLE ROW LEVEL SECURITY" in sql, f"{bang} chưa bật RLS"
        assert f"ALTER TABLE {bang} FORCE ROW LEVEL SECURITY" in sql, (
            f"{bang} thiếu FORCE — policy sẽ không cắn studio_owner, tức không cắn ensure_all_schemas()"
        )
        policy = f"{bang.replace('.', '_')}_tenant_isolation"
        assert f"CREATE POLICY {policy} ON {bang}" in sql, f"{bang} chưa có policy riêng ({policy})"

    # Khoá đúng biểu thức fail-closed: session không set `app.tenant_id` ⇒ `NULLIF(...)` ra NULL ⇒
    # `tenant_id = NULL` không bao giờ đúng ⇒ thấy/ghi 0 row, thay vì raise hoặc rò.
    assert "NULLIF(current_setting('app.tenant_id', true), '')::uuid" in sql


def test_tenant_id_la_not_null_o_ca_hai_bang() -> None:
    """`tenant_id` phải `NOT NULL` — nullable là cách một row vô chủ lọt vào bảng và **không policy
    nào với tới nó** (`tenant_id = <bất kỳ>` đều false với NULL), tức một row không ai đọc được và
    cũng không ai xoá được bằng đường thường.

    Kiểm cả đường `CREATE TABLE` (fresh clone) lẫn đường `ALTER TABLE ADD COLUMN` (DB đã tồn tại từ
    trước T6) — hai đường, và bỏ sót đường thứ hai là cách bảng cũ ở máy đồng đội không bao giờ có
    cột."""
    sql = ddl()

    assert sql.count("tenant_id UUID NOT NULL") >= len(_BANG), (
        "tenant_id phải NOT NULL ở cả hai bảng — nullable ⇒ row vô chủ không policy nào với tới"
    )
    for bang in _BANG:
        assert f"ALTER TABLE {bang} ADD COLUMN IF NOT EXISTS tenant_id UUID NOT NULL" in sql, (
            f"{bang} thiếu đường ALTER — DB đã tồn tại trước T6 sẽ không bao giờ có cột "
            "(CREATE TABLE IF NOT EXISTS là no-op trên bảng đã có)"
        )


def test_ddl_idempotent_chay_hai_lan_khong_doi() -> None:
    """`ddl()` gọi hai lần trả **cùng một chuỗi**, và mọi câu đều có dạng idempotent.

    `ensure_all_schemas()` chạy mỗi lần boot, nên một câu không idempotent làm hỏng lần boot thứ hai
    — trên máy đồng đội, không phải trên máy mình."""
    assert ddl() == ddl()

    sql = ddl()
    assert "CREATE SCHEMA IF NOT EXISTS eval" in sql
    for bang in _BANG:
        assert f"CREATE TABLE IF NOT EXISTS {bang}" in sql
        # `CREATE POLICY` không có `IF NOT EXISTS` ⇒ phải `DROP POLICY IF EXISTS` trước, đúng quy ước
        # `wb`/`kb`. Thiếu vế này là lỗi ở lần boot thứ hai, không phải lần đầu.
        policy = f"{bang.replace('.', '_')}_tenant_isolation"
        assert f"DROP POLICY IF EXISTS {policy} ON {bang}" in sql


async def _bind(conn: Any, tenant_id: UUID) -> None:
    await conn.execute("SELECT set_config('app.tenant_id', %s, true)", (str(tenant_id),))


async def test_rls_that_su_can_tren_postgres_that(admin_pool: Any, pool: Any) -> None:
    """**Bài đo, không phải bài đọc chuỗi.** Chạy DDL thật rồi thử ghi/đọc chéo tenant.

    Ba vế, và vế thứ ba là vế hay bị bỏ:

    1. ghi đúng tenant ⇒ được;
    2. đọc bằng tenant KHÁC ⇒ thấy **0 row** (fail-closed, không raise);
    3. **không set `app.tenant_id`** ⇒ cũng thấy **0 row**. Đây là ca mặc định của mọi connection
       chưa qua middleware, và một fence chỉ chặn "tenant sai" mà bỏ qua "không có tenant" là fence
       mở toang ở trạng thái mặc định.

    Bài này là thứ phân biệt *"DDL có chữ RLS"* với *"RLS đang cắn"*. `ddl()` chỉ là một chuỗi cho
    tới khi Postgres nuốt nó."""
    del admin_pool  # ordering: ensure_all_schemas + grants đã chạy qua fixture

    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await conn.execute(
            "INSERT INTO eval.scorecards (agent_id, tenant_id, golden_set_ref, results, aggregate, gate) "
            "VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)",
            ("agent-rls-probe", ANKOR_ID, "callisto-golden-30-v1", "[]", "{}", "{}"),
        )

    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        cur = await conn.execute("SELECT count(*) FROM eval.scorecards WHERE agent_id = %s", ("agent-rls-probe",))
        row = await cur.fetchone()
    assert row is not None and row[0] == 1, "tenant đúng phải đọc được row của chính mình"

    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, BOREA_ID)
        cur = await conn.execute("SELECT count(*) FROM eval.scorecards WHERE agent_id = %s", ("agent-rls-probe",))
        row = await cur.fetchone()
    assert row is not None and row[0] == 0, "tenant khác phải thấy 0 row — RLS không cắn"

    async with pool.connection() as conn, conn.transaction():
        cur = await conn.execute("SELECT count(*) FROM eval.scorecards WHERE agent_id = %s", ("agent-rls-probe",))
        row = await cur.fetchone()
    assert row is not None and row[0] == 0, (
        "session KHÔNG set app.tenant_id phải thấy 0 row (fail-closed). Đây là trạng thái mặc định "
        "của mọi connection chưa qua middleware — fence bỏ qua ca này là fence mở toang."
    )


async def test_rls_chan_ghi_cheo_tenant(admin_pool: Any, pool: Any) -> None:
    """`WITH CHECK` — bind tenant X nhưng ghi row mang `tenant_id` của Y ⇒ Postgres từ chối.

    Đối xứng với bài trên: `USING` chặn **đọc**, `WITH CHECK` chặn **ghi**. Một policy chỉ có `USING`
    vẫn cho ghi row của tenant khác vào bảng — rồi chính mình không đọc lại được nó.

    **Bắt đúng lỗi RLS, không bắt `psycopg.Error` trần.** Đo được lý do: khi gieo đỏ trước T6, cột
    `tenant_id` chưa tồn tại nên INSERT ném `UndefinedColumn` — vốn **cũng là** một `psycopg.Error`
    ⇒ bài xanh trong khi hàng rào chưa hề tồn tại. Một bài chỉ bắt lớp cha là bài xanh với cả *"RLS
    chặn"* lẫn *"bảng còn chưa có cột"*. Cùng lớp lỗi với `match=` khớp nhầm chỗ ở T4."""
    del admin_pool
    import psycopg

    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"):
        async with pool.connection() as conn, conn.transaction():
            await _bind(conn, ANKOR_ID)
            await conn.execute(
                "INSERT INTO eval.scorecards (agent_id, tenant_id, golden_set_ref, results, aggregate, gate) "
                "VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)",
                ("agent-cross-write", BOREA_ID, "callisto-golden-30-v1", "[]", "{}", "{}"),
            )


async def test_ddl_is_safe_on_populated_table(admin_pool: Any, pool: Any) -> None:
    """`ddl()` chạy lại trên bảng **đã có dữ liệu** không được raise — bất biến giữ cho
    `ADD COLUMN … NOT NULL` (`schema.py`) còn an toàn sau khi writer thật đã land (`evalhub#41`).

    ## Bài này thay cho một comment đã trôi

    `schema.py` từng dạy một tripwire: *"`grep -rn "INSERT INTO eval" …` ra **đúng 1 hit** = chưa có
    writer = `ADD COLUMN … NOT NULL` còn an toàn"*, và tự ràng buộc rằng luật đó phải được sửa
    **trong cùng PR** land writer. Writer đã land ở `studio_workbench/publish.py` (`INSERT INTO
    eval.scorecards` trong `publish()`), luật đọc **không** được sửa cùng lúc ⇒ comment dạy ngược
    suốt từ đó. Một phép kiểm bằng chữ thì trôi được; bài test thì không.

    ## Tính chất đang thật sự đỡ, và bài này đo đúng nó

    Không phải *"bảng rỗng"* (hết đúng từ khi có writer), mà là **không tồn tại row có trước cột**:

    1. `tenant_id` vào DDL ở D20, **trước** writer đầu tiên (D23);
    2. `ensure_all_schemas()` chạy mỗi lần boot ⇒ `ALTER` áp trước mọi lần ghi;
    3. writer khai `tenant_id` **tường minh** trong danh sách cột ⇒ DB thiếu cột thì chính câu
       `INSERT` đỏ, không phải chờ tới `ALTER`.

    Bài này dựng đúng trạng thái *"bảng đã có row thật"* rồi chạy lại **toàn bộ** `ddl()` — tức đi
    qua cả `CREATE TABLE IF NOT EXISTS` (no-op), cả 4 câu `ADD COLUMN IF NOT EXISTS`, cả
    `DROP POLICY`/`CREATE POLICY`. Đó là chính xác thứ xảy ra ở **lần boot thứ hai của một môi
    trường đang chạy**, và là ca mà `test_ddl_idempotent_chay_hai_lan_khong_doi` **không** phủ: bài
    đó so hai chuỗi bằng nhau, không đưa chuỗi nào cho Postgres nuốt trên bảng có dữ liệu.

    Đo được (mutant `M-T1`): gieo `ADD COLUMN IF NOT EXISTS ghi_chu TEXT NOT NULL` — một cột
    `NOT NULL` mới, không `DEFAULT` — vào `ddl()` ⇒ bài này **đỏ** với `NotNullViolation`, đúng điều
    kiện lật thứ hai ghi trong `schema.py`. `test_ddl_idempotent_chay_hai_lan_khong_doi` **vẫn
    xanh**, vì nó so hai chuỗi chứ không đưa chuỗi nào cho Postgres.

    Chỗ nó đỏ phụ thuộc trạng thái DB, và **cả hai chỗ đều là cùng một khuyết tật**:

    - DB **sạch** (bảng vừa tạo, rỗng) ⇒ `ALTER` thêm cột lọt, rồi `INSERT` của bài này đỏ vì không
      cấp `ghi_chu` — đúng thứ **writer thật cũng sẽ gặp**, vì writer khai danh sách cột tường minh;
    - DB **đã có row** từ lần chạy trước ⇒ chính `ALTER` đỏ ngay ở `ensure_all_schemas()` của fixture.

    Nói cách khác bài này bắt được khuyết tật ở **cả hai phía của thứ tự land** — đúng cặp tính chất
    (1)+(3) mà `schema.py` viện làm lý do an toàn."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await conn.execute(
            "INSERT INTO eval.scorecards (agent_id, tenant_id, golden_set_ref, results, aggregate, gate) "
            "VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)",
            ("agent-ddl-replay", ANKOR_ID, "callisto-golden-30-v1", "[]", "{}", "{}"),
        )
        await conn.execute(
            "INSERT INTO eval.golden_sets (tenant_id, golden_set_ref, cases) VALUES (%s, %s, %s::jsonb)",
            (ANKOR_ID, "ddl-replay-probe", "[]"),
        )

    # Bảng giờ có dữ liệu thật. Chạy lại NGUYÊN `ddl()` bằng owner-pool, đúng như `ensure_all_schemas()`.
    async with admin_pool.connection() as conn:
        await conn.execute(ddl())

    # Và dữ liệu phải còn nguyên — một `ddl()` "an toàn" mà xoá mất row thì còn tệ hơn raise.
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        cur = await conn.execute("SELECT count(*) FROM eval.scorecards WHERE agent_id = %s", ("agent-ddl-replay",))
        row = await cur.fetchone()
    assert row is not None and row[0] == 1, "ddl() chạy lại không được làm mất row đã có"
