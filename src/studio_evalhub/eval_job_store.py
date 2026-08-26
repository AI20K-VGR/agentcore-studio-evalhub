"""Job của một lượt Chấm điểm chạy nền — `eval.eval_jobs`.

## Vì sao chạy nền

Cổng Publish chạy ĐỒNG BỘ trong một request HTTP. Docstring `core_set.py` đã đo: *"Bộ Core 30–50
case chạy ~20–30s; chạy đủ 100–500 case mất 5–10 phút ⇒ spinner treo hoặc HTTP 504"*. Và mỗi lượt
giữ **2 trong 8** kết nối của pool (`tenant_context_middleware` giữ 1 suốt request,
`_evaluate` lấy thêm 1 qua `get_pool()`), nên bốn người bấm cùng lúc là cả app đứng chờ.

## Job mang gì

**Chỉ tiến độ và trạng thái.** Scorecard đi vào `eval.scorecards` với `recipe_version IS NULL`
(`scorecard_store`) — đúng chỗ `/publish` vốn đã tra. Lưu thêm một bản ở đây là hai nguồn sự thật
cho cùng một verdict, và chúng lệch nhau vào ngày ai đó sửa một bên.

Nên `read_eval_job` trả về trạng thái; caller ghép nó với `read_pending_scorecard(agent_id,
recipe_hash)` khi `status == "done"`. Hai khoá đó nằm sẵn trên job.

## Không có trạng thái `queued`

Job được tạo ở `running` ngay: không có hàng đợi thật, task chạy liền sau khi tạo. Thêm `queued`
khi chưa có worker nào đọc nó là bịa ra một trạng thái không bao giờ quan sát được — và một trạng
thái không quan sát được là chỗ người đọc sau này suy sai về kiến trúc.

## Tiến trình chết giữa chừng

Job `running` mà tiến trình chết thì không ai chuyển nó sang `failed` — nó treo mãi và người dùng
đợi một thứ đã chết. `sweep_stale_jobs` là đường dọn: gọi lúc khởi động app. Mốc *"lâu không cập
nhật"* chứ không phải *"tạo đã lâu"* — một job 100 case chạy 8 phút vẫn khoẻ nếu nó còn báo tiến độ.

## Tenant

RLS `FORCE` là hàng rào (`schema.py`), nên mọi hàm ở đây **không** tự thêm `WHERE tenant_id` —
cùng nguyên tắc `golden_store`/`scorecard_store`. `create` nhận `tenant_id` vì đó là giá trị của
cột, không phải bộ lọc.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

JobStatus = Literal["running", "done", "failed"]


@dataclass(frozen=True)
class EvalJob:
    """Một dòng `eval.eval_jobs`. `agent_id` + `recipe_hash` là khoá để lấy Scorecard tương ứng."""

    job_id: UUID
    agent_id: str
    recipe_hash: str
    status: JobStatus
    done: int
    total: int
    detail: str | None


async def create_eval_job(conn: Any, tenant_id: UUID, agent_id: str, recipe_hash: str) -> UUID:
    """Tạo job ở trạng thái `running` (xem docstring module: không có `queued`)."""
    cur = await conn.execute(
        """
        INSERT INTO eval.eval_jobs (tenant_id, agent_id, recipe_hash, status)
        VALUES (%s, %s, %s, 'running')
        RETURNING id
        """,
        (str(tenant_id), agent_id, recipe_hash),
    )
    row = await cur.fetchone()
    assert row is not None  # INSERT ... RETURNING luôn trả đúng 1 dòng khi không lỗi
    return UUID(str(row[0]))


async def record_job_progress(conn: Any, job_id: UUID, done: int, total: int) -> None:
    """Cập nhật tiến độ. `updated_at` cũng là nhịp tim mà `sweep_stale_jobs` đọc.

    Chỉ chạm job còn `running`: một job đã `done`/`failed` mà bị kéo ngược về tiến độ dở là trạng
    thái không thể xảy ra thật, và nó chỉ xảy ra khi một task cũ còn sót lại ghi đè job mới."""
    await conn.execute(
        "UPDATE eval.eval_jobs SET done = %s, total = %s, updated_at = now() WHERE id = %s AND status = 'running'",
        (done, total, str(job_id)),
    )


async def finish_eval_job(conn: Any, job_id: UUID) -> None:
    """Đánh dấu xong. Scorecard đã nằm ở `eval.scorecards` — job không giữ bản sao nào."""
    await conn.execute(
        "UPDATE eval.eval_jobs SET status = 'done', updated_at = now() WHERE id = %s AND status = 'running'",
        (str(job_id),),
    )


async def fail_eval_job(conn: Any, job_id: UUID, detail: str) -> None:
    """Đánh dấu hỏng kèm thông điệp cho người dùng đọc.

    `detail` cắt còn 500 ký tự: một traceback đầy đủ đi thẳng ra giao diện vừa vô dụng với người
    đọc vừa là đường rò chi tiết nội bộ."""
    await conn.execute(
        "UPDATE eval.eval_jobs SET status = 'failed', detail = %s, updated_at = now() "
        "WHERE id = %s AND status = 'running'",
        (detail[:500], str(job_id)),
    )


async def read_eval_job(conn: Any, job_id: UUID) -> EvalJob | None:
    """Job trong tenant của phiên, hoặc `None`. RLS lo phần tenant."""
    cur = await conn.execute(
        "SELECT id, agent_id, recipe_hash, status, done, total, detail FROM eval.eval_jobs WHERE id = %s",
        (str(job_id),),
    )
    row = await cur.fetchone()
    if row is None:
        return None
    raw_status = str(row[3])
    # `CHECK` ở schema đã cưỡng chế tập 3 giá trị, nên tới đây là DB bị sửa ngoài đường ứng dụng.
    # Ném thay vì ép kiểu im lặng: một trạng thái không ai biết đọc sẽ thành job treo vĩnh viễn.
    if raw_status == "running":
        narrowed: JobStatus = "running"
    elif raw_status == "done":
        narrowed = "done"
    elif raw_status == "failed":
        narrowed = "failed"
    else:
        raise ValueError(f"eval_jobs.status không hợp lệ: {raw_status!r} (job {row[0]})")
    return EvalJob(
        job_id=UUID(str(row[0])),
        agent_id=str(row[1]),
        recipe_hash=str(row[2]),
        status=narrowed,
        done=int(row[4]),
        total=int(row[5]),
        detail=None if row[6] is None else str(row[6]),
    )


async def sweep_stale_jobs(conn: Any, *, stale_after_seconds: int) -> int:
    """Chuyển mọi job `running` **lâu không cập nhật** sang `failed`. Trả về số dòng đã dọn.

    Gọi lúc khởi động app: tiến trình chết giữa lượt chấm để lại job treo mãi, và người dùng đợi
    một thứ đã không còn chạy.

    Mốc theo `updated_at` chứ không phải `created_at` — một job 100 case chạy 8 phút vẫn khoẻ nếu
    nó còn báo tiến độ, còn một job im 2 phút thì đã chết. Đo *"lâu không cập nhật"* mới phân biệt
    được hai ca đó; đo *"tạo đã lâu"* thì giết nhầm job đang chạy đúng.
    """
    cur = await conn.execute(
        "UPDATE eval.eval_jobs SET status = 'failed', "
        "detail = 'lượt chấm bị gián đoạn (tiến trình dừng giữa chừng) — chấm lại', updated_at = now() "
        "WHERE status = 'running' AND updated_at < now() - make_interval(secs => %s)",
        (stale_after_seconds,),
    )
    return int(cur.rowcount)
