"""Test `agreement` — hàm thuần, ba giá trị trả về, fail-closed khi mẫu số rỗng (`DEC-D18-04`).

**Con số này KHÔNG phải human–machine agreement, và đó không phải chi tiết câu chữ.** `manual_label`
(kb) và `expects_refusal` (evalhub) hiện **trùng nhau về ngữ nghĩa** nhưng được xác định ở **hai phía
khác nhau bằng hai bản cài đặt độc lập**. Vì thế phép so đo được đúng một thứ: **đồng thuận ngữ nghĩa
hàng rào kb ↔ evalhub** trên subset có nhãn. Nó là **regression detector cho semantic drift giữa hai
repo**, không phải phép đo người-so-với-máy — nhãn tay không mang thông tin nào độc lập với dữ liệu
golden-30 đã tự khai.

Giá trị của nó là thật và đã có tiền lệ: trước 23/07, `expects_refusal` thiếu trục T6 ⇒ case chéo-vai
cùng tenant rơi nhầm nhánh, agent từ chối ĐÚNG bị chấm FAIL. Một bộ dò lệch giữa hai phía sẽ bắn ngay
hôm đó.

Mọi bài ở đây dựng nhãn **tự gieo trong fixture** ⇒ số đo là **CƠ CHẾ**, không phải THẬT. Việc gán
nhãn THẬT/CƠ CHẾ là của người viết báo cáo, không phải của hàm (`DEC-D18-04`) — bài đọc dữ liệu thật
nằm ở `tests/integration/test_agreement_golden_30.py`.
"""

from __future__ import annotations

import pytest
from studio_evalhub.agreement import agreement, nhan_tu_golden_set
from studio_evalhub.golden_case import GoldenCase, GoldenSet

# Fixture **bất đối xứng**: 5 case có nhãn / 2 case không, và trong 5 case có nhãn thì lệch **1**.
# Cân 50/50 là chỗ một mutant đảo nhãn vẫn cho ra cùng con số.
_BO_CHAM = {
    "HB-01": "pass",
    "HB-02": "pass",
    "HB-03": "refuse",
    "HB-04": "refuse",
    "HB-05": "pass",
    "HB-06": "pass",
    "HB-07": "refuse",
}
_NHAN_TAY = {
    "HB-01": "pass",
    "HB-02": "pass",
    "HB-03": "refuse",
    "HB-04": "pass",  # ← LỆCH: kb nói pass, evalhub nói refuse
    "HB-05": "pass",
    "HB-06": None,  # chưa gán nhãn
    "HB-07": None,  # chưa gán nhãn
}


def test_rate_va_mau_so_dung_gia_tri_that() -> None:
    """Ba giá trị trả về, và bài assert **giá trị thật** chứ không assert *"có trả về một số"*.

    5 case có nhãn, lệch 1 ⇒ `rate = 4/5 = 0.8`, `n_compared = 5`, lệch = `["HB-04"]`.

    Assert cả ba cùng lúc là có chủ đích: một `rate` trần là **đúng thứ `kit#134` gọi là bằng chứng
    dị dạng** — tỷ lệ không kèm mẫu số. `0.8` trên 5 case là một khẳng định khác hẳn `0.8` trên 30
    case, và không gì khác trong kết quả khôi phục lại được mẫu số."""
    ket_qua = agreement(_BO_CHAM, _NHAN_TAY)

    assert ket_qua.rate == pytest.approx(0.8)
    assert ket_qua.n_compared == 5
    assert ket_qua.lech == ["HB-04"]


def test_case_khong_co_nhan_bi_loai_khoi_mau_so() -> None:
    """Case `manual_label is None` ⇒ **loại khỏi mẫu số**, KHÔNG tính là lệch.

    `None` nghĩa là *"chưa được gán nhãn tay"*, không phải *"nhãn tay bất đồng"* — đúng nghĩa đã ghi
    ở docstring `GoldenCase.manual_label`. Đếm chúng thành lệch sẽ làm mọi bộ dữ liệu gán nhãn một
    phần trông như đang drift nặng, và con số đó **trông hợp lệ**.

    Đo bằng cách so mẫu số với tổng: 7 case vào, 5 case ra."""
    ket_qua = agreement(_BO_CHAM, _NHAN_TAY)

    assert ket_qua.n_compared == 5
    assert len(_BO_CHAM) == 7
    assert "HB-06" not in ket_qua.lech
    assert "HB-07" not in ket_qua.lech


def test_mau_so_rong_tra_none_khong_phai_khong_phay_khong() -> None:
    """**Bất biến nặng nhất của T3** (`M-J5`): `n_compared == 0` ⇒ `rate is None`, KHÔNG phải `0.0`.

    *Không đo được* ≠ *đo được và bằng không*. Cùng luật `Aggregate.citation_accuracy`
    (`DEC-D16-03`), và lý do giống hệt: một `0.00` in ra **không phân biệt được** với một phép đo
    thật cho kết quả bằng không — nó đi thẳng vào báo cáo như một con số, trong khi sự thật là chưa
    có case nào để so.

    Đây là trạng thái THẬT của golden-30 hôm nay (0/30 case có nhãn trên `main`), nên đường này
    không phải giả định — nó là đường đang chạy."""
    ket_qua = agreement(_BO_CHAM, dict.fromkeys(_BO_CHAM))

    assert ket_qua.rate is None
    assert ket_qua.n_compared == 0
    assert ket_qua.lech == []


def test_lech_toan_bo_tra_0_0_chu_khong_phai_none() -> None:
    """Chiều ngược của bài trên: lệch **hết** ⇒ `rate == 0.0`, KHÔNG phải `None`.

    Không có bài này thì một bản vá trả `None` cho mọi trường hợp xấu vẫn xanh ở bài mẫu-số-rỗng —
    và khi đó `None` mất hết ý nghĩa vì nó không còn phân biệt *chưa đo* với *đo ra tệ*. Hai bài
    cùng nhau khoá đúng một bất biến: `None` và `0.0` là **hai câu khác nhau**."""
    dao_het = {case_id: ("refuse" if nhan == "pass" else "pass") for case_id, nhan in _BO_CHAM.items()}

    ket_qua = agreement(_BO_CHAM, dao_het)

    assert ket_qua.rate == 0.0
    assert ket_qua.n_compared == 7
    assert len(ket_qua.lech) == 7


def test_danh_sach_lech_on_dinh_thu_tu() -> None:
    """Danh sách lệch **sắp xếp ổn định** — cùng đầu vào, cùng thứ tự, mọi lần chạy.

    Không phải chi tiết thẩm mỹ: danh sách này đi vào báo cáo ngày, và một thứ tự phụ thuộc thứ tự
    duyệt `dict` sẽ tạo diff giả giữa hai lần chạy trên cùng dữ liệu — đúng lớp nhiễu mà bài
    `test_determinism` của quadrant tồn tại để chặn."""
    nhan_tay_lech_nhieu = {**_NHAN_TAY, "HB-01": "refuse", "HB-03": "pass"}

    lan_1 = agreement(_BO_CHAM, nhan_tay_lech_nhieu).lech
    lan_2 = agreement(dict(reversed(list(_BO_CHAM.items()))), nhan_tay_lech_nhieu).lech

    assert lan_1 == ["HB-01", "HB-03", "HB-04"]
    assert lan_1 == lan_2


def test_nhan_la_vocabulary_thi_raise_khong_dem_thanh_lech() -> None:
    """Nhãn ngoài vocabulary ⇒ **raise**, không lặng lẽ đếm thành lệch. **Fail-closed.**

    Nếu phía sản xuất thêm một giá trị thứ ba (`unsure`, `skip`, …), đếm nó thành *lệch* sẽ làm
    agreement tụt xuống một con số **trông như drift ngữ nghĩa** trong khi thật ra là **vocabulary
    đã đổi** — hai sự cố cần hai phản ứng hoàn toàn khác nhau, và đọc nhầm cái này thành cái kia sẽ
    tốn đúng một ngày đi tìm một drift không tồn tại.

    Cùng lý lẽ với `extra="forbid"` ở T1: giá trị lạ phải **ồn**, không được câm."""
    with pytest.raises(ValueError) as excinfo:
        agreement({**_BO_CHAM, "HB-08": "pass"}, {**_NHAN_TAY, "HB-08": "unsure"})

    assert "unsure" in str(excinfo.value)
    assert "HB-08" in str(excinfo.value)


def test_case_co_nhan_tay_ma_bo_cham_khong_biet_thi_raise() -> None:
    """Nhãn tay cho một case bộ chấm **không có** ⇒ raise, không im lặng bỏ qua.

    Đây chính là dạng drift mà hàm này tồn tại để bắt, ở mức nặng nhất: hai phía **không còn nói về
    cùng một bộ case**. Bỏ qua im lặng sẽ cho ra một `agreement = 1.0` hoàn hảo trên phần giao còn
    lại, tức chỉ số càng đẹp khi hai bên càng lệch nhau."""
    with pytest.raises(ValueError) as excinfo:
        agreement(_BO_CHAM, {**_NHAN_TAY, "HB-99": "refuse"})

    assert "HB-99" in str(excinfo.value)


def _case(case_id: str, *, refusal: bool, nhan: str | None) -> GoldenCase:
    """Case tối thiểu; `refusal=True` dựng bẫy chéo-tenant (trục T1) để `expects_refusal` ra True."""
    return GoldenCase(
        case_id=case_id,
        query="q",
        tenant="ankor",
        section_roles=["hr"],
        expected_tenant="borea" if refusal else "ankor",
        expected_section_role="hr",
        expected="refusal" if refusal else "12 ngày",
        manual_label=nhan,
    )


def test_nhan_tu_golden_set_suy_dung_hai_phia() -> None:
    """Cầu nối: `expects_refusal` (evalhub) → nhãn bộ chấm; `manual_label` (kb) → nhãn tay, **nguyên
    trạng**.

    Đây là **chỗ duy nhất** trong quadrant biết ánh xạ `bool ↔ "refuse"/"pass"`. Gom về một chỗ vì nó
    là điểm khớp giữa hai vocabulary của hai repo: ngày phía sản xuất đổi trục, đúng một hàm phải sửa,
    và bài test vocabulary sẽ chỉ ra nó.

    Nhãn tay đi qua **không biến đổi**, kể cả `None`: hàm này không được phép *đoán* nhãn tay từ dữ
    liệu evalhub — làm vậy là tự sinh ra chính thứ nó đang đi so, và agreement sẽ luôn ra 1.0."""
    golden = GoldenSet(
        golden_set_ref="fx-v1",
        cases=[
            _case("C-01", refusal=False, nhan="pass"),
            _case("C-02", refusal=True, nhan="refuse"),
            _case("C-03", refusal=True, nhan=None),
        ],
    )

    bo_cham, tay = nhan_tu_golden_set(golden)

    assert bo_cham == {"C-01": "pass", "C-02": "refuse", "C-03": "refuse"}
    assert tay == {"C-01": "pass", "C-02": "refuse", "C-03": None}


def test_end_to_end_tren_golden_set_co_nhan_mot_phan() -> None:
    """Đi hết đường: `GoldenSet` → hai bộ nhãn → `agreement`, có **case lệch thật**.

    Fixture bất đối xứng: 4 case, 3 có nhãn, lệch 1 ⇒ `rate = 2/3`, `n_compared = 3`. Case chưa gán
    nhãn không kéo mẫu số lên.

    C-03 là ca đáng giá nhất: kb nói `pass`, evalhub suy ra `refuse`. **Đó chính là hình dạng của một
    semantic drift thật** — đúng lớp bug T6 trước 23/07, khi hai phía bất đồng về việc một case
    chéo-vai thuộc nhánh nào."""
    golden = GoldenSet(
        golden_set_ref="fx-v1",
        cases=[
            _case("C-01", refusal=False, nhan="pass"),
            _case("C-02", refusal=True, nhan="refuse"),
            _case("C-03", refusal=True, nhan="pass"),  # ← LỆCH
            _case("C-04", refusal=False, nhan=None),
        ],
    )

    ket_qua = agreement(*nhan_tu_golden_set(golden))

    assert ket_qua.rate == pytest.approx(2 / 3)
    assert ket_qua.n_compared == 3
    assert ket_qua.lech == ["C-03"]
