"""`compute_scorecard(recipe_hash=…)` — đường **nhận**, không phải đường **sinh** (`DEC-D20-02`).

Ba bài, và bài thứ ba là bài quan trọng nhất trong file.

`publish()` (`workbench@04ca988 publish.py:72`) từ chối **mọi** `Scorecard` có `recipe_hash is None`,
và cổng đó đứng **trước** cổng verdict ở `:78`. Hệ quả đo được hôm nay: bước 7 của money-shot
(*"verdict FAIL → chặn + rollback"*) **chặn đúng, vì lý do sai** — `_reassert_last_published` (`:79`)
không bao giờ chạy ⇒ không có rollback. `DEC-03` (producer của `recipe_hash`, chủ **SWE**) quá hạn từ
D12; ask ① đã gửi.

**T2 KHÔNG sửa một giá trị đang sai.** Nó mở một đường **transit** additive: caller đưa chuỗi nào thì
`Scorecard` mang đúng chuỗi đó. Bất biến đi kèm, và nó là nửa còn lại của "additive":

    caller không truyền  ⇒  hành vi cũ giữ nguyên  ⇒  Scorecard.recipe_hash is None

**Vì sao evalhub không tự băm, kể cả khi `hashlib.sha256(recipe.model_dump_json())` là hai dòng:**
băm **cái gì** chính là câu *"scorecard này chứng nhận cái gì"*, mà `Recipe` là bút SWE. Đo được cạnh
sắc: `Edge.from_` mang `Field(alias="from")` (`contracts/recipe.py:43`) ⇒ `model_dump_json()` ra
`{"from_":…}` còn `by_alias=True` ra `{"from":…}` — **hai chuỗi byte khác nhau cho cùng một recipe**.
Và ngày SWE thêm một field tuỳ chọn vào `Recipe`, **mọi scorecard đã lưu mất hiệu lực trong im
lặng**: không lỗi, không cảnh báo, chỉ một hash không khớp và không ai biết vì sao.

Cùng một luật với `DEC-D19-01` (*đọc, không tính lại*), khác trục: D19 cấm suy `cost` từ `tokens`;
D20 cấm suy `recipe_hash` từ `Recipe`.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from studio_contracts import CaseResult
from studio_evalhub.compute import compute_scorecard

_TS = 0.9
_TC = 0.95

# Nhãn rõ: đây là stand-in trong test, KHÔNG phải một producer. `DEC-D20-02` — chừng nào câu
# "recipe NÀO được chứng nhận cho một run N case" chưa có đáp án, một hash đi từ đường eval không
# mang nghĩa, và một stand-in có nhãn là hình dạng trung thực duy nhất.
_STAND_IN = "stand-in-not-a-producer-abc123"


def _mot_case() -> tuple[list[CaseResult], set[str]]:
    """Bộ nhỏ nhất đủ để `compute_scorecard` chạy — file này canh **transit**, không canh số gộp.

    Số gộp đã có `test_compute_scorecard.py` canh bằng bộ bất đối xứng 2/8. Dựng lại bộ đó ở đây chỉ
    làm bài đỏ vì lý do khác với lý do đang đo."""
    results = [CaseResult(case_id="ANS-0", expected="x", actual="x", success=True, citation_accuracy=1.0)]
    return results, {"ANS-0"}


def test_recipe_hash_truyen_vao_di_thang_ra_scorecard() -> None:
    """**Bài 1 — đường transit có thật.** Caller đưa `recipe_hash="…"` ⇒ `Scorecard` mang **đúng
    chuỗi đó**, không phải một chuỗi được dẫn xuất lại.

    Đỏ trước khi có tham số bằng `TypeError: unexpected keyword argument 'recipe_hash'` — **sai chữ
    ký tính là đỏ đúng lý do** (`ImportError` thì không: nó đỏ vì module không nạp được, không vì
    hành vi thiếu).

    Assert **bằng giá trị**, không bằng `is not None`: `is not None` xanh với cả một cài đặt tự sinh
    hash — đúng thứ `DEC-D20-02` cấm. Chuỗi stand-in ở đây cố tình **không** phải một hex-digest hợp
    lệ, nên bất kỳ đường nào tự băm cũng cho ra giá trị khác và bài này đỏ."""
    results, scored = _mot_case()

    sc = compute_scorecard(
        "agent-x",
        "callisto-golden-30-v1",
        results,
        _TS,
        _TC,
        scored_case_ids=scored,
        recipe_hash=_STAND_IN,
    )

    assert sc.recipe_hash == _STAND_IN


def test_khong_truyen_recipe_hash_thi_van_la_none() -> None:
    """**Bài 2 — nửa còn lại của "additive".** Không truyền ⇒ `recipe_hash is None`, y như trước T2.

    Đây **không** phải bài thừa. Không có nó, một cài đặt đổi default thành `""` hoặc tự sinh một
    hash "cho publish khỏi từ chối" vẫn làm bài 1 xanh — và 11 call-site `EvalHarness().run(...)`
    đang có sẽ âm thầm đổi hành vi.

    `None` ở đây là **giá trị trung thực**, không phải một lỗ hổng cần vá: `DEC-03` chưa có producer,
    nên bịa một chuỗi ở phía eval là nói dối `publish()` về thứ scorecard này chứng nhận. Fail-closed
    sống ở consumer (`publish.py:72`), đúng chỗ của nó."""
    results, scored = _mot_case()

    sc = compute_scorecard("agent-x", "callisto-golden-30-v1", results, _TS, _TC, scored_case_ids=scored)

    assert sc.recipe_hash is None


def test_recipe_hash_la_keyword_only() -> None:
    """**Bài 2b** — `recipe_hash` không nhận được bằng vị trí.

    Chốt hình dạng chữ ký chứ không chỉ hành vi: nếu nó trượt thành positional, một caller đếm nhầm
    thứ tự sẽ đẩy `recipe_hash` vào `threshold_success` (hoặc ngược lại) và bài duy nhất bắt được là
    bài này. `DEC-D20-02` viết **keyword-only** chứ không viết "có tham số recipe_hash"."""
    results, scored = _mot_case()

    with pytest.raises(TypeError, match="positional"):
        compute_scorecard(  # type: ignore[misc]
            "agent-x",
            "callisto-golden-30-v1",
            results,
            _TS,
            _TC,
            _STAND_IN,
            scored_case_ids=scored,
        )


def test_src_khong_tu_dan_xuat_recipe_hash() -> None:
    """**BÀI CHÍ TỬ của T2 — bất biến cưỡng chế của `DEC-D20-02`.** Không file nào trong
    `src/studio_evalhub/` băm, và không file nào gọi `model_dump_json()`.

    Bài này khác hai bài trên: chúng chứng minh **hôm nay** đúng; bài này chặn **vi phạm tương lai**.
    Không có nó, `DEC-D20-02` chỉ là một câu trong plan — và lần sửa nào đó thấy `publish()` từ chối
    hoài sẽ điền `hashlib.sha256(...)` vào `compute.py` cho xong. Chạy tốt, không lỗi, và **sai vĩnh
    viễn**: hash sinh ở evalhub chứng nhận thứ evalhub nghĩ là recipe, không phải thứ SWE dùng để
    publish. Cùng hình với `test_src_khong_hardcode_duong_dan_kb` (`DEC-D16-01`).

    **Quét AST, KHÔNG quét văn bản thô,** và loại docstring có chủ đích: chính docstring là nơi
    `DEC-D20-02` phải được giải thích, kể cả bằng cách viết ra đúng cái tên bị cấm. Quét thô sẽ bắt
    oan mọi câu văn nhắc tới quyết định — và một bài đỏ vì lý do sai là bài sắp bị ai đó nới lỏng."""
    src = Path(__file__).resolve().parent.parent / "src" / "studio_evalhub"
    files = sorted(src.glob("*.py"))
    assert files, f"không tìm thấy file nguồn nào ở {src} — bài này sẽ xanh giả nếu bỏ qua"

    # Tên module băm + tên hàm băm. `hashlib` là đường chính; ba cái sau bắt đường vòng import trực
    # tiếp (`from hashlib import sha256`) lẫn thư viện khác cùng mục đích.
    cam_import = {"hashlib", "blake3", "xxhash"}
    cam_goi = {"model_dump_json", "sha256", "sha1", "md5", "blake2b", "blake2s"}

    # `replay.py` (D22) băm `(prompt, kwargs)` làm khoá cache phát lại — KHÔNG băm `Recipe`, nên
    # nó không thể vi phạm điều `DEC-D20-02` bảo vệ. Miễn trừ **hẹp và có bảo vệ**, không phải lỗ:
    #   · chỉ miễn phần HASHING; `model_dump_json` vẫn cấm ở MỌI file (nửa Recipe-serialization);
    #   · `test_file_duoc_mien_bam_khong_cham_recipe` bên dưới khoá chặt hơn một miễn trừ trần:
    #     file được miễn phải KHÔNG chạm `Recipe` — không có vật để băm sai, chứ không phải
    #     'tin là nó không băm sai'.
    MIEN_TRU_HASH = {"replay.py"}

    vi_pham: list[str] = []
    for file in files:
        tree = ast.parse(file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    goc = alias.name.split(".")[0]
                    if goc in cam_import and file.name not in MIEN_TRU_HASH:
                        vi_pham.append(f"{file.name}:{node.lineno} import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                goc = (node.module or "").split(".")[0]
                if goc in cam_import and file.name not in MIEN_TRU_HASH:
                    vi_pham.append(f"{file.name}:{node.lineno} from {node.module} import …")
            elif isinstance(node, ast.Call):
                ten = node.func.attr if isinstance(node.func, ast.Attribute) else None
                if ten is None and isinstance(node.func, ast.Name):
                    ten = node.func.id
                bi_cam = cam_goi if file.name not in MIEN_TRU_HASH else {"model_dump_json"}
                if ten in bi_cam:
                    vi_pham.append(f"{file.name}:{node.lineno} gọi {ten}()")

    assert not vi_pham, (
        "DEC-D20-02: evalhub NHẬN `recipe_hash`, tuyệt đối không tự dẫn xuất/hash nó. "
        f"Vi phạm: {vi_pham}. Băm cái gì = scorecard chứng nhận cái gì, mà `Recipe` là bút SWE "
        "(DEC-03). Nếu cần một giá trị để publish qua cổng, đường đúng là caller truyền vào — "
        "không phải evalhub tự sinh."
    )


def test_file_duoc_mien_bam_khong_cham_recipe() -> None:
    """Vế thứ hai của bản thu hẹp ở `test_src_khong_tu_dan_xuat_recipe_hash`.

    Một allowlist trần là **lời hứa**; bài này là **phép kiểm**. `replay.py` được miễn kiểm hashing
    với đúng một lý do — nó băm `(prompt, kwargs)` chứ không băm `Recipe`. Ngày ai đó import `Recipe`
    vào file đó rồi băm, `DEC-D20-02` bị vi phạm thật, và bài này đỏ mà không cần ai nhớ ra allowlist
    đang mở cho file nào.

    Kiểm theo **cây cú pháp**, không theo chuỗi: docstring của `replay.py` có nhắc `Recipe` khi giải
    thích `Node.params`, nên một phép `"Recipe" in text` sẽ đỏ oan và bị ai đó vô hiệu hoá cho xong.
    """
    src = Path(__file__).resolve().parent.parent / "src" / "studio_evalhub"
    for ten in ("replay.py",):
        tree = ast.parse((src / ten).read_text(encoding="utf-8"))
        ten_dinh_danh: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                ten_dinh_danh.add(node.id)
            elif isinstance(node, ast.Attribute):
                ten_dinh_danh.add(node.attr)
            elif isinstance(node, ast.ImportFrom):
                ten_dinh_danh.update(alias.name for alias in node.names)
        assert "Recipe" not in ten_dinh_danh, (
            f"{ten} được miễn kiểm hashing với lý do 'không băm Recipe' — nhưng nó vừa chạm `Recipe`. "
            "Hoặc bỏ chỗ chạm đó, hoặc rút file khỏi `MIEN_TRU_HASH` và tìm đường khác."
        )
