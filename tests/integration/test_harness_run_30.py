"""Integration — **ô DoD 1**: `EvalHarness.run` chạy đủ 30 case thật của DE.

Bài duy nhất trong quadrant đi hết đường: file YAML của DE → loader → vòng lặp chạy case → chấm hai
nhánh → `compute_scorecard` → `Scorecard` có verdict. Mọi bài khác chỉ khoá một mắt của chuỗi đó.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from uuid import UUID

from studio_evalhub.agent_runner import StubAgentRunner
from studio_evalhub.golden_case import GoldenSet
from studio_evalhub.golden_loader import load_golden_set
from studio_evalhub.harness import EvalHarness
from studio_evalhub.judge import LLMJudge


async def test_run_tra_scorecard_30_case(
    golden_30_path: Path,
    golden_30_ref: str,
    tenant_ids: Mapping[str, UUID],
    runner_tot: Callable[[GoldenSet, Mapping[str, UUID]], StubAgentRunner],
) -> None:
    """`len(scorecard.results) == 30` và `golden_set_ref` khớp — DoD *"eval harness v1 chạy 30 case"*.

    Runner sinh từ chính golden-set nên nó trả lời đúng mọi case; điều đó làm bài **cũng** khoá được
    hai chuyện mà một bài chỉ đếm 30 sẽ bỏ sót:

    - `success_rate == 1.0` — không case nào rơi vào nhánh sai. Đây là chỗ trục T6 lộ ra: golden-30
      có hai cặp trùng `(query, tenant)` khác `section_roles`, và nếu khoá fixture bỏ qua
      `section_roles` thì đúng 2 case bị chấm bằng câu trả lời của nhánh ngược ⇒ `28/30`, không
      phải `30/30`.
    - mẫu số citation là **22**, không phải 30 — 8 case refusal bị loại theo `DEC-04`.

    Con số `30` một mình không phân biệt được *"chạy đúng 30 case"* với *"chạy 30 lần rồi chấm sai
    một nửa"*."""
    scorecard = await EvalHarness().run(
        "agent-1",
        golden_30_ref,
        golden_set_path=golden_30_path,
        runner=runner_tot(load_golden_set(golden_30_path, expect_ref=golden_30_ref), tenant_ids),
        tenant_ids=tenant_ids,
        threshold_success=0.9,
        threshold_citation_accuracy=0.95,
    )

    assert len(scorecard.results) == 30
    assert scorecard.golden_set_ref == golden_30_ref
    assert scorecard.agent_id == "agent-1"

    # Runner đúng theo định nghĩa ⇒ mọi case phải PASS. `28/30` ở đây nghĩa là hai case T6 bị nuốt.
    assert scorecard.aggregate.success_rate == 1.0
    assert scorecard.gate.verdict == "PASS"


class _LLMDemNhungKhongDuocGoi:
    """`LLM` double tồn tại **để chứng minh nó không bị gọi** — `calls` là toàn bộ nội dung phép đo."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def complete(self, prompt: str, **kwargs: object) -> str:
        self.calls.append(prompt)
        return "PASS"


async def test_golden_30_khong_case_nao_di_qua_judge(
    golden_30_path: Path,
    golden_30_ref: str,
    tenant_ids: Mapping[str, UUID],
    runner_tot: Callable[[GoldenSet, Mapping[str, UUID]], StubAgentRunner],
    tmp_path: Path,
) -> None:
    """**Đo lại trên dữ liệu THẬT** cái mà `DEC-D18-07` khẳng định: golden-30 đi exact-match TOÀN BỘ.

    Nền D18 đo `0/30` case khai `match_mode`. Bài này đo vế mạnh hơn và là vế thật sự quan trọng: kể
    cả khi judge **có mặt**, không case nào của bộ 30 được định tuyến sang nó. Đó là điều kiện để câu
    *"thêm selector production hôm nay là dựng đường dẫn cho một tập rỗng"* còn đúng — và nếu ngày nào
    đó nó sai, ngày đó phải lộ ra ở đây chứ không lộ ra ở hoá đơn API.

    `llm.calls == []` là money-shot của ô DoD *"CI deterministic"*: 30 case chạy hết, judge được
    truyền vào, và vẫn **0 lần chạm provider**.

    Ràng buộc đọc được nếu bài này đỏ: hoặc runner tốt đã hết tốt, hoặc luật định tuyến đã đổi. Cả hai
    đều là thứ phải biết ngay, không phải thứ để phát hiện sau.
    """
    golden = load_golden_set(golden_30_path, expect_ref=golden_30_ref)
    llm = _LLMDemNhungKhongDuocGoi()

    scorecard = await EvalHarness().run(
        "agent-tot",
        golden_30_ref,
        golden_set_path=golden_30_path,
        runner=runner_tot(golden, tenant_ids),
        tenant_ids=tenant_ids,
        threshold_success=0.9,
        threshold_citation_accuracy=0.95,
        judge=LLMJudge(llm, cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json"),
    )

    assert len(scorecard.results) == 30
    assert llm.calls == []
    assert all(r.judge is None for r in scorecard.results)
