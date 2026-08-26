"""`eval_job_store` — job của một lượt Chấm điểm chạy nền.

Job mang **chỉ tiến độ và trạng thái**; Scorecard đi vào `eval.scorecards` (`scorecard_store`).
Hai bất biến quan trọng nhất, mỗi cái một bài: mọi lệnh cập nhật chỉ chạm job còn `running`, và
`sweep` đo *"lâu không cập nhật"* chứ không phải *"tạo đã lâu"*.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from studio_evalhub.eval_job_store import (
    create_eval_job,
    fail_eval_job,
    finish_eval_job,
    read_eval_job,
    record_job_progress,
    sweep_stale_jobs,
)
from studio_kb.doc_factory_core import TENANT_IDS

ANKOR_ID = TENANT_IDS["ankor"]
BOREA_ID = TENANT_IDS["borea"]


async def _bind(conn: Any, tenant_id: UUID) -> None:
    await conn.execute("SELECT set_config('app.tenant_id', %s, true)", (str(tenant_id),))


async def test_tao_roi_doc_lai_ra_dung_job(pool: Any) -> None:
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        job_id = await create_eval_job(conn, ANKOR_ID, "agent-a", "h1")
        job = await read_eval_job(conn, job_id)
    assert job is not None
    assert (job.agent_id, job.recipe_hash, job.status) == ("agent-a", "h1", "running")
    assert (job.done, job.total, job.detail) == (0, 0, None)


async def test_tien_do_roi_xong(pool: Any) -> None:
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        job_id = await create_eval_job(conn, ANKOR_ID, "agent-a", "h1")
        await record_job_progress(conn, job_id, 12, 30)
        giua_chung = await read_eval_job(conn, job_id)
        await finish_eval_job(conn, job_id)
        xong = await read_eval_job(conn, job_id)
    assert giua_chung is not None and (giua_chung.done, giua_chung.total) == (12, 30)
    assert xong is not None and xong.status == "done"


async def test_hong_thi_giu_lai_thong_diep(pool: Any) -> None:
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        job_id = await create_eval_job(conn, ANKOR_ID, "agent-a", "h1")
        await fail_eval_job(conn, job_id, "bộ golden chưa nạp")
        job = await read_eval_job(conn, job_id)
    assert job is not None
    assert job.status == "failed"
    assert job.detail == "bộ golden chưa nạp"


async def test_khong_keo_nguoc_job_da_ket_thuc(pool: Any) -> None:
    """Mọi lệnh cập nhật chỉ chạm job còn `running`.

    Một task cũ còn sót lại (người dùng bấm Chấm điểm lần hai) ghi tiến độ đè lên job đã xong sẽ
    kéo nó về trạng thái dở — người dùng thấy thanh tiến độ chạy lùi và kết quả biến mất."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        job_id = await create_eval_job(conn, ANKOR_ID, "agent-a", "h1")
        await finish_eval_job(conn, job_id)

        await record_job_progress(conn, job_id, 3, 30)
        await fail_eval_job(conn, job_id, "muộn màng")

        job = await read_eval_job(conn, job_id)
    assert job is not None
    assert job.status == "done", "job đã xong bị task cũ kéo ngược"
    assert (job.done, job.detail) == (0, None)


async def test_tenant_khac_khong_doc_duoc(pool: Any) -> None:
    """RLS `FORCE` là hàng rào — không hàm nào ở đây tự viết `WHERE tenant_id`."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        job_id = await create_eval_job(conn, ANKOR_ID, "agent-a", "h1")
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, BOREA_ID)
        assert await read_eval_job(conn, job_id) is None


async def test_doc_job_khong_ton_tai_ra_none(pool: Any) -> None:
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        assert await read_eval_job(conn, uuid4()) is None


async def test_sweep_don_job_im_lang_va_tha_job_dang_bao_tien_do(pool: Any) -> None:
    """Bài quan trọng nhất của module: mốc là *"lâu không cập nhật"*, KHÔNG phải *"tạo đã lâu"*.

    Hai job cùng tạo lâu như nhau; một cái vẫn báo tiến độ. Đo *"tạo đã lâu"* giết cả hai — tức
    giết nhầm một lượt chấm 100 case đang chạy đúng."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        chet = await create_eval_job(conn, ANKOR_ID, "agent-chet", "h-chet")
        song = await create_eval_job(conn, ANKOR_ID, "agent-song", "h-song")
        await conn.execute("UPDATE eval.eval_jobs SET created_at = now() - interval '1 hour'")
        await conn.execute(
            "UPDATE eval.eval_jobs SET updated_at = now() - interval '1 hour' WHERE id = %s", (str(chet),)
        )
        await record_job_progress(conn, song, 7, 100)

        don_duoc = await sweep_stale_jobs(conn, stale_after_seconds=120)

        job_chet = await read_eval_job(conn, chet)
        job_song = await read_eval_job(conn, song)
    assert don_duoc == 1
    assert job_chet is not None and job_chet.status == "failed"
    assert job_chet.detail is not None and "gián đoạn" in job_chet.detail
    assert job_song is not None and job_song.status == "running", "job đang báo tiến độ bị giết nhầm"


async def test_sweep_khong_dung_toi_job_da_ket_thuc(pool: Any) -> None:
    """Vế bất đối xứng của bài trên, và là lỗ mutation tìm ra: `sweep` chỉ chạm `running`.

    Job `done`/`failed` cũng có `updated_at` cũ dần theo thời gian — không lọc theo `status` thì
    một lượt quét lúc khởi động sẽ lật MỌI kết quả cũ thành "bị gián đoạn", tức xoá sạch điểm của
    những lượt chấm đã xong. Mutant bỏ mệnh đề đó sống sót qua 7 bài trước khi có bài này."""
    async with pool.connection() as conn, conn.transaction():
        await _bind(conn, ANKOR_ID)
        xong = await create_eval_job(conn, ANKOR_ID, "agent-xong", "h-xong")
        hong = await create_eval_job(conn, ANKOR_ID, "agent-hong", "h-hong")
        await finish_eval_job(conn, xong)
        await fail_eval_job(conn, hong, "lý do cũ")
        await conn.execute("UPDATE eval.eval_jobs SET updated_at = now() - interval '1 hour'")

        don_duoc = await sweep_stale_jobs(conn, stale_after_seconds=120)

        job_xong = await read_eval_job(conn, xong)
        job_hong = await read_eval_job(conn, hong)
    assert don_duoc == 0, "sweep chạm vào job đã kết thúc"
    assert job_xong is not None and job_xong.status == "done"
    assert job_hong is not None and job_hong.detail == "lý do cũ", "thông điệp lỗi cũ bị ghi đè"
