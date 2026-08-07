# Bảng lệch — wireframe D12 ↔ bề mặt trace thật hôm nay

**Ngày:** 2026-08-07 (D15) · **Người viết:** AIE-2 · **Gửi:** DE (`kit#100`), SWE (`kit#102`)
**Tư cách: ĐỀ NGHỊ, không phải yêu cầu.** Viewer là `#100` (DE), playground là `#102` (SWE). Cùng
tư cách đã khai cho wireframe D12 — vào code người khác giữa Integration Friday là cách nhanh nhất
để vỡ ngày của ba người.

## Trạng thái đối chiếu — đọc trước khi đọc bảng

`DEC-D15-03` định nghĩa *"ghép vào viewer"* là **đối chiếu ra danh sách lệch**, không phải dựng UI.
Đối chiếu cần hai phía. Phía viewer web của `#100` **chưa tồn tại tại thời điểm viết**: `apps/web/src`
không có file nào nhắc `trace` (11 file, toàn bộ là canvas/recipe), và commit gần nhất của
`agentcore-studio-kb` là `b57ba78` (06/08). Không suy đoán viewer sẽ hiện gì.

Nhưng **có một bề mặt render trace của DE đã merge và chạy được**:
`studio_kb.trace_reader.render_timeline` (D5, bút DE). Nó đọc đúng `obs.trace_events` mà bộ chấm vừa
đọc hôm nay, nên đối chiếu với nó là đối chiếu thật chứ không phải đối chiếu với một UI tưởng tượng.

⇒ **§1 và §2 dưới đây là bảng lệch hoàn chỉnh, hai chiều, đối với bề mặt đang tồn tại.**
⇒ **§3 là phần còn chờ `#100`** — nêu rõ cần gì, không đoán.

Mỗi dòng trỏ **một field trace có thật hôm nay**, đã xác minh bằng `model_fields` chứ không bằng trí
nhớ (cùng luật đã áp cho wireframe D12: không field tưởng tượng).

---

## §1 · Field bộ chấm CẦN mà `render_timeline` chưa hiện

`render_timeline` in mỗi event: `ts · node_type · node_id · cost · citations`, cộng dòng kết luận
0-gap. Sáu thứ dưới đây bộ chấm đọc mà người xem timeline **không thấy**.

| # | Field có thật | Bộ chấm dùng ở đâu | Vì sao người cũng cần thấy |
|---|---|---|---|
| **L1** | `TraceEvent.outputs["chunks"]` — 5 key đã freeze: `chunk_id · text · score · tenant_id · section_role` (`KbSearchResultItem`) | `citations_from_trace` chỉ đọc `.citations`; `outputs["chunks"]` là đường **duy nhất** lên leak-check mức **UUID** | Hôm nay `_citation_tenant` cắt tiền tố `chunk_id` (`harness.py:67`) — **nhãn mềm**, trùng được và sửa được. `chunks[].tenant_id` là UUID thật. Đây là dòng ⑥ của wireframe D12, vẫn chưa có |
| **L2** | `TraceEvent.outputs["answer"]` trên `llm-step` | `answer_from_trace` (**mới hôm nay**) dựng lại `AgentAnswer` từ đây — vế cuối cùng khiến bộ chấm hết phụ thuộc RAM | Người xem timeline không đọc được agent **đã trả lời gì**, nên không đối chiếu được vì sao một case FAIL. Đây là field mới trở nên quan trọng **sau** D15, wireframe D12 chưa có |
| **L3** | `TraceEvent.outputs["refused"]` trên `llm-step` | `answer_from_trace` → `score_case` rẽ nhánh | ⚠️ **semantic CHƯA freeze** (Breakpoint `#14`): luật hiện hành là `refused = not citations`, một tín hiệu **cấu trúc do producer định nghĩa**. Nếu hiện, xin gắn nhãn *carrier* — **không** trình bày như bằng chứng agent đã từ chối đúng |
| **L4** | `TraceEvent.tenant_id` (per-event) | `tenant_scope_ok(events, expected)` (`harness.py:105`) | `render_timeline` **không in tenant_id một lần nào**. Không nhìn thấy nó thì bất biến *"mọi event của cùng một run trỏ cùng một tenant"* vô hình. Một run mà node đầu mang `ankor`, node sau mang `borea` vẫn thoả NOT NULL từng dòng mà vỡ hoàn toàn ở mức run |
| **L5** | `TraceEvent.tokens` (`prompt` · `completion`) | Bộ chấm **không** đọc — nhưng DoD của chính `#100` viết *"timeline+tokens+cost+citations"* | ✅ **ĐÃ XONG, không cần làm gì.** Đúng với `kb` `main` lúc viết (`render_timeline` in `cost` mà không in `tokens`), nhưng [kb#16](https://github.com/AI20K-VGR/agentcore-studio-kb/pull/16) đã thêm `tok={prompt}/{completion}` và **đã được approve** — dòng này đóng ngay khi PR đó merge. Giữ lại thay vì xoá để §1 còn đọc được như một bản ghi thời điểm |
| **L6** | `citations = None` **khác** `citations = []` | `_row_to_event` (`run_report.py`) cố ý giữ `None` chứ không đổi thành `[]` | `render_timeline` in `—` cho **cả hai** (`if event.citations else "—"` — list rỗng cũng falsy). *"Không áp dụng"* và *"đã trích, kết quả rỗng"* là hai chuyện khác nhau: cái đầu là `kb-retrieve` (không mang citations theo clause C-1), cái sau là một `llm-step` **không grounded** — tức một dấu hiệu chất lượng thật bị nuốt |

---

## §2 · `render_timeline` hiện mà bộ chấm KHÔNG dùng

Chiều ngược lại. Không phải để đề nghị bỏ — timeline phục vụ gỡ lỗi, không phục vụ chấm điểm. Nêu ra
để **không ai tưởng bộ chấm đang đọc mấy thứ này**, và để khi hai bề mặt lệch số thì biết lệch ở đâu.

| # | `render_timeline` in | Bộ chấm | Ghi chú |
|---|---|---|---|
| **U1** | `cost` per-event | **không đọc** | `_NO_COST` — engine ghi `0.0` cho mọi node hôm nay. Một cột `0.0` toàn tập dễ bị đọc thành *"đã đo, và bằng 0"*, đúng lớp lỗi `DEC-D12-02`. Đề nghị: hiện `todo:`/`chưa đo` cho tới khi có nguồn cost thật |
| **U2** | Kết luận 0-gap (`check_walk`) | **không đọc** | Quan trắc, không phải luật chấm. `success` của một case **không** phụ thuộc run có đủ node hay không — đúng chủ ý, và cần nói rõ kẻo người đọc tưởng bảng điểm đã bao gồm 0-gap |
| **U3** | `node_id` | **không đọc** | `citations_from_trace` cố ý **node-agnostic**; `answer_from_trace` rẽ theo `node_type`, không theo `node_id`. `node_id` do người viết recipe đặt (`n1`, `n_llm`…) nên không phải khoá ổn định |
| **U4** | Thứ tự theo `ts` | **không phụ thuộc** | Có bài khoá: `test_score_is_invariant_to_event_order`. Nghĩa là điểm **không đổi** khi đảo thứ tự event. Nếu viewer và bộ chấm bao giờ đó lệch nhau về thứ tự, đó **không** phải nguyên nhân lệch điểm — tiết kiệm một hướng gỡ lỗi sai |

---

## §3 · Phần còn chờ `#100` — nêu rõ, không đoán

Chiều *"field viewer hiện mà bộ chấm không dùng"* mới chỉ hoàn thành **đối với `render_timeline`**.
Với viewer web của `#100` thì chưa đối chiếu được, vì nó chưa tồn tại tại thời điểm viết.

**Cần từ DE (@DongAnh2704):** danh sách field viewer `#100` render — chỉ cần tên field, không cần
code. Có nó thì §2 mở rộng được trong một lượt, không phải làm lại từ đầu.

**Không chặn gì hôm nay.** Deliverable D15 của AIE-2 (`render_run_cases` + `run_report`) không đọc
viewer, và §1 đã đủ để DE bắt đầu — sáu dòng đó đúng kể cả khi viewer render thêm gì đi nữa, vì
chúng nói về thứ bộ chấm **cần**, không về thứ viewer **có**.

## §4 · Ba thứ xin đừng làm — lý do là số, không phải khẩu vị

Nhắc lại từ wireframe D12 vì cả ba vẫn còn nguyên hiệu lực, và giờ có thêm số của D15:

1. **Đừng in `1.00` cho `citation_accuracy` ở dòng từ-chối.** Đó là quy ước vacuous-truth, không phải
   phép đo. CLI in `n/a` từ D12; `render_run_cases` in `n/a` từ hôm nay. Nếu UI in `1.00` thì hai bề
   mặt nói hai số khác nhau về cùng một run.
2. **Đừng in một tỷ lệ tổng (`%`) khi mẫu số chưa tách.** `DEC-S2-134-03` đòi tách
   `k_citation / n_citation_scored` và loại refusal. `render_run_cases` hôm nay **chỉ** in `k/n` thô
   kèm nhãn *fixed-set, chưa phải population estimate* — có test khoá rằng ký tự `%` không xuất hiện.
   `kit#134`: chỗ hỏng không nằm ở probe, nằm ở bước từ `8/10` sang `"80%"`.
3. **Đừng tự viết `all(...)` để kiểm tenant nhất quán.** `all([])` trong Python là `True`, nên một run
   **không có event nào** sẽ hiện ✔ — xanh-giả. `tenant_scope_ok` fail-closed đúng chỗ đó
   (`harness.py:130`), dùng lại nó thay vì viết lại.
