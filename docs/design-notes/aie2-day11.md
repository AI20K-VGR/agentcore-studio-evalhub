---
id: studio.design-note.aie-2
type: design-note
day: D11
issue: "#83"
author: AIE-2 — Lưu Tiến Duy (@dholmes0207)
date: 2026-08-03
scope: eval harness v1 · golden-set · judge cap ≤100/cache · descope exact-match
status: ĐÃ NỘP · Duyệt: CHỜ
---

# Design-note — AIE-2 · Bộ chấm: eval harness v1, golden-set, judge cap, descope

> **Chỗ đặt: repo của bút** (đây), khớp cả 3 người còn lại — `kb:docs/design-notes/de-day11.md`
> (DE) · `workbench:.../swe-day11.md` (SWE) · `engine:.../aie1-day11.md` (AIE-1).
>
> **Đã đổi chỗ, và lý do đổi đáng ghi.** Bản đầu tôi đặt ở **kit root** với lập luận: file trong
> submodule chỉ thấy được nếu con trỏ kit đã bump, mà lệch con trỏ đã lấy điểm hai lần (`kit#73`,
> `kit#76`/`#77`). Lập luận đó **không sai** nhưng **trả giá sai chỗ**: bản tổng hợp cuối D11 của
> AIE-1 soi `evalhub#6` và kết luận design-note của tôi *"không tách file riêng"* — vì từ trong
> evalhub thì **thật sự không thấy**. Một artifact đặt ở chỗ người audit không nghĩ tới thì mất giá
> trị đúng ở bước nó cần có giá trị nhất.
>
> Đây là **lần thứ hai trong ngày** tôi mắc cùng lớp lỗi: đặt một artifact per-bút ở kit root trong
> khi cả 3 người kia đặt repo-local (lần đầu là decision-log). Ghi lại vì lặp hai lần thì nó là
> **dạng**, không phải sự cố.
>
> **Neo, không suy lại:** GUIDE-C §4.1 (`:280`) — gate = **AND** hai ngưỡng · toán tử **`>=`** · tầng
> **aggregate**. GUIDE-C §3.2 — ngưỡng là **số thập phân tròn, chốt và ghi ra TRƯỚC khi dựng dataset**.

## 1 · Scope — và non-scope

**Trong scope hôm nay (D11):** hợp đồng `scorecard` freeze-ready (9 clause) · 5 quyết định treo từ D2
đã có đáp án · luật bump cho ca thứ tư · pin nhánh từ-chối · đổi neo xfail `no-trace-no-proof`.

**Non-scope, nói rõ để không ai chờ:**

| Không làm | Vì sao |
|---|---|
| Wiring publish/rollback đọc `gate.verdict` | S3 / D24 — bút SWE |
| Dashboard / trace viewer | D25 |
| Implement `compute_scorecard` / `EvalHarness.run` | Xem §3 — đây là **phương án bỏ**, không phải việc quên |
| Fence chunk-level, trục INV-1 roles | S3 / D21-22. Bộ chấm **quan sát** hàng rào, không **tạo** hàng rào |
| Đổi `harness.py:159` | GUIDE-C `:305` — *"must NOT be changed"* (register §11 từng chỉ thị rồi **thu hồi**, CP-2.1) |

## 2 · Phương án chọn — bộ chấm là *quan sát viên*, không phải *người làm hàng rào*

Một câu: **bộ chấm đọc TRACE, không đọc lời agent tự khai.**

- `citation_accuracy` + leak-check lấy từ `CaseRun.events`, **không** từ `AgentAnswer.citations`. Bằng
  chứng đã có trong repo, không phải lập luận: `_LeakyKb` (`e2e_smoke_eval.py`) là KB cố ý hỏng fence —
  agent **vẫn nói năng lịch sự bình thường**, không gì trong câu trả lời tố cáo điều gì, mà conjunct
  `no_leak` **đỏ**, vì chunk chéo tenant **đã nằm trong trace trước khi LLM mở miệng**. Hàng rào đặt ở
  đầu ra không đổi được sự thật là dữ liệu đã bị lấy ra; nó chỉ đổi cách dữ liệu được phát âm.
- `tenant_scope_ok` **observe-only, không gate `success`** — hai lý do, cả hai là lý do chứ không phải
  tiện: (a) bộ chấm không tạo fence nên không phát verdict thay fence; (b) `score_case` không nhận
  `events` nên **cấu trúc mà nói** không đọc được `tenant_id`.
- **`no-trace-no-proof` thuộc tầng giữ `events`, không thuộc `score_case`.** Đây là chỗ bản vá hiển
  nhiên **là sai**, và nói ra điều đó là một phần của thiết kế: invariant đúng là *"không có trace quan
  sát được ⇒ FAIL"*, **không** phải *"citation rỗng ⇒ FAIL"* — luật sau ngược oracle F02
  (GUIDE-C `:592`: *"refused, cited nothing ⇒ the case PASSES"*).

**Golden-set:** DE sở hữu **giá trị** (case + nhãn tay + tên bộ), AIE-2 sở hữu **nơi lưu + loader**
(`eval.golden_sets`). Chọn bảng đó vì nó là bảng **có người ghi được** — `obs.golden_sets` nằm trong
`apps/studio`, ngoài fence-lane của DE, nên DE không điền được. Đó là câu hỏi của chính DE, trả bằng
quyền chứ không bằng sở thích.

**Judge cap ≤100/ngày + cache:** cap là **điều kiện kích hoạt descope**, không phải tính năng. Khi
chạm trần ⇒ rơi về exact-match scorer (INV-7). Cache theo `(case_id, actual)` vì `actual` tất định với
`ExtractiveFakeLLM`, nên cache hit trong CI là 100% và cap không bao giờ chạm trong test.

## 3 · Phương án BỎ (bắt buộc) — và đây là phương án mạnh nhất có thật

### Bỏ 1 · Implement `compute_scorecard` hôm nay để đóng `O3.1`

`O3.1` là ô **nặng nhất** trong grid (+1.91), và nó hỏi *"thứ đó có tồn tại không"* — hôm nay
`gate.verdict` vẫn chưa có, **0/9 ô Grid C dựng được**. Nên đây là phương án hấp dẫn nhất, không phải
bù nhìn.

**Bỏ, vì land hôm nay là tự phá 4 ô đắt nhất trong grid của chính mình.** GUIDE-C §3.2 đòi ngưỡng
literal phải **có trước** dataset; dataset (golden-30) về **D14-15**, sau corpus D13. Viết gate trước
khi có ngưỡng chốt-trước nghĩa là ngưỡng sẽ được chọn *sau* khi thấy số — đúng thứ §3.2 cấm
(`threshold := giá trị mà lượt chạy vừa tính ra`). Hệ quả đo được: 4 ô *"exactly-at"* (D-22 so `==`
trên ngưỡng tròn, `11/20 = 0.55` exact trong CPython 3.14) thành `unknown`.

Cộng thêm ba giá độc lập: `test_gate_blocks_on_fail` là `xfail(strict=True)` ⇒ land hôm nay làm nó
**XPASS ⇒ FAIL** trong lúc quyền đổi marker (M6, GUIDE-C §2.3: *"Do not edit that marker on your own
authority"*) **chưa chốt**; `test_harness_judge_compute_not_implemented` đỏ ngay ngày freeze; và #50
xếp eval-gate blocking là **gold-plating** (S3/D24), ETA của GUIDE-C là D20, #108 là D16.

⇒ Đúng hạn là **D16**, và claim `O3.1 = I` hôm nay là calibration, không phải khiêm tốn.

### Bỏ 2 · Cho `citation_accuracy` gate `success` ở mức per-case

**Bỏ** vì nó **đếm hai lần** mọi lỗi citation: trace sai đã làm `citation_accuracy` tụt ở tầng
aggregate; cho nó gate `success` nữa thì cùng một lỗi kéo cả hai trục của một gate **AND** ⇒ ngưỡng
mất nghĩa. Thêm một lý do đọc-tài-liệu: register của mentor **từng chỉ thị rồi thu hồi** đúng điểm này
(GUIDE-C §4.1 / CP-2.1, `:305`) — nêu nó ra là để chứng minh đã đọc **phần thu hồi**, không chỉ phần
chỉ thị.

## 4 · Trade-off — nói cả chiều lệch

| Chọn | Được | Mất | Chiều lệch |
|---|---|---|---|
| **token-contains** thay exact-match | Câu trả lời đúng ý mà khác cách diễn đạt vẫn PASS; `"1 ngày"` **không** khớp `"11 ngày"` (token `"11"` ≠ `"1"`) nên tránh bẫy substring thô | Không bắt **phủ định** — câu phủ định vẫn "chứa" cụm nên vẫn PASS. Ghi là **giới hạn đã biết, KHÔNG xfail** | **Lệch LÊN** ở ca phủ định (nguy hiểm hơn) |
| **exact-match** thay judge (descope) | Tất định, không phụ thuộc quota/mạng | Câu đúng ý khác chữ bị tính sai | **Lệch XUỐNG** — gate có thể chặn bản đạt, **không** cho lọt bản không đạt. Đây là chiều lệch đúng cho một hàng rào |
| **leak sanity mức slug** thay fence UUID | Chạy được hôm nay, 0 phụ thuộc | `_citation_tenant` cắt tiền tố chuỗi `chunk_id` (`harness.py:49-57`) — **nhãn mềm**: trùng được, sửa được | Chỉ chứng minh tới **mức nhãn**; fence thật là `StaticKbSearch` so UUID + RLS |

Đường lên mức UUID **không cần đổi contract** — đây là chỗ đã **tự rút một tiền đề của mình**:
`outputs["chunks"]` đã mang `tenant_id: UUID` per-chunk từ D5, 4 consumer đang đọc. Thiếu là **một
dòng hợp đồng**, không phải một field. `scorecard-v0.md:335-337` từng định giá nó thành *"mini-RFC +
4/4 chữ ký"* — sai, và định giá quá cao làm việc bị hoãn vô cớ.

## 5 · Rủi ro

| Rủi ro | Vì sao nó thật | Trạng thái |
|---|---|---|
| **Không có nguồn nhãn tay cho `Judge.agreement`** | Field **đích** đã có (`scorecard.py:19`); field **nguồn không tồn tại** ở bất kỳ đâu trong workspace; hằng số **bị cấm** (`judge.py:6-9`) ⇒ **mọi ô judge là `todo:` không có ETA cam kết được**. Đây là món **không tự đặt đáp án** | 🔴 chặn · chủ **mentor** · hạn D18 |
| **Mọi ngưỡng đang pin vào một stand-in** | `ExtractiveFakeLLM` chỉ đọc top-1, không có năng lực quyết định refusal. Với mặc định `0.9/0.95` (**`workbench`**, xem bảng 4 chỗ dưới đây), số đo thật là bộ 5 → `0.80`, bộ 10 → `0.60` / `citation_accuracy` `0.833` ⇒ **một recipe TỐT cũng FAIL cả hai trục**, nên demo *"sửa instructions tệ → FAIL → chặn publish"* chứng minh **số không** | 🟡 recalibrate D16, chủ AIE-2. **Không** hạ số hôm nay — hạ bây giờ là hiệu chỉnh theo stand-in |
| **golden-30 về sau corpus D13** | Corpus-cutover D13 gần chắc làm `smoke-5`/`smoke-10` hiện tại vỡ ⇒ số ở D16 có thể bị đọc là **hồi quy của bộ chấm**. Kế hoạch: sáng D13 hỏi lịch cutover, chiều re-run và báo lệch trước | 🟡 chủ DE (giao bộ) + AIE-2 (báo lệch) · hạn D15 |
| **Carrier `citations` là hành vi, không phải cấu trúc** | `citations_from_trace` gom **node-agnostic** (`harness.py:85-89`) nên phân biệt retrieved/grounded **chỉ vì engine hôm nay tình cờ hành xử vậy**. Bất kỳ node trả **dict** có key `"citations"` sẽ mang citations vào trace | ✅ **phía engine ĐÓNG 04/08** — AIE-1 giao clause + code + test (`engine#15` merged `04:07:30`, `interpreter.py:304` gate `node_type is NodeType.LLM_STEP`, `engine:docs/contracts/trace-citations.v0.md`). 🔴 **phía evalhub CHƯA có lưới** — chủ **AIE-2**, hạn **D16** |
| **`refused` cho dương-tính-giả (#14)** | `refused = not citations`: câu bịa trọn vẹn mà quên đóng ngoặc ⇒ `citations=[]` ⇒ `refused=True` ⇒ **SC-04 PASS dù agent đã bịa**. Trên bài kiểm hàng rào, **xanh-giả nguy hiểm hơn đỏ-giả** | 🟡 chủ **AIE-1** · hạn D17 |
| **`eval.scorecards`/`eval.golden_sets` không có `tenant_id` và không có RLS** | Tự khai: workspace có RLS trên **1/11** bảng; hai bảng của AIE-2 là **0/2**. Đã đồng-ký mini-RFC tenant+RLS của DE (kb#10) với hai bảng này tính vào | 🟡 chủ AIE-2 + DE · hạn D16 |

> ### Ngưỡng `0.9/0.95` nằm ở **BỐN** chỗ, tất cả trong `workbench` — không có chỗ nào trong `evalhub`
>
> Người recalibrate ở D16 cần cả bốn; đổi một chỗ mà quên ba chỗ kia là tạo ra hai bộ số cùng tồn tại.
>
> Trích theo **tên hàm** (bền), số dòng chỉ phụ trợ — và số dòng phải nêu **ref nào**, vì
> **3/4 anchor đã dịch** trên nhánh PR đang chờ merge:
>
> | Chỗ, theo tên (`workbench:src/studio_workbench/builder.py`) | `main` `aaeefa5` | `#12` `022aad5` / `#13` `583bcf9` |
> |---|---|---|
> | **default param** của `create_dynamic_recipe` | `:48-49` | `:48-49` (ổn định) |
> | hardcode `ScorecardThreshold(...)` trong `create_sample_recipe_d3` | `:114` | **`:110`** |
> | hardcode `ScorecardThreshold(...)`, lượt thứ hai | `:192` | **`:188`** |
> | **default param** của `create_recipe_d6` — **đường runtime**, hàm demo D10 dùng | `:206-207` | **`:202-203`** |
>
> Cả `workbench#12` và `#13` đang **`APPROVED` + `CLEAN`**, nên cột phải sẽ **thành `main`** ngay khi ai
> merge. Người recalibrate ở D16 hầu như chắc chắn đọc cột phải.
>
> **Bản trước đếm BA và tự khai "đã đếm" — @DongAnh2704 bắt được chỗ thứ tư.** Finding của họ sắc ở chỗ
> chỉ ra *vì sao* tôi dừng sớm: cùng file, cùng lượt đọc, tôi đếm đủ `golden_set_ref` (`:47,191,205`) mà
> dừng ở ba cho ngưỡng — dù ngưỡng nằm ngay hai dòng dưới. Và `:206-207` là chỗ **nặng nhất trong bốn**:
> nó là default param của một hàm **khác**, trên đường runtime demo, không phải sample recipe.
>
> **Một bảng tự khai "đã đếm" thì người D16 không đếm lại** — đúng failure mode mà bảng này được viết ra
> để chặn. Nên chỗ này là lỗi tệ hơn một anchor thiếu tiền tố repo.
>
> **Vì sao mọi dòng đều nêu tên repo:** bản đầu viết trần `builder.py:48-49`; trong một design-note nằm ở
> `evalhub`, người đọc resolve theo repo đang đứng, và DE chạy `find packages/evalhub -name builder.py`
> rồi kết luận anchor sai. Kết luận đó sai nhưng **finding thì đúng** — một trích dẫn cross-repo không
> nêu repo là trích dẫn mơ hồ. Trong `evalhub` thì `0.9/0.95` **chỉ có trong test fixture**, đúng như DE đo.
>
> **Bài học thứ hai, và nó là bài học về CÁCH ĐO chứ không về nội dung:** bảng ở trên ban đầu tôi đo
> trên **submodule đang ghim trong kit** — tức `workbench@main`. Nhưng thứ sắp thành `main` là **nhánh
> PR**, và ở đó 3/4 anchor đã khác. Một phép đo đúng-trên-`main` mà sai-trên-nhánh-sắp-merge thì nó
> **đúng trong quá khứ**, không đúng ở lúc người ta đọc.
>
> ⇒ **Đo trên nhánh PR mới nhất, không đo trên `main`** — và nếu buộc phải nêu số dòng thì nêu kèm ref.
> Đây là dạng thứ năm của cùng một bệnh mà @DongAnh2704 đã bắt bốn dạng đầu: khai một trạng thái mà
> không kiểm lại **tại đúng thời điểm và đúng ref** người đọc sẽ dùng.

---

**Trạng thái nộp:** `ĐÃ NỘP evalhub:docs/design-notes/aie2-day11.md` (PR `evalhub#7`).
**Duyệt:** 2 Approve trên PR — @TranBaDat2607 `04:21`, @Dozyboy `04:40`.

Ô DoD *"4/4 design-note approved"* **vẫn KHÔNG tick**: hai Approve trên PR chứng minh **đồng đội đã đọc
và đồng ý**, không chứng minh **approver của DoD đã duyệt** — và theo giới hạn cơ học @TranBaDat2607 đo
ở kit#84 §5, trần chữ ký của một bút trên PR của chính mình là **3/4**, không phải 4/4. Tick ô đó là
hành động của approver, không phải của người nộp.
