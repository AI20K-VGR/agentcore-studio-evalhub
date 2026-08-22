"""`eval.golden_sets.kb_id` — cột shell nối ngược golden-set tới KB đã sinh ra nó (`evalhub#36`).

## Vì sao bài này tồn tại — review `evalhub#36` (AIE-2), mục 1

Trước bài này, cột `kb_id` chỉ được kiểm bằng đọc **chuỗi** `ddl()` (khuôn hai bài đầu của
`test_eval_scorecards_recipe_hash.py`), và mutation thật trên nhánh PR đo được đúng lỗ mà chính
`schema.py:107-121` tự cảnh báo cho mọi cột thêm sau:

    BASELINE                                        246 passed, 8 skipped
    M1  xoá dòng ALTER (giữ CREATE TABLE)           246 passed, 8 skipped
    M2  xoá NỐT cột trong CREATE TABLE (xoá trọn)   246 passed, 8 skipped
    grep -rn "kb_id" tests/                         0 hit

M1 không phải mutant nhân tạo — nó là chính xác failure mode mà `schema.py:43-45` khai: `CREATE
TABLE IF NOT EXISTS` là **no-op** trên bảng đã có, nên thiếu đường `ALTER` thì máy đồng đội không
bao giờ có cột, và suite vẫn xanh cho tới khi có writer thật. Bài thứ ba dưới đây là bài giết được
M1 — đúng khuôn `test_recipe_hash_...`/`test_recipe_version_...` đã dựng cho hai cột nullable khác
trên cùng file DDL.

## `NULL`, không `NOT NULL` — lý do khác `tenant_id` ngay cạnh, GIỐNG `recipe_hash`/`recipe_version`

`kb_id` trỏ sang `kb.knowledge_bases` — bảng đó CHÍNH NÓ cũng vừa land dạng shell, chưa ai ghi được
`kb_id` thật. `NOT NULL` trần ở đây sẽ khoá cứng mọi writer tương lai phải biết KB trước khi ghi
được golden-set, kể cả golden-set không cần gắn KB. `NULL` đọc đúng nghĩa "golden-set này chưa gắn
KB nào" — không phải giá trị bịa (`schema.py:112-116`).

## Không FK cross-schema — cố ý, theo Decision #4

`kb_id` KHÔNG `REFERENCES kb.knowledge_bases(id)`: cross-schema FK (eval → kb) vi phạm luật "không
FK xuyên schema" áp dụng cho mọi cột trong file này (`schema.py:118-120`). Ràng buộc cặp
`(tenant_id, kb_id)` không cross-tenant là việc của tầng ứng dụng khi có writer thật — bài này KHÔNG
kiểm điều đó, chỉ kiểm cột tồn tại đúng trên cả hai đường DDL.
"""

from __future__ import annotations

from typing import Any

from studio_evalhub.schema import ddl

_COT = """
SELECT data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'eval' AND table_name = 'golden_sets' AND column_name = 'kb_id'
"""


def test_kb_id_co_o_ca_hai_duong_ddl() -> None:
    """Cả `CREATE TABLE` (fresh clone) lẫn `ALTER TABLE … ADD COLUMN IF NOT EXISTS` (DB đã tồn tại).

    Bỏ sót đường thứ hai là cách bảng cũ ở máy đồng đội không bao giờ có cột — đúng failure mode mà
    `schema.py` đã ghi ra cho `tenant_id` và áp cho mọi cột thêm sau, kể cả cột này."""
    sql = ddl()

    assert "    kb_id UUID,\n" in sql, "thiếu cột trong CREATE TABLE ⇒ fresh clone không có cột"
    assert "ALTER TABLE eval.golden_sets ADD COLUMN IF NOT EXISTS kb_id UUID;" in sql, (
        "thiếu đường ALTER ⇒ DB đã tồn tại sẽ KHÔNG bao giờ có cột (CREATE TABLE IF NOT EXISTS là no-op)"
    )


def test_kb_id_nullable_khong_bi_siet_thanh_not_null() -> None:
    """Cột phải **nullable**. Bài này canh một chiều sửa cụ thể: ai đó *"cho chặt lại cho chắc"*.

    `NOT NULL` ở đây khoá cứng writer tương lai phải biết KB trước khi ghi được golden-set — chặt
    hơn cần thiết cho một liên kết chưa ai tiêu thụ, và trên bảng đã có row thì `ADD COLUMN … NOT
    NULL` không `DEFAULT` sẽ **raise** ngay lúc boot."""
    sql = ddl()

    assert "kb_id UUID NOT NULL" not in sql, (
        "kb_id bị siết thành NOT NULL — chặt hơn cần thiết, và raise trên bảng đã có row"
    )
    assert "kb_id UUID DEFAULT" not in sql, "một kb_id mặc định bịa ra tệ hơn một kb_id vắng mặt"


async def test_duong_alter_them_lai_cot_tren_db_da_ton_tai(admin_pool: Any) -> None:
    """**Bài đo.** Gỡ cột khỏi bảng THẬT rồi chạy lại `ddl()` ⇒ cột phải quay lại, và phải `YES` ở
    `is_nullable`.

    Đây là ca *"DB đã tồn tại từ trước"*, thứ mà hai bài đọc chuỗi ở trên không với tới. Một bản vá
    chỉ sửa `CREATE TABLE` sẽ xanh hai bài đó và **đỏ ở đây** — đúng M1 mà review `evalhub#36` gieo
    trên nhánh PR.

    Tự khôi phục: `ddl()` chạy lại ở cuối chính là thứ đem cột về, nên bài không để lại bảng thiếu
    cột cho bài chạy sau — không phụ thuộc thứ tự file, và không cần fixture dọn riêng."""
    async with admin_pool.connection() as conn, conn.transaction():
        await conn.execute("ALTER TABLE eval.golden_sets DROP COLUMN IF EXISTS kb_id")

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
    assert row[0] == "uuid", f"kiểu cột phải là uuid, đo được {row[0]!r}"
    assert row[1] == "YES", "cột phải nullable — writer chưa biết KB vẫn phải ghi được golden-set"
