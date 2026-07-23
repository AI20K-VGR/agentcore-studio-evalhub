"""CLI smoke-eval — chạy `python -m studio_evalhub.cli`.

Dựng bộ 5 smoke-case Callisto (nguồn từ golden-set của DE, `callisto-smoke-5-v0`) + một runner
mô phỏng, chạy qua `EvalHarness.run_smoke`, rồi in bảng điểm 5 dòng (`case_id · success · citation_acc`).
Chưa nối interpreter thật hay đọc file YAML của DE: case dựng in-code, runner là câu trả lời mô phỏng
— đổi sang đồ thật khi có loader (`pyyaml`/`uv.lock` — mentor) + adapter luồng thật ở `apps/studio`.
"""

from __future__ import annotations

import asyncio

from studio_evalhub.agent_runner import AgentAnswer
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.harness import EvalHarness, SmokeResult

_AGENT_ID = "agent-smoke-demo"


def _demo_golden_set() -> GoldenSet:
    """Bộ 5 smoke-case Callisto — **nguồn từ golden-set của DE** (`callisto-smoke-5-v0`,
    `packages/kb/golden/smoke-5.yaml`; DE sinh + gán nhãn tay, AIE-2 chỉ đọc). Dựng in-code tạm vì
    loader hoãn (`pyyaml` chưa khai là dep — cần sửa `uv.lock` ở repo cha, mentor); đổi sang loader khi
    khai xong. Không suy diễn/đổi wording/bịa id.
    """
    return GoldenSet(
        golden_set_ref="callisto-smoke-5-v0",
        cases=[
            GoldenCase(
                case_id="SC-01",
                query="Nhân viên xin nghỉ phép cần báo trước bao lâu?",
                tenant="ankor",
                section_roles=["public"],
                expected_tenant="ankor",
                expected_section_role="public",
                expected="3 ngày làm việc",
                expected_citation=["ankor-leave-001#c1"],
            ),
            GoldenCase(
                case_id="SC-02",
                query="Nhân viên xin nghỉ phép cần báo trước bao lâu?",
                tenant="borea",
                section_roles=["public"],
                expected_tenant="borea",
                expected_section_role="public",
                expected="7 ngày làm việc",
                expected_citation=["borea-leave-001#c1"],
            ),
            GoldenCase(
                case_id="SC-03",
                query="Trưởng nhóm được duyệt chi tối đa bao nhiêu?",
                tenant="ankor",
                section_roles=["finance"],
                expected_tenant="ankor",
                expected_section_role="finance",
                expected="20 triệu đồng",
                expected_citation=["ankor-expense-001#c2"],
            ),
            GoldenCase(
                case_id="SC-04",
                query="Hạn mức chi của Borea là bao nhiêu?",
                tenant="ankor",
                section_roles=["public"],
                expected_tenant="borea",
                expected_section_role="finance",
                expected="refusal",
                expected_citation=[],
            ),
            GoldenCase(
                case_id="SC-05",
                query="Thang lương của công ty gồm những bậc nào?",
                tenant="ankor",
                section_roles=["engineering"],
                expected_tenant="ankor",
                expected_section_role="hr",
                expected="refusal",
                expected_citation=[],
            ),
        ],
    )


class _DemoRunner:
    """Runner cục bộ cho CLI demo (đứng thay interpreter AIE-1) — khoá fixture theo **`(query, tenant)`**.

    Cặp SC-01/SC-02 dùng CHUNG `query` (cùng câu hỏi, khác tenant → đáp án phải khác: 3 vs 7 ngày), nên
    khoá theo `query` như `StubAgentRunner` sẽ đụng key. `run_case` vốn nhận `tenant` nên phân biệt được.
    Định nghĩa tại đây để **không đụng** `agent_runner.py`. Thiếu fixture → fail-closed (raise), không
    trả câu trả lời rỗng âm thầm.
    """

    def __init__(self, answers: dict[tuple[str, str], AgentAnswer]) -> None:
        self._answers = dict(answers)

    async def run_case(
        self, *, agent_id: str, query: str, tenant: str, section_roles: list[str]
    ) -> AgentAnswer:
        try:
            return self._answers[(query, tenant)]
        except KeyError:
            raise LookupError(
                f"_DemoRunner: chưa có fixture cho (query={query!r}, tenant={tenant!r})"
            ) from None


def _demo_runner() -> _DemoRunner:
    """Câu trả lời mô phỏng agent, khoá theo `(query, tenant)`. Trả-lời-được: `answer` CHỨA cụm
    `expected` + trích đúng `chunk_id` của DE. Từ-chối: `refused=True, citations=[]`. Answer text là
    mô phỏng do AIE-2 soạn; `chunk_id` chỉ tái dùng đúng của DE, KHÔNG bịa id mới.
    """
    return _DemoRunner(
        {
            ("Nhân viên xin nghỉ phép cần báo trước bao lâu?", "ankor"): AgentAnswer(
                answer="Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
                citations=["ankor-leave-001#c1"],
                refused=False,
            ),
            ("Nhân viên xin nghỉ phép cần báo trước bao lâu?", "borea"): AgentAnswer(
                answer="Nhân viên cần báo trước 7 ngày làm việc.",
                citations=["borea-leave-001#c1"],
                refused=False,
            ),
            ("Trưởng nhóm được duyệt chi tối đa bao nhiêu?", "ankor"): AgentAnswer(
                answer="Trưởng nhóm được duyệt chi tối đa 20 triệu đồng.",
                citations=["ankor-expense-001#c2"],
                refused=False,
            ),
            ("Hạn mức chi của Borea là bao nhiêu?", "ankor"): AgentAnswer(
                answer="Tôi không thể trả lời câu hỏi về dữ liệu của tổ chức khác.",
                citations=[],
                refused=True,
            ),
            ("Thang lương của công ty gồm những bậc nào?", "ankor"): AgentAnswer(
                answer="Tôi không có quyền truy cập thông tin thang lương.",
                citations=[],
                refused=True,
            ),
        }
    )


def _render(results: list[SmokeResult]) -> str:
    """Bảng `case_id | success | citation_acc` — cột 'in success' theo issue #14/#19."""
    header = f"{'case_id':<20} {'success':<8} {'citation_acc':>12}"
    lines = [header, "-" * len(header)]
    for r in results:
        lines.append(f"{r.case_id:<20} {('PASS' if r.success else 'FAIL'):<8} {r.citation_accuracy:>12.2f}")
    passed = sum(1 for r in results if r.success)
    lines.append("-" * len(header))
    lines.append(f"{passed}/{len(results)} PASS")
    return "\n".join(lines)


async def _main() -> None:
    results = await EvalHarness().run_smoke(
        agent_id=_AGENT_ID,
        golden_set=_demo_golden_set(),
        runner=_demo_runner(),
    )
    print(_render(results))


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
