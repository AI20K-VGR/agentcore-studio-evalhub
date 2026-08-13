# D19 — failure-mode của **phía eval** cho cost-lineage (đã vá + honest-TODO)

AIE-2, D19 `kit#123` (việc con thứ 3), `DEC-D19-07`. Docs-only — không đổi code ở đây.

## Vì sao có danh sách này khi DE đã có một danh sách

`kb:docs/decisions/cost-lineage-d19.md` §4 liệt **7 mode của phía cộng dồn** (replay double-count,
trộn tenant, float drift, event thiếu…). Bảy mode đó **có chủ rồi**, và chép lại là làm dày tài liệu
mà không thêm một bit thông tin — tệ hơn, nó tạo **bản sao thứ hai** của một danh sách sẽ sửa ở một
chỗ.

Danh sách dưới đây chỉ gồm mode mà **bộ chấm nhìn thấy còn danh sách của DE không nhìn thấy**. Phần
lớn nằm ở **tầng render** hoặc ở **đường đọc lại**, hai chỗ mà một hàm cộng dồn đúng vẫn không cứu
được.

## Cách đọc bảng

Mỗi mode có: neo `file:line` **kiểm được bằng lệnh** · trạng thái · chủ · điều kiện lật.

**Trạng thái** phân biệt ba thứ, không gộp:

- **đã vá** — có lưới trong `studio_evalhub`, nêu tên bài test khoá nó;
- **honest-TODO** — biết, chưa vá, và **nói rõ chưa vá** thay vì ngụy trang thành đã đóng;
- **quyết định** — không phải sót; chỗ này cố ý không làm, và lý do ghi ra.

| # | Mode | Trạng thái ở evalhub | Chủ của phần chưa đóng |
|---|---|---|---|
| `E-1` | render `.2f` biến cost thật thành `0.00` | **đã vá** | AIE-1 / chủ `apps/studio` (bản còn hở) |
| `E-2` | `cost === 0 ⇒ "chưa đo"` gán nhãn sai một phép đo bằng 0 | **đã vá** | SWE (bản còn hở) |
| `E-3` | hai mặt cộng theo hai luật ⇒ lệch ở chữ số thứ 16, vô hình khi in | **đã vá một nửa** | AIE-2 + DE |
| `E-4` | run **không chấm được** vẫn có `Σcost` | **honest-TODO** | AIE-2 |
| `E-5` | cost đọc từ RAM vs đọc lại từ Postgres | **đã vá** | — |
| `E-6` | `Σcost` không có mẫu số đi kèm | **đã vá** | — |
| `E-7` | không gì gate lên cost — **và đó là chủ ý** | **quyết định** | AIE-2 |
| `E-8` | bề mặt eval **không phát hiện được** `cost` lệch luật giá | **honest-TODO** (mù có chủ đích) | DE |

---

## `E-1` · Render `.2f` biến một cost **đã đo** thành `0.00`

**Mode:** cost đúng ở tầng giá trị, sai ở tầng in. `aggregate_run_cost` trả số đúng, người đọc nhận
số `0`.

**Bằng chứng còn sống, đo được:**

```text
apps/studio/scripts/e2e_smoke_eval.py:250
    f"{str(e.tenant_id)[:13] + '…':<15}{tok:<9}{e.cost:<6.2f}{cites}"

f"{0.000291:<6.2f}"  →  "0.00  "
```

`cost_of(37, 12) = 0.000291` — một run có tốn tiền thật — hiển thị thành `0.00`. Bảng money-shot của
demo sẽ nói *run này tốn 0 đồng*.

`DEC-D12-02` cấm in `0.00` cho ô **chưa đo**; đây là **chiều ngược** — in `0.00` cho ô **đã đo**. Hại
ngang nhau, vì người đọc nhận **cùng một chuỗi** và không có cách nào phân biệt.

**Vì sao DE không nhìn thấy:** mode ở tầng render, và `apps/studio/scripts/` không nằm trong lane DE.

**Trạng thái phía evalhub — đã vá:** `render.py:35` `_COST_DISPLAY_NDIGITS = 6`, dòng cost in `.6f`.
Bài khoá: `test_render_run_cost.py::test_in_du_6_chu_so_khong_lam_tron_mat_cost_that` ·
`test_cost_cung_1_so.py::test_doi_trong_lop_C_bat_duoc_render_lam_tron_mat`. Mutant `M-C6`
(`.6f → .2f`) **DIE** — xem `docs/mutations/cost-lineage-d19.md` §4.

**Phần chưa đóng:** `e2e_smoke_eval.py:250` vẫn `.2f`. **Chủ: AIE-1 / chủ `apps/studio`.** Đã nêu ở
ask ③ kèm `#124`. **Điều kiện lật:** ngày emit áp giá — hôm nay mọi `cost` là `0.0` nên `.2f` in ra
`0.00` *tình cờ đúng*; nó thành sai ngay ngày `cost ≠ 0`.

---

## `E-2` · `cost === 0 ⇒ "chưa đo"` gán nhãn sai một **phép đo bằng 0**

**Mode:** phân loại trạng thái của số `0` dựa vào **riêng `cost`**. Hôm nay đúng, mai sai.

**Bằng chứng còn sống:**

```ts
apps/web/src/playground/TraceViewer.tsx:50
    return cost === 0 ? "chưa đo" : cost.toFixed(4);
```

Hôm nay câu đó **đúng** — mọi `cost` là `0.0` vì emit chưa áp giá. Ngày emit nối giá, node
`kb-retrieve` / `tool-call` phát `Tokens(0, 0)` ⇒ giá của chúng **đúng bằng `0`** ⇒ một số **đã đo và
đúng bằng 0** sẽ hiển thị là *"chưa đo"*. Cùng một dòng code, hôm nay đúng, mai sai, và cái làm nó
sai là **việc của người khác land**.

**Vì sao DE không nhìn thấy:** chỉ lộ khi nhìn **cả hai** ngày — trước và sau khi nối giá. Một ảnh
chụp tại một thời điểm bất kỳ đều thấy nó đúng.

**Trạng thái phía evalhub — đã vá:** phân loại theo **`tokens`**, không theo riêng `cost`.
`run_report.py:354` `priced = not (tong_cost == 0 and prompt_tokens + completion_tokens > 0)`;
`render.py:204` `_cost_value` chọn hai chuỗi khác nhau cho hai trạng thái. Bài khoá:
`test_render_run_cost.py::test_chua_noi_gia_khong_duoc_in_mot_so_0_tran` ·
`::test_da_do_bang_0_thi_in_0_000000_chu_khong_phai_chua_do` ·
`::test_hai_trang_thai_so_0_cho_ra_HAI_chuoi_khac_nhau`. Mutant `M-C3` (`priced → False` hằng)
**DIE**.

**`M-C3` để lại một bài học đáng ghi ở đây:** nó bị giết bởi **hai bài `priced is True`**, còn bài
`priced is False` **vẫn xanh**. Tức nếu chỉ viết bài cho trạng thái **hôm nay** (*chưa nối giá*, là
trạng thái của mọi run thật trong hệ thống) thì `M-C3` **sống trọn vẹn**. Bài giết nó là bài cho
trạng thái **chưa tồn tại trong production**. Đây chính là hình dạng của `E-2`: mode chỉ lộ ở ngày
mai thì lưới cũng phải viết cho ngày mai.

**Phần chưa đóng:** `TraceViewer.tsx:50`. **Chủ: SWE.** Đã nêu ở ask ③(a). **Điều kiện lật:** ngày
emit nối giá.

---

## `E-3` · Hai mặt cộng theo **hai luật** ⇒ lệch ở chữ số thứ 16, vô hình khi in

**Mode:** cùng một trace, hai mặt đọc, hai con số — và cả hai **hiển thị giống hệt**.

**Đo trực tiếp:**

```text
per-event cost : [0.000291, 0.001578, 0.010125, 0.0, 0.0, 0.0]

apps/web/src/playground/TraceViewer.tsx:92   reduce((sum, e) => sum + e.cost, 0)
  → 0.011994000000000001      in ra toFixed(4) → "0.0120"
kb (kb#22)  round(sum(cost), 6)
  → 0.011994                  in ra .6f       → "0.011994"

0.011994000000000001 == 0.011994  →  False
```

Bất biến `umbrella-contract.md:131` (*"`cost` ở UI test == trace == dashboard … lệch = fail"*) **đã**
hỏng ở tầng giá trị, và nó **vô hình** ở tầng hiển thị.

**Vì sao DE không nhìn thấy:** cần **hai** cài đặt để thấy; mỗi repo chỉ thấy của mình.

**Trạng thái — đã vá một nửa, và nửa còn lại nói thẳng:**

*Nửa đã vá:* `run_report.py:218` `_COST_ROUND_NDIGITS = 6` + `:347`
`round(sum(e.cost for e in events), _COST_ROUND_NDIGITS)`. Bài conformance
`test_run_cost_from_trace.py::test_conformance_luat_cong_round_6` ghim bảng số **viết tay** (số kỳ
vọng đến từ **ngoài** cài đặt ⇒ tautology-proof), và có vế `!= 0.011994000000000001` — vế đó mới là
vế có răng. Mutant `M-C2` (bỏ `round`) **DIE**. Ở T4, luật này còn được khẳng định lần thứ hai bằng
**Postgres** (`SELECT round(sum(cost)::numeric, 6)`), tức hai bộ máy khác nhau cùng nói một luật.

*Nửa KHÔNG vá được:* **không có lint, không có type, không có test nào bắt được ngày `kb` đổi `6`
thành `8`.** Hai repo không import được nhau (`.importlinter:20` xếp `studio_kb | studio_engine |
studio_workbench | studio_evalhub` **cùng một layer**), nên thứ duy nhất giữ chúng khớp là **cùng
luật + cùng tên field**.

⚠️ **Đo được hôm nay, và nó làm nửa này yếu hơn plan giả định:** docstring của `_COST_ROUND_NDIGITS`
trỏ `kb/src/studio_kb/cost.py` — file đó **chưa tồn tại trên `origin/main` của `kb`**:

```bash
git -C packages/kb ls-tree origin/main src/studio_kb/cost.py   # rỗng
git -C packages/kb ls-tree 3c9d40b   src/studio_kb/cost.py     # có (head kb#22, OPEN)
```

Tức neo đối chiếu hiện trỏ vào một **nhánh PR đang mở** (`kb#22`, `CHANGES_REQUESTED`), không phải
vào `main`. Nếu `kb#22` đổi shape trước khi merge thì bản mirror phía evalhub lệch mà **không có gì
báo**.

**Chủ:** AIE-2 + DE. **Điều kiện lật:** ngày `cost_of` land ở `contracts` (Q-A) — luật cộng đi cùng
nó và **cả hai bản mirror bỏ được**. Trước ngày đó, đây là nợ có điều kiện lật, không phải một món
sẽ tự đóng.

---

## `E-4` · Một run **không chấm được** vẫn có `Σcost` — honest-TODO

**Mode:** bộ chấm từ chối một run, nhưng bề mặt cost vẫn vui vẻ trả về một con số cho chính run đó.

**Đo trực tiếp, không suy từ đọc code** — trace 2 event `llm-step`:

```text
answer_from_trace(events)     → RAISE TraceAnswerError
                                 "trace có 2 event `llm-step` — không suy ra được đâu là câu trả lời"
run_cost_from_trace(events)   → KHÔNG raise
                                 cost=0.75  event_count=2  priced=True
```

Neo: `run_report.py:124-126` (nhánh raise của `answer_from_trace`) vs `run_report.py:282`
(`run_cost_from_trace`, không có nhánh tương ứng).

**Vì sao DE không nhìn thấy:** *"run này chấm được không"* là bất biến của **bộ chấm**, không của
cost table. Với DE, một run có 2 `llm-step` là một run bình thường có 2 event.

**Trạng thái — honest-TODO, chưa vá, và nói rõ là chưa vá.**

Chưa vá vì **chưa quyết được nên vá theo chiều nào**, và nói ra chiều nào cũng có lý:

- *raise luôn* — nhất quán với `answer_from_trace`, nhưng biến `run_cost_from_trace` thành hàm phụ
  thuộc luật của **bộ chấm**, trong khi nó đang là một hàm thuần đọc `events`. Một run không chấm
  được vẫn **tốn tiền thật**, và giấu con số đó đi là mất một sự thật vận hành.
- *trả số kèm cờ* — trung thực hơn, nhưng `priced` đã bị `DEC-D19-05` chốt là **một câu duy nhất**,
  nên phải là một trục thứ hai, tức một quyết định về shape của `RunCost`.

Không quyết trong ngày vì cả hai đường đều đổi hợp đồng của một hàm vừa land, và không có consumer
nào hôm nay cần câu trả lời. **Chủ: AIE-2.** **Điều kiện lật:** consumer đầu tiên hỏi *"run này chấm
được không"* **cùng lúc** với *"run này tốn bao nhiêu"* — tức ngày `run_cost` xuất hiện cạnh
`gate.verdict` trên cùng một bề mặt.

Ranh giới nói thẳng: hôm nay **không có bài test nào** khoá hành vi này. Nó là gap thật, không phải
"đã xử lý theo thiết kế".

---

## `E-5` · Cost đọc từ **RAM** vs đọc lại từ **Postgres**

**Mode:** cùng một `run_id`, hai đường đọc, và giữa chúng có một **biến đổi kiểu có thật**:
`NUMERIC → Decimal → float` (`run_report.py:406` `cost=float(row[10])`). Một run vừa chạy xong và
chính run đó đọc lại ngày mai không đương nhiên cho cùng một số.

**Vì sao DE không nhìn thấy:** mode của đường **đọc lại**; DE đọc thẳng.

**Trạng thái — đã vá:** T4 dựng đúng phép đo đó và nó là ô DoD của ngày.
`test_cost_cung_1_so.py::test_cost_cung_1_so_ba_lop_A_B_C` ghi trace bằng **chính sink của
`apps/studio`** (`PgTraceWriter`) rồi so ba mặt:

```text
A  run_cost_from_trace(read_run(...))     qua _row_to_event, NUMERIC → Decimal → float
B  SELECT round(sum(cost)::numeric, 6)    SQL thô, KHÔNG qua code evalhub
C  render_run_cases(...)                  chuỗi UI-test in ra
```

Cả ba ra `0.011994` — số **viết tay**, không vế nào lấy số từ vế khác.

Kèm `test_doi_trong_mat_B_KHONG_di_qua_code_evalhub` canh chính mặt B: nếu B đi qua code evalhub thì
A≡B thành tautology. Mutant `M-C7` **sống ở lượt gieo đầu** và chỉ chết sau khi bài đối trọng được
dựng lại — chi tiết ở `docs/mutations/cost-lineage-d19.md` §5.

---

## `E-6` · `Σcost` không có mẫu số đi kèm

**Mode:** một tổng không tự nói nó cộng bao nhiêu event. Cùng lớp lỗi `n_scored_citation`
(`kit#134`): *chỗ hỏng không nằm ở probe, nằm ở bước từ `8/10` sang tám-mươi-phần-trăm*.

**Vì sao DE không nhìn thấy:** `RunCost.event_count` **đã mang** con số; mode là **quên in nó** —
một lỗi của bề mặt hiển thị, không của bộ cộng dồn.

**Trạng thái — đã vá:** `run_report.py:278` `event_count: int` · `render.py:190`
`_row("mẫu số cost", f"{run_cost.event_count} event")`. Bài khoá
`test_render_run_cost.py::test_in_mau_so_cost_ben_canh_tong`, **có đối chứng âm** (6 ↔ 42) — thiếu
đối chứng âm thì một renderer in hằng số `"6 event"` vẫn xanh.

Bài đó **bản đầu xanh vacuous**: `assert "6" in out` khớp `"D16"` trong caveat, `assert "event" in
out.lower()` khớp chính chuỗi fixture `trace_source="obs.trace_events (test)"`. Giữ vết trong
docstring của bài, vì nó là cùng lớp lỗi đang gửi finding cho DE ở `kb#22`.

---

## `E-7` · Không gì gate lên cost — **và đó là chủ ý**, chưa chỗ nào ghi ra

**Mode:** người đọc sau thấy `Aggregate`/`Gate` có `success_rate` và `citation_accuracy` nhưng không
có cost, rồi kết luận **sót**.

**Đo được:**

```bash
grep -c "cost" packages/evalhub/src/studio_evalhub/compute.py          # 0
grep -n  "cost" packages/contracts/src/studio_contracts/scorecard.py   # 1 — chỉ trong prose docstring
```

`GateThreshold` là `(success, citation_accuracy)` (`contracts:scorecard.py:28-29`); `Aggregate` là
`(success_rate, citation_accuracy, n_scored_citation)` (`:49-50`, `:86`). **Không trục nào là cost.**

**Vì sao DE không nhìn thấy:** đây là quyết định của phía **verdict**, ngoài phạm vi cost table.

**Trạng thái — quyết định, không phải sót.** `DEC-D19-02` chốt: đặt một trục đang bằng `0.0` cạnh
`gate.verdict` là **dựng sẵn chỗ cho ai đó gate lên nó**, và một gate trên hằng số 0 sẽ **PASS mọi
thứ** cho tới ngày emit nối giá, rồi **FAIL mọi thứ** ngay hôm sau. Đổi `contracts` còn phải qua
`ADR-D16-05`, mà cost hôm nay chưa có consumer nào cần nó ở tầng hợp đồng.

**Chủ: AIE-2.** **Điều kiện lật:** `Σcost > 0` trên run thật **và** có một consumer nêu được ngưỡng
cost có nghĩa. Vế thứ hai không tự đến cùng vế thứ nhất — có số thật vẫn chưa đủ để biết gate ở đâu.

---

## `E-8` · Bề mặt eval **không phát hiện được** `cost` lệch luật giá

**Mode:** một event mang `cost` không khớp `cost_of(tokens)` — bảng giá sai, hoặc emit áp giá cũ.
Bề mặt eval **mù** với chuyện này.

**Vì sao mù, và vì sao mù là đúng:** muốn biết một `cost` có khớp luật giá thì phải tính
`cost_of(tokens)` ⇒ phải có **đơn giá** trong `studio_evalhub`. Nhưng:

- `DEC-D19-01` cấm mọi biểu thức suy `cost` từ `tokens × đơn giá`;
- §7 xếp *"một hằng số đơn giá (`0.003`/`0.015`) xuất hiện trong `studio_evalhub/`"* vào thứ **KHÔNG
  được tính là xong**.

Ba câu đó không thể cùng đúng. Giữ trạng thái *lệch nguồn giá* trong hợp đồng output của evalhub là
khai một trạng thái **không có đường nào tính ra nó** — đúng lớp lỗi đang gửi finding cho DE.

Có lưới chống vi phạm tương lai: `test_run_cost_from_trace.py::test_src_khong_chua_hang_so_don_gia`
quét `src/` tìm `0.003`/`0.015`, quét **từng nguồn riêng** kèm ngưỡng số file (không quét một tổng —
đúng finding vừa gửi `kb#22` lượt 3). Mutant `M-C1` (tính lại từ tokens) bị **chính bài này** bắt,
ngoài dự đoán, vì mutant buộc phải viết đơn giá vào `src/`.

**Chủ: DE** — `price_mismatches` ở `kb#22` là chỗ đúng của phép kiểm này, vì DE **có** bảng đơn giá.

**Điều kiện lật:** `cost_of` land ở `contracts` (Q-A) ⇒ evalhub import được luật giá **mà không** giữ
hằng số ⇒ trạng thái thứ ba quay lại được. Khi đó nó đi ra bằng **danh sách `event_id`** riêng,
**không** nén vào `priced` — một run có thể *đã đo* **và đồng thời** có event lệch, nhét cả hai vào
một `bool` buộc phải nói dối theo một trong hai chiều.

---

## Ranh giới của cả danh sách này

Tám mode trên là mode của **đường đọc**. Không mode nào trong đây đóng được vế **số thật**:
`engine:interpreter.py:73` `_NO_COST = 0.0` và `:438` `cost=_NO_COST` vẫn nguyên trên `origin/main`
của engine (đã ở D20). Mọi `cost` trong hệ thống hôm nay là hằng số `0.0`.

`DEC-D19-06` chốt ô DoD *"cost cùng-1-số"* đóng ở **đường đọc**, **không** đóng ở **số thật**, và
điều kiện chuyển ✅ đầy đủ là đo được chứ không theo ngày: **`price_mismatches` rỗng trên một run
golden thật `VÀ` `Σcost > 0`** — cả hai vế cùng lúc. Chỉ vế thứ hai thì một bảng giá sai vẫn thoả;
chỉ vế thứ nhất thì `0 == cost_of(0, 0)` thoả một cách vacuous.

Ai đọc danh sách này thành *"cost-lineage đã thông"* là đọc sai.
