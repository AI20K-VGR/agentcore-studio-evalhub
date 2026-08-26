"""Móc `on_progress` của `EvalHarness.run` — nguồn duy nhất để báo "đã chạy 12/30 case".

Cổng Publish chạy nền (kit — chấm điểm bất đồng bộ) cần biết còn bao lâu, mà `run()` chạy trọn bộ
trong một lời gọi nên bên ngoài không nhìn thấy gì cho tới lúc xong. Móc này là chỗ duy nhất biết
đã qua bao nhiêu case.

Additive, keyword-only, mặc định `None` ⇒ mọi call-site đang có không đổi một dòng.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.harness import EvalHarness

ANKOR = UUID("a0000000-0000-0000-0000-000000000001")


def _case(case_id: str) -> GoldenCase:
    return GoldenCase(
        case_id=case_id,
        query="q?",
        tenant="ankor",
        section_roles=["hr"],
        expected_tenant="ankor",
        expected_section_role="hr",
        expected="đáp",
        expected_citation=[],
    )


async def _run(harness_kwargs: dict[str, Any], n_cases: int, runner_tot: Any) -> None:
    golden = GoldenSet(golden_set_ref="bo-tien-do", cases=[_case(f"c{i}") for i in range(1, n_cases + 1)])
    await EvalHarness().run(
        "agent-a",
        golden.golden_set_ref,
        golden_set=golden,
        runner=runner_tot(golden, {"ankor": ANKOR}),
        tenant_ids={"ankor": ANKOR},
        threshold_success=0.0,
        threshold_citation_accuracy=0.0,
        **harness_kwargs,
    )


async def test_bao_tien_do_sau_moi_case(runner_tot: Any) -> None:
    """Gọi đúng một lần mỗi case, đếm tăng dần, và mẫu số là tổng case THẬT SỰ chạy."""
    seen: list[tuple[int, int]] = []

    async def _on_progress(done: int, total: int) -> None:
        seen.append((done, total))

    await _run({"on_progress": _on_progress}, 4, runner_tot)
    assert seen == [(1, 4), (2, 4), (3, 4), (4, 4)]


async def test_khong_truyen_moc_thi_khong_doi_gi(runner_tot: Any) -> None:
    """Vế bất đối xứng: không truyền `on_progress` vẫn chạy trọn — móc là additive, không phải
    tham số bắt buộc trá hình."""
    await _run({}, 2, runner_tot)


async def test_mau_so_theo_bo_CORE_chu_khong_theo_ca_bo(runner_tot: Any) -> None:
    """Khi `core_only=True`, mẫu số phải là số case Core — báo "3/40" trong khi chỉ chạy 3 case là
    một thanh tiến độ nói dối, và người vận hành đọc nó để quyết đợi hay huỷ."""
    seen: list[tuple[int, int]] = []

    async def _on_progress(done: int, total: int) -> None:
        seen.append((done, total))

    await _run(
        {"on_progress": _on_progress, "core_only": True, "core_max_cases": 2, "core_min_answer": 1}, 5, runner_tot
    )
    assert [total for _, total in seen] == [2, 2], seen
    assert [done for done, _ in seen] == [1, 2]


async def test_loi_trong_moc_khong_lam_hong_luot_cham(runner_tot: Any) -> None:
    """Móc là báo cáo, không phải cổng. Ghi tiến độ hỏng (mất kết nối DB, job bị xoá) không được
    kéo theo cả lượt chấm — người dùng mất điểm vì thanh tiến độ là đổi một phiền toái lấy một
    hỏng hóc."""

    async def _on_progress(done: int, total: int) -> None:
        raise RuntimeError("ghi tiến độ hỏng")

    await _run({"on_progress": _on_progress}, 2, runner_tot)
