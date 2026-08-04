"""Render `Scorecard` cho người đọc — AIE-2 (D12, `kit#88` *"scorecard skeleton render trống"*).

Module này **chỉ hiển thị**. Nó KHÔNG tính điểm, KHÔNG gọi `compute_scorecard`, KHÔNG quyết
`gate.verdict`. Lý do là một quyết định có ghi, không phải sự tiện tay:

- **Chưa có golden-set thật** (`kit#88` nói thẳng vậy) và `compute_scorecard` là mốc **D16**
  (`kit#108`) — nó còn `raise NotImplementedError` (`compute.py:30`). Gọi nó ở đây là ship một
  deliverable D16 sớm, và làm `test_gate_blocks_on_fail` (`xfail(strict=True)`) **XPASS ⇒ FAIL**
  trong lúc quyền đổi marker (M6) mới chỉ có ADR **dự kiến** viết ở D16.
- GUIDE-C §3.2 đòi ngưỡng literal phải **có trước** dataset. Khoá trước **hình dạng output** khi chưa
  có số là cách duy nhất để D16 chỉ còn việc đổ số vào một khung đã có test.

**Luật số một của file này (DEC-D12-02): ô chưa đo được in `todo:`, KHÔNG in `0.00`.**
`0.00` đọc thành *"đã đo, và bằng 0"* ⇒ ai xem demo sẽ tưởng gate đang chặn. Đó là **cùng một lớp
lỗi** với hằng số `Judge(agreement=1.0)` mà `judge.py:6-9` cấm và §1 hợp đồng khoá: một ô không đo
được được điền một giá trị đọc-được-thành-đã-đo. `kit#134` nói đúng cùng chuyện ở mức thống kê — chỗ
hỏng không nằm ở probe, nằm ở **bước từ "8/10" sang "80%"**.
"""

from __future__ import annotations

from studio_contracts import Scorecard

_TODO = "todo:"
_LABEL_W = 22

_WHY_EMPTY = (
    "Vì sao trống: chưa có golden-set thật (kit#88; golden-30 về D15–16, phải sinh SAU corpus "
    "cutover D13). `compute_scorecard` là mốc D16 (kit#108) và vẫn NotImplementedError ⇒ khung này "
    "cố ý KHÔNG tự tính gì. Mọi ô chưa đo được in `todo:`, không in một số 0 giả (DEC-D12-02) — "
    "một số 0 đọc được thành 'đã đo, và bằng 0'."
)

_AGGREGATE_NOT_RECOMPUTABLE = (
    "* `aggregate` KHÔNG tính lại được từ `results` đã lưu: `CaseResult` không mang cờ nhánh "
    "từ-chối, nên ở tầng hợp đồng không phân biệt được `citation_accuracy = 1.0` là *quy ước "
    "vacuous-truth* hay *phép đo thật* ⇒ số in ra là số của `aggregate`, không phải số dựng lại. "
    "Cách biểu diễn (nullable vs thêm `n_scored_citation`) là nợ có chủ: AIE-2, hạn D16 (DEC-04)."
)


def _row(label: str, value: str) -> str:
    return f"{label:<{_LABEL_W}} {value}"


def render_scorecard(scorecard: Scorecard | None, *, golden_set_ref: str | None = None) -> str:
    """Bảng `Scorecard` cho người đọc; `None` ⇒ **khung trống có `todo:`**, không phải bảng số 0.

    `scorecard is None` là trạng thái **thật của hôm nay**, không phải trạng thái lỗi: chưa có
    golden-set thật và `compute_scorecard` chưa hiện thực. Khung vẫn in đủ **tên** mọi ô mà D16 phải
    điền — `success_rate` · `citation_accuracy` · `gate.threshold` · `gate.verdict` · `recipe_hash` —
    để hình dạng output được khoá bằng test **trước** khi có dataset (GUIDE-C §3.2).

    `golden_set_ref` chỉ dùng cho nhánh trống (khi có `scorecard` thì lấy từ chính nó).
    """
    header = "SCORECARD — " + (
        scorecard.golden_set_ref if scorecard is not None else (golden_set_ref or "(chưa có golden-set)")
    )
    rule = "-" * max(len(header), 78)
    lines = [header, rule]

    if scorecard is None:
        lines += [
            _row("agent_id", _TODO),
            _row("case đã chấm", "0 — chưa có golden-set thật"),
            rule,
            _row("aggregate.success_rate", _TODO),
            _row("aggregate.citation_accuracy", _TODO),
            _row("gate.threshold", _TODO),
            _row("gate.verdict", _TODO),
            _row("recipe_hash", _TODO + " (publish coi None là 'không verify được ⇒ từ chối')"),
            rule,
            _WHY_EMPTY,
        ]
        return "\n".join(lines)

    lines += [
        _row("agent_id", scorecard.agent_id),
        _row("case đã chấm", str(len(scorecard.results))),
        rule,
        _row("aggregate.success_rate", f"{scorecard.aggregate.success_rate:.2f}"),
        _row("aggregate.citation_accuracy", f"{scorecard.aggregate.citation_accuracy:.2f}*"),
        _row(
            "gate.threshold",
            f"success >= {scorecard.gate.threshold.success:.2f} AND "
            f"citation_accuracy >= {scorecard.gate.threshold.citation_accuracy:.2f}",
        ),
        _row("gate.verdict", scorecard.gate.verdict),
        _row(
            "recipe_hash",
            scorecard.recipe_hash
            if scorecard.recipe_hash is not None
            else _TODO + " (None ⇒ publish từ chối, fail-closed)",
        ),
        rule,
        _AGGREGATE_NOT_RECOMPUTABLE,
    ]
    return "\n".join(lines)
