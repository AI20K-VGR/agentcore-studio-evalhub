# Plan Day 11 — AIE-2 · Freeze hợp đồng scorecard · Thứ Hai 03/08/2026

# Executive Summary

**Goal.** Đóng băng hợp đồng `scorecard` với chữ ký + SHA; chốt 5 quyết định treo từ D2; sửa **2 dòng**
contract trong ngày cuối còn rẻ (sau freeze mỗi dòng = mini-RFC + 4/4 chữ ký); và để lại một cơ chế
freeze/chữ ký/decision-log mà 3 người kia dùng lại được trong ~60 giây.

**Deliverables**

| # | Deliverable | Đường dẫn |
|---|---|---|
| 1 | Contract diff 2 dòng (`judge` optional · `recipe_hash`) + 2 test | `packages/contracts/src/studio_contracts/scorecard.py` |
| 2 | Hợp đồng đã freeze | `packages/evalhub/docs/contracts/scorecard.v1.md` |
| 3 | Decision-log 5 quyết định có id/chủ/hạn | `kit:docs/decision-log.md` |
| 4 | Hồ sơ freeze + 4 file chữ ký (1 ký thật, 3 điền sẵn) | `kit:docs/decisions/s1-contract-freeze/` |
| 5 | Design-note ≤2 trang | `kit:docs/design-notes/aie-2-dholmes0207.md` |
| 6 | Template mini-RFC + 1 bản điền thật | `packages/evalhub/docs/mini-rfc/` |
| 7 | Bảng 5 mutation gieo vào engine (khai-trước) | `kit:docs/mutations/s2/dholmes0207-into-engine.md` |
| 8 | Note D11 + bump con trỏ | `docs/reports/daily-notes/2026-08-03-dholmes0207.md` · kit PR-E |

**Critical Path**

| Order / Giờ | Action | Depends on | Output |
|---|---|---|---|
| 1 · 09:00 | Sync + baseline + re-check brief/#83/#84 | — | Bộ số đối chiếu (App. A.1) |
| 2 · 09:30 | Comment #84 (cơ chế freeze + chữ ký + decision-log + 2 giờ cắt) · #83 (phạm vi 1/4) | 1 | Cơ chế công bố **trước** khi ai cần dùng |
| 3 · 10:00 | Push **PR-A** + chạy proof consumer + dán số vào body | 1 | PR-A mở, reviewable |
| 4 · 10:10 | Xin approval PR-A (Dat) + pre-book 3 PR còn lại | 3 | **Đồng hồ chờ duy nhất bắt đầu** |
| 5 · 10:30 | Hỏi #81 → #80 → #82 → #83 (§3) | 2 | 14 quyết định vào hàng đợi |
| 6 · 12:00 | **Ký 3 hợp đồng người khác trước**, mỗi review 1 finding | 5 | 3 review có finding |
| 7 · 13:30 | **PR-C** (decision-log + hồ sơ freeze + 4 sig + design-note) | 2, 5 | Deliverable 3, 4, 5 |
| 8 · 14:00 | **PR-B** (evalhub: docs + 2 test, **không đụng `src/`**) | 1 | Deliverable 2, 6 |
| 9 · 15:00 | Design-note ≤2 trang (mục "phương án bỏ" bắt buộc) | 5 | Deliverable 5 |
| 10 · 16:00 | Gieo 5 mutation vào engine + bảng khai-trước | 2 | Deliverable 7 |
| 11 · **16:30** | **ĐÓNG BÀN GIAO.** Merge A→B→C | 3,7,8 + approval | Nội dung chốt |
| 12 · 16:45 | **PR-E** bump con trỏ (evalhub + docs/reports) | 11 | Deliverable 8 |
| 13 · 17:00 | **Giờ cắt 1**: áp mặc định đã công bố; phần chưa trả lời → `DEFERRED(chủ, hạn)` | 5 | Decision-log trạng thái cuối |
| 14 · 17:30 | Note D11 → PR-D → gộp vào PR-E | 13 | Deliverable 8 |
| 15 · **19:00** | **Giờ cắt 2 = hỏi mentor**: ngày golden-30 · chủ INV-1 · SLA duyệt | 13 | Escalation kèm lưới đỡ |
| 16 · 20:00 | Clone sạch verify (App. D) + tick **chỉ** ô chứng minh được | 12, 14 | Exit criteria |

Không bước nào từ 7→16 chờ bước 4. Nếu bước 4 chưa xong tới 17:00 → §6.

**Blocking Dependencies**

| Cần | Từ | Required response | Nếu thiếu |
|---|---|---|---|
| 1 approval trên PR-A | @TranBaDat2607 (CODEOWNERS contracts) | approve | Deliverable 1 chuyển thành mini-RFC viết sẵn, hạn D16. **Freeze vẫn đi** |
| Ngày giao golden-30 | @DongAnh2704 | một ngày cụ thể | Non-blocking hôm nay · **blocking D16** ⇒ escalate 19:00 |

Mọi dependency khác **non-blocking** và đều có mặc định đã công bố hoặc fallback kỹ thuật (§6).

**Exit Criteria** — đo trong **clone sạch**, không đo working tree:

1. `pytest packages apps tests` = `333–334 passed, 8 skipped, 5 xfailed`, **0 XPASS**
2. Ba số bảng điểm **không đổi**: `cli` 5/5 · `e2e` wiring 5/5 + quality 4/5 + RED-CHECK 2/2 · `smoke_eval_d6` 6/10
3. 5 con trỏ submodule = `main` của repo con · kit CI 10/10
4. 8 deliverable hiện ra trong `git clone --recursive`
5. Decision-log có 5 dòng DEC; **0 món hoãn không có chủ + hạn**
6. 0 ô DoD tick mà không chứng minh được

---

# §1 — Quyết định phải chốt hôm nay

Thứ tự phụ thuộc: **DEC-01 trước**, vì DEC-02/03 là cùng một câu hỏi cơ học ("loại thay đổi này có bump
không?"). Hỏi ba lần riêng lẻ là cách hết giờ; hỏi một lần, lấy một phán quyết, áp cho ba dòng.

```
DEC-01 luật bump ──┬─▶ DEC-02  judge nullability
                   └─▶ DEC-03  recipe_hash
A1-1 carrier ─────────▶ DEC-04  citation_accuracy nhánh từ-chối  ─▶ DEC-05  no-trace-no-proof
```

A1-1 phải đứng trước DEC-04/05 vì nếu carrier đổi thì `retrieved_citations` đổi nghĩa, và lập luận F02
đổi theo.

## DEC-01 · required→optional có bump `SCHEMA_VERSION`?

- **Objective** — có **một phán quyết viết ra** cho cả ba dòng diff, để S2 không kiện lại "anh ship
  breaking change".
- **Đề xuất** — **Không bump.**
- **Reasoning** — `contracts/__init__.py:5-12` liệt kê đúng ba loại breaking: *rename · removal ·
  required-add*. Nới lỏng required→optional **không nằm trong ba loại đó**, và guard cơ khí hoá duy nhất
  (`test_freeze_guard.py:36-56 test_required_add_breaks_old_payload`) chỉ đo chiều required-add. Chiều
  tương thích: mọi payload cũ vẫn validate. Chiều không tương thích là old-reader/new-payload — và
  **hiện có 0 reader** (App. A.8). Nhưng **quy tắc im lặng về nới lỏng**, nên đây là **phán quyết, không
  phải suy luận**: phải có người nói ra và ghi lại.
- **Evidence** — App. A.8 (grep 0 reader / 4 constructor) · `contracts/__init__.py:5-12`.
- **Owner / Required response** — mentor · một chữ: bump hay không.
- **Blocking?** — **Non-blocking**: cả hai biến thể đã viết sẵn (App. A.9), merge được trong cùng phiên
  dù phán quyết đi hướng nào.
- **Artifact** — 1 dòng decision-log trích **nguyên văn** `__init__.py:5-12` + phán quyết + người quyết + ngày.
- **DoD** — dòng log tồn tại kể cả khi mentor không trả lời (khi đó ghi: *"quy tắc không phủ ca này; áp
  cách đọc hẹp = không bump; chờ xác nhận"*). **Thiếu chữ mới là rủi ro, không phải chọn đáp án nào.**

## DEC-02 · `CaseResult.judge` điền gì khi case không qua judge (Q1)

- **Objective** — mở đường cho D16 dựng `CaseResult` mà không phải bịa một phép đo.
- **Đề xuất** — `judge: Judge | None = None`.
- **Reasoning** — ba phương án:
  - **(a) `Judge | None`** — thay đổi cộng thêm, biểu diễn đúng trạng thái "case không qua judge".
  - **(b) hằng `Judge(label="exact-match", agreement=1.0)`** — **bỏ**. `judge.py:6-9` cấm giá trị hằng, và
    lập luận sâu hơn: `agreement` đo *scorer có đồng ý với nhãn tay hay không*. Với case exact-match FAIL
    thì agreement không phải 1.0, cũng không phải 0 — nó **không xác định**, vì không có verdict của người
    cho từng `actual`. Điền 1.0 là bịa một phép đo, đúng thứ `judge.py` sinh ra để chặn. GUIDE-C `:855-887`
    gọi loại này là *"a quality-check metric filled in by the subject of the check"*.
  - **(c) discriminated union** — **bỏ**. Breaking change thật, cho một phân biệt mà `expects_refusal`
    (`golden_case.py:87-109`) đã suy được từ dữ liệu.
  - Nếu **không** làm hôm nay: D16 buộc chọn giữa (b) — thứ `judge.py` cấm — hoặc không dựng `CaseResult`
    nào cả. Nên đây là dòng duy nhất **chặn typing của #108**.
- **Evidence** — App. A.8: **0 reader, 4 constructor toàn test fixture**; `_assert_roundtrip_both_directions`
  là dump→validate→dump nên field default `None` round-trip cả hai chiều alias ⇒ **0 test cũ phải sửa**.
- **Owner / Required response** — @TranBaDat2607 · approve PR-A.
- **Blocking?** — **Blocking** deliverable 1 (không chặn 7 deliverable còn lại).
- **Artifact** — `scorecard.py:30` + 1 test mới (bỏ `judge` vẫn validate, `.judge is None`, round-trip 2 chiều).
- **DoD** — merged, hoặc mini-RFC viết sẵn + hạn D16 (không có trạng thái thứ ba).

## DEC-03 · `recipe_hash` trên `Scorecard` (ruling D-24 của mentor)

- **Objective** — trả một món mentor đã đặt hạn "trước D20", trong ngày nó còn giá 1 dòng.
- **Đề xuất** — `recipe_hash: str | None = None`, kèm luật an toàn: publish coi `recipe_hash is None` là
  **"không verify được ⇒ từ chối"** (fail-closed), nên một field *optional* là đủ, không cần required-add.
- **Reasoning** — `02-MATRIX.md:284` (ruling D-24) ghi *"Fix the schemas before Day 20, then write the
  tests. **Add `recipe_hash` to `Scorecard`**"*, owner **AIE-2 (contract)**, kèm câu *"`Scorecard` is frozen
  contract #4, so this needs a mini-RFC with four signatures"*. Tức mentor **đã định giá** phương án hoãn:
  4 chữ ký. Hôm nay: 1 dòng, additive-optional thuần, không bump dưới bất kỳ cách đọc nào của DEC-01.
  Điểm yếu phải nói thẳng: **land một field chưa có producer** — `Recipe` hiện không có `version`/hash
  (`recipe.py:79-94`), dù `wb.recipe_versions` đã tồn tại (`workbench/.../schema.py:39`), nên cách suy ra
  giá trị là quyết định chung với SWE. Vì nó **không chặn gì trước D20**, đây là **món đầu tiên bị cắt nếu
  hết giờ** — nhưng cắt thì giá tăng 10×, nên vẫn đề xuất làm.
- **Evidence** — `02-MATRIX.md:284` · `GUIDE-B-recipe.md:571,679` (flow S2 không dựng được nếu thiếu).
- **Owner / Required response** — @TranBaDat2607 approve PR-A · @Dozyboy nhận việc suy ra giá trị, hạn D12.
- **Blocking?** — **Blocking** deliverable 1 · **non-blocking** mọi thứ khác.
- **Artifact** — field mới trên `Scorecard` + 1 test chứng minh additive (dict `Scorecard` kiểu pre-D11,
  không có `recipe_hash`, vẫn validate).
- **DoD** — merged, hoặc mini-RFC viết sẵn hạn D16 + dòng log ghi SWE nhận phần giá trị.

## DEC-04 · `citation_accuracy` nhánh từ-chối (Q2 = breakpoint #9)

- **Objective** — chặn một con số biết thổi phồng `aggregate`, và chảy thẳng vào `gate.verdict`.
- **Đề xuất** — ba phần, một luật:
  1. **Aggregate:** loại case từ-chối **khỏi mẫu số** `aggregate.citation_accuracy`.
  2. **Per-case:** **giữ `1.0`** và **pin nó bằng test** nêu tên `harness.py:172` + Q8 + id DEC.
  3. **Render:** bảng người-đọc in `n/a` cho dòng từ-chối thay vì `1.00` — land **D12** (#88, đúng nội
     dung "scorecard skeleton render trống").
  4. **Cách biểu diễn** trong contract (nullable vs `n_scored_citation` trên `Aggregate`) → **để D16**.
- **Reasoning** — số đo của chính mình trên bộ 10 (`scorecard-v0.md:276-282`): `success_rate = 0.60` nhưng
  `aggregate.citation_accuracy = 0.90`, trong khi con số thật chỉ tính 6 case trả-lời là **0.833** ⇒ thổi
  phồng **+0.067**, và **3 case đã đỏ** (SC-04/07/09) vẫn góp `1.00`. GUIDE-C Q8 thêm phép tính chí tử:
  10 refusal ở 1.0 + 20 answered ở 0.85 = **đúng 0.90**, nên với toán tử `>=` một bản **đáng FAIL** lại
  PASS ngay tại ngưỡng 0.9. Vì sao **không** đổi per-case hôm nay: `SmokeResult.citation_accuracy` phải
  giữ `float` — 3 renderer format `:.2f` (`cli.py:222` · `smoke_eval_d6.py:219` · `e2e_smoke_eval.py:294`)
  sẽ `TypeError` với `None`; và `e2e_smoke_eval.py:407` **đã** in `n/a*` cho nhánh từ-chối, nên quy ước
  "không áp dụng" đã tồn tại ở tầng render. Vì sao chọn per-case-giữ-1.0 + pin: `expected_citation == []`
  trên nhánh **trả-lời** cũng trả `1.0` (`harness.py:167`) ⇒ quy ước vacuous-truth tồn tại **cả hai
  nhánh**, nên phải phát biểu nó là **quy ước**, không phải phép đo.
- **Evidence** — `scorecard-v0.md:276-282` (số đo) · App. B.2 (Q8) · GUIDE-C §6.4.2 đòi pin, §9 ghi pin
  **chưa tồn tại** ⇒ đổi `1.0` thành `0.0` ở đó hôm nay **không làm đỏ gì**.
- **Owner / Required response** — mình quyết · chỉ cần biết mentor không phản đối.
- **Blocking?** — **Non-blocking**.
- **Artifact** — pin test mới trong `test_smoke_runner.py` · §3 của `scorecard-v0.md` chuyển Q2 → đáp án
  có id DEC · dòng log.
- **DoD** — pin test xanh · **không đụng `harness.py`** · dòng log ghi nợ đúng chữ: *"`aggregate` không
  tính lại được từ payload `results` đã lưu"*, chủ mình, hạn D16 (xem R5).

## DEC-05 · `no-trace-no-proof` fail-open

- **Objective** — đóng đúng lỗ, không đóng lỗ tưởng tượng. **Đây là món mà bản vá hiển nhiên là sai, và
  nói ra điều đó chính là deliverable.**
- **Đề xuất** — tinh chỉnh, **không lật**:
  - (i) refused + có run thật + 0 citation ⇒ **PASS**;
  - (ii) refused + **0 event** ⇒ **FAIL**, cưỡng chế ở tầng **giữ `events`** (`run_smoke` /
    `EvalHarness.run`), đúng như `tenant_scope_ok` đang làm;
  - (iii) chữ ký `score_case` **không đổi hôm nay**;
  - (iv) hiện thực land **D16** (hoặc D12/D15 khi có entry point đọc trace thật).
- **Reasoning** — `score_case` chỉ nhận `retrieved_citations: list[str]` (`harness.py:145`), nên **cấu
  trúc mà nói nó không phân biệt được** hai trạng thái: *"chưa có run nào"* vs *"có run, không trích gì"*.
  `tenant_scope_ok` phân biệt được vì nó nhận `events` và fail-closed ở `harness.py:117-119`. Hai hàm cùng
  đọc một mặt quan sát mà một bên fail-closed, một bên fail-open — nhưng **nguyên nhân là tầng, không phải
  cẩu thả**. GUIDE-C `:592` (ô F02) phán: *"the honest refusal: refused, cited nothing ⇒ **the case
  PASSES**"* — tức xfail D9 của chính mình (`test_smoke_runner.py:276-306`, assert `success is False` cho
  cùng input) đang **ngược oracle của mentor**. Fixture của chính mình chứng minh khoảng cách:
  `test_determinism.py:113` dựng ca từ-chối bằng `events=[_event([])]` — **một event, zero citation** = F02,
  **không** phải no-trace. Kết luận: invariant đúng là *"không có trace quan sát được ⇒ FAIL"*, không phải
  *"danh sách citation rỗng ⇒ FAIL"*; và nó thuộc tầng giữ `events`. Điều này **đồng thời tháo bẫy
  hai-test-lật-cùng-lúc**, vì nó quyết định bài nào đúng thay vì lật cả hai.
- **Giá nếu phòng vẫn muốn lật thẳng** (đọc ra, và bảng giá này tự nó là một deliverable): đỏ
  `test_refusal_success:241` · `test_cross_role_refusal_success:362` · `test_run_smoke_over_set:392`;
  XPASS⇒FAIL bài `:276`; bảng điểm `cli` 5/5→3/5 · `e2e` quality 4/5→3/5 · `smoke_eval_d6` 6/10 tụt; và
  **mọi số trong pack GATE-1 + note D10 thành cũ 24h sau khi submit**. Chưa kể bản vá đúng chạm 4 consumer
  qua 3 repo (App. A.10) đúng ngày freeze.
- **Evidence** — `harness.py:145,117-119` · App. B.3 (F02 + bảng giá) · `test_determinism.py:113`.
- **Owner / Required response** — mình quyết · không cần ai trả lời.
- **Blocking?** — **Non-blocking**.
- **Artifact** — đổi **neo** của xfail (`test_smoke_runner.py:276-306`) từ `score_case(..., retrieved_citations=[])`
  sang một ca `run_smoke` có `CaseRun.events == []`, **giữ `strict=True`** (vẫn đỏ hôm nay, xanh đúng ngày
  D16 vá) · sửa docstring `test_refusal_success:224-241` từ *"ghi hành vi hiện tại"* → *"quyết định D11,
  oracle F02 `GUIDE-C:592`"* · dòng log.
- **DoD** — evalhub vẫn `2 xfailed, 0 xpassed` · cặp test mâu thuẫn thành **cặp đã-quyết** · **không** đụng
  `test_citation_accuracy_zero_when_trace_empty_but_success_still_true:168-176` (GUIDE-C `:909`: *"This pin
  should not move. If your change turns it red, your change is the thing that is wrong."*).

---

# §2 — Work items

## T1 · Pre-flight & baseline

- **Objective** — có bộ số để mọi delta sau đó quy trách nhiệm được; xác nhận brief vẫn chưa publish.
- **Evidence** — App. A.1 (baseline) · A.2 (brief 404).
- **Expected artifact** — bộ số dán vào note D11.
- **DoD** — 5 con trỏ = `main` submodule · working tree sạch · baseline khớp App. A.1 · đã re-check
  `week-2/days/day-11.md`. **Nếu brief đã publish thì brief thắng plan này** (R8).

## T2 · Công bố cơ chế freeze

- **Objective** — biến 4 dòng DoD không có định nghĩa thành cơ chế 4 người chạy được, kèm đường lùi.
- **Reasoning** — App. A.4: **không tồn tại** file decision-log, template mini-RFC, hay bất kỳ tiền lệ chữ
  ký nào trong org; `week-2/days/day-11.md` 404 nên DoD 4 dòng là spec duy nhất. Ba trong bốn dòng DoD của
  mình (`4/4 contract`, `4/4 design-note`, `4/4 chữ ký`) là **biến đếm nhóm** — một người không thoả được.
  #84 **không có assignee**, tức dòng 4/4 không có chủ. Đây đúng lỗ S1 mà mentor mô tả: *"the problem is
  not awareness, it is that nobody owned closing it"* — và bản vá là escalate **09:30**, không phải 18:00.
  Giá trị của việc này sụp nếu làm muộn, nên nó là bước 2, không phải bước 8.
- **Expected artifact** — comment #84 (cơ chế chữ ký + đường dẫn decision-log + mặc định + 2 giờ cắt) ·
  comment #83 (phạm vi 1/4 + ghi thẳng 3/4 dòng DoD là biến đếm nhóm).
- **DoD** — công bố **trước 10:00** · nêu #84 vô chủ + đề xuất chủ (Dat; carry #10 *"ownership of the
  handover layer"* là của anh ấy) + nhận làm thư ký nếu 12:00 chưa ai nhận · có câu **"brief publish sau
  thì brief thắng, và file này ghi lại việc chuyển đổi"** — công bố kèm đường lùi, không xin phép.

## T3 · PR-A — contract diff 2 dòng

- **Objective** — mở `judge` và thêm `recipe_hash` trong ngày còn rẻ.
- **Reasoning** — xem DEC-02, DEC-03. Thêm một tính chất quyết định topology: **mọi dòng mới đều có default
  hoặc nới kiểu**, nên 0 consumer phải sửa ⇒ PR-A và PR-B **giao hoán được**, và bump con trỏ không thể
  làm vỡ workspace vì chưa code nào đọc field mới. Không đụng `citation_accuracy` hôm nay (DEC-04 phần 4).
- **Evidence** — App. A.8 (grep) · A.6 (CI không test consumer ⇒ phải tự chạy proof) · A.9 (biến thể có-bump).
- **Expected artifact** — PR-A: `scorecard.py` +2 field + docstring/field, +2 test, **0 test cũ sửa**; body
  gồm (a) mục *"anh đang ký cái gì"* 5 dòng, (b) bảng consumer-impact kèm lệnh grep, (c) số proof consumer.
- **DoD** — `mypy packages apps` Success 110 file · `pytest packages apps tests` không đỏ · body ghi rõ
  **contracts-CI xanh không chứng minh workspace xanh** · biến thể có-bump đã viết sẵn · xin mỗi người ký
  nêu **một consumer họ đã kiểm** (chống chữ ký hình thức, R6).

## T4 · Đặt 14 câu quyết định (nội dung §3)

- **Objective** — mỗi câu đóng gói để trả `yes` / `no` / `no + thay bằng X`, không phải "để tôi nghĩ".
- **Reasoning** — thứ tự theo **độ trễ review**, không theo phụ thuộc quyết định: AIE-1 trước vì anh ấy là
  gatekeeper duy nhất thật và review S1 trung bình 435 ký tự ⇒ cần runway dài nhất + ask nhỏ nhất; DE thứ
  hai vì giữ **2 bút** và có **4 món** từ mình (nhưng 3/4 có đáp án bị **cưỡng chế bởi dữ kiện**, nên thực
  chất là *một đồng ý + ba xác nhận*); SWE thứ ba với ask 60 giây (D5 của anh ấy là 2 ngày im lặng — ask
  nặng là cách mua lại sự im lặng đó); mentor cuối vì ông là **approver, không phải người đàm phán**.
- **Expected artifact** — comment trên #81, #80, #82, #83 với nguyên văn §3.
- **DoD** — mỗi câu có: đề xuất của mình · đánh đổi nói thẳng · **cái mình cho lại** · và (với món hoãn
  được) mặc định sẽ áp lúc 17:00.

## T5 · Ký 3 hợp đồng của người khác TRƯỚC

- **Objective** — có đi có lại; và luật S2: review **không có finding thì không được tính**.
- **Reasoning** — ký trước không tốn gì và biến ask của mình từ "làm giúp tôi" thành "đáp lại". Ba finding
  đã có sẵn, không phải đi tìm: `trace-event.v0.md:44` còn `tenant: str` sau khi D-13 đổi thành
  `tenant_id: UUID` (và §7 của doc đó còn khai *"v0 chỉ THIẾU, không MÂU THUẪN"* — câu đó hết đúng từ
  D-13) ⇒ người đọc mới sẽ wire `tenant` và fail validation · `ts` hai test ngược nhau (`engine:113` strict
  vs `kb:98` cho phép trùng) ⇒ carry #9 của mentor · `test_lint_rejects_bad_graph:74` còn
  `xfail(strict=False)` ⇒ cùng lớp lỗi sẽ XPASS im lặng ngày `graph_lint()` xong.
- **Expected artifact** — 3 review có finding + `sig-dholmes0207.md`.
- **DoD** — mỗi review nêu **một defect cụ thể hoặc một test đề xuất** (không phải nhận xét chung) · nhãn
  khớp thân review · không tự vá hộ quadrant người khác.

## T6 · PR-B — evalhub docs + test

- **Objective** — hợp đồng freeze + pin F02 + đổi neo xfail, **không đụng hành vi**.
- **Reasoning** — hai lý do khiến PR này docs+tests-only: (1) ngày ceremony, và bài học D10 của chính mình
  — *"vá `score_case` vài giờ trước demo là đánh cược vào đúng thứ đang được chấm"*; (2) nó làm PR-A/PR-B
  giao hoán được (T3). Vì sao **file mới** `scorecard.v1.md` thay vì `git mv`: dòng 3-8 của `scorecard-v0.md`
  là log suy luận D2→D7 của mình (gồm entry D7 nơi AIE-1 bắt được doc mâu thuẫn `main`) — vết đó là bằng
  chứng, và một tài liệu đã freeze không được mang chữ *"chưa freeze"* trong header lịch sử của nó.
- **Evidence** — GUIDE-C §6.4.2 đòi pin nhánh từ-chối; §9 ghi pin đó **chưa tồn tại** · App. B.3.
- **Expected artifact** — `scorecard.v1.md` (frontmatter khuôn DE `kb-search.v0.md:1-11`, `status:
  v1-frozen`, `freeze: FROZEN`, `freeze_date`, `signatures:`) · `scorecard-v0.md`: sửa header stale `:3` +
  banner `SUPERSEDED BY` + §3 Q1–Q5 chuyển thành **đáp án có id DEC, giữ nguyên câu hỏi gốc** · template
  mini-RFC + 1 bản điền thật (chọn món per-chunk `tenant_id`, chủ DE, S3) · `DESCOPE.md` dòng judge ·
  pin F02 · đổi neo xfail · `## Sổ chốt` append-only cuối `scorecard.v1.md` (khuôn `kb/docs/format.md:299`).
- **DoD** — `pytest packages/evalhub` = `42–43 passed`, **đúng 2 xfailed, 0 xpassed** · 3 số bảng điểm
  **không đổi** · `git diff --stat -- packages/evalhub/src` **rỗng** · `ruff format --check` sạch trên file
  của mình.

## T7 · PR-C — decision-log + hồ sơ freeze + chữ ký + design-note

- **Objective** — 4 dòng DoD có artifact, nằm ở **kit root** nên thấy được **không cần bump con trỏ**.
- **Reasoning** — luật quyết định chỗ nộp: *"I clone your repo fresh"* + *"closing an issue whose artifact I
  cannot find in a fresh clone counts against you"*. Issue comment và PR body **không có trong clone** ⇒
  chỉ dùng cho đàm phán và mốc thời gian, **không bao giờ** làm artifact DoD. File trong submodule chỉ
  thấy được **nếu con trỏ đã bump** — đúng cái đã làm pack GATE-1 của DE vô hình. Nên decision-log +
  design-note ở **kit**, không ở evalhub. Tên file đặt trùng chữ trong DoD (`decision-log`) để
  `grep -ri decision-log` của người đọc mới tìm ra.
  **Cơ chế chữ ký — vì sao 4 file thay vì 1 bảng:** một bảng do mình gõ hộ 4 người thì
  `git log --format='%an'` ra `dholmes0207` cả 4 dòng ⇒ **chữ ký mà tác giả là người thu gom thì không phải
  chữ ký**. Bốn người cùng sửa một bảng thì xung đột dòng kề nhau đúng ngày ma sát cao nhất. Một file/người
  ⇒ 0 xung đột, `git log` chứng minh từng người. Và mỗi chữ ký ghi `contracts@<sha>` vì **chữ ký không nêu
  bytes nó ký thì là trang trí** — có SHA thì một commit sau đó không thể tự nhận là đã được ký.
- **Evidence** — App. A.4 (không có tiền lệ) · A.5 (quyền merge kit = Dat).
- **Expected artifact** — `docs/decision-log.md` (append-only; cột `id · ngày · quyết định · chủ · contract
  chạm · bump? · chữ ký`) · `docs/decisions/s1-contract-freeze/README.md` (hồ sơ + agenda + index chữ ký +
  **lệnh verify để người khác tự chạy**) · `sig-<github-id>.md` ×4 (mình ký thật; 3 file điền sẵn trừ dòng
  của họ) · `docs/design-notes/aie-2-dholmes0207.md`.
- **DoD** — mỗi sig có `contracts@<sha>` · README chứa
  `git log --format='%ad %an %H' -- docs/decisions/s1-contract-freeze/sig-*.md` và
  `ls .../sig-*.md | wc -l   # cần = 4` · 3 file điền sẵn ≤60 giây/người · báo cáo **1/4 với 3 người kia
  đã unblock**, **không bao giờ** báo 4/4.

## T8 · Design-note ≤2 trang

- **Objective** — dòng DoD duy nhất không ai chặn hay mở hộ được.
- **Reasoning** — #83 khoanh đúng 4 chủ đề: eval harness v1 · golden-set · judge cap ≤100/cache · descope
  exact-match. Neo là GUIDE-C §4.1 (gate = AND, `>=`, tầng aggregate), **không suy lại**. **Phương án bỏ
  bắt buộc** và phải là phương án mạnh nhất có thật, không phải bù nhìn: *"implement `compute_scorecard`
  hôm nay để đóng `O3.1` (+1.91, ô nặng nhất) — BỎ, vì GUIDE-C §3.2 đòi ngưỡng literal phải **có trước**
  dataset, mà dataset về D14-15; land hôm nay thì 4 ô 'exactly-at' thành `unknown`, tức tự phá 4 ô đắt
  nhất trong grid của mình."* Thêm một phương án bỏ thứ hai nếu còn chỗ: *"`citation_accuracy` gate
  per-case `success`"* — bỏ vì nó đếm hai lần mọi lỗi citation, và vì register của mentor **từng chỉ thị
  rồi thu hồi** (GUIDE-C §4.1/CP-2.1) ⇒ nêu nó chứng minh mình đọc phần thu hồi, không đọc phần chỉ thị.
- **Evidence** — App. B.1 (D-19/M1) · GUIDE-C §3.2 (luật ngưỡng-trước-dataset) · #83 (4 chủ đề).
- **Expected artifact** — 5 mục: scope (kèm **non-scope**: không wiring publish/rollback = S3/D24, không
  dashboard = D25) · phương án chọn · **1 phương án bỏ** · trade-off (token-contains vs exact-match, chiều
  lệch **xuống** không lệch lên; leak sanity mức slug vs fence UUID) · rủi ro (M5 chưa có nguồn nhãn tay ⇒
  mọi ô judge là `todo:` không có ETA cam kết được; ngưỡng đang pin vào `ExtractiveFakeLLM` ⇒ S2 phải
  recalibrate; golden-30 về sau corpus D13).
- **DoD** — ≤2 trang · có mục phương án bỏ · nộp kèm **câu hỏi SLA duyệt** (DoD ghi *approved*, không phải
  *submitted*) · nếu chưa duyệt thì ghi `ĐÃ NỘP <path>@<sha> <giờ> · Duyệt: CHỜ` và **không tick ô**.

## T9 · Gieo 5 mutation vào `packages/engine`

- **Objective** — biến *"tôi tin phân biệt retrieved/grounded là tình cờ"* thành *"đây là lượt chạy nó
  vỡ"*; 3/5 mutation verify đúng clause đang xin freeze.
- **Reasoning** — chọn engine, không chọn kb hay workbench, vì bốn lý do theo thứ tự trọng số: (1) carry #7
  ghi rõ engine **chưa có sweep tự động** (6 mutation gieo tay, so với 93-mutant sweep của DE mà mentor gọi
  là chuẩn) ⇒ yield thông tin/mutation cao nhất; (2) engine sản xuất **mọi** tín hiệu bộ chấm tiêu thụ
  (carrier · `refused` · thứ tự `ts` · `tenant_id` mỗi event · `outputs["chunks"]`) ⇒ đây là cách duy nhất
  chuyển một niềm tin thành một phép đo; (3) mỗi mutation map 1:1 với một clause đang xin freeze, nên bài
  tập **chính là bước verify** của freeze chứ không phải việc phụ — bắt được là bằng chứng **cho** cách
  viết clause, không bắt được là một test chủ quadrant phải viết hôm nay, **cả hai kết cục đều đẩy freeze
  đi**; (4) không chọn DE vì anh ấy là bottleneck hôm nay và test của anh ấy mạnh nhất ⇒ thêm tải lên
  bottleneck để lấy yield thấp nhất là trade sai; không chọn SWE vì bề mặt mỏng và cùng ngày mình đã đưa
  anh ấy một finding — gieo thêm đọc thành dồn ép.
  Dùng **phương pháp khai-trước của DE** (nêu mutation *và* test phải đỏ **trước khi** chạy): mentor gọi
  đó là instrument tốt nhất nhóm và nó từng bắt hai bug **trong chính tooling của DE**; áp dụng lại chính
  là *"cơ chế biến một người học được thành codebase phản ánh điều đó"* mà #74 §3.2 nói nhóm đang thiếu.
  Kế thừa luôn hai bẫy DE đã trả giá: pytest phát ANSI dù stdout là pipe (regex `FAILED` khớp rỗng) và
  `.pyc` khoá theo `(mtime giây, size)` nên mutant 1 ký tự viết trong cùng giây load bytecode cũ.
- **Evidence** — bảng 5 mutation: **App. C**.
- **Expected artifact** — `kit:docs/mutations/s2/dholmes0207-into-engine.md` (cột *declared* vs *actual* —
  chỗ hai cột lệch nhau chính là finding) + mục để AIE-1 tự append `## Phản hồi của chủ quadrant` bằng
  commit của chính anh ấy ⇒ **một artifact, hai tác giả chứng minh được** (mentor: *"Both of you write
  down what happened"*) + thông báo trên #81 **trước khi** gieo.
- **DoD** — **chỉ assertion ngữ nghĩa tính là bắt được** (`ImportError`/collection error = **không** bắt,
  đúng như mentor nhấn ở 5 mutation của ông) · **không push mutation** (worktree local, `git checkout --`
  sau mỗi lượt) · `git status --short` rỗng sau T9 · ≥1 dòng có *declared ≠ actual*.

## T10 · Đóng bàn giao 16:30 + bump con trỏ

- **Objective** — "mười mét cuối". Làm 16:30 thay vì 18:00 chính là bản vá của S1.
- **Reasoning** — lệch con trỏ đã mất điểm **hai lần** (`kit#73` · `kit#76`/`#77`), và cả hai lần đều là
  cùng lớp lỗi: việc đã merge ở repo con **không tự tồn tại** ở cây mà gate chạy. Nên bump là **phần của
  deliverable, không phải việc dọn**, và verify phải bằng **clone sạch**, không bằng working tree — working
  tree luôn "thấy" thứ người clone không thấy. `GITFLOWS.md:52-53` cho phép gộp bump, và gộp **an toàn chỉ
  vì** mọi dòng mới đều optional (T3).
- **Evidence** — App. A.5 (quyền merge kit) · App. D.5 (lệnh clone sạch).
- **Expected artifact** — merge A→B→C theo thứ tự · PR-E bump `packages/evalhub` + `docs/reports`.
- **DoD** — clone sạch thấy đủ 8 deliverable · `git submodule status` dán vào note · kit CI 10/10 ·
  **không push thêm vào nhánh nào sau khi đã có approval** (`evalhub#5` mất approval vì push muộn) · mở
  issue follow-up cho job CI so con trỏ kit với `main` từng submodule (**không** làm hôm nay).

## T11 · Note D11 + đóng ngày

- **Objective** — note có **số + chẩn đoán** (luật S2: thiếu một trong hai thì không được tính).
- **Reasoning** — heading giữ nguyên template vì đó là section-map máy đọc (`daily-note.md:3-5`). Mục
  `## Contract / integration` phải trả đúng ba câu template hỏi: đổi gì · **ai ký** · vỡ hay mở được gì.
  Self-assessment vào repo report **chỉ chữ + lý do**: report-CI quét *shape* rò rỉ rubric, và dry-run cho
  thấy bảng `| A1.1 | A | lý do |` → 0 match nhưng `weight: 0.10` / `kappa: +0.8` → 2 match ⇒ build fail
  (App. A.11). Mọi số học rubric phải nằm ở kit.
- **Evidence** — App. E (danh sách số bắt buộc + bản nháp 12 dòng self-assessment).
- **Expected artifact** — `docs/reports/daily-notes/2026-08-03-dholmes0207.md`.
- **DoD** — mỗi số kèm một câu "nên sao" · `## Contract / integration` trả đủ 3 câu · **chỉ chữ + lý do**
  trong repo report · tick **chỉ** ô chứng minh được trên #83 · comment trạng thái cuối lên #84.

---

# §3 — Nguyên văn 14 ask

## AIE-1 — @TranBaDat2607 (#81) · gatekeeper contracts + chủ hành vi engine

Đóng khung anh ấy là **gatekeeper + chủ hành vi**, không bao giờ là người giữ bút (anh ấy không giữ bút nào).

**A1-1 · Carrier `citations`** — *Owner: AIE-1 · Required response: yes/no + phương án · **Non-blocking***

> **Quyết định:** trong 1 run, **chỉ event `node_type == llm-step` được mang `citations`**; mọi node khác
> `citations = None`. Chunk **đã truy xuất** nằm ở `outputs["chunks"]` của event `kb-retrieve`, không ở
> `citations`.
> **Đề xuất: YES, và anh không phải viết gì mới** — test của anh đã khoá đúng câu này:
> `engine/tests/test_trace_event_emission.py:152 test_non_llm_events_have_zero_tokens_and_no_citations`
> assert `event.citations is None` cho mọi event ≠ `n_llm`. Tôi chỉ xin **trích câu đó thành clause** trong
> bản freeze trace-event, để một refactor xoá test không lặng lẽ đổi nghĩa `citation_accuracy` của tôi.
> **Đánh đổi:** clause khoá anh lại — sau freeze, muốn cho `kb-retrieve` cũng mang `citations` thì cần
> mini-RFC + 4/4 chữ ký. Nếu anh thấy có khả năng cần (vd S3 muốn trace cả retrieved lẫn grounded trên
> cùng field) thì nói **NO** bây giờ, và tôi siết helper theo `node_type` **phía tôi** thay vì khoá phía
> anh. Cả hai đường đều đóng được lỗ; chỉ khác ai trả giá khi đổi ý.

Vì sao cần clause: `citations_from_trace` gom **node-agnostic** (`harness.py:85-89`), nên nó phân biệt
retrieved/grounded **chỉ vì engine hôm nay tình cờ hành xử vậy** (`interpreter.py:265-271` rẽ theo
`isinstance(output, list)`). Rủi ro dư phải nói ra: bất kỳ node trả **dict** mà dict đó có key
`"citations"` sẽ mang citations vào trace — `condition`/`tool-call` đều trả dict. Tức bảo đảm hiện tại là
**hành vi**, không phải **cấu trúc** — đúng lý do nó cần thành clause.

**A1-2 · `refused`: freeze seam, không freeze công thức** — *Owner: AIE-1 · Required: yes/no · **Non-blocking***

> **Quyết định:** hợp đồng **KHÔNG** freeze công thức `refused`. Nó freeze rằng output `llm-step` có key
> `refused: bool` mang nghĩa *"agent không ground được câu trả lời từ thứ được đưa"*, và rằng **đổi công
> thức phải báo trên #84 cùng ngày** (không cần mini-RFC).
> **Đề xuất: YES.** `refused` đã đổi nghĩa **hai lần trong 4 ngày** (`not retrieved_chunks` → sentinel →
> `not citations`, `executors.py:264`). Freeze công thức là freeze một thứ đang tiến hoá đúng hướng. Freeze
> **seam + nghĩa** cho tôi cái tôi cần (một cờ structural, không phải đoán text) mà không khoá anh.
> **Đánh đổi:** đổi lần thứ ba mà không báo thì `SC-04`/`SC-07`/`SC-09` lật im lặng. Tôi nhận rủi ro đó và
> đã dựng lưới: test A4 của adapter chạy `interpreter.run` lấy quyết định gốc rồi so với `AgentAnswer` đã
> map — nó khoá *"adapter map trung thực"*, không khoá *"engine quyết bằng công thức nào"*.
> **Đi kèm — breakpoint #14 vẫn mở, và nó là XANH-GIẢ chứ không phải đỏ-giả:** `refused = not citations`
> cho dương-tính-giả — câu bịa trọn vẹn *"Hạn mức chi của Borea là 500 triệu"* mà quên đóng ngoặc ⇒
> `citations=[]` ⇒ `refused=True` ⇒ **SC-04 PASS dù agent đã bịa**. Trên bài kiểm hàng rào, xanh-giả nguy
> hiểm hơn đỏ-giả. **Tôi không xin anh làm hôm nay** — tôi xin nó có **chủ + hạn** trong decision-log
> (đề xuất: AIE-1, D17, cùng leak-test).

**Cho lại AIE-1 (anh ấy chưa hỏi):**
- **`ScorecardThreshold` sống sót.** Anh ấy import nó ở **8 file** (7 test engine + `studio_engine/__main__.py:22`).
  Tôi đang **công khai phản đối hợp nhất** (SWE-1) — nói cho anh ấy biết, vì một lần rename sẽ đỏ 8 file của anh.
- **Clause `ts` (DE-2) làm test strict của anh ấy ĐÚNG** thay vì quá chặt ⇒ giữ nguyên
  `interpreter.py:284-287` + `test_event_timestamps_strictly_increase`.
- **5 mutation vào engine với bản ghi khai-trước** — carry #7 là *"no automated mutation sweep for
  `packages/engine` — Dat"*; sweep của tôi là **trả trước** cho món của anh ấy, ghi công là bằng chứng
  coverage của anh ấy.

## DE — @DongAnh2704 (#80) · hai bút, bốn món, **một** cần đồng ý thật

**DE-1 · `outputs["chunks"]` thành invariant có tên** — *Owner: DE · Required: yes/no · **Non-blocking***

> **Quyết định:** với event `node_type == kb-retrieve`, `outputs` **PHẢI** là
> `{"chunks": [<KbSearchResultItem đã model_dump(mode="json")>, …]}` — mỗi phần tử mang đủ `chunk_id ·
> text · score · tenant_id (UUID) · section_role`. Với 5 node còn lại, `outputs` giữ nguyên
> `dict[str, object]` tự do.
> **Đề xuất: YES — và đây KHÔNG phải đổi contract.** `TraceEvent.outputs` vẫn là `dict[str, object]`;
> `SCHEMA_VERSION` **không bump**; **không cần mini-RFC, không cần 4/4 chữ ký**. Engine đã emit đúng shape
> này từ D5 (`interpreter.py:265-268`) và **4 chỗ đang đọc nó** (`scripts/smoke_eval_d6.py:247,270` — file
> của anh; `apps/studio/scripts/e2e_smoke_eval.py:265-271`; `packages/kb/tests/test_spine_live.py:135`).
> Việc duy nhất cần làm: **`trace-event.v0.md:77` đang ghi `outputs` là "⏸ hoãn S2"** — tức field đang chở
> bằng chứng của tôi thì hợp đồng khai là chưa quy định.
> **Vì sao tôi cần:** đây là thứ biến leak-check của tôi từ **sanity theo slug** thành **chứng minh mức
> UUID**. Hôm nay `_citation_tenant` cắt tiền tố chuỗi `chunk_id` (`harness.py:49-57`) — nhãn mềm, trùng
> được, sửa được. Với `outputs["chunks"][].tenant_id` tôi so UUID thẳng.
> **Tôi sửa lại chính ghi chú của mình:** `scorecard-v0.md:335-337` viết *"muốn kiểm leak mức UUID thì
> trace cần `tenant_id` per-chunk → đổi contract → mini-RFC + 4/4 chữ ký"*. **Câu đó định giá quá cao và
> tôi rút.** Dữ liệu đã có; thiếu là một dòng hợp đồng.
> **Đánh đổi:** clause khoá `outputs["chunks"]` thành bề mặt công khai — sau freeze, đổi key `"chunks"`
> hoặc bỏ field trong item là breaking. Nếu anh muốn giữ `outputs` hoàn toàn tự do thì nói **NO**, và tôi
> giữ leak-check ở mức slug + ghi vào decision-log rằng leakage=0 ở D22 sẽ chỉ chứng minh được tới mức nhãn.

**DE-2 · `ts`: chẻ producer ↔ reader** — *Owner: DE · Required: yes/no · **Non-blocking***

> **Quyết định — freeze bằng hai câu, không phải một:**
> (a) **Producer:** mọi emitter PHẢI phát `ts` **tăng nghiêm ngặt** trong cùng một `run_id`.
> (b) **Reader:** reader **KHÔNG được** dựa vào tính phân biệt của `ts`; PHẢI parse ra `datetime` rồi sắp
> theo `(ts, event_id)`, và **KHÔNG** assert tăng nghiêm ngặt.
> **Đề xuất: YES.** Đây là carry item #9 của mentor (*"Duplicate `ts`, two tests encode opposite
> assumptions"*), và tôi có file:line cho cả hai vế: engine `test_trace_event_emission.py:113-118` assert
> `len(set(timestamps)) == 4` (nghiêm ngặt, có clamp `interpreter.py:284-287` đỡ); reader của anh
> `packages/kb/tests/test_trace_reader.py:98-106` assert **ngược lại có chủ đích**. Thêm chỗ thứ ba dùng
> strict `<`: `apps/studio/scripts/e2e_smoke_eval.py:276`.
> **Điểm quan trọng: hai bên đều đang ĐÚNG về tầng của mình.** Chẻ producer/reader làm **cả hai test hợp
> lệ, không ai phải sửa dòng nào**, và chữ *"monotonic"* ở umbrella §3.2 — vốn đọc được hai kiểu — có nghĩa
> duy nhất. Nếu anh muốn một câu duy nhất thì nói **NO** và ta chọn một vế; nhưng lúc đó một trong hai test
> đang xanh phải chết, và tôi nghĩ đó là cái giá không cần trả.

**DE-3 · Q5 nguồn sự thật golden-set** — *Owner: DE · Required: yes/no · **Non-blocking***

> **Quyết định:** `eval.golden_sets` (`evalhub/schema.py:20-25`, bút tôi) là **nguồn sự thật**. DE **sinh
> + gán nhãn** case và giao qua file YAML trong `packages/kb/golden/`; AIE-2 **nạp** vào `eval.golden_sets`.
> `obs.golden_sets` bỏ (hoặc để nguyên như shell chết, có ghi chú).
> **Đề xuất: YES — và lý do là quyền, không phải sở thích.** Q-D trong `trace-event.v0.md:242` của chính
> anh: *"`obs.golden_sets` nằm trong `apps/studio/` — không phải fence-lane của DE. DE điền bằng cách
> nào?"* Câu trả lời là: **không điền được.** Tôi thì viết được `schema.py` của mình. Chọn `eval.golden_sets`
> là chọn cái bảng **có người ghi được**.
> **Đánh đổi:** ranh giới sở hữu dịch — anh sở hữu **giá trị** (case + nhãn tay + tên bộ), tôi sở hữu **nơi
> lưu + loader**. Đó đúng phân vai đã dùng ở §2.6: *"DE sở hữu giá trị `expected`; AIE-2 sở hữu luật khớp"*.
> **Đi kèm:** loader YAML→DB hết blocker — `pyyaml>=6.0` đã khai tường minh ở `pyproject.toml:26` từ
> `kit#65`. Trước đó mọi `import yaml` **ăn ké extra của `uvicorn[standard]`**; ai đổi thành `uvicorn` trần
> là loader chết im lặng. Đã đóng.

**DE-4 · Golden-30 phải có NGÀY** — *Owner: DE · Required: **một ngày cụ thể** · Non-blocking hôm nay,
**blocking D16***

> **Quyết định:** DE giao **30 case có nhãn tay**, muộn nhất **hết ngày D15 (07/08)**, tên bộ
> **`callisto-golden-30-v1`**, sinh **SAU** corpus KB thật (D13). Thành phần: phủ 2 tenant · có case refusal
> cả T1 (chéo-tenant) lẫn T6 (chéo-vai cùng tenant) · `section_roles` đa dạng · `expected` là **cụm ngắn
> sạch** (không space-pad, luật token §2.6) · `expected_citation` chép từ `chunk_id` thật · **≥3 case cần
> judge** (D18 cần đất).
> **Đề xuất: YES với mốc D15.** #108 (D16) là *"eval harness v1 + golden 30"* của tôi. Không có mốc thì
> D16 chạy mù, và tôi **không** dựng thay bộ của anh — umbrella §6 ghi golden-set *"sinh từ doc-factory DE"*.
> **Đánh đổi:** D15 là Integration Friday (#104) và anh còn trace viewer ở đó. Nếu D15 quá chặt, tôi nhận
> **20 case ở D15 + 10 case sáng D16**, miễn là **chia lô có trong decision-log**. Cái tôi không nhận được
> là "sẽ có".
> ⚠️ **Rủi ro tôi nêu trước:** corpus-cutover D13 gần chắc làm `smoke-5`/`smoke-10` hiện tại vỡ. Sáng D13
> tôi hỏi lịch cutover, chiều re-run và báo lệch — không phải để bắt lỗi anh, mà để con số ở D16 không bị
> đọc là hồi quy của tôi.

**Cho lại DE:**
- **Trả lời Q-C của anh ấy, mở từ 21/07** (`trace-event.v0.md:239`), nguyên văn để dán vào §3 của anh:
  > **Q-C — eval harness đọc field nào từ trace, đủ và chốt:** `citations` (chỉ trên `llm-step` —
  > grounded, mẫu số của `citation_accuracy`) · **`outputs["chunks"]` trên `kb-retrieve`** (retrieved, và
  > là chỗ duy nhất có `tenant_id` UUID per-chunk ⇒ leak proof mức UUID) · `tenant_id` mỗi event
  > (`tenant_scope_ok`, nhất quán mức run) · `node_type` (để phân biệt hai nguồn trên) · `run_id` (gom 1
  > run) · `ts` (sắp timeline). **`cost` + `tokens` tôi chỉ báo cáo, không chấm.** Hết — không có field
  > thứ bảy.
- **Finding `trace-event.v0.md:44`**, nói dạng phát hiện không phải mắng: doc §2 còn khai `tenant: str` sau
  khi D-13 đổi thành `tenant_id: UUID`; §7 còn ghi *"v0 chỉ THIẾU, không MÂU THUẪN"* — câu đó hết đúng từ
  D-13. Freeze một doc mà §2 mâu thuẫn `trace.py:30` nghĩa là người đọc mới wire `tenant` rồi fail validation.
- **Đồng-chủ đóng breakpoint #12:** `callisto-smoke-5-v0` còn trong 4 file; **tôi nhận nửa `evalhub`** hôm nay.

## SWE — @Dozyboy (#82) · một cam kết **âm** + một món quà

**SWE-1 · Giữ hai class threshold, KHÔNG hợp nhất** — *Owner: SWE · Required: yes (im lặng = giữ nguyên =
đúng ý) · **Non-blocking***

> **Quyết định:** giữ **hai** class có field giống nhau — `Recipe.scorecard_threshold: ScorecardThreshold`
> (bút anh) và `Gate.threshold: GateThreshold` (bút tôi). **Không hợp nhất.** Thay vào đó freeze một
> **invariant**: `Scorecard.gate.threshold` PHẢI bằng từng field với `Recipe.scorecard_threshold` của
> recipe đang được eval.
> **Đề xuất: YES, và anh không phải làm gì cả.** Hợp nhất hôm nay là **breaking** cho bên bị xoá tên:
> `ScorecardThreshold` đang import ở **8 file**, `GateThreshold` ở 2. Lợi ích ròng hôm nay = **0**, vì
> `compute_scorecard` nhận **hai float**, không nhận object (`compute.py:19-25`), nên không chỗ nào phải convert.
> **Cái thật sự quan trọng là invariant, không phải class:** một scorecard gate theo ngưỡng **khác** ngưỡng
> recipe khai mới là bug. **Test đó tôi viết, trong quadrant tôi, hôm nay.** Anh chỉ cần: đừng rename/remove
> `ScorecardThreshold` trong bản freeze recipe.
> **Đánh đổi:** hai class trùng field trông dư. Giá của dư = 0 file phải sửa; giá của gọn = 10 file + một
> bump `SCHEMA_VERSION`.

**SWE-2 · `golden_set_ref` + ngưỡng: freeze field, không freeze số** — *Owner: SWE · Required: yes/no ·
**Non-blocking***

> **Quyết định:** freeze `golden_set_ref: str` + `scorecard_threshold: {success, citation_accuracy}` **là
> field**. **Giá trị mặc định KHÔNG thuộc hợp đồng** — nó là dữ liệu recipe, và được **hiệu chỉnh lại ở
> D16** sau khi golden-30 chạy trên corpus thật; chủ: AIE-2; ghi vào decision-log.
> **Đề xuất: YES, và đây là một con số cụ thể, không phải nguyên tắc.** `builder.py:48-49` mặc định
> `success=0.9, citation_accuracy=0.95`. Số đo thật của tôi trên fixture: bộ 5 → `success 4/5 = 0.80`; bộ
> 10 → `success 6/10 = 0.60`, `citation_accuracy` thật `0.833`. **Với mặc định của anh, recipe TỐT cũng
> FAIL cả hai trục.** Tức demo bước 7 (*"sửa instructions tệ → verdict FAIL → chặn publish"*) chứng minh
> **số không**, vì bản tốt cũng đỏ. Cần một baseline PASS mới có cái để lật.
> **Đánh đổi:** hạ mặc định bây giờ là hiệu chỉnh theo `ExtractiveFakeLLM` — mentor đã cảnh báo đúng chỗ
> này (*"every threshold you have pinned is calibrated against a stand-in"*). Nên tôi **không** xin anh
> đổi số hôm nay. Tôi xin freeze ghi rõ: **số là dữ liệu, có chủ (AIE-2), có hạn (D16)**. Anh giữ 0.9/0.95
> trong builder tới đó.
> **Cộng thêm — hoà giải 3 tên bộ case, vì nó chảy qua field của anh:** `golden-set-eval-1` (test mentor
> `test_eval_gate.py:54`) · `callisto-smoke-5-v0` (`builder.py:47,191,205`) · `callisto-smoke-10-v0` (bộ 10
> thực dùng). Đề xuất: **`callisto-golden-30-v1`** từ D16; chủ đổi: AIE-2 cho `evalhub/cli.py`, SWE cho
> `builder.py`; hạn D16.

**Cho lại SWE:**
- **Tôi viết test cross-contract** (`Gate.threshold == Recipe.scorecard_threshold`, từng field) trong
  `packages/evalhub/tests/`. #117 (D18) của anh ấy là *"`scorecard_threshold` đọc được cả nhánh judge lẫn
  exact-match — không vỡ"* ⇒ test của tôi là **bằng chứng D18 của anh ấy, giao ở D11**.
- **`gate.verdict` xác nhận freeze nguyên trạng**: `Literal["PASS","FAIL"]`, `Gate{threshold, verdict}` ⇒
  wiring publish/rollback ở D24 dựng được ngay hôm nay, không sợ tôi dịch shape.
- **Finding, đóng gói không nhắc D5:** `test_lint_rejects_bad_graph:74` còn `xfail(strict=False)` (bài kế
  bên đã vá đúng ở `kit#50`) ⇒ cùng lớp lỗi sẽ XPASS im lặng ngày `graph_lint()` xong. Đưa **bản vá 2
  dòng tôi đã dùng ở evalhub D9** kèm lập luận từ `test_eval_gate.py:8-27`, khung *"cùng một lớp lỗi, đây
  là bản vá tôi đã dùng"* — **không tự vá hộ**, vì đó là carry item của anh ấy và chạm vào là phá bằng chứng.

## Mentor — @hieubui2409 (#83) · approver, không phải người đàm phán

Ba câu + một, mỗi câu kèm **"nếu không trả lời thì tôi làm gì"**.

**M-1 · DEC-01** — *Required: 1 chữ · Non-blocking*
> `contracts/__init__.py:5-12` khai kỷ luật: *"new OPTIONAL fields may be added without a bump;
> renames/removals/**required-additions** are breaking"*. `judge` **required → optional** không nằm trong
> ba loại đó, và nó là **ca thứ tư** có tính chất riêng: **tương thích trên dây, KHÔNG tương thích với
> reader**. Payload cũ vẫn validate; consumer giả định non-null thì vỡ. `test_freeze_guard.py` chỉ đo chiều
> dây, nên cơ chế hiện có **không phát hiện** ca này. → Đây là **lỗ trong quy tắc, không phải lỗ trong
> code**.
> **Nếu không trả lời:** áp cách đọc hẹp (không bump), ghi vào log là "chờ xác nhận". `SmokeResult` tiếp
> tục là kiểu nội bộ quadrant tới khi chốt, và **D16 không chết vì câu này**.

**M-2 · Q4 Protocol seam** — *Required: yes/no · Non-blocking*
> `.importlinter` cấm `studio_evalhub` import `studio_engine`/`studio_kb`; `protocols.py` có 3 seam
> (`EmbeddingService`/`LLM`/`TraceWriter`), không có seam cho interpreter hay golden-set repo.
> **Đề xuất: KHÔNG đưa lên contracts hôm nay.** Ba lý do: (a) contracts là layer đáy — thêm seam thứ 4/5 là
> mở rộng bề mặt freeze **đúng ngày đóng băng nó**; (b) `AgentRunner` đang chạy tốt như kiểu riêng quadrant;
> (c) adapter `EngineAgentRunner` sống ở composition root `apps/studio` — chỗ **duy nhất** chạm AIE-1 đã có
> và đã chạy. **Phương án bỏ:** đưa lên contracts ⇒ 4/4 chữ ký cho **mỗi** lần đổi shape seam, trong lúc
> seam còn tiến hoá qua D14/D16.
> **Nếu không trả lời:** giữ nội bộ. Không chặn gì.

**M-3 · Phạm vi verdict + cơ chế + chủ INV-1** — *Required: xác nhận 1 câu + 1 tên · Non-blocking*
> (a) `test_gate_blocks_on_fail` là `xfail(strict=True)`. Hiểu của tôi: **seam điền ở D16** (verdict trên
> giấy — #108), **wiring CHẶN+rollback vào publish ở D24** (SWE). Xin xác nhận một câu, vì `strict=True`
> nghĩa là ngày seam xong bài đó XPASS ⇒ FAIL ⇒ buộc gỡ marker; tôi muốn gỡ **đúng ngày**, không sớm không muộn.
> (b) `week-2/days/day-11.md` chưa publish (404) nên DoD 4 dòng là spec duy nhất, và *"4/4 chữ ký"* không
> có cơ chế nào định nghĩa trong repo. Tôi đề xuất một cơ chế ở #84 và **sẽ chạy theo nếu không có phản
> đối** — nói trước để nếu anh có format riêng thì tôi đổi, chứ không phải để xin phép.
> (c) **INV-1 roles-axis** (#74 §6: *"needs an owner at D11 freeze. AIE-1 or SWE"*) — tôi **không** nhận
> trục này: bộ chấm **quan sát** hàng rào, không **tạo** hàng rào. Nhưng nó phải có chủ hôm nay. Đề xuất
> **SWE**, vì #112 (D17) đã gán *"Own INV-1: session_id resolve {tenant,user,roles} server-side"* cho anh
> ấy, và lỗ nằm ở chỗ recipe tự khai roles (`executors.py:138` đọc `node.params.get("section_roles")`) —
> recipe là bút SWE.
> (d) **Design-note: SLA duyệt trong ngày, hay có vòng sửa?** DoD ghi *"approved"*, comment #74 ghi
> *"approved 1:1"*.
> **Nếu không trả lời:** ghi `ĐÃ NỘP <path>@<sha> <giờ> · Duyệt: CHỜ` và **không tick** ô "4/4 design-note
> approved" — ô đó là hành động của approver, không phải của tôi. INV-1 ghi là **CHƯA CÓ CHỦ + đề xuất +
> hạn gán D12**: một món ghi là vô-chủ-có-hạn là **finding**; một món bị bỏ im lặng là **thất bại**.

---

# §4 — Hoãn: chủ + hạn + vì sao hoãn được

| Món | Chủ | Hạn | Vì sao hoãn được / điều kiện mở |
|---|---|---|---|
| Q5 giao YAML golden-set | DE | corpus D13 · bộ D15 | Dòng đầu `EvalHarness.run` cần, mà D16 mới viết dòng đó. **Escalate nếu hết ngày không có hạn** — thiếu hạn thì D16 mù |
| Q4 Protocol seam lên contracts | mình + AIE-1 | D14 | `agent_runner.py` đã có Protocol nội bộ chạy tốt ⇒ D16 dựng được không cần promote. Sau freeze là mini-RFC ⇒ **món đầu tiên chuyển thành mini-RFC viết sẵn hôm nay** |
| Q3 `section_roles` resolve ở đâu | SWE (mentor đã gán D-21) + DE | D17 | Chữ trong doc của mình đã đúng (`golden_case.py:110-116`); code là của họ |
| per-chunk `tenant_id` cho leak UUID | DE (một dòng clause) | D15 | Dữ liệu **đã có** từ D5 (App. A.7) ⇒ chỉ cần clause. Đây là ca dùng để **điền template mini-RFC đầu tiên** |
| `match_mode` (`exact`/`judge`) trên `GoldenCase` | mình + DE | D16 | `GoldenCase` là kiểu nội bộ quadrant (`golden_case.py:8`), **không bao giờ** cần mini-RFC. Quyết bây giờ rằng nó thành field **optional** khi bộ 30 về |
| Nguồn nhãn tay cho `agreement` (M5) | **mentor** | D18 | Chặn mọi ô judge. Field đích đã có (`scorecard.py:19`), field nguồn **không tồn tại**, hằng số bị cấm ⇒ nêu là blocking, **không tự đặt đáp án** |
| Dọn alias `_retrieved_citations` | mình | D16 | Comment `harness.py:237-247` ghi *"KHÔNG dọn trước D11 freeze"* — **hạn đó hết hôm nay**, nên phải cấp hạn mới. Consumer thật còn lại chỉ `scripts/smoke_eval_d6.py:66,249`. Để một comment có hạn đã trôi qua đúng là loại lỗi doc-mâu-thuẫn-code mà AIE-1 bắt được ở D7 |
| Cách biểu diễn Q2 trong `Aggregate` | mình | D16 | Xem R5 — phải ghi nợ đúng chữ, nếu không D16 sẽ sniff magic string |
| Breakpoint #14 (`refused` xanh-giả) | AIE-1 | D17 | Đường ra đã có: `_PROMPT_HEADER` giờ do AIE-1 kiểm soát, thêm một dòng là có tín hiệu khai báo thật |
| Chủ trục INV-1 roles | **chưa có** — đề xuất SWE | gán D12 | S3/D21-22 mới fence chunk-level; hôm nay chỉ cần **có chủ** |
| Job CI so con trỏ với `main` submodule | mình (issue follow-up) | S2 | Không làm hôm nay; mở issue để nó có chủ |

---

# §5 — Không làm hôm nay

| Không làm | Vì sao |
|---|---|
| Implement `compute_scorecard` / `EvalHarness.run` | 4 lý do độc lập: #50 xếp eval-gate blocking là gold-plating (S3/D24) · ETA của GUIDE-C là D20 và #108 là D16 · land hôm nay làm `test_gate_blocks_on_fail` XPASS⇒FAIL **và** `test_harness_judge_compute_not_implemented` đỏ ngay ngày freeze, trong lúc quyền đổi marker (M6) **chưa chốt** · viết gate **trước** khi ghi ngưỡng literal vi phạm GUIDE-C §3.2 ⇒ 4 ô "exactly-at" thành `unknown`. **Tức land hôm nay là tự phá 4 ô đắt nhất trong grid của mình** |
| Lật `no-trace-no-proof` kiểu thẳng | Sai theo oracle F02 (DEC-05), và bản vá đúng chạm 4 consumer qua 3 repo đúng ngày freeze |
| Đụng `harness.py:159` (*"citation_accuracy không gate success"*) | GUIDE-C §4.1 **thu hồi** chỉ thị cũ và `:305` ghi *"must NOT be changed"*; `:909` nêu tên bài test canh nó. Sửa duy nhất được phép: thêm một câu trỏ tới gate ở tầng aggregate |
| Đổi số / đặt lại ID ô Grid C hoặc F | GUIDE-C §3.1: đổi mapping = **âm thầm dán nhãn lại 9 ô đã chấm** |
| Nhận trục INV-1 roles / fence chunk-level | S3/D21-22; nhận vào là lặp đúng lỗi S1 "gánh tải tích hợp không có title" và pha loãng quadrant mình đúng ngày freeze. Việc của mình là bảo đảm nó **có chủ trong log** |
| Vá nợ format 16 file | Mentor: *"needs an owner, not a fix today"*; và nó chạm file của cả 4 lane đúng ngày freeze |
| Đuổi theo #59 (case model thật) | Deferred S2, cần credential không kiểm soát được. Chỉ cấp cho nó **một chỗ ở**: comment #118 nêu M8 là câu chặn |
| Viết thêm một doc 300 dòng làm headline | *"Repeating Sprint 1 exactly scores lower."* Chiều sâu để trong hợp đồng freeze (nó xứng đáng); cái **mới** là cơ chế dùng chung + hành động xuyên quadrant. Design-note giữ 2 trang **có chủ ý** — mentor nói rõ ông không chấm độ dài |
| Push sau khi đã có approval | `evalhub#5` mất approval vì push muộn (`O3.2`) |
| Nhãn APPROVE khi thân review đòi sửa | Đúng một phần ba khoản trừ `O3.3` |
| Trọng số / kappa / composite trong `docs/reports` | report-CI chặn (App. A.11) |
| Đóng issue mà artifact không thấy trong clone sạch | *"counts against you"* |

---

# §6 — Fallback / Contingency

Neo: `docs/requirements/README.md:84` — *"Luật 2-4-8: kẹt 2h → ghi giả thuyết · 4h → xin hint · 8h → mentor
ngồi cùng 30'."* Ask đầu tiên đặt ~10:30–12:00 ⇒ **giờ cắt 1 = 17:00**, **giờ cắt 2 (mentor) = 19:00**.
Dùng luật của nhóm nghĩa là mốc giờ **không phải ultimatum đơn phương**.

**Nguyên tắc ghi:** không bao giờ ghi **sự im lặng** của người khác. Ghi **trạng thái** + **mặc định đã
công bố** + **lý do kỹ thuật khiến freeze độc lập**. Ba câu dùng lại:

- `Chốt theo mặc định đã công bố trên #84 lúc <giờ>. Không có phản đối nào được ghi trước 17:00.`
- `DEFERRED — chủ <vai>, hạn D<nn>. KHÔNG chặn freeze scorecard vì bộ chấm đọc <X>, nên nghĩa của <Y> không phụ thuộc mục này.`
- `Trạng thái: ĐÃ NỘP <path>@<sha> lúc <giờ>. Duyệt: CHỜ (approver <ai>).`

| Ai chậm | 17:00 | 19:00 | Freeze vẫn đi được vì |
|---|---|---|---|
| **Dat** — approval PR-A (**dependency blocking duy nhất**) | nhắc trên PR, tag cả 2 CODEOWNERS | escalate #83 | Freeze ghi bằng decision-log + chữ ký + **SHA contracts hiện tại**; DEC-02/03 chuyển thành **mini-RFC đã viết sẵn**, hạn D16; `SCHEMA_VERSION` giữ `0.2.0-draft` và log ghi vì sao. **Không self-merge PR contracts** — chạm layer đáy dùng chung, tự merge là nước đi đọc rất tệ. PR-C (kit, docs-only) thì 20:00 tự merge được, **kèm lý do trong merge body**, không im lặng |
| **AIE-1** — A1-1 carrier | áp mặc định | — | **Fallback kỹ thuật bỏ hẳn dependency**: siết `citations_from_trace` theo `node_type is NodeType.LLM_STEP` + thêm `retrieved_chunks_from_trace` đọc `outputs["chunks"]`, **phía evalhub**. Khi đó nghĩa của `citation_accuracy` do **luật chấm** quyết, không do hành vi engine quyết. Ghi: *"clause tương ứng trong hợp đồng trace-event: ĐỀ XUẤT, chưa xác nhận bởi người giữ bút; hành vi engine hôm nay đã khớp và đã được test engine khoá (`test_trace_event_emission.py:152`)"* |
| **AIE-1** — A1-2 `refused` / #14 | `DEFERRED — chủ AIE-1, hạn D17` | — | Freeze **seam**, không freeze công thức ⇒ không chặn gì |
| **DE** — DE-1/2/3 | áp mặc định (cả ba có lý do kỹ thuật **cưỡng chế**, không phải sở thích) | — | Bộ chấm đọc `outputs["chunks"]` — field **đã tồn tại từ D5**, không cần ai đồng ý để đọc. Ghi kèm rủi ro dư: *"shape `outputs` chưa là ràng buộc ⇒ đổi key `\"chunks\"` sẽ vỡ 4 chỗ im lặng; chủ clause DE, hạn D15"* — rồi **gieo mutation M5 đúng vào key đó** để cái chưa-được-bảo-vệ thành **đo được**, không phải khẳng định |
| **DE** — DE-4 golden-30 (**món duy nhất không default được**) | escalate trên #84 | mentor, đóng khung là **rủi ro lịch**, không phải phàn nàn | Lưới đỡ tự dựng: D16 chạy trên `callisto-smoke-10-v0` + ghi rõ *"10/30 case, chờ bộ đủ"*, và **không tự sinh case thay bên giữ nhãn**. Câu gửi mentor kèm lưới đỡ ⇒ là **báo cáo**, không phải phàn nàn |
| **SWE** — SWE-1/2 | im lặng = giữ nguyên = **đúng kết quả muốn** | không escalate | SWE-1 là cam kết **âm**; SWE-2 chỉ cần ghi "số là dữ liệu, chủ AIE-2, hạn D16". **Không nhắc lần hai trước 17:00** — với tiền lệ D5, follow-up trong 4h đọc thành gây áp lực và không mua được gì. Một ask 11:40, một nudge trung tính 17:00, sau đó chỉ hỏi mentor **về chủ trục roles**, không hỏi về câu trả lời của SWE |
| **Mentor** — M-1/2/3 (**ca hậu quả lớn nhất**: ông là approver cho cả design-note lẫn contracts) | — | escalate đúng 3 món kèm lưới đỡ đã dựng | **Quyết định thiết kế then chốt của ngày:** giữ mọi thứ ông duyệt **ra khỏi** critical path. Nếu cần, freeze **không chạm contracts** — khi đó "freeze" không cần approval của ai: ghi vào decision-log + hồ sơ freeze **SHA contracts đang ghim**, thêm header `FROZEN` vào 4 doc v0, `SCHEMA_VERSION` giữ `0.2.0-draft` với ghi chú *"chữ `-draft` bỏ khi mentor duyệt PR contracts; freeze về hiệu lực đã có từ D11 qua decision-log + 4/4 chữ ký, không qua chuỗi phiên bản"* — và nêu **cả hai** phương án trong một đoạn để ông chọn không cần vòng thứ hai. Design-note: **submitted ≠ approved**, không tick ô |

---

# §7 — Checklist cuối ngày (đo được)

| # | Hạng mục | Ngưỡng đạt | Cách đo |
|---|---|---|---|
| 1 | Deliverable | **8/8** tồn tại trong clone sạch | App. D.5 |
| 2 | Quyết định | 5 dòng DEC có id + chủ + hạn; **0** món hoãn không có chủ | đọc `docs/decision-log.md` |
| 3 | Contract | 2 dòng **merged** *hoặc* 1 mini-RFC viết sẵn + hạn D16 — **không có trạng thái thứ ba** | `gh pr view` PR-A |
| 4 | Chữ ký | ≥1 ký thật + 3 file điền sẵn; báo cáo **1/4, 3 người kia đã unblock** | `ls sig-*.md \| wc -l` + `git log --format='%an'` |
| 5 | Test | `333–334 passed, 8 skipped, 5 xfailed`, **0 XPASS**; evalhub **đúng 2 xfailed, 0 xpassed** | App. D.3 |
| 6 | Không hồi quy | 3 số bảng điểm y nguyên · `git diff --stat -- packages/evalhub/src` **rỗng** | App. D.4 |
| 7 | Con trỏ | 5/5 = `main` submodule · kit CI **10/10** | `git submodule status` từ clone sạch |
| 8 | Review | 3 review, mỗi cái ≥1 finding cụ thể, **nhãn khớp thân** | `gh api .../reviews` |
| 9 | Mutation | 5 gieo · 5 dòng *declared vs actual* · **≥1 dòng lệch nhau** | đọc `docs/mutations/s2/…` |
| 10 | Kỷ luật | **0** ô DoD tick mà không chứng minh được · **0** issue đóng mà artifact không thấy trong clone | soát #83 + #84 |
| 11 | Note | có số **và** chẩn đoán cho mỗi số · `## Contract / integration` trả đủ 3 câu | đọc note |
| 12 | Không rò rỉ | `docs/reports` không có trọng số/kappa/composite | report-CI xanh |

---
---

# Appendix

## A — Ground truth & verify output (đo 03/08 sáng)

**A.1 Baseline**

```
pytest packages apps tests    331 passed, 8 skipped, 5 xfailed      (0 XPASS)
pytest packages/evalhub        41 passed, 2 xfailed                 (cả 2 strict=True)
mypy packages apps             Success — 0 lỗi / 110 file
ruff check . · lint-imports    All checks passed · 1 kept, 0 broken
ruff format --check .          16 file nợ (KHÔNG vá)
uv lock --check                pass
kit main                       9ad96a9 · CI 10/10 · 5 con trỏ = main submodule
nhánh việc                     packages/evalhub @ aie-2/day11-scorecard-freeze (sạch, từ 9cc4073)
```

Docker test PG chết qua cuối tuần: `psycopg_pool.PoolTimeout: pool initialization incomplete after 10 sec`
+ `connection to server at "127.0.0.1", port 5433 failed: Connection refused` ⇒ suite ra `40 passed, 2
xfailed, 1 error`. Dựng lại container → baseline khớp. **Nó error to, không skip im** — bài học *"31 skip
là lời nói dối im lặng"* đang chạy đúng.

**A.2 Không có đề bài** — `gh api .../contents/week-2/days/day-11.md` → **404**; requirements main
`c64a212e` (2026-07-23, 11 ngày cũ), root tree không có `week-2/`; cả 50 issue #80–#129 trỏ file chết.
Mentor im lặng từ 31/07 22:09Z; org không có commit/comment nào từ 31/07. ⇒ **DoD 4 dòng là spec duy nhất.**

**A.3 Issue** — #80 DE (**2 bút**: trace-event + `kb.search`) · #81 AIE-1 (consumer, **không giữ bút**) ·
#82 SWE (recipe) · #83 mình (scorecard) · #84 team (**không assignee, 0 comment**). Cả 5 dùng **một** DoD
4 dòng ⇒ 3/4 dòng của mình là biến đếm nhóm. #85–#129 là D12–D20 (5 issue/ngày), tạo cùng batch 21:57Z.

**A.4 Ba thứ không tồn tại trong org** (verify bằng code search + `find`): file decision-log · template
mini-RFC · bất kỳ instance mini-RFC hay tiền lệ chữ ký nào. `docs/decisions.md` được note của AIE-1 trích
(`2026-07-29-TranBaDat2607.md:14`) nhưng **404 ở mọi repo**. File duy nhất có chữ "decision" là
`docs/requirements/00-orientation/decisions-locked.md` — bảng D-1..D-13 của mentor, submodule READ-only.

**A.5 Quyền merge** — `packages/contracts/.github/CODEOWNERS` = `* @TranBaDat2607 @hieubui2409`, đặt bởi
commit `dce8c94` *"chore(codeowners): Đạt (nhóm trưởng) co-owner shared repo — **mentor ra khỏi critical
path**"*. `GITFLOWS.md:66-68` + `contracts/README.md:5` ("owner = mentor") **đã cũ** so với commit đó.
Bằng chứng thực hành: `kit#77` do mình tác giả, **Dat approve + merge**. ⇒ 1 approval của Dat là merge được.

**A.6 CI không bắt được consumer vỡ** — `.github/workflows/reusable-domain-ci.yml:69-71` clone kit **main**
+ init submodule ở **con trỏ kit đang ghim**; `:74-79` chỉ overlay domain của PR; `:100` chỉ chạy
`pytest <domain_path>/tests`; `:104-112` lint/mypy chỉ trên `<domain_path>`. Hai hệ quả: PR contracts
**không bao giờ** chạy test evalhub/apps; PR evalhub resolve `studio_contracts` ở **con trỏ kit** ⇒ code
dùng field contract mới sẽ **đỏ tới khi bump**. ⇒ phải tự chạy proof consumer (App. D.2).

**A.7 Hai tiền đề của chính mình phải rút**

| Ghi chú cũ | Sự thật đo được | Hệ quả |
|---|---|---|
| `scorecard-v0.md:335-337` — leak mức UUID cần `TraceEvent.citations` mang `tenant_id` per-chunk ⇒ **đổi contract, mini-RFC + 4/4 chữ ký** | `interpreter.py:265-268`: `outputs = {"chunks": [item.model_dump(mode="json") for item in output if isinstance(item, KbSearchResultItem)]}`, và `KbSearchResultItem` (`kb.py:23-29`) mang `tenant_id: UUID` **và** `section_role`. 4 consumer đang đọc: `smoke_eval_d6.py:247,270` · `e2e_smoke_eval.py:265-271` · `test_spine_live.py:135` | **Định giá quá cao — rút.** Per-chunk tenant UUID **đã ở trong trace hôm nay**, trên đúng node. Thiếu là **một dòng hợp đồng** (`trace-event.v0.md:77` khai `outputs` là "⏸ hoãn S2"), không phải một field. 0 bump, 0 mini-RFC |
| `scorecard-v0.md:3` ghi `SCHEMA_VERSION = "0.1.0-draft"` | contracts ở `0.2.0-draft` từ D5 (D-13) | Header của mình sai từ D5. **Sửa trước khi freeze** — không freeze một doc tự mâu thuẫn |

**A.8 Grep làm bằng chứng cho PR-A** — `grep -rn "\.judge\b\|judge=" packages apps scripts tests`:
**0 reader**; 4 constructor, tất cả là test fixture (`contracts/tests/test_roundtrip.py:102` ·
`evalhub/tests/test_scorecard_roundtrip.py:27,35` · `test_eval_gate.py:93`).
`_assert_roundtrip_both_directions` (`contracts/tests/test_roundtrip.py:114-124`) là dump→validate→dump ⇒
field default `None` round-trip **cả hai chiều alias**. Version pin **duy nhất** trong workspace:
`contracts/tests/test_roundtrip.py:160-164`. `SmokeResult.citation_accuracy` phải giữ `float`: 3 renderer
format `:.2f` (`cli.py:222` · `smoke_eval_d6.py:219` · `e2e_smoke_eval.py:294`).

**A.9 Biến thể có-bump (viết sẵn, dùng nếu DEC-01 đi hướng khác)** — `__init__.py:33`
(`0.2.0-draft`→`0.3.0-draft`) + đoạn ghi nhận `:5-12` (theo khuôn câu 0.1→0.2) + `test_roundtrip.py:164`.
Không chỗ nào khác ghim version. Doc cần **thông báo** (không sửa): `packages/kb/flow.md:303` ·
`kb/docs/contracts/kb-search.v0.md:286` · `docs/code-standards.md:150` (đã cũ sẵn ở `0.1.0-draft`).

**A.10 Consumer ngoài quadrant của bề mặt mình** — `score_case`/`citations_from_trace`/`SmokeResult`:
`apps/studio/scripts/e2e_smoke_eval.py:104,256-257` · `apps/studio/tests/test_spine_scored_from_postgres.py:49,103,109-110,128,138,140`
· `apps/studio/tests/test_eval_adapter.py:149` · `packages/kb/tests/test_spine_live.py:322,326-327` ·
`scripts/smoke_eval_d6.py:66,249` (**còn dùng alias cũ `_retrieved_citations`**) ·
`packages/kb/scripts/mutation_check.py:141`.

**A.11 report-CI** — `docs/reports/.github/workflows/report-ci.yml:60` *"Scan for rubric/weight/skew/grade
marker SHAPES (never a literal number)"*, và `docs/reports/README.md` cấm bàn về rubric/điểm/chữ của mình.
Dry-run: `| A1.1 | A | lý do |` → **0 match**; `weight: 0.10` + `kappa: +0.8` → **2 match ⇒ build fail**.
Cây report hiện tại: 0 match. ⇒ self-assessment trong repo report **chỉ chữ + lý do**; số học ở kit.

**A.12 Nợ format 16 file** — workbench 6 · engine 5 · apps/studio 4 · root (`tests/test_ops.py`) 1. Trong
đó **3 file là code gốc mentor/scaffold kit** (`apps/studio/core/queue.py` · `apps/studio/middleware.py` ·
`tests/test_ops.py`) ⇒ không thuộc fence quadrant nào.

**A.13 Marker workbench** — `test_graph_lint_not_implemented:69` đã thành **plain assertion** (*"post-gate
fix, `kit#50`"*) ✓; **`test_lint_rejects_bad_graph:74` vẫn `@pytest.mark.xfail(reason=…, strict=False)`**
⇒ finding tặng SWE (T5).

## B — GUIDE-C: phán quyết dùng làm neo

`docs/test-design/GUIDE-C-eval-gate.md` — **948 dòng, mentor viết 30/07 17:08, owner AIE-2**. Cùng bộ:
`00-METHODOLOGY.md` · `01-FOUNDATION.md` · `02-MATRIX.md` · GUIDE-A/B/D. #67 lấy bộ này làm **metric cuối
GATE-3**.

**B.1 D-19 / M1** (§4.1, `:280`) — gate = **AND** hai ngưỡng · toán tử **`>=`** · tầng **aggregate**.
Kèm §3.1 (`:179`) bảng oracle Grid C (C01–C09) *"derived from D-19"*, và §3.2 luật ngưỡng: *"the threshold
is a **ROUND DECIMAL, fixed and written down BEFORE** the dataset is constructed"*, cấm
`threshold := the value the run just computed`. Ruling **D-22** (`02-MATRIX.md:281`): so `==` trên ngưỡng
tròn chốt trước (`11/20 = 0.55` exact trong CPython 3.14).

**B.2 Q8** (= breakpoint #9) — *"the escalation review argues **excluding refusals from the denominator**
is cleaner than pinning 1.0"*. Số hỗ trợ: bộ 10 báo `0.90` vs thật **`0.833`** (+0.067; 3 case đã đỏ vẫn
góp `1.00`) và `10×1.0 + 20×0.85 = đúng 0.90` ⇒ với `>=` một bản **đáng FAIL** lại PASS ngay ngưỡng 0.9.

**B.3 F02** (`:592`) — *"the honest refusal: refused, cited nothing ⇒ **the case PASSES**"*. §6.4.2 (`:645`)
đòi một **pin test** cho giá trị nhánh từ-chối, nêu tên `harness.py:178` + Q8 làm lý do; §9 ghi pin đó
**chưa tồn tại** ⇒ đổi `1.0`→`0.0` ở đó hôm nay **không làm đỏ gì**. `:909` — *"This pin should not move.
If your change turns it red, your change is the thing that is wrong."*
**Giá nếu lật thẳng DEC-05:** đỏ `test_refusal_success:241` · `test_cross_role_refusal_success:362` ·
`test_run_smoke_over_set:392`; XPASS⇒FAIL bài `:276`; `cli` 5/5→3/5 · `e2e` quality 4/5→3/5 ·
`smoke_eval_d6` 6/10 tụt; mọi số trong pack GATE-1 + note D10 thành cũ 24h sau khi submit.

**B.4 `:305`** — *"There is no conflict, and **`harness.py:159` must NOT be changed**"* (register §11 D-19
từng bảo đổi, rồi **thu hồi** — CP-2.1).

**B.5 Ruling D-24** (`02-MATRIX.md:284`) — *"Fix the schemas before Day 20, then write the tests. Add
`recipe_hash` to `Scorecard`"*, owner **AIE-2 (contract)**, kèm *"`Scorecard` is frozen contract #4, so
this needs a mini-RFC with four signatures"*.

**B.6 Câu mentor-only, KHÔNG tự trả lời** — **M5** nguồn nhãn tay cho `agreement` (chặn mọi ô judge) ·
**M6** quyền đổi marker `strict` (§2.3: *"Do not edit that marker on your own authority"*) · **M8** cơ chế
dựng "bản tệ" thật (`"agent-bad-instructions"` ở `test_eval_gate.py:54` là một nhãn chuỗi, không có cơ chế
sau nó) · **Q1/M4** so sánh float.

**B.7 GUIDE-C lệch baseline 2 phút** — ghim evalhub `123e85c4` @ 30/07 **15:06:08**; commit harden D9 của
mình `a9b26cd` @ **15:04:12**; PR #5 merge vào evalhub main (`9cc4073`) @ **17:08**. ⇒ §2.3/§4.3/§4.4 mô
tả một cây **thôi tồn tại 2 giờ sau khi ghim**. Lệnh drift của chính mentor chạy bây giờ:
`git diff --name-only 8a420e7 HEAD -- '*.py'` → 1 file · `--submodule=short` → 6 pointer moves.
`02-MATRIX.md` §6: *"Non-empty ⇒ citations touching those files may have drifted… **and report it if the
guide is genuinely wrong** — a stale citation is a bug in the guide."* ⇒ **báo là được phép và được
khuyến khích**, áp cho cả 4 guide.

## C — Bảng 5 mutation vào `packages/engine`

| # | Seam | Mutation (file:line) | Khai trước: bài phải đỏ | Verify clause nào |
|---|---|---|---|---|
| **M1** | carrier `citations` | `interpreter.py:270` — trong nhánh `isinstance(output, list)`, set `citations = [c["chunk_id"] for c in outputs["chunks"]]` thay vì `None` ⇒ `kb-retrieve` **cũng** mang citations | `engine/tests/test_trace_event_emission.py:152`. **Dự đoán: ĐỎ ở engine, XANH ở evalhub** — helper node-agnostic của tôi đếm gộp vui vẻ | **A1-1.** Nếu evalhub xanh ⇒ phân biệt retrieved/grounded được chứng minh là **tình cờ**, và clause thành **bắt buộc**. Đây là phép đo đắt giá nhất hôm nay |
| **M2** | `refused` | `executors.py:264` — `"refused": not citations` → `"refused": not retrieved_chunks` (về mốc D4) | `engine/tests/test_refusal_from_grounding.py:97,111,120,132,144` | **A1-2.** Xanh ⇒ lần định-nghĩa-lại thứ ba làm bộ chấm lệch **im lặng**; đó là lập luận cho clause "đổi công thức phải báo" |
| **M3** | thứ tự `ts` | `interpreter.py:284-287` — xoá clamp `now = last_ts + timedelta(microseconds=1)` | `test_trace_event_emission.py:113-118` (`len(set(timestamps)) == 4`) **đỏ**; và `kb/tests/test_trace_reader.py:98-106` **phải xanh** — đó chính là điểm | **DE-2.** Chứng minh **hai test đều đúng về tầng của mình** ⇒ chẻ producer/reader là **giải pháp**, không phải thoả hiệp. Đóng carry #9 bằng một phép đo |
| **M4** | trục INV-1 roles | `executors.py:152` — `section_roles = [...] if isinstance(raw_roles, list) else []` → `else ["public","hr","finance","engineering"]` (fail-**open** khi roles méo) | test role-fence trong `engine/tests/` + T6 ở `packages/kb` | **M-3(c).** Thăm trực tiếp lỗ `#74 §6`. Xanh ⇒ bằng chứng cứng từ **một lượt chạy** (không phải từ một báo cáo) rằng trục roles cần chủ **hôm nay** |
| **M5** | key `outputs["chunks"]` | `interpreter.py:266` — rename key `"chunks"` → `"retrieved"` | `smoke_eval_d6.py:247,270` · `e2e_smoke_eval.py:267` · `test_spine_live.py:135`. **Dự đoán: chỉ bài cuối là test thật, và nó gated bởi Postgres** ⇒ khả năng cao **xanh hết trong CI** | **DE-1.** Nếu CI xanh ⇒ invariant tôi đang xin DE freeze **hiện có 0 lớp test bảo vệ**, và 2 consumer sẽ vỡ đều là *script*. Đó là lập luận **bằng số** |
| *(bonus, ghi rõ là re-run)* | trục INV-1 tenant | `interpreter.py:293` — `tenant_id=session_context.tenant_id` → `recipe.tenant_id` | Kết quả của mentor ở §2.6 là **3 failed across 3 quadrants** | Kiểm hồi quy guard S1→S2. **Ghi rõ đây là re-run mutation của mentor, không phải của mình** |

## D — Verification

**D.1 Môi trường** (port 5433 được `conftest.py:23,65-72` cưỡng chế, fail **to** nếu DSN sai)

```bash
docker compose -f docker-compose.test.yml up -d --wait
export STUDIO_DATABASE_URL=postgresql://studio_app:changeme@localhost:5433/studio_test
export STUDIO_DATABASE_URL_ADMIN=postgresql://studio_owner:changeme@localhost:5433/studio_test
```

**D.2 Proof consumer — CI không chạy (A.6). Làm TRƯỚC khi xin review, dán số vào body PR-A**

```bash
git -C packages/contracts checkout aie-2/day11-scorecard-freeze
uv run mypy packages apps          # kỳ vọng Success — 110 file (không đổi; A.8 ⇒ không sinh lỗi mới)
uv run pytest packages apps tests -q
uv run lint-imports                # 1 kept, 0 broken
git -C packages/contracts checkout 3d7004b   # trả về SHA đang ghim — bài học D10
git status --short                            # PHẢI rỗng
```

**D.3 Sau PR-A + PR-B**

```bash
uv run pytest packages apps tests -q   # 333–334 passed, 8 skipped, 5 xfailed, 0 XPASS
uv run pytest packages/evalhub -q      # 42–43 passed, ĐÚNG 2 xfailed, 0 xpassed
uv run pytest packages/contracts -q    # +2 test mới
uv run mypy packages apps              # Success — 110 file
uv run ruff format --check packages/evalhub packages/contracts   # file của mình phải sạch
git diff --stat -- packages/evalhub/src                          # RỖNG
```

**D.4 Ba số phải KHÔNG đổi** (bằng chứng freeze chỉ đụng shape)

```bash
uv run python -m studio_evalhub.cli                    # 5/5 PASS
uv run python apps/studio/scripts/e2e_smoke_eval.py    # exit 0 · wiring 5/5 · quality 4/5 · RED-CHECK 2/2
uv run python scripts/smoke_eval_d6.py                 # 6/10 PASS
```

Chạy **hai lượt**, lọc `run_id` + `ts` rồi diff. Nói **"bảng điểm trùng khít từng dòng qua hai lượt"** —
**KHÔNG** nói "byte-identical": hai lượt lệch ~70 dòng UUID/timestamp (đúng chỗ đã phải sửa cách nói ở D10).

**D.5 Clone sạch** — cơ chế đã bắt được hai lần mất điểm vì lệch con trỏ

```bash
git clone --recursive git@github.com:AI20K-VGR/agentcore-studio-kit.git /tmp/d11-verify
cd /tmp/d11-verify && git submodule status
ls docs/decision-log.md docs/decisions/s1-contract-freeze/ docs/design-notes/aie-2-dholmes0207.md
ls packages/evalhub/docs/contracts/scorecard.v1.md packages/evalhub/docs/mini-rfc/
grep -n "recipe_hash" packages/contracts/src/studio_contracts/scorecard.py
uv sync --frozen && uv run pytest packages/evalhub -q
```

`ls`/`grep` chạy **trong clone**, không trong working tree — đó là toàn bộ điểm: ở D10 working tree "thấy"
một bản vá mà cây gate chạy **không** thấy. Dán bảng `git submodule status` vào note làm bằng chứng.

## E — Note D11: số bắt buộc + bản nháp self-assessment

**Số bắt buộc có, mỗi số kèm một câu "nên sao"** — brief 404 + requirements 11 ngày cũ (⇒ "freeze"/"chữ
ký"/"decision-log" không có định nghĩa publish, nên cơ chế là việc của mình, kèm đường lùi) · GUIDE-C lệch
baseline **2 phút** (`15:04:12` / `15:06:08` / `17:08`; drift `1 file` + `6 pointer moves`) · Q8: `0.90`
báo vs **`0.833`** thật (+0.067; 3 case đỏ góp 1.00) và `10×1.0 + 20×0.85 = đúng 0.90` · Q1 grep **0
reader / 4 constructor** · 5 mutation *declared vs actual* · baseline trước/sau · `git submodule status`
**từ clone sạch** · report-CI dry-run (nháp 0 match; `weight:`/`kappa:` 2 match) · **4 consumer ngoài
quadrant** của `score_case`/`citations_from_trace` (⇒ vì sao thêm entry point thay vì đổi tham số).

Mục `## Contract / integration` trả đủ ba câu template hỏi: đổi gì · **ai ký** · vỡ/mở được gì. Cộng
tự-khai: `eval.scorecards`/`eval.golden_sets` **không có `tenant_id` và không có RLS** (workspace: RLS trên
1/11 bảng; của mình 0/2) — đề nghị đồng-ký mini-RFC schema-drift (carry #8) của DE với hai bảng của mình
tính vào.

**Self-assessment khởi động** (chữ + lý do, **không** số học — A.11), mỗi dòng kèm **điều kiện làm nó tụt**:

| Ô | Chữ | Lý do một dòng + điều kiện tụt |
|---|---|---|
| A1.1 | **A** | Escalate #84 vô chủ lúc 09:3x + hai rủi ro chưa ai gọi tên (GUIDE-C drift · report-CI vs self-assessment), đều kèm lệnh. **Tụt** nếu chỉ nói miệng |
| A1.2 | **A** | Dựng cơ chế freeze không ai nhờ + **điền sẵn 3 file sig** cho người khác. **Tụt** nếu template không nằm trong PR đã merge |
| A1.3 | I | S2 chưa có ai chỉ ra mình sai; kế thừa phương pháp khai-trước của DE + khuôn artifact của AIE-1 là uptake, nhưng ô này đo phản ứng khi **bị chỉ ra** |
| S2.1 | I | Hôm nay **0 thay đổi hành vi**; pin F02 đúng nhưng nhỏ. Claim A ở đây đúng là loại miscalibration đang bị đo |
| S2.2 | **A** | Một dòng goal → chuỗi có phương án bỏ, hoãn có chủ+hạn, DoD cá nhân viết vào chỗ generator để trống. **Tụt** nếu chuỗi chỉ sống trong `Plan/` |
| S2.3 | I | Một ngày không phải nhịp. Ước lượng đang kiểm: "3 PR merged + 2 con trỏ bumped trước 16:30" |
| S2.4 | I | Mutation đã khai, **chưa đo**. Thành A khi sweep engine ra bảng có dự đoán trước khi chạy |
| O3.1 | I | Gate vẫn chưa có verdict — 0/9 ô Grid C dựng được. Đúng hạn D16/D20, nhưng ô này hỏi *thứ đó có tồn tại không* |
| O3.2 | I | Tạm. Khoản trừ S1 là PR nằm chờ lane khác; mitigation hôm nay là pre-book reviewer 10:10. Còn PR nào mở sang mai thì I là tốt nhất |
| O3.3 | **A** *(mục tiêu)* | Claim A **chỉ khi**: clone sạch thấy đủ 8 deliverable · 2 con trỏ bumped · mọi issue chạm đều có artifact tìm được · không review nào nhãn lệch thân. Thiếu một ⇒ I. **Đây là ô đã lấy đi band** |
| D1 | **A** | Cơ chế 3 người dùng lại được trong 60 giây · mutation vào quadrant khác · finding trên hợp đồng của DE · teach kèm artifact-chứng-minh cho SWE. **Tụt** nếu tới D14 chỉ mình dùng cơ chế đó |
| D3 | I | Freeze không làm gì **chạy** mới; ô này đo increment tuần chạy được |

Năm A tạm, bảy I, mỗi A kèm một điều kiện phủ định. Hai ô (`S2.1`, `O3.1`) **cố ý không** claim A dù đọc
thoáng thì được — bất đối xứng đó chính là bằng chứng calibration.

## F — Lưu file

Chép plan này sang **`Plan/day-11-aie2.md`** (thay bản 84 dòng lập trước), theo thói quen
`Plan/day-NN-aie2.md`. `Plan/` không thuộc scope chấm; hợp đồng · decision-log · design-note nằm ở
kit/evalhub như T6/T7.
