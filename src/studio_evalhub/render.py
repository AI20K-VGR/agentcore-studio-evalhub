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

from studio_evalhub.harness import SmokeResult

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


RUN_CASE_COLUMNS: tuple[str, ...] = ("case_id", "expects_refusal", "success", "citation_accuracy")
"""Field của `SmokeResult` **có** lên bảng per-case, theo đúng thứ tự cột."""

RUN_CASE_FIELDS_NOT_SHOWN: tuple[str, ...] = ("expected", "actual")
"""Field của `SmokeResult` **cố ý không** lên bảng: hai trường văn bản dài, in ra sẽ vỡ hàng và đẩy
các cột số ra khỏi tầm mắt. Chúng vẫn nằm nguyên trên object cho ai cần đọc chi tiết.

Hai tuple trên phải **phủ kín** `SmokeResult.model_fields` — có test cưỡng chế bằng code (H5), không
bằng lời. Thêm field thứ 7 mà quên khai vào một trong hai tuple ⇒ đỏ ngay, và người thêm buộc phải
quyết một cách có ý thức thay vì để nó rơi im lặng. Đây là đúng cái bẫy đã dính ở D12 khi
`expects_refusal` (field thứ 6) được thêm vào mà danh sách trong test còn gõ tay."""

_NOT_ESTIMABLE = "not-estimable"

_FIXED_SET_CAVEAT = (
    "Đây là đếm thô trên một fixed-set, chưa phải population estimate: không suy ra tỷ lệ tổng, "
    "không suy ra ngưỡng, không suy ra khoảng tin cậy từ mấy dòng trên."
)

_WHY_RAW_COUNT = (
    "* Vì sao chỉ `k/n` mà không có tỷ lệ tổng (DEC-D15-02): mẫu số citation phải tách riêng và "
    "loại refusal (DEC-S2-134-03), mà `Aggregate` hôm nay chưa có chỗ cho `n_scored_citation` — "
    "nợ có chủ: AIE-2, hạn D16 (DEC-04). In một tỷ lệ tổng khi chưa tách mẫu số là đúng lỗi kit#134 "
    "mô tả: chỗ hỏng không nằm ở probe, nằm ở bước từ `8/10` sang tám-mươi-phần-trăm."
)

_WHY_NA = (
    "* `n/a` = nhánh từ-chối: `citation_accuracy` ở nhánh này là quy ước vacuous-truth (giá trị "
    "trên object vẫn là 1.0), KHÔNG phải phép đo ⇒ không vào tử số cũng không vào mẫu số (DEC-04)."
)


def _count_or_not_estimable(k: int, n: int) -> str:
    """`k/n` thô khi `n > 0`; `n = 0` ⇒ `not-estimable`, KHÔNG phải `0/0` và KHÔNG phải một số 0.

    `0/0` vẫn mời người đọc chia — và phép chia đó không tồn tại. `kit#134`: `n = 0` không cho ra
    ước lượng nào cả, nên thứ trung thực duy nhất in được ở đó là nói thẳng rằng chưa đo được."""
    if n == 0:
        return f"{_NOT_ESTIMABLE} (n = 0)"
    return f"{k}/{n}"


def render_run_cases(
    results: list[SmokeResult],
    *,
    run_id: str,
    golden_set_ref: str,
    trace_source: str,
) -> str:
    """Bảng per-case với số **THẬT** của một run có thật — deliverable D15 (`kit#103`, dòng 🎯).

    Khác `render_scorecard`: hàm kia in khung `todo:` vì chưa có golden-set và `compute_scorecard`
    chưa hiện thực. Ở đây `results` đã là kết quả `score_case` chấm trên `citations_from_trace(...)`
    của một run có `run_id`, nên `todo:` sẽ là nói dối theo chiều ngược lại — trình bày một ô **đã**
    đo được như thể chưa đo.

    Ba metadata đều bắt buộc, không có default:

    - `run_id` — không có nó thì bảng này không truy về được run nào, và câu *"đọc trace của run
      thật"* không kiểm chứng được;
    - `golden_set_ref` — bộ case nào sinh ra mấy dòng này;
    - `trace_source` — trace đọc từ đâu (Postgres bền hoá vs run live). Cùng một `run_id` đọc từ hai
      nguồn khác nhau là hai phép đo khác nhau, và D14 đã trả giá một lần vì trộn *static fixed-set*
      với *current PG measurement* trong cùng một câu.

    **KHÔNG gọi `compute_scorecard`** (mốc D16, `kit#108` — nó còn `NotImplementedError`) và không
    dựng `gate`. Hàm này chỉ hiển thị thứ caller đã tính; nó không tính gì và không đổi gì trên
    `results`.

    **Chỉ in `k/n` thô** (DEC-D15-02) với **hai mẫu số tách rời**:

    - success: `n` = mọi case;
    - citation: `n` = chỉ case nhánh **trả-lời** (`DEC-S2-134-03` loại refusal khỏi mẫu số), `k` =
      số case trả-lời có `citation_accuracy == 1.0`, tức trích **đủ** chunk kỳ vọng. Case đạt một
      phần (`0.5`) không vào tử số; số per-case của nó vẫn in ra ở bảng trên để người đọc thấy phần
      đạt, chứ không bị một dòng đếm thô nuốt mất.
    """
    header = f"RUN CASES — {run_id}"
    rule = "-" * max(len(header), 78)
    col = f"{'case_id':<20} {'expects_refusal':<16} {'success':<8} {'citation_accuracy':>18}"

    lines = [
        header,
        rule,
        _row("golden_set_ref", golden_set_ref),
        _row("trace_source", trace_source),
        rule,
        col,
        "-" * len(col),
    ]

    for r in results:
        branch = "từ-chối" if r.expects_refusal else "trả-lời"
        acc = f"{'n/a':>18}" if r.expects_refusal else f"{r.citation_accuracy:>18.2f}"
        lines.append(f"{r.case_id:<20} {branch:<16} {('PASS' if r.success else 'FAIL'):<8} {acc}")

    answerable = [r for r in results if not r.expects_refusal]
    n_success = len(results)
    k_success = sum(1 for r in results if r.success)
    n_citation = len(answerable)
    k_citation = sum(1 for r in answerable if r.citation_accuracy == 1.0)

    lines += [
        "-" * len(col),
        _row("success (k/n thô)", _count_or_not_estimable(k_success, n_success)),
        _row(
            "citation (k/n thô)",
            _count_or_not_estimable(k_citation, n_citation) + "  — mẫu số đã loại refusal",
        ),
        rule,
        _FIXED_SET_CAVEAT,
        _WHY_RAW_COUNT,
        _WHY_NA,
    ]
    return "\n".join(lines)


def _row(label: str, value: str) -> str:
    return f"{label:<{_LABEL_W}} {value}"


def render_scorecard(scorecard: Scorecard | None, *, golden_set_ref: str | None = None) -> str:
    """Bảng `Scorecard` cho người đọc; `None` ⇒ **khung trống có `todo:`**, không phải bảng số 0.

    `scorecard is None` là trạng thái **thật của hôm nay**, không phải trạng thái lỗi: chưa có
    golden-set thật và `compute_scorecard` chưa hiện thực. Khung vẫn in đủ **tên** mọi ô mà D16 phải
    điền — `success_rate` · `citation_accuracy` · `n_scored_citation` · `gate.threshold` ·
    `gate.verdict` · `recipe_hash` — để hình dạng output được khoá bằng test **trước** khi có dataset
    (GUIDE-C §3.2).

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
            # Mẫu số của trục citation. Ô này có tên ở khung trống TRƯỚC khi có số, đúng lý do khung
            # trống tồn tại: hình dạng output khoá bằng test trước khi có dataset. `citation_accuracy`
            # mà không kèm mẫu số là thứ `kit#134` xếp vào evidence malformed — hai ô phải đọc cùng
            # nhau, nên chúng phải cùng xuất hiện, kể cả khi cả hai còn `todo:`.
            _row("aggregate.n_scored_citation", _TODO + " (mẫu số trục citation)"),
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
