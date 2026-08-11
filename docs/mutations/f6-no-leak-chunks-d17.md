# Sổ gieo mutant D17 — `F-6`: `no_leak` đọc `outputs["chunks"]`

**Ngày:** 2026-08-11 (D17) · **Bút:** AIE-2 · **Ref:** `kit#113` (T3 khai, T7 chạy) · `DEC-D17-02/03`

## §1 · Bốn mutant khai TRƯỚC, chạy ở T7 — 4/4 chết

Bộ này được **khai trong plan ở T3, trước khi có bài test nào chạy** (`docs/plans/day-17-aie2.md`
§T3), rồi mới chạy ở T7. Thứ tự đó là điều kiện để con số có nghĩa: một bộ mutant viết sau khi nhìn
test là bộ mutant kiểm lại danh sách của chính người viết.

| # | Mutation | Dự đoán bài đỏ | Thực tế | Kết quả |
|---|---|---|---|---|
| `M-F1` | `no_leak` đọc lại `retrieved_citations` (revert `F-6`) | bài 1+2 | 5 bài, gồm cả 1+2+3 | **DIE** |
| `M-F2` | `None` xử như `[]` (mất fail-closed *"không quan sát được"*) | bài 4 | bài 4 + `test_tu_choi_khong_co_trace_phai_fail_closed` | **DIE** |
| `M-F3` | Trục T1/T6 dùng chung một biểu thức (tái phát bug `89807bc`) | bài 2+3 | **chỉ bài 3** | **DIE** |
| `M-F4` | `chunks_from_trace` đọc `citations` thay `outputs["chunks"]` | bài 1 | 6 bài (3 unit + 3 control) | **DIE** |

Đánh số bài theo bảng T3: 1 = `test_refusal_ro_cheo_tenant_thi_fail` · 2 =
`test_refusal_ro_kho_khac_o_truc_T6_thi_fail` · 3 = `test_refusal_ro_VAI_khac_thi_fail` · 4 =
`test_refusal_khong_co_kb_retrieve_thi_fail`.

## §2 · Một dự đoán lệch — ghi ra vì lệch mới là dữ liệu

`M-F3` dự đoán làm **bài 2 và bài 3** đỏ. Thực tế **chỉ bài 3**. Dự đoán sai, không phải test sai.

`M-F3` bỏ vế vai khỏi luật T6: `in_caller_tenant and all(section_role ∈ allowed)` → `in_caller_tenant`.
Bài 2 dựng một chunk thuộc **kho khác**, nên `in_caller_tenant` đã `False` sẵn ⇒ `no_leak` vẫn `False`
⇒ bài vẫn chấm FAIL đúng ⇒ **không đỏ**. Chỉ bài 3 (chunk đúng kho, **sai vai**) mới phân biệt được.

Đọc đúng: hai trục **không** che nhau, và bài 3 là bài **duy nhất** canh vế vai. Nếu ai đó xoá bài 3
thì `M-F3` sống mà cả bộ còn lại vẫn xanh — đó là điểm mù đã biết của bộ này, ghi ra thay vì để phát
hiện sau.

Script gieo chỉ so `DIE`/`SURVIVE` nên **không** tự bắt được sai lệch này; nó lộ ra vì bộ chạy có in
tên bài đỏ. Bài học: bảng mutation phải ghi *bài nào đỏ*, không chỉ *có đỏ hay không*.

## §3 · Môi trường chạy — bài học `M-L3` (D16)

D16 mất một mutant vì suite chạy trong môi trường thiếu `packages/kb` ⇒ bài canh nó **skip** ⇒ mutant
sống mà không ai biết. Đo lại cho bộ D17:

| Môi trường | `packages/evalhub/tests` |
|---|---|
| CÓ 2 DSN (`docker-compose.test.yml`, 5433) | `126 passed` |
| KHÔNG DSN | `125 passed, 1 skipped` |
| **Riêng 12 bài của T2+T3** | `12 passed` — **không** cần DB, **không** cần `packages/kb` |

⇒ Bộ `M-F1…M-F4` **không** có lỗ `M-L3`: mọi bài canh chúng là unit thuần trên `TraceEvent` dựng
tay. Lượt gieo trên đây chạy **có** DSN (`126 passed` baseline).

## §4 · Gieo chéo — đã làm, và chỗ mời người khác gieo vào mình

`kit#74`: *"mutation chéo 5 bug"*. Tự gieo **không thay** được gieo chéo — D15 đo được 1/3 lượt do
người ngoài gieo, và finding `B2` là bằng chứng điểm mù của người viết có thật.

**Đã gieo vào code người khác trong ngày:**

| Đích | Bộ | Kết quả | Ghi ở |
|---|---|---|---|
| `kb#19` (DE) — fence tại retrieval | 5 mutant khai trước | **4 sống** lượt 1 → DE vá → **1 sống** lượt 2 | [kb#19 review + bảng mutant](https://github.com/AI20K-VGR/agentcore-studio-kb/pull/19) |
| `engine#21` (AIE-1) — `section_roles` server-resolve | 5 mutant khai trước | **5/5 chết** | [engine#21 review](https://github.com/AI20K-VGR/agentcore-studio-engine/pull/21) |

Lượt `kb#19` là lượt đáng giá nhất: `M1` (seam bỏ qua `section_roles`) sống với **204 test vẫn xanh**,
và nó còn làm `test_t6_label_spoof` lật từ `xfailed` sang `xpassed` — chỗ hở không lộ ở cột `failed`
mà ở cột `xpassed`, và `strict=False` nuốt nó.

**Mời gieo vào `evalhub` — nêu chỗ người viết BIẾT là mình chưa đo được**, không đưa bảng gợi ý (bảng
gợi ý biến gieo chéo thành kiểm lại danh sách của người viết):

- Lần cuối AIE-2 tự gieo vào `harness.py`: **hôm nay 11/08**, 4 mutant `M-F1…4`, cả 4 chết.
- Chỗ chưa đo được: **`_no_leak_from_chunks` với `chunks` chứa phần tử thiếu khoá** — `all_parseable`
  đọc `chunk.get("tenant_id")`/`get("section_role")` nhưng chưa bài nào dựng chunk **thiếu hẳn** một
  trong hai khoá đó (mọi fixture đều đủ 5 khoá).
- Chỗ thứ hai: **tương tác giữa `_NOT_PROVIDED` và `None`** khi một caller tương lai truyền
  `retrieved_chunks=None` *có chủ đích* thay vì để mặc định — chưa có bài nào phân biệt hai đường đó
  từ phía caller.
- Món D16 để lại **vẫn chưa ai gieo**: nhánh `results == []` trong `compute.py` (ca fail-closed định
  nghĩa ở D16, `docs/mutations/eval-harness-d16.md` §5).

## §5 · Giới hạn phải nói ra

Bộ chấm **quan sát** hàng rào, không **tạo** hàng rào. `M-F1…4` chứng minh luật chấm có răng trên
`outputs["chunks"]`; chúng **không** chứng minh fence RLS-UUID — cái đó là `#110`/`#112`. Mọi mutant
ở đây gieo vào `harness.py` của evalhub, không gieo vào đường retrieval thật.
