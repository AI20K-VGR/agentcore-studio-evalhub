# Scorecard v0 — ghi chú bút (AIE-2)

> **Trạng thái:** v0 draft · chưa freeze · `SCHEMA_VERSION = "0.1.0-draft"`
> **Bút:** AIE-2 — Lưu Tiến Duy · **Ngày:** 2026-07-21 (D2, issue #9)
> **Cập nhật:** 2026-07-23 (D4, issue #19) — nhánh trả-lời-được chuyển sang **token-contains**; thêm `expected_section_role` (trục T6); §2.7 chốt mapping `final_state → AgentAnswer` với AIE-1. Xem §2.3, §2.5, §2.6, §2.7.
> **Cập nhật:** 2026-07-24 (D5, issue #24) — citation-accuracy + leak-check đọc từ **TRACE** (gom `citations` **node-agnostic**; carrier thực tế là event `llm-step`, xác nhận qua thread-check), seam trả `CaseRun{answer, events}` nhận `tenant_id: UUID` (D-13); leak-check là sanity slug, fence thật = RLS-UUID; SC-04 bug đã biết. Xem §2.3, §2.7.
> **Cập nhật:** 2026-07-28 (D7, issue #34) — §2.7 sửa `refused`: định nghĩa đã đổi **hai lần** (`not retrieved_chunks` → sentinel → **`not citations`**, engine#10 đã merge) mà doc chỉ ghi mốc đầu, tức doc **mâu thuẫn code trên `main`**; công bắt lỗi thuộc AIE-1 (@TranBaDat2607). Thêm **§2.7.1** (3 mốc + vì sao mốc D4 sai về bản chất) và **§2.7.2** (carrier của `citations` chưa phải hợp đồng → agenda freeze D11). Gỡ đoạn suy luận dựng trên tiền đề sai, thay bằng **số đo thật** ngày 28/07; ghi rõ `Live Gemini evaluation: chưa chạy`. Sửa ghi chú lỗi thời *"`RunResult.events` hiện `[]`"* — engine#8 đã merge, đo được 4 event/run. Q2 (`citation_accuracy = 1.0` nhánh từ-chối) nay có số: thổi phồng `aggregate` **+0.067** trên bộ 10. **KHÔNG** bump `SCHEMA_VERSION` — doc-only. Xem §2.7, §2.7.1, §2.7.2.
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
| `AgentAnswer.refused` | `final_state[<llm node>]["refused"]` = **`not citations`** (STRUCTURAL, không đoán text) — xem §2.7.1 |
| `AgentAnswer.citations` | `final_state[<llm node>]["citations"]` — *cái LLM khai* (không dùng chấm; để cross-check) |
| **`CaseRun.events`** | **`RunResult.events`** (list `TraceEvent`) — **nguồn chấm citations** (gom node-agnostic; carrier thực tế = event `llm-step`) |

Node id lấy theo `node.type == llm-step` (**KHÔNG** hardcode `"n_llm"` — recipe đổi id vẫn chạy).
Seam nhận **`tenant_id: UUID`** (D-13): adapter resolve slug→UUID qua `core.tenants` **trước** khi gọi
`kb.search`/`interpreter.run`; evalhub `run_smoke`/CLI resolve tường minh phía trên seam.

**Cập nhật D7 (2026-07-28): `RunResult.events` KHÔNG còn rỗng.** Ghi chú cũ ở đây nói *"`RunResult.events`
hiện `[]` (AIE-1 populate là việc D5 của họ)"* — engine#8 đã merge và mọi node đều emit event thật; đo
trên luồng thật ngày 28/07 ra **4 event/run** (`kb-retrieve · llm-step · tool-call · end`), 1 `run_id`
duy nhất, `ts` đơn điệu tăng. Demo vẫn dùng trace stub ở tầng unit-test cho tất định, nhưng đó là chọn
lựa của test, không còn là hạn chế của engine.

### 2.7.1 `refused` đã đổi ĐỊNH NGHĨA hai lần — mốc nào là mốc nào

Ghi lại đủ 3 mốc, vì §2.7 bản trước chỉ ghi mốc đầu và điều đó **làm doc mâu thuẫn code trên `main`**.
Công bắt lỗi này thuộc **AIE-1 (@TranBaDat2607)**, nêu trong docstring `LlmStepExecutor` của engine#10:
*"§2.7's premise is **false, not merely stale**; it needs updating."* — nhận xét đúng.

| Mốc | engine tính `refused` bằng | Trạng thái doc trước D7 |
|---|---|---|
| ~D4 (`71caeb8`) | `not retrieved_chunks` | ✅ khớp |
| D5 | `answer.strip() == REFUSAL_SENTINEL` | ❌ doc vẫn ghi mốc D4 |
| **D6 — engine#10, ĐÃ MERGE** | **`not citations`** (citation = bracket-trích ∩ `retrieved_chunks`) | ❌ doc vẫn ghi mốc D4 |

Vì sao mốc D4 sai **về bản chất**, không chỉ lỗi thời: `not retrieved_chunks` chỉ bắt refusal khi
retrieval **rỗng tuyệt đối**. Nhưng ở SC-04, fence bỏ đúng chunk Borea, còn ranker vẫn trả 3 chunk
**ankor** trên các từ chung của câu hỏi ⇒ `retrieved_chunks` KHÔNG rỗng ⇒ `refused=False`. Tiền đề của
mốc D4 không đúng trên chính golden-set đang dùng.

Mốc hiện tại (`not citations`) đọc *"grounding được cái gì"* thay vì *"retrieval trả về cái gì"*: một
citation đã vừa **grounded** vừa **được trích thật**, nên "grounded rỗng" đúng nghĩa là "không trả lời
được từ thứ được đưa". Giới hạn đã khai của nó: **một câu trả lời đúng nhưng quên đóng ngoặc bị chấm
thành refusal.** Đó là cùng một tín hiệu mà `citation_accuracy` vốn đã dựa vào, nên case đó đỏ **một
lần** chứ không hai.

**⚠️ Cảnh báo cho người đọc sau:** đoạn trên nói về luật của **engine**, không phải hợp đồng vĩnh viễn.
Bộ chấm phía evalhub **không pin luật này** — test `A4` của adapter (`apps/studio`) chạy
`interpreter.run` lấy quyết định gốc rồi so với `AgentAnswer` đã map, tức khoá *"adapter map trung
thực"* chứ không khoá *"engine quyết bằng công thức nào"*. Nhờ vậy khi engine đổi luật lần thứ ba thì
adapter và scorer không vỡ theo.

### 2.7.2 Carrier của `citations` — CHƯA phải hợp đồng, đưa vào agenda freeze D11

`_retrieved_citations` gom `.citations` của **mọi** event khác `None`, **không lọc `node_type`**
(`harness.py`). Đo trên một run thật ngày 28/07:

```text
kb-retrieve  citations=None                     outputs có 'chunks'=True
llm-step     citations=['ankor-leave-001#c1']   outputs có 'chunks'=False
tool-call    citations=None                     outputs có 'chunks'=False
end          citations=None                     outputs có 'chunks'=False
```

Nguyên nhân: `interpreter.py` rẽ theo kiểu output — node `kb-retrieve` trả `list` nên
`TraceEvent.citations = None` và chunk đi vào `outputs["chunks"]`; `llm-step` trả `dict` nên `citations`
là danh sách **grounded**.

⇒ Việc phân biệt được *"chunk ĐÃ TRUY XUẤT"* với *"chunk ĐÃ GROUNDED"* hiện đúng **nhờ engine hôm nay
chỉ cho `llm-step` mang citations**, KHÔNG nhờ helper ép node. Nếu engine cho `kb-retrieve` cũng mang
citations thì hai nguồn **trộn** và `citation_accuracy` lặng lẽ đổi nghĩa. **Cần chốt carrier với AIE-1
trước D11 freeze** (sau freeze cần mini-RFC + 4/4 chữ ký theo D-12): hoặc siết helper theo `node_type`
cụ thể, hoặc ghi carrier thành ràng buộc trong hợp đồng `TraceEvent`.

**Hệ quả trên luồng thật (cập nhật 2026-07-23, sau khi đọc DE `StaticKbSearch`):** DE đã ship
`StaticKbSearch` (kb.search thô) lọc **cả `tenant` lẫn `section_role`** (`if chunk.tenant != tenant or
chunk.section_role not in allowed`), chỉ khác là *tin giá trị client khai* — phân giải server-side
(chống T6-spoof) để S3.

**⚠️ Đoạn suy luận cũ ở đây đã bị GỠ (D7).** Bản trước lập luận *"vì `refused = not retrieved_chunks`,
cả 5 case hành xử đúng nhãn ở tầng retrieval"* rồi liệt SC-01/02/03 và SC-05 theo tiền đề đó. Tiền đề
sai (§2.7.1), nên suy luận dựng trên nó không dùng được — kể cả những dòng tình cờ ra kết luận đúng.
Thay bằng **số đo thật**, không suy luận.

**Hành vi đo được trên luồng thật, 2026-07-28** (`apps/studio/scripts/e2e_smoke_eval.py`, bộ smoke-5,
LLM = `ExtractiveFakeLLM` — fixture **chỉ đọc prompt**, không thấy `expected`/`expected_citation`):

| case | nhánh | wiring | điểm | vì sao |
|---|---|---|---|---|
| SC-01/02/03 | trả-lời | THÔNG | PASS | đúng tenant+vai → có chunk → grounded → `refused=False` |
| **SC-04** | từ-chối | THÔNG | **FAIL** | retrieval trả **3 chunk ankor** (không rỗng, không leak borea); fixture chép chunk đầu bất kể liên quan ⇒ có citation ⇒ `refused=False` ⇒ nhánh từ-chối đỏ |
| SC-05 | từ-chối | THÔNG | PASS | vai chặn (`hr ∉ [engineering]`) → retrieval rỗng → không gì grounded → `refused=True` |

Nguyên nhân SC-04 đỏ đã **đổi** so với bản D5: không còn là *"`retrieved_chunks` không rỗng nên tín
hiệu sai"* mà là *"model không từ chối dù đoạn trích không trả lời được câu hỏi"*. Tức lỗi dịch từ
**tầng tín hiệu** sang **tầng năng lực của model** — và đó là giới hạn đã khai của `ExtractiveFakeLLM`
(chỉ đọc top-1, không có năng lực quyết định refusal), không phải lỗi hạ tầng.

⚠️ **`Live Gemini evaluation`: chưa chạy.** Mọi số ở bảng trên đến từ fixture tất định. Mục *"≥1 case
FAIL với LLM THẬT"* của mentor (#59) **vẫn treo**.

**Q2 vẫn mở, và giờ có số:** `citation_accuracy = 1.0` cứng ở nhánh từ-chối (`harness.py`) khiến case
**đã đỏ** vẫn góp `1.00` vào `aggregate`. Đo trên bộ 10 case của DE (`callisto-smoke-10-v0`, lượt chạy
28/07): `success_rate = 0.60` nhưng `aggregate.citation_accuracy = 0.90`, trong khi con số **thật** chỉ
tính 6 case trả-lời là **0.833** → thổi phồng **+0.067**, và **3 case đã đỏ** (SC-04/07/09) vẫn góp
`1.00`. Bộ 5 chỉ có 2 case từ-chối nên chuyện này còn mờ; bộ 10 làm nó đọc được ngay.
**KHÔNG đổi pass-rule ở PR này** — cần chốt 3 bên (AIE-1 tín hiệu `refused` · DE corpus · AIE-2 luật
chấm), cửa sổ D7–D8, và mang vào agenda freeze D11.

Protocol seam `KbSearchService.search` **vẫn `NotImplementedError`** — dùng `StaticKbSearch` hay seam
nào là do wiring `studio_app` quyết. Demo chạy qua `StubAgentRunner` (trace stub) cho **tất định**,
không phụ thuộc wiring.

**Adapter #29 (chốt mentor D5 2026-07-24):** mentor **KHÔNG viết hộ** — đây là mảnh tích-hợp học cao
nhất. `apps/studio` mở cho PR: **đồng-tác AIE-1 (nguồn `final_state`/`events`) + AIE-2 (đích
`CaseRun`/`AgentAnswer`)**, SWE review recipe/DAG. Repos đã public → AIE-2 có write `apps/studio`
(fence chuyển sang tầng CODEOWNERS). Xem Q4 §3.

---

### 2.8 tag ≠ isolation — bộ chấm đứng ở đâu trong hàng rào (D8 2026-07-29, #39)

Đoạn này **không lặp lại** lập luận tag-vs-isolation tổng quát: `engine#12` đã viết nó khá đầy trong
docstring `studio_engine/session.py` (AIE-1, merge 29/07 08:02). Đây là phần chỉ tầng eval nói được —
bộ chấm dựa vào cái gì, và cái đó là tag hay isolation.

**Toàn bộ leak-check nhánh từ-chối của scorecard đứng trên một TAG.** `_citation_tenant()` suy tenant
bằng cách cắt tiền tố chuỗi `chunk_id`: `"ankor-leave-001#c1"` → `"ankor"`. Đó là **nhãn mềm** —
chuỗi do bên sinh dữ liệu tự đặt, trùng được, sửa được, và `TraceEvent.citations` là `list[str]`
không mang `tenant_id` per-chunk nên không có gì để đối chiếu. Suy ra: `no_leak` ở §2.3 là **sanity
theo slug**, **không** chứng minh fence RLS-UUID. Đã ghi ở §2.3, nhắc lại ở đây vì đây là hệ quả
trực tiếp của phân biệt tag/isolation.

**Isolation thật nằm ở chỗ khác, và bộ chấm không sở hữu chỗ đó.** `StaticKbSearch` so
`chunk.tenant_id != tenant_id` bằng **UUID** (`packages/kb/src/studio_kb/static_search.py:92`);
`interpreter.run()` lấy `tenant_id` từ `session_context`, không từ `recipe.tenant_id` (`engine#12`);
RLS trên `kb.chunks` khoá theo `app.tenant_id`. Ba lớp đó là fence. Bộ chấm **quan sát** chúng.

**Vì sao "nhờ LLM đừng nói" là fake fence — bằng chứng đã có trong repo, không phải lập luận.**
`_LeakyKb` (`apps/studio/scripts/e2e_smoke_eval.py`) là một KB cố ý hỏng fence: nó bỏ qua `tenant_id`
được truyền vào và tra bằng tenant khác. Chạy XF-02 với nó thì agent **vẫn nói năng lịch sự bình
thường** — không có gì trong câu trả lời tố cáo điều gì — mà conjunct `no_leak` đỏ, vì chunk chéo
tenant **đã nằm trong trace trước khi LLM mở miệng**. Hàng rào đặt ở đầu ra không đổi được sự thật là
dữ liệu đã bị lấy ra; nó chỉ đổi cách dữ liệu được phát âm. Đây cũng là lý do citation-accuracy chấm
theo **trace** chứ theo `AgentAnswer.citations` (§2.7): cái agent tự khai là một tag nữa.

**`tenant_id NOT NULL` — phân biệt hai câu khác nhau.** `TraceEvent.tenant_id: UUID` là non-optional
trong `studio_contracts`, nên NOT NULL đúng sẵn **ở mức kiểu**: pydantic chặn `None` trước khi event
tồn tại, không cần test nào. Thứ chưa ai đo là **nhất quán ở mức run** — mọi event trong CÙNG một run
trỏ về cùng một tenant. Một run mà node đầu mang ankor còn node sau mang borea vẫn thoả NOT NULL từng
dòng mà vỡ hoàn toàn ở mức run. `tenant_scope_ok()` (D8, `harness.py`) đo đúng khoảng trống đó, và
fail-closed khi `events` rỗng: không có trace thì không chứng minh được, và không-chứng-minh-được
phải đọc là chưa đạt. (`all([])` là `True` — viết thẳng `all(...)` sẽ cho một run không có event nào
điểm hợp lệ.)

**Ranh giới cố ý:** `tenant_scope_ok` **observe-only, không gate `success`**. Hai lý do, cả hai đều
là lý do chứ không phải tiện: (a) bộ chấm không tạo fence nên không nên phát verdict thay fence;
(b) `score_case` chỉ nhận `retrieved_citations`, không nhận `events`, nên cấu trúc mà nói không đọc
được `tenant_id` — và đổi chữ ký nó là chuyện khác, có 3 consumer ngoài quadrant đang gọi.

**Nợ để lại, vào agenda D11:** muốn leak-check chứng minh được ở mức UUID thì `TraceEvent.citations`
phải mang `tenant_id` per-chunk. Đó là đổi contract → mini-RFC + 4/4 chữ ký. Không làm ở D8 (`day-08.md`:
*"chưa fence chunk-level — để Sprint 3"*), nhưng ghi ra để lúc đó không phải suy lại vì sao cần.

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
