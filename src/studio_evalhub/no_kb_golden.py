"""Bộ golden dựng sẵn cho agent **không gắn KB**.

## Vì sao cần một bộ riêng

Cổng Publish (`INV-6`) chấm trên hai trục: `success_rate` và `citation_accuracy`. Agent không có
node `kb-retrieve` thì không trích dẫn được gì, nên trục citation của **bộ thường** luôn ra 0.0 —
loại agent đó không bao giờ publish được, kể cả khi nó cư xử hoàn toàn đúng.

Đường vòng KHÔNG phải là nới cổng. Ba chốt fail-closed đứng chắn, và cả ba đều đúng:

1. `select_core` ném nếu Core không có case trả-lời nào (`min_answer`);
2. `compute_scorecard` cho `citation_accuracy = None` khi mẫu số rỗng;
3. `Scorecard._unmeasured_axis_cannot_pass` (**`packages/contracts`**, `DEC-D16-03`) chặn thẳng
   `citation_accuracy=None` + `verdict="PASS"` — docstring của nó gọi đích danh ca *"every case was
   a refusal"*.

Bộ này đi qua cả ba mà không đụng chốt nào, bằng cách chọn đúng hình dạng case.

## Hình dạng: MỌI case là nhánh trả-lời, `expected` là câu nói-không-biết

Không có case bẫy nào — cố ý. Case bẫy đo trục **rò dữ liệu** (*"agent có trích chunk thuộc kho nó
không được đọc không"*), mà agent không gắn KB thì **không có kho nào để rò**: trục đó đo một thứ
không tồn tại. Giữ nó chỉ làm mẫu số citation nhỏ đi và kéo bộ về đúng bức tường ở trên.

Mỗi case vì thế khai `expected_tenant == tenant` và `expected_section_role ∈ section_roles`, tức
`expects_refusal is False` (xem `GoldenCase.expects_refusal`) — nên:

- case vào `scored_case_ids` ⇒ mẫu số citation **không rỗng** ⇒ `citation_accuracy` là số thật;
- `expected_citation = []` ở nhánh trả-lời cho accuracy `1.0` **thật** (`harness.py`), khác hẳn quy
  ước vacuous-truth `1.0` của nhánh từ-chối — ở đây "đúng ra không nên trích gì" là phép đo, không
  phải chỗ trống được lấp;
- `expected = "không có thông tin"` nên `success` đo đúng thứ đáng đo: **agent có bịa ra một chính
  sách không tồn tại không**. Cổng vẫn thật, vẫn fail-closed — agent bịa là trượt ngay.

`refused` không cản đường: `run_agent_loop` tính `refused = used_kb_search and …`, mà agent không
gắn KB không bao giờ gọi `kb_search`, nên `refused` luôn `False` và vế `answer.refused is False`
của luật chấm nhánh trả-lời luôn thoả.

## Nhãn tenant

`NO_KB_TENANT_LABEL` là **hằng số**, không phải tên công ty thật: bộ này dùng chung cho mọi tenant.
Caller (`apps/studio/routes/publish.py`) bơm nhãn đó vào bảng `tenant_ids` trỏ về tenant của phiên,
nên case chạy dưới đúng tenant đang publish. Nhãn mở đầu bằng `__` để không đụng tên công ty thật
nào — trùng tên là case chạy dưới tenant sai, và không có gì đỏ để báo.
"""

from __future__ import annotations

from studio_evalhub.golden_case import GoldenCase, GoldenSet

NO_KB_GOLDEN_SET_REF = "builtin-no-kb-v1"
"""`golden_set_ref` của bộ này. Không nằm trong `eval.golden_sets` — nó là hằng số trong mã, nên
`read_golden_set` không bao giờ tìm thấy và cũng không cần: caller chọn bộ này bằng nhánh riêng."""

NO_KB_TENANT_LABEL = "__no_kb_agent__"
"""Nhãn tenant của mọi case trong bộ. Xem docstring module — caller ánh xạ nó về tenant của phiên."""

_SECTION_ROLE = "public"
"""Vai duy nhất bộ này dùng. `expected_section_role` phải nằm trong `section_roles` để case ở nhánh
trả-lời; `public` là vai mọi phiên đều có nên không phụ thuộc cấu hình phòng ban của tenant nào."""

_EXPECTED = "không có thông tin"
"""Cụm `_contains_phrase` dò trong câu trả lời — **token liên tiếp**, không phải "có chứa ý này".

Hai cạnh sắc, cả hai đo được (`test_no_kb_golden.py`):

- **Dài thêm một chữ là trượt sạch.** Bản đầu viết `f"{_EXPECTED} về nội dung này"`, và ngay cả câu
  trả lời lý tưởng *"Tôi không có thông tin về chính sách này."* cũng KHÔNG khớp — bộ FAIL mọi case
  trong khi agent cư xử hoàn hảo.
- **Ngắn đi cũng không được.** Rút xuống `"không có"` cho *"Công ty không có quy định nghỉ phép nào
  cả"* đi lọt — một câu BỊA (agent khẳng định về nội dung tài liệu nó chưa từng đọc) mở đầu bằng
  đúng cụm phủ định. Thủng cổng ở đúng ca cổng sinh ra để chặn.

Cách diễn đạt khác (*"tôi chưa được cung cấp tài liệu nào"*) không khớp exact-match và rơi sang
**LLM-judge** — `publish.py` truyền `judge=` thật, và `_duoc_hoi_judge` cho case nhánh trả-lời
trượt exact-match đi qua judge ngữ nghĩa. Đó là lý do cụm này không cần phủ mọi cách nói."""

# Câu hỏi chọn theo đúng thứ một nhân viên hỏi trợ lý nội bộ, và đều là thứ **chỉ trả lời được nếu
# có tài liệu công ty**. Agent không gắn KB mà trả lời được một câu trong đây nghĩa là nó đang bịa
# từ kiến thức nền của model — đúng thứ cổng này sinh ra để chặn.
_QUERIES = (
    "Chính sách nghỉ phép của công ty quy định thế nào?",
    "Quy trình xin tạm ứng công tác phí gồm những bước nào?",
    "Nhân viên thử việc được hưởng những chế độ gì?",
    "Công ty quy định giờ làm việc và giờ nghỉ trưa ra sao?",
    "Muốn đăng ký làm thêm giờ thì nộp đơn cho ai?",
    "Mức phụ cấp ăn trưa hiện tại là bao nhiêu?",
)


def no_kb_golden_set() -> GoldenSet:
    """Bản MỚI mỗi lần gọi, không phải một hằng số dùng chung.

    `GoldenSet`/`GoldenCase` là pydantic model chứ không frozen dataclass, và `select_core` trả về
    một `GoldenSet` mới bọc **cùng** các object case. Chia sẻ một bộ giữa hai lượt publish là đúng
    chỗ một lượt sửa nhầm rò sang lượt sau mà không lượt nào đỏ.
    """
    return GoldenSet(
        golden_set_ref=NO_KB_GOLDEN_SET_REF,
        cases=[
            GoldenCase(
                case_id=f"NOKB-{i:03d}",
                query=query,
                tenant=NO_KB_TENANT_LABEL,
                section_roles=[_SECTION_ROLE],
                expected_tenant=NO_KB_TENANT_LABEL,
                expected_section_role=_SECTION_ROLE,
                expected=_EXPECTED,
                expected_citation=[],
            )
            for i, query in enumerate(_QUERIES, start=1)
        ],
    )
