"""Seam chạy agent cho eval — phác skeleton AIE-2 (D3 #14; D5 #24 đọc trace).

`EvalHarness` cần *chạy một case qua agent* rồi chấm. Interpreter thật là của AIE-1
(`studio_engine.run`), và `.importlinter` cấm `studio_evalhub` import `studio_engine`/`studio_kb`
(hàng rào quadrant — R-SPEC A4). Nên seam ở đây là **Protocol nội bộ evalhub**: harness phụ thuộc
vào *hình dạng* "chạy case → nhận (câu trả lời + trace)", không phụ thuộc interpreter cụ thể.

`run_case` trả `CaseRun` = `AgentAnswer` (câu trả lời + cờ từ chối) + `events` (trace của đúng run
đó, `list[studio_contracts.TraceEvent]`). Từ D5 (#24) **citations chấm điểm đọc từ TRACE** (event
`kb-retrieve`), KHÔNG từ `AgentAnswer.citations` — trace là mặt quan sát thật.

D-13: seam nhận `tenant_id: UUID` (danh tính bất biến), KHÔNG nhận slug. Golden giữ slug làm nhãn;
resolve slug→UUID xảy ra *phía trên* seam (`run_smoke`/CLI/adapter), không giấu trong runner.

Adapter thật (`EngineAgentRunner`, sống ở `studio_app` composition root, D5–6 #29) bọc
`studio_engine.run`: map `final_state[<llm node>]` → `AgentAnswer` và đổ `RunResult.events` →
`CaseRun.events`. Đó là chỗ *duy nhất* chạm AIE-1, nằm ngoài module này. Đưa seam lên
`studio_contracts.protocols` là việc D11 + mentor-approval (Q4 `docs/scorecard-v0.md`).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from studio_contracts import TraceEvent


class AgentAnswer(BaseModel):
    """Câu trả lời một lần agent chạy một case.

    Chỉ mang thứ bộ chấm cần ở nhánh trả-lời-được (`answer` + cờ `refused`), không mang trace/cost
    (những thứ đó thuộc `TraceEvent`/`RunResult` của AIE-1, đi qua `CaseRun.events`)."""

    model_config = ConfigDict(frozen=True)

    answer: str
    """Câu trả lời cuối của agent. So với `GoldenCase.expected` ở nhánh trả-lời-được."""

    citations: list[str]
    """Các `chunk_id` agent **tự khai** đã trích (định dạng DE `ankor-leave-001#c1`).

    Từ D5 (#24): bộ chấm **KHÔNG** dùng field này để chấm — citation-accuracy và leak-check đọc từ
    TRACE (event `kb-retrieve` trong `CaseRun.events`), là mặt quan sát thật. Giữ field ở đây làm
    *cái LLM tự khai* để cross-check hallucination sau (claimed ⊆ retrieved). Xem
    `docs/scorecard-v0.md` §2.3, §2.7."""

    refused: bool = False
    """Agent có từ chối trả lời không. Nhánh từ-chối yêu cầu cờ này True (fail-closed): không suy
    "từ chối" từ nội dung `answer` để tránh đoán mò trên văn bản tự do.

    Nguồn (chốt với AIE-1, D4 2026-07-23): engine cấp cờ này **structural** qua output `llm-step`
    (`studio_engine` commit `71caeb8`: `refused = not retrieved_chunks`). Adapter ở `studio_app` map
    `final_state[<llm node>]["refused"]` vào trường này. Xem `docs/scorecard-v0.md` §2.7."""


class CaseRun(BaseModel):
    """Kết quả một lần chạy case qua seam — đơn vị đầu vào của bộ chấm (D5 #24).

    Gói `answer` (câu trả lời + cờ từ chối) cùng `events` (trace của đúng run đó). Bộ chấm lấy
    citations từ `events` (event `node_type == kb-retrieve`), KHÔNG từ `answer.citations` — xem
    `harness._retrieved_citations` + `docs/scorecard-v0.md` §2.3/§2.7."""

    model_config = ConfigDict(frozen=True)

    answer: AgentAnswer
    """Câu trả lời + cờ `refused`. Chấm nhánh trả-lời-được / từ-chối theo cờ này."""

    events: list[TraceEvent]
    """Trace của run: mỗi node một `TraceEvent`. Adapter thật đổ từ `RunResult.events`; hoặc reader
    Postgres của DE theo `run_id`. Bộ chấm đọc `.citations` của event `node_type == kb-retrieve`."""


@runtime_checkable
class AgentRunner(Protocol):
    """Seam harness gọi để chạy một case. Bản Day-3 là `StubAgentRunner`; bản thật (D5–6, #29) là
    adapter mỏng bọc `studio_engine.run` của AIE-1, tiêm từ `studio_app` (composition root)."""

    async def run_case(
        self,
        *,
        agent_id: str,
        query: str,
        tenant_id: UUID,
        section_roles: list[str],
    ) -> CaseRun:
        """Chạy `query` qua recipe của `agent_id` trong ngữ cảnh (`tenant_id`, `section_roles`) rồi
        trả `CaseRun` (câu trả lời + trace). Không nhận `case_id`: seam là ranh giới "chạy agent",
        không biết tới golden-set.

        D-13: `tenant_id` là **UUID** (danh tính bất biến) — slug đã được resolve *phía trên* seam
        (`run_smoke`/CLI/adapter, qua `core.tenants`), KHÔNG resolve âm thầm trong runner.

        Lưu ý (Q3, `docs/scorecard-v0.md`): `section_roles` là quyền dựng-phiên, KHÔNG truyền thẳng
        vào `kb.search` (giá trị client khai bị bỏ qua, phân giải phía máy chủ — chống T6)."""
        ...


class StubAgentRunner:
    """Stand-in cho interpreter AIE-1: trả `CaseRun` fixture theo `(query, tenant_id, section_roles)`.

    Khoá là **toàn bộ ngữ cảnh `run_case` nhận**, không phải một tập con tiện tay. Ba thành phần, mỗi
    thành phần vào khoá vì một ca thật đã đo được:

    - `query` — hiển nhiên.
    - `tenant_id` (D5) — cùng câu hỏi ở hai kho phải ra kết quả khác nhau (SC-01/SC-02 chung `query`,
      khác tenant → đáp án 3 vs 7 ngày).
    - `section_roles` (**D16**) — cùng câu hỏi, cùng kho, khác **quyền bên hỏi** thì một case phải
      trả lời còn case kia phải từ chối. Golden-30 có đúng hai cặp như vậy (`HB-08`/`HB-26` ankor và
      `HB-09`/`HB-30` borea, trục T6 label-spoof). Bỏ trục này khỏi khoá làm map co từ 30 xuống 28
      fixture, và vì cặp nằm ở hai nhánh ngược nhau nên case thua **chắc chắn** bị chấm bằng câu trả
      lời soạn cho nhánh kia — một `success = False` không nói gì về agent.

    Khoá dùng `tuple(section_roles)` vì `list` không hash được. Thứ tự trong tuple **có nghĩa**: đây
    là khoá tra cứu fixture, không phải một phép so tập hợp — fixture khai `("hr", "finance")` không
    khớp lời gọi `["finance", "hr"]`. Chọn vậy có chủ đích: một khoá chuẩn hoá (sort/frozenset) sẽ
    làm hai fixture khác nhau âm thầm gộp làm một, đúng lớp lỗi mà chính D16 vừa phải sửa.

    Không nhận `case_id` — seam là ranh giới *"chạy agent"*, không biết tới golden-set. Thiếu fixture
    → raise `LookupError` (fail-closed), **không** lùi về một khoá lỏng hơn và **không** trả rỗng âm
    thầm: một case im lặng ra rỗng sẽ chấm sai mà không lỗi nào nổi lên. **KHÔNG** tự resolve
    slug→UUID: nhận `tenant_id` đã resolve sẵn."""

    def __init__(self, answers: dict[tuple[str, UUID, tuple[str, ...]], CaseRun]) -> None:
        self._answers = dict(answers)

    async def run_case(
        self,
        *,
        agent_id: str,
        query: str,
        tenant_id: UUID,
        section_roles: list[str],
    ) -> CaseRun:
        """Trả `CaseRun` fixture khớp `(query, tenant_id, tuple(section_roles))`; raise `LookupError`
        nếu không có (fail-closed, không có đường lùi về khoá lỏng hơn)."""
        key = (query, tenant_id, tuple(section_roles))
        try:
            return self._answers[key]
        except KeyError:
            raise LookupError(
                f"StubAgentRunner: chưa có fixture cho (query={query!r}, tenant_id={tenant_id}, "
                f"section_roles={list(section_roles)!r})"
            ) from None
