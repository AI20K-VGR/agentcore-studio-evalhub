"""Seam chạy agent cho eval — phác skeleton AIE-2 (D3, issue #14).

`EvalHarness` cần *chạy một case qua agent* rồi chấm. Nhưng interpreter thật là của AIE-1
(`studio_engine.run`), và `.importlinter` cấm `studio_evalhub` import `studio_engine`/`studio_kb`
(hàng rào quadrant — R-SPEC A4). Nên seam ở đây là **Protocol nội bộ evalhub**: harness phụ thuộc
vào *hình dạng* "chạy case → nhận câu trả lời", không phụ thuộc vào interpreter cụ thể.

`AgentAnswer` khai đúng *thứ harness cần để chấm* — câu trả lời + danh sách chunk đã trích + cờ đã
từ chối — KHÔNG phải bản sao chữ ký `studio_engine.run(recipe, *, trace_writer) -> RunResult`.
`RunResult` hiện chưa có field câu-trả-lời/citations (AIE-1 bổ sung sau); khi có, adapter bọc quanh
`studio_engine.run` sẽ map sang `AgentAnswer` — adapter đó (D4–6, issue #29) là chỗ *duy nhất* chạm
AIE-1, nằm ngoài module này.

Đưa seam này lên `studio_contracts.protocols` (cạnh `EmbeddingService`/`LLM`/`TraceWriter`) là việc
D11 + mentor-approval (Q4 trong `docs/scorecard-v0.md`), ngoài write-scope hôm nay — nên để nội bộ.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict


class AgentAnswer(BaseModel):
    """Kết quả một lần agent chạy một case — nửa đầu vào của bộ chấm.

    Chỉ mang thứ `score_case` cần, không mang trace/cost (những thứ đó thuộc `RunResult` của AIE-1).
    """

    model_config = ConfigDict(frozen=True)

    answer: str
    """Câu trả lời cuối của agent. So với `GoldenCase.expected` ở nhánh trả-lời-được."""

    citations: list[str]
    """Các `chunk_id` agent đã trích, đúng định dạng DE (`ankor-leave-001#c1`). Dùng cho cả
    `citation_accuracy` (nhánh trả lời) lẫn kiểm rò kho khác (nhánh từ chối)."""

    refused: bool = False
    """Agent có từ chối trả lời không. Nhánh từ-chối yêu cầu cờ này True (fail-closed): không suy
    "từ chối" từ nội dung `answer` để tránh đoán mò trên văn bản tự do.

    Nguồn (chốt với AIE-1, D4 2026-07-23): engine cấp cờ này **structural** qua output `llm-step`
    (`studio_engine` commit `71caeb8`: `refused = not retrieved_chunks`) — đúng thiết kế "không đoán
    text". Adapter ở `studio_app` map `final_state[<llm node>]["refused"]` vào trường này. Xem
    `docs/scorecard-v0.md` §2.7."""


@runtime_checkable
class AgentRunner(Protocol):
    """Seam harness gọi để chạy một case. Bản Day-3 là `StubAgentRunner`; bản thật (D4–6) là adapter
    mỏng bọc `studio_engine.run` của AIE-1, tiêm từ `studio_app` (composition root)."""

    async def run_case(
        self,
        *,
        agent_id: str,
        query: str,
        tenant: str,
        section_roles: list[str],
    ) -> AgentAnswer:
        """Chạy `query` qua recipe của `agent_id` trong ngữ cảnh (`tenant`, `section_roles`) rồi trả
        `AgentAnswer`. Không nhận `case_id`: seam là ranh giới "chạy agent", không biết tới golden-set.

        Lưu ý (Q3, `docs/scorecard-v0.md`): `section_roles` là quyền dựng-phiên, KHÔNG truyền thẳng
        vào `kb.search` (giá trị client khai bị bỏ qua, phân giải phía máy chủ — chống T6)."""
        ...


class StubAgentRunner:
    """Stand-in Day-3 cho interpreter AIE-1: trả câu trả lời fixture theo `query`.

    Khoá theo `query` (không phải `case_id`) vì `run_case` không nhận `case_id` — seam không biết tới
    golden-set. `query` thiếu trong fixture → raise (fail-closed), không trả câu trả lời rỗng âm thầm
    (một case im lặng ra rỗng sẽ chấm sai mà không lỗi nào nổi lên)."""

    def __init__(self, answers: dict[str, AgentAnswer]) -> None:
        self._answers = dict(answers)

    async def run_case(
        self,
        *,
        agent_id: str,
        query: str,
        tenant: str,
        section_roles: list[str],
    ) -> AgentAnswer:
        """Trả `AgentAnswer` fixture khớp `query`; raise `LookupError` nếu không có (fail-closed)."""
        try:
            return self._answers[query]
        except KeyError:
            raise LookupError(f"StubAgentRunner: chưa có fixture cho query {query!r}") from None
