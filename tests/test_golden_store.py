"""`golden_store` — đọc/ghi golden-set ở `eval.golden_sets` dưới RLS `FORCE`.

Nửa DB của cutover **file → DB**. Bài ở đây chạy trên Postgres thật vì thứ đang được chứng minh
**là** hành vi của RLS: một bản double trong bộ nhớ sẽ trả đúng thứ mình lập trình cho nó trả, kể cả
khi policy thật lọc sạch.

## Ca nguy hiểm nhất, và vì sao nó cần hai kiểu lỗi riêng

Dưới `FORCE ROW LEVEL SECURITY`, **cả ba** trạng thái dưới đây đều cho `SELECT` trả **0 dòng**:

1. tenant này chưa có bộ nào — hợp lệ;
2. connection **chưa** `SET app.tenant_id` — lỗi lập trình;
3. connection bind **tenant khác** — lỗi lập trình, và là lỗi nguy hiểm hơn (nó *trông* như đang
   chạy đúng).

Một API trả `GoldenSet` rỗng gộp cả ba thành cùng một kết quả. `GoldenSetNotFound` vs
`GoldenSetScopeError` tách (1) khỏi (2)+(3); các bài dưới đây khoá đúng chỗ tách đó.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.golden_store import (
    GoldenSetNotFound,
    GoldenSetScopeError,
    read_golden_set,
    write_golden_set,
)

ANKOR_ID = UUID("a0000000-0000-0000-0000-000000000001")
BOREA_ID = UUID("b0000000-0000-0000-0000-000000000001")


def _case(case_id: str, tenant: str, expected: str) -> GoldenCase:
    return GoldenCase(
        case_id=case_id,
        query="Nghỉ phép năm được bao nhiêu ngày?",
        tenant=tenant,
        section_roles=["hr"],
        expected_tenant=tenant,
        expected_section_role="hr",
        expected=expected,
        expected_citation=[f"{tenant}-leave-001#c1"],
    )


async def _bind(conn: Any, tenant_id: UUID) -> None:
    await conn.execute("SELECT set_config('app.tenant_id', %s, true)", (str(tenant_id),))


async def test_ghi_roi_doc_lai_ra_dung_bo(pool: Any) -> None:
    """Vòng tròn cơ bản: `write` → `read` ra **cùng** bộ, qua đúng `GoldenCase` chứ không dict thô."""
    golden = GoldenSet(golden_set_ref="probe-roundtrip", cases=[_case("U-01", "ankor", "12 ngày")])

    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await write_golden_set(conn, golden, ANKOR_ID)
        doc_lai = await read_golden_set(conn, "probe-roundtrip", ANKOR_ID)

    assert doc_lai == golden
    assert isinstance(doc_lai.cases[0], GoldenCase)


async def test_hai_tenant_cung_ref_moi_ben_doc_dung_bo_cua_minh(pool: Any) -> None:
    """**Đây là lý do cả cutover tồn tại.** Hai tenant giữ cùng một `golden_set_ref` với nội dung
    KHÁC nhau, và mỗi bên đọc ra đúng bộ của mình.

    Trước cutover, `_resolve_golden_set_path` glob một thư mục dùng chung ⇒ mọi tenant bị chấm bằng
    cùng một bộ Callisto tĩnh. Bài này là bằng chứng chuyện đó đã hết.

    Nội dung hai bộ cố ý khác nhau ở `expected`: nếu chỉ khác `case_id` thì một bản cài đặt trả nhầm
    bộ vẫn có thể xanh nhờ trùng hợp."""
    ref = "handbook-v1"
    bo_ankor = GoldenSet(golden_set_ref=ref, cases=[_case("A-01", "ankor", "12 ngày")])
    bo_borea = GoldenSet(golden_set_ref=ref, cases=[_case("B-01", "borea", "15 ngày")])

    for tenant_id, bo in ((ANKOR_ID, bo_ankor), (BOREA_ID, bo_borea)):
        async with pool.connection() as conn, conn.transaction():
            await _bind(conn, tenant_id)
            await write_golden_set(conn, bo, tenant_id)

    for tenant_id, mong_doi in ((ANKOR_ID, bo_ankor), (BOREA_ID, bo_borea)):
        async with pool.connection() as conn, conn.transaction():
            await _bind(conn, tenant_id)
            assert await read_golden_set(conn, ref, tenant_id) == mong_doi


async def test_khong_co_bo_thi_raise_chu_khong_tra_bo_rong(pool: Any) -> None:
    """Fail-closed: `GoldenSetNotFound`, **không** phải `GoldenSet(cases=[])`.

    Một bộ 0 case đi tiếp vào `EvalHarness.run()` cho `success_rate` trên mẫu số 0 — hoặc
    `ZeroDivisionError`, hoặc tệ hơn, một con số. Cùng lý lẽ `RunCostError`/`TraceAnswerError`."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        with pytest.raises(GoldenSetNotFound, match="khong-ton-tai|không có golden set"):
            await read_golden_set(conn, "khong-ton-tai", ANKOR_ID)


async def test_chua_bind_tenant_thi_raise_SCOPE_khong_phai_NOTFOUND(pool: Any) -> None:
    """**Bài quan trọng nhất file này.** Connection chưa `SET app.tenant_id` ⇒ `GoldenSetScopeError`,
    **không** phải `GoldenSetNotFound`.

    Dưới RLS `FORCE` cả hai ca đều cho `SELECT` trả 0 dòng, nên một bản cài đặt "cứ 0 dòng thì
    NotFound" sẽ **xanh** ở bài này nếu ta chỉ assert `pytest.raises(Exception)`. Khẳng định đúng
    KIỂU mới tách được *"chưa có bộ"* (trạng thái hợp lệ) khỏi *"quên bind tenant"* (lỗi lập trình,
    và nếu nuốt thì im lặng mãi).

    Ghi sẵn một bộ trước để loại trừ cách đọc khác: bảng **có** dữ liệu cho tenant này, chỉ là phiên
    không nhìn thấy nó."""
    golden = GoldenSet(golden_set_ref="co-that", cases=[_case("U-01", "ankor", "12 ngày")])
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await write_golden_set(conn, golden, ANKOR_ID)

    async with pool.connection() as conn, conn.transaction():
        # KHÔNG bind
        with pytest.raises(GoldenSetScopeError):
            await read_golden_set(conn, "co-that", ANKOR_ID)


async def test_bind_tenant_khac_thi_raise_SCOPE(pool: Any) -> None:
    """Phiên bind Borea nhưng caller hỏi bộ của Ankor ⇒ `GoldenSetScopeError`.

    Nguy hiểm hơn ca "chưa bind" vì nó **trông như đang chạy đúng**: có tenant, có ref, RLS lọc sạch,
    kết quả rỗng. Không có phép kiểm này thì nó đọc thành *"Ankor chưa có bộ"* — một câu sai về một
    tenant khác hẳn tenant đang chạy."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, BOREA_ID)
        with pytest.raises(GoldenSetScopeError, match="nhưng caller hỏi"):
            await read_golden_set(conn, "bat-ky", ANKOR_ID)


async def test_ghi_lai_cung_ref_la_CAP_NHAT_khong_phai_nhan_ban(pool: Any) -> None:
    """`ON CONFLICT (tenant_id, golden_set_ref) DO UPDATE` — nạp lại bộ đã sửa không sinh dòng thứ hai.

    Đường dùng chính là DE cập nhật YAML rồi seed lại. Một `INSERT` trần sẽ bắt caller tự xoá trước,
    và cửa sổ giữa hai câu là lúc bộ **không tồn tại** ⇒ publish của tenant đó vỡ."""
    ref = "cap-nhat"
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await write_golden_set(conn, GoldenSet(golden_set_ref=ref, cases=[_case("U-01", "ankor", "12 ngày")]), ANKOR_ID)
        await write_golden_set(conn, GoldenSet(golden_set_ref=ref, cases=[_case("U-01", "ankor", "15 ngày")]), ANKOR_ID)
        cur = await conn.execute("SELECT count(*) FROM eval.golden_sets WHERE golden_set_ref = %s", (ref,))
        row = await cur.fetchone()
        assert row is not None and row[0] == 1, "ghi lại phải CẬP NHẬT, không thêm dòng"
        doc_lai = await read_golden_set(conn, ref, ANKOR_ID)

    assert doc_lai.cases[0].expected == "15 ngày"


async def test_field_la_trong_jsonb_do_o_luc_doc(pool: Any) -> None:
    """`extra="forbid"` còn hiệu lực trên đường **đọc lại**, không chỉ lúc nạp YAML.

    JSONB được ghi bởi một lần chạy TRƯỚC, và giữa hai lần schema có thể đã đổi. Nếu đường đọc dùng
    `model_construct` (bỏ qua validation) thì một field lạ trong DB đi thẳng vào bộ chấm — đúng lớp
    lỗi `DEC-D18-01` viết ra để chặn, chỉ khác nguồn dữ liệu."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await conn.execute(
            "INSERT INTO eval.golden_sets (tenant_id, golden_set_ref, cases) VALUES (%s, %s, %s::jsonb)",
            (
                ANKOR_ID,
                "co-field-la",
                '[{"case_id":"U-01","query":"q","tenant":"ankor","section_roles":["hr"],'
                '"expected_tenant":"ankor","expected_section_role":"hr","expected":"x",'
                '"expected_citation":[],"field_la_hoac_go_nham":"!"}]',
            ),
        )
        with pytest.raises(Exception, match="field_la_hoac_go_nham"):
            await read_golden_set(conn, "co-field-la", ANKOR_ID)
