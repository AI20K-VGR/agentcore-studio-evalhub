"""Test skeleton smoke-eval runner (D3, issue #14) — `score_case` 2 nhánh + `run_smoke` + stub.

KHÓA: luật chấm v0 (`docs/scorecard-v0.md` §2.3) và tính fail-closed của nhánh từ-chối. Không dựng
golden-set thật (DE), interpreter thật (AIE-1) hay publish gate (SWE) — chỉ seam AIE-2 sở hữu.
"""

from __future__ import annotations

import pytest
from studio_evalhub.agent_runner import AgentAnswer, StubAgentRunner
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.harness import EvalHarness, score_case


def _answerable_case() -> GoldenCase:
    return GoldenCase(
        case_id="c-answerable",
        query="Ankor nghỉ phép mấy ngày?",
        tenant="ankor",
        section_roles=["employee"],
        expected_tenant="ankor",
        expected="12 ngày/năm",
        expected_citation=["ankor-leave-001#c1"],
    )


def _refusal_case() -> GoldenCase:
    # tenant ankor hỏi dữ liệu borea → expects_refusal (expected_tenant != tenant)
    return GoldenCase(
        case_id="c-refusal",
        query="Thưởng của Borea?",
        tenant="ankor",
        section_roles=["employee"],
        expected_tenant="borea",
        expected="",
        expected_citation=[],
    )


# --- nhánh trả-lời-được -------------------------------------------------------------------------


def test_answerable_success() -> None:
    case = _answerable_case()
    answer = AgentAnswer(answer="12 ngày/năm", citations=["ankor-leave-001#c1"], refused=False)

    result = score_case(case, answer)

    assert result.success is True
    assert result.citation_accuracy == 1.0
    assert result.case_id == "c-answerable"


def test_answerable_wrong_answer_fails() -> None:
    case = _answerable_case()
    answer = AgentAnswer(answer="10 ngày/năm", citations=["ankor-leave-001#c1"], refused=False)

    assert score_case(case, answer).success is False


def test_answerable_refused_flag_fails() -> None:
    # đúng chữ nhưng agent lại tự từ chối → không tính pass
    case = _answerable_case()
    answer = AgentAnswer(answer="12 ngày/năm", citations=["ankor-leave-001#c1"], refused=True)

    assert score_case(case, answer).success is False


def test_answerable_partial_citation_accuracy() -> None:
    case = GoldenCase(
        case_id="c-two-cites",
        query="q",
        tenant="ankor",
        section_roles=["employee"],
        expected_tenant="ankor",
        expected="A",
        expected_citation=["ankor-a#c1", "ankor-b#c1"],
    )
    answer = AgentAnswer(answer="A", citations=["ankor-a#c1"], refused=False)

    result = score_case(case, answer)

    assert result.success is True  # success chấm theo answer, không theo citation
    assert result.citation_accuracy == 0.5


# --- nhánh từ-chối (fail-closed) ----------------------------------------------------------------


def test_refusal_success() -> None:
    case = _refusal_case()
    answer = AgentAnswer(answer="Không thể trả lời.", citations=[], refused=True)

    assert score_case(case, answer).success is True


def test_refusal_not_refused_fails() -> None:
    case = _refusal_case()
    answer = AgentAnswer(answer="Thưởng borea là X.", citations=[], refused=False)

    assert score_case(case, answer).success is False


def test_refusal_leak_fails() -> None:
    # agent "từ chối" nhưng vẫn trích chunk thuộc expected_tenant (borea) → rò → fail
    case = _refusal_case()
    answer = AgentAnswer(answer="Không thể trả lời.", citations=["borea-bonus-001#c1"], refused=True)

    assert score_case(case, answer).success is False


def test_refusal_unparseable_citation_fails() -> None:
    # citation không parse được tenant → fail-closed
    case = _refusal_case()
    answer = AgentAnswer(answer="Không thể trả lời.", citations=["garbage_no_tenant"], refused=True)

    assert score_case(case, answer).success is False


def test_refusal_other_tenant_citation_still_fails_closed() -> None:
    # trích chunk kho thứ ba (không phải borea): parse được nhưng vẫn đáng ngờ khi phải từ chối —
    # luật §2.3 chỉ cấm expected_tenant; case này parse được + không phải borea → theo luật là PASS.
    case = _refusal_case()
    answer = AgentAnswer(answer="Không thể trả lời.", citations=["carib-x-001#c1"], refused=True)

    # ghi nhận hành vi luật v0 hiện tại (chỉ chặn expected_tenant), để lộ nếu luật đổi ở D11
    assert score_case(case, answer).success is True


# --- run_smoke + stub ---------------------------------------------------------------------------


async def test_run_smoke_over_set() -> None:
    harness = EvalHarness()
    golden_set = GoldenSet(golden_set_ref="gs-smoke", cases=[_answerable_case(), _refusal_case()])
    runner = StubAgentRunner(
        {
            "Ankor nghỉ phép mấy ngày?": AgentAnswer(
                answer="12 ngày/năm", citations=["ankor-leave-001#c1"], refused=False
            ),
            "Thưởng của Borea?": AgentAnswer(answer="Không thể trả lời.", citations=[], refused=True),
        }
    )

    results = await harness.run_smoke(agent_id="agent-1", golden_set=golden_set, runner=runner)

    assert [r.case_id for r in results] == ["c-answerable", "c-refusal"]
    assert all(r.success for r in results)


async def test_stub_missing_fixture_raises() -> None:
    runner = StubAgentRunner({})

    with pytest.raises(LookupError):
        await runner.run_case(agent_id="a", query="chưa-có", tenant="ankor", section_roles=[])
