# Plan Day 19 — AIE-2 · Cost-lineage: UI-test đọc `cost` từ trace (không tự tính lại) + failure-mode eval · Thứ Năm 13/08/2026

> **Issue:** `kit#123` (con, AIE-2) dưới `kit#124` (cha, cả nhóm) · **Repo WRITE:** `agentcore-studio-evalhub` · kit READ
> **Vai:** **mặt đọc**, không phải chủ công. Chủ công cost-lineage là DE (`kit#120`); nguồn số là emit (AIE-1, `kit#121`).
> **Spec:** `week-2/days/day-19.md` **404** (ngày thứ chín liên tiếp — `docs/requirements` chỉ có `week-1/` + `00-orientation/`) ⇒ `#123` là spec thẩm quyền duy nhất.

---

# Executive Summary

Ô DoD của hôm nay đọc rất dễ — *"cost cùng-1-số khớp UI-test↔trace"* — và đó chính là vấn đề. **Với
trạng thái đo được sáng nay, ô đó đóng được trong ba phút bằng một bài test luôn xanh, và không ai
phát hiện ra.** Lý do nằm ở một con số:

```text
interpreter.py:73   _NO_COST = 0.0
interpreter.py:438  cost=_NO_COST,        # MỌI TraceEvent, MỌI node, MỌI run
```

`cost` của mọi event trong toàn hệ thống hôm nay là **hằng số 0.0**. Một bài khẳng định
*"số ở UI-test bằng số ở trace"* sẽ xanh khi mặt đọc **đọc đúng**, xanh khi mặt đọc **tính lại từ
tokens**, xanh khi mặt đọc **trả hằng số 0**, và xanh cả khi mặt đọc **không đọc gì**. Bốn cài đặt
khác nhau, trong đó ba cái sai, cho cùng một kết quả xanh. Đây đúng lớp lỗi `F-6` (`no_leak` trên tập
rỗng, D17) và `refused`-default (D15) đã cắn nhóm hai lần — lần này nó nằm ngay trên ô DoD.

**Việc thật của ngày không phải làm cho ô DoD xanh; nó là làm cho ô DoD *có thể đỏ*.**

## Bốn số làm nền

| Đo | Kết quả | Nghĩa |
|---|---|---|
| `cost` trong trace | **0.0 mọi event** — `_NO_COST` viết chết ở `interpreter.py:73` | Mọi phép so "cùng-1-số" hôm nay là `0.0 == 0.0` |
| `tokens` trong trace | **THẬT** từ 12/08 — `executors.py:362`, `Tokens(prompt=len(prompt.split()), completion=len(answer.split()))` (engine `ec75541`, PR#24 **merged**) | Nguồn giá đã có, đơn giá đã có, **chỉ thiếu bước áp giá** |
| Bề mặt cost ở evalhub | **0** — `run_report.py:219` SELECT cột `cost`, `:256` map vào `TraceEvent.cost`, rồi **vứt**. `render.py`/`harness.py`/`compute.py`: 0 lần nhắc `cost` | *"UI-test đọc cost từ trace"* hôm nay chưa có **bề mặt nào để đọc** |
| Bề mặt cost ở workbench | **0** lần nhắc `cost` trong `packages/workbench/` | Playground trả `score` không mang cost; `apps/web` tự cộng lấy ở client |

## Trạng thái chuỗi cost-lineage, đo từng mắt

```text
  tokens THẬT          áp giá             lưu           mặt đọc
 ─────────────    ───────────────    ───────────    ──────────────
 executors.py  ──▶   ✗ KHÔNG CÓ   ──▶ cost = 0.0 ──▶ evalhub:  ✗ chưa có bề mặt
 (AIE-1, xong)      (_NO_COST)                       kb:       ✓ kb#22 (OPEN)
                                                     web:      ✓ TraceViewer (tự cộng)
```

Mắt gãy là **áp giá tại emit**, và nó **không nằm trong tay ai của hôm nay**: bảng đơn giá `cost_of`
sống ở `kb` (`kb#22`), interpreter sống ở `engine`, và `.importlinter` xếp 4 quadrant là **sibling**
⇒ engine không import được kb. Đường duy nhất là `cost_of` land ở `contracts` (DE gọi là **Q-A**, cần
PR của chủ `contracts`). Chuỗi chặn: **Q-A → AIE-1 nối → cost ≠ 0 → mọi mặt đọc có số thật.**

⇒ **Ô DoD "cùng-1-số" đóng được ở phần ĐƯỜNG ĐỌC, không đóng được ở phần SỐ THẬT.** Nói đủ hai vế là
điều kiện của §7; nói một vế là báo cáo sai.

## Điều đáng ghi nhất, tìm ra khi kiểm nền: **"cùng-1-số" đã sai rồi, chỉ chưa ai đo**

Ba mặt đọc hôm nay in cost ở **ba độ chính xác khác nhau**, và một mặt cộng dồn theo **luật khác**:

| Mặt | Nguồn | Luật cộng | In ra |
|---|---|---|---|
| cost table CLI (DE, `kb#22`) | `obs.trace_events` | `round(sum(cost), 6)` | `{:>12.6f}` |
| TraceViewer (SWE, `apps/web`) | `events[]` của response | `reduce((s,e)=>s+e.cost, 0)` — **không làm tròn** | `toFixed(4)`, và `0 ⇒ "chưa đo"` |
| e2e smoke table (`apps/studio`) | `RunResult.events` | không cộng | `{:<6.2f}` |

Đo trực tiếp trên một run 6 node có 3 bước LLM (37/12 · 211/63 · 1290/417 token, đơn giá của `kb#22`):

```text
per-event cost : [0.000291, 0.001578, 0.010125, 0.0, 0.0, 0.0]
JS reduce      : 0.011994000000000001     ← TraceViewer
round(sum, 6)  : 0.011994                 ← cost table CLI
                 0.011994000000000001 == 0.011994  →  False
```

**Hai mặt đọc, cùng một trace, hai con số khác nhau** — và cả hai **hiển thị giống hệt** (`toFixed(4)`
ra `"0.0120"`, `.6f` ra `"0.011994"`; không ai nhìn thấy đuôi `...001`). Bất biến `cost` ở UI test ==
trace == dashboard (`umbrella-contract.md:131`, *"lệch = fail"*) **đã** hỏng ở tầng giá trị, và nó vô
hình ở tầng hiển thị. Không bài test nào trong workspace hôm nay chạm tới chuyện này.

Cùng phép đo còn lộ hai lỗ nữa, cả hai **chỉ nổ vào ngày cost thành số thật**:

1. **`{:<6.2f}` ở `e2e_smoke_eval.py:250` in một cost có thật thành `0.00`.** `cost_of(37, 12) =
   0.000291` → `f"{0.000291:<6.2f}"` → `"0.00  "`. Bảng money-shot của demo sẽ nói *run này tốn 0
   đồng* trong khi trace ghi có tốn. Đúng lớp lỗi `DEC-D12-02` cấm ở tầng render (*"`0.00` đọc thành
   đã đo, và bằng 0"*), chỉ khác chiều: ở đây `0.00` là **đã đo mà bị làm tròn mất**.
2. **`fmtCost` (`TraceViewer.tsx:49`) sẽ nói dối theo chiều ngược lại.** `cost === 0 ? "chưa đo"` hôm
   nay **đúng** (mọi cost là 0 vì chưa nối). Ngày cost thành thật, node `kb-retrieve`/`tool-call` phát
   `Tokens(0, 0)` ⇒ `cost_of = 0.0` ⇒ một số **đã đo và đúng bằng 0** sẽ hiển thị là **"chưa đo"**.
   Cùng một dòng code, hôm nay đúng, mai sai, và cái làm nó sai là **việc của người khác land**.

Đây là finding cho SWE (ask ③), không phải việc AIE-2 tự vào sửa — `DEC-D15-03` đã chốt luật đó và
`kit#74` chấm kỷ luật ranh giới quadrant.

## Ô DoD nào đóng được thật

| Ô DoD (`#123`/`#124`) | Đóng được? | Bằng gì |
|---|---|---|
| `Cost cùng-1-số khớp UI-test↔trace (tái lập)` | ⚠️ **một nửa** | **Đóng được:** đường đọc — evalhub có bề mặt cost, đọc từ trace đã bền hoá, chứng minh **không tự tính lại** bằng fixture bất đối xứng nơi `cost` **cố ý mâu thuẫn** `tokens`. **Không đóng được:** một con số đến từ một run **được áp giá thật** — emit vẫn ghi `0.0` (chủ: Q-A + AIE-1 `#121`) |
| `hardening happy-path` | ✅ | Đường `run_report` CLI là happy-path của quadrant này: fail-closed cho mọi nhánh mới (rỗng · trộn `run_id` · trộn `tenant_id` · `cost` NULL), + trả nợ `__all__` để bề mặt công khai import được từ fresh clone |
| `failure-mode list nhìn đầu (honest-TODO)` | ✅ | Design-note **của phía eval** — 7 mode DE đã ghi là của phía cộng dồn; phía đọc/chấm có mode riêng mà danh sách kia không nhìn thấy |

## Ranh giới tự áp cho ngày

1. **Không tính `cost` từ `tokens` ở bất kỳ đâu trong `studio_evalhub`.** Kể cả khi ra đúng số. Lý do
   không phải khẩu vị: hai nơi tính giá thì ngày đơn giá đổi một chỗ, ba mặt lệch nhau mà **không mặt
   nào biết mặt nào đúng**. `trace.py:3-5` và `kb#22 §4.1` nói cùng câu đó bằng hai giọng.
2. **Không đụng `studio_contracts`.** Cost không phải trục gate; nhét nó vào `Aggregate`/`Scorecard`
   là mời người sau gate lên một con số đang bằng 0.
3. **Không vào `apps/web` hay `packages/workbench`.** Hai finding ở trên đi bằng ask, không bằng commit.
4. **Không báo cáo `0.0` như một phép đo.** Hai trạng thái phải phân biệt được trong chính output:
   *chưa nối giá* · *đã đo, bằng 0*. (*lệch nguồn giá* là phép kiểm của DE — cần đơn giá, xem
   `DEC-D19-05`.)

---

# §1 — Nền đã kiểm, không giả định

## Trạng thái pointer (kiểm 13/08 đầu ngày)

```bash
git -C . rev-parse HEAD                     # acf8ecf  (kit#150 đã merge)
git submodule status                        # 9/9 sạch, không tiền tố +/-
git -C packages/evalhub log --oneline -1    # afe35a5 (evalhub#20, merged D18)
uv run pytest packages/evalhub -q           # 176 passed, 1 skipped
uv run mypy packages/evalhub                # no issues, 34 files
```

**Nhưng 9/9 sạch KHÔNG có nghĩa là khớp `main` của repo con.** Đo riêng từng con trỏ so với
`origin/main` của chính nó:

| Submodule | Con trỏ ở kit | `origin/main` của repo con | Lệch |
|---|---|---|---|
| `packages/evalhub` | `afe35a5` | `afe35a5` | ✅ khớp |
| `packages/kb` | `0194199` | `0194199` | ✅ khớp |
| `packages/engine` | `62773ba` (D17) | `bfa19cc` (**D20** merged) | ❌ sau **3 merge** |
| `packages/workbench` | `6badd84` (D17) | `04ca988` (D18 publish/rollback) | ❌ sau 1 merge |
| `apps/studio` | `0352176` | `db9ec90` (D18 trace-writer tenant-bind) | ❌ sau 1 merge |

⇒ **D18 đã đóng ở kit** — `kit#150` **MERGED** (`acf8ecf`), `kit#118` **CLOSED**, ba con trỏ của
mình (kb · evalhub · docs/reports) khớp `main`. Ba con trỏ còn lệch (`engine` · `workbench` ·
`apps/studio`) là việc của người khác, **không** chặn D19 — nhưng xem cảnh báo dưới đây.

⚠️ **Con trỏ `engine` lệch là rủi ro ĐO của chính D19, không phải chuyện của người khác.** kit trỏ
`62773ba` (tokens **= 0**), `origin/main` của engine ở `bfa19cc` (tokens **THẬT**, `ec75541`). Đo cost
khi chưa bump ⇒ `Σtokens = 0` ⇒ phân loại ra *"đã đo, bằng 0"* (`priced=True`) — **ngược hoàn toàn**
sự thật (*chưa nối giá*, `priced=False`). Vào **T0a**: bump `packages/engine` trước khi đo, hoặc ghi
rõ mọi số đọc trên con trỏ cũ.

## Trạng thái ba mắt của chuỗi cost — đo từng mắt, không suy

```bash
# 1. Emit có áp giá chưa
git -C packages/engine grep -n "_NO_COST" origin/main -- src/
#   interpreter.py:73   _NO_COST = 0.0
#   interpreter.py:438  cost=_NO_COST,

# 2. Tokens đã thật chưa
git -C packages/engine show origin/main:src/studio_engine/executors.py | grep -n '"tokens"'
#   362:  "tokens": Tokens(prompt=len(prompt.split()), completion=len(answer.split())),

# 3. evalhub có bề mặt cost nào không
grep -rn "cost" packages/evalhub/src/studio_evalhub/{render,harness,compute}.py | wc -l   # 0
grep -rn "cost" packages/workbench/src packages/workbench/*.py | wc -l                    # 0
```

**Đọc cho đúng vế (1):** đây **không** phải "AIE-1 quên". `engine` đã ở **D20** và PR D19 của họ
(`ec75541`) nói thẳng lý do: họ giao `tokens` — *"DE's cost-lineage sink was pricing everything at
zero"* — và **không** tự đặt bảng giá vào interpreter, vì `§4.1` cấm hai nơi tính giá. Bảng giá phải
land ở `contracts` trước. Tức mắt gãy có chủ, có lý do, và **không gỡ được từ trong evalhub**.

## `kb#22` — bản cộng dồn của DE: **đã review 2 lượt, DE đã vá, đang chờ vòng 3**

Đọc `origin/day19/de-cost-lineage` (**532 dòng**, 4 file, head `7ff361c`). Ba thứ AIE-2 phải biết
trước khi viết một dòng:

```python
# studio_kb/cost.py
PROMPT_RATE_PER_1K = 0.003
COMPLETION_RATE_PER_1K = 0.015
def cost_of(t): return round(t.prompt/1000*0.003 + t.completion/1000*0.015, 6)

def aggregate_run_cost(events) -> RunCost:
    ...  # raise nếu rỗng / trộn run_id / trộn tenant_id
    cost=round(sum(e.cost for e in events), 6)   # CỘNG cost đã lưu — KHÔNG cost_of (§4.1)

def price_mismatches(events): return [e.event_id for e in events if e.cost != cost_of(e.tokens)]
```

**Luật cộng của DE là `round(sum(...), 6)`.** Mọi mặt đọc muốn "cùng-1-số" phải cộng **đúng luật đó**.
Đó là hằng số dùng chung mà **không có cơ chế nào cưỡng chế** — xem `DEC-D19-03`.

**Ba finding đã đo được trên `kb#22` — ĐÃ GỬI, ĐÃ ĐƯỢC VÁ.** Giữ lại vì chúng là lý do hình dạng
của T2/T4, không phải vì còn phải làm. DE vá ở `71c25d6` (*"F1 tautology→AST-scan, F2 nối
`price_mismatches`"*) + `7ff361c`. Lượt 2 mở **một finding mới**: bài AST thay thế mang đúng bệnh của
bài nó thay — **xanh im lặng khi ngừng canh** (không assert nó quét trúng file nào). Đang
`CHANGES_REQUESTED`, chờ DE:

1. **`F-7` của DE bất khả thi bằng chính hợp đồng layering.** `cost-lineage-d19.md` §4 ghi cách vá
   `F-7` là *"AIE-2/SWE phải gọi reader của DE"*. `.importlinter` xếp `studio_kb | studio_engine |
   studio_workbench | studio_evalhub` **cùng một layer** ⇒ `studio_evalhub` **không import được**
   `studio_kb.cost`. `make lint` sẽ chặn. Vá đó không thực thi được, và nó là vá của mode nguy hiểm
   nhất trong bảng (mặt đọc tự nhân tokens×giá).
2. **`test_cung_1_so_moi_mat_doc_cung_tong` là một tautology.** Nguyên văn:
   ```python
   surface_reader = aggregate_run_cost(events).cost
   surface_cli    = aggregate_run_cost(events).cost
   assert surface_reader == surface_cli == 0.002
   ```
   Hai vế là **cùng một lời gọi cùng một hàm thuần**. `f(x) == f(x)` xanh với **mọi** cài đặt của
   `f` — kể cả bản tính lại từ tokens, kể cả bản trả hằng số. Vế `== 0.002` có giá trị (nó khoá luật
   cộng), nhưng cái tên và docstring nói bài này canh *"mọi mặt đọc ra cùng tổng"*, mà nó **không thể
   đỏ** vì lý do đó. Đây đúng hình `badge tautology` đã nêu ở review `web#3` (C2) và `wiringOk` ở
   `TraceViewer`.
3. **`test_price_mismatches_hom_nay_toan_0_thi_khop` mang một docstring đã hết hạn.** Nó viết *"Emit
   hôm nay: cost=0, tokens=0"*. Từ khi `engine#24` merge (`ec75541`), `llm-step` phát **tokens thật**
   ⇒ trên một trace thật hôm nay `price_mismatches` **KHÔNG rỗng**. Fixture dùng `tokens` mặc định 0
   nên bài vẫn xanh — và cái xanh đó nói *"hôm nay không lệch giá"*, ngược hẳn sự thật. Số trung thực
   để báo cáo là **`price_mismatches` ≠ rỗng trên mọi run có `llm-step`**, và đó chính là bằng chứng
   mắt "áp giá" đang gãy.
   *(Nit kèm: doc DE trỏ `interpreter.py:300` cho `_NO_COST`; số thật là `:73`/`:438`.)*

## Nợ D18 chưa đóng — đo được, không suy đoán

```bash
git -C packages/evalhub status --short docs/plans/   # ?? docs/plans/day-18-aie2.md
git -C packages/evalhub ls-tree origin/main docs/plans/ --name-only
#   day-11 … day-17   ← KHÔNG có day-18
grep -c "DEC-D18" packages/evalhub/docs/decisions/scorecard.md   # 0
```

Hai hệ quả, cùng một gốc:

- **Plan D18 không nằm trong bất kỳ commit nào** ⇒ không có trên GitHub ⇒ *"artifact không tìm thấy
  trong fresh clone"*, đúng thứ `kit#74` tính là **trừ điểm**. `.gitignore:19-20` đã dựng allowlist
  `!docs/plans/day-*-aie2.md` **chính xác để** chuyện này không xảy ra; cơ chế đúng, chỉ thiếu
  `git add`.
- **`DEC-D18-01…07` chỉ tồn tại trong file chưa commit đó** (+ `docs/mutations/judge-agreement-d18.md`
  trích lại `-04`/`-05`). Sổ quyết định `docs/decisions/scorecard.md` có **0** mục D18, trong khi
  comment đóng `#118` đã dẫn `DEC-D18-04` ra ngoài. Đây đúng cái bẫy file đó tự cảnh báo ở dòng 52:
  *"người tra `DEC-D15-03` sẽ không tìm thấy gì và có quyền kết luận là bịa ra lúc viết"*.

## Bản đồ phụ thuộc D19

```
   T0a kiểm nền + comment (15′)
        │
        ├──► T0b trả nợ D18: commit plan D18 · ghi DEC-D18-* vào sổ (P0, không chặn)
        │
        ▼
   T1 theo dõi vòng kế kb#22 + kb#24 (P0, 15′ — cả hai CHANGES_REQUESTED, chờ DE chứ không chờ mình)
        │
        ▼
   T2 cost_from_trace + RunCost ở evalhub (P0, đường găng)
        │
        ├───────────────┬──────────────────┐
        ▼               ▼                  ▼
   T3 bề mặt UI-test   T4 bài "cùng-1-số"  T5 failure-mode eval
   (render + CLI)      KHÔNG vacuous       (design-note)
        │               │                  │
        └───────┬───────┴──────────────────┘
                ▼
        T7a mutation ─► merge-ready ─► T6 hardening (P1) ─► T7b đóng ngày

   Q-A: cost_of land ở `contracts`  ──► chủ: chủ contracts. CHẶN số thật, KHÔNG chặn đường đọc
   AIE-1 #121: nối cost_of tại emit ──► chặn số thật. engine đã ở D20, _NO_COST chưa đụng
   DE   #120 kb#22                  ──► không chặn T2 (không import được); chặn việc đối chiếu chéo
   SWE  #122 playground hiện cost   ──► không chặn; T3 cấp sẵn số để họ đọc
```

## Dependency/blocker rule (giữ nguyên từ D15/D16/D17/D18)

Không món nào của mình được khai BLOCKED vì món của người khác, trừ khi đã (a) gửi ask có nguyên văn,
(b) ghi điều kiện lật đo được, (c) có đường đi tiếp không cần họ. Áp cho D19: **số cost thật là phụ
thuộc thật** (Q-A + AIE-1), nhưng **không món nào của mình khai BLOCKED** — T2/T3/T4 dựng và chứng
minh **đường đọc** bằng trace tự gieo, và ngày emit nối giá thì không phải viết lại dòng nào.

---

# §2 — Quyết định phải chốt hôm nay

## DEC-D19-01 · "Không tự tính lại" = cấm suy `cost` từ `tokens`; **cộng `cost` đã lưu là ĐỌC**

**Quyết:** trong `studio_evalhub`, `cost` chỉ được lấy từ `TraceEvent.cost`. Cấm mọi biểu thức suy
`cost` từ `tokens` × đơn giá. **Cộng dồn** `cost` đã lưu **không** phải "tính lại" — nó là phép đọc
trên nhiều dòng, cùng hình với `citations_from_trace` đọc nhiều event.

**Vì sao phải viết ra:** câu *"đọc cost từ trace, không tự tính lại"* ở `#123` có **hai** cách đọc, và
cách đọc thứ hai dẫn tới ngõ cụt: *"không tự tính = phải gọi bộ cộng dồn của DE"* (đúng nguyên văn
`F-7` của `kb#22`) — mà `.importlinter` cấm import chéo quadrant. Nếu không chốt cách đọc thứ nhất
thì hôm nay hoặc là phá layering, hoặc là ô DoD không đóng được.

**Cưỡng chế bằng fixture bất đối xứng, không bằng lời:** bài khoá luật này gieo một trace mà `cost`
**cố ý mâu thuẫn** `cost_of(tokens)` —

| event | tokens | `cost` đã lưu | `cost_of(tokens)` |
|---|---|---|---|
| `e1` `llm-step` | 1000 / 1000 | **0.5** | 0.018 |
| `e2` `tool-call` | 1000 / 1000 | **0.25** | 0.018 |

Bản đọc đúng ra **0.75**; bản tính lại ra **0.036**. Không cài đặt nào đúng cả hai. Đây là cùng khuôn
`test_aggregate_cong_cost_da_luu_khong_tinh_lai` của DE — **cố ý dùng cùng khuôn**, vì hai repo phải
canh cùng một bất biến và người review chéo phải nhận ra ngay.

**Cũng cấm luôn nhánh "tiện tay":** không đọc `cost` từ `AgentAnswer`, không nhận `cost` qua tham số
của caller, không cache một `cost` từ lần chạy trước. Nguồn là `events`, và chỉ `events`.

## DEC-D19-02 · Số cost sống ở `run_report`, **không** lên `SmokeResult`, **không** lên `contracts`

**Quyết:** thêm `RunCost` (frozen, thuần) + `run_cost_from_trace(events) -> RunCost` vào
`studio_evalhub/run_report.py`. **Không** thêm field vào `SmokeResult`; **không** đụng
`studio_contracts`.

**Ba lý do, mỗi lý do đo được:**

1. **Cost là sự thật mức RUN, `SmokeResult` là mức CASE.** Nhét một số run-level vào mỗi dòng case là
   nhân bản cùng một số n lần rồi mời người đọc cộng lại — đúng lớp lỗi `DEC-D15-01` mô tả (*"một
   renderer tự tính là một nguồn số thứ hai cho cùng một run"*).
2. **`SmokeResult` có lưới cưỡng chế sẽ đỏ ngay.** `render.py:50-53` khai `RUN_CASE_COLUMNS` +
   `RUN_CASE_FIELDS_NOT_SHOWN`, và `test_render_run_cases.py:350` bắt hai tuple **phủ kín**
   `SmokeResult.model_fields`. Thêm field ⇒ buộc quyết một cột hiển thị per-case cho một số không
   per-case. Lưới đang làm đúng việc của nó; đừng lách nó.
3. **`contracts` là nơi ra verdict.** `Aggregate`/`Scorecard` là artefact **quyết gate** (`INV-6`).
   Đặt một trục đang bằng `0.0` cạnh `gate.verdict` là dựng sẵn chỗ cho ai đó gate lên nó — và một
   gate trên hằng số 0 sẽ **PASS mọi thứ** cho tới ngày emit nối giá, rồi **FAIL mọi thứ** ngay hôm
   sau. Ngoài ra đổi `contracts` phải qua `ADR-D16-05`, mà cost hôm nay chưa có consumer nào cần nó ở
   tầng hợp đồng.

**Hình dạng chốt:**

```python
@dataclass(frozen=True, slots=True)   # hoặc BaseModel frozen — theo khuôn đang dùng ở quadrant
class RunCost:
    run_id: str
    tenant_id: UUID
    prompt_tokens: int
    completion_tokens: int
    cost: float          # round(sum(e.cost), 6) — DEC-D19-03
    event_count: int
    priced: bool         # DEC-D19-05
```

Tên field khớp `RunCost` của `kb#22` **có chủ đích** (`run_id`/`tenant_id`/`prompt_tokens`/
`completion_tokens`/`cost`/`event_count`): hai bên không import được nhau, nên thứ duy nhất giữ chúng
đối chiếu được là **tên + luật giống hệt**. Lệch tên là lệch âm thầm.

## DEC-D19-03 · Luật cộng chốt cứng `round(sum, 6)`, và nó là **nợ có điều kiện lật**

**Quyết:** `RunCost.cost = round(sum(e.cost for e in events), 6)`, khai hằng số
`_COST_ROUND_NDIGITS = 6` kèm docstring trỏ thẳng `kb/src/studio_kb/cost.py`.

**Vì sao phải là một quyết định chứ không phải một dòng code:** đây là **hằng số dùng chung giữa hai
repo không import được nhau**. Không có lint, không có type, không có test nào bắt được ngày DE đổi 6
thành 8. Đo được rằng chuyện đó **có hậu quả thật**, không phải lo xa:

```text
sum([0.000291, 0.001578, 0.010125, 0, 0, 0]) = 0.011994000000000001   ← không làm tròn
round(..., 6)                                = 0.011994
                                     bằng nhau? False
```

**Cưỡng chế được đến đâu thì cưỡng chế đến đó:** một bài **conformance** trong evalhub ghim bảng
`(per-event costs) → tổng kỳ vọng` với **số viết tay** (không tính bằng chính hàm đang test), và cùng
bộ số đó được dán vào comment review `kb#22` để DE ghim đối xứng. Đây là *tautology-proof*: số kỳ
vọng đến từ ngoài cài đặt.

**Cái KHÔNG cưỡng chế được, ghi thẳng vào bảng nợ:** không có cơ chế nào bắt hai repo lệch luật.
**Điều kiện lật:** ngày `cost_of` land ở `contracts` (Q-A), luật cộng đi cùng nó và nợ này đóng.

## DEC-D19-04 · Bất biến "cùng-1-số" khẳng định trên **giá trị đã làm tròn 6**, không trên chuỗi in ra

**Quyết:** phép so "cùng-1-số" giữa hai mặt là so **`float` sau `round(·, 6)`**. Mọi renderer in ít
hơn 6 chữ số thập phân phải **ghi nhãn là bản rút gọn**. Bề mặt của evalhub in `.6f`.

**Vì sao:** `umbrella-contract.md:131` viết *"`cost` ở UI test == trace == dashboard … lệch = fail"*
mà **không nói so ở tầng nào**, và ba mặt hiện có đang in `.6f` / `toFixed(4)` / `:.2f`. Không chốt
tầng so thì bất biến này **không kiểm được**: hai mặt in ra cùng chuỗi mà mang hai số khác nhau
(`0.011994` vs `0.011994000000000001`, cùng ra `"0.0120"`), và hai mặt mang **cùng** số vẫn in hai
chuỗi khác nhau (`"0.011994"` vs `"0.01"`).

**Hệ quả trực tiếp, đo được:** `f"{0.000291:<6.2f}"` → `"0.00  "`. Một run có cost thật in ra số 0.
`DEC-D12-02` cấm in `0.00` cho ô **chưa đo**; đây là chiều ngược — in `0.00` cho ô **đã đo** — và hại
ngang nhau vì người đọc nhận cùng một chuỗi.

## DEC-D19-05 · Hai trạng thái của số 0 phải phân biệt được **trong chính output**

**Quyết:** bề mặt cost của evalhub không bao giờ in một số `0` trần. Hai trạng thái, hai cách in,
phân loại bằng **điều kiện đo được trên chính events**:

| Trạng thái | Điều kiện | In ra |
|---|---|---|
| **chưa nối giá** | `Σcost == 0` **và** `Σtokens > 0` | `chưa-nối-giá (Σtokens=N, cost=0)` + trỏ `#121`/Q-A |
| **đã đo, bằng 0** | `Σcost == 0` **và** `Σtokens == 0` | `0.000000` |

### Trạng thái thứ ba (**lệch nguồn giá**) — **KHÔNG làm hôm nay**, và lý do là ranh giới, không phải thời gian

Bản đầu của quyết định này có dòng thứ ba: *"có event `cost != 0` mà không khớp luật giá đã công bố
⇒ in `LỆCH` + `event_id`"*. **Rút.** Nó không cài đặt được bằng chính luật của plan này:

- muốn biết một `cost` có khớp luật giá thì phải tính `cost_of(tokens)` ⇒ phải có **đơn giá** trong
  `studio_evalhub`;
- `DEC-D19-01` cấm mọi biểu thức suy `cost` từ `tokens × đơn giá`;
- §7 xếp *"một hằng số đơn giá (`0.003`/`0.015`) xuất hiện trong `studio_evalhub/`"* vào **thứ KHÔNG
  được tính là xong**.

Ba câu đó không thể cùng đúng. Giữ dòng thứ ba là khai một trạng thái trong hợp đồng output mà
**không có đường nào tính ra nó** — đúng lớp lỗi plan này đang gửi finding cho DE ở ask ①.

**Chỗ đúng của nó:** `price_mismatches` ở `kb#22` — DE **có** bảng đơn giá, nên phép kiểm đó thuộc
phía DE. Ghi thành `E-8` trong failure-mode list (`DEC-D19-07`), chủ **DE**, **điều kiện lật:** ngày
`cost_of` land ở `contracts` (Q-A) thì evalhub import được luật giá **mà không** giữ hằng số, và
trạng thái thứ ba mới quay lại được.

Và `LỆCH` **không nằm trong ô DoD nào của `#123`** (ba ô là *cùng-1-số* · *hardening* · *failure-mode
list*), nên rút nó không mất gì của ngày.

### `priced: bool` — chốt nghĩa, và **không** overload

`priced` trả lời **đúng một câu**: *"cost của run này đã được đo chưa"*. Không mang thêm nghĩa nào.

| `priced` | Điều kiện | Đọc là |
|---|---|---|
| `False` | `Σtokens > 0` **và** `Σcost == 0` | **Chưa nối giá** — có việc đã chạy nhưng chưa ai áp đơn giá |
| `True` | mọi trường hợp còn lại | **Đã đo** — *kể cả khi giá trị bằng `0`* (run `Σtokens == 0` là phép đo thật bằng không) |

```python
priced = not (tong_cost == 0 and tong_tokens > 0)
```

**`priced` KHÔNG được gánh thêm nghĩa "số này có nhất quán với luật giá không".** Đó là câu hỏi về
**từng event**, cần đơn giá để trả lời, và nó thuộc `price_mismatches` phía DE (xem khối trên).

Ràng buộc còn lại kể cả khi trạng thái thứ ba quay về: `priced` vẫn là **một câu duy nhất**. Ngày
evalhub kiểm được lệch giá, kết quả đó đi ra bằng **danh sách `event_id`** riêng, không nén vào
`bool` — vì một run có thể *đã đo* **và đồng thời** có event lệch, nhét cả hai vào một `bool` buộc
phải nói dối theo một trong hai chiều. Cùng lý lẽ đã áp cho `JudgeUnavailableReason` ở D18: **danh
tính của trigger, không chỉ sự tồn tại của nó**.

**Vì sao đây là quyết định của hôm nay chứ không phải trang trí:** trạng thái **chưa nối giá** là
trạng thái **của mọi run trong hệ thống hôm nay**. Nếu bề mặt in `0.000000` thì báo cáo D19 sẽ mang
một con số đọc được thành *"chạy 30 case tốn 0 đồng"*. Còn nếu in `chưa đo` vô điều kiện (cách
`TraceViewer` đang làm) thì đến ngày emit nối giá, node `kb-retrieve` với `Tokens(0,0)` — một **phép
đo thật bằng 0** — sẽ bị gán nhãn *chưa đo*. Cách duy nhất đúng ở **cả hai ngày** là phân loại bằng
`tokens`, không bằng riêng `cost`.

**Đây cũng là câu trả lời cho `F-1` của DE** (*"cost=0 toàn bộ → cost table ra 0"*): DE ghi nó là
honest-TODO trong tài liệu; ở đây nó thành **một nhánh có test**, in ra tại chỗ người đọc nhìn.

## DEC-D19-06 · Ô DoD "cùng-1-số" đóng ở **đường đọc**; phần **số thật** khai không đóng được

**Quyết:** báo cáo D19 khẳng định đúng hai câu, không gộp:

1. *"Đường đọc cost đã tái lập được: hai mặt đọc (bảng UI-test của evalhub ↔ trace trong
   `obs.trace_events`) cho **cùng một số**, chứng minh **không vacuous** bằng trace mang cost khác 0,
   bất đối xứng, và mâu thuẫn có chủ đích với `tokens`."*
2. *"Con số của một run THẬT hôm nay là `0.0` vì emit chưa áp giá (`_NO_COST`). Chuỗi chặn: Q-A
   (`cost_of` → `contracts`) → AIE-1 `#121` nối tại emit. Không gỡ được từ evalhub."*

**Điều kiện để chuyển ô này sang ✅ đầy đủ (đo được, không theo ngày):** `price_mismatches` trên một
run golden thật trả về **rỗng** và `Σcost > 0`. Cả hai vế cùng lúc — chỉ vế thứ hai thì một bảng giá
sai vẫn thoả; chỉ vế thứ nhất thì `0 == cost_of(0,0)` thoả một cách vacuous.

**Vì sao không được đánh ✅ ngay hôm nay dù mọi test xanh:** vì mọi test xanh **cũng** là điều xảy ra
khi mặt đọc trả hằng số. Ô DoD hỏi *"cost cùng-1-số"*, không hỏi *"suite có xanh không"*.

## DEC-D19-07 · Failure-mode list của **phía eval**, không chép danh sách của DE

**Quyết:** viết `docs/design-notes/aie2-day19-eval-failure-modes.md` — chỉ những mode mà **bộ chấm**
nhìn thấy và **danh sách của DE không nhìn thấy**. Mỗi mode bắt buộc: neo `file:line` kiểm được ·
trạng thái (**đã vá** / **honest-TODO**) · chủ · điều kiện lật.

**Vì sao không gộp vào danh sách DE:** `cost-lineage-d19.md` §4 liệt kê 7 mode của **phía cộng dồn**
(replay double-count, trộn tenant, float drift, event thiếu…). Bảy mode đó có chủ rồi. Chép lại là
làm dày tài liệu mà không thêm một bit thông tin, và tệ hơn: nó tạo **bản sao thứ hai** của một danh
sách sẽ sửa ở một chỗ.

**Mode phía eval — nhìn đầu, chưa vá hết (bản nháp vào T5):**

| # | Failure-mode phía eval | Vì sao DE không nhìn thấy |
|---|---|---|
| **E-1** | Bề mặt UI-test in `0.00` vì format `.2f` ⇒ cost thật hiển thị thành 0 | Mode ở **tầng render**, `aggregate_run_cost` trả số đúng |
| **E-2** | `cost === 0 ⇒ "chưa đo"` gán nhãn sai cho một **phép đo bằng 0** ngày emit nối giá | Chỉ lộ khi nhìn **cả hai** ngày (trước/sau khi nối giá) |
| **E-3** | Hai mặt cộng theo **hai luật** (`round(·,6)` vs raw `reduce`) ⇒ lệch ở chữ số thứ 16, vô hình khi in | Cần **hai** cài đặt để thấy; mỗi repo chỉ thấy của mình |
| **E-4** | Run có **>1 `llm-step`** — `answer_from_trace` đã raise, nhưng `Σcost` vẫn cộng được ⇒ có cost cho một run **không chấm được** | Bất biến của bộ chấm, không của cost table |
| **E-5** | Cost đọc từ **RAM** (run vừa chạy) vs đọc lại từ **Postgres** cùng `run_id` — `NUMERIC` → `Decimal` → `float` là một biến đổi có thật (`run_report.py:236-240`) | Mode của đường **đọc lại**; DE đọc thẳng |
| **E-6** | `Σcost` không có mẫu số đi kèm — một tổng không nói nó cộng bao nhiêu event, cùng lớp lỗi `n_scored_citation` (`kit#134`) | `RunCost.event_count` đã mang; mode là **quên in nó** |
| **E-7** | Không gì gate lên cost, và **đó là chủ ý** — nhưng chưa chỗ nào ghi ra ⇒ người sau tưởng là sót | Quyết định của phía verdict (AIE-2), ngoài phạm vi DE |
| **E-8** | Bề mặt eval **không phát hiện được** `cost` lệch luật giá — cần đơn giá, mà `DEC-D19-01`/§7 cấm đơn giá trong `studio_evalhub`. Chủ: **DE** (`price_mismatches`). **Điều kiện lật:** `cost_of` land ở `contracts` (Q-A) ⇒ evalhub import được luật giá **mà không** giữ hằng số | DE **có** nhìn thấy và đã vá phía mình; mode này là chỗ **phía eval mù**, ghi ra thay vì để tưởng đã phủ |

---

# §3 — Work items: thứ tự là quyết định, không phải danh sách

> Ngân sách ngày ~7h. `T1` **đã co từ 45′ xuống 15′**: review `kb#22`/`kb#24` xong từ trước ngày,
> cả hai đang `CHANGES_REQUESTED` nên bóng ở phía DE. Vẫn xếp đầu vì nếu DE đã đẩy bản vá thì biết
> sớm rẻ hơn biết muộn — nhưng nó **không còn là món mở khoá đường của người khác** như `T1` của D18.

## T0a · Kiểm nền + comment hình dạng ngày — **P0** (15′, làm đầu tiên)

Chạy 5 lệnh ở §1 + 3 lệnh đo chuỗi cost. Nếu số nào khác plan này (đặc biệt: `kb#22` đã merge, hoặc
`_NO_COST` đã bị thay) ⇒ **sửa plan trước, không chạy tiếp theo trí nhớ**.

**Bump `packages/engine` trước khi đo bất kỳ số cost nào** — kit đang trỏ `62773ba` (tokens `= 0`),
`origin/main` ở `bfa19cc` (tokens **thật**). Đo trên con trỏ cũ ⇒ `Σtokens = 0` ⇒ `priced=True`
(*"đã đo, bằng 0"*), **ngược** sự thật (*chưa nối giá*). Không bump được thì mọi số phải ghi kèm
con trỏ engine đã dùng.

Comment lên `#123`: hình dạng ngày (mặt đọc, không phải chủ công), trạng thái `_NO_COST`, và câu
*"ô DoD đóng ở đường đọc, số thật chặn ở Q-A + `#121`"* — nói trước lúc bắt đầu, không nói lúc đóng ngày.

## T0b · Trả nợ D18 — **P0, KHÔNG chặn đường găng** (30′, chạy sau khi T1 gửi)

Ba việc, cùng một gốc (§1):

1. `git add docs/plans/day-18-aie2.md` + commit. Kiểm bằng `git ls-tree origin/main docs/plans/` sau
   khi push — **không** kiểm bằng `ls` trên đĩa (đó đúng là phép kiểm đã nuốt im lặng `day-13`/`day-14`).
2. Ghi `DEC-D18-01…07` vào `docs/decisions/scorecard.md` dưới mục `## D18 · 2026-08-12`. Sổ là nơi
   người ngoài tra; plan là nơi lập luận. Comment đóng `#118` đã dẫn `DEC-D18-04` ra ngoài rồi.
~~3. Xin approval `kit#150`.~~ **XONG trước khi ngày bắt đầu** — `kit#150` MERGED (`acf8ecf`),
   `kit#118` CLOSED. Giữ dòng này để lịch sử đọc được, không phải việc phải làm.

**Kiểm bước 1 phải chạy SAU MERGE, không sau push.** `git ls-tree origin/main docs/plans/` chỉ thấy
file khi PR đã merge, mà evalhub cần ≥1 approval — tức bước kiểm này phụ thuộc người khác và **không
nằm trong 30′** của T0b. T7b không được đóng ngày trước khi phép kiểm đó xanh.

## T1 · Theo dõi vòng kế `kb#22` + `kb#24` — **P0, làm SỚM** (15′)

**Không còn là "đi review".** Cả hai PR đã review xong và đang `CHANGES_REQUESTED` — tức **chờ DE**,
không chờ mình. Việc của T1 rút còn **kiểm DE có vá không**, và chỉ mở lượt mới nếu họ đã đẩy:

| PR | Còn treo gì | Kiểm bằng |
|---|---|---|
| `kb#22` (head `7ff361c`) | Bài AST thay thế **xanh im lặng khi ngừng canh** — không assert nó quét trúng file nào | Gieo mutant làm glob trượt (vd đổi thư mục quét) ⇒ bài phải đỏ, không được xanh trên 0 file |
| `kb#24` (head `0ffa29d`) | (a) chữ ký AIE-2 còn nằm ở B2 · (b) `eval.scorecards` chưa lập luận lại trên **nội dung `results`** | Đọc diff mới; (b) là món lane mình, xem §4 |

**Nếu DE chưa đẩy ⇒ T1 xong trong 2 phút**, đi thẳng T2. Không mở lượt review mới trên cùng một head.

Ba mutant chéo dưới đây là **bản ghi đã chạy**, giữ để đối chiếu, **không phải việc phải làm**.
`M-X2` đã **hết đối tượng**: bài tautology nó canh đã bị DE xoá ở `71c25d6`.

| # | Mutant gieo vào `kb#22` | Dự đoán | Ý nghĩa |
|---|---|---|---|
| `M-X1` | `aggregate_run_cost` đổi `sum(e.cost)` → `sum(cost_of(e.tokens))` | **DIE** ở `test_aggregate_cong_cost_da_luu_khong_tinh_lai` | Xác nhận lưới §4.1 của DE có thật |
| `M-X2` | thay thân `aggregate_run_cost` bằng `return RunCost(..., cost=0.002, ...)` hằng số | **SURVIVE** ở `test_cung_1_so_moi_mat_doc_cung_tong` | Chứng minh bài đó là tautology, không phải đoán |
| `M-X3` | bỏ `round(·, 6)` ở tổng | dự đoán **SURVIVE** (fixture hiện tại cộng ra số chẵn) | Luật cộng chưa có lưới |

`M-X2` là con đáng giá: nó biến câu *"bài này là tautology"* từ một nhận xét đọc code thành một **số
đo** — mutant sống trong khi suite xanh.

**Đề xuất kèm finding (không chỉ chê):** bài "cùng-1-số" **có thể** đỏ nếu vế thứ hai đến từ một
đường khác — `PgCostReader.read_run_cost` (DB round-trip, `NUMERIC → Decimal → float`) so với
`aggregate_run_cost` trên events trong RAM. Hai đường thật, một số. DE đã có
`test_db_read_run_cost_khop_aggregate` gần đúng hình đó rồi; việc là **đổi tên/gộp** để bài mang tên
"cùng-1-số" là bài thật sự canh cùng-1-số.

## T2 · `run_cost_from_trace` + `RunCost` — **P0, đường găng** (1h15)

Đỏ trước, theo thứ tự:

1. Bài **bất đối xứng** `DEC-D19-01` (cost 0.5/0.25 mâu thuẫn tokens 1000/1000) → kỳ vọng `0.75`.
   Đỏ hôm nay vì hàm chưa tồn tại — **`ImportError` không tính là đỏ**; viết stub `raise
   NotImplementedError` trước để bài đỏ vì **lý do đúng**.
2. Bài **conformance luật cộng** (`DEC-D19-03`) với số kỳ vọng **viết tay**: `[0.000291, 0.001578,
   0.010125, 0, 0, 0]` → `0.011994` (**không** phải `0.011994000000000001`).
3. Bài fail-closed: `events` rỗng · trộn `run_id` · trộn `tenant_id` → raise kiểu riêng
   `RunCostError`, không `ValueError` trần (cùng khuôn `TraceAnswerError`, `run_report.py:66`).
   Trộn tenant là hở `INV-1` — `obs.trace_events` **không có RLS**, `tenant_id` là hàng rào duy nhất.
4. Bài `priced` (`DEC-D19-05`), **hai trục tách rời**, không gộp:
   - `priced` là **bool 2 trạng thái**: fixture `Σtokens>0, Σcost==0` ⇒ `False`; fixture
     `Σtokens==0, Σcost==0` ⇒ **`True`** (đo thật bằng không). Assert **giá trị**, không assert
     không-raise.
   - **Không** có fixture nào cho *lệch nguồn giá*: evalhub không giữ đơn giá nên không kiểm được
     (`DEC-D19-05`). Bài đó thuộc `price_mismatches` của DE.

Rồi mới viết thân hàm. Không import `studio_kb` (`make lint` sẽ chặn, và đó là **thiết kế**, không
phải trở ngại).

## T3 · Bề mặt UI-test: dòng cost trong `render_run_cases` + CLI — **P0, ô DoD** (1h)

- `render_run_cases(..., run_cost: RunCost | None = None)` — **keyword-only, default `None`**, đúng
  luật additive đã áp cho `score_run_from_trace(tenant_ids=...)` ở D18: hàm này có consumer **ngoài
  quadrant** (`dev_playground_server.py:189` gọi bằng tham số vị trí), nên đổi mặc định là phá hợp
  đồng của người khác mà họ không chọn.
- `None` ⇒ in đúng như hôm nay, **không** in dòng cost, **không** in `todo:` (`DEC-D12-02`: không có
  dữ liệu thì không dựng ô).
- Có `run_cost` ⇒ thêm hai dòng: `cost (Σ, USD)` in `.6f` hoặc nhãn phân loại (`DEC-D19-04`/`-05`),
  và `mẫu số cost` = `event_count` (`E-6`).
- `run_report` CLI truyền `run_cost=run_cost_from_trace(events)` — đây là bề mặt **UI-test** đọc số
  từ **trace đã bền hoá trong Postgres**, không từ RAM.
- Cập nhật `__all__` cho `RunCost` + `run_cost_from_trace` (một nửa nợ `T9a`, xem T6).

**Không** đụng `render_scorecard` — đó là khung verdict, và `DEC-D19-02` đã chốt cost không lên đó.

## T4 · Bài "cùng-1-số" **không vacuous** — **P0, ô DoD** (1h15)

Đây là ô DoD thật sự, và điều kiện của nó là **bài phải đỏ được**.

**BA lớp, không phải hai** (cần Docker test-stack). Hai lớp đầu chứng minh *phép cộng đúng*; lớp thứ
ba mới là thứ ô DoD thật sự nói — **UI-test hiển thị đúng con số đó**:

```text
ghi bằng chính sink apps/studio (PgTraceWriter)  ──▶  obs.trace_events
                                                        │
              ┌─────────────────────────────────────────┼─────────────────────────────┐
              ▼                                         ▼                             ▼
 A: run_cost_from_trace(read_run(...))    B: SELECT round(sum(cost),6) ...   C: render_run_cases(...)
    đường đọc evalhub, qua _row_to_event     SQL thô, KHÔNG qua code mình       chuỗi UI-test in ra
```

| Lớp | Khẳng định | Vì sao không bỏ được |
|---|---|---|
| **A** | `run_cost_from_trace(events)` ra **đúng giá trị kỳ vọng viết tay** | Nếu chỉ có A thì đang tin chính hàm mình viết |
| **B** | `SELECT round(sum(cost), 6) … WHERE run_id = …` ra **cùng** giá trị | Đường độc lập, **cố ý không dùng code evalhub** — đúng thứ `kb#22` thiếu và là lý do bài của DE không đỏ được |
| **C** | **Output render/UI-test thật sự chứa** giá trị đó | A≡B chỉ chứng minh *phép cộng*. Ô DoD nói **UI-test↔trace**, mà UI-test là **chuỗi người đọc nhìn** — một `render_run_cases` in nhầm cột, làm tròn lại, hay quên dòng cost vẫn để A≡B xanh |

**Lớp C là lớp dễ bỏ quên nhất và là lớp đúng nghĩa DoD.** Bằng chứng nó cần thiết nằm sẵn trong
failure-mode của chính ngày: `E-1` (`{:<6.2f}` in cost thật thành `0.00`) là một bug **chỉ tồn tại ở
tầng in**, A và B đều không thấy. Assert **substring giá trị** trong output, không assert "có gọi
render".

Số kỳ vọng **viết tay** ở cả ba vế — không vế nào lấy số từ vế khác.

**Trace gieo phải bất đối xứng và khác 0**: 6 event, 3 cost khác nhau khác 0
(`0.000291 / 0.001578 / 0.010125`), 3 event cost `0`, tokens **mâu thuẫn** cost ở ít nhất 1 event.
Một trace toàn `0.0` (tức trace thật hôm nay) làm bài này **xanh với mọi cài đặt** — chính là cái bẫy
ở Executive Summary.

**Bài đối trọng bắt buộc:** một bài chứng minh phép so **đỏ được** — sửa một `cost` ở một mặt rồi
khẳng định bài chính đỏ. Thiếu nó thì "cùng-1-số" không phân biệt được *khớp* với *cả hai cùng rỗng*.

### Docker/Postgres không lên — phân biệt hai ca, đừng gộp

Trong **mọi** ca: **không** hạ xuống bài in-memory rồi gọi là xong. Đường Postgres **là** thứ đang
được khẳng định; thay nó bằng in-memory là đổi mệnh đề chứ không phải tụt nấc.

| Ca | Dấu hiệu | Xử lý |
|---|---|---|
| **Lỗi môi trường local** — cổng bận, container chưa `up`, DSN sai, image chưa pull, quyền docker | Sửa được **bằng tay mình**, không cần ai | **KHÔNG được khai BLOCKED.** Phải thử phục hồi: đọc log container, `docker compose up -d --wait`, kiểm cổng 5433, kiểm DSN, chạy lại. Ghi lại đã thử gì |
| **Thiếu hạ tầng/quyền ngoài AIE-2** — không cài được Docker trên máy, CI không cấp service container, cần người khác mở quyền | Sửa **không được nếu không có người khác** | Áp **đúng blocker rule §1**: (a) ask có nguyên văn, (b) điều kiện lật đo được, (c) đường đi tiếp không cần họ. Đủ **cả ba** mới ghi BLOCKED |

**Vì sao phải tách:** *"BLOCKED"* là một tuyên bố về **người khác**. Dùng nó cho một lỗi mình tự sửa
được là đẩy việc của mình sang cột chờ, và nó làm hỏng chính giá trị của nhãn đó ở những ngày blocker
là thật. Một container chưa `up` không phải blocker — nó là một lệnh chưa chạy.

## T5 · Failure-mode eval — design-note — **P0, ô DoD** (45′)

`docs/design-notes/aie2-day19-eval-failure-modes.md`, 7 mode `E-1…E-7` ở `DEC-D19-07`, mỗi mode có
neo `file:line` **kiểm được** (khuôn của `aie1-day19-retrieval-failure-modes.md`, engine D19: 2 mode
đã vá + 2 honest-TODO, có anchor).

Ghi rõ mode nào **hôm nay đã có lưới** (`E-3`/`E-4`/`E-5`/`E-6` sau T2–T4) và mode nào là
**honest-TODO có chủ ngoài quadrant** (`E-1`/`E-2` → SWE; `E-7` → AIE-2, quyết định chứ không phải sót).

## T6 · Hardening happy-path + nợ `__all__` — **P1** (45′)

- Happy-path của quadrant này là `python -m studio_evalhub.run_report --run ID:CASE`. Hardening =
  mọi nhánh mới fail-closed (đã ở T2) + **ghim hình dạng output** bằng một bài đọc chuỗi, để dòng cost
  không lặng lẽ đổi format.
- `__all__` (`__init__.py:25-43`) có 17 tên, thiếu: `answer_from_trace` · `score_run_from_trace` ·
  `render_run_cases` · `TraceAnswerError` · `read_run` · `list_runs` · `ddl`. Nợ `T9a` từ D18, và
  hôm nay có thêm 2 tên nữa. Bổ sung trọn gói + một bài quét `__all__` **phủ kín** bề mặt công khai —
  cùng khuôn lưới `RUN_CASE_COLUMNS`, để nợ này không quay lại lần thứ ba.

**Gate cứng:** T6 chỉ bắt đầu khi T2–T5 đã merge-ready (test đỏ-trước có bằng chứng · mutation T7a đã
chạy · lint/format/mypy sạch · PR chưa xin review lần nào). *"Nếu còn giờ"* không phải điều kiện.

## T7a · Tự gieo mutant — **P0, TRONG merge-ready** (45′)

Khai **trước** khi viết test (`docs/mutations/cost-lineage-d19.md`):

| # | Mutant | Bất biến nó canh | Bài phải đỏ |
|---|---|---|---|
| `M-C1` | `sum(e.cost)` → `sum(cost_of(e.tokens))` | `DEC-D19-01` — đọc, không tính lại | bài bất đối xứng (0.75 vs 0.036) |
| `M-C2` | bỏ `round(·, 6)` | `DEC-D19-03` — luật cộng dùng chung | bài conformance (`0.011994...001`) |
| `M-C3` | `priced` → luôn `False` (bỏ nhánh `Σtokens > 0`) | `DEC-D19-05` — `priced` phân biệt *chưa nối giá* vs *đã đo bằng 0* | bài `priced` 2 trạng thái |
| `M-C4` | bỏ chặn trộn `run_id` | per-run mất nghĩa | bài fail-closed trộn run |
| `M-C5` | bỏ chặn trộn `tenant_id` | `INV-1` (không RLS) | bài fail-closed trộn tenant |
| `M-C6` | render `.6f` → `.2f` | `DEC-D19-04` — tầng so là giá trị, không phải chuỗi | bài in `0.000291` không được ra `0.00` |
| `M-C7` | mặt B của T4 gọi lại `run_cost_from_trace` thay vì SQL thô | bài "cùng-1-số" phải **đỏ được** | bài đối trọng T4 |

`M-C7` là con quan trọng nhất và nó **canh chính bài test**, không canh code sản phẩm: nó biến bài
"cùng-1-số" của mình thành đúng cái tautology mình vừa nêu ở `kb#22`. Nếu `M-C7` **sống**, finding gửi
DE ở T1 tự động áp cho chính mình.

Bảng phải ghi **bài nào đỏ**, không chỉ *có đỏ hay không* (luật rút từ D17: `M-F3` dự đoán 2 bài, thực
tế 1).

## T7b · Đóng ngày — **P0** (30′) · đứng SAU tất cả

Daily-note `2026-08-13-dholmes0207.md` → `docs/reports` + PR · comment + close `#123` · bump con trỏ
evalhub ở kit. Không đóng ngày khi plan D18 chưa lên `origin/main` — nó là hạn chót của T0b.

Báo cáo phải mang **cả hai câu** của `DEC-D19-06`, và mang `price_mismatches ≠ rỗng` như một **số**,
không như một lời than.

---

# §4 — Bảng nợ đến hạn D19

| Món | Chủ | Trạng thái vào D19 | Xử lý hôm nay |
|---|---|---|---|
| **Plan D18 chưa commit** — không có trên `origin/main` | AIE-2 | **đến hạn, đo được** (`ls-tree` không thấy) | **T0b** bước 1 |
| **`DEC-D18-01…07` không có trong sổ quyết định** | AIE-2 | 0 mục D18 trong `scorecard.md`; comment `#118` đã dẫn ra ngoài | **T0b** bước 2 |
| ~~**`kit#150` OPEN**~~ | AIE-2 | **ĐÃ ĐÓNG** — MERGED `acf8ecf`, `kit#118` CLOSED | Không còn việc |
| **Con trỏ `engine` lệch 8 commit** — kit `62773ba` (tokens=0) vs `bfa19cc` (tokens thật) | AIE-2 bump | mới phát sinh | **T0a**: bump trước khi đo, nếu không `priced` phân loại ngược |
| **`__all__` thiếu 7 tên** (`T9a`, D18 đếm 3, đếm lại ra 7) | AIE-2 | P2 hai ngày | **T6**, đóng trọn gói + lưới quét |
| **Luật cộng `round(·,6)` dùng chung 2 repo, 0 cơ chế cưỡng chế** (mới, `DEC-D19-03`) | AIE-2 + DE | mới phát sinh hôm nay | Bài conformance 2 phía + ghi nợ. **Điều kiện lật:** `cost_of` land ở `contracts` |
| **`cost_of` chưa ở `contracts` (Q-A)** | **chủ `contracts`** (mentor/CODEOWNERS) | chưa mở PR | ask ④. **Chặn số thật**, không chặn đường đọc |
| **Emit chưa áp giá (`_NO_COST`)** | **AIE-1** (`#121`) | engine đã ở D20, `interpreter.py:73` chưa đụng | ask ②. `DEC-D19-06` khai không đóng được |
| **`price_mismatches` ≠ rỗng trên mọi run thật** (mới) | AIE-1 + DE | chưa ai đo — bài của DE dùng fixture `tokens=0` | Đo và **báo bằng số** ở T7b; finding gửi kèm T1 |
| **`fmtCost` gán nhãn sai phép đo bằng 0** (mới, `E-2`) | **SWE** (`apps/web`) | chưa biết | ask ③(a). Điều kiện lật: ngày emit nối giá |
| **`{:<6.2f}` in cost thật thành `0.00`** (mới, `E-1`) | **AIE-1/chủ `apps/studio`** | chưa biết | ask ③(b) |
| **TraceViewer cộng raw, lệch luật `round(·,6)`** (mới, `E-3`) | **SWE** | chưa biết | ask ③(c) |
| **Recalibrate ngưỡng** — `DEC-D17-04`, điều kiện: LLM sinh prose thật ≥30 case | AIE-2 | **chưa lật** — điều kiện là **prose thật ≥30 case**, không phải sự tồn tại của key | Không làm hôm nay; nhắc trong ask ④ |
| **`match_mode`** | AIE-2 + DE | `DEC-D18-07`: hoãn theo **điều kiện**, không theo ngày | Không nhắc lại — điều kiện chưa đổi |
| **Agreement của LLM-judge** — 0 lần đo | AIE-2 | **0/30 case đi qua judge** + `manual_label` là nhãn **nhánh**, không phải nhãn đúng/sai của một `actual`. Thiếu là **trục nhãn**, không phải key | Ngoài phạm vi D19 |
| **`eval.scorecards` chưa chốt cần/không-cần RLS** (mới, `kb#24`) | **DE** (trả lời finding); hệ quả rơi lane AIE-2 | AIE-2 đã **từ chối** mức *KHÔNG CẦN*: điều kiện lật do chính PR đặt (*"`results` lưu answer-text của tenant"*) **đã thoả hôm nay** — `harness.py:463` đổ `actual`/`expected` vào `results JSONB` | Không làm hôm nay. **Điều kiện lật:** DE lập luận lại trên **nội dung `results`**, không trên đường đọc `gate`. **Nếu chốt CẦN** ⇒ thêm `tenant_id`+RLS cho `eval.scorecards`, schema lane AIE-2 |
| **Chủ trục `INV-1` roles** | **chưa có chủ** — đề xuất SWE, treo từ D12 | vẫn treo, **kỳ thứ tư** | Nêu lại ở `#124`; không nhận. Bảng nợ của AIE-2 vẫn 0 món vô chủ — món này nằm **ngoài** tập đó |

---

# §5 — Ask gửi ai, nguyên văn — **4 owner · 4 request** (① đã gửi)

> Không @ mentor. Đồng đội cùng cấp thì bình thường.

**① → DE (`kb#22`, review) — ✅ ĐÃ GỬI, DE ĐÃ VÁ**

> **Trạng thái:** gửi lượt 1 → DE vá `71c25d6`+`7ff361c` (F1 tautology→AST-scan, F2 nối
> `price_mismatches` vào CLI) → lượt 2 `CHANGES_REQUESTED` với **một finding mới** (bài AST xanh im
> lặng khi ngừng canh). Nguyên văn dưới đây giữ làm **bản ghi**, không phải việc phải gửi hôm nay.
> Việc còn lại là theo dõi vòng 3 — **T1**.
>
> Ba finding, cái đầu là cái chặn hình dạng của cả hai bên.
>
> **(a) `F-7` không thực thi được bằng cách đang ghi.** `cost-lineage-d19.md` §4 vá `F-7` bằng
> *"AIE-2/SWE phải gọi reader của DE"*. `.importlinter` xếp `studio_kb | studio_engine |
> studio_workbench | studio_evalhub` **cùng một layer** ⇒ `studio_evalhub` import `studio_kb.cost` là
> `make lint` đỏ. Nên mode nguy hiểm nhất trong bảng đang không có vá thật.
>
> Đề xuất thay: (i) mỗi mặt đọc **tự cộng `cost` đã lưu** — vẫn đúng `§4.1` vì `§4.1` cấm suy cost từ
> **tokens**, không cấm cộng cost đã lưu; (ii) luật cộng `round(sum, 6)` được ghim **hai phía** bằng
> một bảng số viết tay giống hệt nhau; (iii) khi `cost_of` land ở `contracts` (Q-A) thì luật cộng đi
> cùng nó và cả hai bản mirror bỏ được. Mình land phía evalhub hôm nay theo đúng (i)+(ii) — bảng số
> dán ở dưới, nếu ghim đối xứng thì hai repo có lưới chung.
>
> **(b) `test_cung_1_so_moi_mat_doc_cung_tong` không đỏ được vì lý do nó nói.** Hai vế là cùng một
> lời gọi cùng một hàm thuần: `f(x) == f(x)` xanh với mọi cài đặt. Đã gieo mutant để không phải chỉ
> nói: thay thân `aggregate_run_cost` bằng `return RunCost(..., cost=0.002, ...)` hằng số → bài này
> **vẫn xanh**. Vế `== 0.002` thì có giá trị (nó khoá luật cộng) — đề xuất tách tên cho đúng việc, và
> để bài "cùng-1-số" lấy vế thứ hai từ một **đường khác thật**: `PgCostReader.read_run_cost` (qua DB,
> `NUMERIC → Decimal → float`) so với `aggregate_run_cost` trên events RAM.
> `test_db_read_run_cost_khop_aggregate` đã gần đúng hình đó rồi.
>
> **(c) Docstring `test_price_mismatches_hom_nay_toan_0_thi_khop` đã hết hạn.** Nó viết *"Emit hôm
> nay: cost=0, tokens=0"*. `engine#24` (`ec75541`) đã merge và `executors.py:362` phát **tokens
> thật** ⇒ trên trace thật hôm nay `price_mismatches` **KHÔNG rỗng**. Fixture dùng tokens mặc định 0
> nên bài vẫn xanh, và cái xanh đó đọc thành *"hôm nay không lệch giá"* — ngược sự thật. Số này đáng
> là **headline** của cả hai báo cáo: lưới `price_mismatches` đang bắt đúng cái nó sinh ra để bắt.
>
> *(Nit: doc trỏ `interpreter.py:300` cho `_NO_COST`; số thật là `:73` khai và `:438` dùng.)*

**② → AIE-1 (`#121`, thread `engine`)**

> `engine` đã ở D20 và `tokens` thật đã land (`ec75541`) — cảm ơn, đó là mắt duy nhất của chuỗi
> cost-lineage đang chạy. Mắt còn gãy là **áp giá tại emit**: `interpreter.py:73` `_NO_COST = 0.0`,
> `:438` `cost=_NO_COST` ⇒ mọi `TraceEvent` trong hệ thống mang `cost = 0.0`.
>
> Hiểu là điều này **có chủ ý**: `§4.1` cấm hai nơi tính giá, mà bảng giá đang ở `kb` (`kb#22`) —
> engine không import được. Đường duy nhất là `cost_of` land ở `contracts` (Q-A) rồi interpreter gọi.
>
> Hai câu hỏi: (a) khi Q-A land, việc nối ở phía interpreter là bao nhiêu — một dòng thay `_NO_COST`,
> hay còn gì khác? (b) `DE F-3` nêu **replay double-count** (chạy lại một run sinh event mới cùng
> `run_id` ⇒ cộng dồn gấp đôi) — `#121` có ô *"xác nhận idempotent"*, mình đọc `ec75541` thấy bài
> idempotent qua 3 tiến trình `PYTHONHASHSEED` khác nhau; bài đó khoá **tokens ổn định**, có khoá luôn
> **không sinh event trùng `run_id`** không? Hai bất biến khác nhau cần hai lưới khác nhau.
>
> Không chặn D19 của mình — đường đọc dựng và chứng minh xong bằng trace tự gieo, ngày nối giá không
> phải viết lại dòng nào.

**③ → SWE (`#122`, thread `workbench`/`web`)**

> Ba thứ về bề mặt cost, cả ba **hôm nay đúng và ngày mai sai** — nên gửi trước khi cost thành số thật.
>
> **(a) `fmtCost` (`TraceViewer.tsx:49`) sẽ gán nhãn sai một phép đo bằng 0.** `cost === 0 ? "chưa
> đo"` đúng hôm nay vì `_NO_COST`. Ngày emit nối giá, `kb-retrieve`/`tool-call` phát `Tokens(0, 0)` ⇒
> `cost_of = 0.0` ⇒ một số **đã đo và đúng bằng 0** hiện là *"chưa đo"*. Phân loại đúng phải dựa vào
> `tokens`, không dựa vào riêng `cost`: `tokens > 0 && cost === 0` ⇒ *chưa nối giá*; `tokens === 0 &&
> cost === 0` ⇒ *0.000000 (đã đo)*. Mình đang land đúng luật đó ở phía evalhub (`DEC-D19-05`) nên hai
> mặt sẽ nói cùng một câu.
>
> **(b) `Σcost` ở TraceViewer (`:92`) cộng raw, cost table của DE cộng `round(·, 6)`.** Đo trên một
> run 6 node 3 bước LLM: `reduce` ra `0.011994000000000001`, `round(sum,6)` ra `0.011994` — **không
> bằng nhau**, mà `toFixed(4)` in cả hai thành `"0.0120"`. Bất biến `umbrella-contract.md:131`
> (*"lệch = fail"*) đang hỏng ở tầng giá trị và vô hình ở tầng hiển thị. Đề xuất: UI cộng theo cùng
> luật, hoặc tốt hơn — đọc **một** tổng từ một chỗ thay vì mỗi mặt tự cộng.
>
> **(c) Playground có thể kiểm được bất biến này trong MỘT response.** `dev_playground_server.py`
> đang trả `events` + `score`; nếu `score` mang thêm tổng cost đọc từ chính `events` đó thì bài
> UI-test↔trace so được ngay trong payload, không cần hai lần chạy. `render_run_cases` sẽ nhận
> `run_cost` **keyword-only, default `None`** (đường cũ y nguyên khi không truyền — cùng khuôn
> `tenant_ids` đã thoả thuận ở D18), nên phía workbench chỉ là một tham số thêm khi nào muốn.
>
> *(Kèm: `apps/studio/scripts/e2e_smoke_eval.py:250` in cost bằng `{:<6.2f}` ⇒ `cost_of(37,12) =
> 0.000291` hiển thị thành `0.00`. Bảng money-shot của demo sẽ nói run tốn 0 đồng. Không phải file của
> mình cũng không phải của SWE — nêu ở `#124` để có chủ.)*

**④ → thread `#124` (cả nhóm) — Q-A là blocker chung, không phải việc riêng của DE**

> Chuỗi cost-lineage hôm nay: `tokens` ✅ (AIE-1) → **áp giá ❌** → lưu `cost=0.0` → 3 mặt đọc ✅.
> Mắt gãy nằm ở chỗ **không quadrant nào chạm được**: bảng đơn giá `cost_of` phải sống nơi
> `interpreter` import được, tức `studio_contracts`, mà `contracts` ngoài fence-lane của cả DE lẫn
> AIE-1 lẫn AIE-2 (`GITFLOWS §5`). DE gọi nó là **Q-A** và đã ghi là honest-TODO.
>
> Nói thẳng hệ quả để cả nhóm biết trước GATE-2 (`#129`, D20): **ô DoD "cost cùng-1-số" của cả 4
> người hôm nay chỉ đóng được ở đường đọc.** Số thật cần Q-A land trước. Nếu Q-A không land trong S2
> thì "cost dashboard 3-surface" ở S3 là một ô **có bề mặt mà không có số**, và cả nhóm nên biết điều
> đó bây giờ thay vì mỗi ngày dời một ngày.
>
> Điều kiện đo được để tuyên bố chuỗi thông: `price_mismatches` **rỗng** trên một run golden thật
> **và** `Σcost > 0`. Cả hai vế cùng lúc — vế đầu một mình thoả một cách vacuous vì
> `0 == cost_of(0,0)`.
>
> *(Nhắc lần thứ tư: trục `INV-1 roles` vẫn chưa có chủ, treo từ D12. Bộ chấm **quan sát** hàng rào,
> không **tạo** hàng rào — lý do từ chối không đổi.)*

---

# §6 — Rủi ro đã biết

| Rủi ro | Dấu hiệu sớm | Xử lý |
|---|---|---|
| **Ô DoD đóng vacuous (`0.0 == 0.0`)** — rủi ro số một của ngày | Bài "cùng-1-số" xanh ngay lần chạy đầu, trước khi có fixture khác 0 | `DEC-D19-01` + T4: trace gieo **bắt buộc** khác 0, bất đối xứng, `cost` mâu thuẫn `tokens`. `M-C7` canh chính bài test |
| **Tự viết lại `cost_of` "cho tiện"** vì evalhub không import được kb | Bất kỳ hằng số `0.003`/`0.015` nào xuất hiện trong `studio_evalhub/` | `DEC-D19-01` cấm. Thêm bài quét `src/` như `test_src_khong_hardcode_duong_dan_kb` — bắt cả vi phạm **tương lai** |
| **`kb#22` đổi shape sau review** ⇒ tên field/luật cộng của evalhub lệch | DE đẩy commit mới lên `day19/de-cost-lineage` | T1 chạy **trước** T2 chính vì thế. Nếu shape đổi sau khi T2 merge ⇒ ghi nợ, không sửa vội trong ngày |
| **Vô tình nhét cost vào `contracts`** để "cho gọn" | Bất kỳ diff nào chạm `packages/contracts/` | `DEC-D19-02`. Đổi `contracts` phải qua `ADR-D16-05`, và cost chưa có consumer ở tầng hợp đồng |
| **Vào sửa `apps/web`/`workbench`** vì finding rõ quá | Diff ngoài `packages/evalhub/` | `DEC-D15-03` + `kit#74` chấm kỷ luật ranh giới. Finding đi bằng ask ③ |
| **Docker test-stack không lên** ⇒ T4 tụt xuống bài in-memory | `pytest` skip vì thiếu `STUDIO_DATABASE_URL_ADMIN` | **Không** hạ bài. Đường Postgres **là** thứ đang khẳng định; ghi BLOCKED đủ 3 điều kiện |
| **Báo cáo nói "cost-lineage khớp"** mà không nói số là 0 | Câu nào trong daily-note có chữ "khớp" mà không kèm `_NO_COST` | `DEC-D19-06` đòi **hai câu**, không gộp |
| **`Σcost` in không kèm mẫu số** | Dòng cost trần trong output | `E-6` + `RunCost.event_count`. `kit#134` đã gọi tên lớp lỗi này |
| **Thêm field vào `SmokeResult` rồi lưới `RUN_CASE_*` đỏ, gỡ lưới cho xanh** | `test_render_run_cases.py:350` đỏ | `DEC-D19-02`: lưới đang làm đúng việc. Cost không lên `SmokeResult` |
| **Push làm bay approval** | Approve rồi push tiếp | Gom lint/format/vá review **trước** khi xin review. Đã mắc ở D17, nhắc lại ở D18 |
| **Squash sai quy ước repo** | Merge PR nhiều commit | `evalhub` dùng **merge-commit** (`#16`, `#17`, `#19`, `#20`) |
| **T0b bị đẩy sang mai lần thứ hai** | Cuối ngày `git ls-tree origin/main docs/plans/` vẫn không có `day-18` | T0b là hạn chót của T7b — không đóng ngày khi nợ D18 còn |

---

# §7 — Định nghĩa "xong" cho D19

**Ba ô DoD `#123`, mỗi ô kèm cách kiểm:**

1. ⚠️ **`Cost cùng-1-số khớp UI-test↔trace (tái lập)` — đóng ĐƯỜNG ĐỌC, KHÔNG đóng SỐ THẬT.**

   Dấu ⚠️ chứ không ✅, khớp nguyên văn bảng ở Executive Summary. §7 là chỗ người ta căn vào để tuyên
   bố ngày đã xong, nên sai ở đây là sai về phía **dễ tuyên bố hoàn thành hơn thực tế**.

   **Nửa đóng được:** hai mặt đọc thật — `run_cost_from_trace(read_run(...))` của evalhub ↔ `SELECT
   sum(cost)` SQL thô trên cùng `run_id` — cho **cùng một số**, trên một trace **khác 0, bất đối
   xứng, `cost` mâu thuẫn `tokens`**, đã bền hoá qua `PgTraceWriter`. Kèm bài đối trọng chứng minh
   phép so **đỏ được**.

   **Nửa KHÔNG đóng được:** số của một run **được áp giá thật**. `interpreter.py:73` vẫn `_NO_COST`.
   Ai đọc ô này thành *"cost-lineage đã thông"* là đọc sai.

   **Điều kiện chuyển ✅ (đo được, không theo ngày):** `price_mismatches` rỗng trên run golden thật
   **và** `Σcost > 0`.

2. ✅ **`hardening happy-path`** — `run_report` CLI: mọi nhánh mới fail-closed với kiểu lỗi riêng
   (rỗng · trộn `run_id` · trộn `tenant_id`), hình dạng output có bài ghim, `__all__` phủ kín bề mặt
   công khai + lưới quét chống tái phát.

3. ✅ **`failure-mode list nhìn đầu (honest-TODO)`** — 7 mode **của phía eval**, mỗi mode có neo
   `file:line` kiểm được, trạng thái đã-vá/honest-TODO, chủ, điều kiện lật. Không chép 7 mode của DE.

**Điều kiện chung, giữ nguyên từ các ngày trước:**

- Mọi bài test mới **đỏ trước** trên code hôm nay. **`ImportError` không tính là đỏ** — dựng stub
  `NotImplementedError` để bài đỏ vì lý do đúng.
- Mutation khai **trước** khi viết test; bảng ghi **bài nào đỏ**, không chỉ có-đỏ-hay-không. Mutant
  chỉ tồn tại chừng nào bất biến nó canh còn tồn tại.
- Mọi món AIE-2 hoãn có **chủ + hạn + điều kiện lật đo được**. **0 món hoãn vô chủ trong tập của
  AIE-2** — món `INV-1 roles` nằm **ngoài** tập đó và được nêu lại như một finding, không được lấp.
- Ranh giới nói ra thay vì để phát hiện sau, trên cả hai trục: (a) **đường đọc** hay **số thật**;
  (b) đo trên **trace gieo** hay trên **run golden thật**.
- PR: merge-commit (không squash), gom lint trước khi xin review, ≥1 approval bất kỳ.

**Thứ KHÔNG được tính là xong:**

- Một bài "cùng-1-số" mà **cả hai vế đi qua cùng một hàm** — đúng finding vừa gửi DE ở ask ①(b).
- Một bài "cùng-1-số" chạy trên trace **toàn `cost = 0.0`** (tức trace thật hôm nay).
- Bất kỳ biểu thức nào trong `studio_evalhub` suy `cost` từ `tokens` — kể cả khi ra đúng số.
- Một hằng số đơn giá (`0.003`/`0.015`) xuất hiện trong `studio_evalhub/`.
- Một `Σcost` in ra **không kèm** `event_count`.
- Một số `0` in ra mà **không phân loại** được là *chưa nối giá* / *đã đo bằng 0*.
- Một dòng cost in ở `.2f` hoặc `.4f` mà **không ghi nhãn rút gọn**.
- Cost xuất hiện trên `SmokeResult`, `Aggregate`, `Scorecard`, hoặc bất kỳ file nào trong
  `packages/contracts/`.
- Một diff chạm `apps/web`, `packages/workbench`, hoặc `packages/kb`.
- Báo cáo dùng chữ *"cost-lineage khớp"* mà không nói `cost` ở emit vẫn là `0.0`.
- Đóng ngày khi plan D18 vẫn chưa lên `origin/main` (kiểm bằng `ls-tree`, không bằng `ls`).
