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

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GoldenCase(BaseModel):
    """Một case trong golden/smoke set — đơn vị `EvalHarness.run()` chạy và chấm."""

    # `extra="forbid"` (`DEC-D18-01`): field lạ trong yaml là **lỗi cứng**, không phải thứ bỏ qua.
    #
    # Mặc định của pydantic là `ignore`, và mặc định đó nuốt câm đúng lớp lỗi nguy hiểm nhất trên
    # seam này: DE gõ nhầm tên một field, `load_golden_set` nạp **thành công**, không cảnh báo gì,
    # rồi bộ chấm đọc được không có gì và trả về một **con số** thay vì một lỗi. Không test nào đỏ,
    # vì không test nào biết field lẽ ra phải có.
    #
    # Rủi ro của chiều ngược lại (yaml thật đỏ vì có field chưa khai ở đây) đã đo, không suy:
    # golden-30 hiện tại có đúng 8 field, khớp 1:1 với khai báo dưới đây ⇒ rủi ro đo được là 0 trên
    # dữ liệu hôm nay, đổi lại chặn được mọi drift tương lai **ở đúng chỗ nó sinh ra**.
    #
    # Bất biến này có bài cưỡng chế ở cả hai tầng: `tests/test_golden_case_shape.py` (tầng kiểu) và
    # `test_loader_manual_label_sai_ten_do_tai_loader` (đường đi thật của dữ liệu DE).
    model_config = ConfigDict(frozen=True, extra="forbid")

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

    expected_section_role: str
    """Vai mà đáp án NẰM Ở (không phải vai bên hỏi — đó là `section_roles`). Trục thứ hai của hàng rào,
    độc lập với `tenant`: case phải-từ-chối khi vai này KHÔNG nằm trong `section_roles` của bên hỏi
    (T6 label-spoof), kể cả khi cùng tenant.

    BẮT BUỘC là field riêng, không suy được từ `expected_citation`: `chunk_id` mã hoá tenant ở tiền tố
    (`ankor-...` → `ankor`) nhưng KHÔNG mã hoá vai; case từ chối lại có `expected_citation: []` nên
    không còn gì để suy. Tên field của DE (`format.md`, thêm 23/07)."""

    expected: str
    """Cụm ngắn PHẢI XUẤT HIỆN trong câu trả lời (không phải đáp án đầy đủ) — mục tiêu token-contains của
    nhánh trả-lời-được (`docs/scorecard-v0.md` §2.3): `answer` CHỨA `expected` là PASS, không bắt khớp
    cả câu / đúng chính tả. DE chọn cụm đủ ngắn mà vẫn duy nhất trong kho của tenant đó (vd
    `"3 ngày làm việc"`). Case từ chối dùng `"refusal"` — không tham gia chấm nhánh trả-lời-được.
    DE gán nhãn tay."""

    expected_citation: list[str] = Field(default_factory=list)
    """Các chunk lẽ ra phải được trích — mẫu số của `CaseResult.citation_accuracy`. Phải khớp chính
    xác chuỗi `kb.search` trả về ở `KbSearchResultItem.chunk_id` (định dạng DE dùng:
    `ankor-leave-001#c1`); lệch định dạng thì mọi case ra 0 mà không có lỗi nào nổi lên.

    Tên số ít là của DE, giữ nguyên dù giá trị là list. Rỗng với case từ chối."""

    manual_label: str | None = None
    """Nhãn tay ground-truth cho case — mẫu số của `Judge.agreement` (`#118` ô DoD 2).

    **`None` nghĩa là "case này CHƯA được gán nhãn tay", không phải "người gán nhãn kết luận là
    không-có-nhãn".** Hai thứ đó khác nhau ở chỗ quan trọng nhất: case `None` phải bị **loại khỏi
    mẫu số** của agreement, còn một nhãn rỗng đã gán thì không. Gộp hai nghĩa vào một giá trị là
    cách agreement ra một con số trông hợp lệ mà mẫu số sai. Optional vì nhãn tay phủ một **subset**,
    không phải cả 30 case (`kb` `DL-16.1`); bắt buộc field này sẽ làm đỏ toàn bộ golden-30 hiện tại
    (0/30 case có nhãn) và biến một field phụ thành một đợt migration của DE.

    **Ai sở hữu cái gì** — nguyên văn `DEC-Q5` (`docs/scorecard-v0.md:509`): DE sở hữu **giá trị**
    (sinh + gán nhãn case, giao qua yaml trong kho của DE, `#115`); AIE-2 sở hữu **shape
    + nơi lưu + loader**. Nên field này được khai ở đây **trước** khi DE emit — nếu khai sau,
    `extra="forbid"` làm yaml của DE đỏ, còn không có `extra="forbid"` thì nhãn bị nuốt câm. Không
    có thứ tự thứ ba an toàn.

    Kiểu `str` chứ **không** phải enum, và đó là quyết định có hạn dùng: trục nhãn (tập giá trị hợp
    lệ — nhãn theo *kết quả mong đợi* hay theo *chất lượng câu trả lời*) là của DE và **chưa chốt**.
    Đóng khung thành enum từ phía tiêu thụ là AIE-2 lấn quyền `DEC-Q5` và đặt trước một vocabulary
    chưa ai đồng ý. Ngày DE chốt trục, chỗ này siết lại được mà không đổi tên field."""

    source: Literal["ai", "human"] | None = None
    """Case này do **máy sinh** hay do **người** viết/sửa — trục của golden set lai (AI sinh diện
    rộng + người sửa phần quan trọng).

    **`None` nghĩa là "chưa khai nguồn", KHÔNG phải `"ai"`.** 60 case golden hiện có (`v1` + `2.0`)
    không mang field này; mặc định `"ai"` sẽ **khai hộ nguồn gốc** cho cả 60 mà không ai kiểm, và
    bảng *"AI sinh bao nhiêu / người sửa bao nhiêu"* đọc từ đó là một con số bịa. Cùng luật
    `manual_label` ngay trên và `DEC-D16-03` (`rate=None ≠ 0.0`).

    Dùng để cưỡng chế *"human ground-truth always wins"* lúc hợp nhất hai nguồn: khi dedup thấy hai
    case cùng nội dung, bản `source="human"` **ghi đè** bản `"ai"`, không phải bản nào tới sau thắng.

    Tập **đóng** (khác `manual_label` cố ý để `str` mở): trục này AIE-2 sở hữu và giá trị đã chốt tại
    đây, nên đóng khung không lấn `DEC-Q5` của DE."""

    is_critical: bool | None = Field(default=None, strict=True)
    """Case thuộc nhánh **không được sai một lần nào** — đầu vào của cổng bảo mật zero-tolerance.

    **`None` nghĩa là "chưa phân loại", KHÔNG phải `False`.** Đây là trục có cái giá lệch nhất trong
    ba: mặc định `False` dán nhãn *"không quan trọng"* lên **mọi** case sẵn có, nên cổng zero-tolerance
    đọc trục này sẽ gác một tập **rỗng** — và xanh. Fail-open đúng trên trục nó gác, im lặng.

    `strict=True` chứ không để pydantic ép kiểu: yaml `is_critical: "true"` (có dấu nháy — lỗi gõ dễ
    gặp nhất) phải **đỏ**, không được diễn giải hộ thành `True`. Một case bị nháy nhầm mà vẫn lọt vào
    nhánh bảo mật là đúng thứ trục này tồn tại để chặn.

    Không suy từ `expects_refusal`: `expects_refusal` là *hành vi đúng của case này là từ chối*, còn
    `is_critical` là *sai case này thì cả lượt chấm hỏng*. Hai tập giao nhau nhiều nhưng không bằng
    nhau — một case trả-lời-được về hạn mức chi tiêu có thể critical mà không refusal."""

    tier: Literal["core", "full"] | None = None
    """Case nằm ở bộ **Core** (chạy lúc gate Publish) hay bộ **Full** (chạy nền).

    Lý do tách: người bấm Publish chờ được 15–30s. Bộ Core 30–50 case chạy ~20–30s; chạy đủ 100–500
    case mất 5–10 phút ⇒ spinner treo hoặc HTTP 504. Nên gate đọc Core, còn Full chạy ngoài đường
    request.

    **`None` nghĩa là "chưa phân tầng", KHÔNG phải `"full"` hay `"core"`.** Mặc định `"core"` nhét
    case chưa ai xét vào đúng tập chạy lúc gate — làm cổng chậm đi và chấm trên tập không ai chọn;
    mặc định `"full"` thì ngược lại, âm thầm loại case khỏi gate. Cả hai đều là quyết định thay người
    phân loại.

    Tập **đóng**, cùng lý do `source`. Một `tier: "medium"` gõ nhầm mà lọt sẽ làm case đó rơi khỏi
    **cả** Core lẫn Full — biến mất khỏi mọi phép chấm, không lỗi nào nổi lên."""

    @property
    def expects_refusal(self) -> bool:
        """True khi hành vi đúng của agent là từ chối thay vì trả lời.

        Dẫn xuất, không lưu — xét CẢ HAI trục hàng rào:

        - **T1 chéo-tenant**: `expected_tenant != tenant` — hỏi dữ liệu kho khác (hoặc không kho nào
          chứa khi `expected_tenant is None`).
        - **T6 chéo-vai**: `expected_section_role not in section_roles` — cùng tenant nhưng đáp án nằm
          ở vai bên hỏi không giữ.

        Refusal khi BẤT KỲ trục nào vi phạm. Trước 23/07 chỉ xét T1 → case chéo-vai cùng tenant (SC-05)
        rơi nhầm vào nhánh trả-lời-được, agent từ chối ĐÚNG lại bị chấm FAIL; thêm trục T6 vá đúng chỗ đó.

        Luật chấm hai nhánh khác nhau (xem `docs/scorecard-v0.md` §2.3):

        - trả lời được → `success` = agent không từ chối VÀ `answer` CHỨA `expected` (token-contains)
        - từ chối      → `success` = agent từ chối VÀ không trích chunk nào thuộc `expected_tenant`

        Vế thứ hai bắt trường hợp agent lấy được nội dung kho khác rồi diễn đạt lại: phép so `expected`
        không phát hiện, danh sách trích dẫn thì có.
        """
        return (self.expected_tenant != self.tenant) or (self.expected_section_role not in self.section_roles)


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
