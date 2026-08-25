"""Chọn bộ **Core** — tập con mà cổng Publish chạy trong một request.

## Vì sao cần, và vì sao là bây giờ

`GoldenCase.tier` khai từ lâu: *"Core (chạy lúc gate Publish) hay Full (chạy nền)"*, kèm con số
trong docstring của chính nó — *"Bộ Core 30–50 case chạy ~20–30s; chạy đủ 100–500 case mất 5–10
phút ⇒ spinner treo hoặc HTTP 504"*. Nhưng **không dòng nào đọc `tier`**: `EvalHarness.run()` chạy
**toàn bộ** `golden.cases`.

Chừng nào bộ golden còn là 30 case viết tay thì đó là nợ tương lai. Từ khi golden set **sinh lúc
upload** (`kb#61`/`app#61`), kích thước bộ **scale theo corpus của khách hàng**: 800 chunk ⇒ 155
case; vài nghìn chunk ⇒ vài trăm. Cổng chạy cả bộ trong một request, nên nó thành nợ của **khách
hàng thứ hai**, không phải của tương lai.

## Vì sao Core phải được TÍNH, không phải chỉ lọc `tier == "core"`

Đo trên cả hai loại bộ đang tồn tại:

| bộ | `tier="core"` | trong đó case **trả-lời** |
|---|---|---|
| sinh máy (800 chunk ⇒ 155 case) | 39 | **0** |
| người viết (`callisto-2.0-golden-30-v1`, 30 case) | **0** (không case nào khai `tier`) | — |

Lọc thẳng `tier == "core"` hỏng ở **cả hai**, theo hai kiểu ngược nhau:

- **bộ sinh máy**: `build_cases` gán `core` cho **đúng case bẫy**, nên cổng sẽ đo *"có từ chối đúng
  không"* và **không bao giờ** đo chất lượng trả lời. `success_rate` vẫn ra một con số — con số của
  một trục khác.
- **bộ người viết**: 0 case khai `tier` ⇒ Core **rỗng** ⇒ cổng chấm trên mẫu số 0.

Nên module này **tính** Core từ hai trục đã khai, thay vì tin rằng chúng đã được khai đủ.

## Luật chọn — ba tầng, theo thứ tự

1. **Mọi case đã khai `is_critical` hoặc `tier="core"` đều vào, không ngoại lệ.** Đây là tầng
   không thương lượng: `is_critical` khai *"sai case này thì cả lượt chấm hỏng"*, nên cắt nó cho vừa
   ngân sách là bỏ đúng thứ ngân sách tồn tại để bảo vệ. Nếu riêng tầng này đã vượt `max_cases` thì
   Core **vượt ngân sách** và `CoreSelection.vuot_ngan_sach` khai ra điều đó.
2. **Bảo đảm tối thiểu `min_answer` case trả-lời.** Không có tầng này, một bộ mà tầng 1 đã lấp đầy
   ngân sách sẽ cho cổng chỉ đo trục từ-chối — đúng ca *"bộ sinh máy"* ở bảng trên.
3. **Lấp phần còn lại theo thứ tự gốc** cho tới `max_cases`.

Thứ tự gốc, không lấy mẫu ngẫu nhiên: cùng bộ vào phải cho cùng Core ra. Một Core nhảy giữa hai
lượt nghĩa là hai lần bấm Publish trên cùng dữ liệu chấm trên hai tập khác nhau, và chênh lệch đó
không phân biệt được với chênh lệch do agent.

## Vì sao RAISE khi Core không đo được cả hai trục

`CoreSelectionError` thay vì trả một bộ lệch kèm cảnh báo: cổng Publish là **fail-closed**
(`INV-6`), và một `success_rate` tính trên tập chỉ-toàn-bẫy hoặc tập rỗng là *"một giá trị trông
hợp lệ"* — đúng thứ `GoldenSetNotFound`/`UnscopedReadUnavailable` được dựng ra để từ chối. Khác
`sample_report` (`studio_kb`) cố ý **báo cáo, không raise**: cái đó mô tả một bộ để người đọc quyết,
còn cái này sinh ra chính tập mà cổng sẽ chấm.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from studio_evalhub.golden_case import GoldenCase, GoldenSet

DEFAULT_MAX_CASES = 40
"""Trần mặc định. Bám khoảng 30–50 mà docstring `GoldenCase.tier` đã khai (~20–30s), lấy giữa."""

DEFAULT_MIN_ANSWER = 10
"""Số case trả-lời tối thiểu để `success_rate` nói được điều gì về chất lượng trả lời.

10 chứ không 1: với 1 case, `success_rate` của trục trả-lời chỉ nhận hai giá trị (0 hoặc 1) và một
lượt LLM dao động là lật hẳn cổng. 10 cho bước nhảy 0.1 — vẫn thô, nhưng đã là một thang đo."""


class CoreSelectionError(ValueError):
    """Core chọn ra không đo được đủ hai trục — cổng chạy nó sẽ trả một con số của trục khác."""


@dataclass(frozen=True, slots=True)
class CoreSelection:
    """Bộ Core kèm **cách nó được chọn** — không chỉ kết quả.

    Người đọc scorecard cần biết cổng vừa chấm trên bao nhiêu case và vì sao đúng những case đó;
    một `GoldenSet` trần không trả lời được câu nào trong hai câu.
    """

    golden: GoldenSet
    n_declared: int
    """Case vào vì đã khai `is_critical`/`tier="core"` — tầng không thương lượng."""
    n_answer: int
    n_refusal: int
    over_budget: bool
    """`True` khi Core lớn hơn `max_cases` vì tầng 1 hoặc tầng 2 đòi. Không phải lỗi — là đánh đổi
    đã khai: thà chạy lâu hơn ngân sách còn hơn bỏ một case `is_critical`."""


def _declared_core(case: GoldenCase) -> bool:
    return case.is_critical is True or case.tier == "core"


def select_core(
    golden: GoldenSet,
    *,
    max_cases: int = DEFAULT_MAX_CASES,
    min_answer: int = DEFAULT_MIN_ANSWER,
) -> CoreSelection:
    """Chọn bộ Core cho cổng Publish. Xem docstring module cho luật ba tầng.

    Raises:
        CoreSelectionError: Core rỗng, hoặc không đủ `min_answer` case trả-lời **kể cả sau khi đã
            lấy hết** case trả-lời có trong bộ. Ca sau nghĩa là bản thân bộ golden thiếu trục
            trả-lời, không phải luật chọn sai — thông điệp nói rõ để người sửa đi đúng chỗ.
    """
    if max_cases < 1:
        raise ValueError(f"select_core: max_cases phải ≥ 1, nhận {max_cases}")
    # `min_answer < 1` làm điều kiện `n_answer < min_answer` ở cuối hàm không bao giờ đúng được,
    # tức tắt hẳn cái chốt fail-closed mà cả module này dựng lên — một Core 0 case trả-lời sẽ đi
    # lọt và `success_rate` báo về trục từ-chối. `select_core` là symbol công khai
    # (`studio_evalhub.select_core`), không chỉ tới qua `EvalHarness.run`, nên phải tự chặn ở đây.
    if min_answer < 1:
        raise ValueError(f"select_core: min_answer phải ≥ 1, nhận {min_answer}")

    # Chọn theo **chỉ số**, không theo `case_id`: `GoldenSet` không ép `case_id` duy nhất (xem
    # `golden_merge.py` — bộ sinh máy và bộ người nộp đặt id độc lập nhau nên đụng được). Lọc lại
    # bằng `case_id in đã_chọn` sẽ kéo theo MỌI case trùng id, kể cả case chưa hề được chọn: một
    # case từ-chối đã khai `is_critical` và một case trả-lời trùng id sẽ cùng lọt vào Core, ngân
    # sách `max_cases` đo trên số đã chọn còn bộ phát ra thì lớn hơn. Chỉ số cũng là nguồn sự thật
    # DUY NHẤT ở đây — không còn cặp `list`/`set` phải giữ đồng bộ bằng tay qua ba tầng.
    declared = [i for i, c in enumerate(golden.cases) if _declared_core(c)]
    rest = [i for i, c in enumerate(golden.cases) if not _declared_core(c)]

    selected: set[int] = set(declared)
    n_answer_selected = sum(1 for i in declared if not golden.cases[i].expects_refusal)

    # Tầng 2 trước tầng 3: bảo đảm trục trả-lời đo được, kể cả khi tầng 1 đã lấp đầy ngân sách.
    for i in rest:
        if n_answer_selected >= min_answer:
            break
        if not golden.cases[i].expects_refusal:
            selected.add(i)
            n_answer_selected += 1

    for i in rest:
        if len(selected) >= max_cases:
            break
        selected.add(i)

    # Giữ thứ tự GỐC của bộ, không phải thứ tự nhặt: hai bộ Core cùng nội dung mà khác thứ tự sẽ
    # cho `Scorecard.results` khác nhau về hình thức, và người đọc không phân biệt được với đổi thật.
    chosen = [golden.cases[i] for i in sorted(selected)]
    n_answer = sum(1 for c in chosen if not c.expects_refusal)

    # `case_id` trùng trong Core là bộ KHÔNG chấm đúng được, nên chặn ở đây chứ không để trôi:
    # `EvalHarness.run` chỉ thêm case **không từ-chối** vào `scored_case_ids`, nhưng
    # `compute_scorecard` lọc bằng `r.case_id in scored_case_ids` — nên `CaseResult` của một case
    # từ-chối trùng id bị kéo vào mẫu `citation_accuracy` của nhánh trả-lời và làm hỏng chính con
    # số cổng đọc. `GoldenSet` không ép id duy nhất (bộ sinh máy và bộ người nộp đặt id độc lập,
    # xem `golden_merge.py`), nên chỗ duy nhất chặn được là ngay trước khi giao tập cho cổng.
    # `Counter` chứ không `sum()` lồng trong comprehension: bản đầu là O(n²), và hàm này chạy
    # trong ngân sách thời gian của cổng Publish (review evalhub#52, Dozyboy).
    duplicates = sorted(case_id for case_id, n in Counter(c.case_id for c in chosen).items() if n > 1)
    if duplicates:
        raise CoreSelectionError(
            f"select_core: Core của {golden.golden_set_ref!r} có case_id trùng: {duplicates}. "
            f"Cổng chấm hai nhánh luật khác nhau theo `expects_refusal` nhưng gộp kết quả theo "
            f"`case_id`, nên hai case cùng id sẽ trộn nhánh từ-chối vào mẫu citation của nhánh "
            f"trả-lời. Sửa ở bộ golden (đặt lại id), không phải ở luật chọn"
        )

    if not chosen:
        raise CoreSelectionError(
            f"select_core: bộ {golden.golden_set_ref!r} không chọn được case nào cho Core "
            f"(bộ có {len(golden.cases)} case) — cổng sẽ chấm trên mẫu số 0"
        )
    if n_answer < min_answer:
        total_answer = sum(1 for c in golden.cases if not c.expects_refusal)
        raise CoreSelectionError(
            f"select_core: Core của {golden.golden_set_ref!r} chỉ có {n_answer} case trả-lời, cần "
            f"≥{min_answer}. Cả bộ chỉ có {total_answer} case trả-lời trên tổng {len(golden.cases)} "
            f"— thiếu ở chính bộ golden, không phải ở luật chọn. `success_rate` tính trên Core này "
            f"sẽ nói về trục từ-chối, không phải chất lượng trả lời"
        )

    return CoreSelection(
        golden=GoldenSet(golden_set_ref=golden.golden_set_ref, cases=chosen),
        n_declared=len(declared),
        n_answer=n_answer,
        n_refusal=len(chosen) - n_answer,
        over_budget=len(chosen) > max_cases,
    )
