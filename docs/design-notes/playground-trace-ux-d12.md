---
id: studio.design-note.playground-trace-ux
type: design-note
day: D12
issue: "#88"
author: AIE-2 — Lưu Tiến Duy (@dholmes0207)
date: 2026-08-04
status: ĐỀ NGHỊ (không phải spec) — chờ SWE (playground, #102) + DE (trace viewer, #100)
---

# Wireframe UX playground-trace — góc nhìn người CHẤM

> **Đây là đề nghị, không phải spec, và không phải PR áp lên quadrant người khác.** Playground là bút
> **SWE** (`kit#102`, D15); trace viewer là bút **DE** (`kit#100`, D15). Việc của AIE-2 hôm nay
> (`kit#88`) là nói rõ **bộ chấm cần đọc được gì từ trace** để hai màn đó không phải đoán — và nói
> **trước** khi hai người kia dựng, chứ không sau.
>
> **Non-scope, nói thẳng:** không dựng UI · không chạm `workbench` · không đề xuất framework · không
> quyết layout. Mỗi khối dưới đây trỏ tới **một field trace có thật hôm nay**, không có field tưởng tượng.

## 1 · Vì sao bộ chấm cần một màn riêng chứ không đọc câu trả lời

Một câu: **bộ chấm đọc TRACE, không đọc lời agent tự khai.** Bằng chứng đã có trong repo, không phải
lập luận: `_LeakyKb` (`e2e_smoke_eval.py`) là KB cố ý hỏng fence — agent **vẫn nói năng bình thường**,
không gì trong câu trả lời tố cáo điều gì, mà conjunct `no_leak` **đỏ**, vì chunk chéo tenant **đã nằm
trong trace trước khi LLM mở miệng**.

⇒ Một playground chỉ hiện *"câu hỏi → câu trả lời"* **không thể** cho người dùng thấy vì sao một case
FAIL. Ba thứ quyết định điểm đều nằm ở tầng trace: **chunk nào đã được lấy ra** · **tenant của từng
event** · **cờ `refused`**.

## 2 · Wireframe

```
┌─ PLAYGROUND ────────────────────────────────┬─ TRACE ─────────────────────────────────────────┐
│ recipe:  callisto-qa-v0        [ ▶ Test ]   │ run_id: run-sc04      tenant_id: 5f3a…  (1 giá trị│
│ tenant:  ankor ▾   roles: [public] ▾        │                        cho MỌI event — xem ⚠️ dưới)│
│ query:   ┌────────────────────────────────┐ │                                                  │
│          │ Hạn mức chi của Borea là bao   │ │  seq  node          ts        tokens  citations  │
│          │ nhiêu?                         │ │  ───  ────────────  ────────  ──────  ─────────  │
│          └────────────────────────────────┘ │  0    kb-retrieve    00:00.0     0     (0)   ①    │
│                                              │  1    llm-step       00:00.4   312     (0)   ②    │
│ ── KẾT QUẢ ──────────────────────────────── │  2    end            00:00.4     0      —         │
│ answer:  "Tôi không có quyền truy cập…"     │                                                  │
│ refused: ✔ true            ③                │  ⚠️ tenant_id nhất quán: ✔  (mọi event = ankor)   │
│                                              │     0 event ⇒ ✘ fail-closed, KHÔNG phải ✔        │
│ ── CHẤM (bộ chấm, không phải agent) ─────── │                                              ④   │
│ nhánh:            từ-chối                   │  ── outputs["chunks"] của event 0 ──────────────  │
│ success:          PASS                      │  (rỗng — đúng: fence chặn trước khi truy xuất)   │
│ citation_acc:     n/a  ⑤                    │  chunk_id            tenant_id  section  score   │
│ leak (slug):      ✔ 0 chunk thuộc borea     │  (không có dòng nào)                        ⑥    │
└──────────────────────────────────────────────┴──────────────────────────────────────────────────┘
```

## 3 · Sáu khối, mỗi khối một field có thật

| # | Khối | Field/hàm có thật hôm nay | Vì sao bộ chấm cần |
|---|---|---|---|
| ① | `citations` per-event | `TraceEvent.citations` · gom bằng `citations_from_trace` (`harness.py:60`) | **Nguồn duy nhất** của `citation_accuracy` + leak-check. Không đọc `AgentAnswer.citations` (agent tự khai) |
| ② | Carrier chỉ trên `llm-step` | clause §6 + `engine:docs/contracts/trace-citations.v0.md`, gate `interpreter.py:304` | Nếu UI hiện citations ở node khác thì hoặc engine đổi hành vi, hoặc UI đang trộn *retrieved* với *grounded* |
| ③ | `refused` | output `llm-step`, key `refused: bool` | Rẽ nhánh chấm. Cảnh báo đã ghi (breakpoint `#14`): công thức hiện tại `refused = not citations` cho **dương-tính-giả** ⇒ UI **không** nên trình bày `refused` như bằng chứng agent đã từ chối đúng |
| ④ | `tenant_id` nhất quán | `tenant_scope_ok(events, expected)` (`harness.py:92`) | **`events` rỗng ⇒ `False`**, không phải `True`. `all([])` trong Python là `True` — nếu UI tự viết `all(...)` thì một run **không có event nào** sẽ hiện ✔ (xanh-giả) |
| ⑤ | `citation_acc = n/a` ở nhánh từ-chối | `_render` (`cli.py:215`, land D12) · DEC-04 phần 3 | `1.00` ở nhánh này là **quy ước vacuous-truth**, không phải phép đo. In `1.00` là mời người đọc cộng nó vào trung bình đầu |
| ⑥ | `outputs["chunks"]` | `interpreter.py:265-268`, 4 consumer đang đọc | Đường duy nhất lên **leak-check mức UUID**. Hôm nay `_citation_tenant` cắt tiền tố `chunk_id` (`harness.py:49-57`) — **nhãn mềm**, trùng được, sửa được |

## 4 · Ba thứ UI **không** nên làm (và lý do là số, không phải khẩu vị)

1. **Không tự tính lại `aggregate` từ danh sách case đang hiện.** `CaseResult` không mang cờ nhánh
   từ-chối ⇒ ở tầng hợp đồng không phân biệt được `citation_accuracy = 1.0` là *quy ước* hay *phép đo*.
   Tự cộng lại sẽ ra **`0.90` trong khi số thật là `0.833`** (GUIDE-C Q8; nợ có chủ: AIE-2, hạn D16).
2. **Không hiện `0.00` cho ô chưa đo.** `0.00` đọc thành *"đã đo, và bằng 0"* ⇒ người xem tưởng gate
   đang chặn. Dùng `todo:` — đúng luật `render_scorecard` (DEC-D12-02, `render.py`).
3. **Không hiện `verdict` khi chưa có scorecard.** `compute_scorecard` là mốc **D16**; trước đó mọi ô
   verdict là `todo:` **không có ETA cam kết được**, không phải `PASS`/`FAIL` mặc định.

## 5 · Cần gì từ ai (không chặn ai hôm nay)

| Cần | Từ | Vì sao non-blocking |
|---|---|---|
| Trace viewer hiện `outputs["chunks"]` per-event, không chỉ `citations` | DE (`kit#100`, D15) | Bộ chấm đã đọc được từ payload; đây là để **người** thấy cùng thứ máy chấm |
| Playground truyền `session` thay vì cho recipe tự khai `section_roles` | SWE (`kit#102`) + INV-1 (`kit#112`, D17) | Lỗ đã ghi thành `DEC-Q3` (chủ SWE+DE, hạn D17), không phải phát hiện mới |
| Một chỗ trong UI in `n/a` thay `1.00` cho dòng từ-chối | SWE | CLI đã làm hôm nay; nếu UI in `1.00` thì hai bề mặt nói hai số khác nhau về cùng một run |
