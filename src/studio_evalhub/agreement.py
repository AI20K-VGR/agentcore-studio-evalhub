"""Agreement-check — hàm thuần so hai bộ nhãn, trả **ba** giá trị (`DEC-D18-04`, D18/T3).

## Con số này đo cái gì — và KHÔNG đo cái gì

**KHÔNG phải human–machine agreement.** Đo trên `kb#21`: `manual_label` trùng khít `expects_refusal`
ở **10/10** case có nhãn, và phía kb có guard khoá cứng sự trùng đó. `expects_refusal` lại là thuộc
tính **dẫn xuất** từ `expected_tenant`/`tenant`/`expected_section_role`/`section_roles` — dữ liệu
golden-30 đã tự khai. ⇒ nhãn tay **không mang thông tin nào độc lập** với bộ case. Gọi nó là *"đồng
thuận người–máy"* là tuyên bố một phép đo không tồn tại.

**Cái nó THẬT SỰ đo: đồng thuận ngữ nghĩa hàng rào kb ↔ evalhub.** Hai phía suy ra cùng một ngữ
nghĩa (*case này thuộc nhánh trả-lời hay nhánh từ-chối*) bằng **hai bản cài đặt độc lập, ở hai repo
khác nhau**. So chúng là một **regression detector cho semantic drift** giữa hai repo.

Giá trị đó không lý thuyết — nó có tiền lệ đã trả giá: trước 23/07 `expects_refusal` chỉ xét trục T1
chéo-tenant, bỏ trục T6 chéo-vai, nên case chéo-vai cùng tenant rơi nhầm nhánh trả-lời-được và agent
từ chối **đúng** bị chấm FAIL. Một bộ dò lệch hai phía sẽ bắn ngay hôm đó thay vì để bug sống tới khi
có người đọc lại luật chấm.

## Ba giá trị, không phải một

Một `rate` trần là **đúng thứ `kit#134` gọi là bằng chứng dị dạng** — tỷ lệ không kèm mẫu số.
`DEC-D16-03` đã trả giá cho bài học này một lần (`n_scored_citation` phải đi cạnh
`citation_accuracy`); không lặp lại ở trục mới. Danh sách case lệch là thứ biến con số thành **hành
động được**: `0.85` không nói được gì, còn *"lệch ở HB-04"* thì mở đúng case đó ra là thấy.

## Hàm này KHÔNG tự gán nhãn THẬT/CƠ CHẾ

Nó nhận hai bộ nhãn và trả ba thứ, hết. Việc gán THẬT/CƠ CHẾ là của **người viết báo cáo**, theo cổng
2/2 của `DEC-D18-04` (dữ liệu đã về **và** trục đã chốt). Nhét luật đó vào hàm là để một hàm thuần
quyết định một câu về **phương pháp** mà nó không có dữ liệu để quyết.
"""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from studio_evalhub.golden_case import GoldenSet


class AgreementResult(BaseModel):
    """Kết quả một lần so nhãn — ba trường, và không trường nào bỏ được."""

    model_config = ConfigDict(frozen=True)

    rate: float | None
    """Tỷ lệ đồng thuận trên các case **có nhãn tay**. `None` khi `n_compared == 0`.

    **`None` ≠ `0.0`**: *chưa đo được* khác *đo được và bằng không*. Trả `0.0` cho mẫu số rỗng là in
    ra một con số không phân biệt được với một phép đo thật — cùng luật `Aggregate.citation_accuracy`
    (`DEC-D16-03`)."""

    n_compared: int
    """Mẫu số — số case thực sự tham gia so. Case chưa gán nhãn tay **không** nằm trong đây."""

    lech: list[str]
    """`case_id` của các case hai phía bất đồng, **sắp xếp ổn định**. Thứ tự cố định vì danh sách này
    đi vào báo cáo ngày; phụ thuộc thứ tự duyệt `dict` sẽ tạo diff giả giữa hai lần chạy cùng dữ
    liệu."""


_VOCABULARY = frozenset({"pass", "refuse"})
"""Tập giá trị nhãn hợp lệ — vocabulary của phía **sản xuất** (kb, `#115`), không phải của evalhub.

Khai tường minh thay vì so hai chuỗi bất kỳ, vì giá trị lạ phải **ồn**: đếm một `unsure`/`skip` thành
*lệch* sẽ kéo agreement xuống một con số **trông như semantic drift** trong khi thật ra là
**vocabulary đã đổi** — hai sự cố cần hai phản ứng hoàn toàn khác nhau. Cùng lý lẽ `extra="forbid"`
của `GoldenCase` (`DEC-D18-01`).

Ngày phía sản xuất chốt thêm giá trị, sửa ở **đúng một chỗ này**, và bài test vocabulary sẽ chỉ ra nó.
"""


def agreement(
    nhan_bo_cham: Mapping[str, str],
    nhan_tay: Mapping[str, str | None],
) -> AgreementResult:
    """So `nhan_bo_cham` (evalhub suy ra) với `nhan_tay` (kb gán) trên các case **có nhãn**.

    Hàm thuần: không đọc file, không phụ thuộc judge, không biết THẬT hay CƠ CHẾ.

    **Ba đường fail-closed**, mỗi đường chặn một kiểu *"con số sai mà trông hợp lệ"*:

    - `nhan_tay[case] is None` ⇒ **loại khỏi mẫu số**, không tính là lệch. `None` là *chưa gán nhãn*,
      không phải *bất đồng*; đếm nó thành lệch làm mọi bộ gán nhãn một phần trông như drift nặng.
    - nhãn ngoài `_VOCABULARY` ⇒ `ValueError` nêu **cả `case_id` lẫn giá trị lạ**.
    - có nhãn tay cho case bộ chấm **không biết** ⇒ `ValueError`. Đây là drift ở mức nặng nhất — hai
      phía không còn nói về cùng một bộ case — và bỏ qua im lặng sẽ cho `rate` **càng đẹp khi hai bên
      càng lệch**, vì phần giao còn lại toàn case khớp.
    """
    la_bo_cham = sorted(set(nhan_tay) - set(nhan_bo_cham))
    if la_bo_cham:
        raise ValueError(f"nhãn tay cho case bộ chấm không biết — hai phía lệch bộ case: {la_bo_cham}")

    so_sanh: list[tuple[str, str, str]] = []
    for case_id in sorted(nhan_bo_cham):
        tay = nhan_tay.get(case_id)
        if tay is None:
            continue
        cham = nhan_bo_cham[case_id]
        for nguon, nhan in (("nhãn tay", tay), ("bộ chấm", cham)):
            if nhan not in _VOCABULARY:
                raise ValueError(
                    f"{nguon} của {case_id} mang giá trị ngoài vocabulary: {nhan!r} ∉ {sorted(_VOCABULARY)}"
                )
        so_sanh.append((case_id, cham, tay))

    lech = [case_id for case_id, cham, tay in so_sanh if cham != tay]
    n_compared = len(so_sanh)
    # Mẫu số rỗng ⇒ `None`, KHÔNG `0.0` — *chưa đo được* ≠ *đo được và bằng không* (`M-J5`).
    rate = None if n_compared == 0 else (n_compared - len(lech)) / n_compared
    return AgreementResult(rate=rate, n_compared=n_compared, lech=lech)


def nhan_tu_golden_set(golden: GoldenSet) -> tuple[dict[str, str], dict[str, str | None]]:
    """Rút `(nhãn bộ chấm, nhãn tay)` từ một `GoldenSet` — cầu nối giữa hai vocabulary.

    - **nhãn bộ chấm** suy từ `expects_refusal` (evalhub tính, từ hai trục hàng rào T1/T6);
    - **nhãn tay** là `manual_label` (kb gán), đi qua **nguyên trạng**, kể cả `None`.

    **Chỗ DUY NHẤT trong quadrant biết ánh xạ `bool ↔ "refuse"/"pass"`.** Gom về một chỗ vì đây là
    điểm khớp giữa hai vocabulary của hai repo: ngày phía sản xuất đổi trục nhãn, đúng một hàm phải
    sửa, và bài test vocabulary chỉ thẳng vào nó.

    **Không được "đoán" nhãn tay từ dữ liệu evalhub** khi nó vắng. Điền `expects_refusal` vào chỗ
    `manual_label is None` sẽ làm hàm tự sinh ra chính thứ nó đang đi so — agreement luôn ra `1.0`,
    trên một mẫu số phồng lên bằng cả bộ case. Đó là dạng xanh-giả tệ nhất có thể có ở trục này:
    một bộ dò drift **không bao giờ bắn**.
    """
    nhan_bo_cham = {case.case_id: ("refuse" if case.expects_refusal else "pass") for case in golden.cases}
    nhan_tay: dict[str, str | None] = {case.case_id: case.manual_label for case in golden.cases}
    return nhan_bo_cham, nhan_tay
