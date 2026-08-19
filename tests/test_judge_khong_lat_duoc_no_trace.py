"""Judge **không lật được cổng `DEC-05`** (`no-trace-no-proof`) — `DEC-D23-01`.

## Lỗ mà file này bịt, và nó tất định

`_hoi_judge` chỉ đưa cho judge `case.expected` và `scored.actual`. Judge **không quan sát `events`**.
Nhưng `_score_case_run` hạ `success` cho `case_run.events == []` theo `DEC-05` — một luật nói về
**trace**, kèm nguyên văn *"bất kể `answer` nói gì"*. Trước bản vá, hai vế đó đặt cạnh nhau cho ra
một đường lật sạch:

| Bước | Trước bản vá |
|---|---|
| Case nhánh trả-lời, `answer` **chứa đúng cụm** `expected`, `events == []` | nấc 1 FAIL — đúng `DEC-05` |
| `not scored.success` ⇒ hỏi judge | judge chỉ thấy text, và text **khớp** |
| judge trả `PASS` ⇒ `model_copy(success=verdict)` | **`success=True`** ⇒ `DEC-05` bị lật |

Không cần judge phán sai lần nào: ca này lật **100% số lần**, bằng chính hành vi đúng của judge. Và
nó chưa nổ trên production chỉ vì chưa caller nào truyền `judge=` (`apps/studio#20`) — tức nối dây
trước khi đóng cổng là bật một fail-open lên, không phải thêm một tầng chấm.

## Ba bài, và bài 2 là bài không suy ra được từ bài 1

1. **Kết quả** — case no-trace giữ `success=False` kể cả khi judge trả `PASS`.
2. **Judge không hề được gọi** — không phải *"gọi rồi bỏ verdict"*. Hai cách cho cùng một
   `Scorecard`, nên bài 1 xanh với **cả hai**; cái phân biệt là số lần gọi. Vế này có giá thật:
   `cap ≤100/ngày` (`INV-4`, `DEC-D18-05`) là quota chia sẻ, tiêu nó cho một verdict bị bỏ đi là
   tiêu vào không khí.
3. **Đối chứng dương** — case content-miss có trace vẫn lật được. Không có bài này thì một bản vá
   `_duoc_hoi_judge` luôn trả `False` (tức tắt hẳn judge) cũng xanh bài 1 và 2.

## Fixture bất đối xứng có chủ đích

`NT-01` trượt **chỉ vì** no-trace (text khớp), `NT-02` trượt **chỉ vì** content (có trace), `NT-03`
không trượt gì. Ba ca khác nhau ở hai trục độc lập — cân chúng theo cùng một kiểu thì một cổng đọc
sai trục vẫn cho ra cùng số lần gọi judge, đúng lớp lỗi `M-G7` đã dạy ở D20.

Mutant đã gieo: `docs/mutations/judge-no-trace-d23.md`.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from studio_contracts import NodeType, Scorecard, Tokens, TraceEvent
from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.harness import EvalHarness
from studio_evalhub.judge import LLMJudge

_REF = "fx-no-trace-v1"
_TS = 0.9
_TC = 0.95

# Cả ba case đều **nhánh trả-lời**: `expected_tenant == tenant` và `expected_section_role` nằm trong
# `section_roles` (hai trục của `GoldenCase.expects_refusal`). Nhánh từ-chối không đi qua judge nên
# không nói được gì về cổng này.
_YAML = """\
golden_set_ref: fx-no-trace-v1
cases:
  - case_id: NT-01
    query: "Nghỉ phép năm bao nhiêu ngày?"
    tenant: ankor
    section_roles: [hr]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "12 ngày"
    expected_citation: []
  - case_id: NT-02
    query: "Duyệt chi phí mất bao lâu?"
    tenant: ankor
    section_roles: [hr]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "ba ngày làm việc"
    expected_citation: []
  - case_id: NT-03
    query: "Thử việc bao nhiêu tháng?"
    tenant: ankor
    section_roles: [hr]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "hai tháng"
    expected_citation: []
"""


class _FakeLLM:
    """`LLM` double — `calls` là thứ bài 2 assert lên. `reply` mặc định `"PASS"`: judge **đồng ý**,
    tức đặt cổng vào ca xấu nhất của nó."""

    def __init__(self, reply: str = "PASS") -> None:
        self.calls: list[str] = []
        self._reply = reply

    async def complete(self, prompt: str, **kwargs: object) -> str:
        del kwargs  # accepted for Protocol-shape parity
        self.calls.append(prompt)
        return self._reply


def _tenant_ids() -> Mapping[str, UUID]:
    return {"ankor": uuid5(NAMESPACE_DNS, "ankor")}


def _event(tenant_id: UUID) -> TraceEvent:
    return TraceEvent(
        event_id="e1",
        run_id="r1",
        agent_id="a",
        tenant_id=tenant_id,
        node_id="n1",
        node_type=NodeType.KB_RETRIEVE,
        ts="2026-08-19T00:00:00+00:00",
        inputs_hash="h",
        outputs={"chunks": []},
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=[],
    )


def _runner() -> StubAgentRunner:
    """`NT-01` là ca khai thác: `answer` **chứa đúng** `"12 ngày"` nhưng `events=[]`.

    Nấc 1 chấm nó FAIL **chỉ vì** `DEC-05` — `score_case` nhánh trả-lời đã cho `success=True` (không
    từ chối, chứa cụm), rồi `_score_case_run` hạ xuống vì không có trace. Đó là điều làm nó thành
    phép đo về **cổng**, không phải về chất lượng câu trả lời.

    `NT-02` trượt vì content (`"Khoảng 3 ngày làm việc."` truyền tải đúng `"ba ngày làm việc"` mà
    `_contains_phrase` không bắt được) và **có** trace ⇒ đây là ca judge được phép lật.

    `NT-03` khớp exact-match và có trace ⇒ không trượt gì, không được hỏi judge.
    """
    tenant_id = _tenant_ids()["ankor"]
    return StubAgentRunner(
        {
            ("Nghỉ phép năm bao nhiêu ngày?", tenant_id, ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Theo tài liệu, nghỉ phép 12 ngày.", citations=[], refused=False),
                events=[],
            ),
            ("Duyệt chi phí mất bao lâu?", tenant_id, ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Khoảng 3 ngày làm việc.", citations=[], refused=False),
                events=[_event(tenant_id)],
            ),
            ("Thử việc bao nhiêu tháng?", tenant_id, ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Thử việc hai tháng.", citations=[], refused=False),
                events=[_event(tenant_id)],
            ),
        }
    )


async def _chay(path: Path, judge: LLMJudge | None) -> Scorecard:
    return await EvalHarness().run(
        "agent-nt",
        _REF,
        golden_set_path=path,
        runner=_runner(),
        tenant_ids=_tenant_ids(),
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        judge=judge,
    )


def _ket_qua(scorecard: Scorecard) -> dict[str, bool]:
    return {r.case_id: r.success for r in scorecard.results}


@pytest.fixture
def golden_nt(tmp_path: Path) -> Path:
    path = tmp_path / "fx-no-trace.yaml"
    path.write_text(_YAML, encoding="utf-8")
    return path


async def test_no_trace_judge_khong_lat_duoc_cong_dec05(golden_nt: Path, tmp_path: Path) -> None:
    """**Bài chính.** `NT-01`: `events == []`, `answer` chứa đúng cụm, judge trả `PASS` ⇒ `success`
    vẫn `False`.

    Đây là bài **đỏ trước bản vá**: không có `_duoc_hoi_judge`, `not scored.success` là điều kiện duy
    nhất, nên `NT-01` đi qua judge và `model_copy(success=True)` ghi đè đúng cổng `DEC-05`.

    Assert cả bản đồ 3 case chứ không riêng `NT-01`: một cổng đóng quá tay (chặn luôn `NT-02`) cũng
    làm `NT-01` xanh, và nó phải lộ ra ở **cùng một dòng assert** thay vì phải nhớ chạy bài 3."""
    llm = _FakeLLM(reply="PASS")
    judge = LLMJudge(llm, cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json")

    scorecard = await _chay(golden_nt, judge=judge)

    assert _ket_qua(scorecard) == {"NT-01": False, "NT-02": True, "NT-03": True}


async def test_no_trace_judge_khong_he_duoc_goi(golden_nt: Path, tmp_path: Path) -> None:
    """**Không hỏi**, chứ không phải *hỏi rồi bỏ verdict* — bài 1 xanh với cả hai cách.

    `cap ≤100/ngày` (`INV-4`, `DEC-D18-05`) là quota chia sẻ và **bền ngoài tiến trình**: một lần gọi
    tiêu vào một case mà verdict chắc chắn bị bỏ là một lần gọi mất hẳn, không phải một lần gọi vô
    hại. Nên bất biến *"không hỏi"* cần lưới riêng đếm số lần gọi.

    `len(llm.calls) == 1` chứ không `<= 1`: vế `<=` xanh cả khi cổng chặn luôn `NT-02`. Và assert nội
    dung prompt để biết **case nào** đã đi qua — `NT-01` và `NT-02` cùng ra 1 lần gọi nếu chỉ đếm."""
    llm = _FakeLLM(reply="PASS")
    judge = LLMJudge(llm, cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json")

    await _chay(golden_nt, judge=judge)

    assert len(llm.calls) == 1
    assert "ba ngày làm việc" in llm.calls[0]  # NT-02
    assert "12 ngày" not in llm.calls[0]  # KHÔNG phải NT-01


async def test_doi_chung_duong_case_content_miss_co_trace_van_lat_duoc(golden_nt: Path, tmp_path: Path) -> None:
    """**Đối chứng dương.** Không có bài này, một `_duoc_hoi_judge` luôn trả `False` — tức tắt hẳn
    nhánh judge — cũng xanh bài 1 và bài 2.

    So `NT-02` giữa hai lần chạy thay vì assert một hằng số: nó nói *"chính judge là thứ lật"*, chứ
    không chỉ *"NT-02 xanh"*. `NT-01` phải `False` ở **cả hai** lần — cổng `DEC-05` không phụ thuộc
    judge có mặt hay không."""
    llm = _FakeLLM(reply="PASS")
    judge = LLMJudge(llm, cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json")

    co_judge = await _chay(golden_nt, judge=judge)
    khong_judge = await _chay(golden_nt, judge=None)

    assert _ket_qua(khong_judge) == {"NT-01": False, "NT-02": False, "NT-03": True}
    assert _ket_qua(co_judge)["NT-02"] is True
    assert _ket_qua(co_judge)["NT-01"] is False
