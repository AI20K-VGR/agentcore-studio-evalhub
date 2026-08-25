"""`golden_merge.py` — cưỡng chế *"human ground-truth always wins"* lúc hợp nhất hai nguồn.

Luật này đã nằm trong docstring `GoldenCase.source` từ khi trục đó ra đời, nhưng **chưa có hàm nào
cưỡng chế** — nên nó là lời hứa, không phải cổng. File này biến nó thành máy kiểm.

Ba nhóm bài, ba kiểu hỏng khác nhau, không nhóm nào thay được nhóm kia:

1. **luật thắng/thua** — `human` ghi đè `ai`, và thứ tự tham số KHÔNG được quyết định thay;
2. **khoá dedup** — case hàng rào T1/T6 (cùng `query`, khác tenant/vai) phải SỐNG SÓT;
3. **fail-closed** — cặp mà luật không nói thì ném, không chọn bừa.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.golden_merge import (
    GoldenSetMergeConflict,
    case_key,
    merge_golden_sets,
    normalize_query,
)

_QUERY = "Nhân viên xin nghỉ phép cần báo trước bao lâu?"


def _case(
    case_id: str,
    *,
    query: str = _QUERY,
    tenant: str = "ankor",
    roles: list[str] | None = None,
    source: str | None = None,
    expected: str = "Báo trước 3 ngày.",
    expected_tenant: str | None = "ankor",
) -> GoldenCase:
    return GoldenCase(
        case_id=case_id,
        query=query,
        tenant=tenant,
        section_roles=["public"] if roles is None else roles,
        expected_tenant=expected_tenant,
        expected_section_role="public",
        expected=expected,
        source=source,
    )


def _bo(ref: str, *cases: GoldenCase) -> GoldenSet:
    return GoldenSet(golden_set_ref=ref, cases=list(cases))


# ---------------------------------------------------------------------------
# 1. Luật thắng/thua
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("human_truoc", [True, False])
def test_human_thang_ai_bat_ke_thu_tu_tham_so(human_truoc: bool) -> None:
    """Bản `human` thắng dù nó là bộ thứ nhất hay thứ hai.

    **Đây là bài mang toàn bộ giá trị của module.** Chạy cả hai chiều là bắt buộc, không phải cho
    đủ: một `dict.update()` trần cũng xanh ở MỘT chiều. Chỉ khi cả hai chiều cùng ra bản `human`
    thì mới chứng minh được `source` quyết định chứ không phải thứ tự — đúng chữ mà docstring
    `GoldenCase.source` dùng: *"không phải bản nào tới sau thắng"*.
    """
    may = _bo("bo-ai", _case("ai-01", source="ai", expected="Máy đoán: 5 ngày."))
    nguoi = _bo("bo-human", _case("human-01", source="human", expected="Người sửa: 3 ngày."))

    dau_vao = (nguoi, may) if human_truoc else (may, nguoi)
    hop_nhat = merge_golden_sets(*dau_vao, golden_set_ref="bo-lai")

    assert len(hop_nhat.cases) == 1
    assert hop_nhat.cases[0].case_id == "human-01"
    assert hop_nhat.cases[0].expected == "Người sửa: 3 ngày."
    assert hop_nhat.golden_set_ref == "bo-lai"


def test_lay_case_nguyen_ven_khong_tron_tung_field() -> None:
    """Bản thắng đi vào nguyên vẹn — không có case lai giữa hai nguồn.

    Trộn từng field sẽ dựng ra một case **chưa ai từng viết**: câu hỏi của người ghép với đáp án
    mong đợi của máy. Không ai rà được nó, và nó vẫn trông hợp lệ."""
    may = _bo(
        "bo-ai",
        _case("ai-01", source="ai", expected="Máy đoán.", expected_tenant="borea"),
    )
    nguoi = _bo("bo-human", _case("human-01", source="human", expected="Người sửa."))

    thang = merge_golden_sets(may, nguoi, golden_set_ref="bo-lai").cases[0]

    assert (thang.case_id, thang.expected, thang.expected_tenant) == ("human-01", "Người sửa.", "ankor"), (
        "mọi field phải tới từ bản human; thấy field của bản ai lẫn vào nghĩa là đang trộn"
    )


def test_case_khong_va_cham_thi_giu_ca_hai() -> None:
    """Hợp nhất là GỘP, không phải THAY — diện phủ của bên kia phải còn.

    Chống lại một cách "sửa" hỏng mà vẫn làm bài trên xanh: trả thẳng bộ `human`."""
    may = _bo("bo-ai", _case("ai-01", query="Câu của máy?", source="ai"))
    nguoi = _bo("bo-human", _case("human-01", query="Câu của người?", source="human"))

    hop_nhat = merge_golden_sets(may, nguoi, golden_set_ref="bo-lai")

    assert sorted(c.case_id for c in hop_nhat.cases) == ["ai-01", "human-01"]


def test_thu_tu_dau_ra_theo_lan_xuat_hien_dau_tien() -> None:
    """Thứ tự tất định, giữ trật tự bộ đầu — hai lượt chấm cùng dữ liệu cho cùng một báo cáo."""
    may = _bo(
        "bo-ai",
        _case("ai-01", query="A?", source="ai"),
        _case("ai-02", query="B?", source="ai"),
        _case("ai-03", query="C?", source="ai"),
    )
    nguoi = _bo("bo-human", _case("human-02", query="B?", source="human"))

    ids = [c.case_id for c in merge_golden_sets(may, nguoi, golden_set_ref="x").cases]

    assert ids == ["ai-01", "human-02", "ai-03"], (
        "bản thắng phải nằm ĐÚNG vị trí mà khoá của nó xuất hiện lần đầu, không bị đẩy xuống cuối"
    )


# ---------------------------------------------------------------------------
# 2. Khoá dedup — case hàng rào phải sống sót
# ---------------------------------------------------------------------------


def test_case_hang_rao_cung_query_khac_tenant_KHONG_bi_gop() -> None:
    """T1: cùng câu hỏi, hỏi dưới tenant khác ⇒ hai case khác nhau, phải còn cả hai.

    Đây là bài đắt nhất trong file. Dedup theo `query` sẽ gộp cặp này làm một và **xoá lặng lẽ**
    đúng case bảo mật mà bộ golden tồn tại để kiểm — `success_rate` sau đó vẫn ra một con số trông
    bình thường, không lỗi nào nổi lên."""
    hop_nhat = merge_golden_sets(
        _bo(
            "bo",
            _case("that-01", tenant="ankor", source="ai"),
            _case("bay-01", tenant="borea", expected_tenant="ankor", source="ai"),
        ),
        golden_set_ref="x",
    )

    assert len(hop_nhat.cases) == 2, "case chéo-tenant KHÔNG được gộp với case thật cùng query"
    assert [c.expects_refusal for c in hop_nhat.cases] == [False, True], (
        "bài chống rỗng: cặp này phải THẬT SỰ là cặp thật/bẫy, không phải hai case ngẫu nhiên"
    )


def test_case_hang_rao_cung_query_khac_vai_KHONG_bi_gop() -> None:
    """T6: cùng câu hỏi, bộ vai khác ⇒ hai case khác nhau."""
    hop_nhat = merge_golden_sets(
        _bo(
            "bo",
            _case("public-01", roles=["public"], source="ai"),
            _case("finance-01", roles=["finance"], source="ai"),
        ),
        golden_set_ref="x",
    )

    assert len(hop_nhat.cases) == 2


def test_thu_tu_vai_khong_tao_ra_case_moi() -> None:
    """`["public","hr"]` và `["hr","public"]` là cùng một phạm vi đọc — thứ tự khai không là dữ liệu."""
    assert case_key(_case("a", roles=["public", "hr"])) == case_key(_case("b", roles=["hr", "public"]))


@pytest.mark.parametrize(
    ("bien_the", "mo_ta"),
    [
        ("  Nhân viên xin nghỉ phép cần báo trước bao lâu?  ", "khoảng trắng đầu/cuối"),
        ("Nhân viên xin nghỉ phép\n  cần báo trước bao lâu?", "xuống dòng giữa câu (YAML block)"),
        ("NHÂN VIÊN XIN NGHỈ PHÉP CẦN BÁO TRƯỚC BAO LÂU?", "hoa/thường"),
    ],
)
def test_bien_the_khong_mang_nghia_van_gap_nhau(bien_the: str, mo_ta: str) -> None:
    """Ba biến thể định dạng phải hợp nhất được với bản gốc."""
    del mo_ta
    hop_nhat = merge_golden_sets(
        _bo("bo-ai", _case("ai-01", query=bien_the, source="ai")),
        _bo("bo-human", _case("human-01", source="human")),
        golden_set_ref="x",
    )
    assert [c.case_id for c in hop_nhat.cases] == ["human-01"]


def test_NFC_hai_cach_ma_hoa_dau_tieng_viet_gap_nhau() -> None:
    """Dựng sẵn vs tổ hợp: hai chuỗi HIỂN THỊ Y HỆT nhau mà `==` trả False.

    Không có `NFC`, một case người viết (bàn phím này) và một case máy sinh (nguồn kia) mang cùng
    câu hỏi sẽ **không bao giờ gặp nhau**, và luật *"human thắng"* im lặng không áp dụng. Lỗi này
    không thấy được khi đọc diff — đó là lý do nó phải có bài riêng chứ không gộp vào bài biến thể
    định dạng ở trên."""
    import unicodedata

    to_hop = unicodedata.normalize("NFD", _QUERY)
    assert to_hop != _QUERY, "fixture hỏng: NFD phải khác NFC về byte, nếu bằng thì bài này rỗng nghĩa"
    assert normalize_query(to_hop) == normalize_query(_QUERY)

    hop_nhat = merge_golden_sets(
        _bo("bo-ai", _case("ai-01", query=to_hop, source="ai")),
        _bo("bo-human", _case("human-01", source="human")),
        golden_set_ref="x",
    )
    assert [c.case_id for c in hop_nhat.cases] == ["human-01"]


def test_dau_cau_khac_nhau_VAN_la_hai_case() -> None:
    """Chuẩn hoá dừng đúng chỗ: không bỏ dấu câu.

    Bài này khoá chiều NGƯỢC LẠI của mọi bài trên — nó đỏ khi ai đó chuẩn hoá MẠNH TAY hơn. Thiếu
    nó, mọi bài ở trên đều xanh hơn khi normalize hung hăng thêm, và không gì cản việc đó."""
    hop_nhat = merge_golden_sets(
        _bo(
            "bo",
            _case("a", query="Trưởng nhóm được duyệt chi tối đa bao nhiêu?", source="ai"),
            _case("b", query="Trưởng nhóm được duyệt chi tối đa bao nhiêu", source="ai"),
        ),
        golden_set_ref="x",
    )
    assert len(hop_nhat.cases) == 2


# ---------------------------------------------------------------------------
# 3. Fail-closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b"),
    [("ai", "ai"), ("human", "human"), (None, "human"), (None, "ai"), (None, None)],
)
def test_cap_luat_khong_noi_thi_nem_chu_khong_chon_bua(a: str | None, b: str | None) -> None:
    """Luật chỉ định nghĩa `human` thắng `ai`. Mọi cặp khác phải do người quyết.

    `(None, "human")` là cặp đáng chú ý nhất: 60 case golden hiện có đều `source=None`, và coi
    `None` là "người viết" sẽ khai hộ nguồn gốc cho cả 60 — đúng thứ mặc định `None` được chọn để
    tránh."""
    with pytest.raises(GoldenSetMergeConflict) as bat:
        merge_golden_sets(
            _bo("b1", _case("c-a", source=a)),
            _bo("b2", _case("c-b", source=b)),
            golden_set_ref="x",
        )

    assert len(bat.value.conflicts) == 1
    assert bat.value.conflicts[0].sources == (a, b)


def test_nem_ra_MOI_va_cham_chu_khong_dung_o_cai_dau_tien() -> None:
    """Người sửa cần thấy đủ danh sách để sửa một lượt, không phải chạy lại 3 lần."""
    with pytest.raises(GoldenSetMergeConflict) as bat:
        merge_golden_sets(
            _bo(
                "b1",
                _case("a1", query="A?", source="ai"),
                _case("b1", query="B?", source="ai"),
                _case("c1", query="C?", source="ai"),
            ),
            _bo(
                "b2",
                _case("a2", query="A?", source="ai"),
                _case("b2", query="B?", source="ai"),
                _case("c2", query="C?", source="ai"),
            ),
            golden_set_ref="x",
        )

    assert len(bat.value.conflicts) == 3, "dừng ở va chạm đầu tiên là buộc người sửa lặp 3 lượt"
    assert {c.key[1] for c in bat.value.conflicts} == {"a?", "b?", "c?"}


def test_thong_diep_va_cham_neu_du_case_id_va_source() -> None:
    """Thông điệp phải chỉ được ra CASE NÀO — một lỗi chỉ nói "có va chạm" thì không sửa được."""
    with pytest.raises(GoldenSetMergeConflict) as bat:
        merge_golden_sets(
            _bo("b1", _case("ai-01", source="ai")),
            _bo("b2", _case("ai-02", source="ai")),
            golden_set_ref="x",
        )

    loi = str(bat.value)
    assert "ai-01" in loi and "ai-02" in loi
    assert "ankor" in loi


def test_khong_truyen_bo_nao_thi_ValueError() -> None:
    """Bộ rỗng đi tiếp sẽ thành mẫu số 0 ở `compute_scorecard` — chặn tại đây."""
    with pytest.raises(ValueError, match="ít nhất một GoldenSet"):
        merge_golden_sets(golden_set_ref="x")


def test_ref_ket_qua_khong_muon_ten_cua_bo_nguon() -> None:
    """`golden_set_ref` bắt buộc keyword-only, không suy từ đầu vào.

    Bộ lai khác cả hai bộ nguồn; mượn tên một trong hai sẽ làm `recipe.golden_set_ref` trỏ vào một
    tập khác hẳn tập mà cái tên đó mô tả (cùng lý lẽ `DEC-D16-01`)."""
    with pytest.raises(TypeError):
        merge_golden_sets(_bo("bo-ai", _case("a", source="ai")))  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# 4. Neo vào dữ liệu THẬT — khoá phải đúng trên corpus đang dùng
# ---------------------------------------------------------------------------


def test_khoa_khong_gay_trung_tren_bo_golden_that() -> None:
    """Trên 5 bộ đóng gói sẵn: khoá đủ cho 0 trùng, còn `query` một mình cho nhiều trùng.

    Bài này neo thiết kế vào số đo, không vào lập luận. Nếu ai đó rút khoá xuống còn `query`, vế
    thứ hai chứng minh ngay hậu quả: các cặp T1/T6 sẽ bị gộp.

    Đọc YAML thẳng chứ không qua `load_golden_set` — bộ đó nằm ở `packages/kb` và `.importlinter`
    cấm `studio_evalhub` import `studio_kb`; đây là test nên chỉ đọc file, không import.
    """
    thu_muc = pathlib.Path(__file__).resolve().parents[2] / "kb" / "src" / "studio_kb" / "golden"
    if not thu_muc.is_dir():  # pragma: no cover — chỉ xảy ra khi chạy evalhub tách khỏi workspace
        pytest.skip(f"không thấy corpus golden ở {thu_muc}")

    tong_trung_query = 0
    for f in sorted(thu_muc.glob("*.yaml")):
        raw = yaml.safe_load(f.read_text(encoding="utf-8"))
        cases = raw.get("cases") or []
        if not cases:
            continue
        # Qua `case_key` THẬT, không dựng lại khoá tại chỗ: một bản chép sẽ vẫn xanh khi ai đó rút
        # khoá trong `golden_merge` xuống còn `query`, và bài này mất đúng thứ nó canh.
        khoa_du = {case_key(GoldenCase(**c)) for c in cases}
        chi_query = {normalize_query(c["query"]) for c in cases}
        assert len(khoa_du) == len(cases), f"{f.name}: khoá đủ bị trùng — khoá không phân biệt được case thật"
        tong_trung_query += len(cases) - len(chi_query)

    assert tong_trung_query >= 20, (
        "bài chống rỗng: corpus phải THẬT SỰ có nhiều case dùng chung query (các cặp hàng rào "
        f"T1/T6), nếu không thì vế 'query không đủ làm khoá' là một lo lắng tưởng tượng. "
        f"Đếm được {tong_trung_query}"
    )


def test_normalize_query_khong_lam_hong_case_that() -> None:
    """Chuẩn hoá không được làm hai case thật trong cùng một bộ đụng nhau — đã khoá ở bài trên qua
    khoá đủ; đây khoá riêng trục `query` cho các cặp CÙNG tenant + CÙNG vai."""
    thu_muc = pathlib.Path(__file__).resolve().parents[2] / "kb" / "src" / "studio_kb" / "golden"
    if not thu_muc.is_dir():  # pragma: no cover
        pytest.skip("không thấy corpus golden")

    for f in sorted(thu_muc.glob("*.yaml")):
        raw = yaml.safe_load(f.read_text(encoding="utf-8"))
        theo_nhom: dict[tuple[str, frozenset[str]], list[str]] = {}
        for c in raw.get("cases") or []:
            theo_nhom.setdefault((c["tenant"], frozenset(c.get("section_roles") or [])), []).append(
                normalize_query(c["query"])
            )
        for nhom, qs in theo_nhom.items():
            assert len(qs) == len(set(qs)), f"{f.name} nhóm {nhom}: chuẩn hoá làm 2 case thật đụng nhau"


def test_regex_gop_khoang_trang_khong_an_ky_tu_that() -> None:
    """Chống một lỗi dễ mắc khi sửa `_WHITESPACE`: `\\s+` → `.+` sẽ nuốt cả câu."""
    assert normalize_query("a  b") == "a b"
    assert re.sub(r"\s+", " ", "a  b") == "a b"
    assert normalize_query("Hạn mức là 5 ngày") == "hạn mức là 5 ngày"
