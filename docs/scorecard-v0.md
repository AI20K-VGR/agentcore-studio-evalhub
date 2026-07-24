# Scorecard v0 — ghi chú bút (AIE-2)

> **Trạng thái:** v0 draft · chưa freeze · `SCHEMA_VERSION = "0.1.0-draft"`
> **Bút:** AIE-2 — Lưu Tiến Duy · **Ngày:** 2026-07-21 (D2, issue #9)
> **Cập nhật:** 2026-07-23 (D4, issue #19) — nhánh trả-lời-được chuyển sang **token-contains**; thêm `expected_section_role` (trục T6); §2.7 chốt mapping `final_state → AgentAnswer` với AIE-1. Xem §2.3, §2.5, §2.6, §2.7.
> **Cập nhật:** 2026-07-24 (D5, issue #24) — citation-accuracy + leak-check đọc từ **TRACE** (gom `citations` **node-agnostic**; carrier thực tế là event `llm-step`, xác nhận qua thread-check), seam trả `CaseRun{answer, events}` nhận `tenant_id: UUID` (D-13); leak-check là sanity slug, fence thật = RLS-UUID; SC-04 bug đã biết. Xem §2.3, §2.7.
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
| `expected_section_role` | `str` | Vai đáp án NẰM Ở — trục T6, độc lập tenant (thêm D4, DE). Không suy được từ `chunk_id` (id không mã hoá vai) |
| `expected` | `str` | **Cụm ngắn phải xuất hiện** trong answer (token-contains, D4) — không còn là câu đầy đủ. DE gán nhãn tay |
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

### 2.3 Luật chấm `success` — v0 (cập nhật D4 2026-07-23)

Case phân loại qua `GoldenCase.expects_refusal`, xét **cả hai trục** hàng rào:

- **T1 chéo-tenant**: `expected_tenant != tenant`.
- **T6 chéo-vai**: `expected_section_role not in section_roles` (thêm D4 — trước chỉ xét T1 → case
  chéo-vai cùng tenant như SC-05 bị chấm sai; xem §2.5).

| Loại | `success` khi |
| --- | --- |
| trả lời được | agent KHÔNG từ chối VÀ `answer` **CHỨA** cụm `expected` (token-contains — §2.6) |
| từ chối | agent từ chối VÀ không trích chunk nào thuộc `expected_tenant` (fail-closed) |

Vế "từ chối" bắt trường hợp agent lấy được nội dung kho khác rồi diễn đạt lại: phép so `expected`
không phát hiện, danh sách trích dẫn thì có. Bản v0 không dùng `forbidden_citations` gán tay — suy
trực tiếp từ `expected_tenant`.

**Đổi D4:** nhánh trả-lời-được chuyển từ khớp-chuỗi-tuyệt-đối (`actual == expected`) sang
token-contains. DE đổi `expected` từ câu đầy đủ sang cụm ngắn (chốt 23/07); exact-match cả câu làm câu
đúng-ý-khác-chữ bị chấm sai (bias xuống). Token-contains **chỉ** áp nhánh trả-lời-được; nhánh từ-chối
giữ nguyên fail-closed (nới ở đó là thủng fence).

**Đổi D5 (#24) — nguồn citations = TRACE:** citation-accuracy (nhánh trả-lời-được) **và** leak-check
(nhánh từ-chối) đọc chunk đã trích từ **TRACE** (`harness._retrieved_citations` gom `citations`
**node-agnostic** — mọi event có, bỏ `None`), KHÔNG từ `AgentAnswer.citations` (agent tự khai). Trace
là mặt quan sát thật — cái node thực sự truy, không phải cái LLM khai. **Carrier node:** thread-check
2026-07-24 xác nhận interpreter (AIE-1) nâng citations lên event **`llm-step`** (không phải
`kb-retrieve` như contract chú thích) — gom node-agnostic để robust với cả hai, chốt node chính xác
với AIE-1 (follow-up). `citation_accuracy` dùng **set-semantics**
(`|expected ∩ retrieved| / |expected|`, ≤1.0 kể cả trace trùng) và **là metric riêng, KHÔNG gate
`success`** ở nhánh trả-lời-được (trace sai/rỗng ⇒ accuracy 0.0 nhưng vẫn PASS nếu answer đúng).
`AgentAnswer.citations` giữ lại làm *cái LLM khai* để cross-check hallucination (claimed ⊆ retrieved)
về sau.

**D-13 — leak-check là SANITY, không phải fence:** vế "không trích chunk thuộc `expected_tenant`" so
theo **tiền tố slug của `chunk_id`** (`ankor-...` → `ankor`). Đây là **sanity thứ cấp**, KHÔNG chứng
minh fence: `TraceEvent.citations` là `list[str]` chunk_id, **không mang `tenant_id` per-chunk**, nên
scorer không kiểm được ở mức UUID. **Fence thật = RLS trên `tenant_id` UUID phía máy chủ** (KB/kb.search).
Vì `core.tenants.name↔id` song ánh, so slug ≡ so UUID (không cần resolve trong scorer). Contract gap
(muốn kiểm leak mức UUID thì trace cần `tenant_id` per-chunk) → follow-up với DE/mentor, không đổi
contract ở PR này.

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

### 2.5 Trục T6 — `expected_section_role` (D4)

`chunk_id` mã hoá tenant ở tiền tố (`ankor-...` → `ankor`) nhưng **không** mã hoá vai; case từ chối có
`expected_citation: []` nên cũng không suy ngược được. Vì vậy vai-của-đáp-án phải là field riêng của
DE. Thiếu nó thì refusal chéo-vai cùng tenant (SC-05: hỏi từ vai `engineering` về đáp án vai `hr`)
không biểu diễn được, và `expects_refusal` chỉ-xét-tenant phân loại nhầm sang trả-lời-được → agent từ
chối đúng bị chấm FAIL. Fix D4: `expects_refusal` xét cả T1 lẫn T6.

### 2.6 Luật token hoá — định nghĩa (D4, artifact ký-duyệt cho `format.md` §"CHỜ AIE-2 CHỐT")

`answer` CHỨA `expected` được định nghĩa **theo token**, không phải substring thô. Cài đặt:
`studio_evalhub.harness._contains_phrase`.

1. **Chuẩn hoá**: cả hai vế `lower()` rồi tách token bằng `\w+` (unicode — chữ có dấu tiếng Việt và
   chữ số là token nguyên; dấu câu/khoảng trắng là ranh giới).
2. **Khớp**: chuỗi token của `expected` phải xuất hiện **liên tiếp** trong token của `answer`.
3. **Fail-closed**: `expected` token hoá ra rỗng ⇒ không khớp.

Nhờ tách token nguyên vẹn: `"1 ngày"` KHÔNG khớp `"11 ngày"` (`"11"` ≠ `"1"`) — vá bẫy mà substring
thô / space-pad `" 1 ngày "` mắc; đồng thời `"1 ngày/tuần"`, `"...1 ngày."`, cụm ở đầu/cuối câu vẫn
khớp.

**Phân vai:** DE sở hữu *giá trị* `expected` (cụm cần chứa, viết sạch — vd `"3 ngày làm việc"`, không
nhét space/ký tự để khớp); AIE-2 sở hữu *luật khớp* (token hoá trên).

**Known limitation:** token-contains KHÔNG bắt phủ định/ngữ cảnh — `"không ... 1 ngày"` vẫn "chứa" cụm
nên vẫn PASS. Chỉ LLM-judge (S3) mới xử lý. Chấp nhận với 5 smoke-case factual tuần này; ghi lại để
không tưởng đã kín.

> **→ Gửi DE (chốt `format.md`):** đồng ý bỏ space-pad; DE viết `expected` là **cụm ngắn sạch**, AIE-2
> khớp bằng **token liên tiếp có normalize** (định nghĩa §2.6) — chặn `"11 ngày"` mà không trượt oan
> dấu câu/đầu-cuối câu. Nhánh từ-chối + `expected_citation` giữ nguyên (không token hoá).

### 2.7 Seam → adapter mapping — chốt với AIE-1 (D4 2026-07-23; cập nhật D5 2026-07-24)

AIE-1 đã điền interpreter (`studio_engine`, commit `71caeb8` + `15d7081`). `RunResult.final_state` là
`dict[node_id, output]`; node `llm-step` cho output:

```text
final_state[<llm node>] = {"answer": str, "tokens": ..., "citations": list[str], "refused": bool}
```

Seam evalhub trả **`CaseRun{answer: AgentAnswer, events: list[TraceEvent]}`** (D5 #24). Adapter
(`EngineAgentRunner`, sống ở `studio_app` composition root — evalhub **cấm** import `studio_engine`,
`.importlinter`) map:

| Đích evalhub | Nguồn `studio_engine.RunResult` |
| --- | --- |
| `AgentAnswer.answer` | `final_state[<llm node>]["answer"]` |
| `AgentAnswer.refused` | `final_state[<llm node>]["refused"]` = `not retrieved_chunks` (STRUCTURAL, không đoán text) |
| `AgentAnswer.citations` | `final_state[<llm node>]["citations"]` — *cái LLM khai* (không dùng chấm; để cross-check) |
| **`CaseRun.events`** | **`RunResult.events`** (list `TraceEvent`) — **nguồn chấm citations** (gom node-agnostic; carrier thực tế = event `llm-step`) |

Node id lấy theo `node.type == llm-step` (**KHÔNG** hardcode `"n_llm"` — recipe đổi id vẫn chạy).
Seam nhận **`tenant_id: UUID`** (D-13): adapter resolve slug→UUID qua `core.tenants` **trước** khi gọi
`kb.search`/`interpreter.run`; evalhub `run_smoke`/CLI resolve tường minh phía trên seam. **Lưu ý:**
`RunResult.events` hiện **`[]`** (AIE-1 populate là việc D5 của họ) — evalhub chấm được ngay khi trace
được đổ; demo dùng trace stub cho tất định.

**Hệ quả trên luồng thật (cập nhật 2026-07-23, sau khi đọc DE `StaticKbSearch`):** DE đã ship
`StaticKbSearch` (kb.search thô) lọc **cả `tenant` lẫn `section_role`** (`if chunk.tenant != tenant or
chunk.section_role not in allowed`), chỉ khác là *tin giá trị client khai* — phân giải server-side
(chống T6-spoof) để S3. Vì `refused = not retrieved_chunks`, cả 5 case hành xử **đúng nhãn** ở tầng
retrieval:

- SC-01/02/03 (trả-lời-được): đúng tenant+vai → có chunk → `refused=False` → PASS được (nếu `answer`
  chứa cụm `expected`).
- SC-05 (chéo-vai): role chặn (`hr ∉ [engineering]`) → rỗng → `refused=True` → refusal PASS.

**⚠️ Bug đã biết — SC-04 (D5, DE nêu ở report D4):** trước đây ghi "SC-04 → rỗng → `refused=True` →
PASS" là **SAI**. `ankor-expense-001` front-matter `public` (chỉ `#c2` override `finance`), nên hỏi
*"hạn mức chi Borea"* từ ankor/public: fence chặn chunk borea ĐÚNG (không leak) **nhưng** semantic
search vẫn nhặt được chunk **public** của ankor → `retrieved_chunks` KHÔNG rỗng → `refused =
not retrieved_chunks = False` → golden expect refusal ⇒ **chấm FAIL**. Gốc: `refused = not
retrieved_chunks` sai semantics cho T1 (chỉ bắt refusal khi scope rỗng tuyệt đối). Đang chốt 3 bên
(AIE-1 tín hiệu `refused` · DE corpus · AIE-2 luật chấm) — hướng: T1 chấm theo **leak-safety từ trace**
làm chính. **KHÔNG đổi pass-rule ở PR này**; phải chốt trước khi nối luồng thật kẻo adapter khuếch đại.

Protocol seam `KbSearchService.search` **vẫn `NotImplementedError`** — dùng `StaticKbSearch` hay seam
nào là do wiring `studio_app` quyết. Demo chạy qua `StubAgentRunner` (trace stub) cho **tất định**,
không phụ thuộc wiring.

**Adapter #29 (chốt mentor D5 2026-07-24):** mentor **KHÔNG viết hộ** — đây là mảnh tích-hợp học cao
nhất. `apps/studio` mở cho PR: **đồng-tác AIE-1 (nguồn `final_state`/`events`) + AIE-2 (đích
`CaseRun`/`AgentAnswer`)**, SWE review recipe/DAG. Repos đã public → AIE-2 có write `apps/studio`
(fence chuyển sang tầng CODEOWNERS). Xem Q4 §3.

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
