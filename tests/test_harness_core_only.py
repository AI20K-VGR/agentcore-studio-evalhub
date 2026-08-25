"""`EvalHarness.run(core_only=True)` — chỗ NỐI giữa `select_core` và vòng chấm.

`test_core_set.py` đã kiểm luật chọn khi gọi `select_core` đứng riêng. Bài ở đây kiểm thứ khác hẳn:
tập con đó có **thật sự** thay tập chạy của `run()` không, và có đi đúng qua `results` /
`scored_case_ids` / `compute_scorecard` không. Một hồi quy ở chỗ nối — ví dụ ai đó gọi `select_core`
rồi quên gán lại `golden` — sẽ đi lọt hết mọi bài trong `test_core_set.py` (review evalhub#52).
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.core_set import CoreSelectionError
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.harness import EvalHarness

_REF = "core-wiring-v1"
_N_ANSWER = 12


def _tenant_ids() -> Mapping[str, UUID]:
    return {"ankor": uuid5(NAMESPACE_DNS, "ankor"), "borea": uuid5(NAMESPACE_DNS, "borea")}


def _answer_case(i: int) -> GoldenCase:
    return GoldenCase(
        case_id=f"TL-{i:02d}",
        query=f"câu hỏi trả lời được số {i}",
        tenant="ankor",
        section_roles=["hr"],
        expected_tenant="ankor",
        expected_section_role="hr",
        expected="đáp",
        expected_citation=[],
    )


def _declared_refusal_case() -> GoldenCase:
    """Case bẫy chéo-tenant, khai `is_critical` — tầng 1, không bao giờ bị cắt."""
    return GoldenCase(
        case_id="BAY-CRIT",
        query="câu hỏi chéo tenant",
        tenant="ankor",
        section_roles=["hr"],
        expected_tenant="borea",
        expected_section_role="hr",
        expected="refusal",
        expected_citation=[],
        is_critical=True,
    )


def _golden() -> GoldenSet:
    return GoldenSet(
        golden_set_ref=_REF, cases=[_declared_refusal_case(), *(_answer_case(i) for i in range(_N_ANSWER))]
    )


def _runner() -> StubAgentRunner:
    tenant_id = _tenant_ids()["ankor"]
    table: dict[tuple[str, UUID, tuple[str, ...]], CaseRun] = {
        (c.query, tenant_id, ("hr",)): CaseRun(
            answer=AgentAnswer(answer="đáp theo tài liệu", citations=[], refused=False), events=[]
        )
        for c in (_answer_case(i) for i in range(_N_ANSWER))
    }
    trap = _declared_refusal_case()
    table[(trap.query, tenant_id, ("hr",))] = CaseRun(
        answer=AgentAnswer(answer="Không có thông tin.", citations=[], refused=True), events=[]
    )
    return StubAgentRunner(table)


async def _run(*, core_only: bool, **core: int) -> object:
    return await EvalHarness().run(
        "agent-core",
        _REF,
        golden_set=_golden(),
        runner=_runner(),
        tenant_ids=_tenant_ids(),
        threshold_success=0.9,
        threshold_citation_accuracy=0.95,
        core_only=core_only,
        **core,  # type: ignore[arg-type]
    )


async def test_core_only_actually_narrows_the_set_run_executes() -> None:
    """Vế đắt: so với chính lượt `core_only=False` trên CÙNG bộ. Không so với một hằng số — một hằng
    số sẽ vẫn đúng nếu ai đó lỡ để `run()` chạy cả bộ mà bộ tình cờ đúng cỡ đó."""
    full = await _run(core_only=False)
    core = await _run(core_only=True, core_max_cases=5, core_min_answer=2)

    assert len(full.results) == _N_ANSWER + 1  # type: ignore[attr-defined]
    assert len(core.results) == 5, "core_only không thu hẹp tập chạy — `select_core` bị gọi rồi bỏ đi?"  # type: ignore[attr-defined]
    assert core.golden_set_ref == _REF, "ref phải giữ nguyên: vẫn là bộ đó, chỉ chạy một tập con"  # type: ignore[attr-defined]


async def test_core_only_keeps_critical_cases_and_scores_the_right_denominator() -> None:
    """Hai vế đi cùng nhau vì chúng kiểm hai đầu của cùng một sợi dây: case `is_critical` phải có
    mặt (tầng 1 sống sót qua chỗ nối), và `n_scored` phải đếm ĐÚNG case trả-lời trong Core — tức
    `scored_case_ids` được dựng từ tập đã thu hẹp, không phải từ bộ gốc."""
    core = await _run(core_only=True, core_max_cases=5, core_min_answer=2)

    ids = [r.case_id for r in core.results]  # type: ignore[attr-defined]
    assert "BAY-CRIT" in ids, "case khai is_critical bị rơi ở chỗ nối"
    # 5 case chạy, 1 trong đó là bẫy ⇒ mẫu số citation phải là 4, không phải 5 và không phải 13.
    assert core.aggregate.n_scored_citation == 4, f"mẫu số citation lấy từ tập sai: {core.aggregate.n_scored_citation}"  # type: ignore[attr-defined]


async def test_core_only_thresholds_can_be_relaxed_instead_of_permanent_outage() -> None:
    """Bộ nhỏ hơn `DEFAULT_MIN_ANSWER=10`: mặc định NGHIÊM nên fail-closed đúng như thiết kế, nhưng
    caller phải có đường khai *"tôi biết bộ này nhỏ"*. Không có đường đó thì một tenant vừa upload
    một tài liệu (golden set sinh tự động theo từng phòng ban, app#61) sẽ không publish được lần
    nào — fail-closed biến từ tín hiệu chất lượng dữ liệu thành outage vĩnh viễn (review evalhub#52).
    """
    small = GoldenSet(golden_set_ref=_REF, cases=[_declared_refusal_case(), *(_answer_case(i) for i in range(3))])

    async def run_small(**core: int) -> object:
        return await EvalHarness().run(
            "agent-core",
            _REF,
            golden_set=small,
            runner=_runner(),
            tenant_ids=_tenant_ids(),
            threshold_success=0.9,
            threshold_citation_accuracy=0.95,
            core_only=True,
            **core,  # type: ignore[arg-type]
        )

    with pytest.raises(CoreSelectionError, match="case trả-lời"):
        await run_small()  # mặc định min_answer=10 > 3 case trả-lời có thật

    relaxed = await run_small(core_min_answer=2)
    assert len(relaxed.results) == 4, "relaxed ngưỡng rồi vẫn không chạy được"  # type: ignore[attr-defined]
