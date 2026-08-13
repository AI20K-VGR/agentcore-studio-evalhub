"""`EvalHarness.run(recipe_hash=…)` — mắt GIỮA của đường ống, vá ở D20.

## Lỗ được vá

`T2` mở đường nhận ở `compute_scorecard(recipe_hash=…)` và khoá nó bằng test. Nhưng caller **duy
nhất trên đường thật** là `apps/studio/routes/publish.py`, và nó gọi `EvalHarness().run(...)` — **không**
gọi thẳng `compute_scorecard`. `EvalHarness.run` lại không xuyên tham số đó qua ⇒ đường ống đứt ở
giữa:

    routes/publish.py:105  EvalHarness().run(agent_id, golden_set_ref, …)   ← không có tham số
            ↓
    harness.py             compute_scorecard(…)                            ← KHÔNG truyền
            ↓
    compute.py             recipe_hash: str | None = None                  ← T2 mở ở ĐÂY

Tức kể cả khi SWE chốt `🅑` và caller có hash trong tay, **không có đường nào đưa nó tới `Scorecard`**.

Lỗ này là của chính `T2`: khoá bất biến ở `compute_scorecard` rồi coi như xong, **không kiểm caller
thật**. Bài học lặp lại đúng lớp lỗi cả tuần đi tìm — một mắt xanh không nói gì về chuỗi.

**Vẫn KHÔNG sinh hash.** `DEC-D20-02` không đổi: evalhub **nhận**, tuyệt đối không tự dẫn xuất. Băm
trên chuỗi byte nào vẫn là câu hỏi mở của SWE (`kit#127` 🅑).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from uuid import UUID

from studio_evalhub.agent_runner import StubAgentRunner
from studio_evalhub.golden_case import GoldenSet
from studio_evalhub.golden_loader import load_golden_set
from studio_evalhub.harness import EvalHarness

# Nhãn rõ: stand-in trong test, KHÔNG phải producer (`DEC-D20-02`). Cố tình không phải hex-digest hợp
# lệ — bất kỳ đường nào tự băm cũng cho giá trị khác, và bài dưới đây đỏ.
_STAND_IN = "stand-in-not-a-producer-see-DEC-03"


async def test_recipe_hash_truyen_qua_run_toi_scorecard(
    golden_30_path: Path,
    golden_30_ref: str,
    tenant_ids: Mapping[str, UUID],
    runner_tot: Callable[[GoldenSet, Mapping[str, UUID]], StubAgentRunner],
) -> None:
    """Truyền `recipe_hash` vào `EvalHarness.run` ⇒ `Scorecard` mang **đúng chuỗi đó**.

    Đây là bài duy nhất đo **mắt giữa**. `test_recipe_hash_transport.py` (T2) đo mắt cuối
    (`compute_scorecard`), và nó xanh **kể cả khi mắt giữa đứt** — đó là lý do lỗ này sống sót qua T2.

    Assert bằng **giá trị**, không `is not None`: `is not None` xanh với cả một cài đặt tự sinh hash,
    đúng thứ `DEC-D20-02` cấm."""
    golden = load_golden_set(golden_30_path, expect_ref=golden_30_ref)

    scorecard = await EvalHarness().run(
        "agent-1",
        golden_30_ref,
        golden_set_path=golden_30_path,
        runner=runner_tot(golden, tenant_ids),
        tenant_ids=tenant_ids,
        threshold_success=0.9,
        threshold_citation_accuracy=0.95,
        recipe_hash=_STAND_IN,
    )

    assert scorecard.recipe_hash == _STAND_IN


async def test_khong_truyen_thi_van_None(
    golden_30_path: Path,
    golden_30_ref: str,
    tenant_ids: Mapping[str, UUID],
    runner_tot: Callable[[GoldenSet, Mapping[str, UUID]], StubAgentRunner],
) -> None:
    """Không truyền ⇒ `recipe_hash is None`, y như trước bản vá.

    Nửa còn lại của "additive", và **không** phải bài thừa: không có nó, một cài đặt đổi default thành
    `""` hoặc tự sinh một hash *"cho `publish()` khỏi từ chối"* vẫn làm bài trên xanh.

    `None` ở đây là **giá trị trung thực**: `DEC-03` chưa có producer, nên bịa một chuỗi ở phía eval là
    nói dối `publish()` về thứ scorecard này chứng nhận. Fail-closed sống ở consumer
    (`publish.py:72`), đúng chỗ của nó."""
    golden = load_golden_set(golden_30_path, expect_ref=golden_30_ref)

    scorecard = await EvalHarness().run(
        "agent-1",
        golden_30_ref,
        golden_set_path=golden_30_path,
        runner=runner_tot(golden, tenant_ids),
        tenant_ids=tenant_ids,
        threshold_success=0.9,
        threshold_citation_accuracy=0.95,
    )

    assert scorecard.recipe_hash is None
