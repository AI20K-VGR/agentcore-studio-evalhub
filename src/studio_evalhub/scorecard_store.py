"""Đọc/ghi Scorecard **tạm** ở `eval.scorecards` — để lượt Publish khỏi chấm lại từ đầu.

## Vì sao

`/publish` gọi lại `_evaluate()` nguyên vẹn, nên bấm Chấm điểm chạy hết bộ golden rồi bấm Publish
chạy **lần nữa**. Với bộ 100 case × tới 20 lượt LLM mỗi case, đó là trả hai lần cho cùng một recipe.

Lý do route **không tin** Scorecard của UI vẫn đúng và không đổi: client tự khai `verdict: "PASS"`
là xong. Nên client **không cầm gì cả** — server tự ghi lúc chấm, tự tra lúc publish, và khoá bằng
`recipe_hash`. Sửa một ký tự trên canvas là hash đổi, tra không ra, phải chấm lại. Verdict không đi
qua tay client ở bất kỳ nấc nào.

## Hai loại dòng, phân biệt bằng `recipe_version`

    recipe_version IS NOT NULL  →  chứng nhận một version ĐÃ publish (`studio_workbench.publish`)
    recipe_version IS NULL      →  điểm tạm của một lượt Chấm điểm, chờ bấm Publish

Cột đó có sẵn từ trước (`schema.py`), nên không cần bảng mới hay cột mới — chỉ cần đọc nó như một
dấu phân loại. Mọi hàm dưới đây chỉ chạm nhánh `IS NULL`; nhánh còn lại là lịch sử chứng nhận và
không hàm nào ở đây được phép xoá.

## Tenant

RLS `FORCE` trên `eval.scorecards` là hàng rào (`schema.py`), nên `read`/`drop` **không** tự thêm
`WHERE tenant_id` — đúng nguyên tắc "RLS là hàng rào, không phải lớp phụ" đã dùng ở `golden_store`.
`write` vẫn nhận `tenant_id` vì đó là **giá trị của cột**, không phải bộ lọc: policy `WITH CHECK`
từ chối nếu nó lệch phiên.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from studio_contracts import Aggregate, CaseResult, Gate, Scorecard


async def write_pending_scorecard(conn: Any, scorecard: Scorecard, tenant_id: UUID) -> None:
    """Ghi điểm của một lượt Chấm điểm. `recipe_version` để `NULL` — đây chưa phải chứng nhận.

    **Một câu `INSERT ... ON CONFLICT DO UPDATE`, không phải delete-rồi-insert** (review AIE-1,
    PR #57). Bất biến *"tối đa một dòng chờ cho mỗi `(tenant_id, agent_id, recipe_hash)`"* được
    cưỡng chế bởi index một phần `eval_scorecards_one_pending_per_recipe` (`schema.py`), không phải
    bởi thứ tự hai câu SQL trong hàm này.

    Bản đầu dùng hai câu rời, và nó **vỡ thật** dưới ghi đồng thời: hai lượt Chấm điểm cùng agent +
    cùng `recipe_hash` (double click, hai tab) đều thấy `DELETE` khớp 0 dòng dưới READ COMMITTED
    rồi đều `INSERT` ⇒ 2 dòng cùng khoá. Tái hiện được bằng 2 transaction đồng bộ qua barrier —
    `count = 2` trước bản vá, `1` sau. Cùng khuôn `golden_store.write_golden_set` đã dùng cho đúng
    lớp bài toán này (`evalhub#46`).

    `created_at = now()` khi ghi đè: dòng chờ mang nghĩa *"điểm của lượt chấm gần nhất"*, nên mốc
    thời gian phải theo lượt mới chứ không giữ lại mốc của lượt đã bị thay thế.
    """
    await conn.execute(
        """
        INSERT INTO eval.scorecards
            (tenant_id, agent_id, golden_set_ref, results, aggregate, gate, recipe_hash, recipe_version)
        VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, NULL)
        ON CONFLICT (tenant_id, agent_id, recipe_hash) WHERE recipe_version IS NULL
        DO UPDATE SET
            golden_set_ref = EXCLUDED.golden_set_ref,
            results = EXCLUDED.results,
            aggregate = EXCLUDED.aggregate,
            gate = EXCLUDED.gate,
            created_at = now()
        """,
        (
            str(tenant_id),
            scorecard.agent_id,
            scorecard.golden_set_ref,
            json.dumps([result.model_dump(mode="json") for result in scorecard.results]),
            json.dumps(scorecard.aggregate.model_dump(mode="json")),
            json.dumps(scorecard.gate.model_dump(mode="json")),
            scorecard.recipe_hash,
        ),
    )


async def read_pending_scorecard(conn: Any, agent_id: str, recipe_hash: str) -> Scorecard | None:
    """Điểm tạm mới nhất của đúng `(agent_id, recipe_hash)` trong tenant của phiên, hoặc `None`.

    Nhiều nhất một dòng khớp — `write_pending_scorecard` xoá bản cũ trước khi ghi (xem docstring
    hàm đó cho lý do "mới nhất thắng" phải là cấu trúc chứ không phải `ORDER BY`). `LIMIT 1` giữ
    lại như chốt phòng thủ cho dữ liệu ghi bởi bản cũ hơn của module này.
    """
    cur = await conn.execute(
        """
        SELECT agent_id, golden_set_ref, results, aggregate, gate, recipe_hash
        FROM eval.scorecards
        WHERE agent_id = %s AND recipe_hash = %s AND recipe_version IS NULL
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (agent_id, recipe_hash),
    )
    row = await cur.fetchone()
    if row is None:
        return None
    return Scorecard(
        agent_id=str(row[0]),
        golden_set_ref=str(row[1]),
        results=[CaseResult.model_validate(item) for item in row[2]],
        aggregate=Aggregate.model_validate(row[3]),
        gate=Gate.model_validate(row[4]),
        recipe_hash=None if row[5] is None else str(row[5]),
    )


async def drop_pending_scorecards(conn: Any) -> None:
    """Huỷ MỌI điểm tạm của tenant hiện tại — gọi khi kho tài liệu đổi.

    `recipe_hash` khoá được *"recipe có bị sửa không"* nhưng **không** khoá được *"KB có đổi
    không"*: nạp thêm một tài liệu là recipe giữ nguyên hash trong khi điểm cũ đã thôi nói về kho
    hiện tại. Đó là lý do cần một đường huỷ tường minh thay vì một hạn thời gian đoán chừng.

    Chỉ chạm `recipe_version IS NULL`. Dòng đã publish là chứng nhận của một version thật và không
    bao giờ bị xoá ở đây.
    """
    await conn.execute("DELETE FROM eval.scorecards WHERE recipe_version IS NULL")
