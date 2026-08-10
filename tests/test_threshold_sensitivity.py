"""Test độ nhạy ngưỡng — **ô DoD 3: "đổi threshold → verdict đổi"**.

Chứng minh bằng **test**, không bằng ảnh chụp màn hình: cùng một `list[CaseResult]`, chạy
`compute_scorecard` hai lần với hai bộ ngưỡng ⇒ `PASS` rồi `FAIL`. Đây là bài chứng minh **gate có
răng** — không có nó thì `gate.verdict` có thể là một hằng số và mọi bài khác vẫn xanh.

**File này KHÔNG chốt và KHÔNG recalibrate ngưỡng** (`DEC-D16-05`). Ngưỡng mặc định `0.9/0.95` sống ở
recipe (`workbench/builder.py:169`) và **giữ nguyên trong D16**; số đo trên golden-30 là **thu thập
số liệu** cho quyết định ở ngày sau. Hai việc đó tách nhau có chủ đích: một ngưỡng bị hạ trong cùng
ngày đo được điểm thì không phân biệt được với việc chỉnh cho vừa số, và người đọc scorecard sau này
không có cách nào biết thứ tự hai việc.
"""

from __future__ import annotations

import pytest
from studio_contracts import CaseResult
from studio_evalhub.compute import compute_scorecard


def _bo_case() -> tuple[list[CaseResult], set[str]]:
    """8 case nhánh trả-lời: 6 đúng / 2 sai, `citation_accuracy` 0.75 đều.

    ⇒ `success_rate = 6/8 = 0.75` và `citation_accuracy = 0.75`. Hai trục **cùng giá trị** ở đây là
    có chủ đích cho bài thứ hai: nó cho phép nhích từng trục một mà trục kia đứng yên, nên khi
    verdict lật thì biết chắc trục nào lật nó."""
    results = [
        *[_r(f"OK-{i}", success=True) for i in range(6)],
        *[_r(f"BAD-{i}", success=False) for i in range(2)],
    ]
    return results, {r.case_id for r in results}


def _r(case_id: str, *, success: bool) -> CaseResult:
    return CaseResult(case_id=case_id, expected="x", actual="x", success=success, citation_accuracy=0.75)


def _verdict(results: list[CaseResult], scored: set[str], ts: float, tc: float) -> str:
    return compute_scorecard("a", "g", results, ts, tc, scored_case_ids=scored).gate.verdict


def test_doi_threshold_thi_verdict_doi() -> None:
    """**Ô DoD 3.** Cùng một `results`, hai bộ ngưỡng ⇒ `PASS` rồi `FAIL`.

    `results` **không đổi** giữa hai lượt — đó là toàn bộ thiết kế của bài. Nếu dựng hai bộ dữ liệu
    khác nhau thì verdict đổi có thể do dữ liệu, và bài không nói được gì về ngưỡng. Ở đây biến duy
    nhất là ngưỡng, nên kết luận chỉ có một cách đọc.

    Bài này cũng là lưới chặn một `gate.verdict` hằng số: một bản hiện thực trả `"PASS"` cứng, hoặc
    `"FAIL"` cứng, đều làm đúng một trong hai assert đỏ."""
    results, scored = _bo_case()

    # Ngưỡng thấp hơn điểm đo trên cả hai trục ⇒ đạt.
    assert _verdict(results, scored, 0.7, 0.7) == "PASS"

    # Ngưỡng mặc định của recipe (builder.py:169) — GIỮ NGUYÊN, không đổi ở D16.
    assert _verdict(results, scored, 0.9, 0.95) == "FAIL"


@pytest.mark.parametrize(
    ("ts", "tc", "mong_doi", "vi_sao"),
    [
        (0.75, 0.75, "PASS", "cả hai trục ĐÚNG BẰNG điểm đo ⇒ >= cho PASS"),
        (0.76, 0.75, "FAIL", "nhích trục success +0.01 ⇒ lật"),
        (0.75, 0.76, "FAIL", "nhích trục citation +0.01 ⇒ lật"),
    ],
)
def test_verdict_doi_o_dung_hai_phia_cua_nguong(ts: float, tc: float, mong_doi: str, vi_sao: str) -> None:
    """Ngưỡng đặt **ngay tại điểm đo** ⇒ `PASS`; nhích `+0.01` ⇒ `FAIL`.

    Đây là bài khoá toán tử `>=` (mutant `M-C2`). Ca biên là ca **duy nhất** phân biệt `>=` với `>`
    — mọi bộ dữ liệu khác đều xanh với cả hai toán tử, nên một suite không có ca biên thì không có ý
    kiến gì về chuyện đó. `DEC-04` đo đúng ca này ở quy mô thật: `10×1.0 + 20×0.85` rơi **đúng** vào
    `0.90` ở ngưỡng `0.9`.

    Ba tham số cũng chứng minh hai trục **độc lập**: nhích trục nào thì trục đó lật verdict, trục
    kia đứng yên. Không có hai dòng cuối thì một bản hiện thực chỉ đọc một trục vẫn xanh."""
    results, scored = _bo_case()

    assert _verdict(results, scored, ts, tc) == mong_doi, vi_sao
