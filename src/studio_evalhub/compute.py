"""Scorecard-compute seam — spec AIE-2 (R-SPEC A7 INV-6, umbrella-contract.md:146-158).

Aggregates a golden-set run's per-case `CaseResult`s (P2 `studio_contracts.CaseResult`) into
`success_rate` + `citation_accuracy` (`Aggregate`), then decides `gate.verdict` (PASS|FAIL) against
the recipe's `ScorecardThreshold`. `gate.verdict == "FAIL"` is a HARD gate for Publish (INV-6,
umbrella-contract's "money-shot" step 7: "sửa instructions tệ → verdict FAIL → chặn publish +
rollback") — SWE's publish/rollback pipeline reads this field and blocks + rolls back, never
advisory-only. This module produces the verdict; it does NOT wire the publish/rollback gate itself
(that stays SWE's ownership, R-SPEC A4).

Body intentionally empty (`NotImplementedError`) — this is the OJT spec surface for AIE-2 to fill.
"""

from __future__ import annotations

from collections.abc import Collection

from studio_contracts import Aggregate, CaseResult, Gate, GateThreshold, Scorecard


def compute_scorecard(
    agent_id: str,
    golden_set_ref: str,
    results: list[CaseResult],
    threshold_success: float,
    threshold_citation_accuracy: float,
    *,
    scored_case_ids: Collection[str],
) -> Scorecard:
    """Gộp `results` (một phần tử/case) thành `Scorecard` + quyết `gate.verdict`.

    **Hai mẫu số KHÁC NHAU, và đó là toàn bộ nội dung của hàm này** (`DEC-04`):

    - `success_rate` = `k_success / len(results)` — **mọi** case, kể cả từ-chối. Case từ-chối có
      `success` thật (agent từ chối đúng hay không), nên loại nó khỏi đây là bỏ mất phép đo.
    - `citation_accuracy` = `Σ acc / n_scored` với `n_scored` = **chỉ case nhánh trả-lời**. Case
      từ-chối mang `citation_accuracy = 1.0` như một **quy ước vacuous-truth** (`harness.py:185`),
      không phải một phép đo — thả nó vào mẫu số là kéo điểm lên giả.

    Con số làm việc phân biệt này khẩn, không phải sạch sẽ lý thuyết: bộ 10 báo `0.90` trong khi số
    thật là `0.833`, và `10×1.0 + 20×0.85 = đúng 0.90` ⇒ **một bản đáng FAIL lại PASS ngay ngưỡng
    `0.9`**. Golden-30 có 8/30 = 26.7% refusal — cùng lớp sai số, quy mô lớn hơn.

    **`scored_case_ids` — vì sao caller phải nói, không phải hàm này tự suy** (`DEC-D16-03`, đường
    (b)): `CaseResult` **không mang cờ nhánh** (`contracts/scorecard.py:22-30`), nên hàm này cấu trúc
    mà nói không biết case nào là từ-chối. Ba đường suy đều sai:

    - suy từ `citation_accuracy == 1.0` ⇒ **CẤM** — `expected_citation == []` ở nhánh **trả-lời**
      cũng ra `1.0` (`harness.py:180`). Suy một cờ ngữ nghĩa từ một giá trị số là đúng lớp lỗi
      breakpoint `#14`, và nó **xanh-giả**: không lỗi nào nổi lên, chỉ có một con số sai.
    - thêm cờ vào `CaseResult` ⇒ required-add = breaking contract, không cần cho hôm nay.
    - truyền **số đếm** `n_scored: int` ⇒ không đủ: nó sửa được mẫu số nhưng **tử số** vẫn phải biết
      cộng những case nào (đo thật: 2 refusal `1.0` + 8 trả-lời `0.85`, cộng cả 10 rồi chia 8 ra
      `1.1`, chia 10 ra `0.88`, chỉ cộng đúng 8 case mới ra `0.85`).

    Caller **biết** nhánh vì nó cầm `GoldenCase`: `{c.case_id for c in golden.cases if not
    c.expects_refusal}`.

    **Tử số và mẫu số lấy từ CÙNG một danh sách đã lọc** — `n_scored = len(scored)`, tuyệt đối không
    `len(scored_case_ids)`. Hai nguồn khác nhau cho hai vế của một phép chia là đúng chỗ một mutant
    sống được: đổi một vế mà vế kia không đổi thì con số lệch, và không assert nào bắt được nếu bài
    test cũng đọc mẫu số từ nguồn thứ hai đó.

    **Fail-closed:** `scored_case_ids` chứa id không có trong `results` ⇒ `raise`. Bỏ qua im lặng là
    cách một bộ case lệch (typo, sai bộ, harness lọc nhầm) đi thẳng vào một `verdict` trông bình
    thường.

    **`results` rỗng ⇒ `raise`**, không phải `success_rate = 0.0`. Cùng luật fail-closed với
    `tenant_scope_ok` (`harness.py:130`): không có case nào thì không có gì được chứng minh, và một
    `Scorecard` dựng trên 0 case là một verdict về không-cái-gì. Chỗ này không có trong `DEC-04` vì
    `DEC-04` mô tả công thức, không mô tả ca `n = 0` của trục `success` — nên nó đi theo cùng hướng
    đã chốt cho trục citation ở `DEC-D16-03` thay vì tự chọn một mặc định êm tai.
    """
    if not results:
        raise ValueError(
            "compute_scorecard: results rỗng — không có case nào thì không chứng minh được gì. "
            "Một Scorecard trên 0 case là một verdict về không-cái-gì (fail-closed)."
        )

    ids_co_that = {r.case_id for r in results}
    thieu = sorted(set(scored_case_ids) - ids_co_that)
    if thieu:
        raise ValueError(
            f"compute_scorecard: scored_case_ids chứa id không có trong results: {thieu}. "
            "Bỏ qua im lặng sẽ làm mẫu số citation nhỏ hơn ý định mà không ai biết (fail-closed)."
        )

    # MỘT danh sách, hai vế của phép chia. Tách nguồn ở đây là chỗ mutant sống được.
    scored = [r for r in results if r.case_id in scored_case_ids]
    n_scored = len(scored)

    success_rate = sum(1 for r in results if r.success) / len(results)
    citation_accuracy = sum(r.citation_accuracy for r in scored) / n_scored if n_scored else None

    dat_success = success_rate >= threshold_success
    # `citation_accuracy is None` ⇒ trục này CHƯA ĐƯỢC ĐO ⇒ không đạt. Viết tường minh thay vì dựa
    # vào so sánh với None (Python 3 raise TypeError) — để ý định đọc được, không phải một tác dụng
    # phụ của kiểu.
    dat_citation = citation_accuracy is not None and citation_accuracy >= threshold_citation_accuracy

    return Scorecard(
        agent_id=agent_id,
        golden_set_ref=golden_set_ref,
        results=list(results),
        aggregate=Aggregate(success_rate=success_rate, citation_accuracy=citation_accuracy),
        gate=Gate(
            threshold=GateThreshold(success=threshold_success, citation_accuracy=threshold_citation_accuracy),
            verdict="PASS" if (dat_success and dat_citation) else "FAIL",
        ),
        # `recipe_hash` chưa có producer (`DEC-03`) ⇒ `None` là giá trị trung thực duy nhất hôm nay.
        # Fail-closed nằm ở consumer publish, không ở đây.
    )
