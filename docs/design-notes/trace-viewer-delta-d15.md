# Bảng lệch — wireframe D12 ↔ bề mặt trace thật hôm nay

**Ngày:** 2026-08-07 (D15) · **Người viết:** AIE-2
**Gửi:** DE (`kit#100`) — §1/§2, đã giao · SWE (`kit#102`) — §3, **chưa giao tại thời điểm commit này**
**Tư cách: ĐỀ NGHỊ, không phải yêu cầu.** Bề mặt CLI là `#100` (DE), playground + viewer web là
`#102` (SWE). Cùng tư cách đã khai cho wireframe D12 — vào code người khác giữa Integration Friday là
cách nhanh nhất để vỡ ngày của ba người.

## Trạng thái đối chiếu — đọc trước khi đọc bảng

`DEC-D15-03` định nghĩa *"ghép vào viewer"* là **đối chiếu ra danh sách lệch**, không phải dựng UI.
Đối chiếu cần hai phía, và hôm nay có **hai** bề mặt thật để đối chiếu:

| bề mặt | bút | trạng thái | đối chiếu ở |
|---|---|---|---|
| `studio_kb.trace_reader.render_timeline` (CLI) | DE | merged từ D5, `tokens` thêm ở [kb#16](https://github.com/AI20K-VGR/agentcore-studio-kb/pull/16) | **§1 · §2** |
| `apps/web/src/playground/TraceViewer.tsx` | **SWE** | [web#3](https://github.com/AI20K-VGR/agentcore-studio-web/pull/3) @ `011b5534`, mở 07:42, **chưa merge** | **§3** |

> **Đính chính, ghi lộ ra thay vì sửa lặng.** Bản đầu của khối này viết *"phía viewer web của `#100`
> **chưa tồn tại tại thời điểm viết**: `apps/web/src` không có file nào nhắc `trace`"*. **Sai hai vế.**
> Đúng với `main`, nhưng [web#3](https://github.com/AI20K-VGR/agentcore-studio-web/pull/3) đã thêm
> `src/playground/TraceViewer.tsx` lúc **07:42** — tức trước cả khi câu đó được gõ. Và viewer web là
> bút **SWE (`#102`)**, không phải `#100`: `#100` giao bề mặt CLI.
>
> *Nên sao:* kiểm sự tồn tại của một bề mặt bằng `git ls-files` trên `main` là kiểm **một** trong hai
> chỗ nó có thể sống. Nhánh và PR đang mở là chỗ còn lại, và ở giữa Integration Friday thì đó mới là
> chỗ mọi thứ đang nằm. Cùng lớp lỗi với vấp #2 của runbook: *"fresh clone" không có nghĩa là "fresh
> database"* — cả hai đều là quên mất một chỗ trạng thái vẫn tồn tại.

⇒ **§1 và §2** là bảng lệch hai chiều đối với bề mặt **CLI**.
⇒ **§3** là đối chiếu với **viewer web** — làm được thật, không còn phải chờ.

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

## §3 · Đối chiếu với viewer web — `TraceViewer.tsx` (web#3 @ `011b5534`, bút SWE)

**Tư cách: ĐỀ NGHỊ.** `#102` là bút SWE. Ba dòng đầu dưới đây là **đúng ba khối** wireframe D12 đã
nêu cho playground (③④⑤) — nêu ra không phải để trách, mà vì chúng chứng minh wireframe đã chỉ đúng
chỗ và đơn giản là **chưa tới tay** trước khi SWE dựng. Lỗi giao hàng, không phải lỗi đọc.

Điều đáng chú ý nhất: SWE **đã tự nối vào `score_run_from_trace()`** — hàm AIE-2 land hôm nay, import
trong `try/except ImportError` vì `evalhub#15` chưa merge (`dev_playground_server.py:178-198`). Nên
mối nối bộ-chấm ↔ playground **đã tồn tại**, chỉ là chưa ai đối chiếu hai đầu.

| # | Chỗ | Bằng chứng | Vì sao đáng sửa |
|---|---|---|---|
| **W1** | UI in `1.00` ở nhánh **từ-chối**, chỗ CLI in `n/a` | `TraceViewer.tsx`: `citation_accuracy?.toFixed(2)`, không có nhánh refusal | Đây là **lỗi cấu trúc, không sửa được ở TSX**: payload của `dev_playground_server.py:194-198` gửi `citation_accuracy` thô và **không mang `expects_refusal`**, nên UI không có cách nào biết đang ở nhánh nào. Đúng thứ wireframe D12 §4.1 nêu — *"`CaseResult` không mang cờ nhánh từ-chối ⇒ ở tầng hợp đồng không phân biệt được"*. `1.0` ở nhánh này là **quy ước vacuous-truth** (`DEC-04`), không phải phép đo. Chỗ vá: thêm cờ vào payload |
| **W2** | `Σcost=0.0000` đọc như *"đã đo, và bằng 0"* | `totalCost.toFixed(4)` + `cost.toFixed(4)` mỗi event | `interpreter.py:73` `_NO_COST = 0.0`, dùng ở `:389` — engine ghi `0.0` cho **mọi** node. Chưa có nguồn cost thật (D19, `kit#120`). Cùng dòng U1 của §2 và cùng luật `DEC-D12-02`: ô chưa đo phải hiện `todo:`/`chưa đo`, không hiện `0` |
| **W3** | `monotonic` tính trên mảng **đã sort** ⇒ gần như luôn ✓ | `const sorted = [...events].sort(...)` rồi `sorted.every((e,i) => i===0 \|\| e.ts > sorted[i-1].ts)` | **Đúng F1 đã filed cho `kb#16`**, giờ là bề mặt thứ ba. Đo đơn điệu trên chuỗi đã xếp thì kết quả là hằng số. Thêm hai chi tiết: so bằng `>` trên **chuỗi** (`_parse_ts` của kb có docstring nói vì sao so chuỗi sai), và `sort` dùng `localeCompare` trong khi so dùng `>` — hai ngữ nghĩa khác nhau trên cùng dữ liệu. Và `>` chặt nghĩa là **`ts` trùng ⇒ KHÔNG monotonic**, ngược hẳn `check_ts_monotonic` của kb |
| **W4** *(nhỏ)* | Dòng chi tiết in `0 event · ordering monotonic ✓` | `[].every()` trong JS là `true`, y như `all([])` trong Python | Badge tổng **đã fail-closed đúng** (`ok = … && sorted.length > 0`) — nên đây chỉ là lệch giữa badge và dòng chi tiết, không phải xanh-giả ở mức kết luận. Ghi vì nó là ④ của wireframe D12, và vì phần khó thì SWE đã làm đúng |
| **W5** *(nhỏ)* | `citations = null` và `= []` hiện như nhau | `event.citations && event.citations.length > 0` | Cùng L6 của §1, cùng lớp với `render_timeline`. *"Không áp dụng"* (`kb-retrieve`) và *"đã trích, rỗng"* (`llm-step` không grounded) là hai chuyện khác nhau |

**Không dòng nào chặn merge web#3** — đây là đề nghị gửi chủ bút, không phải review chính thức.
**W1 là dòng đáng làm trước**, vì nó khiến hai bề mặt nói **hai số khác nhau về cùng một run**, và
đó chính là thứ D19 (`kit#120`) sẽ phải dựng cost-lineage lên trên.

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
