"""Bộ chấm đọc trace của một run **THẬT** đã bền hoá — AIE-2, D15 (`kit#103`, dòng 🎯).

## Khoảng trống mà file này lấp

`score_case` cần hai thứ: `retrieved_citations` và một `AgentAnswer`. Vế thứ nhất đã đọc từ trace
kể từ D5 (`citations_from_trace`). Vế thứ hai thì **luôn đến từ RAM** — `CaseRun.answer` do runner
trả về trong cùng tiến trình. Kể cả `apps/studio/tests/test_spine_scored_from_postgres.py` (D7),
bài đọc trace từ Postgres, vẫn lấy `case_run.answer` từ bộ nhớ:

    engine → PgTraceWriter → obs.trace_events → đọc lại → citations   ✅ D5/D7
                                              → đọc lại → answer      ❌ file NÀY

Một bộ chấm còn phải giữ object trong RAM thì không đọc được run của người khác, không đọc lại được
run hôm qua, và không nối được vào playground `#102` (nơi run xảy ra ở tiến trình khác). Đó là lý do
`answer_from_trace` tồn tại.

## Vì sao đọc `obs.trace_events` bằng SQL thô thay vì mượn `studio_kb.trace_reader`

`.importlinter` xếp 4 quadrant là **sibling** ⇒ `studio_evalhub` **KHÔNG** import được `studio_kb`.
Đây là **cùng tình thế** mà `studio_kb/trace_reader.py` đã ghi và đã giải bằng cùng cách: nó đọc một
bảng do `studio_app` sở hữu, cũng không import được `studio_app`, nên nó đọc bằng SQL thô và nhận
`pool` qua constructor. Ở đây chép đúng khuôn đó — không phát minh lại, và cũng không phá layering
để cho tiện (`make lint` sẽ bắt, nhưng quan trọng hơn: nó xoá đúng ranh giới ownership mà cả Sprint 2
đang được chấm).

## Cái file này KHÔNG làm

Không gọi `compute_scorecard` (mốc D16, `kit#108` — còn `NotImplementedError`), không dựng
`Scorecard`, không quyết `gate`. Nó chấm per-case và giao cho `render_run_cases` in ra `k/n` thô.
Land `compute_scorecard` sớm sẽ làm `test_gate_blocks_on_fail` (`xfail(strict=True)`) XPASS ⇒ FAIL.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from studio_contracts import NodeType, Tokens, TraceEvent

from studio_evalhub.agent_runner import AgentAnswer
from studio_evalhub.cli import _demo_golden_set
from studio_evalhub.golden_case import GoldenCase
from studio_evalhub.harness import SmokeResult, chunks_from_trace, citations_from_trace, score_case
from studio_evalhub.render import render_run_cases

Pool = AsyncConnectionPool[AsyncConnection[Any]]

TRACE_SOURCE_POSTGRES = "obs.trace_events (Postgres — trace đã bền hoá qua PgTraceWriter)"
"""Nhãn `trace_source` cho đường đọc-lại-từ-DB.

Nhãn này không phải trang trí: cùng một `run_id` đọc từ RAM và đọc từ Postgres là **hai phép đo
khác nhau** (JSONB serialize, `numeric` cho `cost`, `text` cho `ts`, thứ tự row do `ORDER BY` quyết).
D14 đã trả giá một lần vì trộn *static fixed-set* với *current PG measurement* trong cùng một câu."""


class TraceAnswerError(ValueError):
    """Không dựng lại được `AgentAnswer` từ trace.

    Có kiểu riêng thay vì `ValueError` trần để test khẳng định được **đúng lý do vỡ** — một bài
    `pytest.raises(ValueError)` sẽ xanh cả khi hàm vỡ vì lý do khác hoàn toàn. Cùng khuôn với
    `TraceTimestampError`/`RecipeWalkError` của `studio_kb.trace_reader`.
    """


def answer_from_trace(events: list[TraceEvent]) -> AgentAnswer:
    """Dựng lại `AgentAnswer` từ event `llm-step` của một run **đã bền hoá**.

    Nguồn là `TraceEvent.outputs` của node `llm-step` — đúng cái mà `EngineAgentRunner._llm_answer`
    (`apps/studio/src/studio_app/eval_adapter.py:37`) đọc từ `RunResult.final_state`, chỉ khác là ở
    đây nó được đọc **sau khi đã đi qua Postgres**. Interpreter đổ nguyên `raw_outputs` của executor
    vào `TraceEvent.outputs` (`interpreter.py:366-371`), nên `answer`/`refused`/`citations` sống sót
    round-trip.

    **Fail-closed ở mọi nhánh không chứng minh được** — raise, không đoán:

    | tình huống | vì sao raise |
    |---|---|
    | `events` rỗng | không có trace thì không có gì để chấm; trả answer rỗng là biến *chưa đo* thành *đã đo và trượt* |
    | không có `llm-step` | run không đi qua bước LLM ⇒ không có câu trả lời nào để so |
    | thiếu key `answer` | node đúng nhưng payload thiếu — lý do vỡ khác hẳn, phải phân biệt được lúc gỡ lỗi |
    | thiếu key `refused` | **thêm D15 sau finding B2** — xem khối dưới bảng |
    | **nhiều** `llm-step` | *"câu trả lời của run"* lúc đó phải do hợp đồng nói, không do thứ tự dòng nói |

    Nhánh cuối là nhánh đắt nhất. `#102` cho người dùng dựng recipe tự do, nên recipe nhiều bước LLM
    là chuyện sẽ tới. Chọn im lặng cái đầu hay cái cuối sẽ cho ra một bảng điểm trông vẫn đúng trong
    khi nó đang chấm nhầm bước — đúng lớp lỗi breakpoint `#14` (suy một giá trị ngữ nghĩa im lặng rồi
    chấm như thể đã đo).

    **Nhánh `refused` là finding của người ngoài, không phải của tôi.** @DongAnh2704 gieo mutation
    chéo T7 (`kb#17`, `kit#74`) và tìm ra: bản đầu dùng `outputs.get("refused", False)`, đổi default
    `False → True` thì **toàn suite vẫn xanh**. Một nhánh có docstring mà 0 lớp test — mọi fixture
    đều set `refused` tường minh nên nhánh mặc định chưa từng chạy lần nào.

    Vá theo hướng **raise** thay vì ghim `False`, vì mặc định `False` không phải lựa chọn an toàn mà
    là lựa chọn **đo sai**: một ca đáng là *từ-chối* nhưng thiếu key sẽ bị đẩy sang nhánh trả-lời rồi
    báo FAIL — bảng điểm nói *agent trả lời sai* trong khi sự thật là *trace không đọc được*. Producer
    thật luôn ghi key này (`engine:executors.py:265` — `"refused": not citations`), nên thiếu nó là
    trace dị dạng chứ không phải ca vận hành bình thường.

    **Giới hạn có ghi — `refused` chưa freeze semantic** (Breakpoint `#14`, xác nhận lại ở D14/B7).
    Ở đây nó được dùng đúng nghĩa **carrier**: đọc lại giá trị mà producer đã ghi. Nó KHÔNG phải một
    oracle độc lập khẳng định run này thật sự an toàn — luật hiện hành vẫn là `refused = not
    citations`, một tín hiệu cấu trúc do producer định nghĩa. Leak-check thật nằm ở `score_case`
    nhánh từ-chối, chấm trên citation TRACE chứ không trên cờ này.

    Hàm **thuần**: không đụng `events` cũng không đụng `outputs` bên trong. Một hàm `pop` key ra để
    đọc sẽ làm rỗng trace của caller, và `citations_from_trace` gọi sau sẽ thấy một trace khác trace
    nó được đưa.
    """
    if not events:
        raise TraceAnswerError("trace rỗng — không có event nào để dựng lại AgentAnswer")

    llm_steps = [e for e in events if e.node_type is NodeType.LLM_STEP]
    if not llm_steps:
        seen = ", ".join(sorted({e.node_type.value for e in events}))
        raise TraceAnswerError(f"trace không có event `llm-step` (chỉ thấy: {seen}) — không có câu trả lời để chấm")
    if len(llm_steps) > 1:
        raise TraceAnswerError(
            f"trace có {len(llm_steps)} event `llm-step` — không suy ra được đâu là câu trả lời của run. "
            "Chọn bừa một bước sẽ cho ra bảng điểm trông đúng mà chấm nhầm bước; hợp đồng phải nói "
            "trước bước nào là câu trả lời cuối."
        )

    outputs = llm_steps[0].outputs
    if "answer" not in outputs:
        raise TraceAnswerError(
            f"event `llm-step` không có key `answer` trong outputs (có: {sorted(outputs)}) — "
            "node đúng nhưng payload thiếu"
        )

    if "refused" not in outputs:
        raise TraceAnswerError(
            f"event `llm-step` không có key `refused` trong outputs (có: {sorted(outputs)}) — "
            "không đoán. Mặc định `False` sẽ đẩy một ca đáng là từ-chối sang nhánh trả-lời và báo "
            "FAIL, tức bảng điểm nói agent trả lời sai trong khi trace mới là thứ không đọc được."
        )

    raw_citations = outputs.get("citations")
    return AgentAnswer(
        answer=str(outputs["answer"]),
        citations=[str(c) for c in raw_citations] if isinstance(raw_citations, list) else [],
        refused=bool(outputs["refused"]),
    )


def score_run_from_trace(
    case: GoldenCase,
    events: list[TraceEvent],
    *,
    tenant_ids: Mapping[str, UUID] | None = None,
) -> SmokeResult:
    """Chấm một case **hoàn toàn** từ trace đã bền hoá: cả `answer` lẫn `citations` đọc từ `events`.

    Đây là chỗ hai vế gặp nhau. `citations_from_trace` (D5) lo vế citation; `answer_from_trace` (hôm
    nay) lo vế câu trả lời. Sau hàm này, không còn mảnh nào của phép chấm phụ thuộc RAM của tiến
    trình đã chạy agent — bảng điểm dựng lại được từ `run_id` và không gì khác.

    ## `tenant_ids` — additive, default `None` (D18/T5)

    Trả nợ ghi trong bảng D17: hàm này là **một trong 6 call-site còn đi đường `citations` vacuous**
    sau `F-6`, và là món nặng nhất — vì `workbench/dev_playground_server.py:189` gọi nó, nên **số
    hiển thị trên Playground chưa hưởng bản vá**. Nêu bởi SWE ở review `evalhub#18`.

    - **không truyền** ⇒ `no_leak` chấm trên `retrieved_citations` — đường CŨ, y nguyên. Đang dùng:
      `dev_playground_server.py:189` (gọi 2 tham số vị trí) và `run_report` CLI.
    - **truyền** ⇒ chấm trên `outputs["chunks"]` qua `chunks_from_trace`: tenant so bằng **UUID
      thật**, vai so bằng **`section_role` thật**. Caller chọn opt-in.

    **Keyword-only + default `None` là hình duy nhất giữ được tương thích**: đây là API công khai có
    consumer **ngoài quadrant**, nên đổi hành vi mặc định là phá hợp đồng của người khác mà họ không
    chọn. Luật này ghi sẵn ở chính bảng nợ (*"phải additive + báo trước SWE"*), không phải phép lịch sự.

    **Vì sao đường cũ vacuous, và vì sao vẫn giữ:** case từ-chối trên runner thật gần như luôn phát
    **0 citation**, nên `all(...)` chạy trên tập rỗng ⇒ `no_leak` luôn `True` ⇒ luật đúng và luật sai
    cho **cùng một kết quả**. Đo trên golden-30 ở D17: 8/8 case từ-chối. Giữ nó không phải vì nó đúng
    — mà vì đổi mặc định của một API công khai là việc của **caller**, không phải của hàm này.

    `tenant_ids` **bắt buộc đi cùng** đường chunks chứ không phải một cờ bật/tắt: `_no_leak_from_chunks`
    so tenant bằng UUID thật, nên thiếu bảng ánh xạ slug→UUID thì không có gì để so. Gộp hai thứ vào
    một tham số làm chỗ này không thể dùng sai.

    **Map thiếu tenant của case ⇒ `ValueError` nêu tên, không để `KeyError` trần lọt.** Trước bản vá
    này, `tenant_ids` thiếu key sẽ ném `KeyError: '<tenant>'` từ `harness.py:268` — **khác kiểu** với
    thứ `score_case` hứa (*"Đòi `tenant_ids`; thiếu ⇒ `ValueError`"*), và mang đúng một chuỗi tenant
    không nói được gì về việc phải làm. Cạnh sắc đó vốn có sẵn ở đường harness, nhưng T5 là chỗ **đưa
    nó ra một API công khai có consumer ngoài quadrant**, nên chặn ở đây trước khi mời ai opt-in.

    Chỉ đòi `case.tenant`. `expected_tenant` **cố ý không** bị đòi: với case T1 nó đúng là kho caller
    **không có quyền**, nên nó không nằm trong `tenant_ids` của run (`harness.py:259-263`) — đòi nó sẽ
    làm mọi case T1 đỏ.
    """
    answer = answer_from_trace(events)
    citations = citations_from_trace(events)
    if tenant_ids is None:
        return score_case(case, answer, citations)
    if case.tenant not in tenant_ids:
        raise ValueError(
            f"`tenant_ids` thiếu tenant của case {case.case_id!r}: {case.tenant!r} không có trong "
            f"{sorted(tenant_ids)}. Đường chunks so tenant bằng UUID thật nên thiếu UUID là không so "
            "được — dựng lại map cho đủ tenant của case."
        )
    return score_case(
        case,
        answer,
        citations,
        retrieved_chunks=chunks_from_trace(events),
        tenant_ids=tenant_ids,
    )


_COST_ROUND_NDIGITS = 6
"""Số chữ số thập phân của luật cộng cost — **hằng số dùng chung với `kb`, không có cơ chế cưỡng chế**.

Nguồn đối chiếu: `kb/src/studio_kb/cost.py` — `aggregate_run_cost` cộng
`round(sum(e.cost for e in events), 6)`. Hai repo **không import được nhau** (`.importlinter` xếp
`studio_kb | studio_engine | studio_workbench | studio_evalhub` cùng một layer), nên thứ duy nhất
giữ hai bên khớp là **cùng luật + cùng tên field**, và không lint/type/test nào bắt được ngày `kb`
đổi `6` thành `8`.

Rằng chuyện đó có hậu quả thật thì đo được, không phải lo xa:

    sum([0.000291, 0.001578, 0.010125, 0, 0, 0])  = 0.011994000000000001   ← không làm tròn
    round(..., 6)                                 = 0.011994
                                          bằng nhau?  False

Cưỡng chế được đến đâu thì cưỡng chế đến đó: `test_conformance_luat_cong_round_6` ghim bảng
`(per-event cost) → tổng kỳ vọng` bằng **số viết tay**, không tính bằng chính hàm đang test — số kỳ
vọng đến từ **ngoài** cài đặt nên bài đó tautology-proof. Cùng bộ số được dán sang review `kb#22` để
ghim đối xứng.

**Điều kiện đóng nợ:** ngày `cost_of` land ở `contracts` (Q-A), luật cộng đi cùng nó và cả hai bản
mirror bỏ được (`DEC-D19-03`)."""


class RunCostError(ValueError):
    """Không cộng dồn được `cost` của một run.

    Có kiểu riêng thay vì `ValueError` trần để test khẳng định được **đúng lý do vỡ** — cùng khuôn
    `TraceAnswerError` ở trên, và cùng lý lẽ: một bài `pytest.raises(ValueError)` sẽ xanh cả khi hàm
    vỡ vì lý do khác hoàn toàn.
    """


@dataclass(frozen=True, slots=True)
class RunCost:
    """Cost mức **RUN**, đọc từ trace đã bền hoá — `DEC-D19-02`.

    ## Vì sao ở đây mà không phải trên `SmokeResult` hay `contracts`

    - **Cost là sự thật mức RUN, `SmokeResult` là mức CASE.** Nhét một số run-level vào mỗi dòng case
      là nhân bản cùng một số n lần rồi mời người đọc cộng lại — đúng lớp lỗi `DEC-D15-01` mô tả
      (*"một renderer tự tính là một nguồn số thứ hai cho cùng một run"*). Lưới `RUN_CASE_COLUMNS` +
      `RUN_CASE_FIELDS_NOT_SHOWN` (`render.py:50-53`, ghim ở `test_render_run_cases.py:350`) sẽ đỏ
      ngay nếu ai thêm field — và lưới đó **đang làm đúng việc của nó**.
    - **`contracts` là nơi ra verdict.** Đặt một trục đang bằng `0.0` cạnh `gate.verdict` là dựng sẵn
      chỗ cho ai đó gate lên nó; một gate trên hằng số 0 sẽ **PASS mọi thứ** cho tới ngày emit nối
      giá rồi **FAIL mọi thứ** ngay hôm sau.

    ## Tên field khớp `RunCost` của `kb#22` là CÓ CHỦ ĐÍCH

    `run_id` · `tenant_id` · `prompt_tokens` · `completion_tokens` · `cost` · `event_count` — hai
    bên không import được nhau, nên thứ duy nhất giữ chúng đối chiếu được khi review chéo là **tên +
    luật giống hệt**. Lệch tên là lệch âm thầm.
    """

    run_id: str
    tenant_id: UUID
    prompt_tokens: int
    completion_tokens: int
    cost: float
    event_count: int
    priced: bool


def run_cost_from_trace(events: list[TraceEvent]) -> RunCost:
    """Cộng dồn `cost` **đã lưu** của một run — `DEC-D19-01`.

    ## "Không tự tính lại" nghĩa là gì, chốt một cách đọc

    Cấm mọi biểu thức suy `cost` từ `tokens × đơn giá`. **Cộng dồn `cost` đã lưu KHÔNG phải "tính
    lại"** — nó là phép đọc trên nhiều dòng, cùng hình với `citations_from_trace` đọc nhiều event.

    Phải chốt vì câu *"đọc cost từ trace, không tự tính lại"* (`kit#123`) có **hai** cách đọc, và
    cách thứ hai (*"không tự tính = phải gọi bộ cộng dồn của DE"*, đúng nguyên văn `F-7` của `kb#22`)
    dẫn tới ngõ cụt: `.importlinter` cấm import chéo quadrant, nên hoặc phá layering, hoặc ô DoD
    không đóng được.

    Cũng cấm luôn nhánh "tiện tay": không đọc `cost` từ `AgentAnswer`, không nhận `cost` qua tham số
    của caller, không cache một `cost` từ lần chạy trước. Nguồn là `events`, và chỉ `events`.

    ## Fail-closed ở mọi nhánh không chứng minh được — raise, không đoán

    - `events` rỗng ⇒ không có run nào để nói về;
    - trộn `run_id` ⇒ "cost của run này" mất nghĩa;
    - trộn `tenant_id` ⇒ hở `INV-1`. `obs.trace_events` nay CÓ RLS ở tầng DB (GAP-1, `app#40`),
      nhưng hàm này là hàm **thuần** — nó nhận `list[TraceEvent]` đã đọc sẵn trong RAM, trong đó có
      đường `read_run_unscoped` cố ý đọc xuyên tenant để `tenant_scope_ok` bắt được run trộn. RLS ở
      tầng DB không với tới đây, nên lưới của hàm thuần vẫn là lưới **duy nhất** cho đầu vào này;
      một tổng trộn tenant là một con số của tenant này rò sang tenant kia.

    ## `priced` trả lời ĐÚNG MỘT CÂU: *"cost của run này đã được đo chưa"*

    Hai trạng thái của số 0 phải phân biệt được, và phân loại bằng **`tokens`**, không bằng riêng
    `cost` (`DEC-D19-05`):

    | `priced` | Điều kiện | Đọc là |
    |---|---|---|
    | `False` | `Σtokens > 0` **và** `Σcost == 0` | **chưa nối giá** — có việc đã chạy nhưng chưa ai áp đơn giá |
    | `True` | mọi trường hợp còn lại | **đã đo** — *kể cả khi bằng `0`* (`Σtokens == 0` là đo thật bằng không) |

    Đây là trạng thái của **mọi run trong hệ thống hôm nay**: `interpreter.py:73` `_NO_COST = 0.0`,
    `:438` `cost=_NO_COST`. In `0.000000` trần sẽ đọc thành *"chạy 30 case tốn 0 đồng"*; in *"chưa
    đo"* vô điều kiện (cách `TraceViewer.tsx:50` đang làm) thì tới ngày emit nối giá, node
    `kb-retrieve` với `Tokens(0, 0)` — một **phép đo thật bằng 0** — bị gán nhãn *chưa đo*. Chỉ cách
    phân loại theo `tokens` mới đúng ở **cả hai** ngày.

    `priced` **không** gánh thêm nghĩa *"số này có nhất quán với luật giá không"*. Đó là câu hỏi về
    **từng event**, cần đơn giá để trả lời, và `DEC-D19-01` cấm đơn giá sống trong `studio_evalhub`
    ⇒ nó thuộc `price_mismatches` phía DE (`E-8`, điều kiện lật: Q-A).
    """
    if not events:
        raise RunCostError(
            "`events` rỗng — không có run nào để cộng cost. Trả `RunCost(cost=0)` ở đây sẽ dựng một "
            "con số trông như phép đo trong khi thật ra là *không có gì để đo*, đúng lớp lỗi `F-6` "
            "(`no_leak` trên tập rỗng, D17)."
        )

    run_ids = sorted({e.run_id for e in events})
    if len(run_ids) > 1:
        raise RunCostError(
            f"trộn run_id trong cùng một lần cộng: {run_ids}. `RunCost` là cost **của một run**; "
            "cộng chéo run thì con số không trả lời được câu hỏi nào."
        )

    tenants = sorted({e.tenant_id for e in events}, key=str)
    if len(tenants) > 1:
        raise RunCostError(
            f"trộn tenant_id trong cùng một run: {[str(t) for t in tenants]}. RLS ở tầng DB "
            "(GAP-1) không với tới hàm thuần này — nó chấm trên event đã đọc sẵn, kể cả qua "
            "`read_run_unscoped` (cố ý xuyên tenant), nên `tenant_id` trên từng event là hàng rào "
            "duy nhất còn lại ở đây (`INV-1`) — một tổng trộn tenant là số của tenant này rò sang "
            "tenant kia, dưới dạng một con số trông bình thường."
        )

    tong_cost = round(sum(e.cost for e in events), _COST_ROUND_NDIGITS)
    prompt_tokens = sum(e.tokens.prompt for e in events)
    completion_tokens = sum(e.tokens.completion for e in events)

    # `priced` phân loại bằng TOKENS, không bằng riêng `cost` — chỉ cách này đúng ở CẢ HAI ngày:
    # hôm nay (emit chưa áp giá ⇒ tokens>0, cost=0 ⇒ *chưa nối giá*) và ngày emit nối giá
    # (`kb-retrieve` phát `Tokens(0,0)` ⇒ cost đúng bằng 0 ⇒ *đã đo, bằng 0*).
    priced = not (tong_cost == 0 and prompt_tokens + completion_tokens > 0)

    return RunCost(
        run_id=run_ids[0],
        tenant_id=tenants[0],
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost=tong_cost,
        event_count=len(events),
        priced=priced,
    )


class UnscopedReadUnavailable(RuntimeError):
    """Đường đọc-xuyên-tenant không đáng tin trên connection này — raise thay vì trả rỗng.

    Fail-closed cùng họ với `RunCostError`/`TraceAnswerError`: nhánh không chứng minh được thì
    raise, không đoán. Khác ở chỗ hai lớp kia nói về *dữ liệu*, lớp này nói về *quyền đọc* — và đó
    đúng là chỗ trước đây bị nhập nhằng, xem `_assert_doc_xuyen_tenant_duoc`."""


# `row_security_active(regclass)` là built-in Postgres trả lời đúng câu cần hỏi — "RLS có đang áp
# lên CHÍNH role của connection này không" — và nó gộp sẵn cả 4 biến số: bảng đã `ENABLE` chưa, có
# `FORCE` không, role có phải owner không, role có `BYPASSRLS`/superuser không. Tự tra
# `pg_class`/`pg_roles` rồi ghép tay là dựng lại một bản sao kém hơn của hàm này.
#
# `to_regclass(...) IS NULL` bọc ngoài: `row_security_active` RAISE nếu bảng chưa tồn tại, mà "chưa
# chạy `ensure_all_schemas()`" không phải chuyện của guard này — để câu SELECT thật bên dưới báo
# `relation does not exist` như thường lệ, đừng đổi nó thành một lỗi về quyền.
_ROW_SECURITY_ACTIVE = """
SELECT CASE
           WHEN to_regclass('obs.trace_events') IS NULL THEN false
           ELSE row_security_active('obs.trace_events')
       END
"""


async def _assert_doc_xuyen_tenant_duoc(conn: AsyncConnection[Any], ten_ham: str) -> None:
    """Chặn trước khi SELECT: RLS đang áp lên role này ⇒ đường đọc-xuyên-tenant vô nghĩa.

    **Vì sao phải raise chứ không trả rỗng** (`evalhub#37`, GAP-1 / `app#40`). Policy của
    `obs.trace_events` là `tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid`.
    Hai hàm dưới đây CỐ Ý không set `app.tenant_id` — đọc xuyên tenant là việc của chúng. Dưới
    policy đó `current_setting(..., true)` trả `NULL`, phép so trả `NULL`, và **mọi** dòng bị lọc:
    câu SELECT thành công, trả `[]`, không một cảnh báo nào.

    Cái `[]` đó là chế độ hỏng tệ nhất có thể, vì nó không phân biệt được với câu trả lời hợp lệ
    *"bảng chưa có run nào"*. Đi thêm một bước thì `run_cost_from_trace` biến nó thành
    `RunCostError("events rỗng")` — đúng ngữ pháp, sai nguyên nhân, đẩy người đọc đi tìm ở phía dữ
    liệu trong khi lỗi nằm ở phía quyền.

    **Vì sao không sửa bằng cách set `app.tenant_id` rồi lặp từng tenant.** `read_run_unscoped` tồn
    tại để `tenant_scope_ok` (`harness.py:187`) bắt được run mà node đầu mang `ankor` còn node sau
    mang `borea`. Lọc theo một tenant khiến RLS giấu đi **đúng những event lạ mà phép kiểm đó đi
    tìm** ⇒ `tenant_scope_ok` trả `True` cho một run hỏng thật. Đó là hồi quy bảo mật, không phải
    bản vá — nên hàm phải đọc được mọi dòng, hoặc phải từ chối trả lời. Guard này là vế thứ hai.

    Vế thứ nhất (một role Postgres riêng có `BYPASSRLS` cho bộ chấm) chạm `docker/postgres-init` +
    `docker-compose*.yml` ở repo kit và `grant_app_privileges()` ở `apps/studio` — ngoài package
    này, PR riêng. Cho tới lúc đó, guard này biến một lỗi im lặng thành một lỗi kêu to, và câu lỗi
    nói thẳng cần làm gì.
    """
    cursor = await conn.execute(_ROW_SECURITY_ACTIVE)
    row = await cursor.fetchone()
    if row is None or not row[0]:
        return
    raise UnscopedReadUnavailable(
        f"`{ten_ham}` đọc `obs.trace_events` KHÔNG lọc tenant, nhưng RLS đang áp lên role hiện tại "
        "⇒ mọi dòng bị policy lọc và hàm sẽ trả rỗng IM LẶNG, không phân biệt được với `bảng chưa "
        "có run nào`. Từ chối trả lời thay vì trả một câu sai (`evalhub#37`, GAP-1 / `app#40`). "
        "Cách chạy được: dùng DSN của một role có `BYPASSRLS` cho bộ chấm. KHÔNG vá bằng cách set "
        "`app.tenant_id` rồi lặp từng tenant — làm vậy RLS sẽ giấu đúng những event lạ mà "
        "`tenant_scope_ok` đi tìm, biến phép kiểm trộn-tenant thành vô nghĩa."
    )


_READ_RUN = """
SELECT event_id, run_id, agent_id, tenant_id, node_id, node_type, ts,
       inputs_hash, outputs, tokens, cost, citations
FROM obs.trace_events
WHERE run_id = %s
ORDER BY ts, event_id
"""

_LIST_RUNS = """
SELECT run_id, count(*) AS n
FROM obs.trace_events
GROUP BY run_id
ORDER BY min(ts)
"""


def _row_to_event(row: tuple[Any, ...]) -> TraceEvent:
    """Dựng `TraceEvent` từ một dòng `obs.trace_events`, đúng thứ tự cột của `_READ_RUN`.

    `cost` là `NUMERIC` ⇒ psycopg trả `Decimal`. Lời gọi `float(...)` là **lớp phòng hờ, không phải
    lớp duy nhất**: `TraceEvent.cost: float` với `model_config` không strict ⇒ pydantic lax mode đã
    tự ép `Decimal → float` rồi. Đo được bằng mutation R5 (`docs/mutations/self-render-d15.md` §5.2):
    bỏ `float()` đi thì **không bài nào đỏ**. Giữ lại vì nó là lưới cho ngày ai đó bật `strict=True`,
    nhưng đừng đọc dòng này như thứ đang giữ bất biến — pydantic đang giữ.

    `citations` `NULL` giữ nguyên `None` chứ không đổi thành `[]`: *"chưa có trích dẫn nào"* và
    *"không áp dụng"* là hai chuyện khác nhau, và `citations_from_trace` phân biệt hai cái đó.
    Cái này thì **có** lưới — mutation R3 đỏ ngay."""
    return TraceEvent(
        event_id=row[0],
        run_id=row[1],
        agent_id=row[2],
        tenant_id=row[3],
        node_id=row[4],
        node_type=NodeType(row[5]),
        ts=row[6],
        inputs_hash=row[7],
        outputs=row[8],
        tokens=Tokens(**row[9]),
        cost=float(row[10]),
        citations=row[11],
    )


async def read_run_unscoped(pool: Pool, run_id: str) -> list[TraceEvent]:
    """Mọi event của `run_id`, xếp theo `(ts, event_id)` như `studio_kb.trace_reader` làm.

    Khác `PgTraceReader.read_run`, hàm này **không** lọc `tenant_id`: nó là công cụ **đọc lại một run
    đã biết id** ở phía bộ chấm, không phải một API phục vụ request của tenant. Bù lại, tenant vẫn
    được kiểm — `tenant_scope_ok(events, expected)` (`harness.py:105`) đối chiếu mọi event của run về
    cùng một tenant, và đó là phép kiểm có nghĩa hơn cho bộ chấm: nó bắt được run mà node đầu mang
    `ankor` còn node sau mang `borea`, thứ mà một mệnh đề `WHERE tenant_id = %s` sẽ lặng lẽ giấu đi
    bằng cách chỉ trả về nửa số event.

    `run_id` không tồn tại ⇒ `[]`, không raise: rỗng là câu trả lời hợp lệ. Caller quyết nó có nghĩa
    gì — `answer_from_trace` sẽ raise ngay sau đó, đúng chỗ.

    **Hậu tố `_unscoped` (§7 mục 5, thẩm định VinSOC `kit#129`).** Tên cũ là `read_run` — trơn, và
    trơn thì chỗ gọi thiếu `tenant_scope_ok` trông y như chỗ gọi đủ. Thẩm định giữ nguyên **cách**
    kiểm (Won't Fix as designed) nhưng nói thẳng chỗ yếu: *"hàm này quả thật không tự bảo vệ được —
    nó dựa vào bên gọi nhớ gọi `tenant_scope_ok`. Đó là hợp đồng bằng lời, không phải bằng mã."* Hậu
    tố trả lời phần "bằng lời"; phần "bằng mã" là `tests/test_unscoped_reader_naming.py`, bài chặn
    coroutine đọc `obs.trace_events` không lọc tenant mà tên không tự khai.
    """
    async with pool.connection() as conn:
        await _assert_doc_xuyen_tenant_duoc(conn, "read_run_unscoped")
        cursor = await conn.execute(_READ_RUN, (run_id,))
        rows = await cursor.fetchall()
    return [_row_to_event(row) for row in rows]


async def list_runs_all_tenants(pool: Pool) -> list[tuple[str, int]]:
    """`(run_id, số event)` của **mọi** run trong bảng, cũ nhất trước — để `--list` chỉ ra chạy cái nào.

    **Hậu tố `_all_tenants` (§7 mục 4, thẩm định VinSOC `kit#129`, AV-203742).** Tên cũ `list_runs`
    không nói ra rằng nó vượt qua mọi tenant. Bộ quét tự ghi nhận *"giảm nhẹ do cần quyền truy cập cục
    bộ"* — đúng: chỉ chạy qua cờ `--list`, cần chuỗi kết nối DB, và người đã có chuỗi đó thì đọc được
    cả CSDL bằng `psql`. Nên đây không phải lỗ hổng khai thác được. Nhưng thẩm định gọi đúng tên vấn
    đề: **"một hàm không lọc tenant là một hàm chờ bị dùng nhầm chỗ"** — hôm nay sau cờ `--list`, ngày
    mai ai đó thấy tiện và gọi từ một route. Hậu tố làm chuyện đó phải xảy ra một cách có ý thức.

    `_all_tenants` chứ không phải `_unscoped`: hàm này **cố ý** vượt mọi tenant (đó là việc của
    `--list`), khác `read_run_unscoped` là "không lọc gì vì lọc ở tầng khác".
    """
    async with pool.connection() as conn:
        await _assert_doc_xuyen_tenant_duoc(conn, "list_runs_all_tenants")
        cursor = await conn.execute(_LIST_RUNS)
        return [(row[0], row[1]) for row in await cursor.fetchall()]


def _case_by_id(case_id: str) -> GoldenCase:
    """Case của `callisto-smoke-5-v0` theo id; không có ⇒ `LookupError` (fail-closed).

    Golden-30 thật là của DE và về D16; hôm nay bộ 5 case smoke đã merge là nguồn duy nhất có thật,
    và AIE-2 **chỉ đọc** nó — không sinh case, không sửa nhãn."""
    for case in _demo_golden_set().cases:
        if case.case_id == case_id:
            return case
    known = ", ".join(c.case_id for c in _demo_golden_set().cases)
    raise LookupError(f"không có case {case_id!r} trong callisto-smoke-5-v0 (có: {known})")


async def _amain(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m studio_evalhub.run_report",
        description="Chấm case từ trace ĐÃ BỀN HOÁ trong obs.trace_events rồi in bảng per-case (D15).",
    )
    parser.add_argument(
        "--dsn",
        default=os.environ.get("STUDIO_DATABASE_URL"),
        help="DSN Postgres (mặc định $STUDIO_DATABASE_URL)",
    )
    parser.add_argument("--list", action="store_true", help="liệt kê run_id có trong bảng rồi thoát")
    parser.add_argument(
        "--run",
        action="append",
        default=None,
        metavar="RUN_ID:CASE_ID",
        help="cặp run_id và case_id của callisto-smoke-5-v0 để chấm; lặp lại được",
    )
    args = parser.parse_args(argv)

    if not args.dsn:
        parser.error("thiếu DSN: đặt $STUDIO_DATABASE_URL hoặc truyền --dsn")

    pool: Pool = AsyncConnectionPool(args.dsn, open=False)
    await pool.open(wait=True)
    try:
        if args.list:
            for run_id, n in await list_runs_all_tenants(pool):
                print(f"{run_id}\t{n} event")
            return 0

        if not args.run:
            parser.error("thiếu --run RUN_ID:CASE_ID (chạy --list để xem run có sẵn)")

        results: list[SmokeResult] = []
        run_ids: list[str] = []
        events_by_run: dict[str, list[TraceEvent]] = {}
        for spec in args.run:
            run_id, sep, case_id = spec.partition(":")
            if not sep:
                parser.error(f"--run phải có dạng RUN_ID:CASE_ID, nhận {spec!r}")
            # Đọc MỘT lần cho mỗi run_id. Hai `--run R1:A --run R1:B` mà đọc hai lượt thì `events`
            # nhân đôi ⇒ Σcost nhân đôi — đúng `F-3` (replay double-count) trong failure-mode list
            # của DE, chỉ khác là ở đây nó sinh ra từ chính vòng lặp CLI chứ không từ replay.
            if run_id not in events_by_run:
                events_by_run[run_id] = await read_run_unscoped(pool, run_id)
            results.append(score_run_from_trace(_case_by_id(case_id), events_by_run[run_id]))
            run_ids.append(run_id)
    finally:
        await pool.close()

    print(
        render_run_cases(
            results,
            run_id=", ".join(run_ids),
            golden_set_ref=_demo_golden_set().golden_set_ref,
            trace_source=TRACE_SOURCE_POSTGRES,
            run_cost=_run_cost_cho_cli(events_by_run),
        )
    )
    return 0


def _run_cost_cho_cli(events_by_run: dict[str, list[TraceEvent]]) -> RunCost | None:
    """Cost của bảng CLI — chỉ khi lệnh nói về **đúng một** run.

    Đây là chỗ bề mặt UI-test đọc số từ **trace đã bền hoá trong Postgres**, không từ RAM: `events`
    đi qua `read_run_unscoped` → `_row_to_event` (`NUMERIC → Decimal → float`), tức cùng đường mà một người
    khác đọc lại run của mình ngày mai sẽ đi.

    **Nhiều run trong một lệnh ⇒ `None`, không phải một tổng gộp.** `RunCost` là cost **của một
    run**; cộng chéo run cho ra một con số không trả lời được câu hỏi nào, và `run_cost_from_trace`
    đã fail-closed đúng như thế. Chọn `None` thay vì để nó raise vì `--run` **vốn** nhận nhiều spec
    từ trước D19 — biến một lệnh đang chạy được thành lỗi là phá hợp đồng CLI để thêm một dòng
    hiển thị, đổi sai chiều.

    Ranh giới này nói ra chứ không để phát hiện sau: bảng nhiều run **không có** dòng cost, và đó là
    *"không có dữ liệu thì không dựng ô"* (`DEC-D12-02`) chứ không phải cost bằng 0.
    """
    if len(events_by_run) != 1:
        return None
    (events,) = events_by_run.values()
    return run_cost_from_trace(events)


def main() -> int:
    return asyncio.run(_amain())


if __name__ == "__main__":
    raise SystemExit(main())
