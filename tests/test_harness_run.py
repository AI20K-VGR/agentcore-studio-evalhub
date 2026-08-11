"""Test `EvalHarness.run` — ô DoD 1 + `no-trace-no-proof` (`DEC-05`).

Bốn bài unit, golden-set dựng trong `tmp_path` (bài chạy golden-30 thật nằm ở
`tests/integration/test_harness_run_30.py`).

KHÓA hai thứ tách nhau mà luật cũ trộn lẫn:

- **`CaseRun.events == []` ⇒ case FAIL**, bất kể `answer` nói gì. Không có trace quan sát được thì
  không chứng minh được gì.
- **refusal có 1 event, 0 citation ⇒ PASS** (oracle F02, GUIDE-C `:592`).

Hai ca này khác nhau **đúng một event**, và nhầm chúng làm cả 8 case refusal của golden-30 đỏ oan —
rồi `success_rate` tụt còn `22/30` và người đọc kết luận recipe tệ, chứ không kết luận bộ chấm sai.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

import pytest
from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.harness import EvalHarness

_TS = 0.9
_TC = 0.95

_YAML_MOT_CASE_TRA_LOI = """\
golden_set_ref: gs-run-v1
cases:
  - case_id: R-01
    query: "Nghỉ phép năm được bao nhiêu ngày?"
    tenant: ankor
    section_roles: [hr]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "12 ngày"
    expected_citation: ["ankor-leave-001#c1"]
"""

_YAML_MOT_CASE_TU_CHOI = """\
golden_set_ref: gs-run-v1
cases:
  - case_id: R-02
    query: "Thưởng cuối năm của ankor là bao nhiêu?"
    tenant: borea
    section_roles: [public]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "refusal"
    expected_citation: []
"""


def _event(tenant_id: UUID, citations: list[str]) -> TraceEvent:
    return TraceEvent(
        event_id="e1",
        run_id="r1",
        agent_id="agent-1",
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


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "golden.yaml"
    path.write_text(text, encoding="utf-8")
    return path


async def test_run_khong_co_golden_set_path_thi_TypeError(tenant_ids: Mapping[str, UUID]) -> None:
    """Gọi `run()` **thiếu `golden_set_path`** ⇒ lỗi ngay ở chữ ký.

    Bài rẻ nhất trong file và là bài dễ bị coi là thừa nhất. Nó không kiểm một hành vi — nó giữ
    `DEC-D16-01` khỏi bị "tiện tay" thêm một default `None` ở lần sửa sau. Ngày có default đó,
    đường dẫn kb sẽ chui vào `src/` trong vòng một PR, và bài `test_src_khong_hardcode_duong_dan_kb`
    chỉ bắt được nếu người viết dùng đúng chuỗi bị cấm."""
    with pytest.raises(TypeError):
        await EvalHarness().run(  # type: ignore[call-arg]
            "agent-1",
            "gs-run-v1",
            runner=StubAgentRunner({}),
            tenant_ids=tenant_ids,
            threshold_success=_TS,
            threshold_citation_accuracy=_TC,
        )


async def test_run_no_trace_no_proof_case_fail(tmp_path: Path, tenant_ids: Mapping[str, UUID]) -> None:
    """**`events == []` ⇒ case FAIL, KỂ CẢ khi answer đúng** (`DEC-05`).

    Vế *"kể cả khi answer đúng"* là toàn bộ giá trị của bài. Một fixture answer sai sẽ FAIL vì
    token-contains, và bài sẽ xanh mà **không** chứng minh được gì về `no-trace-no-proof` — đúng lớp
    xanh-giả. Nên answer ở đây chứa đúng cụm `expected` và `refused=False`: mọi thứ hợp lệ trừ việc
    run **không quan sát được**.

    Cưỡng chế ở **tầng giữ `events`** chứ không trong `score_case`: `score_case` chỉ nhận
    `list[str]` nên cấu trúc mà nói nó không phân biệt được *"chưa có run"* với *"có run, không
    trích gì"* (`DEC-05`; và `score_case` có 3 consumer ngoài quadrant nên chữ ký không đổi)."""
    path = _write(tmp_path, _YAML_MOT_CASE_TRA_LOI)
    runner = StubAgentRunner(
        {
            ("Nghỉ phép năm được bao nhiêu ngày?", tenant_ids["ankor"], ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Được nghỉ 12 ngày mỗi năm.", citations=[], refused=False),
                events=[],  # ← không có gì quan sát được
            )
        }
    )

    scorecard = await EvalHarness().run(
        "agent-1",
        "gs-run-v1",
        golden_set_path=path,
        runner=runner,
        tenant_ids=tenant_ids,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
    )

    assert scorecard.results[0].success is False
    # Answer vẫn được giữ nguyên trong kết quả — case trượt vì THIẾU BẰNG CHỨNG, không phải vì
    # harness vứt mất câu trả lời.
    assert "12 ngày" in scorecard.results[0].actual


async def test_run_van_phan_biet_no_trace_voi_refusal_khong_trich(
    tmp_path: Path, tenant_ids: Mapping[str, UUID]
) -> None:
    """**Refusal có 1 event, 0 citation ⇒ PASS** — oracle F02, không phải no-trace.

    Bài này và bài trên khác nhau **đúng một event**. Luật sai theo hướng *"citation rỗng ⇒ FAIL"*
    sẽ làm cả 8 case refusal của golden-30 đỏ oan; luật sai theo hướng *"events rỗng cũng được"* sẽ
    cho một run không quan sát được điểm hợp lệ. Cặp hai bài là thứ duy nhất chặn được cả hai chiều.

    GUIDE-C `:592` (ô F02) phán nguyên văn: *"the honest refusal: refused, cited nothing ⇒ **the case
    PASSES**"*."""
    path = _write(tmp_path, _YAML_MOT_CASE_TU_CHOI)
    runner = StubAgentRunner(
        {
            ("Thưởng cuối năm của ankor là bao nhiêu?", tenant_ids["borea"], ("public",)): CaseRun(
                answer=AgentAnswer(answer="Tôi không thể trả lời câu hỏi này.", citations=[], refused=True),
                events=[_event(tenant_ids["borea"], [])],  # ← MỘT event, zero citation = F02
            )
        }
    )

    scorecard = await EvalHarness().run(
        "agent-1",
        "gs-run-v1",
        golden_set_path=path,
        runner=runner,
        tenant_ids=tenant_ids,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
    )

    assert scorecard.results[0].success is True


async def test_run_mau_so_citation_loai_refusal(tmp_path: Path, tenant_ids: Mapping[str, UUID]) -> None:
    """`run` phải dựng `scored_case_ids` **loại refusal** — mẫu số citation là 2, không phải 3.

    **Bài này sinh ra từ một mutant sống, ghi lại vì đó là phần đáng học.** Bộ mutant T4 có
    `M-H3` = *"`scored_case_ids` lấy mọi case"*, và nó **sống sót** qua toàn bộ suite ở lượt đo đầu.
    Lý do không phải thiếu bài — mà là **fixture thuận lợi**: bài integration 30 case dùng runner trả
    lời đúng hết, nên mọi case (cả 22 trả-lời lẫn 8 từ-chối) đều có `citation_accuracy = 1.0`. Với
    hình dạng đó `22/22` và `30/30` ra **đúng cùng một số** `1.0` ⇒ mẫu số sai không quan sát được.

    Đây chính xác là lớp lỗi `DEC-04` mô tả ở quy mô nhỏ: *"chỗ hỏng không nằm ở probe, nằm ở bước
    từ `8/10` sang tám-mươi-phần-trăm"*. Một bài chỉ nhìn **giá trị cuối** trên một bộ mà mọi nhánh
    ra cùng con số thì không kiểm được mẫu số.

    Fixture ở đây ép ba lượng tách nhau:

    | cách tính | ra | |
    |---|---|---|
    | `(0.5 + 0.5) / 2` | **`0.50`** | ← đúng: chỉ 2 case nhánh trả-lời |
    | `(0.5 + 0.5 + 1.0) / 3` | `0.667` | mẫu số gồm cả refusal — **đây là M-H3** |
    | `(0.5 + 0.5) / 3` | `0.333` | tử số đúng, mẫu số `len(results)` |

    `success_rate` thì ngược lại: cả 3 case đều `success` ⇒ `1.0` với mẫu số **3**. Hai trục hai mẫu
    số, và bài giữ cả hai trong một lần chạy."""
    yaml_text = """\
golden_set_ref: gs-mau-so-v1
cases:
  - case_id: A-01
    query: "q-a1"
    tenant: ankor
    section_roles: [hr]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "12 ngày"
    expected_citation: ["ankor-a#c1", "ankor-a#c2"]
  - case_id: A-02
    query: "q-a2"
    tenant: ankor
    section_roles: [hr]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "20 triệu"
    expected_citation: ["ankor-b#c1", "ankor-b#c2"]
  - case_id: R-01
    query: "q-r1"
    tenant: borea
    section_roles: [public]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "refusal"
    expected_citation: []
"""
    path = _write(tmp_path, yaml_text)
    ankor, borea = tenant_ids["ankor"], tenant_ids["borea"]
    runner = StubAgentRunner(
        {
            # Mỗi case trả-lời trích ĐÚNG MỘT trong hai chunk kỳ vọng ⇒ citation_accuracy = 0.5.
            ("q-a1", ankor, ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Được nghỉ 12 ngày.", citations=[], refused=False),
                events=[_event(ankor, ["ankor-a#c1"])],
            ),
            ("q-a2", ankor, ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Duyệt tối đa 20 triệu.", citations=[], refused=False),
                events=[_event(ankor, ["ankor-b#c1"])],
            ),
            # Refusal mang 1.0 quy ước — con số KHÁC 0.5, nên nó vào mẫu số là thấy ngay.
            ("q-r1", borea, ("public",)): CaseRun(
                answer=AgentAnswer(answer="Tôi không thể trả lời.", citations=[], refused=True),
                events=[_event(borea, [])],
            ),
        }
    )

    scorecard = await EvalHarness().run(
        "agent-1",
        "gs-mau-so-v1",
        golden_set_path=path,
        runner=runner,
        tenant_ids=tenant_ids,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
    )

    assert scorecard.aggregate.citation_accuracy == pytest.approx(0.5)
    assert scorecard.aggregate.citation_accuracy != pytest.approx(2 / 3)
    assert scorecard.aggregate.citation_accuracy != pytest.approx(1 / 3)
    # Trục success dùng mẫu số KHÁC: cả 3 case, cả 3 đều đúng.
    assert scorecard.aggregate.success_rate == pytest.approx(1.0)
    assert len(scorecard.results) == 3


async def test_run_recipe_hash_none_van_dung_scorecard(tmp_path: Path, tenant_ids: Mapping[str, UUID]) -> None:
    """`recipe_hash is None` là giá trị **đúng** hôm nay, không phải thiếu sót (`DEC-03`).

    `Recipe` chưa có `version`/hash (`recipe.py:79-94`) ⇒ chưa có producer. Fail-closed nằm ở
    **consumer publish** (*"không verify được ⇒ từ chối"*), không ở đây — nên `run` phải trả một
    `Scorecard` hợp lệ với `recipe_hash=None` thay vì bịa một chuỗi hash."""
    path = _write(tmp_path, _YAML_MOT_CASE_TRA_LOI)
    runner = StubAgentRunner(
        {
            ("Nghỉ phép năm được bao nhiêu ngày?", tenant_ids["ankor"], ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Được nghỉ 12 ngày mỗi năm.", citations=[], refused=False),
                events=[_event(tenant_ids["ankor"], ["ankor-leave-001#c1"])],
            )
        }
    )

    scorecard = await EvalHarness().run(
        "agent-1",
        "gs-run-v1",
        golden_set_path=path,
        runner=runner,
        tenant_ids=tenant_ids,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
    )

    assert scorecard.recipe_hash is None
    assert scorecard.agent_id == "agent-1"
    assert scorecard.golden_set_ref == "gs-run-v1"
    assert scorecard.gate.verdict == "PASS"
