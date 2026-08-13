# D20 · T3/T4 — `gate.verdict` từ một run THẬT, và money-shot chặn vì verdict

> Ô DoD `#128`/`#129`: *"Demo spine 4 bước chạy thật"* + *"AC executable xanh — eval v1 verdict"*.

## State lúc chạy — SHA của **chính lúc chạy**, không dùng lại khối nền

| Repo | SHA lúc chạy | `--porcelain` lúc chạy |
|---|---|---|
| `apps/studio` | **`b866bc2`** | rỗng |
| `packages/evalhub` | **`7684658`** | rỗng |
| `packages/workbench` | `04ca988` | rỗng |
| `packages/kb` | `0194199` | rỗng |
| `packages/engine` | `bfa19cc` | rỗng |

**SHA lúc bàn giao khác SHA lúc chạy, và không im lặng thay bằng SHA cuối:**

| Repo | Lúc chạy số dưới đây | Lúc bàn giao | Vì sao đổi |
|---|---|---|---|
| `apps/studio` | `b866bc2` | `19b7f4d` | T4 land sau T3 |
| `packages/evalhub` | `7684658` | `3a7df0b` | T5 evidence + T6 RLS land sau |

Số ở trang này **tái lập được ở SHA cột giữa**, không phải ở cột phải. Neo `file:line` neo được nội
dung; nó không neo được phiên bản.

---

## 1. Chuỗi đã chạy — không tắt mắt nào

```text
golden-30 (kb/golden/callisto-golden-30-v1.yaml, 30 case)
  → EngineAgentRunner(kb_search=PgKbSearch,          ← KB thật trên Postgres
                      llm=ExtractiveFakeLLM,
                      embedding=_StubEmbedding,
                      trace_writer=PgTraceWriter)    ← trace ghi thật
  → EvalHarness().run(threshold_success=0.9, threshold_citation_accuracy=0.95)
  → compute_scorecard
  → Scorecard(aggregate=…, gate.verdict=…)
```

## 2. Số đo

| Đo | Giá trị | Nghĩa |
|---|---|---|
| `len(results)` | **30** | Chạy đủ bộ |
| `k_success` | **5** | 5/30 case đạt |
| `success_rate` | **0.1667** | Dưới ngưỡng `0.9` |
| `citation_accuracy` | **0.2273** | Dưới ngưỡng `0.95` |
| `n_scored_citation` | **22** | Mẫu số loại đúng 8 case từ-chối (`DEC-04`) |
| `gate.verdict` | **`FAIL`** | — |
| `gate.threshold` | `0.9` / `0.95` | **Không chạm một ký tự** |
| `recipe_hash` | `None` | `DEC-03` chưa có producer |
| `obs.trace_events` | **120 row** | 30 case × 4 node — chuỗi **thật sự** đi qua engine + Postgres |

### Hai câu, không gộp — `DEC-D20-03`

**(a) Chuỗi đã thông.** `gate.verdict` ra được từ một run đi qua engine thật + KB thật + Postgres
thật — **lần đầu tiên trong lịch sử workspace**. Trước hôm nay con số đó là **0 lần**.

**(b) Verdict là `FAIL` vì `ExtractiveFakeLLM` là một double trích câu, KHÔNG vì hàng rào hỏng và
KHÔNG vì agent tệ.** `120` row trace chứng minh engine chạy; `n_scored_citation = 22` chứng minh mẫu
số đúng; `0.1667` đo một double, không đo một agent.

Ai đọc `FAIL` hôm nay thành *"bộ chấm hỏng"* hoặc *"agent tệ"* đều đọc sai. Nó là *"chuỗi đã thông và
hàng rào đang đứng"*.

### ⚠️ FINDING — `success_rate = 0.1667`, không phải `0.2667` như `DEC-D17-04` đo

`DEC-D17-04` đo `success_rate = 0.2667` (8/30) trên cùng golden-30. Hôm nay: **5/30**.

**Không sửa số, không sửa plan.** Ghi lại kèm giả thuyết chưa xác nhận: `packages/engine` hôm nay
đứng ở **`bfa19cc`** — bản D20 của AIE-1 (PR#25, 6-node DAG spine) vừa merge — nên run này đi qua
**engine mới hơn** bản D17 đã đo. Chưa quy được nguyên nhân trong ngày.

**Vì sao nó không làm ô DoD lung lay:** bài T3 **không** hardcode `0.2667` hay `0.1667`. Nó khoá
`len(results) == 30`, `n_scored_citation == 22`, `verdict == "FAIL"` và `trace rows > 0` — bốn thứ
không đổi theo con số này. Một bài ghim `success_rate` vào hằng số sẽ đỏ hôm nay vì một lý do **không
liên quan** tới thứ nó đi tìm.

**Chủ:** AIE-2 (đo lại) + AIE-1 (engine). **Điều kiện lật:** chạy lại cùng golden-30 trên
`engine@62773ba` (bản D17) và so — nếu số về `0.2667` thì nguyên nhân là engine; nếu không, tìm tiếp.
Ngoài đường găng GATE-2, hạn **D21**.

---

## 3. `verdict == "FAIL"` một mình **không chứng minh gì** — và đây là phép đo cho câu đó

`FAIL` là giá trị **dễ trúng nhất**: runner chết, KB rỗng, harness chấm sai, hoặc `compute_scorecard`
trả hằng `"FAIL"` — **mọi** cài đặt hỏng đều ra `FAIL`.

Đo trực tiếp, không lập luận: gieo **`M-G1`** (`compute_scorecard` trả hằng `verdict="FAIL"`).

| Bài | Dưới `M-G1` |
|---|---|
| `test_verdict_fail_tu_run_that` | **VẪN XANH** ✅ |
| `test_runner_tot_lat_verdict_sang_pass` | **ĐỎ** — `assert 'FAIL' == 'PASS'` |

⇒ Nếu hôm nay chỉ có bài live, ô DoD *"eval v1 verdict"* đã **đóng bằng một hằng số** và không ai
biết. Bài đối chứng *"runner tốt ⇒ verdict lật sang PASS"*, chạy trên **cùng chỗ nối**, là thứ duy
nhất làm ô đó **có thể đỏ**.

## 4. `M-G3` — phép đo duy nhất phân biệt *"chạy thật"* với *"trông như chạy thật"*

Gieo: đổi `runner` của bài live từ `EngineAgentRunner` sang `StubAgentRunner` (runner tốt).

```text
FAILED test_verdict_fail_tu_run_that — AssertionError: assert 'PASS' == 'FAIL'
```

**KILLED.** Hai lưới cùng bắt: verdict lật `FAIL`→`PASS`, **và** `obs.trace_events` về 0 (stub không
ghi một dòng nào). Cần cả hai — một mình verdict có thể lật vì lý do khác.

`M-G3` sống ⇒ ô DoD *"Demo spine 4 bước chạy thật"* **không đóng**, bất kể suite xanh. Nó không sống.

---

## 5. T4 — money-shot bước 6/7 trên Postgres thật

| Bài | Đầu vào | Kết quả | Chứng minh |
|---|---|---|---|
| 1 | `recipe_hash=None` + `verdict=PASS` | raise, thông điệp nói **`scorecard.recipe_hash is None`** | Ghim trạng thái **hôm nay**: cổng `:72` chặn kể cả khi verdict hoàn toàn đạt |
| 2 | stand-in hash + `verdict=FAIL` | raise, thông điệp nói **`gate.verdict='FAIL'`**, và `wb.recipes` v1 vẫn `published` | **Bước 7 lần đầu chạy ĐÚNG LÝ DO** — `_reassert_last_published` thật sự chạy |
| 3 | stand-in hash + `verdict=PASS` | publish thành công, `wb.recipes` có row `status='published'` | **Bước 6.** Đối chứng dương: không có nó, hai bài trên không phân biệt *"chặn đúng"* với *"chặn tất"* |

### `M-G4` và một lỗ tìm thấy trong chính bài test

Gieo `M-G4` (bài 2 đổi stand-in → `None`) lần đầu **không** bị `pytest.raises` bắt:

```text
match="verdict"  →  KHỚP, nhưng khớp vào agent_id='gate2-bai2-verdict-fail'
                    trong thông điệp của cổng recipe_hash, KHÔNG vào lý do chặn
```

`publish()` nội suy `agent_id` vào **cả hai** thông điệp, nên một `agent_id` mang tên nhánh làm
`match=` khớp vào **chính cái tên mình đặt**. Bài xanh trong khi cổng đã chặn sai chỗ — đúng lớp lỗi
D19 số 2 (*chuỗi khớp nhầm chỗ khác*), và đúng lớp lỗi mà bài này tồn tại để bắt.

**Vá trước khi commit:** `agent_id` đổi sang tên trung tính (`gate2-case2-blocked-branch`), `match=`
neo vào cụm **chỉ có ở thông điệp cổng** — `scorecard\.recipe_hash is None` và `gate\.verdict='FAIL'`.
Sau vá, **chính `match=` giết được `M-G4`**, không phải assert phủ định làm hộ.

---

## 6. Ô DoD nào đóng, ô nào không

| Ô | Trạng thái | Bằng gì |
|---|---|---|
| `Demo spine 4 bước chạy thật` | ✅ | 30 case qua engine+KB+Postgres thật, 120 row trace, `M-G3` KILLED |
| `AC executable xanh — eval v1 verdict` | ✅ | Verdict ra từ dữ liệu, `M-G1` KILLED bằng bài đối chứng lật PASS, `n_scored_citation=22` |
| `AC executable xanh — cost cùng-1-số` | ⚠️ **nửa đóng, không đổi từ D19** | `engine interpreter.py:73` vẫn `_NO_COST = 0.0`. `DEC-D19-06` giữ nguyên hiệu lực. Điều kiện lật: `price_mismatches` **rỗng** trên một run golden thật **VÀ** `Σcost > 0` — cả hai cùng lúc. Chủ **AIE-1** (`#121`) |
| `plan-vs-actual đối chiếu` | ✅ | [`plan-vs-actual.md`](plan-vs-actual.md) — 5 bảng, 4 dòng đánh dấu D11 SAI |

**Không nằm trong ownership AIE-2, không khai:** gói ZIP · security scan · trạng thái integrated của
cả nhóm. Không có owner/spec nào giao ba món đó cho AIE-2.
