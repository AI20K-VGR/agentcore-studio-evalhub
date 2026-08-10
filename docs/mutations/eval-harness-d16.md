# Tự gieo mutant D16 — loader · compute · harness · render · gate

**Ngày:** 2026-08-10 (D16) · **Người gieo:** AIE-2 (chủ quadrant, tự gieo vào code của chính mình)
**Mục tiêu đo:** ba seam vừa land (`load_golden_set`, `compute_scorecard`, `EvalHarness.run`) có
suite **có răng** hay không — hôm nay là ngày code mới nhiều nhất Sprint 2, tức mặt tấn công lớn nhất.

> **Khai TRƯỚC khi chạy.** `M-L1…3` và `M-C1…4` được khai trong `docs/plans/day-16-aie2.md` (§T1, §T2)
> **trước** khi một dòng code nào của D16 được viết. `M-H*`, `M-R*`, `M-T*`, `M-G*` được khai ở đầu
> khối tương ứng, cũng trước code/test của khối đó.

## Giao thức đo (kế thừa `self-render-d15.md`, hai bẫy đã trả giá)

- `PYTHONDONTWRITEBYTECODE=1` — bytecode cache khoá theo `(mtime giây, size)`; sửa trong cùng giây,
  cùng độ dài ⇒ chạy code cũ.
- `--color=no` **và đọc exit code** — regex `FAILED` khớp rỗng trên chuỗi có ANSI escape.
- **Đếm `collected` mỗi lượt.** Collection failure **KHÔNG BAO GIỜ** tính là `caught`, kể cả khi
  pytest báo đỏ đúng số bài mong đợi (`into-engine-d11.md` M5 lượt 1 đã trả giá).
- Mỗi mutant gieo bằng một phép thay chuỗi có `assert` khớp đúng — không khớp thì dừng, không gieo mù.

**Baseline:** `108 passed · 1 skipped · 0 failed · 0 xfailed · 0 XPASS` · `109 tests collected`.

## §1 · Bộ khai trước ở plan — chạy tổng lại ở T10

Bảy mutant dưới đây chạy lại **trong một lượt liên tục** ở T10. Cả bảy: `exit=1`,
`109 tests collected` (không lượt nào là collection failure), restore kiểm bằng `diff` + `git status`.

| # | Mutant | Bài đỏ (đo được) | Kết quả |
|---|---|---|---|
| **M-L1** | loader bỏ qua `expect_ref` (nạp bất kỳ file nào) | `test_loader_doc_ref_mismatch_raises` | ☠️ caught |
| **M-L2** | `ValidationError` bị nuốt thành `cases=[]` | `test_loader_thieu_field_raises` | ☠️ caught |
| **M-L3** | `expects_refusal` chỉ đọc trục T1, bỏ T6 | 5 bài: 2 integration golden-30 · `test_gate_blocks_on_fail` · 2 bài cross-role | ☠️ caught |
| **M-C1** | mẫu số citation dùng `len(results)` | 5 bài, gồm bài chí tử `..._loai_refusal_khoi_mau_so_citation` | ☠️ caught |
| **M-C2** | `>=` → `>` (cả hai trục) | 2 bài **ca biên** | ☠️ caught |
| **M-C3** | `AND` → `OR` | 4 bài, gồm 2 ca lệch một trục | ☠️ caught |
| **M-C4** | `n_scored == 0` trả `1.0` (vacuous PASS) | `..._n_scored_citation_bang_0_thi_none_va_fail` | ☠️ caught |

### Hai chỗ số đo LỆCH với dự đoán trong plan — ghi lại vì đây là phần đáng học

**M-L2 có lưới HẸP HƠN plan viết.** Plan khai *"→ `..._thieu_field_raises` (T1a) **+**
`..._dung_30_case_va_ref` (T1b) phải đỏ"*. Đo được: **chỉ T1a đỏ**. Lý do đo được chứ không đoán —
golden-30 thật của DE **hợp lệ**, nên nhánh nuốt lỗi không bao giờ chạy trên nó. Mutant vẫn chết,
nhưng ai đọc plan mà không đọc dòng này sẽ tưởng có hai lưới ở hai tầng; thật ra chỉ có một.

**M-L3 đúng như plan cảnh báo, và cảnh báo đó quan trọng.** Nó **chỉ** có lưới khi `packages/kb` đã
init: 2 trong 5 bài đỏ là integration. Chạy suite trong môi trường không có submodule kb ⇒ hai bài
đó **skip** ⇒ lưới mỏng đi. Môi trường đo hôm nay có `packages/kb` (xem §4).

## §2 · Bộ khai theo khối, chạy tại chỗ

Mười bốn mutant dưới đây chạy **trong chính khối sinh ra chúng**, có evidence tại thời điểm đó. T10
ghi lại, **không** chạy lại — chạy lại là mở rộng scope mutation ngoài thứ plan T10 yêu cầu.

**Tổng cả ngày: 21 mutant** (7 ở §1 + 14 ở §2).

| # | Mutant | Bài đỏ | Kết quả |
|---|---|---|---|
| **M-H1** | bỏ hẳn luật `no-trace-no-proof` | `test_run_no_trace_no_proof_case_fail` · `test_tu_choi_khong_co_trace_phai_fail_closed` | ☠️ caught |
| **M-H2** | đổi thành *"citation rỗng ⇒ FAIL"* (luật SAI, ngược oracle F02) | 4 bài, gồm integration 30 case | ☠️ caught |
| **M-H3** | `scored_case_ids` lấy **mọi** case | — | 🩸 **SỐNG** → xem §3 |
| **M-H4** | khoá `StubAgentRunner` lùi về `(query, tenant_id)` | integration 30 case · `test_stub_phan_biet_...` | ☠️ caught |
| **M-R1** | caller không truyền mẫu số ⇒ renderer **tự đoán** `len(results)` | `..._mau_so_chua_biet_thi_todo_chu_khong_bia` | ☠️ caught |
| **M-R2** | in `len(results)` thay `n_scored` | `..._noi_ro_mau_so_citation_da_loai_refusal` | ☠️ caught |
| **M-R3** | khung trống in `0.00` thay `todo:` (`DEC-D12-02`) | 2 bài | ☠️ caught |
| **M-T1** | `verdict` hằng số `"PASS"` | 3 bài | ☠️ caught |
| **M-T2** | `>=` → `>` đo qua bài độ nhạy ngưỡng | **đúng** ca biên `0.75/0.75` | ☠️ caught |
| **M-T3** | gate bỏ trục citation | **đúng** dòng nhích trục citation | ☠️ caught |
| **M-G1** | `verdict` hằng số `"FAIL"` (gate chặn **mọi thứ**) | bài đối trọng `test_gate_passes_on_good_recipe` + 5 bài | ☠️ caught |
| **M-G2** | render tự tính qua **tra cứu module** | vế **động** của spy | ☠️ caught |
| **M-G3** | render `import compute_scorecard` vào namespace | vế **tĩnh** của spy, **cả hai** bài render | ☠️ caught |
| **M-G4** | `LLMJudge.judge` stub `Judge(agreement=1.0)` thay vì raise | `test_judge_seam_van_con_notimplemented` | ☠️ caught |

**M-T2 và M-T3 mỗi cái chỉ giết đúng MỘT ca** của bài parametrize — đó là bằng chứng ba dòng tham số
không thừa: mỗi dòng canh một thứ khác nhau, không phải ba cách viết của cùng một phép thử.

**M-G2 chỉ giết bài ở `test_render.py`**, không giết bài ở `test_render_run_cases.py` — vì mutant chỉ
tiêm vào `render_scorecard`. M-G3 giết cả hai. Ghi đúng như đo, không làm tròn thành *"spy bắt hết"*.

## §3 · Mutant SỐNG — `M-H3`, và vì sao nó sống

**Mutant:** `EvalHarness.run` dựng `scored_case_ids` từ **mọi** case, không loại refusal.

**Nó sống sót qua toàn bộ suite ở lượt đo đầu.** Nguyên nhân **không phải thiếu bài** — mà là
**fixture thuận lợi**: bài integration 30 case dùng runner trả lời đúng hết, nên cả 22 case trả-lời
lẫn 8 case từ-chối đều có `citation_accuracy = 1.0`. Với hình dạng đó `22/22` và `30/30` cho ra
**đúng cùng một số** `1.0`, và mẫu số sai **không quan sát được**.

Đây là `DEC-04` lặp lại ở quy mô nhỏ, và là đúng thứ `kit#134` gọi tên: *chỗ hỏng không nằm ở probe,
nằm ở bước từ `8/10` sang tám-mươi-phần-trăm*. Một bài chỉ nhìn **giá trị cuối** trên một bộ mà mọi
nhánh ra cùng con số thì không kiểm được mẫu số — nó chỉ kiểm được rằng phép chia có chạy.

**Bài vá:** `test_run_mau_so_citation_loai_refusal` (`tests/test_harness_run.py`). Fixture ép ba
lượng **tách nhau**:

| cách tính | ra | |
|---|---|---|
| `(0.5 + 0.5) / 2` | **`0.50`** | ← đúng: chỉ 2 case nhánh trả-lời |
| `(0.5 + 0.5 + 1.0) / 3` | `0.667` | mẫu số gồm cả refusal — **chính là M-H3** |
| `(0.5 + 0.5) / 3` | `0.333` | tử số đúng, mẫu số `len(results)` |

**Đã gieo lại M-H3 sau khi vá** và xác nhận mutant chết. Không sửa lặng: mutant sống được ghi ở đây
kèm bài vá, đúng luật T10.

**Bài học đủ tổng quát để đáng ghi:** một fixture "thuận lợi" (mọi nhánh cùng giá trị) làm **cả
mutation lẫn assert** mù cùng lúc. Đây là lần thứ hai cùng một lớp lỗi trong hai ngày — D15 đã trả
giá ở `M11` (`|expected|=2, |retrieved|=1, |giao|=1` ⇒ hai công thức khác nhau ra cùng `0.5`). Luật
rút ra: **fixture nuôi một phép chia thì mọi lượng trong phép chia đó phải đôi một khác nhau.**

## §4 · Môi trường đã chạy mutation — bắt buộc ghi

`M-L3` và một phần `M-C1`/`M-H2` **chỉ có lưới ở tầng integration**, mà tầng đó `skip` khi thiếu
`packages/kb`. Nên môi trường đo là một phần của kết quả, không phải chi tiết vặt — cùng lớp với
chuyện `77 passed` của D15 đo trong shell **không có** `STUDIO_DATABASE_URL_ADMIN`.

| | |
|---|---|
| `packages/kb` | **đã init** — golden-30 đọc được ở `packages/kb/golden/callisto-handbook-30-draft.yaml` (`kb@1e8774f`) |
| Bài integration | **chạy thật**, không skip |
| `STUDIO_DATABASE_URL_ADMIN` | **chưa set** ⇒ `test_scorecard_roundtrip.py` skip (1 skipped) — bài DB, không liên quan mutant nào ở đây |
| Chạy từ | workspace root (`uv run pytest packages/evalhub/tests`) |

## §5 · Tự gieo KHÔNG thay được gieo chéo

D15 đã đo được điều này: 1/3 lượt mutation do người ngoài gieo, và finding `B2` là bằng chứng
**điểm mù của người viết có thật**. `M-H3` của hôm nay là bằng chứng thứ hai, và nó nặng hơn — nó
sống qua chính bộ suite mà người viết vừa tuyên bố là đủ.

⇒ **Mời một người gieo vào `compute.py`.** Nêu rõ *lần cuối gieo vào đâu, khi nào* thay vì đưa một
bảng gợi ý — bảng gợi ý biến gieo chéo thành kiểm lại danh sách của người viết, tức mất đúng thứ
đang cần.

- Lần cuối AIE-2 tự gieo vào `compute.py`: **hôm nay (10/08)**, 4 mutant `M-C1…4`, cả 4 chết.
- Chỗ người viết **biết là mình chưa đo được**: nhánh `results == []` (ca fail-closed mới định nghĩa
  hôm nay, chưa có mutant nào nhắm vào nó) và tương tác giữa `scored_case_ids` với `results` có
  `case_id` trùng.
