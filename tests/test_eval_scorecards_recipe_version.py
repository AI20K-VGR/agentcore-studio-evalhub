"""`eval.scorecards.recipe_version` — vế thứ hai của khoá audit. Sinh ra từ review `workbench#28`.

## Vì sao `recipe_hash` một mình không đủ

`workbench#28` ghi hàng audit mang `recipe_hash`, và tưởng thế là đủ để trả lời câu mà `evalhub#28`
mở ra: *"scorecard nào đã chứng nhận **version** nào của agent này"*. Đo lại trên chính ca mà bài test
của PR đó dựng ra (publish 2 lần **cùng một recipe**):

    wb.recipe_versions:  version=1  hash=eb1799fe9556…
                         version=2  hash=eb1799fe9556…
    eval.scorecards:     2 hàng, CÙNG hash, không có cột version

    số version = 2, số hash phân biệt = 1   ⇒ nối bằng hash là MỘT-NHIỀU

Nội dung recipe không đổi ⇒ hash không đổi ⇒ hash **không** phân biệt được version. Câu hỏi vẫn treo.

## Nối vào `wb.recipes`, không phải `wb.recipe_versions`

`wb.recipes` có `UNIQUE (agent_id, tenant_id, version)`; `wb.recipe_versions` **không có** — chính
`publish.py` khai điều đó khi giải thích vì sao `rollback()` phải đọc theo NỘI DUNG chứ không theo số
version. Nên khoá nối duy nhất đúng là `(agent_id, tenant_id, recipe_version)` **vào `wb.recipes`**.

**Cột này chỉ có giá trị nếu `agent_id` của hàng audit khớp `agent_id` của recipe được publish** — đó
là finding riêng ở `workbench#28` (`publish()` hiện không có cổng nào buộc điều đó, dò được: hai bảng
trong cùng transaction khai hai agent khác nhau). Thiếu vế ấy thì khoá 3 cột vỡ ngay ở cột đầu, và cột
này thành trang trí. Hai mục phải land cùng đợt.

## `NULL`, cùng lý do `recipe_hash`

Hàng ghi bởi một writer chưa biết truyền version (kể cả `workbench#28` ở bản hiện tại) phải ghi được.
`NOT NULL` vừa chặt hơn cần thiết vừa raise trên bảng đã có row.

## Ba bài, bài 3 là bài duy nhất đo

Hai bài đầu đọc **chuỗi** `ddl()`; chúng không với tới ca *"DB đã tồn tại"* — `CREATE TABLE IF NOT
EXISTS` là no-op trên bảng đã có, nên một bản vá chỉ sửa `CREATE TABLE` vẫn xanh cả hai. Bài 3 gỡ cột
khỏi bảng thật rồi chạy lại `ddl()` — đúng ca đó.
"""

from __future__ import annotations

from typing import Any

from studio_evalhub.schema import ddl

_COT = """
SELECT data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'eval' AND table_name = 'scorecards' AND column_name = 'recipe_version'
"""


def test_recipe_version_co_o_ca_hai_duong_ddl() -> None:
    """`CREATE TABLE` (fresh clone) **và** `ALTER TABLE … ADD COLUMN IF NOT EXISTS` (DB đã tồn tại)."""
    sql = ddl()

    assert "    recipe_version INT,\n" in sql, "thiếu cột trong CREATE TABLE ⇒ fresh clone không có cột"
    assert "ALTER TABLE eval.scorecards ADD COLUMN IF NOT EXISTS recipe_version INT;" in sql, (
        "thiếu đường ALTER ⇒ DB đã tồn tại sẽ KHÔNG bao giờ có cột (CREATE TABLE IF NOT EXISTS là no-op)"
    )


def test_recipe_version_nullable_khong_bi_siet_thanh_not_null() -> None:
    """Nullable. `NOT NULL` chặn được cả writer hiện tại của `workbench#28` (chưa truyền version) và
    raise trên bảng đã có row nếu không kèm `DEFAULT`."""
    sql = ddl()

    assert "recipe_version INT NOT NULL" not in sql, (
        "recipe_version bị siết NOT NULL — chặn writer chưa truyền version, và raise trên bảng đã có row"
    )
    assert "recipe_version INT DEFAULT" not in sql, "một version mặc định bịa ra tệ hơn một version vắng mặt"


async def test_duong_alter_them_lai_cot_tren_db_da_ton_tai(admin_pool: Any) -> None:
    """**Bài đo.** Gỡ cột khỏi bảng THẬT rồi chạy lại `ddl()` ⇒ cột quay lại, `integer`, nullable.

    Tự khôi phục: chính `ddl()` ở cuối đem cột về, nên không để lại bảng thiếu cột cho bài chạy sau."""
    async with admin_pool.connection() as conn, conn.transaction():
        await conn.execute("ALTER TABLE eval.scorecards DROP COLUMN IF EXISTS recipe_version")

    async with admin_pool.connection() as conn:
        cur = await conn.execute(_COT)
        assert await cur.fetchone() is None, "tiền đề của bài sai: cột vẫn còn sau khi DROP"

    async with admin_pool.connection() as conn, conn.transaction():
        await conn.execute(ddl())

    async with admin_pool.connection() as conn:
        cur = await conn.execute(_COT)
        row = await cur.fetchone()

    assert row is not None, (
        "chạy lại ddl() KHÔNG đem cột về ⇒ thiếu đường ALTER. CREATE TABLE IF NOT EXISTS là no-op "
        "trên bảng đã có, nên DB của đồng đội sẽ vĩnh viễn không có cột này."
    )
    assert row[0] == "integer", f"kiểu cột phải là integer, đo được {row[0]!r}"
    assert row[1] == "YES", "cột phải nullable — writer chưa truyền version vẫn phải ghi được"
