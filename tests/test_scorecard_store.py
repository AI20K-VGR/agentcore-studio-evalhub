"""`scorecard_store` — Scorecard **tạm** của lượt Chấm điểm, để lượt Publish khỏi chấm lại.

Trước đây `/publish` gọi lại `_evaluate()` từ đầu: bấm Chấm điểm chạy hết bộ golden, bấm Publish
chạy **lần nữa**. Với bộ 100 case × tới 20 lượt LLM/case thì đó là trả hai lần cho cùng một recipe.

Lý do route không tin Scorecard của UI vẫn đúng và không đổi: client tự khai `verdict: "PASS"` là
xong. Nên **client không cầm gì cả** — server tự ghi lúc chấm, tự tra lúc publish, khoá bằng
`recipe_hash`. Sửa một ký tự trên canvas là hash đổi, tra không ra, phải chấm lại.

Phân biệt hai loại dòng bằng `recipe_version`:

    recipe_version IS NOT NULL  →  chứng nhận một version ĐÃ publish — bất khả xâm phạm
    recipe_version IS NULL      →  điểm tạm, chờ bấm Publish — tra được, huỷ được
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from studio_contracts import Aggregate, CaseResult, Gate, GateThreshold, Scorecard
from studio_evalhub.scorecard_store import (
    drop_pending_scorecards,
    read_pending_scorecard,
    write_pending_scorecard,
)
from studio_kb.doc_factory_core import TENANT_IDS

ANKOR_ID = TENANT_IDS["ankor"]
BOREA_ID = TENANT_IDS["borea"]


def _card(*, agent_id: str = "agent-a", recipe_hash: str = "h1", verdict: str = "PASS") -> Scorecard:
    return Scorecard(
        agent_id=agent_id,
        golden_set_ref="bo-thu",
        results=[CaseResult(case_id="c1", expected="x", actual="x", success=True, citation_accuracy=1.0)],
        aggregate=Aggregate(success_rate=1.0, citation_accuracy=1.0, n_scored_citation=1),
        gate=Gate(threshold=GateThreshold(success=0.9, citation_accuracy=0.95), verdict=verdict),
        recipe_hash=recipe_hash,
    )


async def _bind(conn: Any, tenant_id: UUID) -> None:
    await conn.execute("SELECT set_config('app.tenant_id', %s, true)", (str(tenant_id),))


async def test_ghi_roi_tra_lai_ra_dung_scorecard(pool: Any) -> None:
    """Vòng tròn cơ bản — và `results`/`aggregate`/`gate` phải sống sót qua JSONB nguyên vẹn,
    không chỉ `verdict`."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await write_pending_scorecard(conn, _card(), ANKOR_ID)
        doc = await read_pending_scorecard(conn, "agent-a", "h1")
    assert doc is not None
    assert doc.gate.verdict == "PASS"
    assert [r.case_id for r in doc.results] == ["c1"]
    assert doc.aggregate.citation_accuracy == 1.0
    assert doc.recipe_hash == "h1"


async def test_hash_khac_thi_khong_tra_ra(pool: Any) -> None:
    """Khoá của cả cơ chế: sửa recipe ⇒ `recipe_hash` đổi ⇒ điểm cũ KHÔNG dùng lại được.

    Thiếu vế này thì tái dùng điểm thành một đường publish recipe chưa từng được chấm."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await write_pending_scorecard(conn, _card(recipe_hash="h1"), ANKOR_ID)
        assert await read_pending_scorecard(conn, "agent-a", "h2") is None


async def test_agent_khac_thi_khong_tra_ra(pool: Any) -> None:
    """Cùng hash nhưng khác agent cũng không dùng lại — `publish()` đã canh `scorecard.agent_id`,
    đây là tầng chặn sớm hơn."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await write_pending_scorecard(conn, _card(agent_id="agent-a"), ANKOR_ID)
        assert await read_pending_scorecard(conn, "agent-b", "h1") is None


async def test_tenant_khac_khong_doc_duoc(pool: Any) -> None:
    """RLS `FORCE` là hàng rào, không phải một mệnh đề `WHERE` hàm này tự nhớ viết."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await write_pending_scorecard(conn, _card(), ANKOR_ID)
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, BOREA_ID)
        assert await read_pending_scorecard(conn, "agent-a", "h1") is None


async def test_ban_moi_nhat_thang(pool: Any) -> None:
    """Chấm lại cùng recipe hai lần ⇒ tra ra bản SAU. Bản trước có thể mang verdict cũ; trả về nó
    là publish theo một lượt chấm đã bị chính người dùng thay thế."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await write_pending_scorecard(conn, _card(verdict="FAIL"), ANKOR_ID)
        await write_pending_scorecard(conn, _card(verdict="PASS"), ANKOR_ID)
        doc = await read_pending_scorecard(conn, "agent-a", "h1")
    assert doc is not None
    assert doc.gate.verdict == "PASS"


async def test_huy_chi_xoa_dong_tam_khong_dung_chung_nhan_da_publish(pool: Any) -> None:
    """`drop_pending_scorecards` xoá điểm tạm khi tenant nạp tài liệu mới — KB đổi thì điểm cũ
    không còn nói về KB hiện tại, mà `recipe_hash` không bắt được (recipe không đổi, chỉ nội dung
    kho đổi).

    Vế bất đối xứng, và là vế quan trọng hơn: dòng `recipe_version IS NOT NULL` là **chứng nhận
    của một version đã publish** — xoá nó là mất lịch sử chứng nhận."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        await write_pending_scorecard(conn, _card(), ANKOR_ID)
        await conn.execute(
            "INSERT INTO eval.scorecards (tenant_id, agent_id, golden_set_ref, results, aggregate, gate, "
            "recipe_hash, recipe_version) VALUES (%s, 'agent-a', 'bo-thu', '[]'::jsonb, '{}'::jsonb, "
            "'{}'::jsonb, 'h1', 7)",
            (str(ANKOR_ID),),
        )

        await drop_pending_scorecards(conn)

        assert await read_pending_scorecard(conn, "agent-a", "h1") is None
        cur = await conn.execute("SELECT count(*) FROM eval.scorecards WHERE recipe_version IS NOT NULL")
        row = await cur.fetchone()
    assert row is not None
    assert row[0] == 1, "chứng nhận của version đã publish phải còn nguyên"
