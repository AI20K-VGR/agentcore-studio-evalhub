"""Test `compute_scorecard` — hai mẫu số tách rời + `gate.verdict`.

KHÓA `DEC-04` (ba tầng) và `DEC-D16-03`:

- `success_rate` đếm **mọi** case (refusal có `success` thật)
- `citation_accuracy` chỉ đếm **case nhánh trả-lời** — refusal mang `1.0` là **quy ước
  vacuous-truth**, không phải phép đo
- mẫu số citation `== 0` ⇒ `citation_accuracy = None` **và** `verdict = "FAIL"` (*không đo được thì
  không PASS được*)
- ngưỡng so bằng `>=`, không `>`

Bài đắt nhất trong file là bài đầu. Nó dựng lại **đúng con số đã đo được** ở `DEC-04`: một bộ mà
mẫu số sai làm điểm nhích lên vừa đủ để một bản đáng FAIL thành PASS. Mọi bài còn lại là hàng rào
quanh nó.
"""

from __future__ import annotations

import pytest
from studio_contracts import CaseResult
from studio_evalhub.compute import compute_scorecard

_TS = 0.9
_TC = 0.95


def _case(case_id: str, *, success: bool, acc: float) -> CaseResult:
    """`CaseResult` tối thiểu — chỉ 3 field bộ gộp đọc mới quan trọng (`case_id`, `success`,
    `citation_accuracy`). `judge=None` là giá trị đúng cho case exact-match/refusal (`DEC-02`)."""
    return CaseResult(case_id=case_id, expected="x", actual="x", success=success, citation_accuracy=acc)


def _bo_10_case() -> tuple[list[CaseResult], set[str]]:
    """Bộ dựng lại đúng hình dạng đã đo ở `DEC-04`: **2 từ-chối (`1.0` quy ước) + 8 trả-lời (`0.85`)**.

    Bất đối xứng có chủ đích (2/8, không 5/5): tỷ lệ cân là chỗ một mutant đảo mẫu số vẫn cho ra
    cùng con số. Ở đây ba cách tính ra ba số **khác nhau rõ rệt** — `0.85` (đúng), `0.88` (cộng cả
    refusal vào mẫu số), `1.1` (cộng cả refusal vào tử số nhưng chia mẫu số đúng)."""
    tra_loi = [_case(f"ANS-{i}", success=True, acc=0.85) for i in range(8)]
    tu_choi = [_case(f"REF-{i}", success=True, acc=1.0) for i in range(2)]
    results = [*tra_loi, *tu_choi]
    return results, {c.case_id for c in tra_loi}


def test_compute_loai_refusal_khoi_mau_so_citation() -> None:
    """**BÀI CHÍ TỬ.** 2 refusal `1.0` + 8 trả-lời `0.85` ⇒ `citation_accuracy == 0.85`, **không**
    `0.88`.

    `0.88` là con số một bộ gộp sai mẫu số sẽ in ra, và nó **không phân biệt được** với một phép đo
    thật — không exception, không cảnh báo, chỉ là một `Scorecard` cao hơn sự thật. `DEC-04` đo đúng
    chỗ này trên bộ 10: báo `0.90` trong khi thật là `0.833`.

    Assert cả `n_scored` gián tiếp qua giá trị: `6.8/8 = 0.85` chỉ ra được khi **cả tử số lẫn mẫu
    số** cùng loại refusal. Sai một trong hai vế cho ra `0.88` hoặc `1.1`."""
    results, scored = _bo_10_case()

    scorecard = compute_scorecard(
        agent_id="a",
        golden_set_ref="g",
        results=results,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        scored_case_ids=scored,
    )

    assert scorecard.aggregate.citation_accuracy == pytest.approx(0.85)
    assert scorecard.aggregate.citation_accuracy != pytest.approx(0.88)
    # Bộ đủ 10 case vẫn phải nằm nguyên trong scorecard — loại refusal khỏi MẪU SỐ, không khỏi kết quả.
    assert len(scorecard.results) == 10


def test_compute_success_rate_dem_moi_case() -> None:
    """`success_rate` **có** refusal trong mẫu số — ngược với `citation_accuracy`.

    Đây là vế còn lại của `DEC-04` và là chỗ dễ "sửa cho nhất quán" nhất: thấy citation loại refusal
    rồi loại luôn ở success. Case từ-chối có `success` **thật** (agent từ chối đúng hay không), nên
    loại nó là vứt đi 8/30 phép đo của golden-30.

    Dựng lệch có chủ đích: 6 trả-lời PASS + 2 trả-lời FAIL + 2 refusal PASS ⇒ `8/10 = 0.8`. Nếu mẫu
    số chỉ đếm nhánh trả-lời thì ra `6/8 = 0.75`; nếu tử số bỏ refusal thì ra `6/10 = 0.6`. Ba số
    tách nhau nên bài chỉ xanh khi cả hai vế đúng."""
    results = [
        *[_case(f"ANS-OK-{i}", success=True, acc=1.0) for i in range(6)],
        *[_case(f"ANS-BAD-{i}", success=False, acc=1.0) for i in range(2)],
        *[_case(f"REF-{i}", success=True, acc=1.0) for i in range(2)],
    ]
    scored = {r.case_id for r in results if r.case_id.startswith("ANS")}

    scorecard = compute_scorecard(
        agent_id="a",
        golden_set_ref="g",
        results=results,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        scored_case_ids=scored,
    )

    assert scorecard.aggregate.success_rate == pytest.approx(0.8)


def test_compute_verdict_pass_o_dung_bang_nguong() -> None:
    """Điểm **đúng bằng** ngưỡng ⇒ `PASS`. Khoá `>=`, không `>`.

    `DEC-04` đo đúng ca biên này: `10×1.0 + 20×0.85` ra **đúng** `0.90` ở ngưỡng `0.9`. Một `>` thay
    `>=` làm ca biên lật, và ca biên là ca duy nhất phân biệt hai toán tử — mọi bộ dữ liệu khác đều
    xanh với cả hai."""
    results = [
        *[_case(f"ANS-OK-{i}", success=True, acc=0.95) for i in range(9)],
        _case("ANS-BAD", success=False, acc=0.95),
    ]
    scored = {r.case_id for r in results}

    scorecard = compute_scorecard(
        agent_id="a",
        golden_set_ref="g",
        results=results,
        threshold_success=0.9,
        threshold_citation_accuracy=0.95,
        scored_case_ids=scored,
    )

    assert scorecard.aggregate.success_rate == pytest.approx(0.9)
    assert scorecard.aggregate.citation_accuracy == pytest.approx(0.95)
    assert scorecard.gate.verdict == "PASS"


def test_compute_verdict_fail_khi_chi_mot_truc_hut() -> None:
    """Hụt **một** trục là FAIL — kiểm **cả hai chiều**, vì `AND` → `OR` chỉ lộ ra ở một chiều.

    Một mutant đổi `AND` thành `OR` vẫn cho PASS đúng khi cả hai trục đạt và FAIL đúng khi cả hai
    trục hụt. Nó **chỉ** sai ở đúng hai ca lệch này — nên bài phải có cả hai, không chọn một."""
    # Chiều 1: success hụt (0.5 < 0.9), citation đạt (1.0 >= 0.95)
    hut_success = [
        _case("ANS-OK", success=True, acc=1.0),
        _case("ANS-BAD", success=False, acc=1.0),
    ]
    sc1 = compute_scorecard(
        agent_id="a",
        golden_set_ref="g",
        results=hut_success,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        scored_case_ids={r.case_id for r in hut_success},
    )
    assert sc1.aggregate.success_rate == pytest.approx(0.5)
    assert sc1.aggregate.citation_accuracy == pytest.approx(1.0)
    assert sc1.gate.verdict == "FAIL"

    # Chiều 2: success đạt (1.0 >= 0.9), citation hụt (0.5 < 0.95)
    hut_citation = [
        _case("ANS-A", success=True, acc=0.5),
        _case("ANS-B", success=True, acc=0.5),
    ]
    sc2 = compute_scorecard(
        agent_id="a",
        golden_set_ref="g",
        results=hut_citation,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        scored_case_ids={r.case_id for r in hut_citation},
    )
    assert sc2.aggregate.success_rate == pytest.approx(1.0)
    assert sc2.aggregate.citation_accuracy == pytest.approx(0.5)
    assert sc2.gate.verdict == "FAIL"


def test_compute_n_scored_citation_bang_0_thi_none_va_fail() -> None:
    """Golden toàn refusal ⇒ mẫu số citation `0` ⇒ **`citation_accuracy = None` + `verdict = FAIL`**.

    Ba kết cục sai phải chặn cùng lúc, và chúng khác nhau về bản chất:

    - `ZeroDivisionError` — hỏng to, dễ thấy, ít nguy hiểm nhất trong ba cái.
    - `1.0` — **vacuous PASS**: `0/0` được đọc là "hoàn hảo". Đây là kết cục nguy hiểm nhất vì nó
      cho ra một `verdict = PASS` trên một trục **chưa từng được đo**.
    - `0.0` — nói dối theo chiều ngược: đọc được là *"đo được, và bằng không"*, không phân biệt được
      với một bộ trích dẫn sai hoàn toàn.

    `None` là giá trị trung thực duy nhất, cùng luật với `not-estimable` của `render.py:76-83` và
    fail-closed của `tenant_scope_ok` (`harness.py:130`, `events` rỗng ⇒ `False`). Luật đã chốt ở
    **`DEC-D16-03`** khối *"Ca mẫu số rỗng"* — **không mở id mới cho ca này**.

    `success_rate` vẫn tính bình thường: refusal có `success` thật, nên trục đó **đo được**. Chỉ
    trục citation là không."""
    results = [_case(f"REF-{i}", success=True, acc=1.0) for i in range(4)]

    scorecard = compute_scorecard(
        agent_id="a",
        golden_set_ref="g",
        results=results,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        scored_case_ids=set(),
    )

    assert scorecard.aggregate.citation_accuracy is None
    assert scorecard.gate.verdict == "FAIL"
    # Không PASS được, kể cả khi trục kia hoàn hảo — đó là toàn bộ nội dung của "không đo được thì
    # không PASS được".
    assert scorecard.aggregate.success_rate == pytest.approx(1.0)


def test_compute_khong_doi_results_dau_vao() -> None:
    """Không mutate input — `results` của caller phải nguyên vẹn sau lời gọi.

    `CaseResult` là `frozen=True` nên không sửa được **từng phần tử**, nhưng chính `list` thì không
    frozen: một bản hiện thực lọc bằng `results.remove(...)` / `results.sort(...)` / `del` sẽ làm
    caller mất case mà `Scorecard` trả về vẫn trông đúng. So bằng **bản sao chụp trước**, không so
    độ dài."""
    results, scored = _bo_10_case()
    truoc = list(results)

    compute_scorecard(
        agent_id="a",
        golden_set_ref="g",
        results=results,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        scored_case_ids=scored,
    )

    assert results == truoc
    assert [r.case_id for r in results] == [r.case_id for r in truoc]


def test_compute_scored_id_khong_co_trong_results_thi_raise() -> None:
    """Fail-closed: `scored_case_ids` chứa id **không tồn tại** trong `results` ⇒ `raise`.

    Bỏ qua im lặng là cách một bộ lệch (typo, sai bộ case, harness lọc nhầm) đi thẳng vào một
    `verdict` trông bình thường: mẫu số nhỏ hơn ý định mà không ai biết, và điểm citation được tính
    trên một tập con tuỳ tiện.

    Bài này không nằm trong 6 acceptance gốc — nó là hàng rào của chính chữ ký (A), thêm vào vì
    `Collection[str]` cho phép trạng thái đó tồn tại. Không có nó thì lỗ hổng duy nhất của (A) không
    có lưới."""
    results = [_case("ANS-1", success=True, acc=1.0)]

    with pytest.raises(ValueError) as excinfo:
        compute_scorecard(
            agent_id="a",
            golden_set_ref="g",
            results=results,
            threshold_success=_TS,
            threshold_citation_accuracy=_TC,
            scored_case_ids={"ANS-1", "KHONG-CO-THAT"},
        )

    assert "KHONG-CO-THAT" in str(excinfo.value)


def test_mau_so_citation_duoc_mang_theo_khong_de_nguoi_doc_doan() -> None:
    """`n_scored_citation` phải mang **đúng** mẫu số đã dùng để chia — không phải `len(results)`.

    Bộ `_bo_10_case()` bất đối xứng đúng chỗ này: **10 case, mẫu số 8**. Hai số khác nhau, nên một
    mutant lấy `len(results)` làm mẫu số (hoặc quên nối dây và để `None`) đều ĐỎ ở đây. Nếu bộ là
    10/10 thì cả ba cách viết cho cùng một số và bài này vô dụng.

    Vì sao đáng một field: `citation_accuracy = 0.85` đọc một kiểu trên 8 case, kiểu khác trên 30,
    và **không gì khác trên `Scorecard` khôi phục lại được** — `len(results)` đếm cả refusal, còn
    case bị `DEC-04` loại thì `Aggregate` không nhìn thấy. Một tỷ lệ không có `n` đi kèm là thứ
    `kit#134` xếp vào evidence malformed."""
    results, scored = _bo_10_case()

    scorecard = compute_scorecard(
        agent_id="a",
        golden_set_ref="g",
        results=results,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        scored_case_ids=scored,
    )

    assert scorecard.aggregate.n_scored_citation == 8
    assert len(scorecard.results) == 10, "bộ phải bất đối xứng, nếu không bài này không phân biệt được gì"


def test_mau_so_rong_la_0_chu_khong_phai_None() -> None:
    """Mẫu số rỗng ⇒ `n_scored_citation == 0`, **không** `None`.

    Hai giá trị này nói hai chuyện khác nhau và không được nhập một: `0` là *"đã đếm, và đếm ra
    rỗng"*; `None` là *"producer này không mang mẫu số"* (payload viết trước khi có field). Trả
    `None` ở ca rỗng làm consumer không phân biệt được **bộ toàn refusal** với **producer cũ**, và
    mất đúng thông tin khiến `citation_accuracy = None` đọc được thành có căn cứ."""
    results = [_case(f"REF-{i}", success=True, acc=1.0) for i in range(4)]

    scorecard = compute_scorecard(
        agent_id="a",
        golden_set_ref="g",
        results=results,
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        scored_case_ids=set(),
    )

    assert scorecard.aggregate.n_scored_citation == 0
    assert scorecard.aggregate.n_scored_citation is not None, "0 và None là hai chuyện khác nhau"
    assert scorecard.aggregate.citation_accuracy is None
    assert scorecard.gate.verdict == "FAIL"
