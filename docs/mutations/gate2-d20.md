# Sổ mutation D20 — GATE-2 (`M-G1` … `M-G6`)

> `kit#128` T8a. Bảng khai **trước** khi viết test, và ghi **bài nào đỏ** — không chỉ
> có-đỏ-hay-không. Một ngày gate không có mutant là một ngày gate **không có phép đo**.

## Luật đo áp cho cả sáu — rút từ sự cố `.pyc` D19

1. **Dọn `__pycache__` trước mỗi lần gieo và mỗi lần khôi phục.**
2. **Kiểm giá trị RUNTIME, không chỉ kiểm file + `git diff`.** Một mutant **cùng kích thước file** có
   thể không bao giờ có hiệu lực, và người gieo sẽ ghi `SURVIVED` cho một mutant **chưa từng được
   gieo**.
3. Sau khôi phục: `grep -rn MUTANT` phải **rỗng**, và chạy lại suite.

## Bảng khai

| # | Mutant | Dự đoán | Kết quả | Bài nào ĐỎ |
|---|---|---|---|---|
| `M-G1` | `compute_scorecard` trả `verdict="FAIL"` hằng | DIE ở bài runner-tốt | ✅ **KILLED** | `test_runner_tot_lat_verdict_sang_pass` |
| `M-G2` | `compute_scorecard` bỏ `recipe_hash` (luôn `None`) | DIE ở T2 bài 1 | ✅ **KILLED** | `test_recipe_hash_truyen_vao_di_thang_ra_scorecard` |
| `M-G3` | Chỗ nối T3 đổi `runner` sang `StubAgentRunner` | DIE | ✅ **KILLED** | `test_verdict_fail_tu_run_that` |
| `M-G4` | T4 bài 2 đổi `recipe_hash` stand-in → `None` | DIE ở assert chuỗi | ✅ **KILLED** | `test_bai2_verdict_fail_chan_va_rollback_that_su_chay` |
| `M-G5` | `agreement` trả `rate` khi `n_compared=0` (`None`→`0.0`) | DIE ở bài mẫu số | ✅ **KILLED** | `test_mau_so_rong_tra_none_khong_phai_khong_phay_khong` |
| `M-G6` | `ddl()` bỏ `ENABLE ROW LEVEL SECURITY` | DIE ở T6 | ✅ **KILLED** | `test_ddl_bat_rls_va_co_policy_cho_ca_hai_bang` |

**6/6 killed. 0 survivor.**

---

## `M-G1` — và đây là kết quả đáng giá nhất trong sổ

Gieo: `verdict="PASS" if (dat_success and dat_citation) else "FAIL"` → `verdict="FAIL"`.

| Bài | Dưới `M-G1` |
|---|---|
| `test_verdict_fail_tu_run_that` (bài live) | **VẪN XANH** ⚠️ |
| `test_runner_tot_lat_verdict_sang_pass` (đối chứng) | **ĐỎ** — `assert 'FAIL' == 'PASS'` |

**Đây là phép đo trực tiếp cho câu *"`FAIL` là giá trị dễ trúng nhất"*.** Nếu hôm nay chỉ có bài live
— tức nếu làm đúng những gì ô DoD chữ nghĩa đòi — thì ô *"eval v1 verdict"* đã **đóng bằng một hằng
số**, suite vẫn xanh, và không ai biết. Bài đối chứng không phải phần thêm; nó **là** điều kiện của ô.

## `M-G3` — phép đo duy nhất phân biệt *"chạy thật"* với *"trông như chạy thật"*

```text
FAILED test_verdict_fail_tu_run_that — AssertionError: assert 'PASS' == 'FAIL'
```

Hai lưới cùng bắt, và cần cả hai: verdict lật `FAIL`→`PASS`, **và** `obs.trace_events` về 0 (stub
không ghi một dòng nào vào Postgres). Một mình verdict có thể lật vì lý do khác.

`M-G3` sống ⇒ ô DoD *"Demo spine 4 bước chạy thật"* **không đóng**, bất kể suite xanh. Nó không sống.

## `M-G2` — vì sao kiểm runtime chứ không kiểm `git diff`

```console
$ python -c "... compute_scorecard(..., recipe_hash='SEEDED').recipe_hash"
runtime recipe_hash = None        # ← truyền 'SEEDED' vào, ra None
FAILED test_recipe_hash_truyen_vao_di_thang_ra_scorecard
```

Dòng `runtime` mới là bằng chứng mutant **có hiệu lực**. `git diff` chỉ chứng minh file đã đổi.

## `M-G4` — mutant lộ một lỗ trong CHÍNH bài test

Lần gieo đầu, `pytest.raises(ValueError, match="verdict")` **không** bắt được:

```text
match="verdict"  →  KHỚP, nhưng khớp vào agent_id='gate2-bai2-verdict-fail'
                    nằm trong thông điệp của cổng recipe_hash — KHÔNG vào lý do chặn
```

`publish()` nội suy `agent_id` vào **cả hai** thông điệp, nên một `agent_id` mang tên nhánh làm
`match=` khớp vào **chính cái tên mình đặt**. Thứ giết được `M-G4` lúc đó là assert phủ định
(`"recipe_hash" not in str(...)`), không phải `match=`.

**Vá trước khi commit:** `agent_id` → tên trung tính; `match=` neo vào cụm **chỉ có ở thông điệp
cổng** — `scorecard\.recipe_hash is None` và `gate\.verdict='FAIL'`. Sau vá, gieo lại `M-G4`:

```text
E  AssertionError: Regex pattern did not match.
E    Expected regex: "gate\.verdict='FAIL'"
E    Actual message: "publish: scorecard.recipe_hash is None for agent_id=..."
```

Chính `match=` giết được. Đúng lớp lỗi D19 số 2 — **chuỗi khớp nhầm chỗ khác**.

## `M-G6` — giới hạn phải nói ra: bài Postgres thật KHÔNG giết được nó

Gieo bỏ `ALTER TABLE eval.scorecards ENABLE ROW LEVEL SECURITY`:

| Bài | Dưới `M-G6` |
|---|---|
| `test_ddl_bat_rls_va_co_policy_cho_ca_hai_bang` (chuỗi) | **ĐỎ** ✅ |
| `test_rls_that_su_can_tren_postgres_that` (Postgres thật) | **VẪN XANH** ⚠️ |

Lý do, đo bằng `pg_class`:

```console
$ SELECT n.nspname||'.'||c.relname, c.relrowsecurity, c.relforcerowsecurity …
 eval.golden_sets | t | t
 eval.scorecards  | t | t      ← vẫn 't' dù DDL không còn ENABLE
 obs.golden_sets  | f | f
```

`ENABLE` của lần chạy trước **còn nguyên trên bảng**, và `FORCE` không tắt nó ⇒ trên một DB **đã
migrate**, bài hành vi mù với mutant này. **Bài chuỗi là lưới DUY NHẤT ở trục này** — đó là lý do nó
tồn tại, không phải phần thừa. Nghịch lý đáng ghi: ở đây bài *"đọc chuỗi"* mạnh hơn bài *"chạy thật"*.

### Finding phụ, ngoài lane AIE-2 — `obs.golden_sets` **không có RLS**

Dòng thứ ba của bảng `pg_class` trên. `obs.*` là schema **composition-owned**
(`apps/studio/src/studio_app/obs/schema.py`), không phải lane AIE-2 ⇒ **không tự sửa**, chỉ nêu. Nó
cùng hạng dữ liệu với `eval.golden_sets` (mang `query`/`expected` của tenant). Chủ: **AIE-1** /
composition. Điều kiện lật: `relrowsecurity = 't'` trên `obs.golden_sets`.

---

## Vệ sinh sau khi gieo

```console
$ grep -rn "MUTANT" packages/evalhub/src packages/evalhub/tests apps/studio/tests
(rỗng)
$ find . -name "*.pyc" | wc -l
0
```

Suite sau khôi phục, trên state `evalhub@4d9481a` · `apps/studio@19b7f4d`, cây `--porcelain` rỗng:

```text
packages/evalhub/tests   231 passed
apps/studio/tests         50 passed, 1 xpassed
gộp cả hai               281 passed, 1 xpassed
```

## ⚠️ Finding hạ tầng — flake liên-quadrant, KHÔNG do D20 gây ra

Trong lúc chạy mutation, `apps/studio/tests/test_eval_adapter.py` đỏ **không ổn định** ở hai bài
`test_recipe_construction_via_real_builder` / `_empty_roles` với `KeyError: 'section_roles'`.

**Đã quy trách nhiệm bằng phép đo, không bằng phỏng đoán:**

| Cấu hình | Kết quả |
|---|---|
| Gộp cả hai suite, **có** 2 file mới của D20 | ~50% đỏ (2 đỏ / 3 lượt, rồi 2/4) |
| Gộp cả hai suite, **bỏ** 2 file mới của D20 (`--ignore`) | **vẫn ~50% đỏ** (2 đỏ / 4 lượt) |
| `apps/studio/tests` chạy riêng | 6/6 xanh |
| `packages/evalhub/tests` chạy riêng | xanh |
| evalhub + **chỉ** `test_eval_adapter.py` | 5/5 xanh |

⇒ **Pre-existing, không phải do hai file mới của D20** — vế thứ hai là vế quan trọng, và nó được đo
chứ không được khẳng định.

**Sau khi dọn sạch bytecode** (`find . -name "*.pyc" | wc -l` → từ **752** về **0**), gộp cả hai
suite: **8/8 xanh**, và không tái hiện được nữa.

### ❌ Giả thuyết đầu tiên đã bị BÁC BỎ — ghi lại thay vì sửa lặng

**Bản đầu của mục này viết:** *"`.pyc` cũ của `workbench@6badd84` — con trỏ bump lên `04ca988` sáng
nay, bytecode cũ nạp lẫn source mới cho ra recipe thiếu khoá `section_roles`."* Đo lại:

```console
$ git show 6badd84:src/studio_workbench/builder.py | grep -n "section_roles"
216:                "section_roles": section_roles,     ← BẢN CŨ VẪN CÓ
$ git show 04ca988:src/studio_workbench/builder.py | grep -c "section_roles"
9
```

⇒ **cả hai bản `builder.py` đều có `section_roles` trong `node.params`.** Bytecode của `6badd84`
không thể tạo ra `KeyError` đó. Giả thuyết **sai**, và nó sai theo kiểu dễ tin nhất: đúng *hình dạng*
(bump con trỏ + `.pyc` cũ) nên nghe rất hợp lý, mà không ai kiểm cái tiền đề *"bản cũ thiếu khoá"*.

### ✅ Nguyên nhân thật — và nó là một finding LIÊN REPO, không phải sự cố máy cá nhân

`workbench#23` (**OPEN**, bút SWE — *"Day19/20 hardening: dọn `builder.py` params thừa"*) **bỏ**
`tenant_id`/`section_roles` khỏi `node.params`:

```diff
-    section_roles = _parse_kb_scope(scope, t_id)
+    # trả về không còn cần đưa vào `node.params` nữa: `interpreter.run()` luôn ghi đè
+    # `tenant_id`/`section_roles` của node `kb-retrieve` bằng `session_context` (D8/D17, #111)
-                "section_roles": section_roles,
```

Bytecode còn sót trên máy khớp **đúng shape của nhánh đó**, không phải của `6badd84` — đó là thứ tạo
ra `KeyError`. Dọn `.pyc` xong thì hết.

**Đính chính thứ hai — món này ĐÃ CÓ CHỦ trước khi tôi viết dòng trên.** Bản đầu ghi *"finding liên
repo chưa ai xử"*. Sai: `workbench#23` đã có review `CHANGES_REQUESTED` của AIE-2 lúc **`07:18:52Z`**,
tức **trước** cả trả lời ask ① của SWE (`07:44`) lẫn ask ②/③ (`07:45`/`07:46`). Review đó đã bắt §1
kèm số đo ba cấu hình, **cộng một mục nặng hơn mà phép đo ở đây không thấy**: bài
`test_inv1_recipe_khai_tenant_khac_thi_session_thang` **mất răng** — mutant M3 (đẩy `**node.params`
xuống *sau* hai override ⇒ client params thắng session) **chết** ở `04ca988` nhưng **SỐNG** ở
`1b19a8c`, vì không còn params nào để mà "thắng". Hỏng mà vẫn xanh.

Giữ mục dưới đây vì nó là **đường độc lập** dẫn tới cùng một chỗ — bytecode sót vô tình dựng lại
đúng trạng thái sau-merge — nhưng công đầu và mức chặn thuộc về review kia, không thuộc phép đo này.

`workbench#23` đã tự cập nhật test **trong repo của nó** (`tests/test_wiring_d4.py`:
`assert "section_roles" not in n1.params`), nhưng `apps/studio/tests/test_eval_adapter.py` — **repo
khác** — vẫn khẳng định chiều ngược lại:

```python
assert kb_node.params["section_roles"] == ["public", "finance"]   # :349
```

⇒ **Ngày `workbench#23` merge, hai bài của `apps/studio` đỏ**, và đỏ ở một repo mà PR đó không chạm
tới nên CI của nó không thấy. Máy tôi hôm nay đã **xem trước** đúng lỗi đó qua bytecode sót.

**Không tự sửa** — `test_eval_adapter.py` (AIE-1) và `builder.py` (SWE) đều ngoài lane AIE-2, và
`DEC-D20-01` giới hạn AIE-2 ở **file test mới** trong `apps/studio`. Chủ: **SWE** (`workbench#23`) +
**AIE-1** (test). Điều kiện lật: `workbench#23` merge **cùng lượt** với bản vá `test_eval_adapter.py`,
hoặc PR đó khai rõ breaking-change liên repo.

**Ảnh hưởng tới D20: không.** Hai bài test mới của D20 **không đọc `node.params`** — `_runner_tot`
khoá theo `(query, tenant_id, tuple(case.section_roles))` lấy từ **`GoldenCase`**, và bài live đi qua
`interpreter.run()` vốn ghi đè hai khoá đó từ `session_context`.

**Ảnh hưởng tới evidence D20: không.** Mọi số của T3/T5 đã được **chạy lại sau khi dọn sạch 752 file
`.pyc`**, với `PYTHONDONTWRITEBYTECODE=1`, và **trùng khít** bản đầu:

```text
success_rate 0.1667 (5/30) · citation_accuracy 0.2273 · n_scored_citation 22
verdict FAIL · trace_events 120 · recipe_hash None
judge_routed 17 · agreement rate=1.0 n_compared=10 lech=[]
```
