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
    vuot_ngan_sach: bool
    """`True` khi Core lớn hơn `max_cases` vì tầng 1 hoặc tầng 2 đòi. Không phải lỗi — là đánh đổi
    đã khai: thà chạy lâu hơn ngân sách còn hơn bỏ một case `is_critical`."""


def _da_khai_core(case: GoldenCase) -> bool:
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

    declared = [c for c in golden.cases if _da_khai_core(c)]
    con_lai = [c for c in golden.cases if not _da_khai_core(c)]
    tra_loi_con_lai = [c for c in con_lai if not c.expects_refusal]

    chon: list[GoldenCase] = list(declared)
    da_chon = {c.case_id for c in chon}

    # Tầng 2 trước tầng 3: bảo đảm trục trả-lời đo được, kể cả khi tầng 1 đã lấp đầy ngân sách.
    thieu = min_answer - sum(1 for c in chon if not c.expects_refusal)
    for c in tra_loi_con_lai:
        if thieu <= 0:
            break
        chon.append(c)
        da_chon.add(c.case_id)
        thieu -= 1

    for c in con_lai:
        if len(chon) >= max_cases:
            break
        if c.case_id not in da_chon:
            chon.append(c)
            da_chon.add(c.case_id)

    # Giữ thứ tự GỐC của bộ, không phải thứ tự nhặt: hai bộ Core cùng nội dung mà khác thứ tự sẽ
    # cho `Scorecard.results` khác nhau về hình thức, và người đọc không phân biệt được với đổi thật.
    theo_goc = [c for c in golden.cases if c.case_id in da_chon]
    n_tra_loi = sum(1 for c in theo_goc if not c.expects_refusal)

    if not theo_goc:
        raise CoreSelectionError(
            f"select_core: bộ {golden.golden_set_ref!r} không chọn được case nào cho Core "
            f"(bộ có {len(golden.cases)} case) — cổng sẽ chấm trên mẫu số 0"
        )
    if n_tra_loi < min_answer:
        tong_tra_loi = sum(1 for c in golden.cases if not c.expects_refusal)
        raise CoreSelectionError(
            f"select_core: Core của {golden.golden_set_ref!r} chỉ có {n_tra_loi} case trả-lời, cần "
            f"≥{min_answer}. Cả bộ chỉ có {tong_tra_loi} case trả-lời trên tổng {len(golden.cases)} "
            f"— thiếu ở chính bộ golden, không phải ở luật chọn. `success_rate` tính trên Core này "
            f"sẽ nói về trục từ-chối, không phải chất lượng trả lời"
        )

    return CoreSelection(
        golden=GoldenSet(golden_set_ref=golden.golden_set_ref, cases=theo_goc),
        n_declared=len(declared),
        n_answer=n_tra_loi,
        n_refusal=len(theo_goc) - n_tra_loi,
        vuot_ngan_sach=len(theo_goc) > max_cases,
    )
