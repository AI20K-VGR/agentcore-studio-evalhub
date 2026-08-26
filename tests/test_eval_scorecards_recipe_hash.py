"""`eval.scorecards.recipe_hash` — mục 1 của `evalhub#28` (issue của SWE).

## Vì sao cột này cần, và cần ở ĐÂY

`workbench` đã ghi `recipe_hash` vào `wb.recipes` **và** `wb.recipe_versions` (`workbench#27`), nên câu
*"version này của agent ứng với hash recipe nào"* trả lời được. Câu còn lại thì không: **`Scorecard`
chưa từng được ghi ở đâu cả** — nó sống trong một lần gọi HTTP rồi mất. Kiểm bằng đúng tripwire mà
`schema.py` tự đặt ra:

    grep -rn "INSERT INTO eval" packages/*/src apps/*/src

→ đúng 1 hit, và hit đó là chính dòng comment trong `schema.py` ⇒ **0 writer thật**.

⇒ Không có cột thì mục 2 của `evalhub#28` (SWE ghi `INSERT INTO eval.scorecards` trong `publish()`)
**không có chỗ để ghi**. Cột đi trước writer, không ngược lại — cùng lập luận chi phí mà `DEC-D20-05`
đã dùng cho `tenant_id`: trước writer đầu tiên đây là một dòng DDL trên bảng rỗng, sau đó là migration
trên bảng đã có dữ liệu nhiều tenant.

**Phạm vi khai đúng: cột này KHÔNG tự đóng audit trail.** Nó chỉ làm chỗ để `Scorecard` khai *"tôi
chứng nhận hash X"*. Nối được sang *"X là version nào của agent"* vẫn là một phép **join** sang
`wb.recipes.recipe_hash` — khác schema, nên không có FK, và không PR nào ở đây tạo ra được liên kết đó.
Mục 2 mới là mục làm audit trail chạy.

## `NULL`, không `NOT NULL` — và đây là chỗ khác `tenant_id` ngay cạnh

Hợp đồng là `Scorecard.recipe_hash: str | None`. `DEC-03` **cho phép** `None` và đặt luật fail-closed ở
**consumer** (`publish()` từ chối khi `None`), chứ không cấm giá trị đó tồn tại. Một cột `NOT NULL` ở
đây sẽ **chặt hơn hợp đồng**: nó biến một scorecard hợp lệ-nhưng-chưa-khai thành một row không ghi
được. Và không `DEFAULT`: `NULL` đọc được thành *"scorecard này không khai recipe nào"*, còn một chuỗi
bịa ra đọc thành *"khai một recipe không tồn tại"* — tệ hơn hẳn.

## Ba bài, và bài 3 là bài duy nhất đo

Bài 1/2 đọc **chuỗi** `ddl()`. Chuỗi có chữ không chứng minh Postgres nuốt nó, và **không** chứng minh
cột xuất hiện trên một DB đã tồn tại — `CREATE TABLE IF NOT EXISTS` là **no-op** trên bảng đã có, nên
một bản vá chỉ sửa `CREATE TABLE` sẽ xanh cả hai bài đầu và **vẫn** để máy đồng đội không có cột.

Bài 3 dựng đúng ca đó: gỡ cột khỏi bảng thật (mô phỏng DB có từ trước), chạy lại `ddl()`, đòi cột quay
lại. Đây là bài mà một bản vá thiếu đường `ALTER` **đỏ**, và là lý do file này tồn tại thay vì thêm 2
dòng assert vào `test_eval_schema_rls.py`.
"""

from __future__ import annotations

from typing import Any

from studio_evalhub.schema import ddl

_COT = """
SELECT data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'eval' AND table_name = 'scorecards' AND column_name = 'recipe_hash'
"""


def _khoi_bang(sql: str, ten_bang: str) -> str:
    """Phần DDL nói về đúng một bảng: từ `CREATE TABLE … <ten_bang>` tới `);` đầu tiên, cộng mọi
    dòng `ALTER TABLE <ten_bang>`. Đủ cho các phép grep dưới đây và không kéo bảng khác vào."""
    lines = sql.splitlines()
    out: list[str] = []
    trong_create = False
    for line in lines:
        if line.startswith("CREATE TABLE") and ten_bang in line:
            trong_create = True
        if trong_create:
            out.append(line)
            if line.strip().startswith(");"):
                trong_create = False
        elif line.startswith(f"ALTER TABLE {ten_bang}"):
            out.append(line)
    return "\n".join(out)


def test_recipe_hash_co_o_ca_hai_duong_ddl() -> None:
    """Cả `CREATE TABLE` (fresh clone) lẫn `ALTER TABLE … ADD COLUMN IF NOT EXISTS` (DB đã tồn tại).

    Bỏ sót đường thứ hai là cách bảng cũ ở máy đồng đội không bao giờ có cột — đúng failure mode mà
    `schema.py` đã ghi ra cho `tenant_id` và vẫn áp cho mọi cột thêm sau."""
    sql = ddl()

    assert "    recipe_hash TEXT,\n" in sql, "thiếu cột trong CREATE TABLE ⇒ fresh clone không có cột"
    assert "ALTER TABLE eval.scorecards ADD COLUMN IF NOT EXISTS recipe_hash TEXT;" in sql, (
        "thiếu đường ALTER ⇒ DB đã tồn tại sẽ KHÔNG bao giờ có cột (CREATE TABLE IF NOT EXISTS là no-op)"
    )


def test_recipe_hash_nullable_khong_bi_siet_thanh_not_null() -> None:
    """Cột phải **nullable**. Bài này canh một chiều sửa cụ thể: ai đó *"cho chặt lại cho chắc"*.

    `NOT NULL` chặt hơn hợp đồng `Scorecard.recipe_hash: str | None`, và trên bảng đã có row thì
    `ADD COLUMN … NOT NULL` **không `DEFAULT`** còn **raise** ngay lúc boot — hỏng ở máy người khác,
    không ở máy người sửa."""
    # Cắt về ĐÚNG khối `eval.scorecards` thay vì grep cả chuỗi DDL: `eval.eval_jobs` cũng có cột
    # `recipe_hash`, và ở đó `NOT NULL` là ĐÚNG (job luôn biết hash lúc tạo). Bản trước grep toàn
    # bộ nên bảng mới làm bài này đỏ vì một dòng thuộc bảng khác — một chốt báo nhầm chỗ còn tệ
    # hơn không có chốt, vì nó dạy người sửa đi sai hướng.
    sql = _khoi_bang(ddl(), "eval.scorecards")

    assert "recipe_hash TEXT NOT NULL" not in sql, (
        "recipe_hash bị siết thành NOT NULL — chặt hơn hợp đồng (str | None), và raise trên bảng đã có row"
    )
    assert "recipe_hash TEXT DEFAULT" not in sql, "một hash mặc định bịa ra tệ hơn một hash vắng mặt"


async def test_duong_alter_them_lai_cot_tren_db_da_ton_tai(admin_pool: Any) -> None:
    """**Bài đo.** Gỡ cột khỏi bảng THẬT rồi chạy lại `ddl()` ⇒ cột phải quay lại, và phải `YES` ở
    `is_nullable`.

    Đây là ca *"DB đã tồn tại từ trước"*, thứ mà hai bài đọc chuỗi ở trên không với tới. Một bản vá
    chỉ sửa `CREATE TABLE` sẽ xanh hai bài đó và **đỏ ở đây**.

    Tự khôi phục: `ddl()` chạy lại ở cuối chính là thứ đem cột về, nên bài không để lại bảng thiếu cột
    cho bài chạy sau — không phụ thuộc thứ tự file, và không cần fixture dọn riêng."""
    async with admin_pool.connection() as conn, conn.transaction():
        await conn.execute("ALTER TABLE eval.scorecards DROP COLUMN IF EXISTS recipe_hash")

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
    assert row[0] == "text", f"kiểu cột phải là text, đo được {row[0]!r}"
    assert row[1] == "YES", "cột phải nullable — NOT NULL chặt hơn hợp đồng Scorecard.recipe_hash"
