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

Bảng này được viết **trước** commit test đầu tiên của D19. Thứ tự đó là điều kiện để con số có
nghĩa — một bộ mutant viết sau khi nhìn test là bộ mutant kiểm lại danh sách của chính người viết
(luật rút từ D17 §1).

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

## §4 · Kết quả — T3/T4

Chưa chạy. `M-C6` (T3) và `M-C7` (T4) khai ở §1, kết quả điền khi các T đó chạy.
