# Scorecard v0 — ghi chú bút (AIE-2)

> **Trạng thái:** v0 draft · chưa freeze · `SCHEMA_VERSION = "0.1.0-draft"`
> **Bút:** AIE-2 — Lưu Tiến Duy · **Ngày:** 2026-07-21 (D2, issue #9)
> **Freeze:** workshop contract-negotiation D11 — các câu ở §3 cần chốt trước mốc đó.

Ghi chú của người giữ bút `scorecard`: ghi lại quyết định đã ra và phần chưa quyết. Contract nằm ở
`studio_contracts.scorecard`; file này không lặp lại nội dung contract.

---

## 1. Phần không đụng vào

`studio_contracts/scorecard.py` đã tồn tại và khớp umbrella-contract §3.4, gồm cả trường `judge`.
`packages/contracts` ngoài quyền ghi của AIE-2 (mentor-approval), và
`tests/test_scorecard_roundtrip.py` chặn việc evalhub định nghĩa lại `Scorecard`.

Bút v0 D2 không sửa gì trong contracts. Việc của D2 là chốt nửa đầu vào còn thiếu.

```text
GoldenCase  ──▶  EvalHarness.run()  ──▶  CaseResult  ──▶  compute_scorecard()  ──▶  Scorecard
(evalhub —                                   (contracts — đã có, khớp umbrella)
 chốt D2)
```

---

## 2. Shape đầu vào — chốt với DE 2026-07-21

DE sinh case từ doc-factory và gán nhãn tay `expected`; AIE-2 tiêu thụ. Tên trường giữ nguyên của
DE — bên sản xuất sở hữu tên trên dây.

| Trường | Kiểu | Nghĩa |
| --- | --- | --- |
| `case_id` | `str` | Id ổn định; chảy vào `CaseResult.case_id`, là nửa khoá cache của judge |
| `query` | `str` | Câu hỏi đưa vào agent (tên khớp tham số đầu `kb.search`) |
| `tenant` | `str` | Tenant bên hỏi — dựng ngữ cảnh RLS (INV-1) |
| `section_roles` | `list[str]` | Quyền bên hỏi nắm — trục thứ hai của hàng rào (T6) |
| `expected_tenant` | `str \| None` | Kho chứa đáp án thật sự |
| `expected` | `str` | Đáp án chuẩn, DE gán nhãn tay |
| `expected_citation` | `list[str]` | Chunk lẽ ra phải được trích — mẫu số của `citation_accuracy` |

Model: `studio_evalhub.golden_case.GoldenCase` / `GoldenSet`.
Lưu trữ: một dòng `eval.golden_sets`, cột `cases` (JSONB) = mảng `GoldenCase`.

### 2.1 `expected_tenant`

Trường AIE-2 đề nghị bổ sung, DE đồng ý. So `tenant` với `expected_tenant` để phân loại case:

| `tenant` | `expected_tenant` | Loại case | Kỳ vọng |
| --- | --- | --- | --- |
| `ankor` | `ankor` | trả lời được | trả lời + trích dẫn đúng |
| `ankor` | `borea` | bẫy hàng rào | từ chối |
| `ankor` | `null` | không kho nào có | từ chối |

Không có trường này thì hai dòng cuối không phân biệt được trên cột `expected`.

Kèm theo: bộ case chạy được từ phía tenant khác — đổi bên hỏi thì case bẫy thành case trả lời được,
không phải gán nhãn lại.

### 2.2 Không thêm `match_mode`

Shape D2 không có cờ phân loại. Cả hai tình huống phải-từ-chối suy được từ `tenant` vs
`expected_tenant`, nên cài thành thuộc tính dẫn xuất `GoldenCase.expects_refusal`.

Lý do chọn suy-ra:

- không sửa shape DE sở hữu;
- loại bỏ khả năng cờ và tenant mâu thuẫn nhau;
- ít một trường phải gán nhãn tay.

Đánh đổi: khi lên 30 case có câu chủ quan cần LLM-judge, sẽ cần cờ thật (`exact` / `judge`) vì lúc
đó không suy được từ tenant. Thêm cờ là thay đổi cộng thêm, không phá file v0 — hợp với kỷ luật
additive-only. Quyết định lại ở D11.

### 2.3 Luật chấm `success` — v0

| Loại | `success` khi |
| --- | --- |
| trả lời được | `actual` khớp `expected` |
| từ chối | agent từ chối VÀ không trích chunk nào thuộc `expected_tenant` |

Vế thứ hai bắt trường hợp agent lấy được nội dung kho khác rồi diễn đạt lại: phép so với `expected`
không phát hiện, danh sách trích dẫn thì có.

Bản v0 không dùng danh sách `forbidden_citations` gán tay — suy trực tiếp từ `expected_tenant`.

### 2.4 Phân bổ 5 smoke-case

| # | Loại | Kiểm gì |
| --- | --- | --- |
| 1 | trả lời được | đường chạy cơ bản |
| 2 | trả lời được, ≥2 citation | `citation_accuracy` có giá trị khác 1.0 |
| 3 | bẫy hàng rào | `leakage = 0` |
| 4 | nhạy với chỉ dẫn | case tụt điểm khi chỉ dẫn xấu đi (demo bước 7) |
| 5 | không kho nào có | chống bịa |

Case #4 cần chọn có chủ đích: nếu cả 5 case đều không tụt điểm khi chỉ dẫn xấu đi thì gate không
chặn và demo bước 7 không chạy được.

---

## 3. Câu hỏi treo — gửi mentor D2, chốt ở D11

### Q1 — `CaseResult.judge` điền gì khi case không qua judge

`judge: Judge` là trường bắt buộc. Cả 5 smoke-case đều exact-match hoặc refusal; nấc descope #3
(judge → exact-match) biến mọi case thành không-judge. `judge.py` quy định `agreement` phải suy từ
so sánh thật với nhãn tay, không phải giá trị hằng.

| | Phương án | Đánh đổi |
| --- | --- | --- |
| a | `judge` nhận `Judge \| None` | thay đổi cộng thêm, không phá payload cũ; phải sửa contracts (mentor-approval) |
| b | Giữ bắt buộc, quy ước `Judge(label="exact-match", agreement=1.0)` | không đụng contracts; là giá trị hằng mà `judge.py` loại trừ |
| c | Tách hai loại `CaseResult` (discriminated union) | chặt về kiểu; breaking change |

Đề xuất: (a) — là thay đổi cộng thêm nên không cần bump `SCHEMA_VERSION`, và biểu diễn đúng trạng
thái "case không qua judge".

### Q2 — `citation_accuracy` của case từ chối

Case từ chối đúng thì không trích dẫn gì. Tính giá trị tuyệt đối hay loại khỏi mẫu số của
`aggregate.citation_accuracy`?

Hai cách cho ra `aggregate` khác nhau, kéo theo `gate.verdict` khác nhau. Cần chốt trước khi viết
`compute_scorecard`.

Đề xuất: loại khỏi mẫu số. Tính giá trị tuyệt đối sẽ làm `citation_accuracy` biến thiên theo tỉ lệ
case refusal trong bộ, không theo chất lượng trích dẫn.

### Q3 — `section_roles` phân giải ở đâu

`kb.search` quy định `section_roles` phân giải phía máy chủ, giá trị client khai bị bỏ qua (chống
T6 label-spoof). File case là giá trị client khai.

Đề xuất: harness không truyền `case.section_roles` thẳng vào `kb.search`, mà dựng phiên mang các
quyền đó rồi chạy case, đi qua đường phân giải như request thật.

Cần xác nhận chung với DE (chủ `kb.search`) và AIE-1 (chủ executor `kb-retrieve`).

### Q4 — Seam để harness gọi interpreter

`.importlinter` cấm `studio_evalhub` import `studio_kb` / `studio_engine`. `EvalHarness.run` phải
chạy case qua DAG của recipe (AIE-1) và đọc golden-set (DE sinh).

`studio_contracts.protocols` hiện có 3 seam: `EmbeddingService`, `LLM`, `TraceWriter` — không có
seam cho interpreter hay golden-set repo.

Đề xuất: thêm Protocol vào contracts, `studio_app` tiêm bản thật. Là thay đổi contracts, đưa vào
chương trình nghị sự D11; đụng AIE-1 và DE.

### Q5 — Bộ case nằm ở bảng nào

| Bảng | Chủ | Trạng thái |
| --- | --- | --- |
| `eval.golden_sets` | AIE-2 (`studio_evalhub/schema.py`) | có cột `cases` JSONB |
| `obs.golden_sets` | DE (`studio_app/obs/schema.py`) | shell, DE điền cột thật sau |

Cần xác định ai ghi, ai đọc, bảng nào là nguồn sự thật. Chưa chốt thì `EvalHarness.run` không xác
định được nguồn dữ liệu.

---

## 4. Nấc descope liên quan

Nấc của quadrant là judge → exact-match scorer (xem `DESCOPE.md`). Bộ 5 smoke-case v0 không có case
nào cần judge, nên evalhub đang ở sẵn nấc này từ S1; judge chỉ xuất hiện khi lên 30 case ở S3.

Hệ quả: Q1 phát sinh ngay ở S1, không phải ở S3.
