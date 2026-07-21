"""Shape đầu vào của eval — golden/smoke case (bút v0 AIE-2, D2 issue #9).

`studio_contracts.Scorecard` (R-SPEC A1#4) mô tả thứ một lần chạy eval SINH RA (`CaseResult` mỗi
case + `Aggregate` + `Gate`). Không contract nào mô tả thứ nó TIÊU THỤ — bản thân các case. Module
này là nửa còn thiếu đó.

Đặt trong evalhub, không đưa lên `studio_contracts`: đây là kiểu riêng của quadrant, cùng cách xử
lý như `studio_engine.RunResult` — không phải seam thứ 5, nên đổi shape không cần mini-RFC.

Shape chốt với DE (Nguyễn Đông Anh) ngày 2026-07-21: DE sinh case từ doc-factory và gán nhãn tay
`expected`; AIE-2 tiêu thụ. Tên trường giữ nguyên của DE — bên sản xuất sở hữu tên trên dây.

Lưu trữ: một dòng `eval.golden_sets` (xem `schema.py`) = `golden_set_ref` + mảng JSONB các case;
`GoldenSet.cases` ánh xạ 1:1 vào cột đó.

Chưa quyết (xem `docs/scorecard-v0.md` §3 — mang ra workshop D11, không tự đặt mặc định ở đây):
  1. `CaseResult.judge` là trường bắt buộc, nhưng case so-khớp-trực-tiếp và case kỳ-vọng-từ-chối
     không có judge.
  2. `citation_accuracy` của case từ chối (không trích dẫn gì) — giá trị tuyệt đối hay loại khỏi
     mẫu số của `aggregate`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GoldenCase(BaseModel):
    """Một case trong golden/smoke set — đơn vị `EvalHarness.run()` chạy và chấm."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    """Id ổn định. Chảy thẳng vào `CaseResult.case_id`; cũng là nửa khoá cache `(case_id, actual)`
    của LLM-judge (cap ≤100 call/ngày, INV-4)."""

    query: str
    """Câu hỏi đưa vào agent. Tên `query` (không phải `question`) để khớp tham số đầu của
    `kb.search`."""

    tenant: str
    """Tenant của bên hỏi. Dựng ngữ cảnh chạy; RLS trên `kb.chunks` phân giải theo trường này
    (INV-1)."""

    section_roles: list[str]
    """Quyền mà bên hỏi nắm. Một chunk hiển thị khi `KbSearchResultItem.section_role` nằm trong
    danh sách này — trục thứ hai của hàng rào (T6 label-spoof), độc lập với `tenant` (T1).

    Lưu ý: contract `kb.search` quy định `section_roles` phân giải phía máy chủ, giá trị client
    khai bị bỏ qua. Harness phải xử lý trường này như "dựng phiên mang các quyền này rồi chạy
    case", không truyền thẳng vào `kb.search`. Xem Q3 trong `docs/scorecard-v0.md`."""

    expected_tenant: str | None
    """Kho chứa đáp án thật sự — nhãn về vị trí tri thức, không phải về nội dung câu trả lời.
    So với `tenant` để phân loại case (xem `expects_refusal`):

    - `== tenant`  → case trả lời được
    - `!= tenant`  → case bẫy hàng rào: hỏi dữ liệu kho khác, agent phải từ chối
    - `None`       → không kho nào chứa đáp án, agent phải từ chối

    Cũng là trường cho phép chạy cùng một bộ case từ phía tenant khác: đổi bên hỏi thì case bẫy
    thành case trả lời được, không phải gán nhãn lại."""

    expected: str
    """Đáp án chuẩn, DE gán nhãn tay. Chỉ có nghĩa với case trả lời được."""

    expected_citation: list[str] = Field(default_factory=list)
    """Các chunk lẽ ra phải được trích — mẫu số của `CaseResult.citation_accuracy`. Phải khớp chính
    xác chuỗi `kb.search` trả về ở `KbSearchResultItem.chunk_id` (định dạng DE dùng:
    `ankor-leave-001#c1`); lệch định dạng thì mọi case ra 0 mà không có lỗi nào nổi lên.

    Tên số ít là của DE, giữ nguyên dù giá trị là list. Rỗng với case từ chối."""

    @property
    def expects_refusal(self) -> bool:
        """True khi hành vi đúng của agent là từ chối thay vì trả lời.

        Dẫn xuất, không lưu: shape D2 không có cờ `match_mode`, và cả hai tình huống phải-từ-chối
        đều suy được từ `tenant` so với `expected_tenant` (bẫy hàng rào khi khác nhau; không kho
        nào có khi `expected_tenant is None`). Cách này không sửa shape DE sở hữu và loại bỏ khả
        năng cờ và tenant mâu thuẫn nhau.

        Luật chấm hai nhánh khác nhau:

        - trả lời được → `success` = `actual` khớp `expected`
        - từ chối      → `success` = agent từ chối VÀ không trích chunk nào thuộc `expected_tenant`

        Vế thứ hai bắt trường hợp agent lấy được nội dung kho khác rồi diễn đạt lại: phép so với
        `expected` không phát hiện, danh sách trích dẫn thì có.
        """
        return self.expected_tenant != self.tenant


class GoldenSet(BaseModel):
    """Một bộ case có tên — một dòng `eval.golden_sets`, và là thứ `recipe.golden_set_ref` trỏ tới.

    Không mang `agent_id`: bộ case gắn với KB/domain, không gắn với agent — đó là lý do `Scorecard`
    để `agent_id` và `golden_set_ref` thành hai trường riêng. Giữ tách biệt để một recipe mới trỏ
    được vào bộ case sẵn có mà không đụng engine.
    """

    model_config = ConfigDict(frozen=True)

    golden_set_ref: str
    """Khớp `Recipe.golden_set_ref` và `Scorecard.golden_set_ref`."""

    cases: list[GoldenCase]
    """Ánh xạ vào `eval.golden_sets.cases` (JSONB). 5 case ở S1 (smoke), 30 ở S3 (golden)."""
