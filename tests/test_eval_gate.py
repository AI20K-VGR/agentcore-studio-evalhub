"""Phase 8 — eval-gate ĐỎ-by-design tests (spec AIE-2, R-SPEC A7 INV-6/INV-7).

`harness.py`/`judge.py`/`compute.py` are intentionally empty (`NotImplementedError`) at P8 —
the OJT spec surface AIE-2 fills next. These tests pin the SHAPE of that gap rather than pretend
it is closed: the eval-gate money-shot ("sửa instructions tệ → verdict FAIL → chặn + rollback",
R-SPEC A7 INV-6) cannot run for real yet because nothing produces a real verdict.

## Sửa D9 — `strict=False` là một lỗi, không phải một lựa chọn

Bản trước đánh dấu **cả hai** bài `xfail(strict=False)` với lập luận: *"unexpected pass (once AIE-2
implements the seam) is reported as XPASS, not a failure — main tracks these to flip green"*. Lập luận
đó tạo ra hai vấn đề khác nhau, và cả hai đều làm suite nói dối:

**Bài `test_harness_judge_compute_not_implemented` không đỏ được ở CHIỀU NÀO.** Nó đang PASS (báo
`XPASS`) vì ba seam vẫn raise `NotImplementedError` đúng như nó khẳng định. Nhưng nếu ai đó stub một
giá trị giả — đúng thứ docstring của nó nói là sẽ bắt được — thì assert vỡ, `xfail` hấp thụ, pytest báo
`XFAIL`, và suite **vẫn xanh**. Một canh gác mà cả hai kết cục đều xanh thì không canh gì. D9 gỡ hẳn
marker: bài đang xanh thật, nên để nó xanh thật, và stub giả sẽ làm nó ĐỎ.

**Bài `test_gate_blocks_on_fail` đỏ thật, nhưng `strict=False` khiến ngày nó được vá không ai biết.**
`EvalHarness.run` còn `NotImplementedError` nên bài này `XFAIL` hợp lệ — nó đang ghi một gap thật. Vấn
đề là lúc seam xong, nó lặng lẽ thành `XPASS` và không ai buộc phải quay lại xem assert bên trong có
còn đúng hợp đồng hay không. D9 đổi sang `strict=True`: `XPASS` trở thành FAIL, buộc gỡ marker và đọc
lại assert. Gap vẫn nhìn thấy được trong suite, nhưng lối ra khỏi nó không còn im lặng.

Nguyên tắc rút ra, áp cho cả hai: **`xfail` không strict chỉ hợp lý khi không quan tâm kết cục nào.**
Ở đây kết cục nào cũng quan trọng — nên hoặc không marker (bài đang đúng), hoặc `strict=True` (bài đang
ghi gap).

Boundary (R-SPEC A4): these tests exercise ONLY the eval-harness/judge/scorecard seam AIE-2 owns —
they do NOT stand up a real golden-set (DE's job), a real DAG interpreter (AIE-1's job), or
publish/rollback wiring (SWE's job); those are consumed, not asserted, here.
"""

from __future__ import annotations

import pytest
from studio_contracts import CaseResult, Judge
from studio_evalhub.compute import compute_scorecard
from studio_evalhub.harness import EvalHarness
from studio_evalhub.judge import LLMJudge


@pytest.mark.xfail(strict=True, reason="spec AIE-2 fills harness/judge/compute — EvalHarness.run chưa có verdict")
async def test_gate_blocks_on_fail() -> None:
    """Money-shot (R-SPEC A7 INV-6, umbrella-contract step 7): an agent recipe with bad
    instructions runs the 30-case golden set through `EvalHarness.run`, `compute_scorecard`
    decides `gate.verdict == "FAIL"`, and SWE's publish/rollback wiring (not exercised here —
    ownership fence) blocks + rolls back on that verdict. Currently unreachable — `EvalHarness.run`
    raises `NotImplementedError`, so there is no real verdict to gate on yet. This is the ĐỎ this
    test records until AIE-2 implements the seam, at which point the assertion below is the real
    contract to satisfy."""
    harness = EvalHarness()
    scorecard = await harness.run(agent_id="agent-bad-instructions", golden_set_ref="golden-set-eval-1")

    assert scorecard.gate.verdict == "FAIL"


async def test_harness_judge_compute_not_implemented() -> None:
    """KHÓA: spec AIE-2 seams (`EvalHarness.run`, `LLMJudge.judge`, `compute_scorecard`) all have
    an intentionally empty body — each MUST raise `NotImplementedError`, not silently return a
    fabricated result, until AIE-2 fills them in. A red-teamer or reviewer "making this green" by
    stubbing a fake return value (instead of implementing the real seam) would be caught by this
    assertion flipping from raise-NotImplementedError to no-raise.

    **KHÔNG marker (sửa D9).** Bài này đang xanh thật — ba seam đúng là còn raise. Bản trước đeo
    `xfail(strict=False)` nên chính cái kết cục nó tồn tại để bắt (stub giả ⇒ assert vỡ) lại bị marker
    hấp thụ thành `XFAIL` = xanh. Không marker thì stub giả làm bài này ĐỎ, đúng như docstring hứa.

    Vì sao đây không phải "test đang chờ tính năng": nó khẳng định một điều **đúng ngay hôm nay** —
    rằng seam chưa điền thì phải kêu, chứ không phải chờ seam được điền. Bài chờ tính năng là
    `test_gate_blocks_on_fail` ở trên, và bài đó mới cần `xfail`."""
    harness = EvalHarness()
    judge = LLMJudge()

    with pytest.raises(NotImplementedError):
        await harness.run(agent_id="agent-1", golden_set_ref="golden-set-eval-1")

    with pytest.raises(NotImplementedError):
        await judge.judge(case_id="case-1", expected="A", actual="A")

    with pytest.raises(NotImplementedError):
        compute_scorecard(
            agent_id="agent-1",
            golden_set_ref="golden-set-eval-1",
            results=[
                CaseResult(
                    case_id="case-1",
                    expected="A",
                    actual="A",
                    success=True,
                    citation_accuracy=1.0,
                    judge=Judge(label="pass", agreement=0.95),
                )
            ],
            threshold_success=0.9,
            threshold_citation_accuracy=0.9,
            # D16: tham số mới (DEC-D16-03 đường (b)). `case-1` là case nhánh trả-lời nên nó nằm
            # trong tập được chấm citation. Bài này không đổi mục đích — vẫn khẳng định seam raise.
            scored_case_ids={"case-1"},
        )
