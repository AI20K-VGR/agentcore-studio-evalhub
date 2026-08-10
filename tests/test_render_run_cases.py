"""Test tầng RENDER cho bảng per-case của một **run thật** — `render_run_cases`. D15, `kit#103`.

Viết **trước** khi `render_run_cases` tồn tại (T3 bước 1). Đây là chỗ duy nhất trong ngày làm được
đúng nghĩa test-trước: T4 là siết test cho code đã có.

Hàm này khoá ba luật, tất cả đều là biến thể của *"không in một con số mình không đo"*:

1. **In số THẬT của run, không in `todo:`** — `render_scorecard(None)` in `todo:` vì chưa có
   golden-set; ở đây đã có `SmokeResult` chấm từ trace thật nên `todo:` là sai loại.
2. **Dòng từ-chối in `n/a`, không in `1.00`** — nối `DEC-D12-01`. `1.0` ở nhánh từ-chối là quy ước
   vacuous-truth, không phải phép đo.
3. **Chỉ in `k/n` thô, KHÔNG in tỷ lệ tổng** (`DEC-D15-02`). Mẫu số citation tách riêng và loại
   refusal (`DEC-S2-134-03`); `Aggregate` chưa có chỗ cho `n_scored_citation` (nợ có chủ, hạn D16).
   `kit#134`: chỗ hỏng không nằm ở probe, nằm ở **bước từ `8/10` sang `"80%"`**.

Fixture ở đây cố ý **bất đối xứng theo cột** (T3 bước 3): `case_id` khác nhau, có cả nhánh trả-lời
lẫn nhánh từ-chối, `success` không đồng loạt `True`, `citation_accuracy` không đồng loạt cùng một số,
và `k ≠ n` ở cả hai dòng đếm — với **hai mẫu số khác nhau** (5 và 3). Fixture mà mọi cột đọc giống
nhau thì mutant hoán cột hay bóp một giá trị về hằng vẫn xanh.

Luật H2 (`|expected| ≠ |retrieved| ≠ |giao|`) **không** áp ở đây: đó là luật của **scorer** (T4).
Renderer nhận `citation_accuracy` như một số đã có sẵn trên `SmokeResult`, nó không tính tử/mẫu nên
không có gì để bất đối xứng.
"""

from __future__ import annotations

import pytest
from studio_evalhub.compute import compute_scorecard
from studio_evalhub.harness import SmokeResult
from studio_evalhub.render import render_run_cases, render_scorecard

# Metadata run — dùng chung mọi bài để một chỗ đổi là mọi bài theo.
_RUN_ID = "run-d15-0001"
_GOLDEN_SET_REF = "callisto-smoke-5-v0"
_TRACE_SOURCE = "obs.trace_events (Postgres, bền hoá D14)"


def _answered(*, case_id: str, accuracy: float, success: bool) -> SmokeResult:
    return SmokeResult(
        case_id=case_id,
        expected="3 ngày làm việc",
        actual="Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
        success=success,
        citation_accuracy=accuracy,
        expects_refusal=False,
    )


def _refused(*, case_id: str, success: bool) -> SmokeResult:
    """Nhánh từ-chối — `citation_accuracy` LUÔN `1.0` theo quy ước (`harness.py:185`), kể cả khi FAIL."""
    return SmokeResult(
        case_id=case_id,
        expected="refusal",
        actual="Tôi không thể trả lời câu hỏi về dữ liệu của tổ chức khác.",
        success=success,
        citation_accuracy=1.0,
        expects_refusal=True,
    )


def _run_results() -> list[SmokeResult]:
    """Fixture bất đối xứng theo cột — xem docstring module.

    Số rút ra được từ fixture này, và **mọi con số phải khác nhau** để mutant hoán chỗ lộ ra:

    | | |
    |---|---|
    | tổng case | `5` |
    | success `k/n` | `3/5` |
    | citation `k/n` (chỉ nhánh trả-lời) | `1/3` |

    Bốn số `5 · 3 · 1 · 3` — mẫu số success (`5`) khác mẫu số citation (`3`), nên một mutant dùng
    `len(results)` cho mẫu số citation không sống được.
    """
    return [
        _answered(case_id="SC-01", accuracy=1.0, success=True),
        _answered(case_id="SC-02", accuracy=0.5, success=True),
        _answered(case_id="SC-03", accuracy=0.0, success=False),
        _refused(case_id="SC-04", success=True),
        _refused(case_id="SC-05", success=False),
    ]


def _row(out: str, case_id: str) -> str:
    """Dòng bảng của đúng `case_id`. Đỏ ngay nếu có 0 dòng hoặc >1 dòng — cả hai đều là lỗi thật."""
    rows = [ln for ln in out.splitlines() if ln.startswith(case_id)]
    assert len(rows) == 1, f"{case_id}: kỳ vọng đúng 1 dòng, thấy {len(rows)}"
    return rows[0]


# ---------------------------------------------------------------------------
# 1. In số THẬT của run — không phải khung `todo:`
# ---------------------------------------------------------------------------


def test_render_case_in_so_that_cua_run_chu_khong_in_todo() -> None:
    """Bài chính T3: đã có `SmokeResult` chấm từ trace thật ⇒ bảng phải in **số**, không in `todo:`.

    `todo:` là ngôn ngữ của `render_scorecard(None)` — trạng thái *"chưa đo được"*. Dùng lại nó ở đây
    sẽ nói dối theo chiều ngược với `DEC-D12-02`: một ô **đã** đo được lại được trình bày như chưa
    đo. Bài này đỏ nghĩa là D15 vẫn đang render skeleton, tức `O3.1` đứng yên ngày thứ tư."""
    out = render_run_cases(
        _run_results(),
        run_id=_RUN_ID,
        golden_set_ref=_GOLDEN_SET_REF,
        trace_source=_TRACE_SOURCE,
    )

    assert "todo:" not in out, "đã có số thật thì KHÔNG được in todo:"

    # Metadata run phải in ra — không có `run_id` thì bảng này không truy về được run nào.
    assert _RUN_ID in out
    assert _GOLDEN_SET_REF in out
    assert _TRACE_SOURCE in out

    # Số per-case của nhánh trả-lời in đúng giá trị trên object, không bóp về hằng.
    assert "1.00" in _row(out, "SC-01")
    assert "0.50" in _row(out, "SC-02")
    assert "0.00" in _row(out, "SC-03")

    # Cột success phân biệt được hai chiều.
    assert "PASS" in _row(out, "SC-01")
    assert "FAIL" in _row(out, "SC-03")


def test_render_case_in_du_5_case_khong_nuot_dong_nao() -> None:
    """Vế đối chứng: mọi `case_id` truyền vào đều có đúng một dòng.

    Thiếu bài này thì một bản vá chỉ in case đầu (hoặc `break` sớm trong vòng lặp) vẫn thoả mọi
    assert bên trên, vì bài trên chỉ hỏi từng dòng có số đúng chứ không hỏi có đủ dòng không."""
    results = _run_results()
    out = render_run_cases(results, run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE)

    for r in results:
        _row(out, r.case_id)


# ---------------------------------------------------------------------------
# 2. Nhánh từ-chối in `n/a` — nối DEC-D12-01
# ---------------------------------------------------------------------------


def test_render_case_tu_choi_in_n_a_chu_khong_in_1_00() -> None:
    """`DEC-D12-01` áp cho bảng mới: dòng từ-chối in `n/a`, `1.00` không xuất hiện trên dòng đó.

    Vế đắt là case từ-chối **đã FAIL** (`SC-05`): nếu in `1.00` thì một dòng đỏ lại mang con số đẹp
    nhất bảng. Đó là cơ chế thổi phồng `aggregate` mà GUIDE-C Q8 chỉ ra."""
    out = render_run_cases(_run_results(), run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE)

    for case_id in ("SC-04", "SC-05"):
        row = _row(out, case_id)
        assert "n/a" in row, f"{case_id}: dòng từ-chối phải in n/a"
        assert "1.00" not in row, f"{case_id}: dòng từ-chối KHÔNG được in 1.00"

    # Vế đối chứng: nhánh trả-lời KHÔNG được in `n/a` — nếu không, một bản vá in `n/a` cho MỌI dòng
    # cũng xanh, và lúc đó bảng mất sạch thông tin citation.
    for case_id in ("SC-01", "SC-02", "SC-03"):
        assert "n/a" not in _row(out, case_id), f"{case_id}: dòng trả-lời KHÔNG được in n/a"

    # `n/a` không tự giải thích ⇒ phải có chú thích nói nó nghĩa gì.
    assert "quy ước" in out
    assert "DEC-04" in out


def test_render_case_phan_biet_duoc_hai_nhanh_tren_dong_bang() -> None:
    """Nhánh của mỗi case phải đọc được **trên chính dòng đó**, không phải suy từ cột `n/a`.

    Suy nhánh từ một giá trị hiển thị là đúng lớp lỗi breakpoint `#14` (suy một cờ ngữ nghĩa từ một
    giá trị ⇒ xanh-giả) — cùng lý do `SmokeResult.expects_refusal` tồn tại thành field riêng thay vì
    được suy từ `citation_accuracy == 1.0`."""
    out = render_run_cases(_run_results(), run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE)

    for case_id in ("SC-01", "SC-02", "SC-03"):
        assert "trả-lời" in _row(out, case_id)
    for case_id in ("SC-04", "SC-05"):
        assert "từ-chối" in _row(out, case_id)


# ---------------------------------------------------------------------------
# 3. `k/n` thô — KHÔNG tỷ lệ tổng (DEC-D15-02 · DEC-S2-134-03)
# ---------------------------------------------------------------------------


def test_render_case_in_k_tren_n_tho_KHONG_in_ty_le_tong() -> None:
    """`DEC-D15-02`: in đếm thô `k/n`, **không** in `success_rate`/`citation_accuracy` tổng.

    Hai lý do đã chốt, không phải mới nghĩ:

    - `DEC-S2-134-03` — mẫu số citation phải tách `k_citation / n_citation_scored` và **loại
      refusal**; `Aggregate` hôm nay chưa có chỗ cho `n_scored_citation` (nợ có chủ, hạn D16).
    - In một tỷ lệ tổng khi chưa tách mẫu số là **đúng lỗi `kit#134` mô tả**: chỗ hỏng không nằm ở
      probe, nằm ở bước từ `8/10` sang `"80%"`.

    Hai mẫu số phải **khác nhau** trong output (`5` cho success, `3` cho citation). Đây là chỗ mutant
    dùng `len(results)` cho cả hai sẽ chết."""
    out = render_run_cases(_run_results(), run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE)

    assert "3/5" in out, "success k/n thô = 3/5"
    assert "1/3" in out, "citation k/n thô = 1/3 (chỉ nhánh trả-lời, đã loại refusal)"

    # Không tỷ lệ tổng dưới bất kỳ hình dạng nào.
    assert "%" not in out, "KHÔNG in phần trăm — DEC-D15-02"
    for banned in ("0.60", "60.0", "0.33", "33.3", "success_rate", "citation_accuracy ="):
        assert banned not in out, f"KHÔNG in tỷ lệ tổng: {banned!r}"

    # Nhãn bắt buộc: người đọc phải biết đây chưa phải ước lượng quần thể.
    assert "fixed-set" in out
    assert "chưa phải population estimate" in out


def test_render_case_mau_so_citation_loai_refusal_chu_khong_dung_tong_case() -> None:
    """Mẫu số citation là **số case trả-lời** (`3`), không phải tổng case (`5`).

    Tách riêng bài này khỏi bài `k/n` bên trên vì đây là bất biến của `DEC-S2-134-03`, và nó phải đỏ
    **một mình** khi ai đó gộp refusal vào mẫu số — chứ không lẫn vào một assert `"1/3" in out`.

    Fixture chọn `5` và `3` khác nhau chính là để phép đo này có sức phân biệt: nếu hai mẫu số bằng
    nhau thì mutant gộp refusal vẫn xanh."""
    results = _run_results()
    n_answerable = sum(1 for r in results if not r.expects_refusal)
    n_total = len(results)
    assert n_answerable != n_total, "fixture hỏng: hai mẫu số phải khác nhau thì bài này mới đo được gì"

    out = render_run_cases(results, run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE)

    assert f"/{n_answerable}" in out, "mẫu số citation phải là số case trả-lời"
    assert f"1/{n_total}" not in out, "mẫu số citation KHÔNG được là tổng case (refusal phải bị loại)"
    assert "loại refusal" in out or "loại nhánh từ-chối" in out, "phải nói rõ mẫu số đã loại refusal"


# ---------------------------------------------------------------------------
# 4. Không gọi `compute_scorecard` — nối test cùng họ của `render_scorecard`
# ---------------------------------------------------------------------------


def test_render_case_KHONG_goi_compute_scorecard() -> None:
    """Render **không** tự tính — nối `DEC-D12-03` và `DEC-D15-01` (bỏ 1).

    `compute_scorecard` là mốc D16 (`kit#108`). Khoá bằng chứng cứng: nó vẫn raise. Nếu một bản vá
    cho `render_run_cases` gọi nó, thì hoặc bài này đỏ (vì raise lọt lên), hoặc `compute_scorecard`
    đã được hiện thực sớm — cả hai đều là thứ phải nhìn thấy, không được trôi. Land sớm còn làm
    `test_gate_blocks_on_fail` (`xfail(strict=True)`) XPASS ⇒ FAIL."""
    with pytest.raises(NotImplementedError):
        compute_scorecard(
            agent_id="a",
            golden_set_ref="g",
            results=[],
            threshold_success=0.9,
            threshold_citation_accuracy=0.95,
            # D16: tham số mới của `compute_scorecard` (DEC-D16-03 đường (b)) — caller nói nhánh nào
            # được chấm citation. `results=[]` nên tập rỗng là giá trị đúng; bài này không đổi mục
            # đích, vẫn chỉ khoá "renderer KHÔNG gọi sang tầng tính".
            scored_case_ids=set(),
        )

    # Gọi được và không raise ⇒ đường đi của renderer không chạm `compute_scorecard`.
    out = render_run_cases(_run_results(), run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE)
    assert "PASS" in out

    # Và không có verdict: verdict là output của gate (D16), không phải của renderer.
    assert "verdict" not in out


# ---------------------------------------------------------------------------
# 5. `results` rỗng ⇒ not-estimable, KHÔNG in `0%` / `0.00`
# ---------------------------------------------------------------------------


def test_render_case_rong_la_not_estimable_KHONG_in_0_phan_tram() -> None:
    """`n = 0` ⇒ nói **not-estimable**, không in `0%` cũng không in `0.00`.

    `kit#134`: `n=0` không cho ra một ước lượng nào cả — in `0%` ở đó là khẳng định *"đã đo, và bằng
    0"* trên một phép đo chưa từng xảy ra. Cùng lớp lỗi với `DEC-D12-02` (`todo:` chứ không `0.00`),
    chỉ khác là ở đây lý do là mẫu số rỗng chứ không phải chưa có golden-set."""
    out = render_run_cases([], run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE)

    assert "0%" not in out and "%" not in out
    assert "0.00" not in out, "n=0 KHÔNG được in 0.00"
    assert "not-estimable" in out
    assert "0/0" not in out, "0/0 vẫn mời người đọc chia — nói thẳng là not-estimable"

    # Metadata vẫn phải in: một run rỗng cũng cần truy được về run nào.
    assert _RUN_ID in out


def test_render_case_toan_refusal_thi_citation_la_not_estimable() -> None:
    """Mẫu số citation rỗng (mọi case đều từ-chối) ⇒ **citation** not-estimable, còn success vẫn đếm.

    Đây là nhánh `n=0` **từng phần** — nguy hiểm hơn nhánh rỗng hoàn toàn vì bảng vẫn có dòng, vẫn
    trông như đã đo. `DEC-S2-134-03` loại refusal khỏi mẫu số citation, nên một run toàn refusal có
    `n_citation_scored = 0` **trong khi** `n_success = 2`."""
    out = render_run_cases(
        [_refused(case_id="SC-04", success=True), _refused(case_id="SC-05", success=False)],
        run_id=_RUN_ID,
        golden_set_ref=_GOLDEN_SET_REF,
        trace_source=_TRACE_SOURCE,
    )

    assert "1/2" in out, "success vẫn đếm được khi toàn refusal"
    assert "not-estimable" in out, "citation phải là not-estimable khi mẫu số rỗng"
    assert "0/0" not in out
    assert "%" not in out


# ---------------------------------------------------------------------------
# 6. Không đổi giá trị trên object — chỉ đổi hiển thị
# ---------------------------------------------------------------------------


def test_render_case_khong_doi_gia_tri_tren_object_chi_doi_hien_thi() -> None:
    """Renderer là hàm **thuần hiển thị**: sau khi gọi, mọi field trên mọi `SmokeResult` giữ nguyên.

    Nối `test_render_khong_doi_gia_tri_tren_object_chi_doi_hien_thi` của D12. Cách sửa "hiển nhiên"
    cho `n/a` là đổi `citation_accuracy` sang `float | None` trên object — làm vậy sẽ `TypeError` ở 3
    renderer format `:.2f` ngoài quadrant và phá pin test D11.

    So sánh bằng `model_dump()` chứ không gõ tay từng field (H5): thêm field thứ 7 vào `SmokeResult`
    thì bài này tự bảo vệ luôn field đó, không cần ai nhớ sửa test."""
    results = _run_results()
    before = [r.model_dump() for r in results]

    render_run_cases(results, run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE)

    assert [r.model_dump() for r in results] == before
    assert all(isinstance(r.citation_accuracy, float) for r in results)


def test_render_case_moi_field_cua_SmokeResult_deu_duoc_phan_loai_hien_thi_hay_khong() -> None:
    """H5 — bất biến cưỡng chế **bằng code**: mọi field của `SmokeResult` phải được phân loại là
    *có in ra bảng* hay *cố ý không in*, và hai tập đó phải phủ kín `model_fields`.

    Đây là đúng cái bẫy đã dính ở D12: thêm field thứ 6 (`expects_refusal`) vào `SmokeResult` mà
    danh sách trong test gõ tay nên không ai biết. Bài này không hỏi *"in đủ mọi ô"* — bảng cố ý
    không in `expected`/`actual` vì chúng là văn bản dài. Nó hỏi câu đắt hơn: **field mới có được ai
    nhìn không**. Thêm field thứ 7 mà quên khai ⇒ đỏ ngay, và người thêm phải quyết một cách có ý
    thức thay vì để nó rơi im lặng."""
    from studio_evalhub.render import RUN_CASE_COLUMNS, RUN_CASE_FIELDS_NOT_SHOWN

    declared = set(RUN_CASE_COLUMNS) | set(RUN_CASE_FIELDS_NOT_SHOWN)
    actual = set(SmokeResult.model_fields)

    assert declared == actual, (
        f"field chưa phân loại: {actual - declared}; field khai thừa: {declared - actual}. "
        "Thêm field vào SmokeResult thì phải khai nó có lên bảng hay không."
    )
    assert not (set(RUN_CASE_COLUMNS) & set(RUN_CASE_FIELDS_NOT_SHOWN)), "một field không thể vừa in vừa không"

    # Và mọi field đã khai là có in thì phải thật sự in ra — khai suông không tính.
    out = render_run_cases(_run_results(), run_id=_RUN_ID, golden_set_ref=_GOLDEN_SET_REF, trace_source=_TRACE_SOURCE)
    for field in RUN_CASE_COLUMNS:
        assert field in out, f"khai {field} là cột nhưng không thấy trong output"


# ---------------------------------------------------------------------------
# 7. Chống hồi quy — `render_scorecard` cũ không đổi hành vi
# ---------------------------------------------------------------------------


def test_render_scorecard_cu_khong_doi_hanh_vi() -> None:
    """Pin: thêm `render_run_cases` **không** được đụng `render_scorecard`.

    16 bài trong `test_render.py` đã khoá chi tiết hành vi cũ; bài này là chốt chặn ở tầng module —
    nó đỏ ngay cả khi ai đó đổi `render_scorecard` theo một cách mà `test_render.py` tình cờ chưa
    bao. Hai hàm dùng chung helper `_row`/`_TODO`, nên refactor để dùng chung là chỗ dễ trượt nhất."""
    out = render_scorecard(None)

    assert "todo:" in out, "khung trống vẫn phải là ngôn ngữ todo:"
    assert out.count("todo:") >= 5
    assert "0.00" not in out
    assert "PASS" not in out and "FAIL" not in out
