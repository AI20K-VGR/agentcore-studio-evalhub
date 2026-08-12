"""Eval-gate money-shot — `gate.verdict` chặn thật (R-SPEC A7 INV-6, umbrella-contract bước 7).

## D16 — bài này đổi từ *ghi một gap* sang *chứng minh một hợp đồng*

Từ D9 tới D15 file này giữ hai bài **đỏ-by-design**: seam AIE-2 còn `NotImplementedError` nên
money-shot không chạy được, và `xfail(strict=True)` là cách ghi lại gap đó **mà không cho phép lối ra
im lặng** — ngày seam xong, marker biến bài thành `XPASS` ⇒ pytest báo FAIL ⇒ buộc quay lại đọc assert.

**D16 là ngày cơ chế đó bắn.** `EvalHarness.run` và `compute_scorecard` đã land (T2/T4), pytest in
`[XPASS(strict)]`, và việc phải làm **không phải xoá một dòng marker** — `DEC-D16-04` ghi rõ:

- `agent_id="agent-bad-instructions"` và `golden_set_ref="golden-set-eval-1"` **chưa bao giờ tồn
  tại**. Gỡ marker mà giữ nguyên thân bài sẽ ra `LookupError`/`FileNotFoundError`, **không** ra
  `FAIL` — tức bài sẽ xanh/đỏ vì lý do chẳng liên quan gì tới gate.
- Nguồn `FAIL` phải **tất định, không LLM**: `judge.py` còn là spec đến D18, và một money-shot phụ
  thuộc LLM là một bài không tái lập được.
- Phải có **bài đối trọng**. Không có nó thì `test_gate_blocks_on_fail` không phân biệt được *"gate
  chặn đúng"* với *"gate chặn mọi thứ"*, và một `verdict = "FAIL"` hằng số cũng cho nó xanh.

Lưới cũ (`strict=True`) canh *"seam chưa xong"*. Lưới mới canh *"gate có phân biệt PASS/FAIL hay
không"* — và đó là câu trả lời cho vế thứ ba của ADR (*"cái gì thay thế lưới cũ"*).

Boundary (R-SPEC A4): file này chỉ chạm seam AIE-2 sở hữu. Golden-set là của DE (tiêu thụ, không
dựng), interpreter là của AIE-1 (thay bằng `StubAgentRunner`), publish/rollback là của SWE (đọc
`gate.verdict`, không nối ở đây).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from uuid import UUID

from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub import judge as judge_module
from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.golden_case import GoldenSet
from studio_evalhub.golden_loader import load_golden_set
from studio_evalhub.harness import EvalHarness
from studio_evalhub.judge import LLMJudge

_TS = 0.9
_TC = 0.95


class _LLMLuonPass:
    """`LLM` double tất định — bài dưới đo **shape** của giá trị trả về, không đo nội dung chấm."""

    async def complete(self, prompt: str, **kwargs: object) -> str:
        return "PASS"


def _event(tenant_id: UUID, citations: list[str]) -> TraceEvent:
    return TraceEvent(
        event_id="e1",
        run_id="r1",
        agent_id="a",
        tenant_id=tenant_id,
        node_id="n1",
        node_type=NodeType.KB_RETRIEVE,
        ts="2026-08-10T00:00:00+00:00",
        inputs_hash="h",
        # `kb-retrieve` THẬT luôn mang `outputs["chunks"]` (`interpreter.py:347`), kể cả khi
        # retrieval trả rỗng. Stub phải mô hình đúng: thiếu hẳn khoá nghĩa là *payload không
        # đọc được* ⇒ `chunks_from_trace` fail-closed `None` (vá sau review evalhub#18, DE).
        outputs={"chunks": []},
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=citations,
    )


def _bad_runner(golden: GoldenSet, tenant_ids: Mapping[str, UUID]) -> StubAgentRunner:
    """Runner trả câu SAI có chủ đích cho MỌI case — nguồn FAIL tất định của money-shot.

    Hai nhánh sai theo **hai kiểu khác nhau**, để verdict FAIL không phụ thuộc một luật chấm duy nhất:

    - case trả-lời → answer KHÔNG chứa cụm `expected`, `refused=False` ⇒ `success=False`
    - case từ-chối → answer **trả lời thật** (`refused=False`) ⇒ `success=False`

    Ba ràng buộc, mỗi cái chặn một kiểu *"FAIL sai lý do"*:

    1. **Mỗi `CaseRun` mang đúng MỘT trace event**, không phải `events=[]`. `events=[]` sẽ làm case
       trượt vì luật `no-trace-no-proof` (T4/`DEC-05`), **không** vì answer tệ — bài sẽ xanh vì một
       lý do khác với điều nó khẳng định, đúng lớp xanh-giả.
    2. **Answer là câu trọn vẹn, đọc được**, chỉ sai nội dung. Chuỗi rỗng sẽ làm bài đỏ ở tầng parse
       chứ không ở tầng chấm.
    3. **Không đụng `Recipe.instructions`.** *"Sửa instructions tệ"* là mô tả demo ở tầng UI; ở tầng
       test thì thứ quan sát được là **output**, và `Recipe` là bút SWE (R-SPEC A4).

    Sinh từ **chính golden-set** nên nó sai theo định nghĩa, không theo một bảng chép tay sẽ mục khi
    DE đổi bộ case. Khoá fixture ba thành phần (D16): golden-30 có hai cặp trùng
    `(query, tenant_id)` chỉ khác `section_roles` (trục T6).
    """
    fixtures: dict[tuple[str, UUID, tuple[str, ...]], CaseRun] = {}
    for case in golden.cases:
        tenant_id = tenant_ids[case.tenant]
        if case.expects_refusal:
            # Đáng lẽ phải từ chối — đây lại trả lời thật, và trích cả chunk của kho khác.
            answer = AgentAnswer(
                answer="Theo tài liệu nội bộ, con số là 42 triệu đồng mỗi quý.",
                citations=[],
                refused=False,
            )
        else:
            # Câu trọn vẹn, đọc được, chỉ SAI nội dung — không chứa cụm `expected`.
            answer = AgentAnswer(
                answer="Theo tài liệu, con số là 999 phần trăm trong mọi trường hợp.",
                citations=[],
                refused=False,
            )
        fixtures[(case.query, tenant_id, tuple(case.section_roles))] = CaseRun(
            answer=answer,
            events=[_event(tenant_id, [])],  # ĐÚNG 1 event — FAIL phải đến từ answer, không từ no-trace
        )
    return StubAgentRunner(fixtures)


async def test_gate_blocks_on_fail(golden_30_path: Path, golden_30_ref: str, tenant_ids: Mapping[str, UUID]) -> None:
    """**MONEY-SHOT** (INV-6): recipe tệ chạy hết golden-30 ⇒ `gate.verdict == "FAIL"`.

    Bốn assert, không phải một — và ba dòng sau là thứ phân biệt *"gate chặn vì recipe tệ"* với
    *"gate chặn vì harness hỏng"*. Chỉ giữ dòng đầu thì một `EvalHarness.run` vỡ hoàn toàn cũng cho
    bài này xanh.

    `xfail(strict=True)` đã **gỡ hẳn** ở đây (`DEC-D16-04`), không đổi sang `strict=False`, và thân
    bài viết lại vì hai giá trị cũ (`agent-bad-instructions` / `golden-set-eval-1`) chưa bao giờ tồn
    tại."""
    golden = load_golden_set(golden_30_path, expect_ref=golden_30_ref)

    scorecard = await EvalHarness().run(
        "agent-bad-instructions",
        golden_30_ref,
        golden_set_path=golden_30_path,
        runner=_bad_runner(golden, tenant_ids),
        tenant_ids=tenant_ids,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
    )

    assert scorecard.gate.verdict == "FAIL"  # money-shot INV-6
    assert scorecard.aggregate.success_rate == 0.0  # FAIL vì answer sai, KHÔNG vì thiếu trace
    assert len(scorecard.results) == 30  # đã chạy hết bộ, không dừng sớm
    assert all(len(r.actual) > 0 for r in scorecard.results)  # answer trọn vẹn, không rỗng

    # FAIL trên CẢ HAI trục, và mỗi trục vì một luật khác nhau: success vì answer sai / refusal
    # không từ chối; citation vì trace không trích được chunk kỳ vọng nào.
    assert scorecard.aggregate.citation_accuracy == 0.0


async def test_gate_passes_on_good_recipe(
    golden_30_path: Path,
    golden_30_ref: str,
    tenant_ids: Mapping[str, UUID],
    runner_tot: Callable[[GoldenSet, Mapping[str, UUID]], StubAgentRunner],
) -> None:
    """**Bài đối trọng.** Cùng golden-set, runner trả lời ĐÚNG ⇒ `verdict == "PASS"`.

    Không có bài này thì `test_gate_blocks_on_fail` không phân biệt được *"gate chặn đúng"* với
    *"gate chặn mọi thứ"*: một `verdict = "FAIL"` hằng số, một `success_rate` luôn `0.0`, hay một
    `EvalHarness.run` trả rác đều cho money-shot xanh. Hai bài chạy trên **cùng 30 case, cùng ngưỡng
    `0.9/0.95`** — biến duy nhất là chất lượng câu trả lời."""
    golden = load_golden_set(golden_30_path, expect_ref=golden_30_ref)

    scorecard = await EvalHarness().run(
        "agent-good",
        golden_30_ref,
        golden_set_path=golden_30_path,
        runner=runner_tot(golden, tenant_ids),
        tenant_ids=tenant_ids,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
    )

    assert scorecard.gate.verdict == "PASS"
    assert scorecard.aggregate.success_rate == 1.0
    assert len(scorecard.results) == 30


async def test_judge_khong_tra_agreement_hang_so(tmp_path: Path) -> None:
    """**Bài kế nhiệm của `test_judge_seam_van_con_notimplemented`** — seam cuối đã được điền, nên
    nửa *"còn là spec"* hết chỗ bám; nửa **quan trọng hơn** được giữ nguyên ở đây.

    Lịch sử, vì mỗi bước đều được chính bài cũ dự báo trước:

    - bản gốc (`test_harness_judge_compute_not_implemented`) khẳng định **cả ba** seam còn raise;
    - **D16** (`DEC-D16-04`) thu hẹp còn `LLMJudge.judge`, ghi sẵn *"T2 và T4 điền hai trong ba, nên
      bài **phải đỏ** — đúng như thiết kế, và đúng cái nó tồn tại để báo"*, và tự đặt hạn **D18**;
    - **D18/T2** điền `LLMJudge.judge` thật ⇒ bài đỏ đúng như đã dự báo, bằng
      `TypeError: __init__() missing 1 required positional argument: 'llm'` — tức seam đã có hình
      dạng thật (`DEC-D18-02`: `LLM` tiêm vào), không còn là spec rỗng.

    **Không thu hẹp được lần thứ hai**, và đây là dữ kiện phải ghi chứ không phải suy: đo sau T2,
    `grep -rn "raise NotImplementedError" src/` ra **0 kết quả** — `compute_scorecard` đã được cài từ
    trước (nó raise `ValueError` cho `results` rỗng, không phải `NotImplementedError`). Không còn
    seam spec nào để bài trỏ tới, nên giữ lại vế `NotImplementedError` là giữ một bài **không thể
    xanh vì bất kỳ lý do đúng nào**.

    Nửa được giữ: lưới bắt *"stub một giá trị giả"*. Đây là lớp lỗi mà `judge.py:6-9`, `ADR B5` và §7
    ô DoD 2 cấm bằng ba chỗ khác nhau, luôn cùng một câu: **một `agreement` hằng không phân biệt được
    với một judge thật đồng thuận 100%**, và nó hỏng âm thầm mọi aggregate trên `agreement` (INV-4).

    Đây là lớp lỗi mà `judge.py:6-9`, `ADR B5` và §7 ô DoD 2 cấm bằng ba chỗ khác nhau, luôn cùng một
    câu: **một `agreement` hằng không phân biệt được với một judge thật đồng thuận 100%**, và nó hỏng
    âm thầm mọi aggregate trên `agreement` (INV-4). Ngày ô DoD được làm đầy bằng một hằng số là ngày
    con số agreement mất hết ý nghĩa cho mọi ngày sau.

    Khoá bằng **shape**, không bằng lời hứa: `judge()` trả `bool` — không có chỗ nào để nhét một
    `float` bịa ra. `agreement` là phép so với **nhãn tay**, mà `judge()` không nhận nhãn tay, nên
    mọi số nó trả ở vị trí đó **chỉ có thể** là hằng số. Bài này đỏ ngay khi ai đó nới chữ ký về
    `tuple[bool, float]` rồi trả `1.0` cho đủ ô."""
    judge = LLMJudge(_LLMLuonPass(), cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json")

    ket_qua = await judge.judge(case_id="case-1", expected="A", actual="A")

    assert isinstance(ket_qua, bool)
    assert "Judge(" not in (Path(judge_module.__file__ or "").read_text(encoding="utf-8"))
