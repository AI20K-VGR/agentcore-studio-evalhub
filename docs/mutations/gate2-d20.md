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

**Giả thuyết CHƯA xác nhận:** `.pyc` cũ của `workbench@6badd84` — con trỏ workbench được bump lên
`04ca988` **sáng nay** ở T0a, và `create_recipe_d4` là hàm nằm trong `builder.py` của chính repo đó.
Bytecode cũ nạp lẫn với source mới cho ra một recipe thiếu khoá `section_roles`. Khớp hình với sự cố
`.pyc` D19 (*state chạy ≠ state khai*), chỉ khác tầng: ở đó runtime lệch file, ở đây bytecode lệch
commit.

**Không tự sửa** — `test_eval_adapter.py` và `builder.py` đều ngoài lane AIE-2, và `DEC-D20-01` giới
hạn AIE-2 ở **file test mới** trong `apps/studio`. Chủ: **AIE-1** (adapter/test) + **SWE**
(`builder.py`). Điều kiện lật: tái hiện được với `__pycache__` sạch ⇒ là bug thật, không phải bytecode.

**Ảnh hưởng tới evidence D20: không.** Mọi số của T3/T5 đã được **chạy lại sau khi dọn sạch 752 file
`.pyc`**, với `PYTHONDONTWRITEBYTECODE=1`, và **trùng khít** bản đầu:

```text
success_rate 0.1667 (5/30) · citation_accuracy 0.2273 · n_scored_citation 22
verdict FAIL · trace_events 120 · recipe_hash None
judge_routed 17 · agreement rate=1.0 n_compared=10 lech=[]
```
