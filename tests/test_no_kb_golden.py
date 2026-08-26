"""Bộ golden dựng sẵn cho agent **không gắn KB** — `studio_evalhub.no_kb_golden`.

Agent không có node `kb-retrieve` thì không có kho nào để tra, cũng không có kho nào để **rò**.
Nên bộ này bỏ hẳn nhánh bẫy (trục rò-dữ-liệu đo một thứ không tồn tại) và cho **mọi** case là
nhánh trả-lời, với `expected` chính là câu *"không có thông tin"*.

Ba bất biến dưới đây là lý do bộ này đi lọt được cổng mà không phải nới chốt nào — đổi một trong
ba là bộ quay lại đúng bức tường cũ (`Scorecard` validator chặn `citation_accuracy=None` + PASS),
nên mỗi cái có một bài riêng chứ không gộp.
"""

from __future__ import annotations

import pytest
from studio_contracts.scorecard import CaseResult
from studio_evalhub.compute import compute_scorecard
from studio_evalhub.core_set import select_core
from studio_evalhub.no_kb_golden import NO_KB_GOLDEN_SET_REF, NO_KB_TENANT_LABEL, no_kb_golden_set


def test_every_case_is_answer_branch() -> None:
    """Bất biến 1 — không case nào là nhánh từ-chối.

    Một case từ-chối lọt vào sẽ KHÔNG vào `scored_case_ids`, làm mẫu số citation nhỏ đi; nếu bộ
    chỉ toàn từ-chối thì mẫu số về 0 ⇒ `citation_accuracy = None` ⇒ verdict không bao giờ PASS
    được (validator `Scorecard`). Đây chính là bức tường bộ này sinh ra để đi vòng."""
    golden = no_kb_golden_set()
    assert golden.cases, "bộ rỗng thì không chấm được gì"
    assert [c.case_id for c in golden.cases if c.expects_refusal] == []


def test_every_case_expects_no_citation() -> None:
    """Bất biến 2 — `expected_citation` rỗng ở MỌI case.

    `expected_citation == []` ở nhánh trả-lời cho `citation_accuracy = 1.0` **thật**
    (`harness.py`), không phải quy ước vacuous-truth của nhánh từ-chối. Một case đòi trích dẫn sẽ
    luôn trượt — agent không-KB không trích được gì — và kéo trục citation xuống dưới ngưỡng."""
    assert [c.case_id for c in no_kb_golden_set().cases if c.expected_citation] == []


def test_expected_phrase_is_the_not_knowing_answer() -> None:
    """Bất biến 3 — `expected` là câu nói-không-biết, không phải một đáp án nội dung.

    Cổng đo *"agent có bịa ra một chính sách không tồn tại không"*. Đổi `expected` thành một đáp án
    thật là biến bộ này thành bộ đo kiến thức nền của model — một trục khác hẳn, và là trục agent
    không-KB đáng lẽ phải trượt."""
    for case in no_kb_golden_set().cases:
        assert "không có thông tin" in case.expected.lower(), case.case_id


def test_core_selection_accepts_the_set_at_the_gate_budget() -> None:
    """`publish.py` gọi `select_core(..., core_min_answer=1)`. Bộ này phải đi lọt chốt đó mà không
    cần cờ nới nào — nếu không thì cổng ném `CoreSelectionError` trước khi kịp chấm."""
    selection = select_core(no_kb_golden_set(), min_answer=1)
    assert selection.n_answer == len(selection.golden.cases)
    assert selection.n_refusal == 0


def test_agent_that_says_it_does_not_know_passes_the_gate() -> None:
    """Đầu-cuối: agent trả lời đúng kiểu ⇒ citation ĐO ĐƯỢC (1.0, không phải None) ⇒ PASS.

    Bài này là thứ chứng minh bức tường đã đi vòng được — dựng `Scorecard` thật, đi qua đúng
    validator từng chặn (`citation_accuracy=None` + PASS)."""
    golden = no_kb_golden_set()
    results = [
        CaseResult(
            case_id=c.case_id,
            expected=c.expected,
            actual="Tôi không có thông tin về việc này.",
            success=True,
            citation_accuracy=1.0,
        )
        for c in golden.cases
    ]
    card = compute_scorecard(
        "agent-khong-kb",
        NO_KB_GOLDEN_SET_REF,
        results,
        0.9,
        0.95,
        scored_case_ids={c.case_id for c in golden.cases},
        recipe_hash="h",
    )
    assert card.aggregate.citation_accuracy == 1.0
    assert card.gate.verdict == "PASS"


def test_agent_that_invents_an_answer_still_fails() -> None:
    """Vế bất đối xứng: cổng vẫn THẬT. Agent bịa ra chính sách thay vì nói không biết ⇒ trượt trục
    `success` ⇒ FAIL. Thiếu bài này thì bài trên không phân biệt được với một cổng luôn PASS."""
    golden = no_kb_golden_set()
    results = [
        CaseResult(
            case_id=c.case_id,
            expected=c.expected,
            actual="Công ty cho nghỉ 12 ngày/năm.",
            success=False,
            citation_accuracy=1.0,
        )
        for c in golden.cases
    ]
    card = compute_scorecard(
        "agent-khong-kb",
        NO_KB_GOLDEN_SET_REF,
        results,
        0.9,
        0.95,
        scored_case_ids={c.case_id for c in golden.cases},
        recipe_hash="h",
    )
    assert card.gate.verdict == "FAIL"


def test_tenant_label_is_not_a_real_tenant_name() -> None:
    """Nhãn tenant của bộ là hằng số, KHÔNG phải tên tenant thật — `publish.py` bơm nó vào bảng tra
    trỏ về tenant của phiên. Nhãn trùng tên một công ty thật sẽ làm case chạy dưới tenant sai."""
    assert NO_KB_TENANT_LABEL.startswith("__")
    assert all(c.tenant == NO_KB_TENANT_LABEL for c in no_kb_golden_set().cases)


def test_set_is_a_fresh_object_each_call() -> None:
    """Trả bản mới mỗi lần gọi, không phải một hằng số dùng chung: `select_core` dựng `GoldenSet`
    mới từ `cases` nhưng caller khác vẫn cầm được list gốc — chia sẻ một object giữa hai lượt
    publish là đúng chỗ một lượt sửa nhầm rò sang lượt sau."""
    assert no_kb_golden_set() is not no_kb_golden_set()
