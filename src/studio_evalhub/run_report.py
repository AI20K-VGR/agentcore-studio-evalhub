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
from typing import Any

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from studio_contracts import NodeType, Tokens, TraceEvent

from studio_evalhub.agent_runner import AgentAnswer
from studio_evalhub.cli import _demo_golden_set
from studio_evalhub.golden_case import GoldenCase
from studio_evalhub.harness import SmokeResult, citations_from_trace, score_case
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
    | **nhiều** `llm-step` | *"câu trả lời của run"* lúc đó phải do hợp đồng nói, không do thứ tự dòng nói |

    Nhánh cuối là nhánh đắt nhất. `#102` cho người dùng dựng recipe tự do, nên recipe nhiều bước LLM
    là chuyện sẽ tới. Chọn im lặng cái đầu hay cái cuối sẽ cho ra một bảng điểm trông vẫn đúng trong
    khi nó đang chấm nhầm bước — đúng lớp lỗi breakpoint `#14` (suy một giá trị ngữ nghĩa im lặng rồi
    chấm như thể đã đo).

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

    raw_citations = outputs.get("citations")
    return AgentAnswer(
        answer=str(outputs["answer"]),
        citations=[str(c) for c in raw_citations] if isinstance(raw_citations, list) else [],
        refused=bool(outputs.get("refused", False)),
    )


def score_run_from_trace(case: GoldenCase, events: list[TraceEvent]) -> SmokeResult:
    """Chấm một case **hoàn toàn** từ trace đã bền hoá: cả `answer` lẫn `citations` đọc từ `events`.

    Đây là chỗ hai vế gặp nhau. `citations_from_trace` (D5) lo vế citation; `answer_from_trace` (hôm
    nay) lo vế câu trả lời. Sau hàm này, không còn mảnh nào của phép chấm phụ thuộc RAM của tiến
    trình đã chạy agent — bảng điểm dựng lại được từ `run_id` và không gì khác.
    """
    return score_case(case, answer_from_trace(events), citations_from_trace(events))


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

    `cost` là `NUMERIC` ⇒ psycopg trả `Decimal`, ép `float` để khớp contract. `citations` `NULL`
    giữ nguyên `None` chứ không đổi thành `[]`: *"chưa có trích dẫn nào"* và *"không áp dụng"* là hai
    chuyện khác nhau, và `citations_from_trace` phân biệt hai cái đó."""
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


async def read_run(pool: Pool, run_id: str) -> list[TraceEvent]:
    """Mọi event của `run_id`, xếp theo `(ts, event_id)` như `studio_kb.trace_reader` làm.

    Khác `PgTraceReader.read_run`, hàm này **không** lọc `tenant_id`: nó là công cụ **đọc lại một run
    đã biết id** ở phía bộ chấm, không phải một API phục vụ request của tenant. Bù lại, tenant vẫn
    được kiểm — `tenant_scope_ok(events, expected)` (`harness.py:105`) đối chiếu mọi event của run về
    cùng một tenant, và đó là phép kiểm có nghĩa hơn cho bộ chấm: nó bắt được run mà node đầu mang
    `ankor` còn node sau mang `borea`, thứ mà một mệnh đề `WHERE tenant_id = %s` sẽ lặng lẽ giấu đi
    bằng cách chỉ trả về nửa số event.

    `run_id` không tồn tại ⇒ `[]`, không raise: rỗng là câu trả lời hợp lệ. Caller quyết nó có nghĩa
    gì — `answer_from_trace` sẽ raise ngay sau đó, đúng chỗ.
    """
    async with pool.connection() as conn:
        cursor = await conn.execute(_READ_RUN, (run_id,))
        rows = await cursor.fetchall()
    return [_row_to_event(row) for row in rows]


async def list_runs(pool: Pool) -> list[tuple[str, int]]:
    """`(run_id, số event)` của mọi run trong bảng, cũ nhất trước — để `--list` chỉ ra chạy cái nào."""
    async with pool.connection() as conn:
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
            for run_id, n in await list_runs(pool):
                print(f"{run_id}\t{n} event")
            return 0

        if not args.run:
            parser.error("thiếu --run RUN_ID:CASE_ID (chạy --list để xem run có sẵn)")

        results: list[SmokeResult] = []
        run_ids: list[str] = []
        for spec in args.run:
            run_id, sep, case_id = spec.partition(":")
            if not sep:
                parser.error(f"--run phải có dạng RUN_ID:CASE_ID, nhận {spec!r}")
            events = await read_run(pool, run_id)
            results.append(score_run_from_trace(_case_by_id(case_id), events))
            run_ids.append(run_id)
    finally:
        await pool.close()

    print(
        render_run_cases(
            results,
            run_id=", ".join(run_ids),
            golden_set_ref=_demo_golden_set().golden_set_ref,
            trace_source=TRACE_SOURCE_POSTGRES,
        )
    )
    return 0


def main() -> int:
    return asyncio.run(_amain())


if __name__ == "__main__":
    raise SystemExit(main())
