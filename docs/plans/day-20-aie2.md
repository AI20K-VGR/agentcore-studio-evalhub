# Plan Day 20 — AIE-2 · GATE-2: `gate.verdict` từ một run THẬT + plan-vs-actual vs design-note D11 · Thứ Sáu 14/08/2026

> **Issue:** `kit#128` (con, AIE-2) dưới `kit#129` (cha, GATE-2 cả nhóm) · **Repo WRITE:** `agentcore-studio-evalhub` · kit READ
> **Vai:** bút của **bộ chấm**. GATE-2 không hỏi *"bộ chấm có chạy không"* — nó hỏi *"spine 4 mảng ghép thật, và eval v1 ra verdict"*.
> **Spec:** `week-2/days/day-20.md` **404** (ngày thứ mười liên tiếp — `docs/requirements` chỉ có `week-1/` + `00-orientation/`) ⇒ `#128` + `#129` là spec thẩm quyền duy nhất.

---

# Executive Summary

Bốn mảnh của money-shot đã tồn tại, mỗi mảnh có test xanh của riêng nó, và **chỗ nối giữa chúng chưa
từng chạy một lần nào**. Đo bằng đếm call-site, không bằng cảm giác:

```text
compute_scorecard   ← call-site trong src/ :  1   (harness.py:551, trong EvalHarness.run)
EvalHarness().run   ← call-site toàn repo  :  8   → 8/8 nằm trong tests/, 8/8 runner = StubAgentRunner
EngineAgentRunner   ← call-site toàn kit   :  3   → 3/3 dừng ở score_case, 0/3 đi tới compute_scorecard
render_scorecard    ← call-site ngoài tests:  0   (đường CLI vẫn in khung `todo:` trống)
```

⇒ **Chưa có một `gate.verdict` nào trong lịch sử workspace được sinh ra từ một run đi qua engine thật
+ KB thật + Postgres thật.** Verdict tồn tại trên đường stub; run thật tồn tại trên đường không có
verdict. Hai đường, hai sự thật, và mỗi đường đều xanh.

Đó chính xác là câu `#129` đòi chứng minh: *"spine 4 mảng ghép thật lần đầu"*.

## Điều đáng ghi nhất, tìm ra khi kiểm nền: **`publish()` từ chối MỌI `Scorecard` mà evalhub dựng được — và từ chối TRƯỚC khi đọc verdict**

SWE đã land `publish()`/`rollback()` thật ở D18 (`workbench` `origin/main` `04ca988`, PR#22). Đọc thứ
tự hai cổng trong đó:

```python
# workbench/src/studio_workbench/publish.py
72:    if scorecard.recipe_hash is None:
74:        raise ValueError("publish: scorecard.recipe_hash is None … refusing")
78:    if scorecard.gate.verdict == "FAIL":
79:        await _reassert_last_published(…)      # ← rollback sống ở ĐÂY
```

Và phía sinh:

```python
# evalhub/src/studio_evalhub/compute.py:117
        # `recipe_hash` chưa có producer (`DEC-03`) ⇒ `None` là giá trị trung thực duy nhất hôm nay.
```

`compute_scorecard` trả `recipe_hash = None` cho **mọi** scorecard. Cổng `:72` chặn trước cổng `:78`.
Hệ quả đo được, hai vế và vế thứ hai nguy hiểm hơn:

| Bước money-shot (`umbrella-contract`) | Điều sẽ xảy ra hôm nay | Vấn đề |
|---|---|---|
| Bước 6 · verdict `PASS` → publish | `ValueError` ở `:72` | **Không chạy được.** Publish từ chối trước khi nhìn verdict |
| Bước 7 · verdict `FAIL` → chặn + rollback | `ValueError` ở `:72` | **Trông như chạy đúng, thật ra sai lý do.** Publish bị chặn — nhưng vì `recipe_hash`, không vì verdict; và `_reassert_last_published` ở `:79` **không bao giờ chạy** ⇒ rollback không xảy ra |

Bước 7 là ô demo dễ tuyên bố nhất của cả gate (*"đã chặn đấy thôi"*), và nó **chặn đúng vì lý do
sai**. Đúng lớp lỗi `F-6` (D17), `refused`-default (D15), `0.0 == 0.0` (D19) — lần thứ tư, lần này
nằm trên ô demo của gate giữa kỳ.

**Món này đến hạn hôm nay, không phải phát sinh hôm nay.** Hợp đồng tự khai:

```text
contracts/src/studio_contracts/scorecard.py:208  recipe_hash: str | None = None
:223  D11 (ruling D-24): "Fix the schemas before Day 20, then write the tests.
      Add `recipe_hash` to `Scorecard`", owner AIE-2
:231  Known gap: this field currently has NO producer … joint decision with SWE
      (pen of `Recipe`) — DEC-03, owner SWE, due D12
```

Hạn D-24 là **Day 20**, tức hôm nay. `DEC-03` quá hạn từ **D12** — tám ngày.

## Bốn số làm nền

| Đo | Kết quả | Nghĩa |
|---|---|---|
| Verdict từ run thật | **0 lần**, cả lịch sử repo | Ô DoD *"eval v1 verdict"* của `#129` chưa có gì đứng sau |
| `recipe_hash` producer | **0** ở cả 5 quadrant (`grep -rn recipe_hash */src` → chỉ evalhub tự khai `None`) | Mọi `Scorecard` bị `publish()` từ chối ở cổng đầu |
| Nhãn tay golden-30 | **10/30** (6 `pass` · 4 `refuse`), `kb` `0194199` trên `main` | Agreement có mẫu số thật, nhưng mẫu số là **10**, không phải 30 |
| Con trỏ `apps/studio` | **`0352176`, đứng yên từ D13** — sau `origin/main` (`db9ec90`) **3 commit** | Composition root — nơi **duy nhất** chỗ nối được phép sống — là con trỏ cũ nhất trong 9 |

## Ô DoD nào đóng được thật

`#128` + `#129` cùng 4 ô. Đọc thẳng, không làm mềm:

| Ô DoD | Đóng được? | Bằng gì |
|---|---|---|
| `Demo spine 4 bước chạy thật` | ✅ | Chỗ nối `EngineAgentRunner` → `EvalHarness.run` → `compute_scorecard`, chạy golden-30 trên Postgres thật, ra `Scorecard` có verdict. **Lần đầu tiên** |
| `AC executable xanh — eval v1 verdict` | ✅ | Verdict là số ra từ run trên; **và** bài chứng minh verdict **đỏ được** (mutant), không phải một hằng số |
| `AC executable xanh — cost cùng-1-số` | ⚠️ **một nửa** — không đổi từ D19 | `interpreter.py:73` `_NO_COST` vẫn nguyên. `DEC-D19-06` giữ nguyên hiệu lực; điều kiện lật vẫn là `price_mismatches` rỗng **và** `Σcost > 0` |
| `plan-vs-actual đối chiếu` | ✅ | Đối chiếu 4 mục của design-note D11 (`§1` non-scope · `§3` hai phương án bỏ · `§4` ba trade-off · `§5` sáu rủi ro), mỗi dòng neo `file:line` hoặc số đo |
| `review ≤2 vòng` | ⚠️ phụ thuộc | Gom lint/format **trước** khi xin review (đã mắc ở D17, nhắc lại D18/D19) |

**Verdict thật của run thật sẽ là `FAIL`, và đó là kết quả đúng để báo cáo.** `DEC-D17-04` đã đo trên
golden-30: `success_rate = 0.2667` (8/30), `citation_accuracy = 1.0000` trên `n_scored = 22`, ngưỡng
`0.9/0.95` **giữ nguyên**. Con số `0.2667` **không đo chất lượng agent** — nó đo một double trả câu
canned. Ai đọc `FAIL` hôm nay thành *"bộ chấm hỏng"* hoặc *"agent tệ"* đều đọc sai; nó là *"chuỗi đã
thông và hàng rào đang đứng"*.

## Ranh giới tự áp cho ngày

1. **Không hạ ngưỡng để demo ra màu xanh.** D11 `§4` chốt chiều lệch đúng của một hàng rào là
   **xuống**; `DEC-D16-05`/`DEC-D17-04` chốt ngưỡng thuộc recipe và giữ nguyên. Hạ số vào đúng ngày
   gate là hiệu chỉnh theo thứ mình muốn nhìn thấy.
2. **Không tự chọn hàm băm cho `recipe_hash`.** Băm **cái gì** quyết định scorecard **chứng nhận cái
   gì**, mà `Recipe` là bút SWE. Xem `DEC-D20-02`.
3. **Không sửa `publish.py`.** Finding đi bằng ask, không bằng commit — `DEC-D15-03` + `kit#74` chấm
   kỷ luật ranh giới quadrant.
4. **Không báo cáo `PASS` ở bất kỳ đâu bằng cách đổi dữ liệu đầu vào.** Nếu cần một nhánh `PASS` để
   chứng minh cổng phân biệt được hai chiều, nó phải là một `Scorecard` **dựng tay trong test**, có
   nhãn rõ là fixture, không phải một run được uốn cho đẹp.

---

# §1 — Nền đã kiểm, không giả định

## Trạng thái 9 con trỏ (kiểm 14/08 đầu ngày)

```bash
git submodule foreach --quiet 'echo "$name $(git rev-parse --short HEAD) behind=$(git rev-list --count HEAD..origin/main)"'
```

| Con trỏ | kit đang trỏ | Sau `origin/main` | Ý nghĩa cho hôm nay |
|---|---|---|---|
| `apps/studio` | `0352176` | **3** | **Chặn T3** — chỗ nối sống ở đây; con trỏ đứng từ D13 |
| `packages/evalhub` | `007acc9` (nhánh D19) | **3** | Nợ D19 chưa đóng — `evalhub#22` còn OPEN |
| `packages/workbench` | `6badd84` | **3** | Thiếu `publish()`/`rollback()` thật của SWE (D18, PR#22) — **cần cho T4** |
| `docs/reports` | `8c4f119` | **2** | Daily-note D19 chưa lên |
| `packages/engine` · `packages/kb` · `packages/contracts` · `apps/web` · `docs/requirements` | — | 0 | Khớp |

**Ba con trỏ chặn việc, không phải chặn mỹ quan.** Chỗ nối T3 cần `apps/studio` (adapter) và T4 cần
`workbench` (publish). Bump là **bước đầu**, không phải bước dọn cuối ngày.

## Nợ D19 chưa đóng khi D20 bắt đầu — đo được

```bash
gh pr view 22 -R AI20K-VGR/agentcore-studio-evalhub --json state,reviews,mergeStateStatus
#   state=OPEN  reviews=[]  mergeStateStatus=BLOCKED   (CI: 3 SUCCESS / 1 SKIPPED)
gh issue view 123 -R AI20K-VGR/agentcore-studio-kit --json state    # OPEN
git -C . log --oneline origin/main..HEAD                            # d74afed (bump engine, CHƯA push)
```

CI xanh, 0 review, chặn ở approval. Đây là **cùng một hình dạng** đã nuốt plan D18 (`kit#74`:
*"artifact không tìm thấy trong fresh clone"*): việc đã xong nhưng chưa land thì với người đọc là
chưa tồn tại. T0a xử trước mọi thứ khác.

## Bốn mảnh, và chỗ nối chưa từng chạy — đo từng mắt

```text
 golden-30 (kb)        runner THẬT              bộ chấm              cổng publish
 ───────────────   ──────────────────      ─────────────────    ──────────────────
 callisto-         EngineAgentRunner       EvalHarness.run      publish()  (SWE)
 golden-30-v1      apps/studio/src/         → compute_scorecard  workbench@04ca988
 30 case           studio_app/              → gate.verdict       :72 recipe_hash
 10 nhãn tay       eval_adapter.py                               :78 verdict
      ✅                  ✅                       ✅                   ✅
      │                   │                        │                    │
      └───────┬───────────┘                        │                    │
              ✗ 0 call-site                        │                    │
                                                   └────────✗───────────┘
                                            mọi Scorecard có recipe_hash=None
```

Lệnh dựng lại bảng trên:

```bash
# 1. Verdict chỉ ra từ đâu
grep -rn "compute_scorecard" packages/evalhub/src/            # 1 call-site: harness.py:551
grep -rn "EvalHarness()\.run(" packages/evalhub               # 8, tất cả trong tests/
grep -rn "StubAgentRunner" packages/evalhub/tests | wc -l     # runner của cả 8

# 2. Runner thật đi tới đâu
grep -rn "EngineAgentRunner" apps/studio                      # 3 call-site
grep -n  "score_case\|compute_scorecard" apps/studio/scripts/e2e_smoke_eval.py
#   → score_case: có ; compute_scorecard: KHÔNG

# 3. Đường trace thật có verdict không
grep -n "compute_scorecard\|Scorecard" packages/evalhub/src/studio_evalhub/run_report.py
#   → 0 hit ngoài docstring. CLI: score_run_from_trace → render_run_cases, hết.

# 4. recipe_hash có producer nào không
grep -rn "recipe_hash" packages/*/src apps/studio/src
#   → chỉ evalhub tự khai None + workbench đọc để từ chối
```

**`run_report` CLI còn một giới hạn thứ hai, ít ai để ý:** `_case_by_id` (`run_report.py:437`) ghim
cứng `callisto-smoke-5-v0` — **5 case**, không phải golden-30. Nên kể cả ngày CLI dựng được
`Scorecard`, mẫu số vẫn là 5. Đường trace thật và đường golden-30 chưa từng là một đường.

## Nền đã có sẵn, không cần dựng lại

| Thứ | Ở đâu | Trạng thái |
|---|---|---|
| Chấm từ trace **đọc ra từ Postgres** | `apps/studio/tests/test_spine_scored_from_postgres.py` | ✅ D7, bút AIE-2 (PR#2, nhánh `aie-2/day09-…`) — **tiền lệ** cho `DEC-D20-01` |
| `EvalHarness.run` chạy đủ 30 case | `tests/integration/test_harness_run_30.py` | ✅ D16, runner **stub** |
| Agreement 3 giá trị | `agreement.py:76` + `nhan_tu_golden_set:117` | ✅ D18 |
| Ngưỡng `0.9/0.95` chốt trước dataset | `workbench/builder.py:169` | ✅ giữ nguyên, `DEC-D17-04` |
| Postgres test-stack | `docker-compose.test.yml` | ✅ `studio-test-postgres-test-1` healthy |

## Dependency/blocker rule (giữ nguyên từ D15…D19)

Món chặn ⇒ **ask có tên chủ + điều kiện lật đo được**, không phải câu than. Món của quadrant khác ⇒
**không tự vào sửa**, kể cả khi diff một dòng. Món hoãn ⇒ **chủ + hạn + điều kiện lật**; 0 món hoãn
vô chủ trong tập AIE-2.

---

# §2 — Quyết định phải chốt hôm nay

## DEC-D20-01 · Chỗ nối GATE-2 sống ở composition root (`apps/studio/tests/`), **không** ở evalhub

**Vì sao không có lựa chọn khác:**

```ini
# .importlinter:18-21
layers =
    studio_app
    studio_kb | studio_engine | studio_workbench | studio_evalhub
    studio_contracts
```

Bốn quadrant **sibling** ⇒ `studio_evalhub` không import được `studio_kb` (`PgKbSearch`) hay
`studio_engine` (`interpreter`). Phép nối cần cả ba trong **một tiến trình**. `studio_app` là tầng
trên, là chỗ **duy nhất** hợp lệ.

**Tiền lệ, không phải ngoại lệ mới:** `test_spine_scored_from_postgres.py` đã sống ở
`apps/studio/tests/` từ D7, bút AIE-2, merge qua PR#2 — với **cùng lập luận** ghi ngay trong docstring
của nó. Và `.importlinter` ràng buộc `src/`, **không quét `tests/`**.

**Ranh giới vẫn giữ:** chỉ thêm **file test mới**; không sửa `src/studio_app/`, không sửa
`eval_adapter.py`, không sửa `e2e_smoke_eval.py`. Hai finding đã biết ở `apps/studio` (`E-1`
`{:<6.2f}`) đi bằng ask ②, không bằng commit.

## DEC-D20-02 · `recipe_hash` — evalhub **nhận** giá trị, tuyệt đối **không tự dẫn xuất**

`compute_scorecard` nhận thêm `recipe_hash: str | None = None`, **keyword-only**, truyền thẳng vào
`Scorecard`. Additive: `None` là default ⇒ 8 call-site hôm nay không đổi một dòng.

**Vì sao không tự băm ở trong evalhub, kể cả khi `hashlib.sha256(recipe.model_dump_json())` là hai
dòng:** băm **cái gì** chính là câu *"scorecard này chứng nhận cái gì"*. `Recipe` là bút SWE. Nếu
evalhub chọn `model_dump_json()` thì ngày SWE thêm một field tuỳ chọn vào `Recipe`, **mọi scorecard
đã lưu mất hiệu lực trong im lặng** — không lỗi, không cảnh báo, chỉ có một hash không khớp và không
ai biết vì sao. Đó là `DEC-03`, chủ **SWE**, quá hạn từ D12 — ask ①.

**Đây cùng một luật với `DEC-D19-01`**, chỉ khác trục: *đọc, không tính lại*. D19 cấm suy `cost` từ
`tokens`; D20 cấm suy `recipe_hash` từ `Recipe`. Cả hai vì cùng lý do: hai nơi tính ra một giá trị
thì ngày luật đổi một chỗ, không mặt nào biết mặt nào đúng.

**Hôm nay giá trị đến từ đâu:** test T4 truyền một hash **dựng tay trong fixture**, có nhãn rõ là
stand-in. Nó đủ để chứng minh cổng `:78` phân biệt được `PASS`/`FAIL`, và **không** giả vờ là một
producer. Producer thật vẫn khai là nợ, có chủ, có điều kiện lật.

## DEC-D20-03 · Verdict `FAIL` từ run thật là **kết quả đúng**; không hạ ngưỡng, không đổi fixture cho đẹp

Ba neo, cả ba đã có từ trước hôm nay:

- `DEC-D17-04` — điều kiện lật ngưỡng cũ **đã thoả và đã đo**; kết luận **KHÔNG ĐỔI**. Điều kiện lật
  mới: số từ một LLM **sinh prose thật, không biết trước nhãn**, trên ≥30 case. Chưa thoả.
- D11 `§4` — chiều lệch đúng của một hàng rào là **xuống**: gate có thể chặn bản đạt, **không** cho
  lọt bản không đạt.
- GUIDE-C `§3.2` — ngưỡng là số chốt **trước** dataset. Hạ nó sau khi thấy số là đúng thứ điều khoản
  đó cấm.

**Cách báo cáo bắt buộc hai câu, không gộp:** (a) chuỗi đã thông — verdict ra từ run thật; (b) verdict
là `FAIL` vì fixture LLM là double trả câu canned, **không** vì hàng rào hỏng hay agent tệ. Một câu
*"eval v1 chạy được"* không kèm câu thứ hai là báo cáo thiếu.

## DEC-D20-04 · Agreement báo **ba giá trị + một câu nói nó đo gì**; và khai thẳng đang ở nấc descope

`#128` viết *"judge-agreement vs nhãn tay **có số** (hoặc exact-match descope)"*. Đóng **cả hai vế**,
vì chúng không loại trừ nhau:

- **Số:** `agreement(*nhan_tu_golden_set(golden_30))` → `rate` · `n_compared` · `lệch`. Mẫu số là
  **10**, không phải 30 — 20 case chưa có nhãn tay. Một `rate` trần không mẫu số là đúng thứ
  `kit#134` gọi là bằng chứng dị dạng.
- **Câu nói nó đo gì:** đây **không** phải human–machine agreement. `agreement.py:3-16` đã ghi:
  `manual_label` trùng khít `expects_refusal` 10/10, mà `expects_refusal` là thuộc tính **dẫn xuất**
  từ chính dữ liệu golden ⇒ nhãn tay không mang thông tin độc lập. Cái nó đo là **đồng thuận ngữ
  nghĩa hàng rào kb ↔ evalhub** — một regression detector cho semantic drift giữa hai repo.
- **Descope:** `DESCOPE.md` khai nấc *LLM-judge → exact-match scorer*, và evalhub **đang ở nấc đó**.
  Khai bằng **số**, không bằng lời: đếm bao nhiêu case định tuyến sang judge trên run thật của T3.
  Dự đoán **0** (khớp phép đo D18 *"0/30 case cần judge"* với runner tốt); nếu ra khác 0 thì con số
  đó là finding, không phải nhiễu.

## DEC-D20-05 · `eval.scorecards` thêm `tenant_id` + RLS **hôm nay**, vì hôm nay là ngày verdict đầu tiên tồn tại

`kb#24` đã lật `eval.scorecards` từ *KHÔNG CẦN* sang **CẦN RLS** — tiêu chí là **bản chất data**,
không phải *ai đọc*. Lập luận đã nêu khi review: `harness.py:463` đổ `actual`/`expected` vào
`results JSONB`, tức bảng chứa **answer-text của tenant**.

**Vì sao là hôm nay chứ không phải "khi có writer":** RLS land **trước** writer đầu tiên là một dòng
DDL; land **sau** là migration trên bảng đã có dữ liệu của nhiều tenant, cộng một câu hỏi không trả
lời được (*"dữ liệu đã ghi trước đó thuộc tenant nào"*). Hôm nay là ngày `Scorecard` thật đầu tiên
tồn tại ⇒ đây là ngày cuối cùng món này còn rẻ. Tự khai của D11 `§5`: workspace có RLS trên **1/11**
bảng, hai bảng của AIE-2 là **0/2**.

**Phạm vi:** chỉ `schema.py` của evalhub (`eval.golden_sets` + `eval.scorecards`) — lane AIE-2, không
đụng `apps/studio/core/schema.py` (`ensure_all_schemas` direct-import `ddl()`, antichain).

## DEC-D20-06 · plan-vs-actual đối chiếu **D11 nguyên trạng**, và nói cả chiều D11 SAI

Không sửa design-note D11 cho khớp thực tế. Mỗi dòng bốn cột: **D11 hứa gì** · **thực tế** · **lệch
chiều nào** · **neo kiểm được**. Bắt buộc có cả hai loại dòng:

- dòng D11 **đúng** (vd: *"`compute_scorecard` đúng hạn là D16"* — land D16, `kit#108`);
- dòng D11 **sai hoặc định giá sai** (vd: `scorecard-v0.md:335-337` định giá đường lên fence mức UUID
  thành *"mini-RFC + 4/4 chữ ký"* — **sai**, và định giá quá cao làm việc bị hoãn vô cớ; D11 `§4` đã
  tự rút tiền đề đó).

Một bảng chỉ có dòng đúng là một bảng tự chấm, không phải một đối chiếu.

---

# §3 — Work items: thứ tự là quyết định, không phải danh sách

> Ngân sách ~7h. Đường găng: **T0a → T2 → T3 → T4**. Ba con trỏ phải bump **trước T3**, nên T0a không
> phải việc dọn dẹp — nó là bước 1 của đường găng.

## T0a · Đóng nợ D19 + bump 3 con trỏ — **P0, đường găng** (40′, làm đầu tiên)

Bốn việc, thứ tự cố định:

1. Xin approval `evalhub#22` (CI xanh, 0 review, `BLOCKED`). **Không push thêm gì trước khi xin** —
   push làm bay approval, đã mắc ở D17.
2. Merge `evalhub#22` bằng **merge-commit** (quy ước repo: `#16`, `#17`, `#19`, `#20`, `#21`).
3. Bump 3 con trỏ trong kit: `packages/evalhub` · `packages/workbench` (cần cho T4) ·
   `apps/studio` (cần cho T3) + push `d74afed` đang treo local. `docs/reports` bump ở T8b cùng
   daily-note.
4. Comment + close `kit#123`. Comment phải dẫn `DEC-D19-06` nguyên văn hai vế (đường đọc đóng · số
   thật không đóng), không rút gọn thành *"cost-lineage xong"*.
5. Dán nguyên văn `git submodule status` + `git rev-parse HEAD` của kit vào đầu
   `docs/evidence/day20/` làm **khối SHA nền** của ngày.

**Kiểm bước 3 bằng `git submodule status`, không bằng `ls`** — cùng phép kiểm đã nuốt im lặng
`day-13`/`day-14`/`day-18`.

**Khối SHA nền là nền, không phải là câu trả lời.** T3/T4/T5 chạy **giữa** ngày, mà `evalhub` còn đổi
tiếp sau đó (T6 · T8a · lint/format · vá review) trước khi merge ⇒ SHA lúc chạy số **khác** SHA lúc
bàn giao. Nên mỗi bảng số trong evidence ghi SHA của **chính lúc chạy** — `evalhub`, cộng
`apps/studio` và `workbench` cho T3/T4 — không dùng lại SHA đầu ngày. Neo `file:line` neo được **nội
dung**; nó không neo được **phiên bản**.

**Trước mỗi lần chạy evidence: `git status --porcelain` rỗng** ở `packages/evalhub` (và `apps/studio`
cho T3/T4). Một con số chạy trên sửa local chưa commit là con số của một state **không tồn tại ở bất
kỳ commit nào** — không ai tái lập được, kể cả chính mình sau khi lint/format. Đây đúng gốc sự cố
`.pyc` ở D19 (*state chạy ≠ state khai*), chỉ khác tầng: ở đó runtime lệch file, ở đây file lệch commit.

## T0b · Kiểm nền + comment hình dạng ngày — **P0** (20′)

Chạy 4 lệnh `§1`. Nếu số nào khác plan này — đặc biệt: `recipe_hash` đã có producer, hoặc `_NO_COST`
đã bị thay, hoặc `publish.py` đã đổi thứ tự hai cổng — ⇒ **sửa plan trước, không chạy tiếp theo trí
nhớ**.

Comment lên `#128`: hình dạng ngày + con số *"verdict từ run thật: 0 lần"* + câu *"verdict hôm nay sẽ
là FAIL và FAIL là kết quả đúng"*. Nói **trước** lúc bắt đầu, không nói lúc đóng ngày — một dự đoán
viết sau khi thấy kết quả không phải là dự đoán.

## T1 · Ask ① gửi SWE về `recipe_hash` — **P0, gửi SỚM** (20′)

Gửi ngay sau T0b vì nó **chặn money-shot của cả nhóm** và cần người khác quyết. Không chờ có code rồi
mới hỏi: đây là món quá hạn D12, và ngày gate là ngày cuối để nó còn kịp.

**Hai câu hỏi, không phải một, và câu ② chặn câu ①** — ① băm trên nội dung nào · ② recipe **nào** được
chứng nhận khi một scorecard gộp N case. Câu ② là finding đo được sáng nay, không có trong `DEC-03`:
`eval_adapter` dựng một recipe **mỗi case**, nên golden-30 sinh 30 recipe. Hỏi ① mà bỏ ② sẽ nhận về
một quy tắc băm đúng cho một thứ không xác định.

**Gửi cho SWE, CC AIE-1** (câu ② chạm adapter). **Không** gửi như *"SWE truyền hộ tại điểm gọi
evalhub"* — điểm gọi đó không tồn tại (`§5` ①), và một ask dựng trên một call-site tưởng tượng sẽ
quay lại thành một vòng review mất công cả hai phía.

Nội dung ở `§5` ①. Kèm **bảng hai chiều đo được**, không chỉ câu hỏi — finding phải đứng được kể cả
khi không ai trả lời trong ngày.

## T2 · `compute_scorecard(recipe_hash=…)` additive — **P0, đường găng** (45′)

Đỏ trước, theo thứ tự:

1. Bài: truyền `recipe_hash="abc123"` ⇒ `Scorecard.recipe_hash == "abc123"`. Đỏ hôm nay vì tham số
   chưa tồn tại — **`TypeError` do sai chữ ký tính là đỏ đúng lý do**; `ImportError` thì không.
2. Bài: **không** truyền ⇒ `recipe_hash is None`, và 8 call-site cũ không đổi hành vi. Đây là bài giữ
   tính additive, không phải bài thừa.
3. Bài **cưỡng chế `DEC-D20-02`**: quét `src/studio_evalhub/` không có `hashlib`, không có
   `model_dump_json()` trong đường dựng `Scorecard`. Cùng hình với `test_src_khong_hardcode_duong_dan_kb`
   — bắt cả vi phạm **tương lai**, không chỉ hôm nay.

Bài 3 là bài quan trọng nhất trong T2: nó biến `DEC-D20-02` từ một câu trong plan thành một lưới.

## T3 · Chỗ nối GATE-2 — verdict từ run THẬT — **P0, đường găng, ô DoD** (1h45)

File mới: `apps/studio/tests/test_gate2_verdict_from_live_spine.py`.

Chuỗi, không tắt mắt nào:

```text
golden-30 (kb/golden/callisto-golden-30-v1.yaml)
  → EngineAgentRunner(kb_search=PgKbSearch, llm=ExtractiveFakeLLM, trace_writer=PgTraceWriter)
  → EvalHarness().run(golden_set_path=…, runner=…, tenant_ids=…, threshold_success=0.9,
                      threshold_citation_accuracy=0.95)
  → Scorecard(aggregate=…, gate.verdict=…)
```

**Bốn assert, và mỗi cái canh một thứ khác nhau:**

| Assert | Canh gì | Vì sao không bỏ được |
|---|---|---|
| `len(scorecard.results) == 30` | Chạy đủ bộ | Một mình nó **không** phân biệt *"chạy đúng 30"* với *"chạy 30 lần chấm sai một nửa"* |
| `aggregate.n_scored_citation == 22` | Mẫu số citation loại 8 refusal (`DEC-04`) | Sai mẫu số là chỗ một bản đáng FAIL lại PASS ngay ngưỡng |
| `gate.verdict == "FAIL"` | Verdict là số ra từ dữ liệu | **Chưa đủ** — xem hàng dưới |
| `verdict đỏ được` (mutant `M-G1`) | Verdict **không** phải hằng số | Một `verdict == "FAIL"` xanh với cả cài đặt *"luôn trả FAIL"*. Đây là bài giữ ô DoD **có thể đỏ** |

**`M-G1` là điều kiện của ô DoD, không phải phần thêm.** Bài học D19: *"việc của ngày không phải làm ô
DoD xanh; nó là làm ô DoD **có thể đỏ**"* — bốn lần trong một ngày một bài xanh vì thứ nó đi tìm tình
cờ có mặt ở chỗ khác. Ở đây `FAIL` là giá trị **dễ trúng nhất**: mọi cài đặt hỏng đều ra `FAIL`. Nên
phép đối chứng phải là *"cho runner tốt ⇒ verdict lật sang PASS"*, chạy trên cùng chỗ nối.

### Docker/Postgres không lên — phân biệt hai ca, đừng gộp

- **Stack không lên** ⇒ ghi **BLOCKED** đủ ba điều kiện (lệnh đã chạy · lỗi nguyên văn · điều kiện
  lật). **Không** hạ bài xuống in-memory: đường Postgres **là** thứ đang được khẳng định.
- **Stack lên nhưng test skip** vì thiếu DSN ⇒ đó là lỗi cấu hình của mình, sửa, không ghi BLOCKED.

## T4 · Money-shot: publish chặn **vì verdict**, không vì `recipe_hash` — **P0, ô DoD** (45′)

Ba bài, và bài thứ ba là bài thật:

1. `recipe_hash=None` + `verdict` bất kỳ ⇒ `publish()` raise, và **thông điệp nói `recipe_hash`**.
   Ghim trạng thái hôm nay để nó không trôi trong im lặng.
2. `recipe_hash="<stand-in>"` + `verdict="FAIL"` ⇒ raise, **thông điệp nói `verdict`**, và
   `_reassert_last_published` **đã chạy** (rollback thật xảy ra). Đây là bước 7 money-shot, lần đầu
   chạy đúng lý do.
3. `recipe_hash="<stand-in>"` + `verdict="PASS"` ⇒ publish thành công, `wb.recipes` có row
   `status='published'`. Bước 6.

**Bài 1 và bài 2 phải phân biệt được bằng chuỗi thông điệp, không chỉ bằng `pytest.raises(ValueError)`.**
Cả hai raise cùng kiểu; một bài chỉ bắt kiểu sẽ **xanh với cả hai lý do** — đúng lớp lỗi đang đi tìm.

Bài 2/3 dùng `Scorecard` **dựng tay trong fixture**, có nhãn rõ là stand-in (`DEC-D20-02`). Không uốn
run thật của T3 để ra `PASS`.

## T5 · Agreement có số + đếm định tuyến judge — **P0, ô DoD** (40′)

1. Chạy `agreement(*nhan_tu_golden_set(golden_30))` → ghi **ba** giá trị.
2. Đếm trên run T3: bao nhiêu case rơi vào nhánh judge (`not expects_refusal and not scored.success`).
   Đây là số **chưa ai đo** — D18 đo *"0/30 với runner tốt"*, hôm nay runner là
   `ExtractiveFakeLLM` thật, nên con số có thể khác. Nếu khác 0 ⇒ finding.
3. Ghi vào evidence: ba giá trị + câu `DEC-D20-04` nói nó đo gì + nấc descope hiện tại.

## T6 · `eval.scorecards` + `eval.golden_sets`: `tenant_id` + RLS — **P1** (45′)

DDL trong `schema.py`, idempotent như phần còn lại. Bài test: `ddl()` chứa `ENABLE ROW LEVEL SECURITY`
+ policy cho cả hai bảng, và `tenant_id` là `NOT NULL`.

**Cắt trước tiên nếu hết giờ** — nhưng cắt thì phải ghi nợ kèm câu *"hôm nay là ngày cuối món này còn
rẻ"* (`DEC-D20-05`), không ghi trần một dòng.

## T7 · plan-vs-actual + evidence GATE-2 — **P0, ô DoD** (1h)

`docs/evidence/day20/plan-vs-actual.md` (cùng chỗ với `docs/evidence/day14/`).

Bốn bảng, đối chiếu D11 nguyên trạng theo `DEC-D20-06`:

| Nguồn D11 | Số dòng | Nội dung |
|---|---|---|
| `§1` non-scope | 5 | Mỗi món: đã làm ở ngày nào / vẫn non-scope / đã đổi chủ |
| `§3` hai phương án bỏ | 2 | *Bỏ 1* (`compute_scorecard` hoãn tới D16) — **D11 đúng**, land D16 `kit#108`. *Bỏ 2* (citation gate per-case) — vẫn bỏ, lý do vẫn đứng |
| `§4` ba trade-off | 3 | token-contains lệch **LÊN** ở ca phủ định — còn nguyên, chưa xfail. Fence mức slug → đã lên mức UUID (`F-6`, D17). Định giá *"mini-RFC + 4/4 chữ ký"* — **D11 SAI**, tự rút |
| `§5` sáu rủi ro | 6 | Trạng thái + chủ + điều kiện lật, tính đến hôm nay |

Cộng một bảng thứ năm: **rủi ro D11 KHÔNG nhìn thấy** — `recipe_hash` không có producer chặn
`publish()` (D11 xếp nó là *"known gap"* của hợp đồng, không xếp là **chặn money-shot**). Một
plan-vs-actual chỉ chấm những gì plan cũ đã liệt kê thì không đo được cái plan cũ **bỏ sót**.

## T8a · Tự gieo mutant — **P0, TRONG merge-ready** (45′)

Khai bảng **trước** khi viết test, ghi **bài nào đỏ**, không chỉ có-đỏ-hay-không.

| # | Mutant | Dự đoán | Canh bất biến nào |
|---|---|---|---|
| `M-G1` | `compute_scorecard` trả `verdict="FAIL"` hằng | DIE ở bài runner-tốt (T3) | Verdict là **số ra từ dữ liệu** |
| `M-G2` | `compute_scorecard` bỏ `recipe_hash` (luôn `None`) | DIE ở T2 bài 1 | Tham số thật sự được truyền qua |
| `M-G3` | Chỗ nối T3 đổi `runner` sang `StubAgentRunner` | DIE — nếu SỐNG thì chỗ nối **không** đi qua engine thật | `DEC-D20-01`: đây là bài canh chính bài test |
| `M-G4` | T4 bài 2 đổi `recipe_hash` stand-in → `None` | DIE ở assert chuỗi thông điệp | Hai lý do raise **phân biệt được** |
| `M-G5` | `agreement` trả `rate` mà `n_compared=0` | DIE ở bài mẫu số | `rate=None ≠ 0.0` (`DEC-D16-03`) |
| `M-G6` | `ddl()` bỏ `ENABLE ROW LEVEL SECURITY` | DIE ở T6 | RLS có thật trong DDL, không chỉ trong plan |

`M-G3` là con đáng giá nhất: nó là phép đo duy nhất phân biệt *"chỗ nối chạy thật"* với *"chỗ nối
trông như chạy thật"*. Nếu nó SỐNG, ô DoD `Demo spine 4 bước chạy thật` **không đóng**, bất kể suite
xanh.

**Dọn `__pycache__` rồi kiểm giá trị runtime, không chỉ kiểm file + `git diff`** — luật rút từ D19:
một mutant **cùng kích thước file** có thể không bao giờ có hiệu lực, và người gieo ghi `SURVIVED`
cho một mutant chưa từng được gieo.

## T8b · Đóng ngày — **P0** (30′) · đứng SAU tất cả

Daily-note `docs/reports/daily-notes/2026-08-14-dholmes0207.md` + bump `docs/reports` + comment đóng
`#128`, và comment lên `#129` phần của AIE-2.

**Chạy `git submodule status` + `git status --porcelain` lần cuối, đối chiếu với khối SHA nền T0a.**
Con trỏ nào đã đổi trong ngày ⇒ daily-note ghi **cả hai** SHA (lúc chạy evidence · lúc bàn giao).
Con trỏ đổi là bình thường; **con trỏ đổi mà báo cáo im lặng** mới là thứ làm evidence mất giá trị —
người tích hợp mở SHA bàn giao ra và không dựng lại được con số đã đọc.

**Comment đóng khai đúng bốn thứ:** (a) phần GATE-2 **của AIE-2** xong hay chưa xong; (b) evidence
chạy trên **state nào** — SHA, không phải *"trên main"*; (c) dependency nào còn **BLOCKED**/chưa land
(`recipe_hash` · `_NO_COST` · con trỏ của quadrant khác); (d) món nào hoãn, kèm chủ + điều kiện lật.

**Thứ thứ năm không khai, kể cả khi nghe được từ người khác:** gói ZIP đã tạo hay chứa đủ workspace ·
security scan đã chạy hay PASS · cả nhóm đã integrated xong. Không có owner/spec nào giao mấy món đó
cho AIE-2, nên khai chúng là **khai thay người khác** — một câu xác nhận không có phép đo của chính
mình đứng sau, đúng lớp lỗi cả tuần đi tìm, chỉ khác là nó nằm ở tầng báo cáo chứ không ở tầng test.

Không đóng ngày khi: `evalhub#22` chưa merge · con trỏ `apps/studio`/`workbench` chưa bump ·
`M-G3` còn sống · bảng số nào trong evidence không có SHA đi kèm.

## Thứ tự cắt nếu hết giờ

`T6` → `T5` bước 2 → `T7` bảng thứ năm. **Không cắt** `T8a`: một ngày gate không có mutant là một
ngày gate không có phép đo.

---

# §4 — Bảng nợ đến hạn D20

| Món | Chủ | Trạng thái vào D20 | Xử lý hôm nay |
|---|---|---|---|
| **`evalhub#22` OPEN, `kit#123` OPEN** — nợ D19 | AIE-2 | CI xanh, 0 review, `BLOCKED` | **T0a** |
| **3 con trỏ lệch** (`apps/studio` −3 · `workbench` −3 · `evalhub` −3) | AIE-2 bump | `apps/studio` đứng từ D13 | **T0a**, trước T3/T4 |
| **`recipe_hash` không có producer** ⇒ `publish()` từ chối mọi Scorecard | **SWE** (`DEC-03`, pen của `Recipe`) | **quá hạn D12** — 8 ngày; hạn D-24 của hợp đồng là **hôm nay** | ask ① câu ①. T2 mở đường nhận; **không** tự băm |
| **Một run N case = N recipe khác nhau** (mới, đo hôm nay) — `eval_adapter` dựng recipe **mỗi case**, `query` nằm trong `Node.params` (`builder.py:209-215`) ⇒ golden-30 sinh 30 recipe | **SWE** (bút `Recipe`) + **AIE-1** (adapter) | chưa ai nêu; adapter tự khai giới hạn từ D6 | ask ① câu ②. **Chặn câu ①**: chưa có recipe ổn định cho cả run thì `recipe_hash` không mang nghĩa, bất kể băm bằng gì |
| **`studio_workbench` không import được `studio_evalhub`** ⇒ SWE không làm caller truyền `recipe_hash` được | cấu trúc (`.importlinter` sibling) | đo hôm nay: `grep -rn studio_evalhub packages/workbench/src/` → rỗng | Không phải món phải vá. Ghi để đường nối không bị chốt vào một caller **không tồn tại**; caller đúng là composition root |
| **Verdict chưa từng ra từ run thật** | AIE-2 | 0 call-site | **T3** — ô DoD chính |
| **`eval.scorecards` cần `tenant_id` + RLS** (`kb#24` đã lật) | AIE-2 | 0/2 bảng có RLS | **T6**. Hôm nay là ngày cuối còn rẻ |
| **Sổ quyết định thiếu `DEC-D17-01/-02/-03/-05`** — plan D17 khai 5 id, sổ chỉ có `-04` | AIE-2 | treo từ D19 | Gộp vào T8b nếu còn giờ; nếu không ⇒ nợ có hạn **D21** |
| **`RuntimeWarning` ở happy-path `run_report`** | AIE-2 | có từ D19/T3, output vẫn đúng | Nợ, hạn **D21**. Điều kiện lật: CI bật `-W error` |
| **`E-4`** — run **không chấm được** vẫn có `Σcost` | AIE-2 | ghi ở design-note D19 | Nợ. Điều kiện lật: consumer đầu tiên hỏi hai câu cùng lúc |
| **Emit chưa áp giá (`_NO_COST`)** ⇒ ô cost cùng-1-số nửa đóng | **AIE-1** (`#121`) + chủ `contracts` (Q-A) | không đổi từ D19 | ask ②/④. `DEC-D19-06` giữ nguyên |
| **Luật cộng `round(·,6)` dùng chung 2 repo, 0 cưỡng chế** — neo đang trỏ nhánh PR `kb#22` | AIE-2 + DE | `kb#22` còn OPEN | Nhắc ở ask ③; không tự sửa |
| **Playground chấm bằng đường `no_leak` vacuous** — `dev_playground_server.py:189` gọi 2 tham số vị trí, chưa opt-in `tenant_ids` | **SWE** | bản vá D18 là additive opt-in, playground chưa nhận | ask ③. Liên quan trực tiếp ô *playground-trace UX* của `#128` |
| **`_case_by_id` ghim `callisto-smoke-5-v0`** ⇒ đường trace thật mẫu số 5, không phải 30 | AIE-2 | đo hôm nay | Nợ có hạn **D21**; ngoài đường găng GATE-2 |
| **Recalibrate ngưỡng** | AIE-2 | `DEC-D17-04`: KHÔNG ĐỔI; điều kiện lật = LLM sinh prose thật ≥30 case | Không làm hôm nay. `DEC-D20-03` |
| **Agreement human–machine thật** (nhãn tay độc lập với `expects_refusal`) | AIE-2 + DE | `manual_label` 10/10 trùng nhánh ⇒ 0 thông tin độc lập | Ngoài phạm vi. Điều kiện lật: DE gán nhãn **đúng/sai của một `actual`**, không phải nhãn **nhánh** |
| **Trục `INV-1 roles`** | **chưa có chủ** — kỳ thứ năm | treo từ D12 | Nêu lại ở `#129`; không nhận. Tập nợ AIE-2 vẫn 0 món vô chủ — món này nằm **ngoài** tập đó |

---

# §5 — Ask gửi ai, nguyên văn — **4 owner · 4 request**

> Không @ mentor. Đồng đội cùng cấp thì bình thường.

**① → SWE (`recipe_hash` producer — `DEC-03`, chặn money-shot của cả nhóm)**

> `publish()` (`publish.py:72`) từ chối mọi `Scorecard` có `recipe_hash is None`, và cổng đó đứng
> **trước** cổng `verdict` ở `:78`. `compute_scorecard` (`compute.py:117`) trả `None` cho **mọi**
> scorecard vì `DEC-03` chưa có producer. Hệ quả đo được:
>
> | Bước money-shot | Hôm nay | Vấn đề |
> |---|---|---|
> | 6 · `PASS` → publish | raise ở `:72` | Không chạy được |
> | 7 · `FAIL` → chặn + rollback | raise ở `:72` | Chặn **đúng, vì lý do sai**; `_reassert_last_published` (`:79`) không chạy ⇒ **không có rollback** |
>
> Bước 7 là ô demo dễ tuyên bố nhất của gate, và nó đang xanh vì một lý do khác với lý do được demo.
>
> Hợp đồng tự khai hạn: `contracts/scorecard.py:223` — *"Fix the schemas before Day 20"* (D-24), và
> `DEC-03` chủ SWE hạn **D12**.
>
> **Trước khi hỏi băm gì, phải nói ai truyền — và phép đo lật một giả định dễ mắc:** *"SWE truyền
> `recipe_hash` tại điểm gọi evalhub"* **không thực thi được, vì điểm gọi đó không tồn tại**.
>
> ```bash
> grep -rn "studio_evalhub" packages/workbench/src/     # → rỗng, 0 dòng
> grep -rln "studio_evalhub" packages/workbench/        # → chỉ dev_playground_server.py
> ```
>
> `dev_playground_server.py` nằm ở **gốc repo, ngoài `src/`**, nạp bằng `importlib`, và gọi
> `score_run_from_trace` — **không phải** `compute_scorecard`. Cộng thêm `.importlinter` xếp
> `studio_workbench` và `studio_evalhub` **sibling cùng layer** ⇒ workbench **cấu trúc mà nói** không
> làm caller được. Caller duy nhất vừa cầm `Recipe` vừa gọi được evalhub là **composition root**
> (`apps/studio/eval_adapter.py:100`).
>
> ⇒ **Hai câu hỏi, và câu ② chặn câu ①.**
>
> **② Recipe NÀO được chứng nhận cho một run N case?** `eval_adapter` dựng **một recipe mới cho MỖI
> case** — `query`/`tenant_id`/`section_roles` nằm trong `Node.params` của `n1`
> (`builder.py:209-215`) ⇒ golden-30 sinh **30 recipe khác nhau**. Một `Scorecard` gộp 30 case thì
> câu *"scorecard này chứng nhận recipe nào"* **không có câu trả lời đơn nhất**, bất kể ai băm và băm
> bằng gì. Cần một recipe **ổn định cho cả run** (load theo `agent_id`), đúng thứ chính docstring của
> adapter đã tự khai từ D6: *"bản production sẽ load recipe theo `agent_id` thay vì dựng mỗi lần"*.
> Chủ: **SWE** (bút `Recipe` + `create_recipe_d4`), cần **AIE-1** phía adapter.
>
> **① Băm trên NỘI DUNG NÀO?** Ba nguồn provenance có sẵn, đo từng cái, không cái nào dùng nguyên
> trạng được:
>
> | Ứng viên | Đo | Kết |
> |---|---|---|
> | `Recipe.version`/`.hash` | `recipe.py:88-94` — 7 field, không có | ✗ không tồn tại |
> | `wb.recipe_versions.version` | Có, nhưng `publish()` tự cấp `COALESCE(MAX(version),0)+1` **sau** khi gate qua | ✗ chicken-and-egg: scorecard chứng nhận **trước** publish |
> | `TraceEvent.inputs_hash` | Có sẵn (`trace.py:34`, NOT NULL trong `obs.trace_events`) | ⚠️ sai hạt — hash inputs của **một node** |
>
> Ứng viên thật sự duy nhất: **`recipe.model_dump_json()`** — chính thứ `publish.py:97` đang dùng để
> lưu vào JSONB, tức **đã là canonical form trên thực tế của SWE**, chỉ chưa được khai là canonical.
> Cạnh sắc phải chốt chứ không đoán: pydantic v2 mặc định serialize theo **field name** ⇒ `Edge.from_`
> ra `"from_"`; `by_alias=True` ra `"from"` — **hai chuỗi byte khác nhau cho cùng một recipe**.
>
> Không tự chọn ở phía evalhub vì `Recipe` là bút SWE: nếu evalhub chọn, thì ngày `Recipe` thêm một
> field tuỳ chọn, **mọi scorecard đã lưu mất hiệu lực trong im lặng** — không lỗi, không cảnh báo,
> chỉ một hash không khớp và không ai biết vì sao.
>
> Phía evalhub mở sẵn đường nhận trong hôm nay: `compute_scorecard(..., recipe_hash: str | None =
> None)` keyword-only, additive, truyền thẳng — cần đúng một chuỗi, không cần đổi contract. Đường
> nhận **không** phụ thuộc hai câu trả lời trên, nên T2 chạy được ngay; thứ phụ thuộc là **giá trị có
> nghĩa hay không**. Chừng nào ② chưa có đáp án, `recipe_hash` đi từ đường eval **không mang nghĩa**,
> và stand-in trong fixture T4 là hình dạng trung thực duy nhất (`DEC-D20-02` không đổi).

**② → AIE-1 (`apps/studio` + emit áp giá)**

> (a) Con trỏ `apps/studio` trong kit đứng ở `0352176` từ **D13**, sau `origin/main` 3 commit. Chỗ nối
> GATE-2 sống ở `apps/studio/tests/` (`.importlinter` xếp 4 quadrant sibling — composition root là chỗ
> duy nhất import được cả `studio_engine` + `studio_kb` + `studio_evalhub`), nên bump là điều kiện của
> ô DoD *"spine 4 bước chạy thật"*. Đã bump ở `kit` phía AIE-2 trong T0a — báo để khỏi bump chồng.
>
> (b) `interpreter.py:73` `_NO_COST = 0.0` vẫn nguyên ⇒ ô *cost cùng-1-số* của `#129` vẫn nửa đóng
> (`DEC-D19-06`). Không có gì mới cần từ phía eval; chỉ xác nhận `#121` còn nằm ở lane nào.
>
> (c) `e2e_smoke_eval.py:250` in `{:<6.2f}` — ngày emit áp giá, `cost_of(37,12)=0.000291` sẽ hiện
> thành `0.00` trên đúng bảng money-shot (`E-1`, design-note failure-mode D19).
>
> (d) **CC câu ② của ask ①:** `eval_adapter.py:100` dựng recipe **mỗi case** qua `create_recipe_d4`,
> `query` nằm trong `Node.params` ⇒ golden-30 sinh 30 recipe khác nhau, và `Scorecard` gộp 30 case
> không trỏ được về **một** recipe. Chính docstring của adapter đã tự khai đường ra từ D6 (*"bản
> production sẽ load recipe theo `agent_id` thay vì dựng mỗi lần"*). Không đề xuất sửa trong hôm nay
> — chỉ xin xác nhận đó là hình dạng đúng để `recipe_hash` có nghĩa.

**③ → SWE (playground-trace UX — ô của chính `#128`)**

> `dev_playground_server.py:189` gọi `score_run_from_trace(case, events)` bằng **2 tham số vị trí** ⇒
> đi đường `no_leak` cũ, chấm trên `retrieved_citations`. Đường đó **vacuous** trên runner thật: case
> từ-chối phát 0 citation ⇒ `all(...)` trên tập rỗng ⇒ `no_leak` luôn `True`. Đo trên golden-30 ở D17:
> **8/8** case từ-chối.
>
> Bản vá `F-6` đã land D18 dưới dạng **additive opt-in**: truyền `tenant_ids=` ⇒ chấm trên
> `outputs["chunks"]`, so tenant bằng **UUID thật** và vai bằng **`section_role` thật**. Giữ opt-in
> đúng vì đổi mặc định của một API công khai là việc của caller.
>
> ⇒ Xin bật opt-in ở playground. Số hiển thị trên Playground hiện **chưa hưởng bản vá**, và đó là ô
> *playground-trace UX* của `#128`.
>
> (b) `TraceViewer.tsx` — `fmtCost`: `cost === 0 ? "chưa đo"` hôm nay đúng; ngày emit nối giá, node
> `kb-retrieve`/`tool-call` phát `Tokens(0,0)` ⇒ một số **đã đo và đúng bằng 0** sẽ hiển thị *"chưa
> đo"* (`E-2`). Và TraceViewer cộng raw, không `round(·,6)` như hai mặt còn lại (`E-3`).

**④ → DE (`kb#22` + nhãn tay)**

> (a) `kb#22` còn OPEN. Neo đối chiếu luật cộng `round(·,6)` của evalhub đang trỏ vào **nhánh PR**,
> chưa có trên `main` của kb — ghi là nợ hai phía, không phải finding mới.
>
> (b) Agreement báo hôm nay có mẫu số **10/30**. Số đó **đo đồng thuận ngữ nghĩa kb↔evalhub**, không
> phải human–machine — `manual_label` trùng khít `expects_refusal` 10/10, mà `expects_refusal` là dẫn
> xuất từ chính dữ liệu golden ⇒ nhãn tay chưa mang thông tin độc lập.
>
> ⇒ Nếu muốn ô *agreement* thành một phép đo human–machine thật, thứ cần là nhãn **đúng/sai của một
> `actual`** (chấm câu trả lời), không phải nhãn **nhánh** (`pass`/`refuse`). Không gấp trong hôm nay;
> nêu để nó có chủ và có hình dạng thay vì treo thành *"agreement chưa có số"*.

---

# §6 — Rủi ro đã biết

| Rủi ro | Dấu hiệu sớm | Xử lý |
|---|---|---|
| **Chỗ nối T3 "chạy thật" mà thật ra vẫn stub** — rủi ro số một của ngày | `M-G3` (đổi sang `StubAgentRunner`) **SỐNG** | `DEC-D20-01` + `M-G3` là **điều kiện** của ô DoD, không phải phần thêm. `M-G3` sống ⇒ ô không đóng |
| **`verdict == "FAIL"` xanh vì mọi cài đặt hỏng đều ra FAIL** | Bài T3 xanh ngay lần chạy đầu, chưa có bài runner-tốt | Bài đối chứng *"runner tốt ⇒ verdict lật PASS"* trên **cùng** chỗ nối. `M-G1` |
| **Hạ ngưỡng để demo xanh** | Bất kỳ diff nào chạm `0.9`/`0.95` | `DEC-D20-03` + `DEC-D17-04` + GUIDE-C §3.2. Ngưỡng thuộc recipe, không thuộc bộ chấm |
| **Tự băm `recipe_hash` "cho xong"** vì SWE chưa trả lời | `hashlib` xuất hiện trong `studio_evalhub/` | `DEC-D20-02` + bài quét T2/3. Stand-in **chỉ** sống trong fixture của test, có nhãn |
| **T4 bài 1 và bài 2 cùng xanh vì cùng `ValueError`** | `pytest.raises(ValueError)` không kèm `match=` | Assert **chuỗi thông điệp**, không chỉ kiểu. Đúng lớp lỗi D19 số 2 (chuỗi khớp nhầm chỗ khác) |
| **Vào sửa `publish.py`/`TraceViewer.tsx`/`dev_playground_server.py`** vì finding rõ quá | Diff ngoài `packages/evalhub/` và ngoài `apps/studio/tests/` | `DEC-D15-03` + `kit#74`. Finding đi bằng ask ①/③ |
| **Sửa `apps/studio/src/`** trong lúc thêm test T3 | Diff chạm `src/studio_app/` | `DEC-D20-01`: **chỉ file test mới**. Nếu adapter thiếu gì ⇒ ask ②, không tự vá |
| **Docker test-stack không lên** ⇒ T3/T4 tụt xuống in-memory | `pytest` skip vì thiếu DSN | **Không** hạ bài. Ghi BLOCKED đủ 3 điều kiện. Đường Postgres **là** thứ đang khẳng định |
| **Bump con trỏ sau khi viết test** ⇒ test chạy trên `workbench` cũ, không có `publish()` | T4 `ImportError`/`AttributeError` | T0a bump **trước** T3/T4. Đây là lý do T0a nằm trên đường găng |
| **Evidence chạy ở một state, bàn giao ở state khác** — số đúng nhưng không ai tái lập được | Bảng số không có SHA đi kèm; hoặc `git status --porcelain` khác rỗng lúc chạy T3/T4/T5 | Khối SHA nền ở T0a + SHA **lúc chạy** cho từng bảng + đối chiếu lần cuối ở T8b. Cùng gốc sự cố `.pyc` D19: *state chạy ≠ state khai* |
| **Báo cáo "GATE-2 xanh"** mà không nói verdict là `FAIL` | Câu nào có chữ *"xanh"*/*"thông"* mà không kèm `FAIL` + lý do | `DEC-D20-03` đòi **hai câu**, không gộp |
| **plan-vs-actual chỉ có dòng D11 đúng** | Bảng T7 không có dòng nào đánh dấu **SAI** | `DEC-D20-06`. Một bảng tự chấm không phải một đối chiếu |
| **Push làm bay approval** | Approve rồi push tiếp | Gom lint/format/vá review **trước** khi xin review. Mắc ở D17, nhắc D18/D19 |
| **Squash sai quy ước** | Merge PR nhiều commit | `evalhub` dùng **merge-commit** (`#16`,`#17`,`#19`,`#20`,`#21`) |
| **Đóng ngày khi `evalhub#22` vẫn OPEN** | Cuối ngày `gh pr view 22` còn `OPEN` | T0a là hạn chót của T8b — cùng luật đã dùng cho nợ D18 ở D19 |

---

# §7 — Định nghĩa "xong" cho D20

**Bốn ô DoD `#128`/`#129`, mỗi ô kèm cách kiểm:**

1. ✅ **`Demo spine 4 bước chạy thật`** — một `Scorecard` sinh ra từ chuỗi golden-30 (kb) →
   `EngineAgentRunner` (engine + `PgKbSearch` + `PgTraceWriter`) → `EvalHarness.run` →
   `compute_scorecard`, chạy trên Postgres thật. **Kiểm bằng `M-G3`**: đổi runner sang stub ⇒ bài phải
   đỏ. `M-G3` sống ⇒ ô **không** đóng, bất kể suite xanh.

2. ✅ **`AC executable xanh — eval v1 verdict`** — `gate.verdict` là giá trị **ra từ dữ liệu**, chứng
   minh bằng bài đối chứng lật được sang `PASS` với runner tốt (`M-G1`), cộng `n_scored_citation = 22`
   khoá đúng mẫu số của `DEC-04`.

   **Verdict của run thật là `FAIL`** — và câu này đi **kèm** lý do: fixture LLM là double trả câu
   canned (`DEC-D17-04` đã đo `success_rate = 0.2667`), **không** vì hàng rào hỏng. Hai câu, không gộp.

3. ⚠️ **`AC executable xanh — cost cùng-1-số`** — **không đổi từ D19**, và nói lại nguyên văn thay vì
   để trôi: đóng ở **đường đọc**, không đóng ở **số thật**. `interpreter.py:73` vẫn `_NO_COST = 0.0`.
   Điều kiện chuyển ✅ (đo được, không theo ngày): `price_mismatches` **rỗng** trên một run golden thật
   **VÀ** `Σcost > 0` — cả hai vế cùng lúc.

4. ✅ **`plan-vs-actual đối chiếu`** — 4 bảng trên D11 nguyên trạng + bảng thứ năm cho thứ D11 **không
   nhìn thấy**. Mỗi dòng có neo `file:line` hoặc một số đo. Có ít nhất một dòng đánh dấu D11 **SAI**.

**Điều kiện chung, giữ nguyên từ các ngày trước:**

- Mọi bài test mới **đỏ trước** trên code hôm nay. **`ImportError` không tính là đỏ** — dựng stub
  `NotImplementedError` (hoặc chấp nhận `TypeError` sai chữ ký ở T2) để bài đỏ vì **lý do đúng**.
- Mutation khai **trước** khi viết test; bảng ghi **bài nào đỏ**, không chỉ có-đỏ-hay-không. Dọn
  `__pycache__` + kiểm giá trị **runtime** trước khi ghi `SURVIVED`.
- Mọi món AIE-2 hoãn có **chủ + hạn + điều kiện lật đo được**. **0 món hoãn vô chủ trong tập AIE-2**;
  món `INV-1 roles` nằm **ngoài** tập đó và được nêu lại như finding, không được lấp.
- Ranh giới nói ra thay vì để phát hiện sau, trên ba trục: (a) **đường đọc** hay **số thật**; (b) chạy
  trên **runner thật** hay **stub**; (c) `recipe_hash` là **producer thật** hay **stand-in trong
  fixture**.
- Mọi số đo **truy vết được tới state đã chạy**: SHA của `packages/evalhub` (cộng `apps/studio` và
  `packages/workbench` cho T3/T4) tại **lúc chạy**, với `git status --porcelain` rỗng lúc đó. Con trỏ
  đổi trong ngày ⇒ ghi **cả hai** SHA, không im lặng thay bằng SHA cuối.
- PR: merge-commit (không squash), gom lint trước khi xin review, ≥1 approval bất kỳ.

**Thứ KHÔNG được tính là xong:**

- Một chỗ nối T3 mà `M-G3` **sống** — tức không có phép đo nào phân biệt nó với đường stub.
- Một `verdict == "FAIL"` **không** kèm bài đối chứng lật sang `PASS`. `FAIL` là giá trị dễ trúng
  nhất; một bài chỉ khẳng định nó xanh với mọi cài đặt hỏng.
- Một bài T4 chỉ bắt `pytest.raises(ValueError)` mà không phân biệt được *chặn vì `recipe_hash`* với
  *chặn vì `verdict`*.
- Bất kỳ `hashlib`/`model_dump_json()` nào trong đường dựng `Scorecard` của `studio_evalhub`.
- Bất kỳ diff nào chạm `0.9`/`0.95`, `packages/workbench/`, `apps/web/`, `packages/kb/`, hoặc
  `apps/studio/src/`.
- Một `rate` agreement in ra **không kèm** `n_compared` và danh sách `lệch`.
- Báo cáo dùng chữ *"GATE-2 xanh"* / *"spine đã thông"* mà không nói verdict là `FAIL` và vì sao.
- Một bảng plan-vs-actual **không có dòng nào** đánh dấu D11 sai.
- Một bảng số trong evidence **không kèm SHA** của state đã chạy — kể cả khi con số đúng.
- Một số đo chạy trên cây có **sửa local chưa commit** (`git status --porcelain` khác rỗng).
- Một câu xác nhận về **gói ZIP · security scan · trạng thái integrated của cả nhóm** trong bất kỳ
  báo cáo nào của AIE-2. Ba món đó không có owner/spec giao cho AIE-2 ⇒ khai chúng là khai thay
  người khác.
- Đóng ngày khi `evalhub#22` còn OPEN, `kit#123` còn OPEN, hoặc con trỏ `apps/studio`/`workbench`
  chưa bump (kiểm bằng `git submodule status`, không bằng `ls`).
