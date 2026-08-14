"""Ô DoD D19: `cost` **cùng-1-số** khớp UI-test ↔ trace, tái lập — T4 (`kit#123`).

## Điều kiện của bài này là NÓ PHẢI ĐỎ ĐƯỢC

`cost` của mọi event trong hệ thống hôm nay là hằng số `0.0` (`engine:interpreter.py:73` `_NO_COST`,
`:438` `cost=_NO_COST`). Chạy "cùng-1-số" trên một trace thật hôm nay là so `0.0 == 0.0` — **xanh với
mọi cài đặt**, kể cả mặt đọc trả hằng số, kể cả mặt đọc không đọc gì. Nên trace gieo ở đây **bắt
buộc**: khác 0, bất đối xứng, và `cost` **mâu thuẫn có chủ đích** với `tokens` ở ít nhất một event.

## BA lớp, không phải hai

```text
ghi bằng chính sink apps/studio (PgTraceWriter)  ──▶  obs.trace_events
              ┌───────────────────────────────────────┼──────────────────────────────┐
              ▼                                       ▼                              ▼
 A: run_cost_from_trace(read_run_unscoped(...))   B: SELECT round(sum(cost),6)     C: render_run_cases(...)
    đường đọc evalhub, qua _row_to_event    SQL thô, KHÔNG qua code mình     chuỗi UI-test in ra
```

- **A** — nếu chỉ có A thì đang tin chính hàm mình viết.
- **B** — đường **độc lập**, cố ý không dùng code evalhub. Đúng thứ `kb#22` thiếu, và là lý do bài
  của DE không đỏ được.
- **C** — A≡B chỉ chứng minh *phép cộng*. Ô DoD nói **UI-test↔trace**, mà UI-test là **chuỗi người
  đọc nhìn**: một renderer in nhầm cột, làm tròn lại, hay quên dòng cost vẫn để A≡B xanh (`E-1`).

Số kỳ vọng **viết tay** ở cả ba vế; không vế nào lấy số từ vế khác.

## Luật assert rút từ T3 — áp cho lớp C

`assert <chuỗi> in out` trên **cả** output của `render_run_cases` gần như không bao giờ là một phép
kiểm: bảng mang khối caveat prose dài, và mutant `M-C6` đã chứng minh hai bài độ-chính-xác xanh vì
chuỗi cần tìm nằm sẵn trong lời giải thích. Nên lớp C ở đây neo vào **đúng dòng** và có **đối chứng
âm** (đổi số ⇒ chuỗi phải đổi).
"""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

import pytest
from studio_app.core._db import Pool
from studio_app.obs.trace_writer import PgTraceWriter
from studio_contracts.nodes import NodeType
from studio_contracts.trace import Tokens, TraceEvent
from studio_evalhub.harness import SmokeResult
from studio_evalhub.render import render_run_cases
from studio_evalhub.run_report import TRACE_SOURCE_POSTGRES, read_run_unscoped, run_cost_from_trace

_RUN_ID = "run-d19-cung-1-so"
_TENANT = UUID("a0000000-0000-0000-0000-000000000001")

# Số kỳ vọng VIẾT TAY — tính ngoài code, ghim thẳng. Không vế nào tính bằng hàm đang test.
#
#   per-event cost : [0.000291, 0.001578, 0.010125, 0.0, 0.0, 0.0]
#   sum(...)       : 0.011994000000000001     ← KHÔNG làm tròn
#   round(sum, 6)  : 0.011994                 ← luật cộng của kb#22
_TONG_KY_VONG = 0.011994
_TONG_KHONG_LAM_TRON = 0.011994000000000001
_SO_EVENT = 6


def _trace_gieo() -> list[TraceEvent]:
    """6 event: 3 cost khác nhau khác 0, 3 cost `0`, và `tokens` **mâu thuẫn** `cost` ở event 3.

    Mâu thuẫn có chủ đích ở `n3`: `cost` đã lưu là `0.010125` trong khi `tokens` chỉ có `1/1`
    (`cost_of(1, 1)` ≈ `0.000018`). Một mặt đọc tính lại từ tokens sẽ **không** ra `0.011994` ở bất
    kỳ vế nào của bài này.
    """
    khung = [
        (1, NodeType.LLM_STEP, 0.000291, Tokens(prompt=37, completion=12)),
        (2, NodeType.LLM_STEP, 0.001578, Tokens(prompt=211, completion=63)),
        (3, NodeType.LLM_STEP, 0.010125, Tokens(prompt=1, completion=1)),  # ← mâu thuẫn có chủ đích
        (4, NodeType.KB_RETRIEVE, 0.0, Tokens(prompt=0, completion=0)),
        (5, NodeType.TOOL_CALL, 0.0, Tokens(prompt=0, completion=0)),
        (6, NodeType.END, 0.0, Tokens(prompt=0, completion=0)),
    ]
    return [
        TraceEvent(
            event_id=f"{_RUN_ID}-e{seq}",
            run_id=_RUN_ID,
            agent_id="agent-d19",
            tenant_id=_TENANT,
            node_id=f"n{seq}",
            node_type=node_type,
            ts=f"2026-08-13T09:00:0{seq}+00:00",
            inputs_hash="stub",
            outputs={},
            tokens=tokens,
            cost=cost,
        )
        for seq, node_type, cost, tokens in khung
    ]


async def _ghi_trace(pool: Pool) -> None:
    """Ghi bằng **chính sink của `apps/studio`**, không bằng INSERT tự chế.

    Dùng `PgTraceWriter` chứ không tự viết SQL insert là có lý do: nếu bài này tự dựng hàng thì nó
    khẳng định về một bảng *giống* `obs.trace_events`, không phải về đường mà trace thật đi qua. Kiểu
    dữ liệu trên dây (`Jsonb` cho `tokens`, `NUMERIC` cho `cost`) là một phần của thứ đang được đo.
    """
    writer = PgTraceWriter(pool)
    for event in _trace_gieo():
        await writer.write(event)


async def _mat_B_sql_tho(pool: Pool, run_id: str) -> float:
    """Mặt **B** — SQL thô, **KHÔNG** đi qua một dòng code nào của `studio_evalhub`.

    Đây là chỗ bài này khác bài của `kb#22`: ở đó cả hai vế là cùng một lời gọi cùng một hàm thuần
    (`f(x) == f(x)`, xanh với mọi cài đặt). Ở đây vế thứ hai đọc thẳng từ Postgres và cộng bằng
    Postgres, nên nó **không thể** cùng sai một kiểu với vế A.

    `round(sum(cost)::numeric, 6)` ghim đúng luật cộng của `kb#22` **ở phía DB**, tức luật đó bị
    khẳng định hai lần bằng hai bộ máy khác nhau.
    """
    async with pool.connection() as conn:
        cur = await conn.execute(
            "SELECT round(sum(cost)::numeric, 6) FROM obs.trace_events WHERE run_id = %s",
            (run_id,),
        )
        row = await cur.fetchone()
    assert row is not None and row[0] is not None, "mặt B không đọc được gì — bài sẽ vacuous"
    return float(row[0])


def _dong_cost(out: str) -> str:
    """Rút đúng dòng cost. Xem docstring module về lý do không assert trên cả output."""
    dong = [d for d in out.splitlines() if d.startswith("cost (Σ, USD)")]
    assert len(dong) == 1, f"phải có đúng 1 dòng cost, thấy {len(dong)}"
    return dong[0]


def _results() -> list[SmokeResult]:
    return [
        SmokeResult(
            case_id="HB-01",
            expected="3 ngày làm việc",
            actual="Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
            success=True,
            citation_accuracy=1.0,
            expects_refusal=False,
        )
    ]


# ── ô DoD: ba lớp cùng một số ───────────────────────────────────────────────────────────────────


async def test_cost_cung_1_so_ba_lop_A_B_C(admin_pool: Pool, pool: Pool) -> None:
    """`run_cost_from_trace` ↔ `SELECT round(sum(cost),6)` ↔ chuỗi UI-test — **cùng một số**.

    Ba vế, ba con đường, một số kỳ vọng viết tay `0.011994`.

    Vế phụ `!= 0.011994000000000001` giữ luật cộng `round(·, 6)` sống ở tầng giá trị: hai số đó in ra
    `.4f` đều thành `"0.0120"`, nên nếu chỉ so chuỗi thì lệch này **vô hình** — đúng lý do
    `DEC-D19-04` chốt tầng so là **giá trị**, không phải chuỗi.
    """
    del admin_pool  # thứ tự thôi — schema/grant phải có trước DML của app-role
    await _ghi_trace(pool)

    # A — đường đọc evalhub, qua read_run_unscoped → _row_to_event (NUMERIC → Decimal → float)
    events = await read_run_unscoped(pool, _RUN_ID)
    mat_a = run_cost_from_trace(events)

    # B — SQL thô, đường độc lập
    mat_b = await _mat_B_sql_tho(pool, _RUN_ID)

    # C — chuỗi UI-test thật sự in ra
    out = render_run_cases(
        _results(),
        run_id=_RUN_ID,
        golden_set_ref="golden-30@d19",
        trace_source=TRACE_SOURCE_POSTGRES,
        run_cost=mat_a,
    )
    dong_c = _dong_cost(out)

    assert mat_a.cost == _TONG_KY_VONG
    assert mat_b == _TONG_KY_VONG
    assert dong_c.endswith("0.011994")

    assert mat_a.cost == mat_b, "A ≠ B — đường đọc evalhub lệch với chính Postgres"
    assert mat_a.cost != _TONG_KHONG_LAM_TRON, "thiếu round(·, 6) — lệch luật cộng của kb#22"
    assert mat_a.event_count == _SO_EVENT, "Σcost không được in mà thiếu mẫu số (E-6)"
    assert f"{_SO_EVENT} event" in out


async def test_lop_C_doi_chung_am_doi_so_thi_chuoi_phai_doi(admin_pool: Pool, pool: Pool) -> None:
    """Lớp C không được xanh bằng một hằng số in cứng.

    Bài trên khẳng định chuỗi **chứa** `0.011994`. Một renderer in hằng số `"0.011994"` cũng thoả.
    Đối chứng âm: đưa vào một `RunCost` khác ⇒ dòng cost phải đổi theo.
    """
    del admin_pool
    await _ghi_trace(pool)
    events = await read_run_unscoped(pool, _RUN_ID)
    mat_a = run_cost_from_trace(events)

    khac = render_run_cases(
        _results(),
        run_id=_RUN_ID,
        golden_set_ref="golden-30@d19",
        trace_source=TRACE_SOURCE_POSTGRES,
        run_cost=replace(mat_a, cost=0.999999),
    )

    assert _dong_cost(khac).endswith("0.999999")
    assert "0.011994" not in _dong_cost(khac)


# ── bài đối trọng: phép so PHẢI đỏ được ─────────────────────────────────────────────────────────


async def test_doi_trong_mat_B_KHONG_di_qua_code_evalhub(
    admin_pool: Pool, pool: Pool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bài đối trọng **canh chính mặt B** — mutant `M-C7`.

    ## Bản đầu của bài này KHÔNG giết được `M-C7`, giữ vết vì đó là bài học

    Bản đầu dựng theo kiểu: A đọc `events` vào RAM, `UPDATE` DB sau lưng nó, rồi khẳng định
    `A ≠ B`. Gieo `M-C7` (`_mat_B_sql_tho` → `run_cost_from_trace(await read_run_unscoped(...))`) ⇒ mutant
    **SỐNG**, vì bản thay thế cũng **đọc lại DB** nên cũng thấy giá trị mới ⇒ `A ≠ B` vẫn đúng.

    Phép thử đó đo *"B có đọc lại DB không"*, trong khi bất biến cần đo là *"B có đi qua code
    `studio_evalhub` không"*. Hai câu khác nhau, và chỉ câu thứ hai mới là thứ làm bài "cùng-1-số"
    hết vacuous.

    ## Cách dựng đúng: bẻ đường đọc evalhub, rồi xem mặt B có đổi theo không

    - B **thật sự độc lập** (SQL thô + `sum` của Postgres) ⇒ **không đổi** ⇒ vẫn ra số viết tay.
    - B đi qua `run_cost_from_trace` (`M-C7`) ⇒ nhận giá trị đã bị bẻ ⇒ **bài này đỏ**.

    Nếu `M-C7` sống, finding mình gửi DE ở `kb#22` (*"hai vế là cùng một lời gọi cùng một hàm
    thuần — `f(x) == f(x)` xanh với mọi cài đặt"*) tự động áp cho chính mình.
    """
    del admin_pool
    await _ghi_trace(pool)

    def _duong_doc_bi_be(events: list[TraceEvent]) -> object:
        del events
        return replace(run_cost_from_trace(_trace_gieo()), cost=9.999999)

    # Bẻ trong CHÍNH module test này: `_mat_B_sql_tho` tra tên ở global của module, nên nếu nó có
    # gọi `run_cost_from_trace` thì lời gọi đó rơi vào bản đã bẻ.
    monkeypatch.setitem(globals(), "run_cost_from_trace", _duong_doc_bi_be)

    mat_b = await _mat_B_sql_tho(pool, _RUN_ID)

    assert mat_b == _TONG_KY_VONG, (
        f"mặt B đổi theo khi bẻ đường đọc evalhub (ra {mat_b}) ⇒ nó KHÔNG độc lập — đúng mutant "
        "M-C7, và là hình tautology đã gửi finding cho DE ở kb#22."
    )


async def test_doi_trong_phep_so_do_duoc_khi_DB_doi(admin_pool: Pool, pool: Pool) -> None:
    """Bài đối trọng thứ hai — chứng minh phép so **đỏ được**, không phải luôn khớp.

    Thiếu nó thì *"cùng-1-số"* không phân biệt được **khớp** với **cả hai cùng rỗng**. Cách dựng: A
    đọc `events` vào RAM, rồi `UPDATE` thẳng `obs.trace_events` sau lưng nó — từ giây đó sự thật
    trong DB đã đổi mà `events` trong tay A thì không, nên hai mặt **phải** lệch.

    Bài này **không** giết `M-C7` (đã đo: mutant cũng đọc lại DB nên cũng thấy số mới). Nó canh một
    bất biến khác — *phép so có răng* — và được giữ tách bạch với bài trên thay vì gộp, vì gộp hai
    bất biến vào một bài là cách nhanh nhất để mất một trong hai.
    """
    del admin_pool
    await _ghi_trace(pool)

    events = await read_run_unscoped(pool, _RUN_ID)
    mat_a = run_cost_from_trace(events)
    assert mat_a.cost == _TONG_KY_VONG

    # Sửa cost của MỘT event sau lưng A: 0.000291 → 1.000291 (chênh đúng 1.0, số viết tay)
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE obs.trace_events SET cost = %s WHERE event_id = %s",
            (1.000291, f"{_RUN_ID}-e1"),
        )

    mat_b_sau_khi_sua = await _mat_B_sql_tho(pool, _RUN_ID)

    assert mat_b_sau_khi_sua == 1.011994, "mặt B không thấy thay đổi trong DB — nó không đọc DB"
    assert mat_a.cost != mat_b_sau_khi_sua, (
        "A vẫn khớp B sau khi DB đã đổi ⇒ mặt B KHÔNG độc lập (nó đọc lại chính events của A). "
        "Đây đúng mutant M-C7, và là hình tautology đã gửi finding cho DE ở kb#22."
    )


async def test_doi_trong_lop_C_bat_duoc_render_lam_tron_mat(admin_pool: Pool, pool: Pool) -> None:
    """Lớp C phải đỏ được khi renderer làm mất chữ số — `E-1` dựng thành phép đo.

    A≡B vẫn xanh khi renderer in `.2f`, vì cả hai đều ở tầng giá trị. Bài này là chỗ duy nhất trong
    bộ T4 nhìn thấy `E-1`.
    """
    del admin_pool
    await _ghi_trace(pool)
    events = await read_run_unscoped(pool, _RUN_ID)
    mat_a = run_cost_from_trace(events)

    dong = _dong_cost(
        render_run_cases(
            _results(),
            run_id=_RUN_ID,
            golden_set_ref="golden-30@d19",
            trace_source=TRACE_SOURCE_POSTGRES,
            run_cost=mat_a,
        )
    )

    gia_tri_in = dong.split()[-1]
    assert gia_tri_in == f"{_TONG_KY_VONG:.6f}"
    assert gia_tri_in != "0.01", "renderer làm tròn `.2f` — cost thật mất chữ số (E-1)"
    assert len(gia_tri_in.split(".")[1]) == 6, "phải in đủ 6 chữ số thập phân (DEC-D19-04)"


# ── ranh giới: số THẬT hôm nay vẫn là 0, nói ra thay vì để phát hiện sau ────────────────────────


@pytest.mark.parametrize("cost_that", [0.0])
async def test_trace_THAT_hom_nay_cho_ra_chua_noi_gia_chu_khong_phai_do_that_bang_0(
    admin_pool: Pool, pool: Pool, cost_that: float
) -> None:
    """Trace **như emit thật hôm nay** (`cost=_NO_COST`, `tokens` thật) ⇒ `priced is False`.

    Ba lớp ở trên chạy trên trace **gieo**. Bài này chạy trên trace mang đúng hình dạng emit hôm nay
    và khẳng định bề mặt phân loại nó là *chưa nối giá*, **không** phải *đã đo, bằng 0* — tức ô DoD
    "cùng-1-số" đóng ở **đường đọc**, còn **số thật** thì chưa (`DEC-D19-06`).

    Đây là vế thứ hai của `DEC-D19-06` dựng thành test thay vì để nó chỉ sống trong báo cáo.
    """
    del admin_pool
    run_id = f"{_RUN_ID}-emit-that"
    writer = PgTraceWriter(pool)
    for seq, tokens in enumerate([Tokens(prompt=37, completion=12), Tokens(prompt=211, completion=63)], 1):
        await writer.write(
            TraceEvent(
                event_id=f"{run_id}-e{seq}",
                run_id=run_id,
                agent_id="agent-d19",
                tenant_id=_TENANT,
                node_id=f"n{seq}",
                node_type=NodeType.LLM_STEP,
                ts=f"2026-08-13T10:00:0{seq}+00:00",
                inputs_hash="stub",
                outputs={},
                tokens=tokens,
                cost=cost_that,
            )
        )

    ket_qua = run_cost_from_trace(await read_run_unscoped(pool, run_id))
    dong = _dong_cost(
        render_run_cases(
            _results(),
            run_id=run_id,
            golden_set_ref="golden-30@d19",
            trace_source=TRACE_SOURCE_POSTGRES,
            run_cost=ket_qua,
        )
    )

    assert ket_qua.cost == 0.0
    assert ket_qua.priced is False, "Σtokens > 0 mà Σcost == 0 ⇒ chưa nối giá, không phải đo bằng 0"
    assert "chưa-nối-giá" in dong
    assert "Σtokens=323" in dong
    assert "0.000000" not in dong, "emit chưa áp giá mà in như một phép đo"
