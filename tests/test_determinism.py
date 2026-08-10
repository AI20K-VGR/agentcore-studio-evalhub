"""Determinism của smoke-eval — Day 7, DoD #34 (*"chạy lại ra **cùng** bảng điểm"*).

Vai AIE-2 ở `day-07.md`: *"xác nhận toàn luồng deterministic (chạy 2 lần ra cùng số). Đây là điều
kiện để CI đứng vững — không flaky do model."* Luật vàng: *"AC không phụ thuộc IQ của LLM — chấm
pipeline/trace, không chấm chất lượng câu trả lời."*

## Vì sao cần file này khi đã có `test_smoke_runner.py`

`test_smoke_runner.py` (26 test) khoá **giá trị** của điểm: nhánh nào PASS, `citation_accuracy` bằng
bao nhiêu, leak-check có bắt không. Nó KHÔNG khoá **tính ổn định** — một scorer trả đúng giá trị ở
lượt đầu mà lượt sau lệch vẫn qua sạch mọi test ở đó. Trước file này, `run_smoke` có đúng **1** test
(`test_run_smoke_over_set`, chạy một lượt) và `_render` có **0**.

Cụ thể hơn: `RunResult.run_id` là `uuid4()` và `TraceEvent.ts` là `datetime.now(UTC)` (engine
`interpreter.py`), nên **metadata của trace KHÔNG tất định** giữa hai lượt chạy. Điểm số vẫn phải tất
định. Ranh giới đó chính là thứ 4 test dưới đây khoá — và nếu nó vỡ thì CI thành flaky vì một lý do
không liên quan gì tới chất lượng câu trả lời.

## Cố ý KHÔNG pin nguyên văn bảng `_render`

Định dạng bảng còn chốt ở D8 (`Plan` D7→D8). Snapshot nguyên văn hôm nay thì mai sửa cột là đỏ oan
hai ngày liền, và người sửa sẽ học được thói "cập nhật snapshot cho hết đỏ" — đúng thứ làm snapshot
mất giá trị. Ở đây pin **equality của `SmokeResult`**; snapshot format freeze **một lần** ở D8.

## Ba nguồn không-tất-định đã loại trừ ở tầng này

`StubAgentRunner` tra fixture theo `(query, tenant_id)` → không có LLM, không network, không đồng hồ.
`_ANKOR`/`_BOREA` là `uuid5` (hằng theo tên, không phải `uuid4`). Nên mọi lệch nếu có đều đến từ
scorer, không từ môi trường — đó là điều kiện để 4 test này nói được điều gì.
"""

from __future__ import annotations

import os
import subprocess
import sys
from uuid import NAMESPACE_DNS, UUID, uuid5

from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.harness import EvalHarness, SmokeResult, citations_from_trace, score_case

_ANKOR: UUID = uuid5(NAMESPACE_DNS, "ankor")


def _event(
    citations: list[str] | None,
    *,
    node_type: NodeType = NodeType.KB_RETRIEVE,
    event_id: str = "e1",
    run_id: str = "r1",
    ts: str = "2026-07-28T00:00:00+00:00",
) -> TraceEvent:
    """`TraceEvent` với metadata mở ra được — 3 field `event_id`/`run_id`/`ts` là đúng những field
    engine sinh không-tất-định, nên test bên dưới cần điều khiển chúng."""
    return TraceEvent(
        event_id=event_id,
        run_id=run_id,
        agent_id="agent-1",
        tenant_id=_ANKOR,
        node_id="n1",
        node_type=node_type,
        ts=ts,
        inputs_hash="h",
        outputs={},
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=citations,
    )


def _answerable_case() -> GoldenCase:
    return GoldenCase(
        case_id="c-answerable",
        query="Ankor nghỉ phép mấy ngày?",
        tenant="ankor",
        section_roles=["employee"],
        expected_tenant="ankor",
        expected_section_role="employee",
        expected="12 ngày",
        expected_citation=["ankor-leave-001#c1"],
    )


def _refusal_case() -> GoldenCase:
    return GoldenCase(
        case_id="c-refusal",
        query="Thưởng của Borea?",
        tenant="ankor",
        section_roles=["employee"],
        expected_tenant="borea",
        expected_section_role="public",
        expected="refusal",
        expected_citation=[],
    )


def _golden_set() -> GoldenSet:
    return GoldenSet(golden_set_ref="gs-determinism", cases=[_answerable_case(), _refusal_case()])


def _runner() -> StubAgentRunner:
    return StubAgentRunner(
        {
            ("Ankor nghỉ phép mấy ngày?", _ANKOR, ("employee",)): CaseRun(
                answer=AgentAnswer(answer="Được nghỉ 12 ngày.", citations=[], refused=False),
                events=[_event(["ankor-leave-001#c1"])],
            ),
            ("Thưởng của Borea?", _ANKOR, ("employee",)): CaseRun(
                answer=AgentAnswer(answer="Không có thông tin.", citations=[], refused=True),
                events=[_event([])],
            ),
        }
    )


# ---------------------------------------------------------------------------
# 1. Lượt-2-bằng-lượt-1 — DoD "chạy lại ra CÙNG bảng điểm"
# ---------------------------------------------------------------------------


async def test_run_smoke_twice_yields_identical_results() -> None:
    """KHÓA D1: hai lượt `run_smoke` trên cùng input ra `SmokeResult` **bằng nhau từng field**.

    So bằng `==` trên `list[SmokeResult]` chứ không so từng field bằng tay: `SmokeResult` là pydantic
    `frozen=True` nên `__eq__` đã bao mọi field, và **thêm field mới vào model sẽ tự động được so** —
    viết tay thì field mới lọt qua im lặng. `test_equality_actually_discriminates` bên dưới là chỗ
    chứng minh phép `==` này có răng, không phải luôn-True.

    Dựng runner MỚI cho mỗi lượt: nếu tái dùng một instance thì test còn chứng minh thêm "runner không
    giữ trạng thái", tức trộn hai điều cần khoá vào một assert. `StubAgentRunner` đã có test riêng cho
    chuyện đó (`test_stub_missing_fixture_raises`).
    """
    golden = _golden_set()

    first = await EvalHarness().run_smoke(
        agent_id="agent-1", golden_set=golden, runner=_runner(), tenant_ids={"ankor": _ANKOR}
    )
    second = await EvalHarness().run_smoke(
        agent_id="agent-1", golden_set=golden, runner=_runner(), tenant_ids={"ankor": _ANKOR}
    )

    assert first == second
    assert [r.case_id for r in first] == ["c-answerable", "c-refusal"]  # thứ tự golden giữ nguyên


# ---------------------------------------------------------------------------
# 2. Điểm bất biến với metadata — chỗ loại nguồn flaky duy nhất
# ---------------------------------------------------------------------------


async def test_score_is_invariant_to_trace_metadata() -> None:
    """KHÓA D2: đổi `run_id`/`ts`/`event_id` của mọi event → **`citations_from_trace` VÀ điểm** không đổi.

    Đây là test quan trọng nhất trong file. Engine sinh `run_id = uuid4()` và `ts = now(UTC)`
    (`interpreter.py`), nên hai lượt chạy luồng THẬT **luôn** cho metadata khác nhau. Nếu bộ chấm đọc
    bất kỳ field nào trong số đó thì bảng điểm đổi giữa hai lượt và CI thành flaky — mà nguyên nhân
    lại không liên quan gì tới chất lượng câu trả lời, đúng thứ luật vàng cấm.

    **Assert đặt ở `citations_from_trace`, không chỉ ở `score_case`** — và đây là điểm quan trọng,
    tìm ra bằng mutation-check. `score_case(case, answer, retrieved_citations)` KHÔNG nhận `events`,
    nên nó *về mặt cấu trúc* không đọc được metadata: assert riêng ở đó là tautology, cấy bug vào
    helper vẫn xanh. `citations_from_trace(events)` là hàm **duy nhất** thấy cả `TraceEvent`, tức chỗ
    duy nhất metadata có thể lọt vào đường chấm. Khoá ở đó mới có răng.

    Cả hai vế đều đi qua helper (không truyền list hardcode làm baseline) để đường đi đối xứng —
    baseline hardcode chính là lỗi làm bản đầu của test này rỗng nghĩa.

    `TraceEvent` là `frozen=True` nên phải `model_copy(update=...)`, không gán tại chỗ được.
    """
    case = _answerable_case()
    run = CaseRun(
        answer=AgentAnswer(answer="Được nghỉ 12 ngày.", citations=[], refused=False),
        events=[_event(["ankor-leave-001#c1"]), _event([], node_type=NodeType.LLM_STEP)],
    )
    shifted = run.model_copy(
        update={
            "events": [
                event.model_copy(
                    update={
                        "event_id": f"{event.event_id}-khac",
                        "run_id": "run-hoan-toan-khac",
                        "ts": "2099-12-31T23:59:59+00:00",
                    }
                )
                for event in run.events
            ]
        }
    )

    # metadata ĐÃ đổi thật — không có 3 dòng này thì test tự lừa
    assert shifted.events[0].event_id != run.events[0].event_id
    assert shifted.events[0].run_id != run.events[0].run_id
    assert shifted.events[0].ts != run.events[0].ts

    assert citations_from_trace(shifted.events) == citations_from_trace(run.events)
    assert score_case(case, shifted.answer, citations_from_trace(shifted.events)) == score_case(
        case, run.answer, citations_from_trace(run.events)
    )


# ---------------------------------------------------------------------------
# 3. Điểm bất biến với thứ tự event
# ---------------------------------------------------------------------------


async def test_score_is_invariant_to_event_order() -> None:
    """KHÓA D3: đảo thứ tự `events` → `citation_accuracy` không đổi.

    `citations_from_trace` gom `.citations` vào một **list** (thứ tự giữ nguyên), nhưng `score_case`
    nhánh trả-lời-được so bằng `set(...)` và nhánh từ-chối bằng `all(...)` — cả hai độc lập thứ tự.
    Test này pin điều đó lại: nếu sau này ai đổi sang phép so phụ thuộc thứ tự (vd so list, hoặc lấy
    `[0]` làm "citation chính") thì điểm sẽ đổi theo thứ tự event mà DB/reader trả về — một nguồn
    flaky mới, và trace đọc từ Postgres KHÔNG bảo đảm cùng thứ tự với trace trong bộ nhớ.
    """
    case = _answerable_case()
    answer = AgentAnswer(answer="Được nghỉ 12 ngày.", citations=[], refused=False)
    cited = ["ankor-leave-001#c1", "ankor-leave-001#c2"]

    forward = score_case(case, answer, cited)
    reversed_ = score_case(case, answer, list(reversed(cited)))

    assert forward == reversed_
    assert forward.citation_accuracy == 1.0  # chunk kỳ vọng có mặt, bất kể ở đầu hay cuối


# ---------------------------------------------------------------------------
# 4. Negative control — chứng minh 3 test trên KHÔNG rỗng nghĩa
# ---------------------------------------------------------------------------


def test_equality_actually_discriminates() -> None:
    """KHÓA D4 (negative control): `SmokeResult.__eq__` phải PHÂN BIỆT được, không luôn-True.

    Ba test trên đều kết thúc bằng một phép `==`. Nếu `__eq__` bị hỏng — hoặc bị ai đó ghi đè thành
    so theo `case_id` — thì cả ba xanh vĩnh viễn mà không khoá gì cả. Một bộ test không bao giờ đỏ
    được là một bộ test chưa được kiểm chứng, nên chỗ này cấy lệch từng field một và đòi `!=`.

    Đi qua **mọi** field thay vì một field mẫu: `__eq__` so theo tập field, nên chỉ cần một field bị
    loại khỏi phép so là lệch ở field đó lọt qua im lặng — đúng loại lỗi mà "thử một field" bỏ sót.

    **Sửa D12:** chữ *"mọi field"* trước đây là một **danh sách gõ tay** — thêm field thứ 6
    (`expects_refusal`, DEC-D12-01) là nó hết đúng mà không bài nào đỏ. Đúng lớp lỗi bài này sinh ra
    để chặn, chỉ ở một tầng cao hơn: một bất biến phát biểu bằng lời mà không ai cưỡng chế. Nên bây
    giờ danh sách được **đối chiếu cơ khí** với `SmokeResult.model_fields`.
    """
    base = SmokeResult(
        case_id="c1", expected="12 ngày", actual="Được nghỉ 12 ngày.", success=True, citation_accuracy=1.0
    )
    perturbations: list[dict[str, object]] = [
        {"case_id": "c2"},
        {"expected": "99 ngày"},
        {"actual": "câu khác"},
        {"success": False},
        {"citation_accuracy": 0.0},
        {"expects_refusal": True},
    ]

    # Cưỡng chế chữ "mọi field": thêm field mới mà quên cấy lệch cho nó ⇒ bài này đỏ NGAY.
    perturbed_fields = {name for update in perturbations for name in update}
    assert perturbed_fields == set(SmokeResult.model_fields), (
        "danh sách cấy lệch không còn phủ đủ field của SmokeResult — "
        f"thiếu {set(SmokeResult.model_fields) - perturbed_fields}"
    )

    assert base == base.model_copy()  # bản sao y nguyên PHẢI bằng
    for update in perturbations:
        assert base != base.model_copy(update=update), f"__eq__ bỏ qua field {list(update)[0]!r}"


# ---------------------------------------------------------------------------
# 5. Determinism XUYÊN TIẾN TRÌNH — lớp bất định mà 4 test trên không thấy (D9)
# ---------------------------------------------------------------------------

# Kịch bản chạy trong tiến trình con. Để nguyên văn ở module-level thay vì nhúng vào f-string giữa
# thân test: payload này là thứ thật sự được chấm, nên nó phải đọc được khi review.
#
# Cố ý KHÔNG import helper của file này (`_event`, `_runner`, …): file test không phải module cài đặt
# được, và `sys.path` hack sẽ làm bài test phụ thuộc layout thư mục. Dựng lại kịch bản tối thiểu ngay
# trong payload — nó chỉ cần đi qua `run_smoke` → `score_case` → `citations_from_trace`, không cần
# trùng khít với các test trên.
_SUBPROCESS_PAYLOAD = """
import asyncio, hashlib, json
from uuid import NAMESPACE_DNS, uuid5
from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.harness import EvalHarness, citations_from_trace

ANKOR = uuid5(NAMESPACE_DNS, "ankor")

def event(citations):
    return TraceEvent(
        event_id="e1", run_id="r1", agent_id="agent-1", tenant_id=ANKOR, node_id="n1",
        node_type=NodeType.KB_RETRIEVE, ts="2026-07-30T00:00:00+00:00", inputs_hash="h",
        outputs={}, tokens=Tokens(prompt=0, completion=0), cost=0.0, citations=citations,
    )

# Nhiều citation trên MỘT event, và nhiều case: nếu bộ chấm gom citation qua `set` rồi trả theo thứ tự
# iteration thì thứ tự đó đổi theo PYTHONHASHSEED, và hash dưới sẽ lệch giữa hai lượt.
CITES = ["ankor-leave-001#c1", "ankor-leave-002#c1", "ankor-policy-007#c3", "ankor-hr-011#c2"]

golden = GoldenSet(golden_set_ref="gs-xproc", cases=[
    GoldenCase(case_id="c-answerable", query="q-answerable", tenant="ankor",
               section_roles=["employee", "public", "finance"], expected_tenant="ankor",
               expected_section_role="employee", expected="12 ngay",
               expected_citation=CITES),
    GoldenCase(case_id="c-refusal", query="q-refusal", tenant="ankor",
               section_roles=["employee"], expected_tenant="borea",
               expected_section_role="public", expected="refusal", expected_citation=[]),
])

runner = StubAgentRunner({
    ("q-answerable", ANKOR, ("employee", "public", "finance")): CaseRun(
        answer=AgentAnswer(answer="Duoc nghi 12 ngay.", citations=[], refused=False),
        events=[event(CITES)],
    ),
    ("q-refusal", ANKOR, ("employee",)): CaseRun(
        answer=AgentAnswer(answer="Khong co thong tin.", citations=[], refused=True),
        events=[event(["carib-x-001#c1"])],
    ),
})

results = asyncio.run(EvalHarness().run_smoke(
    agent_id="agent-1", golden_set=golden, runner=runner, tenant_ids={"ankor": ANKOR}))

# Hai nửa, và nửa thứ hai là nửa bắt buộc:
#
# `scores` — `SmokeResult` có ĐÚNG 5 field vô hướng (case_id/expected/actual/success/
# citation_accuracy), KHÔNG mang danh sách citation. Nên riêng nó chỉ bắt được thứ tự phần tử của
# `list[SmokeResult]` (tức thứ tự `run_smoke` duyệt case) và giá trị vô hướng.
#
# `citations` — thứ tự do `citations_from_trace` trả về. Phải hash riêng vì nó KHÔNG chảy vào
# `SmokeResult`: nó chỉ vào `citation_accuracy`, mà đó là phép ĐẾM giao tập nên bất biến với thứ tự.
# Không có nửa này thì một hiện thực gom citation qua `set` sẽ đi qua sạch — đã đo bằng mutation.
# Gọi `runner.run_case` trực tiếp vì `run_smoke` chỉ trả `SmokeResult`, không trả `CaseRun`.
cites = []
for c in golden.cases:
    cr = asyncio.run(runner.run_case(
        agent_id="agent-1", query=c.query, tenant_id=ANKOR, section_roles=list(c.section_roles)))
    cites.append(citations_from_trace(cr.events))

# `sort_keys=True` chuẩn hoá thứ tự KHOÁ của dict (thứ tự field pydantic là tất định theo khai báo,
# không theo hash) — nhưng KHÔNG sắp lại phần tử trong list. Đó là chủ đích: thứ tự list mới là chỗ
# bất định-theo-hash lộ ra, nên nó phải được giữ nguyên để hash bắt được.
payload = {"scores": [r.model_dump(mode="json") for r in results], "citations": cites}
blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
print(hashlib.sha256(blob.encode()).hexdigest())
"""


def _score_hash_in_subprocess(hash_seed: str) -> str:
    """Chạy `_SUBPROCESS_PAYLOAD` trong một tiến trình Python MỚI với `PYTHONHASHSEED=hash_seed`,
    trả hash sha256 của bảng điểm.

    `sys.executable` là interpreter của venv hiện tại nên `studio_evalhub` import được không cần
    `PYTHONPATH`. `check=True` để lỗi trong tiến trình con nổi lên thành đỏ chứ không thành hash rỗng —
    một bài so hai chuỗi rỗng sẽ luôn xanh."""
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", _SUBPROCESS_PAYLOAD],
        env={**os.environ, "PYTHONHASHSEED": hash_seed},
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def test_bang_diem_bat_bien_qua_pythonhashseed() -> None:
    """KHÓA D5: hai TIẾN TRÌNH khác nhau, `PYTHONHASHSEED` khác nhau ⇒ bảng điểm cùng một hash.

    Lớp bất định mà 4 test trên không thấy: `test_run_smoke_twice_yields_identical_results` chạy hai
    lượt trong **cùng một** process, nên `PYTHONHASHSEED` của hai lượt bằng nhau và mọi thứ tự phụ thuộc
    hash sẽ giống nhau ở cả hai — test xanh trong khi lượt chạy CI kế tiếp lại ra số khác.

    Python randomize hash của `str` theo từng process (PEP 456), nên thứ tự iteration của `set`/`dict`
    khoá-chuỗi đổi giữa các lần chạy. Bộ chấm hiện tại có `set` ở `score_case`:
    `len(expected & set(retrieved)) / len(expected)`. Phép đó chỉ ĐẾM nên bất biến với thứ tự — nhưng
    "an toàn vì hiện thực hôm nay đếm" khác với "được khoá".

    ## Payload hash hai nửa, và nửa thứ hai là nửa bắt buộc

    `SmokeResult` có đúng **5 field vô hướng**, KHÔNG mang danh sách citation. Nên hash chỉ trên bảng
    điểm **về mặt cấu trúc không thể** thấy thứ tự `citations_from_trace`: thứ tự đó chỉ chảy vào
    `citation_accuracy`, mà đó là phép đếm. Đo rồi: gieo `citations_from_trace` trả `list(set(...))` thì
    một payload chỉ-bảng-điểm đi qua **sạch**.

    Vì thế payload gồm cả `citations` lấy trực tiếp từ `runner.run_case` → `citations_from_trace`. Hai
    nửa phủ hai lớp khác nhau:

    | nửa | bắt được |
    |---|---|
    | `scores` | thứ tự phần tử `list[SmokeResult]` (tức thứ tự `run_smoke` duyệt case) + giá trị vô hướng |
    | `citations` | thứ tự phần tử của `citations_from_trace` |

    Payload dùng **4 citation trên một event** và `section_roles` ba phần tử để một hiện thực
    set-iteration có chỗ mà lệch. Một case với một citation sẽ không phân biệt được.

    Vì sao so hash chứ không so object: hai tiến trình khác nhau không chia sẻ object được, nên phải qua
    một dạng tuần tự hoá. Hash là dạng gọn nhất mà vẫn nhạy với mọi ký tự.
    """
    first = _score_hash_in_subprocess("1")
    second = _score_hash_in_subprocess("424242")

    assert first, "tiến trình con không in ra hash — kịch bản chạy lỗi"
    assert len(first) == 64, f"hash không phải sha256 hex: {first!r}"
    assert first == second, "bảng điểm đổi theo PYTHONHASHSEED — có iteration thứ-tự-phụ-thuộc trong đường chấm điểm"
