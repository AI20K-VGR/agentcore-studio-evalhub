---
id: studio.contract.scorecard.v1
type: interface-freeze
status: v1-frozen
freeze: FROZEN   # lật 2026-08-04 — evalhub#6/#7 + contracts#1/#3 merged; xem §0.3 chi tiết chữ ký từng PR
freeze_target: D11
contract_ref: umbrella-contract §3.4
pen: AIE-2 — Lưu Tiến Duy
date: 2026-08-03
supersedes: docs/scorecard-v0.md
schema_version_at_freeze: 0.2.0-draft
contracts_sha_at_freeze: 3d7004b2e55d500e3706b9eac412fc809eb4e839
signatures: ["AIE-1 @TranBaDat2607", "AIE-2 @dholmes0207 (bút, tự ký)", "DE @DongAnh2704", "SWE @Dozyboy"]   # 4/4 PR mang nội dung scorecard đều đủ 3/3 Approve (contracts#1@2b95ca9 · contracts#3@dcea5b4 · evalhub#6@150d6bd · evalhub#7@c4fc9e7); 12/12 chữ ký ở đúng head PR, 0 stale. Đồng bộ 2026-08-04 07:55Z — dấu vết đầy đủ + lệnh verify ở docs/decisions/scorecard.md
---

# 🖊️ scorecard — HỢP ĐỒNG v1 (FROZEN)

> **Bút:** AIE-2 — Lưu Tiến Duy · **Ngày:** 2026-08-03 (D11, issue #83)
> **Thay cho:** [`docs/scorecard-v0.md`](../scorecard-v0.md) — v0 giữ nguyên làm **log suy luận D2→D7**,
> không xoá: nó chứa vết AIE-1 bắt được doc mâu thuẫn `main` ở D7, và vết đó là bằng chứng.
> **Vì sao file mới thay vì `git mv`:** một tài liệu đã freeze không được mang chữ *"chưa freeze"*
> trong header lịch sử của chính nó.

Hợp đồng nằm ở code: `studio_contracts.scorecard` (`Scorecard`/`CaseResult`/`Aggregate`/`Gate`/
`Judge`/`GateThreshold`). File này **không lặp lại** shape — nó khoá **câu chữ đang đọc-được-hai-kiểu**,
tức những chỗ mà hai người đọc cùng một field ra hai nghĩa khác nhau.

---

## §0.1 Đã khoá ở bản này vs còn chờ người khác

| | Nội dung | Trạng thái |
|---|---|---|
| ✅ | `CaseResult.judge` nhận `None` khi không có judge chạy (§1) | quyết rồi — chờ contracts#1 merge |
| ✅ | Luật bump cho nới `required`→`optional` (§2) | quyết rồi — ADR-D11-02 |
| ✅ | `citation_accuracy` nhánh từ-chối: quy ước, **không phải phép đo** (§3) | quyết rồi + pin test |
| ✅ | `citation_accuracy` đo **fence**, KHÔNG đo **truy xuất** — giới hạn khai vào hợp đồng (§3.1) | quyết rồi — null control đã tái lập |
| ✅ | `no-trace-no-proof` thuộc tầng giữ `events`, không thuộc `score_case` (§4) | quyết rồi + xfail đổi neo |
| ✅ | `Gate.threshold` ≡ `Recipe.scorecard_threshold` từng field (§5) | quyết rồi — test AIE-2 viết |
| ✅/🔴 | Carrier của `citations` chỉ trên `llm-step` (§6) | **engine ĐÓNG** (`engine#15`, gate `interpreter.py:304`) · **evalhub CHƯA có lưới** — chủ AIE-2, hạn D16 |
| ⏳ | `outputs["chunks"]` thành invariant có tên (§7) | **chờ DE** — dữ liệu đã có từ D5 |
| ⏳ | `recipe_hash` trên `Scorecard` (§8) | PR riêng hôm nay — giá trị chờ SWE |
| 🔴 | Nguồn nhãn tay cho `Judge.agreement` (§9) | **chặn mọi ô judge** — chưa có nguồn |

## §0.2 Chữ ký

Theo **ADR-D11-01** (@Dozyboy, kit#84): chữ ký thật = **bấm Approve trên PR** chứa hợp đồng, xác
thực bằng tài khoản GitHub. File này **không** chứa bảng tự-điền — ai sửa file cũng gõ được tên người
khác, nên một bảng tự-điền không phải chữ ký.

Dấu vết Approve (ai · PR nào · ngày · `<repo>@<sha>`) ghi ở
[`docs/decisions/scorecard.md`](../decisions/scorecard.md) — **cùng repo này**, không ở kit.
Chỗ đặt theo lần lặp cuối của kit#130 (*"kit stays pure index, no repo's content duplicated here"*):
nội dung ở repo của bút, kit chỉ giữ index (`kit:docs/decisions/README.md`). DE và SWE cũng đặt
decision-log trong repo của mình.

## §0.3 Điều kiện còn thiếu để lật `FROZEN`

| # | Điều kiện | Chờ ai |
|---|---|---|
| 1 | [contracts#1](https://github.com/AI20K-VGR/agentcore-studio-contracts/pull/1) (`judge` → optional) merge | @TranBaDat2607 / @hieubui2409 (CODEOWNERS) |
| 2 | PR `recipe_hash` trên `Scorecard` (ruling D-24) merge | cùng trên |
| 3 | 4/4 Approve trên hai PR đó | SWE · DE · AIE-1 · AIE-2 |

**Chưa lật `freeze: FROZEN`** — 3 điều kiện chưa đủ cả 3. Báo cáo trạng thái là **freeze-ready**,
không phải frozen; và **không** tick ô DoD nào dựa trên trạng thái này.

---

## §1 · `CaseResult.judge` — `None` nghĩa là "không có judge chạy"

**Clause.** `CaseResult.judge: Judge | None = None`. Giá trị `None` mang nghĩa **case này được chấm
KHÔNG qua LLM-judge** (exact-match hoặc kiểm từ-chối — loại duy nhất tồn tại trước S3). `None` là giá
trị **trung thực duy nhất**; một `Judge(...)` hằng số là **vi phạm hợp đồng**.

**Vì sao không được điền hằng.** `Judge.agreement` đo *scorer có đồng ý với nhãn tay hay không*
(`judge.py:6-9` cấm giá trị hằng). Với một case exact-match FAIL thì agreement **không xác định** —
không phải `1.0`, cũng không phải `0.0` — vì không có verdict của người cho từng `actual`. Điền `1.0`
là bịa một phép đo, và nó **không phân biệt được** với một judge thật đồng thuận 100% ⇒ làm hỏng âm
thầm mọi aggregate trên `agreement` (INV-4). GUIDE-C `:855-887` gọi đúng loại này:
*"a quality-check metric filled in by the subject of the check"*.

**`Judge` giữ nguyên shape bắt buộc** (`label` + `agreement`) cho ca S3 khi judge **thật** đã chạy.

## §2 · Luật bump — nới `required` → `optional`

**Clause.** Nới một field `required` → `optional` **KHÔNG** bump `SCHEMA_VERSION`, **với điều kiện
đếm được 0 reader giả định non-null**. Nếu số đó > 0 thì đây là breaking **cho reader** dù guard
payload xanh ⇒ cần DEC + bump.

Đầy đủ bối cảnh, phương án bỏ, số đo: **ADR-D11-02**. Tóm: `contracts/__init__.py:5-12` liệt kê 3
loại breaking (rename · removal · required-add); nới required→optional **không nằm trong 3 loại đó**,
nên đây là **ca thứ tư** — *tương thích trên dây, KHÔNG tương thích với reader*. Đo hôm nay: **0
reader, 4 constructor toàn test fixture**; workspace `331 → 333 passed` (đúng +2 test mới, 0 test cũ
sửa), mypy `Success — 110 file` không đổi.

## §3 · `citation_accuracy` nhánh từ-chối là QUY ƯỚC, không phải phép đo

**Clause, ba phần.**

1. **Per-case:** case từ-chối trả `citation_accuracy = 1.0`. Đây là **quy ước vacuous-truth**, **không
   phải** một phép đo chất lượng trích dẫn. Giá trị này **được pin bằng test** và không được đổi
   không-tuyên-bố.
2. **Aggregate:** case từ-chối **bị loại khỏi mẫu số** của `aggregate.citation_accuracy`.
3. **Render:** bảng người-đọc in `n/a` cho dòng từ-chối, **không** in `1.00`.

**Vì sao per-case giữ `1.0` mà aggregate lại loại.** `SmokeResult.citation_accuracy` phải giữ kiểu
`float`: 3 renderer format `:.2f` (`cli.py:222` · `smoke_eval_d6.py:219` · `e2e_smoke_eval.py:294`)
sẽ `TypeError` với `None`. Và quy ước vacuous-truth **tồn tại cả hai nhánh**: `expected_citation == []`
trên nhánh **trả-lời** cũng trả `1.0` (`harness.py:167`). Nên phải phát biểu nó là **quy ước**, không
phải phép đo — đó chính là nội dung clause này.

**Vì sao aggregate phải loại — số, không phải nguyên tắc.** Đo trên `callisto-smoke-10-v0`:
`success_rate = 0.60` nhưng `aggregate.citation_accuracy = 0.90`, trong khi con số **thật** chỉ tính
6 case trả-lời là **0.833** ⇒ thổi phồng **+0.067**, và **3 case đã đỏ** (SC-04/07/09) vẫn góp `1.00`.
Phép tính chí tử (GUIDE-C Q8): `10 refusal ở 1.0 + 20 answered ở 0.85 = đúng 0.90` ⇒ với toán tử `>=`
một bản **đáng FAIL** lại PASS ngay tại ngưỡng 0.9.

**Nợ có chủ + hạn.** Cách **biểu diễn** trong contract (nullable vs thêm `n_scored_citation` trên
`Aggregate`) để **D16**, chủ AIE-2. Ghi đúng chữ để D16 không phải sniff magic string:
> *"`aggregate` không tính lại được từ payload `results` đã lưu."*

**Không đụng `harness.py:159`** — GUIDE-C `:305`: *"There is no conflict, and `harness.py:159` must
NOT be changed"* (register §11 D-19 từng bảo đổi rồi **thu hồi**, CP-2.1). Sửa duy nhất được phép:
thêm một câu trỏ tới gate ở tầng aggregate.

### §3.1 · GIỚI HẠN — `citation_accuracy` đo sức mạnh FENCE, không đo sức mạnh TRUY XUẤT

**Clause.** Trên bộ golden hiện tại, `citation_accuracy` **KHÔNG** chứng minh chất lượng truy xuất.
Bất kỳ ai đọc một `citation_accuracy` cao và kết luận *"retrieval tốt"* là đọc sai hợp đồng này.

**Bằng chứng — null control của AIE-1 (`engine#15`), đã tự tái lập ngày 03/08:**

```
$ uv run python packages/engine/scripts/measure_chunk_embed.py --null
embedding                                     recall@1  tranh   top1 không hoà
bag-of-words dim=8 (đang chạy)                     6/6      2                2
bag-of-words dim=256                               6/6      2                2
NULL: vector hằng số (0 thông tin)                 6/6      2                0
NULL: băm cả câu (không cấu trúc cosine)           5/6      2                1
```

Một **vector hằng số — 0 bit thông tin** đạt `recall@1 = 6/6`, **bằng đúng** bản thật.

**Vì sao:** fence tự quyết **4/6 case** — sau khi lọc `tenant_id` + `section_role` thì chỉ còn **đúng
một** ứng viên, nên ranking không quyết định gì. 2 case còn lại vector hằng số thắng nhờ **hoà điểm rồi
ăn may thứ tự sort** (cột *"top1 không hoà"* = **0** chính là chỗ đó).

**Hệ quả phải nói thẳng:** `citation_accuracy` hiện **không phát hiện được hồi quy embedding**. Gateway
thật về mà embedding tệ hơn stub thì điểm vẫn `6/6`. Tức một trục của gate `AND` đang **không có răng**
trên bộ hiện tại — và điều đó làm ngưỡng `citation_accuracy = 0.95` đo một thứ khác với thứ tên nó gợi
ra.

> **Ba chỗ giữ ngưỡng, cho người recalibrate ở D16** (đã đếm, không phải một chỗ như dễ tưởng):
> `workbench:src/studio_workbench/builder.py:48-49` — **default param** của `create_dynamic_recipe`
> (`success_threshold: float = 0.9`, `citation_accuracy_threshold: float = 0.95`); và
> `workbench:…/builder.py:114` + `workbench:…/builder.py:192` — hai chỗ **hardcode** `ScorecardThreshold(success=0.9,
> citation_accuracy=0.95)` trong sample recipe. Đổi chỉ default mà quên hai chỗ hardcode là cách
> recalibrate ra hai bộ số cùng tồn tại.

**Sửa ở BỘ GOLDEN, không sửa ở embedding.** Cần case có **≥2 ứng viên cùng `tenant` + cùng
`section_role`** để ranking buộc phải chọn thật. Hiện chỉ **2/6** case có tình huống đó. Đây là yêu cầu
**bổ sung** cho golden-30 (§DE-4 / `callisto-golden-30-v1`), chủ **DE**, hạn **D15** — và nó là yêu cầu
*"có tranh chấp trong cùng fence"*, khác với các yêu cầu đã nêu (phủ 2 tenant, có refusal T1/T6,
`section_roles` đa dạng).

**Vì sao ghi giới hạn này VÀO bản freeze thay vì đợi sửa xong:** một hợp đồng khai đúng thứ nó chưa
chứng minh được thì **mạnh hơn**, không yếu đi. Không ghi thì đến D16 sẽ có người đọc `0.95` là bằng
chứng retrieval, và đó là **xanh-giả** — cùng lớp nguy hiểm với `refused` dương-tính-giả ở §6.

**Ghi công:** phép đo là của **AIE-1 (@TranBaDat2607)** trên `engine#15`
(`docs/design-notes/aie1-day11.md` §3). Nêu ra trên `evalhub#6` **trước khi** freeze đóng, và lời đề
nghị nguyên văn là: *"đừng ghi vào scorecard v1 rằng `citation_accuracy` chứng minh chất lượng truy
xuất — hiện chưa"*. Clause này là làm đúng điều đó. Đã tự chạy lại `--null` để xác nhận, không nhận ở
mức báo cáo.

## §4 · `no-trace-no-proof` — invariant đúng, và nó KHÔNG thuộc `score_case`

**Clause.**
- (i) từ-chối + **có run thật** + 0 citation ⇒ **PASS**. Đây là oracle F02 (GUIDE-C `:592`):
  *"the honest refusal: refused, cited nothing ⇒ **the case PASSES**"*.
- (ii) từ-chối + **0 event** ⇒ **FAIL**, cưỡng chế ở **tầng giữ `events`** (`run_smoke` /
  `EvalHarness.run`), đúng như `tenant_scope_ok` đang làm (`harness.py:119-120`, `if not events: return False`).
- (iii) chữ ký `score_case` **KHÔNG đổi** ở bản freeze này.
- (iv) hiện thực land **D16**.

**Vì sao invariant đúng là "không có trace quan sát được ⇒ FAIL", không phải "danh sách citation rỗng
⇒ FAIL".** `score_case` chỉ nhận `retrieved_citations: list[str]` (`harness.py:145`), nên **cấu trúc
mà nói** nó không phân biệt được *"chưa có run nào"* với *"có run, không trích gì"*. `tenant_scope_ok`
phân biệt được **vì nó nhận `events`**. Hai hàm cùng đọc một mặt quan sát mà một bên fail-closed, một
bên fail-open — **nguyên nhân là tầng, không phải cẩu thả**.

Fixture của chính quadrant này chứng minh khoảng cách: `test_determinism.py:113` dựng ca từ-chối bằng
`events=[_event([])]` — **một event, zero citation** = F02, **không** phải no-trace.

**Vì sao KHÔNG lật thẳng hôm nay** (bảng giá này tự nó là một phần của clause): lật sẽ đỏ
`test_refusal_success:241` · `test_cross_role_refusal_success:362` · `test_run_smoke_over_set:392`;
XPASS⇒FAIL bài `:276`; bảng điểm `cli` 5/5→3/5 · `e2e` quality 4/5→3/5 · `smoke_eval_d6` 6/10 tụt; và
**mọi số trong pack GATE-1 + note D10 thành cũ 24h sau khi submit**. Bản vá đúng chạm **4 consumer qua
3 repo** đúng ngày freeze.

**Pin không được dịch.** `test_citation_accuracy_zero_when_trace_empty_but_success_still_true:168-177`
**không được đụng** — GUIDE-C `:909`: *"This pin should not move. If your change turns it red, your
change is the thing that is wrong."*

## §5 · Invariant `Gate.threshold` ≡ `Recipe.scorecard_threshold`

**Clause.** `Scorecard.gate.threshold` PHẢI bằng **từng field** với `Recipe.scorecard_threshold` của
recipe đang được eval. Một scorecard gate theo ngưỡng **khác** ngưỡng recipe khai là **bug**.

**Hai class threshold giữ nguyên, KHÔNG hợp nhất.** `Recipe.scorecard_threshold: ScorecardThreshold`
(bút SWE) và `Gate.threshold: GateThreshold` (bút AIE-2) tồn tại song song. Lý do là **giá**, không
phải thẩm mỹ: `ScorecardThreshold` đang import ở **8 file** (7 test engine +
`studio_engine/__main__.py:22`), `GateThreshold` ở 2. Lợi ích ròng của hợp nhất hôm nay = **0**, vì
`compute_scorecard` nhận **hai float**, không nhận object (`compute.py:19-25`). Giá của dư = 0 file
phải sửa; giá của gọn = 10 file + một bump.

**Giá trị ngưỡng KHÔNG thuộc hợp đồng.** `golden_set_ref: str` +
`scorecard_threshold: {success, citation_accuracy}` freeze **là field**. Con số là **dữ liệu recipe**,
chủ **AIE-2**, hiệu chỉnh lại ở **D16** sau khi golden-30 chạy trên corpus thật. `workbench:…/builder.py:48-49`
giữ `success=0.9, citation_accuracy=0.95` tới đó.

Số đo thật để biết vì sao phải recalibrate: bộ 5 → `success 4/5 = 0.80`; bộ 10 →
`success 6/10 = 0.60`, `citation_accuracy` thật `0.833`. **Với mặc định hiện tại, một recipe TỐT cũng
FAIL cả hai trục** ⇒ demo *"sửa instructions tệ → FAIL → chặn publish"* chứng minh **số không**, vì
bản tốt cũng đỏ. Không hạ số hôm nay: mọi ngưỡng đang pin vào `ExtractiveFakeLLM`, và hạ bây giờ là
hiệu chỉnh theo một stand-in.

**`gate.verdict` freeze nguyên trạng:** `Literal["PASS","FAIL"]`, `Gate{threshold, verdict}`. Gate =
**AND** hai ngưỡng · toán tử **`>=`** · tầng **aggregate** (D-19/M1, GUIDE-C §4.1 `:280`). Ngưỡng phải
là **số thập phân tròn, chốt và ghi ra TRƯỚC khi dựng dataset** (GUIDE-C §3.2) — cấm
`threshold := giá trị mà lượt chạy vừa tính ra`.

## §6 · Carrier của `citations` — ⏳ CHỜ AIE-1

**Clause đề xuất.** Trong một run, **chỉ event `node_type == llm-step` được mang `citations`**; mọi
node khác `citations = None`. Chunk **đã truy xuất** nằm ở `outputs["chunks"]` của event
`kb-retrieve`, **không** ở `citations`.

**Trạng thái: ✅ ĐÃ ĐÓNG phía engine — 2026-08-04.** AIE-1 giao **cả ba lớp** trong `engine#15`
(merged `04:07:30`): **code** — `interpreter.py:304` gate `raw_outputs.get("citations") if node_type is
NodeType.LLM_STEP else None`; **contract** — `engine:docs/contracts/trace-citations.v0.md`; **test** —
bài "gỡ cổng ⇒ đỏ". Trước đó đã có `test_non_llm_events_have_zero_tokens_and_no_citations` khoá **hành
vi**; giờ có gate khoá **cấu trúc**.

Ghi đúng nhân quả: clause này được giao **vì** mutation M1 của bảng sweep — AIE-1 dẫn nó làm bằng chứng
chính, và commit mở đầu bằng *"Trả câu hỏi đang treo của AIE-2: `scorecard.v1.md` §6"*. Tức §6 không
phải một ask được đáp; nó là một **phép đo** đổi thành một **cổng**.

**Vì sao cần thành clause.** `citations_from_trace` gom **node-agnostic** (`harness.py:85-89`), nên nó
phân biệt retrieved/grounded **chỉ vì engine hôm nay tình cờ hành xử vậy** (`interpreter.py:265-271`
rẽ theo `isinstance(output, list)`). Rủi ro dư: bất kỳ node trả **dict** có key `"citations"` sẽ mang
citations vào trace — `condition`/`tool-call` đều trả dict. Tức bảo đảm hiện tại là **hành vi**, không
phải **cấu trúc**.

**🔴 Nợ CÒN LẠI, phía evalhub — CHƯA làm, và bản trước của doc này khai sai là đã làm.**
`citations_from_trace` vẫn **node-agnostic**: `harness.py:62` ghi thẳng *"gom `.citations` từ **mọi**
trace event, **không phụ thuộc `node_type`**"*, `:82` ghi *"siết theo node cụ thể **nếu cần**"* — tức
hoãn. Quét `src/`: **0 gate**.

Việc phải làm: siết `citations_from_trace` theo `node_type is NodeType.LLM_STEP` + thêm
`retrieved_chunks_from_trace` đọc `outputs["chunks"]`. Khi đó nghĩa của `citation_accuracy` do **luật
chấm** quyết, không do hành vi engine quyết — và bộ chấm không còn phụ thuộc việc engine giữ cổng.
**Chủ AIE-2, hạn D16.**

> **Đính chính (finding @DongAnh2704, 04/08).** Bản trước viết *"Lưới đỡ **đã có**: siết theo
> `node_type` phía evalhub"* — thì hoàn thành, cho một việc chưa làm. Nó ngược đúng `DEC-08` (§3.1) và
> ngược luật tự đặt trong bảng mutation. Nặng hơn: câu đó **đã lan** vào
> `kb:docs/contracts/trace-event.v0.md:237` — một hợp đồng đang xin freeze — nên đã báo DE gỡ.
> Bài học: **thì của động từ trong một clause là một khẳng định kiểm được**, không phải văn phong.

**`refused`: freeze seam, KHÔNG freeze công thức.** Hợp đồng khoá rằng output `llm-step` có key
`refused: bool` mang nghĩa *"agent không ground được câu trả lời từ thứ được đưa"*, và rằng **đổi công
thức phải báo trên #84 cùng ngày**. Không freeze công thức: `refused` đã đổi nghĩa **hai lần trong 4
ngày** (`not retrieved_chunks` → sentinel → `not citations`, `executors.py:264`) và đang tiến hoá đúng
hướng.

⚠️ **Breakpoint #14 — XANH-GIẢ, nguy hiểm hơn đỏ-giả.** `refused = not citations` cho dương-tính-giả:
một câu bịa trọn vẹn mà quên đóng ngoặc ⇒ `citations=[]` ⇒ `refused=True` ⇒ **SC-04 PASS dù agent đã
bịa**. Trên bài kiểm hàng rào, xanh-giả tệ hơn. Chủ đề xuất **AIE-1**, hạn **D17**, cùng leak-test.

## §7 · `outputs["chunks"]` — ⏳ CHỜ DE

**Clause đề xuất.** Với event `node_type == kb-retrieve`, `outputs` PHẢI là
`{"chunks": [<KbSearchResultItem đã model_dump(mode="json")>, …]}` — mỗi phần tử mang đủ
`chunk_id · text · score · tenant_id (UUID) · section_role`. Với 5 node còn lại, `outputs` giữ nguyên
`dict[str, object]` tự do.

**Đây KHÔNG phải đổi contract.** `TraceEvent.outputs` vẫn là `dict[str, object]`; `SCHEMA_VERSION`
**không** bump; không cần mini-RFC. Engine đã emit shape này từ D5 (`interpreter.py:265-268`) và **4
chỗ đang đọc**: `scripts/smoke_eval_d6.py:247,270` · `apps/studio/scripts/e2e_smoke_eval.py:265-271`
· `packages/kb/tests/test_spine_live.py:135`. Thiếu là **một dòng hợp đồng** — `trace-event.v0.md`
**§7 (bảng carrier)** khai `outputs` là *"⏸ hoãn S2"* / *"có trong schema, chưa điền"*, tức field đang
chở bằng chứng của bộ chấm thì hợp đồng khai là chưa quy định.

> Trích theo **§ + tên field**, không theo số dòng: bản kb#10 đang mở dịch dòng đó từ `:77` sang `:113`.
> Một trích dẫn theo số dòng qua repo khác là một trích dẫn sẽ mục — đúng lớp lỗi vừa nêu thành finding
> trên kb#10, nên không tự mắc lại.

**Trạng thái `outputs` — đo lại 2026-08-04, và nó đã đổi từ lần đo trước:**

| Nơi | kb `main` | nhánh kb#10 `day11/de-contract-freeze` |
|---|---|---|
| **§3** bảng field | `⏸ hoãn S2` | ✅ **DE đã sửa** → *"`outputs` \| ✅ điền thật (D11)"* |
| **§2** schema yaml | `outputs: obj?` dưới `# ── để trống tới S2 ──` | ❌ **còn nguyên** |

⇒ **F-5 còn mở, nhưng chỉ cho §2** — không phải cho cả doc. Trên nhánh kb#10 doc đang **tự mâu thuẫn
§2 ↔ §3**.

> Bản trước của mục này ghi *"đã verify trên HEAD kb#10: `outputs` **vẫn** `⏸ hoãn S2`"*. Câu đó **đúng
> lúc đo** và **sai sau đó vài giờ** — DE sửa §3 ở giữa. @DongAnh2704 bắt được khi review evalhub#7, và
> nêu đúng hệ quả: để nguyên thì chủ quadrant đọc sẽ tưởng **bị đòi làm lại việc đã làm**.
>
> Bài học đưa vào cách viết clause: **một câu trạng thái về repo khác phải đóng dấu thời điểm đo ngay
> trong câu đó**, không chỉ ở phần verify cuối doc — vì phần verify thì người đọc lướt qua, còn câu ask
> thì họ hành động theo. Cùng lý do §7 này trích theo **§ + tên field** thay vì số dòng.

DE cũng đã sửa drift `tenant: str` → `tenant_id: UUID` trong cùng PR (hàng `d13-align`, ghi công review
AIE-2).

**Vì sao cần:** biến leak-check từ **sanity theo slug** thành **chứng minh mức UUID**. Hôm nay
`_citation_tenant` cắt tiền tố chuỗi `chunk_id` (`harness.py:49-57`) — nhãn mềm, trùng được, sửa được.

**Tiền đề cũ đã RÚT.** `scorecard-v0.md:335-337` viết *"muốn kiểm leak mức UUID thì trace cần
`tenant_id` per-chunk → đổi contract → mini-RFC + 4/4 chữ ký"*. **Câu đó định giá quá cao và đã rút:**
dữ liệu đã có từ D5, trên đúng node. 0 bump, 0 mini-RFC.

**Rủi ro dư nếu không có clause:** shape `outputs` chưa là ràng buộc ⇒ đổi key `"chunks"` sẽ vỡ 4 chỗ
**im lặng**. Chủ clause DE, hạn D15.

## §8 · `recipe_hash` — PR riêng hôm nay

**Clause.** `Scorecard.recipe_hash: str | None = None`, kèm **luật an toàn phía consumer**: publish
coi `recipe_hash is None` là *"không verify được ⇒ từ chối"* (**fail-closed**). Vì fail-closed nằm ở
consumer, một field *optional* là đủ — **không cần required-add**, nên không bump.

Neo: ruling **D-24** (`02-MATRIX.md:284`) — *"Fix the schemas before Day 20, then write the tests. Add
`recipe_hash` to `Scorecard`"*, owner **AIE-2 (contract)**.

**Điểm yếu nói thẳng:** đây là **land một field chưa có producer**. `Recipe` hiện không có
`version`/hash (`recipe.py:79-94`), dù `wb.recipe_versions` đã tồn tại
(`workbench/.../schema.py:39`). Cách **suy ra giá trị** là quyết định chung với SWE (bút `Recipe`) —
chủ đề xuất SWE, hạn **D12**.

## §9 · 🔴 Nguồn nhãn tay cho `Judge.agreement` — CHẶN

Field **đích** đã có (`scorecard.py:19` `Judge.agreement`). Field **nguồn không tồn tại**: không có
chỗ nào trong workspace lưu *verdict của người* cho từng `actual`. Và hằng số **bị cấm** (§1).

⇒ **Mọi ô judge là `todo:` không có ETA cam kết được.**

**Chủ: AIE-2**, hạn **D18**, phụ thuộc **DE** cho phần giá trị.

> ### ⚠️ ĐÍNH CHÍNH chủ sở hữu — 2026-08-04 (không sửa clause, sửa metadata)
>
> Bản freeze ghi *"món **không tự đặt đáp án** — chủ **mentor**"*. Câu đó **sai về bản chất**: mentor
> **không tác động vào quá trình**, chỉ nhận kết quả và chạy để chấm. Một món gán cho người-không-hành-động
> thì **không bao giờ nhích** — nó là *"món bị bỏ im lặng"* khoác áo *"hoãn có chủ"*, đúng thứ nguy hiểm
> hơn cả việc không ghi.
>
> **Chủ đúng, suy ra từ chính `DEC-Q5` và §2.6 của tôi** — *"DE sở hữu **giá trị** (case + **nhãn tay** +
> tên bộ); AIE-2 sở hữu **nơi lưu + loader** và **luật khớp**"*:
>
> | Phần | Chủ |
> |---|---|
> | Định nghĩa `agreement` đo **cái gì**, format field nhãn tay, chỗ lưu (mở rộng `eval.golden_sets`) | **AIE-2** — bút `scorecard` |
> | **Sinh nhãn tay** cho case golden-30 | **DE** — bút golden-set (`DEC-Q5`) |
>
> Tôi **nhận món này**, không đẩy sang DE: phần chặn thật là *"đo cái gì và lưu ở đâu"* — đó là bút tôi.
> Phần của DE là giá trị, và nó đi cùng golden-30 (hạn D15) chứ không phải một việc mới.
>
> **Vì sao sửa được một doc đã `FROZEN` mà không cần mini-RFC:** clause của §9 (*"field nguồn không tồn
> tại ⇒ mọi ô judge là `todo:`"*) **không đổi một chữ**. Chỉ đổi **ai hành động** — metadata theo dõi,
> không phải điều khoản hợp đồng. Luật freeze chặn *rename · removal · required-add* trên **shape**
> (`contracts/__init__.py:5-12`), không chặn việc sửa một ô chủ-sở-hữu bị gán sai.

---

## Sổ chốt (append-only — cập nhật khi có thoả thuận, KHÔNG xoá dòng cũ)

| Ngày | Điều | Chốt ra sao |
|---|---|---|
| 03/08 (D11) | **`CaseResult.judge` nhận `None`** | `Judge \| None = None`; `None` = "không có judge chạy". Hằng số bị cấm (`judge.py:6-9` + INV-4). PR: contracts#1 (@Dozyboy mở, AIE-2 xác nhận với tư cách giữ bút). Không bump — xem dòng dưới |
| 03/08 (D11) | **Luật bump cho nới `required`→`optional`** | **Không bump**, điều kiện: đếm được **0 reader giả định non-null**. Đo: 0 reader / 4 constructor; `331→333 passed` đúng +2 test mới. Quy tắc `__init__.py:5-12` chỉ liệt kê 3 loại breaking ⇒ đây là **ca thứ tư** (tương thích dây, không tương thích reader), guard hiện có **không phát hiện**. ADR-D11-02 |
| 03/08 (D11) | **`citation_accuracy` nhánh từ-chối** | Per-case giữ `1.0` **là quy ước, có pin test**; aggregate **loại khỏi mẫu số**; render in `n/a`. Số: `0.90` báo vs `0.833` thật (+0.067, 3 case đỏ góp 1.00); `10×1.0 + 20×0.85 = đúng 0.90` ⇒ `>=` cho bản đáng FAIL lại PASS. Cách biểu diễn trong `Aggregate` → D16, chủ AIE-2 |
| 03/08 (D11) | **`citation_accuracy` đo FENCE, không đo TRUY XUẤT** (§3.1) | Null control của AIE-1 (`engine#15`), **đã tự tái lập**: vector hằng số **0 bit thông tin** đạt `recall@1 = 6/6`, bằng đúng bag-of-words thật; cột *"top1 không hoà"* = **0**. Vì fence tự quyết **4/6 case** (lọc `tenant_id`+`section_role` còn đúng 1 ứng viên), 2 case còn lại thắng nhờ hoà điểm. ⇒ `citation_accuracy` **không phát hiện được hồi quy embedding**; một trục của gate `AND` đang **không có răng**. Sửa ở **bộ golden** (cần ≥2 ứng viên cùng tenant+section_role; hiện 2/6), **không** sửa embedding. Chủ **DE**, hạn **D15**, gộp vào yêu cầu `callisto-golden-30-v1`. Ghi công AIE-1; nêu trước khi freeze đóng |
| 03/08 (D11) | **`no-trace-no-proof`** | Invariant đúng = *"không có trace quan sát được ⇒ FAIL"*, **không** phải *"citation rỗng ⇒ FAIL"*; cưỡng chế ở tầng giữ `events`, không ở `score_case` (chữ ký không nhận `events`). F02 (`GUIDE-C:592`) giữ nguyên: refused + có run + 0 citation ⇒ **PASS**. Hiện thực D16. xfail `test_smoke_runner.py:276` **đổi neo** sang ca `run_smoke` có `events == []`, giữ `strict=True` |
| 03/08 (D11) | **`Gate.threshold` ≡ `Recipe.scorecard_threshold`** | Giữ **hai** class (`ScorecardThreshold` 8 file vs `GateThreshold` 2 file), **không hợp nhất**; thay bằng **invariant** bằng-từng-field. Test do AIE-2 viết. Giá trị ngưỡng = **dữ liệu**, chủ AIE-2, recalibrate D16 |
| 03/08 (D11) | **Chữ ký + decision-log** | Theo **ADR-D11-01**: chữ ký thật = Approve trên PR; dấu vết ở `docs/decisions/scorecard.md` **cùng repo này**. Bỏ ý định làm bảng tự-điền trong file contract, và bỏ ý định làm `sig-<id>.md` per-người — tách theo **hợp đồng** đã giải quyết vấn đề "một người gõ hộ bốn dòng". **Đổi chỗ hai lần trong ngày, ghi lại cả hai:** ban đầu định gom vào `kit:docs/decision-log.md`; rồi theo khung kit#130 (`kit:docs/decisions/<contract>.md`); rồi kit#130 **closed** và lần lặp cuối của nó chốt *"kit stays pure index"* ⇒ nội dung về repo của bút, kit chỉ giữ `docs/decisions/README.md` làm index. DE (kb) và SWE (workbench) cũng đặt trong repo mình |
| 04/08 (D12) | **Sửa 2 ô chủ-sở-hữu gán cho `mentor`** — món F-6 (nguồn nhãn tay cho `Judge.agreement`) và M6 (quyền đổi marker `strict`) | Mentor **không tác động** vào quá trình, chỉ nhận kết quả và chạy để chấm ⇒ món gán cho người-không-hành-động **không bao giờ nhích**; nó là *"món bị bỏ im lặng"* khoác áo *"hoãn có chủ"*. Chủ đúng suy ra từ `DEC-Q5`/§2.6: **F-6 → AIE-2** (định nghĩa `agreement` đo gì + format + chỗ lưu) **+ DE** (sinh nhãn tay, cùng golden-30 D15); **M6 → AIE-2**, gỡ marker được ở D16 với điều kiện **viết ADR** + cửa sổ phản hồi (kit#84 uỷ quyền team tự quyết ⇒ *"your own authority"* nghĩa là *quyết một mình không có ADR*, không phải *thiếu một người để xin*). **KHÔNG cần mini-RFC:** 0 thay đổi trên `studio_contracts` shape, clause §9 (*"field nguồn không tồn tại ⇒ mọi ô judge là `todo:`"*) giữ nguyên chữ. Bỏ thêm cụm *"món không tự đặt đáp án"* vì chính cụm đó là phần sai — nó TỰ đặt đáp án được, bởi tôi. PR `evalhub#10` |
