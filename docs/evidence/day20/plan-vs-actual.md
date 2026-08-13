# D20 · plan-vs-actual — design-note D11 đối chiếu **nguyên trạng**

> `DEC-D20-06`. Nguồn: [`docs/design-notes/aie2-day11.md`](../../design-notes/aie2-day11.md),
> **không sửa một chữ** để khớp thực tế. Mỗi dòng bốn cột: **D11 hứa gì** · **thực tế** · **lệch
> chiều nào** · **neo kiểm được**.

**Bắt buộc có cả hai loại dòng.** Một bảng chỉ có dòng D11 **đúng** là một bảng **tự chấm**, không
phải một đối chiếu. Dưới đây có 4 dòng đánh dấu **SAI/LỆCH** và 1 bảng thứ năm cho thứ D11 **không
nhìn thấy**.

## State lúc đối chiếu

| Repo | SHA | `--porcelain` |
|---|---|---|
| `packages/evalhub` | `3a7df0b` | rỗng |
| `apps/studio` | `19b7f4d` (nhánh `aie-2/d20-gate2-verdict-from-live-spine`) | rỗng |
| `packages/workbench` | `04ca988` | rỗng |
| `packages/kb` | `0194199` | rỗng |
| `packages/engine` | `bfa19cc` | rỗng |
| kit | `e1d8d62` | 3 gitlink lệch có chủ đích (xem [README](README.md)) |

---

## Bảng 1 — `§1` non-scope (5 món)

| D11 hứa gì | Thực tế D20 | Lệch | Neo |
|---|---|---|---|
| Wiring publish/rollback đọc `gate.verdict` — *"S3 / D24 — bút SWE"* | **Land D18**, sớm hơn 6 ngày. SWE giao `publish()`/`rollback()` thật; AIE-2 đo nó hôm nay ở T4 | ⚠️ **D11 định giá MUỘN** — hoãn một món đã sắp tới | `workbench@04ca988 publish.py:72,78` · `apps/studio/tests/test_gate2_publish_money_shot.py` |
| Dashboard / trace viewer — *"D25"* | Trace viewer đã có từ D12–D15 | ⚠️ **D11 định giá MUỘN** | `docs/design-notes/playground-trace-ux-d12.md` · `trace-viewer-delta-d15.md` |
| Implement `compute_scorecard` / `EvalHarness.run` — *"phương án bỏ, đúng hạn D16"* | Land **đúng D16** | ✅ **D11 ĐÚNG** | `ceba128` (`kit#108 T2`) · `144c62a` (`kit#108 T4`) |
| Fence chunk-level + trục `INV-1 roles` — *"S3 / D21-22"* | **Tách đôi:** fence chunk-level lên **sớm** ở `F-6`/D17 (`_no_leak_from_chunks`); `INV-1 roles` vẫn **chưa có chủ**, kỳ thứ năm, treo từ D12 | ⚠️ **nửa sớm, nửa muộn** — gộp hai món có nhịp khác nhau vào một ô | `harness.py:240` · `§4` bảng nợ plan D20 |
| Đổi `harness.py:159` — *"GUIDE-C `:305` must NOT be changed"* | Luật vẫn giữ, **không đổi**. Nhưng **anchor `:159` đã mục**: dòng đó nay là docstring `citations_from_trace` | ✅ luật đúng · ⚠️ **neo mục** | `harness.py:157-161` |

## Bảng 2 — `§3` hai phương án BỎ

| D11 hứa gì | Thực tế D20 | Lệch | Neo |
|---|---|---|---|
| **Bỏ 1** — hoãn `compute_scorecard` tới D16, vì GUIDE-C `§3.2` đòi ngưỡng chốt **trước** dataset | Land **D16**, ngưỡng `0.9/0.95` vẫn nằm ở recipe và **chưa từng bị hạ** — kể cả hôm nay, ngày verdict thật đầu tiên ra `FAIL` | ✅ **D11 ĐÚNG**, và đúng vì **lý do đã nêu trước** chứ không phải trúng may | `ceba128` · `builder.py:107,169,242,256` · `DEC-D17-04` |
| **Bỏ 2** — không cho `citation_accuracy` gate `success` ở mức per-case (đếm hai lần một lỗi) | **Vẫn bỏ, lý do vẫn đứng.** Hôm nay đo được vế cụ thể: `citation_accuracy = 0.2273` và `success_rate = 0.1667` là **hai trục độc lập**; gộp chúng sẽ làm một lỗi citation kéo cả hai vế của gate `AND` | ✅ **D11 ĐÚNG** | `compute.py` `DEC-04` · số T3 |

## Bảng 3 — `§4` ba trade-off

| D11 hứa gì | Thực tế D20 | Lệch | Neo |
|---|---|---|---|
| **token-contains**: không bắt **phủ định**, ghi là *"giới hạn đã biết, KHÔNG xfail"*, **lệch LÊN** | **Còn nguyên, vẫn không xfail.** Bài ghi giới hạn vẫn ở đó, không ai lặng lẽ biến nó thành xfail | ✅ **D11 ĐÚNG** — và đây là dòng đắt nhất bảng: lệch LÊN là chiều **nguy hiểm** và nó vẫn mở | `tests/test_smoke_runner.py:254` `test_contains_phrase_negation_known_limitation` |
| **exact-match thay judge** (descope): *"lệch XUỐNG — chiều lệch ĐÚNG cho một hàng rào"* | **Chiều đúng, nhưng D11 chưa bao giờ đo QUY MÔ.** Hôm nay đo lần đầu trên runner thật: **17/22** case nhánh trả-lời rơi vào vùng exact-match không kết luận được | ⚠️ **D11 ĐÚNG chiều, THIẾU độ lớn** — một trade-off không có độ lớn thì không so được với lựa chọn khác | [`agreement-va-judge-routing.md`](agreement-va-judge-routing.md) `§3` |
| **leak sanity mức slug** thay fence UUID: *"chỉ chứng minh tới mức nhãn"* | **Đã lên mức UUID** ở `F-6`/D17 — `_no_leak_from_chunks` so `tenant_id` UUID thật + `section_role` thật | ✅ D11 dự đoán đúng đường ra | `harness.py:240-267` |
| ⤷ và D11 **tự rút một tiền đề của chính mình**: định giá đường lên UUID thành *"mini-RFC + 4/4 chữ ký"* | **`scorecard-v0.md` tự khai câu đó là SAI** ngay tại chỗ, và ghi hệ quả: *"định giá quá cao làm việc bị hoãn vô cớ"* | ❌ **D11 SAI** (đã tự rút) · ⚠️ **và neo trong plan D20 cũng mục**: plan trỏ `:335-337`, chỗ thật là `:350` (câu sai) + `:355` (chỗ rút) | `docs/scorecard-v0.md:350,355` |

## Bảng 4 — `§5` sáu rủi ro

| D11 hứa gì | Thực tế D20 | Lệch | Neo |
|---|---|---|---|
| **Nguồn nhãn tay cho `Judge.agreement`** — 🔴 chặn, chủ AIE-2 + DE, hạn **D18** | **Nửa đóng, và nửa đóng theo cách dễ báo cáo sai.** Có số: `rate=1.0 · n_compared=10 · lệch=[]`. Nhưng `CaseResult.judge` vẫn `None`, và con số **không phải human–machine agreement** — `manual_label` trùng khít `expects_refusal` 10/10, mà `expects_refusal` **dẫn xuất từ chính dữ liệu golden** | ⚠️ **D11 hỏi đúng câu, nhưng câu trả lời hôm nay trả lời một câu KHÁC** | `agreement.py:3-16` · `harness.py:543` |
| **Mọi ngưỡng pin vào stand-in** — 🟡 recalibrate **D16**, chủ AIE-2 | **KHÔNG recalibrate**, và đó là quyết định có neo: `DEC-D17-04` đo điều kiện lật rồi kết luận **KHÔNG ĐỔI**. Điều kiện lật mới: LLM sinh prose thật, ≥30 case — **chưa thoả** | ✅ D11 nêu đúng rủi ro · ⚠️ **hạn D16 trượt**, nhưng trượt **có lý do ghi lại** | `DEC-D17-04` · `DEC-D20-03` |
| **golden-30 về sau corpus D13** — 🟡 hạn D15 | **Đóng.** Golden-30 chạy đủ **30/30** case trên Postgres thật hôm nay, `n_scored_citation = 22` đúng `DEC-04` | ✅ **D11 ĐÚNG**, đã xử đúng hạn | `test_gate2_verdict_from_live_spine.py` |
| **Carrier `citations` là hành vi, không phải cấu trúc** — phía engine ✅ D11; **phía evalhub 🔴 chưa có lưới**, hạn **D16** | **Đóng.** evalhub gom theo `node_type is NodeType.KB_RETRIEVE`, **không** còn node-agnostic | ✅ **D11 ĐÚNG**, đã đóng | `harness.py:133-136` |
| **`refused` cho dương-tính-giả (`#14`)** — 🟡 chủ **AIE-1**, hạn D17 | Ngoài lane AIE-2; không đo lại hôm nay, **không tự nhận** | — không kết luận | — |
| **`eval.scorecards`/`eval.golden_sets` không `tenant_id`, không RLS** — 🟡 chủ AIE-2 + DE, hạn **D16** | **Đóng HÔM NAY (T6, D20)** — 2/2 bảng có `tenant_id NOT NULL` + `ENABLE`+`FORCE` RLS, kiểm cả bằng `pg_class` lẫn bằng ghi/đọc chéo tenant | ⚠️ **TRỄ 4 NGÀY so với hạn D11 tự đặt.** Không làm mềm: đây là món của chính AIE-2, hạn của chính AIE-2 | `schema.py` · `tests/test_eval_schema_rls.py` · `3a7df0b` |

---

## Bảng 5 — rủi ro D11 **KHÔNG nhìn thấy**

> Một plan-vs-actual chỉ chấm những gì plan cũ đã liệt kê thì **không đo được cái plan cũ bỏ sót**.
> Sáu dòng dưới đây không có dòng nào tương ứng trong `§5`.

| Rủi ro D11 bỏ sót | Vì sao D11 không thấy | Đo được hôm nay | Chủ |
|---|---|---|---|
| **`recipe_hash` không có producer ⇒ `publish()` từ chối MỌI `Scorecard`** | D11 xếp nó là *"known gap"* của **hợp đồng**, không xếp là **chặn money-shot**. Hai cách xếp cùng đúng về sự kiện, khác hẳn về mức khẩn | Cổng `:72` đứng **trước** `:78` ⇒ bước 7 (*FAIL → chặn + rollback*) chặn **đúng, vì lý do sai**; `_reassert_last_published` không bao giờ chạy ⇒ **không có rollback** | **SWE** (`DEC-03`, quá hạn D12) — ask ① |
| **Một run N case = N recipe khác nhau** | D11 nghĩ về `Scorecard` như một object; không ai hỏi *"nó chứng nhận **recipe nào**"* | `eval_adapter.py:98` dựng recipe **mỗi case** (`query` trong `Node.params`, `builder.py:208-217`) ⇒ golden-30 sinh **30 recipe** ⇒ câu hỏi không có đáp án đơn nhất | **SWE** + **AIE-1** — ask ① câu 🅐 |
| **Bốn mảnh có test xanh riêng, chỗ nối giữa chúng chưa từng chạy** | D11 kiểm **từng mảnh**, giả định ghép được. Không phép đo nào của D11 nhìn vào *chỗ nối* | `compute_scorecard` 1 call-site trong `src`; `EvalHarness().run` **11/11** trong `tests/` runner stub; `EngineAgentRunner` **4/4** dừng ở `score_case` ⇒ **0 verdict từ run thật, cả lịch sử repo** | AIE-2 — **đóng hôm nay (T3)** |
| **Tiền đề *"judge cho một tập rỗng"* sai trên đường thật** | D18 đo `0/30` với `runner_tot` — runner **đúng theo định nghĩa**. Con số đó được dùng để hoãn việc | Runner thật ⇒ **17/22**. Kết luận *"selector cho tập rỗng"* **không còn đứng** | AIE-2 |
| **`studio_workbench` không import được `studio_evalhub`** ⇒ SWE **cấu trúc mà nói** không làm caller được | D11 chưa cần nghĩ tới ai truyền `recipe_hash` | `grep -rn studio_evalhub packages/workbench/src/` → **rỗng**; `.importlinter:18-21` xếp sibling ⇒ caller đúng là **composition root** | cấu trúc — ghi để đường nối không bị chốt vào một caller không tồn tại |
| **Neo `file:line` neo được NỘI DUNG, không neo được PHIÊN BẢN** | D11 dùng `file:line` khắp nơi như thể chúng bền | 2 anchor mục **trong chính D11/plan D20**: `harness.py:159` và `scorecard-v0.md:335-337`. Đó là lý do mọi bảng số D20 ghi **SHA lúc chạy**, không dùng lại SHA đầu ngày | AIE-2 — đã áp dụng trong bộ evidence này |

---

## Đọc bảng trên như thế nào

**Ba nhóm, và nhóm thứ ba là nhóm đáng đọc nhất:**

1. **D11 đúng (6 dòng)** — `compute_scorecard` hoãn tới D16, citation gate per-case, token-contains
   lệch LÊN, golden-30 sau corpus, carrier citations, đường lên fence UUID. Cả sáu đúng vì **lý do
   đã viết trước**, không phải trúng may.
2. **D11 sai hoặc định giá sai (4 dòng)** — *"mini-RFC + 4/4 chữ ký"* (tự rút) · hoãn
   publish/rollback tới D24 (land D18) · hoãn trace viewer tới D25 · gộp fence chunk-level với
   `INV-1 roles` vào một ô. Ba trong bốn dòng lệch cùng **một chiều: định giá quá cao ⇒ hoãn vô cớ.**
3. **D11 không nhìn thấy (6 dòng)** — và món nặng nhất của D20 nằm **trọn trong nhóm này**:
   `recipe_hash` chặn money-shot, và chỗ nối 4 mảnh chưa từng chạy.

**Hai món trễ hạn của chính AIE-2, khai thẳng:** RLS trên `eval.*` (hạn D11 đặt là D16 → đóng D20,
**trễ 4 ngày**) và recalibrate ngưỡng (hạn D16 → **không làm**, nhưng có `DEC-D17-04` ghi lý do và
điều kiện lật đo được). Món thứ nhất là trễ thật; món thứ hai là quyết định có neo, không phải trễ.
