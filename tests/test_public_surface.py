"""Lưới quét bề mặt công khai — `__all__` phải **phủ kín**, D19/T6 (`kit#123`).

## Vì sao món nợ này cần một lưới chứ không cần một lần sửa

`__all__` thiếu tên đã là nợ **hai ngày** (`T9a`, D18), và mỗi lần đếm lại ra một con số khác:

```text
D18  đếm tay          →  3 tên thiếu
D19  plan đếm lại     →  7 tên thiếu
T6   đếm bằng AST     → 19 tên chưa phân loại
```

Ba lần đếm, ba con số, và cả ba đều **đếm bằng mắt**. Một lần sửa nữa cũng sẽ hụt lần thứ tư — thứ
thiếu không phải là công sức, mà là **một phép đếm chạy được**.

Nên bài này không kiểm *"`__all__` có đủ 19 tên không"* (một danh sách gõ tay đối chiếu một danh
sách gõ tay là tautology). Nó kiểm: **mọi tên public khai trong gói đều đã được phân loại** — hoặc
xuất ở `__all__`, hoặc nằm trong `KHONG_XUAT` kèm lý do. Thêm một hàm public mới mà quên khai ⇒ đỏ
ngay, và người thêm buộc phải **quyết một cách có ý thức** thay vì để nó rơi im lặng.

Đây đúng khuôn lưới `RUN_CASE_COLUMNS` / `RUN_CASE_FIELDS_NOT_SHOWN` (`render.py:75-85`) đang dùng
cho `SmokeResult.model_fields`, chỉ đổi tập nền từ *field của một model* sang *tên public của cả
gói*. Khuôn đó đã bắt được đúng lỗi này một lần ở D12 (`expects_refusal` là field thứ 6 thêm vào mà
danh sách trong test còn gõ tay).

## "Public" định nghĩa bằng gì

Tên **module-level** không bắt đầu bằng `_`, khai trong `src/studio_evalhub/*.py` (trừ `__init__.py`):
`class` · `def` · `async def` · gán thường · gán có annotation. Quét bằng **AST**, không bằng `dir()`
— `dir()` trả cả tên **import vào** module, nên nó sẽ đòi khai `UUID`, `Path`, `BaseModel`… tức đo
nhầm thứ khác hẳn.
"""

from __future__ import annotations

import ast
import pathlib

import studio_evalhub

KHONG_XUAT: dict[str, str] = {
    "Pool": (
        "alias kiểu của psycopg (`run_report.py:53` — `AsyncConnectionPool[AsyncConnection[Any]]`), "
        "không phải API của evalhub. Xuất nó là hứa một kiểu bên thứ ba qua bề mặt của mình."
    ),
    "main": (
        "entry-point CLI, gọi bằng `python -m studio_evalhub.run_report` chứ không import. "
        "Có HAI hàm cùng tên (`cli.py` và `run_report.py`) nên xuất còn va nhau ở tầng tên."
    ),
    "RUN_CASE_COLUMNS": "khai báo lưới nội bộ cho bảng per-case; consumer là test, không phải caller.",
    "RUN_CASE_FIELDS_NOT_SHOWN": "cùng lý do `RUN_CASE_COLUMNS`.",
}
"""Tên public **cố ý không** xuất, kèm lý do — cùng vai `RUN_CASE_FIELDS_NOT_SHOWN`.

Bắt buộc có lý do chứ không chỉ có tên: một danh sách loại trừ không lý do là chỗ để người sau nhét
thêm vào cho lưới hết đỏ, và khi đó lưới thành trang trí."""


def _ten_public_khai_trong_goi() -> dict[str, str]:
    """`{tên: file khai}` cho mọi tên public module-level trong gói. Quét AST, xem docstring module."""
    src = pathlib.Path(studio_evalhub.__file__).parent
    files = sorted(f for f in src.glob("*.py") if f.name != "__init__.py")
    assert len(files) >= 10, f"chỉ quét được {len(files)} module — nghi resolve sai gốc, bài xanh giả"

    ket: dict[str, str] = {}
    for f in files:
        for node in ast.parse(f.read_text(encoding="utf-8")).body:
            ten: str | None = None
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                ten = node.name
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                ten = node.target.id
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and not t.id.startswith("_"):
                        ket.setdefault(t.id, f.name)
                continue
            if ten and not ten.startswith("_"):
                ket.setdefault(ten, f.name)
    return ket


def test_moi_ten_public_deu_da_duoc_phan_loai() -> None:
    """Lưới chính: `__all__` ∪ `KHONG_XUAT` phải **phủ kín** tên public của gói.

    Thêm một `def` public vào bất kỳ module nào mà không khai ⇒ bài này đỏ, nêu đúng tên và file.
    """
    khai_trong_goi = _ten_public_khai_trong_goi()
    da_phan_loai = set(studio_evalhub.__all__) | set(KHONG_XUAT)

    chua_phan_loai = {ten: f for ten, f in khai_trong_goi.items() if ten not in da_phan_loai}

    assert chua_phan_loai == {}, (
        f"tên public chưa phân loại: {chua_phan_loai}. Thêm vào `__all__` nếu nó là API công khai, "
        "hoặc vào `KHONG_XUAT` kèm lý do nếu cố ý không xuất."
    )


def test_khong_khai_thua_ten_khong_ton_tai() -> None:
    """Chiều ngược: không được khai một tên gói không có.

    Thiếu vế này thì `__all__` phình lên bằng cách thêm tên bừa cho lưới hết đỏ. Kiểm **cả hai**
    danh sách, vì `KHONG_XUAT` cũng mục theo cùng một kiểu.
    """
    khai_trong_goi = _ten_public_khai_trong_goi()

    thua_all = [t for t in studio_evalhub.__all__ if t not in khai_trong_goi]
    thua_khong_xuat = [t for t in KHONG_XUAT if t not in khai_trong_goi]

    assert thua_all == [], f"`__all__` khai tên gói không khai ở module nào: {thua_all}"
    assert thua_khong_xuat == [], f"`KHONG_XUAT` khai tên không tồn tại: {thua_khong_xuat}"


def test_moi_ten_trong_all_deu_import_duoc_that() -> None:
    """Khai suông không tính — mỗi tên trong `__all__` phải lấy được từ chính gói.

    `kit#74` chấm bằng *fresh clone rồi chạy lệnh y nguyên*: một tên chỉ import được qua đường module
    con là một tên **không giao**.
    """
    thieu = [t for t in studio_evalhub.__all__ if not hasattr(studio_evalhub, t)]

    assert thieu == [], f"`__all__` khai tên gói không export được: {thieu}"


def test_mot_ten_khong_the_vua_xuat_vua_khong_xuat() -> None:
    """Hai tập phải rời nhau — cùng ràng buộc `RUN_CASE_COLUMNS ∩ RUN_CASE_FIELDS_NOT_SHOWN = ∅`."""
    giao = set(studio_evalhub.__all__) & set(KHONG_XUAT)

    assert giao == set(), f"vừa khai xuất vừa khai không xuất: {giao}"


def test_moi_muc_KHONG_XUAT_deu_co_ly_do() -> None:
    """Lý do là bắt buộc, và phải là một câu thật.

    Một danh sách loại trừ không lý do là chỗ để người sau nhét tên vào cho lưới hết đỏ — lúc đó lưới
    thành trang trí. Ngưỡng độ dài không phải để chấm văn: nó chặn `""` và `"n/a"`.
    """
    so_sai = {ten: ly_do for ten, ly_do in KHONG_XUAT.items() if len(ly_do.strip()) < 30}

    assert so_sai == {}, f"mục KHONG_XUAT thiếu lý do thật: {so_sai}"


# ── ghim hình dạng output của happy-path (T6) ───────────────────────────────────────────────────


_KHOI_COST_DA_DO = [
    "cost (Σ, USD)          0.011994",
    "mẫu số cost            6 event",
]
"""Hình dạng **chốt** của khối cost khi run đã được áp giá.

Ghim nguyên văn cả dòng, kể cả khoảng trắng căn cột — vì đây là thứ **người đọc nhìn**, và mọi mode
trong `docs/design-notes/aie2-day19-eval-failure-modes.md` thuộc nhóm `E-1`/`E-6` đều là lỗi **chỉ
tồn tại ở tầng in**: số đúng ở tầng giá trị, sai ở tầng chuỗi.

Bài dùng bảng này là **characterization test**: nó không nói hình dạng này *tốt*, nó nói hình dạng
này **đang là thế** — nên đổi format phải là một hành động có chủ ý, kèm sửa bảng này, chứ không
trôi qua im lặng trong một commit về việc khác."""

_KHOI_COST_CHUA_NOI_GIA = [
    "cost (Σ, USD)          chưa-nối-giá (Σtokens=2030, cost=0) — emit chưa áp giá "
    "(engine:interpreter.py:438 `_NO_COST`); chặn ở kit#121 + Q-A (`cost_of` → contracts)",
    "mẫu số cost            6 event",
]
"""Hình dạng **chốt** của khối cost khi `Σtokens > 0` mà `Σcost == 0` — trạng thái của **mọi run
thật trong hệ thống hôm nay**.

Ghim cả phần trỏ chỗ tắc (`kit#121` + Q-A), không chỉ phần nhãn: bỏ nó đi thì người đọc biết *"chưa
đo"* mà không biết **hỏi ai**, và một nhãn không có chủ là một nhãn sẽ bị lờ đi."""


def _khoi_cost(out: str) -> list[str]:
    """Hai dòng cost, theo thứ tự xuất hiện. Neo theo **dòng**, không quét cả output.

    Lý do neo theo dòng nằm ở `docs/mutations/cost-lineage-d19.md` §4: mutant `M-C6` đã chứng minh
    `assert <chuỗi> in out` xanh trên một renderer hỏng, vì khối caveat prose của chính bảng này chứa
    sẵn các giá trị đang đi tìm.
    """
    return [d for d in out.splitlines() if d.startswith(("cost (", "mẫu số cost"))]


def test_ghim_hinh_dang_khoi_cost_da_do() -> None:
    """Khối cost của run đã áp giá — so **nguyên văn**, không so từng mảnh."""
    from uuid import UUID

    from studio_evalhub import RunCost, SmokeResult, render_run_cases

    out = render_run_cases(
        [
            SmokeResult(
                case_id="HB-01",
                expected="3 ngày làm việc",
                actual="Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
                success=True,
                citation_accuracy=1.0,
                expects_refusal=False,
            )
        ],
        run_id="r1",
        golden_set_ref="golden-30@d19",
        trace_source="obs.trace_events (test)",
        run_cost=RunCost(
            run_id="r1",
            tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
            prompt_tokens=1538,
            completion_tokens=492,
            cost=0.011994,
            event_count=6,
            priced=True,
        ),
    )

    assert _khoi_cost(out) == _KHOI_COST_DA_DO


def test_ghim_hinh_dang_khoi_cost_chua_noi_gia() -> None:
    """Khối cost của run chưa áp giá — nhánh mà **mọi run thật hôm nay** đi qua."""
    from uuid import UUID

    from studio_evalhub import RunCost, SmokeResult, render_run_cases

    out = render_run_cases(
        [
            SmokeResult(
                case_id="HB-01",
                expected="3 ngày làm việc",
                actual="Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
                success=True,
                citation_accuracy=1.0,
                expects_refusal=False,
            )
        ],
        run_id="r1",
        golden_set_ref="golden-30@d19",
        trace_source="obs.trace_events (test)",
        run_cost=RunCost(
            run_id="r1",
            tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
            prompt_tokens=1538,
            completion_tokens=492,
            cost=0.0,
            event_count=6,
            priced=False,
        ),
    )

    assert _khoi_cost(out) == _KHOI_COST_CHUA_NOI_GIA


def test_khong_truyen_run_cost_thi_khoi_cost_RONG() -> None:
    """Đường cũ: `None` ⇒ **0 dòng** cost. Ghim bằng chính hàm rút khối, không bằng `"cost" not in out`.

    Vế `== []` mạnh hơn: nó bắt cả trường hợp renderer in một khối cost **rỗng** hoặc in `todo:`.
    """
    from studio_evalhub import SmokeResult, render_run_cases

    out = render_run_cases(
        [
            SmokeResult(
                case_id="HB-01",
                expected="3 ngày làm việc",
                actual="Nhân viên cần báo trước tối thiểu 3 ngày làm việc.",
                success=True,
                citation_accuracy=1.0,
                expects_refusal=False,
            )
        ],
        run_id="r1",
        golden_set_ref="golden-30@d19",
        trace_source="obs.trace_events (test)",
    )

    assert _khoi_cost(out) == []
    assert "todo:" not in out
