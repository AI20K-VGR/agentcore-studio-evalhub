"""Fixture dùng chung — **chỗ DUY NHẤT trong quadrant biết golden-30 của DE nằm ở đâu**.

`DEC-D16-01` chia ba tầng: `load_golden_set` nhận `path`, `EvalHarness.run` nhận `golden_set_path`
keyword-only bắt buộc, và **composition root** (CLI arg · `apps/studio` · fixture test) là tầng duy
nhất được biết đường dẫn cụ thể. File này là composition root của suite — nên đường dẫn kb nằm ở
đây, và **chỉ** ở đây, chứ không phải trong `src/` (bất biến đó có bài cưỡng chế riêng:
`test_src_khong_hardcode_duong_dan_kb`).

Đường dẫn resolve từ **workspace root**, không từ cwd: `pytest` chạy được từ kit gốc lẫn từ trong
`packages/evalhub`, và một fixture phụ thuộc cwd sẽ skip im lặng ở một trong hai chỗ.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.golden_case import GoldenSet

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

_GOLDEN_DIR = _WORKSPACE_ROOT / "packages" / "kb" / "golden"

# HAI tên, thử theo thứ tự — vì bộ 30 đang đổi tên giữa chừng và fixture này phải sống qua cả hai
# phía của lần đổi đó:
#
#   - `callisto-golden-30-v1.yaml`      ← tên MỚI, sau `kb#18`
#   - `callisto-handbook-30-draft.yaml` ← tên CŨ, vẫn là thứ con trỏ kb của kit đang trỏ tới
#
# Vì sao phải xử lý thay vì đợi: `golden_30_path` **skip** khi không thấy file, và skip là trạng
# thái IM LẶNG. Ngày con trỏ kb được bump qua `kb#18`, một hằng số tên-cũ sẽ làm toàn bộ bài
# integration của quadrant lặng lẽ biến mất khỏi suite — trong đó có bài duy nhất giữ lưới cho
# mutant `M-L3` và cho bug T6 (`kb#18` N1). Suite vẫn "xanh", chỉ là nó không còn đo gì.
#
# Đây KHÔNG phải một fallback kiểu "khoá lỏng hơn": ref vẫn được `load_golden_set` assert từ **nội
# dung** file, nên trỏ nhầm sang file khác vẫn raise. Chỗ này chỉ là đường dẫn.
#
# ĐIỀU KIỆN GỠ, đọc được: khi con trỏ `packages/kb` của kit đã bump qua `kb#18`, xoá tên cũ khỏi
# tuple và để một tên duy nhất.
_TEN_FILE_GOLDEN_30 = ("callisto-golden-30-v1.yaml", "callisto-handbook-30-draft.yaml")

_GOLDEN_30 = next(
    (p for p in (_GOLDEN_DIR / ten for ten in _TEN_FILE_GOLDEN_30) if p.is_file()),
    _GOLDEN_DIR / _TEN_FILE_GOLDEN_30[0],
)


@pytest.fixture
def golden_30_ref() -> str:
    """Ref THẬT — nằm trong **nội dung** file, không suy từ tên file (`DEC-D16-01`)."""
    return "callisto-golden-30-v1"


@pytest.fixture
def golden_30_path() -> Path:
    """Đường dẫn tới golden-30 thật của DE (`kb@1e8774f`, 30 case). Thiếu file ⇒ **skip có lý do đọc
    được**, không phải một bài lặng lẽ biến mất.

    Skip ở tầng fixture chứ không phải `pytest.mark.skipif`: mark phải được **import** vào từng file
    test, mà `tests/` không có `__init__.py` nên đường import đó phụ thuộc thứ tự nạp conftest của
    pytest — một bài đỏ vì `ImportError` là đúng thứ bài này tồn tại để tránh.

    ⚠️ **Quan trọng cho mutation:** mutant `M-L3` (`expects_refusal` bỏ trục T6) **chỉ có lưới ở tầng
    integration**. Chạy suite trong môi trường không có `packages/kb` ⇒ mọi bài dùng fixture này skip
    ⇒ `M-L3` sống mà không ai biết. Vì thế môi trường chạy mutation phải được ghi lại — cùng lớp với
    chuyện `77 passed` của D15 đo trong shell không có `STUDIO_DATABASE_URL_ADMIN`."""
    if not _GOLDEN_30.is_file():
        pytest.skip(
            f"golden-30 của DE không có ở {_GOLDEN_30} — cần `git submodule update --init "
            "packages/kb` (chạy từ workspace root). Bài integration này nạp file thật, không dựng "
            "fixture thay thế."
        )
    return _GOLDEN_30


@pytest.fixture
def tenant_ids() -> Mapping[str, UUID]:
    """Map slug → `tenant_id` UUID. Resolve **phía trên seam** (D-13): golden giữ slug làm nhãn,
    runner nhận UUID. Thật thì map đến từ `core.tenants`; test dựng stand-in tất định bằng `uuid5`
    để hai lượt chạy ra cùng một danh tính."""
    return {"ankor": uuid5(NAMESPACE_DNS, "ankor"), "borea": uuid5(NAMESPACE_DNS, "borea")}


def _trace_event(tenant_id: UUID, citations: list[str]) -> TraceEvent:
    """Một event `kb-retrieve` mang `citations` — mặt quan sát bộ chấm đọc."""
    return TraceEvent(
        event_id="e1",
        run_id="r1",
        agent_id="agent-1",
        tenant_id=tenant_id,
        node_id="n1",
        node_type=NodeType.KB_RETRIEVE,
        ts="2026-08-10T00:00:00+00:00",
        inputs_hash="h",
        outputs={},
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=citations,
    )


@pytest.fixture
def runner_tot() -> Callable[[GoldenSet, Mapping[str, UUID]], StubAgentRunner]:
    """Factory dựng `StubAgentRunner` trả lời **đúng** mọi case của một golden-set.

    Sinh từ chính golden-set nên nó đúng theo định nghĩa, không phải theo một bảng chép tay sẽ mục
    khi DE đổi bộ case. Hai nhánh, mỗi nhánh thoả đúng luật chấm của nó:

    - **trả-lời**: answer chứa cụm `expected`, `refused=False`, trace trích đúng `expected_citation`
      ⇒ `success=True`, `citation_accuracy=1.0`.
    - **từ-chối**: `refused=True`, trace có **1 event, 0 citation** ⇒ đây là oracle **F02**
      (GUIDE-C `:592` — *"the honest refusal: refused, cited nothing ⇒ the case PASSES"*), **không**
      phải no-trace.

    Khoá fixture ba thành phần `(query, tenant_id, tuple(section_roles))` — golden-30 có hai cặp
    trùng `(query, tenant_id)` khác `section_roles` (trục T6), khoá hai thành phần sẽ nuốt mất một
    nửa mỗi cặp.

    Dùng chung cho T4 (chạy 30 case) và T7 (bài đối trọng `test_gate_passes_on_good_recipe`): không
    có một runner **tốt** thì bài money-shot không phân biệt được *"gate chặn đúng"* với *"gate chặn
    mọi thứ"*."""

    def _dung(golden: GoldenSet, tenant_map: Mapping[str, UUID]) -> StubAgentRunner:
        fixtures: dict[tuple[str, UUID, tuple[str, ...]], CaseRun] = {}
        for case in golden.cases:
            tenant_id = tenant_map[case.tenant]
            if case.expects_refusal:
                answer = AgentAnswer(answer="Tôi không thể trả lời câu hỏi này.", citations=[], refused=True)
                # Trace mang MỘT chunk hợp lệ của CHÍNH kho người hỏi — không phải rỗng.
                #
                # Bản trước để `[]`, và đó là **fixture thuận lợi**: `all(...)` trên tập rỗng luôn
                # `True`, nên luật `no_leak` sai kiểu gì cũng không lộ ra. Đúng chỗ bug `kb#18` N1
                # trốn được suốt: 4 case T6 của golden-30 (`expected_tenant == tenant`) bị luật cũ
                # chấm FAIL oan ngay khi trace có bất kỳ chunk nào của kho mình, mà không bài
                # integration nào thấy vì trace toàn rỗng.
                #
                # Một agent thật gần như luôn có retrieval trước khi quyết định từ chối, nên rỗng
                # mới là ca không giống đời thật. Với luật đúng: T6 ⇒ chunk thuộc kho người hỏi nên
                # PASS; T1 ⇒ chunk KHÔNG thuộc `expected_tenant` nên cũng PASS.
                events = [_trace_event(tenant_id, [f"{case.tenant}-handbook-000#c1"])]
            else:
                answer = AgentAnswer(
                    answer=f"Theo tài liệu, {case.expected}.",
                    citations=list(case.expected_citation),
                    refused=False,
                )
                events = [_trace_event(tenant_id, list(case.expected_citation))]
            fixtures[(case.query, tenant_id, tuple(case.section_roles))] = CaseRun(answer=answer, events=events)
        return StubAgentRunner(fixtures)

    return _dung
