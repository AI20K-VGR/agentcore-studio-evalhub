"""Test `load_golden_set` — unit, **KHÔNG chạm `packages/kb`**.

Cả sáu bài dựng YAML bằng `tmp_path`, nội dung viết ngay trong bài. Không bài nào biết golden-30 của
DE nằm ở đâu — và đó là điều kiện để chúng còn là **unit test của loader**. Một bài unit đọc file của
DE sẽ đỏ vì những lý do chẳng liên quan gì tới loader (DE đổi tên file, submodule chưa init, chạy từ
clone riêng evalhub), và khi đó suite không còn phân biệt được *"loader vỡ"* với *"dữ liệu đi chỗ
khác"* — hai sự cố cần hai phản ứng hoàn toàn khác nhau. Bài đọc file thật nằm ở
`tests/integration/test_golden_30_that.py`.

KHÓA `DEC-D16-01`: `expect_ref` bắt buộc + lệch ⇒ raise · ref đọc từ **nội dung**, không từ **tên
file** · `src/` không mang đường dẫn kb.

**Fixture bất đối xứng có chủ đích: 3 trả-lời / 1 từ-chối**, không 2/2. Tỷ lệ cân là chỗ một mutant
đảo nhánh vẫn cho ra cùng con số.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError
from studio_evalhub.golden_loader import load_golden_set

_REF = "gs-unit-v1"

_YAML_4_CASE = """\
golden_set_ref: gs-unit-v1
cases:
  - case_id: U-01
    query: "Nghỉ phép năm được bao nhiêu ngày?"
    tenant: ankor
    section_roles: [hr]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "12 ngày"
    expected_citation: ["ankor-leave-001#c1"]
  - case_id: U-02
    query: "Quy trình duyệt chi phí đi lại?"
    tenant: ankor
    section_roles: [hr, finance]
    expected_tenant: ankor
    expected_section_role: finance
    expected: "3 ngày làm việc"
    expected_citation: ["ankor-expense-002#c1"]
  - case_id: U-03
    query: "Giờ làm việc tiêu chuẩn?"
    tenant: borea
    section_roles: [public]
    expected_tenant: borea
    expected_section_role: public
    expected: "8 giờ"
    expected_citation: ["borea-hours-001#c1"]
  - case_id: U-04
    query: "Thưởng cuối năm của ankor là bao nhiêu?"
    tenant: borea
    section_roles: [public]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "refusal"
    expected_citation: []
"""


def _write(tmp_path: Path, name: str, text: str = _YAML_4_CASE) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_loader_doc_ref_mismatch_raises(tmp_path: Path) -> None:
    """File khai `golden_set_ref: X` mà caller đòi `Y` ⇒ **raise**, không cảnh báo rồi chạy tiếp.

    Đây là bài giữ đúng cái bẫy đã đo được ở nền D16: file tên `callisto-handbook-30-**draft**.yaml`
    nhưng ref bên trong là `callisto-golden-30-**v1**`. Không có bài này thì ngày ai đó truyền nhầm
    ref là ngày harness chạy **một bộ case khác** với bộ nó tưởng đang chạy — và không lỗi nào nổi
    lên, vì mọi case đều hợp lệ, chỉ là sai bộ."""
    path = _write(tmp_path, "bo-nao-do.yaml")

    with pytest.raises(ValueError) as excinfo:
        load_golden_set(path, expect_ref="gs-khac-v9")

    # Thông báo phải mang CẢ HAI ref: người đọc log cần biết đã đòi gì và nhận được gì, không phải
    # một câu "mismatch" rồi tự đi mở file.
    message = str(excinfo.value)
    assert _REF in message
    assert "gs-khac-v9" in message


def test_loader_khong_suy_ref_tu_ten_file(tmp_path: Path) -> None:
    """**Cùng một nội dung, hai tên file khác nhau ⇒ cả hai nạp được với cùng `expect_ref`.**

    Bài này khoá chiều ngược của bài trên: ref là thứ đọc từ **nội dung**, tên file chỉ là đường dẫn.
    Nó tồn tại để ngày DE bỏ chữ `draft` khỏi tên file không làm gãy gì cả — và để không ai "tối ưu"
    loader bằng cách parse tên file, thứ sẽ chạy đúng đúng một lần rồi sai im lặng mãi về sau."""
    duong_dan_draft = _write(tmp_path, "callisto-handbook-30-draft.yaml")
    duong_dan_v1 = _write(tmp_path, "callisto-handbook-30-v1.yaml")

    tu_draft = load_golden_set(duong_dan_draft, expect_ref=_REF)
    tu_v1 = load_golden_set(duong_dan_v1, expect_ref=_REF)

    assert tu_draft.golden_set_ref == _REF
    assert tu_v1.golden_set_ref == _REF
    assert tu_draft == tu_v1

    # Fixture bất đối xứng: 3 trả-lời / 1 từ-chối. Nếu loader (hay `expects_refusal`) đảo nhánh, con
    # số này đổi — với 2/2 thì không.
    assert [c.case_id for c in tu_draft.cases if c.expects_refusal] == ["U-04"]
    assert len([c for c in tu_draft.cases if not c.expects_refusal]) == 3


def test_loader_thieu_field_raises(tmp_path: Path) -> None:
    """Thiếu `expected_section_role` ở **một** case ⇒ `ValidationError`, không default âm thầm.

    Fail-closed đúng chỗ: `expected_section_role` là trục thứ hai của hàng rào (T6 chéo-vai) và
    **không suy được** từ `expected_citation` (`golden_case.py:69-71`). Một loader tự điền default
    cho nó sẽ đẩy case chéo-vai sang nhánh trả-lời-được, và agent từ chối ĐÚNG bị chấm FAIL — đúng
    con bug đã xảy ra trước 23/07."""
    thieu = _YAML_4_CASE.replace("    expected_section_role: finance\n", "", 1)
    path = _write(tmp_path, "thieu-field.yaml", thieu)

    with pytest.raises(ValidationError):
        load_golden_set(path, expect_ref=_REF)


def test_loader_manual_label_sai_ten_do_tai_loader(tmp_path: Path) -> None:
    """`DEC-D18-01` — nhãn tay **sai tên** trong yaml ⇒ đỏ **tại loader**, thông báo mang tên field sai.

    Bài `test_manual_label_sai_ten_phai_do` khoá cùng bất biến ở tầng **kiểu**; bài này khoá nó trên
    **đường đi thật của dữ liệu**: DE không dựng `GoldenCase` bằng Python, DE emit yaml rồi loader
    nạp. Chỉ có bài ở tầng kiểu thì một ngày loader chèn thêm một bước làm sạch dict (lọc key lạ
    "cho an toàn") sẽ trả `extra="forbid"` về vô hiệu mà bài kia vẫn xanh.

    Vì sao thông báo phải mang **tên field sai** chứ không chỉ "validation error": người nhận lỗi
    này là DE, đang sửa file của họ, và thứ họ cần biết là **gõ nhầm chữ nào** — không phải mở
    `golden_case.py` của quadrant khác mà đối chiếu."""
    sai_ten = _YAML_4_CASE.replace(
        '    expected: "12 ngày"\n',
        '    expected: "12 ngày"\n    manaul_label: ANSWER\n',
        1,
    )
    path = _write(tmp_path, "nhan-sai-ten.yaml", sai_ten)

    with pytest.raises(ValidationError) as excinfo:
        load_golden_set(path, expect_ref=_REF)

    assert "manaul_label" in str(excinfo.value)


def test_loader_manual_label_doc_duoc_theo_tung_case(tmp_path: Path) -> None:
    """Nhãn tay đi qua loader **về đúng case của nó**, và case không có nhãn ⇒ `None`.

    **Fixture bất đối xứng ở cả hai trục**, không phải chỉ "có nhãn / không nhãn":

    - vị trí — nhãn nằm ở case **1** và case **4**, hai case giữa bỏ trống. Gán đủ 4 case thì một
      mutant phát nhãn của case đầu cho mọi case vẫn cho ra cùng kết quả;
    - giá trị — hai nhãn **khác nhau** (`ANSWER` / `REFUSE`). Cùng một giá trị thì mutant trả hằng
      số sống sót.

    Assert nguyên **danh sách theo thứ tự** thay vì đếm số case có nhãn: `len([...]) == 2` xanh kể
    cả khi hai nhãn dán nhầm sang hai case khác, mà nhãn dán nhầm case chính là dạng hỏng khiến
    agreement-check ra một con số **sai mà trông hợp lệ**.

    Giá trị nhãn ở đây là **chỗ giữ chỗ**, không phải vocabulary đã chốt — trục nhãn là của DE
    (`#115`), xem docstring `GoldenCase.manual_label`. Bài này khoá **đường đi** của nhãn, không
    khoá tập giá trị hợp lệ."""
    co_nhan = _YAML_4_CASE.replace(
        '    expected: "12 ngày"\n',
        '    expected: "12 ngày"\n    manual_label: ANSWER\n',
        1,
    ).replace(
        '    expected: "refusal"\n',
        '    expected: "refusal"\n    manual_label: REFUSE\n',
        1,
    )
    path = _write(tmp_path, "co-nhan-tay.yaml", co_nhan)

    golden = load_golden_set(path, expect_ref=_REF)

    assert [c.manual_label for c in golden.cases] == ["ANSWER", None, None, "REFUSE"]


def test_src_khong_hardcode_duong_dan_kb() -> None:
    """**Bất biến cưỡng chế của `DEC-D16-01`:** không file nào trong `src/studio_evalhub/` mang một
    đường dẫn tới kho của DE.

    Bài này khác mọi bài còn lại trong file: nó không chứng minh loader hôm nay đúng, nó chặn **vi
    phạm tương lai**. Không có nó thì `DEC-D16-01` chỉ là một câu trong decision-log, và lần sửa nào
    đó thấy tiện sẽ điền thẳng `packages/kb/golden/...` vào một default — chạy tốt trong workspace,
    `FileNotFoundError` trong fresh clone của `kit#74`.

    **Quét literal chuỗi, KHÔNG quét văn bản thô.** Docstring nằm ngoài phạm vi có chủ đích: một
    docstring không bao giờ là đường dẫn được mở, và chính DEC này cần được giải thích ở nơi nó bị
    vi phạm. Quét thô sẽ bắt oan mọi câu văn nhắc tới quyết định, và một bài đỏ vì lý do sai là bài
    sắp bị ai đó nới lỏng."""
    src = Path(__file__).resolve().parent.parent / "src" / "studio_evalhub"
    files = sorted(src.glob("*.py"))
    assert files, f"không tìm thấy file nguồn nào ở {src} — bài này sẽ xanh giả nếu bỏ qua"

    vi_pham: list[str] = []
    for file in files:
        tree = ast.parse(file.read_text(encoding="utf-8"))

        # Đánh dấu node docstring để loại khỏi phạm vi quét (module/class/function đều có thể có).
        docstrings: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                first = node.body[0] if node.body else None
                if (
                    isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)
                ):
                    docstrings.add(id(first.value))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if id(node) in docstrings:
                continue
            if "packages/kb" in node.value or "golden/" in node.value:
                vi_pham.append(f"{file.name}:{node.lineno} → {node.value!r}")

    assert not vi_pham, (
        "DEC-D16-01: src/ không được biết golden-set nằm ở đâu — đường dẫn do caller truyền.\n" + "\n".join(vi_pham)
    )
