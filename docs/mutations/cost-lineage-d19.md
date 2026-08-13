# Sổ gieo mutant D19 — cost-lineage: mặt đọc `cost` từ trace

**Ngày:** 2026-08-13 (D19) · **Bút:** AIE-2 · **Ref:** `kit#123` (T7a khai, chạy theo từng T) ·
`DEC-D19-01/02/03/04/05`

## §0 · Vì sao ngày này cần mutant hơn mọi ngày khác

Ô DoD hôm nay đọc rất dễ — *"cost cùng-1-số khớp UI-test↔trace"* — và đó là vấn đề. Đo được sáng nay:

```text
engine origin/main (bfa19cc)
  interpreter.py:73    _NO_COST = 0.0
  interpreter.py:438   cost=_NO_COST,     ← MỌI TraceEvent, MỌI node, MỌI run
```

`cost` của mọi event trong hệ thống hôm nay là **hằng số `0.0`**. Một bài khẳng định *"số ở UI-test
bằng số ở trace"* sẽ xanh khi mặt đọc **đọc đúng**, xanh khi nó **tính lại từ tokens**, xanh khi nó
**trả hằng số 0**, và xanh cả khi nó **không đọc gì**. Bốn cài đặt, ba cái sai, cùng một màu xanh.

⇒ Việc của mutation hôm nay không phải chứng minh test có chạy, mà chứng minh **test có thể đỏ**.

## §1 · Bảy mutant khai TRƯỚC khi viết bài test nào

Thứ tự khai-trước là điều kiện để con số có nghĩa: một bộ mutant viết **sau** khi nhìn test là bộ
mutant kiểm lại danh sách của chính người viết (luật rút từ D17 §1).

**Và thứ tự đó phải kiểm được từ repo, không phải tin lời người viết.** Bảng dưới đây khai ở
`docs/plans/day-19-aie2.md` §T7a — một artifact **riêng**, land ở commit `e8c74f4`, trước mọi commit
mang test:

```bash
git log -1 --format='%ad %h' --date=format:'%H:%M:%S' e8c74f4   # 00:07:43  plan (bảng M-C1…M-C7)
git log -1 --format='%ad %h' --date=format:'%H:%M:%S' 2f55d67   # 00:35:05  commit test đầu tiên
git show e8c74f4:docs/plans/day-19-aie2.md | grep -c '^| `M-C'  # 7
```

*(Bản trước của dòng này viết "bảng này được viết trước commit test đầu tiên" và trỏ vào **chính file
sổ** — mà sổ với test nằm **cùng một commit** `2f55d67`, nên câu đó không kiểm được từ repo. Sửa ở
T7a khi rà lại; ghi cả vết sửa vì một sổ mutation mà chính nó không kiểm được là đúng lớp lỗi nó
sinh ra để bắt.)*

| # | Mutation | Bất biến nó canh | Bài **dự đoán** đỏ | Chạy ở |
|---|---|---|---|---|
| `M-C1` | `sum(e.cost)` → `sum(cost_of(e.tokens))` | `DEC-D19-01` — **đọc**, không tính lại | bài bất đối xứng (`0.75` vs `0.036`) | T2 |
| `M-C2` | bỏ `round(·, 6)` ở tổng | `DEC-D19-03` — luật cộng dùng chung 2 repo | bài conformance (`0.011994...001`) | T2 |
| `M-C3` | `priced` → luôn `False` (bỏ nhánh `Σtokens > 0`) | `DEC-D19-05` — phân biệt *chưa nối giá* vs *đã đo bằng 0* | bài `priced` 2 trạng thái | T2 |
| `M-C4` | bỏ chặn trộn `run_id` | per-run mất nghĩa | bài fail-closed trộn run | T2 |
| `M-C5` | bỏ chặn trộn `tenant_id` | `INV-1` — `obs.trace_events` **không có RLS** | bài fail-closed trộn tenant | T2 |
| `M-C6` | render `.6f` → `.2f` | `DEC-D19-04` — tầng so là **giá trị**, không phải chuỗi | bài in `0.000291` không được ra `0.00` | T3 |
| `M-C7` | mặt B của T4 gọi lại `run_cost_from_trace` thay vì SQL thô | bài *"cùng-1-số"* phải **đỏ được** | bài đối trọng T4 | T4 |

**Luật ghi kết quả (rút từ D17 `M-F3`):** bảng phải ghi **bài nào đỏ**, không chỉ *có đỏ hay không*.
`M-F3` hôm D17 dự đoán 2 bài, thực tế 1 — và chính chỗ lệch đó mới là dữ liệu.

## §2 · `M-C7` là con đáng giá nhất, và nó canh chính bài test của mình

Sáu mutant đầu canh **code sản phẩm**. `M-C7` canh **bài test**: nó biến bài *"cùng-1-số"* của T4
thành đúng cái tautology mình vừa gửi finding cho DE ở `kb#22` (*"hai vế là cùng một lời gọi cùng một
hàm thuần — `f(x) == f(x)` xanh với mọi cài đặt"*).

Nếu `M-C7` **sống**, finding gửi DE tự động áp cho chính mình, và ô DoD của ngày đóng vacuous.

## §3 · Kết quả — T2 (`run_cost_from_trace` + `RunCost`)

Baseline: `176 passed, 1 skipped` (đầu ngày) → **`189 passed, 1 skipped`** sau 13 bài mới của T2.
Mỗi mutant chạy **toàn bộ** suite evalhub, không chỉ file test của nó. Hoàn nguyên rồi chạy lại:
`189 passed, 1 skipped` — khớp baseline, file `run_report.py` byte-identical với bản gốc.

| # | Mutation áp vào `run_report.py` | Dự đoán | **Thực tế** | Kết quả |
|---|---|---|---|---|
| `M-C1` | `sum(e.cost …)` → `sum(tokens.prompt/1000*0.003 + tokens.completion/1000*0.015 …)` | 1 bài | **4 bài** | **DIE** |
| `M-C2` | `round(tong, _COST_ROUND_NDIGITS)` → `sum(...)` trần | 1 bài | **1 bài**, đúng y | **DIE** |
| `M-C3` | `priced` → `False` hằng | 1 bài | **2 bài** | **DIE** |
| `M-C4` | `if len(run_ids) > 1:` → `if False:` | 1 bài | **1 bài**, đúng y | **DIE** |
| `M-C5` | `if len(tenants) > 1:` → `if False:` | 1 bài | **1 bài**, đúng y | **DIE** |

Bài giết, tên đầy đủ (`tests/test_run_cost_from_trace.py`):

| # | Bài đỏ |
|---|---|
| `M-C1` | `test_cost_doc_tu_trace_khong_tinh_lai_tu_tokens` · `test_tokens_khong_he_tham_gia_vao_con_so_cost` · `test_priced_false_khi_co_tokens_ma_cost_bang_0` · `test_src_khong_chua_hang_so_don_gia` |
| `M-C2` | `test_conformance_luat_cong_round_6` |
| `M-C3` | `test_priced_true_khi_tokens_bang_0_la_do_that_bang_khong` · `test_priced_true_khi_co_cost_that` |
| `M-C4` | `test_tron_run_id_thi_raise_RunCostError` |
| `M-C5` | `test_tron_tenant_id_thi_raise_RunCostError` |

### Lệch dự đoán 1 — `M-C1` bắn 4 bài, và hai trong đó nói ra một thứ plan chưa biết

Bài bất đối xứng đỏ đúng như khai. Ba bài kia ngoài dự đoán:

- **`test_src_khong_chua_hang_so_don_gia` đỏ** — bài quét `src/` bắt được `M-C1` vì mutant **phải**
  viết `0.003`/`0.015` vào `src/` mới tính lại được. Tức lưới chống-đơn-giá không chỉ là hàng rào
  cho vi phạm tương lai như khai ở §6 plan; nó là **lưới thứ hai, độc lập**, cho đúng `DEC-D19-01`.
  Một cài đặt tính-lại không thể vừa tránh bài này vừa tránh bài bất đối xứng.
- **`test_priced_false_khi_co_tokens_ma_cost_bang_0` đỏ** — đây là dữ kiện mới và đáng ghi nhất:
  bản tính-lại biến một run *chưa nối giá* (`Σcost == 0`, `Σtokens > 0`) thành một run có cost khác
  `0` ⇒ `priced` lật sang `True`. **`M-C1` không chỉ phá con số, nó phá luôn phân loại trạng thái.**

  ⇒ `DEC-D19-01` và `DEC-D19-05` **không độc lập** như bảng §1 ngầm giả định. Một mặt đọc tự tính
  lại giá sẽ báo *"đã đo"* cho **mọi run trong hệ thống hôm nay** — đúng con số sai nguy hiểm nhất
  của ngày, và nó đến từ một vi phạm ở trục khác.

### Lệch dự đoán 2 — `M-C3` bắn 2 bài, nhưng KHÔNG phải bài đã đoán

Khai ở §1: *"bài `priced` 2 trạng thái"*. Thực tế đỏ là **hai bài `priced is True`**; bài
`test_priced_false_khi_co_tokens_ma_cost_bang_0` **vẫn xanh** — hiển nhiên khi nhìn lại, vì mutant ép
`priced = False` và bài đó khẳng định đúng `False`.

Hệ quả phải nói thẳng: **nếu chỉ viết bài cho trạng thái hôm nay thì `M-C3` sống trọn vẹn.** Trạng
thái *chưa nối giá* (`False`) là trạng thái của mọi run thật hôm nay, nên nó là bài mà người ta tự
nhiên viết trước; còn bài giết mutant lại là bài cho trạng thái **chưa tồn tại trong production** —
*đã đo, bằng 0* (`True`). Cùng hình với `M-F3` của D17 (dự đoán 2 bài, thực tế 1): dự đoán sai,
không phải test sai, và chỗ lệch mới là dữ liệu.

## §4 · Kết quả — T3 (dòng cost ở `render_run_cases` + CLI)

Baseline: `189 → 203 passed, 1 skipped` sau 14 bài mới của T3.

| # | Mutation áp vào `render.py` | Dự đoán | **Thực tế** | Kết quả |
|---|---|---|---|---|
| `M-C6` | `_COST_DISPLAY_NDIGITS = 6` → `2` | 1 bài (`…khong_lam_tron_mat_cost_that`) | **3 bài** — nhưng chỉ sau khi vá test, xem dưới | **DIE** |

Bài giết (sau vá): `test_in_du_6_chu_so_khong_lam_tron_mat_cost_that` ·
`test_in_du_6_chu_so_cho_tong_le` · `test_da_do_bang_0_thi_in_0_000000_chu_khong_phai_chua_do`.

### `M-C6` bắt được HAI bài xanh vacuous của chính mình — đây là giá trị thật của lượt gieo này

Lượt gieo **thứ nhất**, `M-C6` chỉ giết **1** bài, và **không phải** bài đã khai:

```text
gieo lần 1:  FAILED test_da_do_bang_0_thi_in_0_000000_chu_khong_phai_chua_do
             (test_in_du_6_chu_so_khong_lam_tron_mat_cost_that   → VẪN XANH)
             (test_in_du_6_chu_so_cho_tong_le                    → VẪN XANH)
```

Hai bài độ-chính-xác — **đúng hai bài sinh ra để canh `M-C6`** — xanh dưới mutant. Nguyên nhân đo
được:

```python
>>> "0.000291" in _WHY_COST_PRECISION   # khối caveat do CHÍNH MÌNH viết
True
>>> "0.011994" in _WHY_COST_PRECISION
True
```

Bài viết `assert "0.000291" in out` quét **cả** output, mà output mang một khối caveat giải thích
*"in `.2f` thì một cost thật 0.000291 hiện thành `0.00`"* — tức chuỗi cần tìm nằm sẵn trong lời giải
thích về chính lỗi đó. Renderer in `0.00` vẫn xanh.

Vá: mọi khẳng định về **nội dung** dòng cost đi qua `_dong_cost(out)` (rút đúng dòng bắt đầu bằng
`cost (Σ, USD)`, assert có **đúng một**). Gieo lại ⇒ **3 bài đỏ**, gồm đủ hai bài lẽ ra phải đỏ từ
đầu.

**Đây là lần thứ ba trong một ngày cùng một lớp lỗi**, và cả ba đều là *bài xanh vì chuỗi cần tìm
tình cờ có mặt ở chỗ khác*:

| # | Ở đâu | Chuỗi khớp nhầm | Tìm ra bởi |
|---|---|---|---|
| 1 | `kb#22` của DE — `len(surfaces) > 5` | 9 file `scripts/` đỡ cho 12 file `src/` bị bỏ qua | mutant `Z-2` (T1) |
| 2 | `test_in_mau_so_cost_ben_canh_tong` (của mình) | `"event"` khớp `trace_source="obs.trace_events (test)"`; `"6"` khớp `"D16"` | đọc lại khi bài xanh sớm hơn dự kiến |
| 3 | hai bài độ-chính-xác (của mình) | `"0.000291"`/`"0.011994"` khớp khối caveat tự viết | **mutant `M-C6`** |

Luật rút ra, áp cho T4: **một bề mặt render mang prose dài thì `assert <chuỗi> in out` gần như không
bao giờ là một phép kiểm** — phải neo vào **dòng** hoặc **vị trí**, và phải có đối chứng âm (đổi
giá trị ⇒ chuỗi phải đổi). Điều này áp thẳng vào lớp **C** của T4 (*"output UI-test thật sự chứa giá
trị đó"*), nơi cám dỗ viết `assert str(cost) in out` là lớn nhất.

## §5 · Kết quả — T4 (bài "cùng-1-số" ba lớp, cần Postgres)

Baseline: `203 → 210 passed` (có DB; 6 bài T4 + 1 bài DB cũ hết skip). Không DB: `203 passed,
7 skipped`.

| # | Mutation áp vào `tests/test_cost_cung_1_so.py` | Dự đoán | **Thực tế** | Kết quả |
|---|---|---|---|---|
| `M-C7` | `_mat_B_sql_tho` → `run_cost_from_trace(await read_run(...)).cost` | bài đối trọng T4 | **lượt 1: SỐNG** · lượt 2 (sau vá bài): 1 bài | **SURVIVED → DIE** |

Bài giết (sau vá): `test_doi_trong_mat_B_KHONG_di_qua_code_evalhub`.

### `M-C7` SỐNG ở lượt gieo đầu — và đó chính là việc nó sinh ra để làm

Plan viết về `M-C7`: *"nếu `M-C7` **sống**, finding gửi DE ở T1 tự động áp cho chính mình"*. Nó đã
sống thật, ở lượt gieo đầu, với **5/5 bài xanh**.

Bài đối trọng bản đầu dựng theo hình plan gợi ý (*"sửa một `cost` ở một mặt rồi khẳng định bài chính
đỏ"*):

```text
1. A đọc events vào RAM              → A = 0.011994
2. UPDATE obs.trace_events (e1)      → DB nay mang 1.011994
3. B = SQL thô                       → 1.011994
4. assert A != B                     → xanh ✅
```

Gieo `M-C7` ⇒ `_mat_B_sql_tho` thành `run_cost_from_trace(await read_run(...))` — bản thay thế
**cũng đọc lại DB**, nên cũng thấy `1.011994` ⇒ `A != B` vẫn đúng ⇒ **mutant sống**.

**Chẩn đoán:** phép thử đó đo *"B có đọc lại DB không"*, trong khi bất biến cần đo là *"B có đi qua
code `studio_evalhub` không"*. Hai câu khác nhau, và chỉ câu thứ hai mới làm bài "cùng-1-số" hết
vacuous. Một bài đối trọng đo nhầm câu là **đúng lớp lỗi** mà `M-C7` được khai để bắt.

**Vá:** bẻ chính đường đọc evalhub trong module test (`monkeypatch.setitem(globals(), ...)`) rồi
khẳng định mặt B **không đổi**:

- B thật sự độc lập (SQL thô + `sum` của Postgres) ⇒ không đổi ⇒ vẫn ra `0.011994` ⇒ xanh;
- B đi qua `run_cost_from_trace` (`M-C7`) ⇒ nhận giá trị đã bẻ ⇒ **đỏ**.

Gieo lại ⇒ **DIE**.

Bài cũ **giữ lại**, đổi tên thành `test_doi_trong_phep_so_do_duoc_khi_DB_doi` và ghi rõ nó **không**
giết `M-C7`. Nó canh một bất biến khác — *phép so có răng* — và tách bạch hai bất biến vào hai bài
thay vì gộp, vì gộp là cách nhanh nhất để mất một trong hai.

### Tổng kết bốn lượt mutation của ngày

`M-C1…M-C5` (T2) chết ngay lượt đầu. `M-C6` (T3) và `M-C7` (T4) **đều phải gieo hai lượt**, và cả
hai lần lý do giống nhau: **bài test đo nhầm thứ nó tưởng nó đo**.

| Mutant | Lượt 1 | Bệnh của bài | Lượt 2 |
|---|---|---|---|
| `M-C6` | giết 1/3 bài đáng lẽ phải đỏ | `assert <chuỗi> in out` khớp nhầm khối caveat tự viết | 3 bài, DIE |
| `M-C7` | **SỐNG** | bài đối trọng đo *"B có đọc lại DB"* thay vì *"B có đi qua code evalhub"* | 1 bài, DIE |

Cả hai chỉ lộ ra vì mutant được **gieo thật**. Suite xanh ở baseline không nói gì về chuyện này —
đúng câu §0: việc của mutation hôm nay không phải chứng minh test có chạy, mà chứng minh test **có
thể đỏ**.
