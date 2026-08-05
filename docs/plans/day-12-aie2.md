# Plan Day 12 — AIE-2 · Scorecard skeleton render trống + playground-trace wireframe · Thứ Ba 04/08/2026

> **Viết lúc 16:30 ICT, không phải 09:00.** Nửa ngày đầu đã tiêu vào việc không có trong plan: 2 vòng
> finding của @DongAnh2704 trên `evalhub#10`/`#11` (`0fb0723`, `c2517b3`, `b898cf1`). Plan này là plan
> cho **phần còn lại của ngày**, và nó thừa nhận điều đó thay vì viết lại lịch giả từ sáng.

# Executive Summary

**Goal.** Land đúng một món đã hẹn trong hợp đồng **FROZEN** từ D11 và trùng đúng đề bài D12: bảng chấm
in `n/a` cho nhánh từ-chối + **khung scorecard render được khi CHƯA có golden-set thật**, không bịa một
con số nào. Kèm wireframe UX playground-trace. Đóng `evalhub#11`, đồng bộ con trỏ, đóng ngày.

**Neo đề bài.** `week-2/days/day-12.md` → **404** (`requirements` `main` = `c64a212e`, **2026-07-23**,
root tree không có `week-2/` — App. A.2). ⇒ Spec duy nhất là body `kit#88`: *"Soạn **scorecard skeleton
render trống** + playground-trace UX wireframe; **chưa có golden-set thật**"*. Bốn dòng DoD trên `#88`
là **DoD chung của nhóm** (canvas · graph-lint) — việc của SWE `#87`; chỉ **2 dòng** áp được cho mình:
`pytest happy+negative xanh` và `decision-log ghi nếu tụt nấc`.

**Điểm khớp quan trọng nhất.** `scorecard.v1.md` §DEC-04 phần 3 (đã FROZEN) tự hẹn: *"Render: bảng
người-đọc in `n/a` cho dòng từ-chối thay vì `1.00` — land **D12** (#88, đúng nội dung 'scorecard
skeleton render trống')"*. Đề bài hôm nay và món nợ D11 của mình là **cùng một món**. Không phải trùng
hợp may — đó là lý do nó là deliverable số 1 chứ không phải việc mới.

**Deliverables**

| # | Deliverable | Đường dẫn |
|---|---|---|
| 1 | `_render` in `n/a` nhánh từ-chối + test happy/negative | `src/studio_evalhub/cli.py:215` · `tests/test_smoke_runner.py` |
| 2 | Khung render **Scorecard trống** (`todo:`, 0 số bịa) | `src/studio_evalhub/cli.py` (hàm mới) + test |
| 3 | Wireframe UX playground-trace | `docs/design-notes/playground-trace-ux-d12.md` |
| 4 | `evalhub#11` merged (đồng bộ 4 chỗ F-6) | đã push `b898cf1` · chờ 3 approve |
| 5 | Comment kế hoạch `#88` + xử `#84` (quá hạn) | issue kit |
| 6 | PR bump con trỏ `packages/evalhub` trên kit | kit (main còn `5003627`, D11) |
| 7 | Note D12 | `docs/reports/daily-notes/2026-08-04-dholmes0207.md` |
| 8 | Plan này | `packages/evalhub/docs/plans/day-12-aie2.md` |

**Critical Path**

| Order / Giờ | Action | Depends on | Output |
|---|---|---|---|
| ~~1 · 16:20~~ | ~~Sửa 4 chỗ F-6 + push~~ | — | **XONG** `b898cf1` |
| ~~2 · 16:30~~ | ~~Reply DE: `DEC-Q5` + giờ cutover D13~~ | 1 | **XONG** — comment `#11` |
| 3 · 16:45 | Plan này + comment kế hoạch lên `#88` | — | Deliverable 5, 8 |
| 4 · 17:00 | **DEC-D12-01** (§1) rồi land Deliverable 1 | 3 | `n/a` + 2 test |
| 5 · 18:00 | Deliverable 2 — khung render trống | 4 | `todo:` render + 2 test |
| 6 · 19:00 | Deliverable 3 — wireframe (≤1 trang, ASCII) | — | docs |
| 7 · 19:30 | Xin 3 approve `#11` **sau khi** gộp hết sửa | 1 | Deliverable 4 |
| 8 · 20:00 | Xử `#84` (quá hạn) + tick **chỉ** ô chứng minh được trên `#88` | 3 | Deliverable 5 |
| 9 · 20:30 | Merge `#11` → PR bump con trỏ evalhub trên kit | 7 | Deliverable 6 |
| 10 · 21:00 | Note D12 + dọn branch kit local về `main` | 9 | Deliverable 7 |
| 11 · 21:30 | Verify clone sạch (App. B) | 9, 10 | Exit criteria |

Bước 4/5/6 **không** chờ bước 7. Nếu 3 approve không tới trước 21:00 → §6.

**Blocking Dependencies**

| Cần | Từ | Required response | Nếu thiếu |
|---|---|---|---|
| 3 approve trên `evalhub#11` | @Dozyboy · @TranBaDat2607 · @DongAnh2704 | Approve | Deliverable 1–3 vẫn land trên nhánh mới; `#11` carry sang D13, ghi vào note |
| `DEC-Q5` có/không | @DongAnh2704 | một chữ | **Đã có lưới**: `b898cf1` ghi *ĐỀ XUẤT, chưa xác nhận* ở cả 4 chỗ ⇒ non-blocking hôm nay, **blocking D16** |
| Giờ cutover KB thật (D13) | @DongAnh2704 | một mốc giờ | Mặc định: coi cutover có thể xảy ra **bất kỳ lúc nào sau 09:00 D13** ⇒ sáng D13 re-run trước khi làm gì khác |
| Cách suy ra giá trị `recipe_hash` | @Dozyboy | phương án | Contract §8 (`:343`) tự ghi hạn **D12**. Non-blocking: field đã optional, publish fail-closed khi `None` |

**Exit Criteria** — đo trong **clone sạch**, không đo working tree:

1. `uv run pytest packages/evalhub` = `43–45 passed`, **đúng 2 xfailed, 0 XPASS**
2. Ba số bảng điểm **không đổi**: `cli` 5/5 · `e2e` wiring 5/5 + quality 4/5 + RED-CHECK 2/2 · `smoke_eval_d6` 6/10
3. Con trỏ `packages/evalhub` trên kit `main` = `main` của evalhub · kit CI xanh
4. **0 con số bịa**: mọi ô chưa đo được in `todo:`/`n/a`, không in `0.00`
5. `compute_scorecard` **vẫn** `NotImplementedError` (mốc D16 — luật prep-vs-ship)
6. 0 ô DoD tick mà không chứng minh được; `#88` có comment kế hoạch, `#84` không còn im lặng

---

# §1 — Quyết định phải chốt hôm nay

## DEC-D12-01 · `_render` biết một case là từ-chối bằng cách nào?

- **Objective** — land `n/a` mà **không** đụng `float` của `SmokeResult.citation_accuracy` (3 renderer
  format `:.2f` sẽ `TypeError` với `None` — DEC-04 D11 đã đo).
- **Chặn thật:** `SmokeResult` (`harness.py:30-46`) có đúng 5 field — `case_id · expected · actual ·
  success · citation_accuracy`. **Không có** `refused`/`expects_refusal` ⇒ `_render(results)`
  (`cli.py:215`) **cấu trúc mà nói không biết** dòng nào là từ-chối. Đây là lý do `n/a` chưa land ở D11,
  và nó là một chặn thật, không phải quên.
- **Ba phương án:**
  - **(a) Thêm `expects_refusal: bool = False` vào `SmokeResult`** — **đề xuất**. Docstring của chính
    class đó (`harness.py:36-38`) **tự cho phép**: *"`SmokeResult` là kiểu riêng của quadrant (như
    `RunResult` của engine), đổi shape không cần mini-RFC"*. Nguồn giá trị đã có sẵn:
    `GoldenCase.expects_refusal` (`golden_case.py:87-109`), và `score_case` đã nhận `case` nên không
    phải luồn thêm tham số.
  - **(b) `_render(results, golden_set)`** — bỏ. Đẩy việc join lại cho **mọi** caller, và caller thứ ba
    (`e2e_smoke_eval.py:174`) đã tự dựng row type riêng có `expects_refusal` ⇒ chọn (b) là bắt hai chỗ
    làm cùng một join theo hai cách.
  - **(c) suy từ `actual`/`citation_accuracy == 1.0 and not citations`** — **bỏ, và bỏ dứt khoát**. Đây
    đúng lớp lỗi breakpoint `#14` (`refused = not citations` cho dương-tính-giả). Suy một cờ ngữ nghĩa
    từ một con số là cách tạo ra **xanh-giả**, thứ nguy hiểm hơn đỏ-giả trên bài kiểm hàng rào.
- **Evidence** — `harness.py:30-46` (5 field) · `harness.py:36-38` (giấy phép đổi shape) ·
  `golden_case.py:87-109` · `e2e_smoke_eval.py:341` (`"n/a*" if r.expects_refusal`) — **quy ước `n/a`
  đã tồn tại ở tầng render từ D10**, hôm nay chỉ là mang nó vào `cli`.
- **Owner / Required response** — mình quyết, **không cần ai trả lời** (kiểu riêng của quadrant).
- **Blocking?** — Non-blocking.
- **Artifact** — field mới + `_render` in `n/a` + 2 test (happy: dòng trả-lời vẫn in `0.00`–`1.00`;
  negative: dòng từ-chối in `n/a`, **và** `citation_accuracy` trên object vẫn là `float` 1.0).
- **DoD** — `citation_accuracy` **giữ `float`** · 3 renderer khác **0 dòng sửa** · pin test nêu tên
  DEC-04 + `#88` để một refactor không lặng lẽ trả `1.00` về bảng.

## DEC-D12-02 · "render trống" = khung có `todo:`, KHÔNG phải bảng có `0.00`

- **Objective** — quyết trước khi viết, vì hai cách đọc cho ra hai artifact khác nhau hẳn.
- **Đề xuất** — trống nghĩa là: **khung đủ cột + 0 dòng case + mọi ô aggregate in `todo:`**, kèm một
  dòng nói rõ *vì sao* trống (chưa có golden-set thật — `#88`).
- **Reasoning** — in `0.00` cho `success_rate` khi chưa đo là **cùng một lớp lỗi** với hằng số
  `Judge(agreement=1.0)` mà `judge.py:6-9` cấm và §1 contract khoá: một ô **không đo được** được điền
  một giá trị **đọc được thành đã đo**. `0.00` còn tệ hơn ở chỗ nó đọc thành *"đo rồi, và fail"* ⇒ ai
  xem demo sẽ tưởng gate đang chặn. Và `kit#134` (mở 07:40 hôm nay, có `role:aie-2`) nói đúng cùng
  chuyện ở mức thống kê: chỗ hỏng không nằm ở probe, nằm ở **bước từ "8/10" sang "80%"**.
- **Owner** — mình quyết. **Blocking?** — Non-blocking.
- **Artifact** — hàm render nhận `Scorecard | None`; `None` ⇒ in khung + `todo:` + lý do.
- **DoD** — `grep -c "0\.00"` trên output rỗng-set = **0** · test khoá đúng câu này.

## DEC-D12-03 · KHÔNG gọi `compute_scorecard` hôm nay

- **Đề xuất** — render đọc `Scorecard | None`, **không** gọi `compute.compute_scorecard`.
- **Reasoning** — `compute_scorecard` còn `raise NotImplementedError` (`compute.py:30`) và nó là mốc
  **D16** (`kit#108`). Ba lý do giữ nguyên: (1) luật prep-vs-ship — không ship deliverable D16 sớm;
  (2) GUIDE-C §3.2 đòi **ngưỡng literal phải có trước dataset**, mà dataset về D14–15; (3) land hôm nay
  làm `test_gate_blocks_on_fail` (`xfail(strict=True)`) **XPASS ⇒ FAIL**, trong lúc quyền đổi marker
  (M6) mới chỉ có ADR **dự kiến** viết ở D16.
- **DoD** — `compute.py` **0 dòng sửa** · `git diff -- src/studio_evalhub/compute.py` rỗng.

## DEC-D12-04 · `DEC-Q5` — không chờ thêm, đã có lưới

Đã thực hiện xong trong `b898cf1`: 4 chỗ ghi *ĐỀ XUẤT, chưa xác nhận* + điều kiện lật = DE chốt
`DEC-Q5`. Sổ chốt **append** dòng mới, không sửa dòng 04/08 cũ (append-only ⇒ xoá vết lỗi là xoá đúng
phần đáng học). ⇒ `DEC-Q5` từ **chặn** thành **có lưới**, và mọi việc còn lại của ngày đi tiếp được.

---

# §2 — Work items

## T1 · Comment kế hoạch lên `#88`

- **Objective** — luật nhóm: có kế hoạch buổi sáng trên issue ngày. Hôm nay muộn ⇒ comment phải nói
  thẳng *vì sao muộn* (2 vòng finding), không giả vờ đúng giờ.
- **Expected artifact** — comment nêu: 3 deliverable của mình · **4 dòng DoD là DoD nhóm, 2 dòng áp
  được cho mình** · giờ cắt 21:00.
- **DoD** — có nêu `day-12.md` 404 + `requirements` `c64a212e` (23/07) làm căn cứ, để người đọc biết
  spec là body issue chứ không phải file đề.

## T2 · Deliverable 1 — `n/a` nhánh từ-chối

- **Objective** — trả món DEC-04 phần 3 đúng ngày contract tự hẹn.
- **Reasoning** — xem DEC-D12-01. Món này nhỏ nhưng nó là **món duy nhất hôm nay có hợp đồng FROZEN
  đứng sau**; mọi thứ khác là khung.
- **Expected artifact** — `SmokeResult.expects_refusal` + `_render` + 2 test.
- **DoD** — `43+ passed, 2 xfailed, 0 XPASS` · 3 số bảng điểm không đổi · 3 renderer ngoài repo **0
  dòng sửa**.

## T3 · Deliverable 2 — khung render Scorecard trống

- **Objective** — đúng chữ trong `#88`: *render trống*.
- **Reasoning** — xem DEC-D12-02, DEC-D12-03. Giá trị thật của món này không phải cái bảng — mà là nó
  **khoá trước** hình dạng output trước khi có dataset, đúng luật ngưỡng-trước-dataset của GUIDE-C
  §3.2. Khi golden-30 về (D16) thì chỉ đổ số vào khung đã có test.
- **Expected artifact** — hàm render + 2 test (rỗng ⇒ `todo:` không có `0.00`; có `Scorecard` giả lập
  dựng tay ⇒ in đúng số của nó, **không** gọi `compute_scorecard`).
- **DoD** — `compute.py` 0 dòng sửa · 0 ký tự `0.00` trong output rỗng · docstring trỏ `#88` + DEC-D12-02.

## T4 · Deliverable 3 — wireframe UX playground-trace

- **Objective** — dòng thứ hai của `#88`, và là **cái duy nhất hôm nay chạm SWE/DE** ⇒ làm dạng ASCII
  ≤1 trang, không code, để nó đọc được như một đề nghị chứ không như một PR áp lên quadrant người khác.
- **Reasoning** — trace viewer là **D15, chủ DE** (`kit#100`); playground là **SWE** (`kit#102`). Nên
  artifact hôm nay phải là *"đây là thứ bộ chấm cần đọc được từ trace"*, không phải một UI. Neo vào
  thứ mình thật sự tiêu thụ: `citations_from_trace` (`harness.py:60`) · `tenant_scope_ok`
  (`harness.py:92`) · `outputs["chunks"]` · `refused`.
- **DoD** — ≤1 trang · nêu rõ **non-scope** (không dựng UI, không chạm workbench) · mỗi khối trên
  wireframe trỏ tới **một** field trace có thật hôm nay.

## T5 · Deliverable 4 — đóng `evalhub#11`

- **Objective** — 3 approve, và **gộp hết sửa trước khi xin**.
- **Reasoning** — `evalhub#5` đã mất approval một lần vì push muộn. Hôm nay đã push `b898cf1` **trước**
  khi có approve nào ⇒ 0 chữ ký bị dismiss. Từ giờ tới lúc merge: **không push thêm** vào nhánh đó;
  Deliverable 1–3 đi **nhánh khác** (`aie-2/d12-render-skeleton`).
- **DoD** — `#11` merged · 0 approval bị dismiss · Deliverable 1–3 không nằm chung nhánh với `#11`.

## T6 · Xử `#84` + tick DoD trên `#88`

- **Objective** — nudge quá hạn 05:34 gọi tên **cả 4 người** cho `#84`; im lặng khi kẹt là lỗi luật số 1.
- **Reasoning** — @TranBaDat2607 đã post bản tổng hợp *"D11 xong — 4/4 hợp đồng FROZEN"* lúc 06:49 ⇒
  căn cứ đóng đã có, chỉ thiếu người bấm. Nhưng đây là issue **nhóm**: mình comment xác nhận phần của
  mình (`scorecard` FROZEN + link 4 PR) và nói rõ mình không đơn phương đóng issue nhóm nếu chưa ai
  phản đối trong cửa sổ tới 21:00 — công bố kèm đường lùi, không xin phép.
- **DoD** — `#84` không còn im lặng · tick **chỉ** ô chứng minh được trên `#88` (2 dòng DoD của mình,
  **không** tick 2 dòng canvas/graph-lint của SWE).

## T7 · Deliverable 6 — bump con trỏ evalhub trên kit

- **Objective** — lệch con trỏ đã mất điểm **hai lần** (`kit#73` · `kit#76`/`#77`).
- **Đo hiện tại** (App. A.4): kit `main` ghi `packages/evalhub = 5003627` (D11), evalhub `main` đã đi
  tới `c2517b3` sau `#9`/`#10` ⇒ **đang lệch**; 5 con trỏ còn lại đã bump ở `kit#133`.
- **DoD** — bump **sau khi** `#11` merged (không bump vào commit nhánh) · verify bằng **clone sạch**,
  không bằng working tree.

## T8 · Note D12 + dọn branch local

- **Objective** — note có **số + chẩn đoán**; và dọn cái đang sai: branch kit local
  `aie-2/d11-decisions-designnote-mutations` đã merged (PR `kit#131`) nhưng vẫn đang checkout, behind
  `origin/main` **8 commit**.
- **DoD** — note có mỗi số kèm một câu "nên sao" · `## Contract / integration` trả đủ 3 câu (đổi gì ·
  ai ký · vỡ hay mở được gì) · **chỉ chữ + lý do** trong repo report (report-CI quét shape rò rỉ
  rubric) · branch kit về `main`.

---

# §3 — Ask gửi ai, nguyên văn

## DE — @DongAnh2704 · **đã gửi 16:3x** trên `evalhub#11`

Hai câu, gộp một comment vì DE đang online (comment của họ 16:07, tức 9 phút trước khi gửi):

1. **`DEC-Q5` xác nhận hay không** — kèm 3 nhánh hệ quả viết sẵn (chốt ⇒ caveat sập; chưa chốt ⇒ caveat
   đứng, *"chờ DE"* thành sự thật có bằng chứng; NO ⇒ mình giữ loader phía mình + tự sinh nhãn subset,
   ghi `DESCOPE`).
2. **Mốc giờ cutover KB thật D13** + **xác nhận thứ tự golden-30 sinh SAU corpus mới**. Đóng khung là
   câu hỏi **radar**, không phải câu hỏi lịch: nếu `smoke-5`/e2e vỡ sau cutover mà mình không biết giờ,
   số ở D16 bị đọc là hồi quy của bộ chấm.

## SWE — @Dozyboy · một món hạn **hôm nay** theo contract của mình

> `scorecard.v1.md:340-343` ghi: `recipe_hash` là **land một field chưa có producer** — `Recipe` không
> có `version`/hash (`recipe.py:79-94`) dù `wb.recipe_versions` đã tồn tại
> (`workbench/.../schema.py:39`) — và *"cách suy ra giá trị là quyết định chung với SWE, chủ đề xuất
> SWE, hạn **D12**"*. Hôm nay là D12. **Không chặn gì của mình** (field optional, publish fail-closed
> khi `None`), nên đây là nhắc một dòng, không phải đòi: cần **một phương án** suy ra hash, hoặc một
> câu "để D16" để mình ghi vào Sổ chốt kèm chủ + hạn mới.

## AIE-1 — @TranBaDat2607 · lật một dòng đã xong

> `F-4` trong decision-log ghi chủ **AIE-1**, hạn **D12**: clause *carrier `citations` chỉ trên
> `llm-step`*. Theo ghi chú của chính mình, `engine#15` **merged 04:07:30** với gate
> `interpreter.py:304` (`node_type is NodeType.LLM_STEP`) + `engine:docs/contracts/trace-citations.v0.md`
> ⇒ **phía engine đã đóng**. Việc của mình: xác nhận rồi **lật `F-4` sang ✅** trong decision-log, và
> ghi rõ phần **evalhub chưa có lưới** vẫn là của mình, hạn D16. Không để một dòng đã xong nằm im ở
> trạng thái chờ — đó là cách bảng theo dõi mất uy tín.

---

# §4 — Hoãn: chủ + hạn (0 món vô chủ)

| Món | Chủ | Hạn | Vì sao hoãn được |
|---|---|---|---|
| `compute_scorecard` thật + `EvalHarness.run` | AIE-2 | D16 (`kit#108`) | Ngưỡng phải có trước dataset (GUIDE-C §3.2); dataset về D14–15 |
| Golden-30 thật | DE (giá trị) + AIE-2 (loader) | D15–16 | Phải sinh **sau** corpus cutover D13 |
| Judge + cache + cap ≤100/ngày | AIE-2 | D18 (`kit#118`) | Nguồn nhãn tay chưa xác nhận (`DEC-Q5`) |
| Lưới evalhub cho carrier `citations` | AIE-2 | D16 | Phía engine đã đóng `04/08`; phía mình là test, không phải clause |
| Gỡ marker `strict` (M6) + ADR | AIE-2 | D16 | Chỉ XPASS khi seam land ⇒ chưa tới ngày |
| ADR cho luật bump `required→optional` | AIE-2 | D14 | Mentor không trả lời kiến trúc từ S2 ⇒ tự viết, không chờ |
| Cách suy ra `recipe_hash` | SWE | D12 → xin gia hạn D16 nếu im | Field optional + publish fail-closed |
| Confidence-interval cho mọi số scorecard (`kit#134`) | AIE-2 | D16 | Chưa có dataset đủ lớn để CI có nghĩa; nhưng **luật viết số** áp từ note hôm nay |

---

# §5 — Không làm hôm nay

Canvas React Flow / recipe validator / graph-lint (SWE `#87`) · doc-factory Callisto (DE `#85`) ·
refactor interpreter (AIE-1 `#86`) · `compute_scorecard` (D16) · golden-30 (D15–16) · judge (D18) ·
T1/T6 suite (D17) · eval-gate wiring (S3/D24) · trace viewer (DE, D15) · **không** hạ ngưỡng
`0.9/0.95` (hạ bây giờ là hiệu chỉnh theo `ExtractiveFakeLLM`, một stand-in).

---

# §6 — Fallback

| Nếu | Thì |
|---|---|
| 3 approve `#11` không tới trước 21:00 | Merge-blocked ≠ work-blocked: Deliverable 1–3 land nhánh riêng; `#11` carry D13, ghi vào note + comment `#11` nói rõ đang chờ ai |
| DE không trả lời `DEC-Q5` | Lưới đã có (`b898cf1`). Note ghi *"ĐỀ XUẤT, chưa xác nhận"* — **không** báo là đã chốt |
| DE không cho giờ cutover | Mặc định coi cutover có thể xảy ra bất kỳ lúc nào sau 09:00 D13 ⇒ D13 re-run e2e+smoke **trước** khi làm việc khác |
| Hết giờ | Cắt theo thứ tự: Deliverable 3 (wireframe) → 2 → 1. **Không cắt** Deliverable 1: nó có contract FROZEN đứng sau |
| `n/a` làm đỏ một test ngoài evalhub | Hoàn `SmokeResult` về 5 field, chuyển sang phương án (b) của DEC-D12-01, ghi vào Sổ chốt vì sao (a) không đi được |

---

# §7 — Checklist cuối ngày (đo được)

- [ ] `uv run pytest packages/evalhub` = `43+ passed, 2 xfailed, 0 XPASS`
- [ ] `git diff -- src/studio_evalhub/compute.py` **rỗng**
- [ ] Output render rỗng-set: `grep -c "0\.00"` = **0**
- [ ] 3 số bảng điểm không đổi (App. B.2)
- [ ] Con trỏ `packages/evalhub` trên kit `main` = evalhub `main`; kit CI xanh
- [ ] `#88` có comment kế hoạch + tick **chỉ** 2 ô của mình
- [ ] `#84` không còn im lặng
- [ ] Note D12 tồn tại, mỗi số kèm một câu "nên sao"
- [ ] Branch kit local về `main`, working tree sạch

---

# §8 — ĐÃ XẢY RA (ghi lúc đóng ngày — plan-vs-actual)

| Plan nói | Thực tế |
|---|---|
| T2 `n/a` + 2 test | ✅ `evalhub#12` `bbe9f18` — **9** test mới, không phải 2 |
| T3 khung trống | ✅ `render.py` mới (plan nói đặt trong `cli.py` — tách module vì nó có 2 nhánh + hằng số riêng) |
| T4 wireframe | ✅ `docs/design-notes/playground-trace-ux-d12.md` |
| T5 đóng `#11` | 🟡 chờ Approve (CI xanh) — **và** phải push thêm `50647d7` vì DE xác nhận `DEC-Q5` giữa ngày |
| T1/T6 comment `#88`/`#84` | ✅ |
| T7 bump con trỏ | ⏸ **đúng thứ tự**: chờ `#11`+`#12` merge trước |
| T8 note + dọn branch | ✅ `report#46` · kit local về `main` |
| DEC-Q5 "non-blocking, có lưới" | ❗ **DE xác nhận CÓ lúc 09:42Z** — caveat sống **74 phút**, phải lật lại đủ 4 chỗ |

**Ba thứ plan không đoán được, và cả ba đều đắt hơn phần đoán được:**

1. **`SmokeResult` không có cờ nhánh.** Plan (DEC-D12-01) đoán đúng là có chặn, nhưng chưa thấy hệ quả
   thứ hai: thêm field thứ 6 làm `test_equality_actually_discriminates` — bài khai *"đi qua **mọi**
   field"* — **hết đúng mà không đỏ**, vì danh sách là gõ tay. Sửa thành đối chiếu cơ khí với
   `model_fields`. *Bài học:* mỗi lần thêm field vào model có test "mọi field", hỏi test đó cưỡng chế
   bằng **chữ** hay bằng **code**.
2. **Chính caveat của mình hết đúng trong ngày.** Plan viết luật *"prep phải có điều-kiện-huỷ"* nhưng
   không có luật cho *"caveat đã hết đúng"*. Bổ sung: **một caveat hết đúng cũng là một dòng trạng thái
   sai** — lật ngay, và giữ cả 3 trạng thái trong sổ append-only.
3. **DE đóng phần lớn rủi ro D13 giúp mình, bằng một quyết định đặt tên.** Golden draft dùng tiền tố
   `HB-` ⇒ additive với `SC-01..SC-10`. Plan xếp D13 là *"ngày rủi ro nhất tuần"*; sau khi đọc file
   draft của DE thì rủi ro thu hẹp còn **`chunk_id` của corpus cũ**. *Bài học:* đọc artifact của
   upstream **trước** khi định giá rủi ro của mình — rẻ hơn nhiều so với chờ tới lúc nó vỡ.

**Đo lệch một chỗ, ghi lại:** baseline định so với `333 passed` của D11 → suýt báo *"tụt 24 test"*. Thật
ra Postgres chưa lên (`56 skipped`). Phải đo baseline **cùng phiên** bằng `stash`/`pop` mới nói được câu
"0 hồi quy". Con số đúng: `300 → 309`.

---

# Appendix

## A — Ground truth (đo 04/08, 16:16–16:40 ICT)

**A.1 · Baseline evalhub** — `uv run pytest packages/evalhub -q` → `41 passed, 1 skipped, 2 xfailed`
(0.57s). Skip **duy nhất**: `test_scorecard_roundtrip.py:61` — `STUDIO_DATABASE_URL_ADMIN not set`
(cần `docker compose -f docker-compose.test.yml up -d`), tức **skip do môi trường, không do diff**.
Chạy bằng `python -m pytest` **thất bại** ở `conftest.py:18` (`ModuleNotFoundError: pytest_asyncio`)
⇒ luôn dùng `uv run`.

**A.2 · Đề bài** — `requirements` `main` = `c64a212e` (`2026-07-23T11:19:40Z`); root tree =
`00-orientation · week-1 · README.md · nda-denylist.sh · .pre-commit-config.yaml · .gitignore`.
**Không có `week-2/`** ⇒ `week-2/days/day-12.md` 404. Đây là **ngày thứ hai liên tiếp** đề bài không
tồn tại (D11 cũng vậy).

**A.3 · `evalhub#11`** — `OPEN`, `reviewDecision = REVIEW_REQUIRED`, `mergeable = MERGEABLE`, mảng
`reviews` **rỗng** ⇒ DE để lại **issue comment**, *không phải* review chính thức ⇒ theo ADR-D11-01
(chữ ký thật = Approve) thì PR này có **0 chữ ký**. CI: `ci/test-reconstructed` SUCCESS ·
`TTS deep-facts` SUCCESS ×2 · `ci/lint-shallow` SKIPPED. Mặt tốt: 0 approve ⇒ push `b898cf1` **không
dismiss** gì.

**A.4 · Con trỏ submodule** — kit `main` (`64dd4d7`): `docs/reports 9afade2` · `contracts 79edfb7` ·
`engine 971e336` · **`evalhub 5003627`** · `kb 93b97c6` · `workbench 8d0b33b`. evalhub `main` đã ở
`c2517b3` sau `#9`/`#10` ⇒ **chỉ con trỏ evalhub lệch**. Branch kit local
`aie-2/d11-decisions-designnote-mutations` (PR `kit#131` đã merged) đang behind `origin/main` **8**.

**A.5 · Issue** — `kit#83` (D11 AIE-2) `CLOSED` 07:54Z ✅ · `kit#84` (D11 nhóm) **`OPEN`**, nudge quá
hạn 05:34Z gọi tên cả 4 người, @TranBaDat2607 tổng hợp *"4/4 FROZEN"* 06:49Z · `kit#134` mở 07:40Z có
`role:aie-2` (confidence intervals) · `kit#88`/`#89` là issue D12.

**A.6 · Chỗ `n/a` đã tồn tại** — `e2e_smoke_eval.py:341`: `acc = "n/a*" if r.expects_refusal else
f"{r.citation_acc:.2f}"`, chú thích ở `:407`. ⇒ quy ước có từ D10 ở **một** renderer; `cli.py:215`
chưa có, và đó là khoảng cách hôm nay đóng.

**A.7 · Bề mặt spec còn `NotImplementedError`** — `compute.compute_scorecard` (`compute.py:30`) ·
`EvalHarness.run` (`harness.py:203`). Cả hai là mốc **D16**, **không** phải hôm nay.

## B — Verification

**B.1 · Chạy** — `uv run pytest packages/evalhub -q -rs` (luôn `uv run`, xem A.1).

**B.2 · Ba số bảng điểm** — `cli` 5/5 · `e2e` wiring 5/5 + quality 4/5 + RED-CHECK 2/2 ·
`smoke_eval_d6` 6/10. Đổi một trong ba **mà không giải thích được** = hồi quy.

**B.3 · Render GFM trước khi push doc** (bài học nit-2 D12 — blockquote dài cắt câu; và F3 vòng trước —
blockquote chèn giữa bảng làm vỡ 4 dòng):

```bash
jq -Rs '{text:.,mode:"gfm"}' <file>.md | gh api -X POST /markdown --input - > /tmp/o.html
grep -o "<table" /tmp/o.html | wc -l     # phải khớp số bảng thật
grep -o "|" /tmp/o.html | wc -l          # pipe còn lại phải nằm TRONG <code>
```

Đo cho `b898cf1`: `scorecard.v1.md` 5 `<table>`, 4 pipe (đều trong `<code>`: `Judge | None`) ·
`decisions/scorecard.md` 4 `<table>`, 6 pipe (trong `<code>`) · `aie2-day11.md` 4 `<table>`, 0 pipe.

**B.4 · Clone sạch** — verify Deliverable 6 bằng `git clone --recursive` rồi kiểm con trỏ, **không**
bằng working tree: working tree luôn "thấy" thứ người clone không thấy (đúng lớp lỗi đã làm pack
GATE-1 của DE vô hình).

## C — Đã làm trước khi plan này tồn tại (16:00–16:40)

| Giờ | Việc | Bằng chứng |
|---|---|---|
| ~14:00 | `#9` `#10` merged (đồng bộ bảng chữ ký · gỡ 2 món gán mentor) | `0fb0723` · `7039383` |
| 16:07 | DE comment `#11`: nit-2 fixed, finding-1 *fix một nửa* | `#11` comment |
| 16:35 | Đồng bộ **4** chỗ (DE nêu 2) + append Sổ chốt, không sửa dòng cũ | `b898cf1` |
| 16:4x | Comment `#11`: bảng 4 chỗ + 2 câu hỏi cho DE (`DEC-Q5` · giờ cutover) | `#11` comment |

**Bài học ghi ngay, không đợi note:** vòng đầu tôi sửa `decisions` + `design-note` mà bỏ
`contracts/scorecard.v1.md` — **file FROZEN, thẩm quyền cao nhất, vẫn đọc như đã chốt**. Một trạng
thái *"chưa chốt"* phải đúng ở **mọi** file nêu nó; chỗ lệch còn lại luôn là chỗ người đọc sẽ tin.

## D — Lưu file

Plan này ở `packages/evalhub/docs/plans/day-12-aie2.md` — **cùng repo bút `scorecard`**, cùng chỗ
`day-11-aie2.md`. Không đặt ở kit: kit giữ **index** (`docs/decisions/README.md`), nội dung về repo của
bút (chốt D11, ADR-D11-01).

**KHÔNG commit — và đây là chủ ý, không phải quên.** `.gitignore:17` ignore `docs/plans/` với đúng lý
do đã trả giá: *"Plan làm việc cá nhân — không thuộc scope chấm. Đã từng bị `git add docs/` quét vào
`evalhub#7` (+937 dòng) rồi phải gỡ"*. `git ls-files docs/plans/` = **rỗng** ⇒ `day-11-aie2.md` cũng
local-only. Plan là **prep**, và luật prep-vs-ship nói prep sống ở local, không mở PR deliverable.
⇒ Kiểm tra trước mỗi lần `git add`: `git check-ignore -v docs/plans/*.md` phải có hit.
