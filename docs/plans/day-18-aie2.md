# Plan Day 18 — AIE-2 · LLM-judge sơ khởi (cache + cap≤100) + agreement-check vs nhãn tay · Thứ Tư 12/08/2026

> **Issue:** `kit#118` (con, AIE-2) dưới `kit#119` (cha, cả nhóm) · **Repo WRITE:** `agentcore-studio-evalhub` · kit READ
> **Vai:** chủ công ô DoD của cả nhóm — ba trong bốn ô DoD chung là bút AIE-2.
> **Spec:** `week-2/days/day-18.md` **404** (ngày thứ tám liên tiếp) ⇒ `#118` là spec thẩm quyền duy nhất.

---

# Executive Summary

Ngày này có một cái bẫy nằm ngay ở chữ đầu tiên của đề bài, và nó phải được nói ra trước khi gõ dòng
nào: **`#118` đòi "LLM-judge sơ khởi", nhưng đo được sáng nay là không có LLM nào để gọi, và không có
case nào cần judge chấm.** Hai vế đó không phải rủi ro dự phòng — chúng là trạng thái hiện tại, đo
được, và chúng quyết định hình dạng của cả ngày.

Ba số làm nền:

| Đo | Kết quả | Nghĩa |
|---|---|---|
| Nhà cung cấp LLM dùng được | **0** — `.env` không tồn tại, `STUDIO_GEMINI_API_KEY` không có trong shell, `STUDIO_USE_FAKE_PROVIDERS=true` là mặc định | Trigger descope #2 của `DESCOPE.md` **đã thoả** trước khi ngày bắt đầu |
| Case cần judge trong golden-30 | **0/30** — 22 dương chấm bằng `_contains_phrase`, 8 âm chấm bằng luật refusal | Nhánh judge chưa có case nào đi qua |
| Nhãn tay (`manual_label`) trong golden-30 | **0/30** — field chưa tồn tại ở bất kỳ đâu trong workspace | `Judge.agreement` chưa có mẫu số |

⇒ **Nấc descope không phải phương án B của hôm nay; nó là đường mặc định.** `DESCOPE.md` viết sẵn từ
D2 rằng nấc này kích hoạt khi *"nhà cung cấp LLM không dùng được"* hoặc *"CI cần chạy tất định"* — cả
hai đúng ngay lúc này. Việc của ngày không phải là chạy đua để bật judge thật rồi hạ cánh vội, mà là
**làm cho nấc descope trở thành một nấc có số**, và dựng đúng cái seam để ngày có key thì bật lên
không phải viết lại.

**Điều đáng ghi nhất của ngày, tìm ra khi kiểm nền: `GoldenCase` sẽ NUỐT CÂM `manual_label` của DE.**
`golden_case.py:31` khai `model_config = ConfigDict(frozen=True)` và **không** khai `extra`, nên
pydantic dùng mặc định `ignore`. Đo trực tiếp:

```text
GoldenCase(..., manual_label='REFUSE')  →  hasattr(c, 'manual_label') = False
                                          c.model_extra              = None
                                          model_config extra         = <unset → ignore>
```

Nghĩa là: ngày DE emit `manual_label` vào yaml, `load_golden_set` **nạp thành công**, loader **không
báo gì**, và agreement-check đọc được **không có gì**. Không exception, không cảnh báo, suite vẫn
xanh. Đây đúng lớp lỗi đã cắn nhóm hai lần trong tuần — `uv sync --frozen` dùng lockfile sai mà CI
xanh (D17), và `strict=False` nuốt `xpassed` ở `kb#19` (D17) — mà lần này nó nằm trên **đường găng
của chính DoD hôm nay**, và nó sẽ nổ ở phía DE chứ không phải phía mình. Vá nó là **T1**, việc code
đầu tiên của ngày, trước cả judge — chỉ có **T0a** (15′ đo nền + comment) đứng trước, và mọi việc
hành chính đẩy xuống **T0b** để không món nào chặn thứ đang chặn DE.

**Ô DoD nào đóng được thật:**

| Ô DoD (`#118`) | Đóng được? | Bằng gì |
|---|---|---|
| `exact-match fallback sẵn` | ✅ **có** | Nấc `DESCOPE.md` đã tồn tại từ S1; hôm nay biến nó thành đường **cưỡng chế bằng test** thay vì một trang văn bản |
| `LLM-judge cache+cap≤100` | ✅ **có** — seam + cơ chế, KHÔNG có call thật | Cache + counter + descope-sentinel test được **tất định**, không cần provider. Cái không có là số từ mô hình thật |
| `agreement-check có số vs nhãn tay` | ⚠️ **một nửa** | Số đo được **hôm nay** là agreement của **exact-match scorer** vs nhãn tay — baseline mà judge phải vượt. Agreement của *judge* cần **đủ ba** điều kiện `DEC-D18-04`: `manual_label` về · key Gemini · ≥1 case thật sự cần judge |
| `CI deterministic` | ✅ **có** | Hệ quả trực tiếp của descope: không call mạng trong CI, đã là luật sẵn |

**Ranh giới tự áp cho ngày:** không bịa một `Judge(...)` hằng số để làm đầy ô DoD. `judge.py:8-9`,
`contracts/scorecard.py` docstring và `ADR B5` (D14) cấm ba lần bằng ba chỗ khác nhau, và lý do luôn
là cùng một câu: **một `agreement` hằng không phân biệt được với một judge thật đồng thuận 100%**.
Ngày mà ô DoD được làm đầy bằng một hằng số là ngày con số agreement mất hết ý nghĩa cho mọi ngày sau.

---

# §1 — Nền đã kiểm, không giả định

## Trạng thái pointer (kiểm 12/08 sáng)

```bash
git -C . rev-parse HEAD                    # f1be661 == origin/main
git submodule status                       # 9/9 sạch, không tiền tố +/-
git -C packages/evalhub log --oneline -1   # b905fb9 (F-6, merged D17)
uv lock --check                            # sạch
uv run pytest packages/evalhub -q          # 128 passed, 1 skipped
uv run mypy packages/evalhub               # no issues, 28 files
```

9/9 con trỏ khớp `main` của repo con. Không món nào của D17 còn treo: `kit#146/147/148`,
`engine#22`, `evalhub#18`, `report#68` **đều MERGED**, `kit#113` **CLOSED**.

## Ba phép đo quyết định hình dạng ngày

```bash
# 1. Có nhà cung cấp LLM nào dùng được không
ls .env                                     # No such file
printenv | grep -ci gemini                  # 0
grep STUDIO_USE_FAKE_PROVIDERS .env.example # =true  (mặc định)

# 2. Có case nào cần judge không
python -c "... any('match_mode' in c for c in cases)"   # False  (0/30)

# 3. Nhãn tay đã về chưa
python -c "... any('manual_label' in c for c in cases)" # False  (0/30)
```

**Đọc cho đúng:** vế (1) **không** phải "hạ tầng hỏng". `GeminiProvider` tồn tại và chạy được
(`apps/studio/src/studio_app/providers/gemini.py`, Decision #9 — hạ tầng chung, LLM-only, bút SWE).
Thứ thiếu là **cấp phát**: một key thật trong `.env`. Đó là việc của người giữ hạ tầng, không phải
việc gỡ được từ trong evalhub — nên nó thành **ask ③** chứ không thành work item.

Vế (3) có tiền lệ đã ghi: `kb/src/studio_kb/golden_set.py:33` viết *"nhãn tay ground-truth cho subset
là **D18** — sẽ thêm field `manual_label`"*, và `kb` decision `DL-16.1` chốt *"`manual_label` (D18/#115)
**chừa chỗ, chưa thêm**"*. Tức DE **đã lập kế hoạch đúng** và đang chờ đúng ngày. Không phải món trễ
hạn; là món đến hạn **hôm nay**, và phụ thuộc hai chiều với T1 của mình.

## Bẫy đã tìm ra khi kiểm nền — `extra="ignore"` nuốt câm nhãn tay

Đo trực tiếp, không suy:

```python
c = GoldenCase(case_id='X', ..., manual_label='REFUSE')
hasattr(c, 'manual_label')  # False
c.model_extra               # None
GoldenCase.model_config.get('extra')  # unset → pydantic mặc định 'ignore'
```

Chuỗi hệ quả nếu không vá, theo đúng thứ tự nó sẽ xảy ra:

1. DE thêm `manual_label` vào `GOLDEN_CASES` + re-emit yaml (đúng quy trình `DL-16.1`, byte-identical gate xanh).
2. `load_golden_set` nạp file — **thành công**, `golden_set_ref` khớp, `model_validate` không phàn nàn.
3. `GoldenCase` **vứt** field. `case.manual_label` không tồn tại.
4. Agreement-check hoặc `AttributeError` (may), hoặc đọc `getattr(case, 'manual_label', None)` rồi
   báo *"0 case có nhãn tay"* (xui) — và số agreement ra `None`/`0` **trông như một phép đo**.
5. Không test nào đỏ, vì không test nào biết field lẽ ra phải có.

Bước 4 nhánh xui là chỗ nguy hiểm: nó cho ra một **con số** thay vì một lỗi, và con số đó đi thẳng
vào báo cáo ngày. Đây là lý do T1 xếp trước T2 — vá seam nhận dữ liệu trước khi viết thứ tiêu thụ dữ
liệu.

## Bản đồ phụ thuộc D18

```
   T0a kiểm nền + comment (15′)
        │
        ▼            ┌─ DE #115: manual_label vào GOLDEN_CASES + re-emit yaml
        │            │        │ (cần T1 xong trước, nếu không nhãn bị nuốt câm)
        │            ▼        ▼
   T1 GoldenCase.extra="forbid" + manual_label optional   ◄── đường găng, P0
        │
        ├──► T0b ADR-D16-05 + việc kèm (P0, KHÔNG chặn T1 — chạy sau khi T1 mở PR)
        │
        ├───────────┬───────────────┐
        ▼           ▼               ▼
   T2 LLMJudge   T3 agreement    T4 harness wiring
   cache+cap     exact-match      + CI deterministic
   +sentinel     baseline         (judge branch qua FIXTURE, không qua golden-30)
   (reason)
        │           │               │
        └───────────┴───────┬───────┘
                            ▼
              T7a mutation ─► merge-ready ─► T5 (P1, hard gate) ─► T6 (P2) ─► T7b đóng ngày

   AIE-1 #116 (prose ổn định) ──► điều kiện lật của DEC-D17-04 (recalibrate) — KHÔNG chặn D18
   SWE  #117 (threshold đọc 2 nhánh) ──► no-op nếu giữ contract ổn định (xem DEC-D18-06)
   SWE  cấp key Gemini ──► ask ③, điều kiện lật để judge có số THẬT
   DE   vocabulary/trục manual_label ──► ask ① (b), điều kiện 2/2 để số mang nhãn THẬT
```

**Hai nửa của T7 là hai work item riêng (`T7a`/`T7b`), không phải một item đọc theo hai cách.**
`T7a` (mutation) thuộc điều kiện merge-ready của T1–T4 — sổ mutation ship cùng PR, tiền lệ
`evalhub#18`; `T7b` (đóng ngày) đứng sau tất cả, kể cả T5/T6. Để chung một item thì thứ tự văn bản
(T5 → T6 → T7) đọc ngược với thứ tự thực thi, và cái gate ở T5 mất chỗ bám: **T5 chờ mutation, mà
mutation lại nằm trong item xếp sau T5** — vòng phụ thuộc giả sinh ra từ cách đánh số chứ không từ
công việc.

## Dependency/blocker rule (giữ nguyên từ D15/D16/D17)

Không món nào của mình được khai BLOCKED vì món của người khác, trừ khi đã (a) gửi ask có nguyên văn,
(b) ghi điều kiện lật đo được, (c) có đường đi tiếp không cần họ. Ba điều kiện, đủ cả ba mới được ghi
BLOCKED. Áp cho D18: `manual_label` của DE là phụ thuộc thật, nhưng **T1 không chờ nó** — T1 dựng chỗ
để nhãn đi vào, và test T1 tự gieo nhãn giả để chứng minh chỗ đó nhận được.

---

# §2 — Quyết định phải chốt hôm nay

## DEC-D18-01 · `GoldenCase` phải `extra="forbid"`, và `manual_label` khai TRƯỚC khi DE emit

**Quyết:** `model_config = ConfigDict(frozen=True, extra="forbid")`, kèm khai
`manual_label: str | None = None` trong **cùng một** thay đổi.

**Vì sao hai vế phải đi cùng nhau, không tách:** `extra="forbid"` một mình sẽ làm yaml của DE **đỏ
ngay** khi họ emit — biến một lỗi câm thành một lỗi ồn, đúng hướng, nhưng chặn DE. Khai
`manual_label` một mình thì field vào được, nhưng **mọi typo tương lai vẫn câm** (`manual_labels`,
`manaul_label` — nuốt sạch). Đi cùng nhau thì: nhãn đúng tên đi vào được, nhãn sai tên **đỏ tại
loader** với tên field sai in ra.

**Vì sao đây không cần mini-RFC:** `GoldenCase` là **kiểu nội bộ quadrant**, khai tường minh ở
`golden_case.py:8` (*"Đặt trong evalhub, không đưa lên `studio_contracts` … đổi shape không cần
mini-RFC"*), và `DEC-D16-06` nhắc lại nguyên văn (*"`GoldenCase` là kiểu **nội bộ quadrant** ⇒
**không bao giờ** cần mini-RFC"*). Thêm field optional cũng rơi đúng dòng đầu bảng miễn của
`TEMPLATE.md`. Không đụng `studio_contracts`, nên `ADR-D16-05` không liên quan.

**Rủi ro thật của `extra="forbid"`, và vì sao vẫn làm:** nó biến mọi field lạ trong yaml thành lỗi
cứng. Nếu DE đang có field nào chưa khai ở `GoldenCase` thì loader đỏ ngay hôm nay. Đã đo: golden-30
có **đúng 8 field**, khớp 1:1 với `GoldenCase` — không field thừa. Rủi ro đo được là **0** trên dữ
liệu hiện tại, và giá trị là chặn mọi drift tương lai ở đúng chỗ nó sinh ra.

**Bằng chứng phải có:** một bài đỏ-trước gieo `manual_label` sai tên → `ValidationError` nêu đúng tên
field; một bài gieo nhãn đúng tên → đọc ra được giá trị. Bài thứ nhất **phải đỏ trên code hôm nay**
(đo: hiện tại nó xanh vì field bị nuốt) — đó là định nghĩa của đỏ-trước ở repo này.

## DEC-D18-02 · `LLMJudge` nhận `LLM` qua seam tiêm vào, KHÔNG import `studio_app`

**Quyết:** `LLMJudge.__init__(self, llm: LLM, ...)` — `LLM` là
`studio_contracts.protocols.LLM` (`protocols.py:27`, `async def complete(prompt, **kwargs) -> str`).
Composition root (CLI / `apps/studio` / fixture test) là chỗ **duy nhất** biết provider thật nào được
dựng.

**Vì sao, và đây là cùng một lý lẽ với `DEC-D16-01` chứ không phải một luật mới:**

1. **Layering** — `.importlinter` xếp 4 quadrant là sibling. `studio_evalhub` **không** import
   `studio_app`. Provider thật (`GeminiProvider`) sống ở `apps/studio`, tức phía **trên** evalhub.
   Import ngược lên là vi phạm lint, và một đường vòng (`importlib`, đọc env trực tiếp) là **cùng một
   phụ thuộc, chỉ né được lint chứ không né được thực tế** — nguyên văn lý lẽ đã dùng cho đường dẫn
   `packages/kb/...` ở D16.
2. **Fresh clone** — `kit#74` chấm bằng *"clone sạch rồi chạy lệnh y nguyên"*. Clone riêng evalhub
   thì `apps/studio` không tồn tại.
3. **Tiền lệ trong chính repo này** — `AgentRunner` đã là seam tiêm vào đúng hình đó
   (`agent_runner.py`), và `EvalHarness.run(runner=...)` nhận nó qua tham số. Judge không có lý do
   gì để khác.

**Hệ quả cho test:** judge test được **hoàn toàn tất định** bằng một `LLM` double trong repo — không
mạng, không key, CI xanh. Ô DoD *"CI deterministic"* đóng như một **hệ quả cấu trúc**, không phải một
việc riêng phải làm.

## DEC-D18-03 · Descope là đường MẶC ĐỊNH của D18, không phải phương án dự phòng

**Quyết:** hôm nay chạy ở nấc exact-match. Judge được dựng đủ (seam + cache + cap + sentinel) và test
đủ, nhưng **không** có call LLM thật trong ngày, và **không** có call LLM nào trong CI — bao giờ cũng.

**Vì sao đây là quyết định chứ không phải bỏ cuộc:** `DESCOPE.md` (viết D2, không phải viết hôm nay)
liệt 4 trigger. Đo sáng nay, **hai** trigger đã thoả:

- *"nhà cung cấp LLM không dùng được"* — không `.env`, không key, `USE_FAKE_PROVIDERS=true`;
- *"CI cần chạy tất định, không phụ thuộc phản hồi mô hình"* — luôn đúng, và `#118` đòi thẳng ô DoD này.

Một thang cắt giảm viết sẵn từ D2 mà đến ngày trigger thoả lại không kích hoạt thì nó chưa bao giờ là
thang cắt giảm — nó là một trang văn bản. **Hôm nay là ngày cơ chế đó bắn**, cùng hình với `DEC-D16-04`
(*"`strict=True` được dựng ở D9 với đúng mục đích này — hôm nay là ngày nó bắn"*).

**Cái descope KHÔNG được phép làm:** đổi shape `Scorecard`. `judge=None` đã mang đúng nghĩa
*"case này chấm không qua LLM-judge"* từ `DEC-02`/`ADR B5`, và `Aggregate`/`Gate` không có field nào
của judge. ⇒ tụt nấc **không đụng một byte nào** của contract — và đó chính là thứ làm `#117` (SWE)
trở thành no-op, xem `DEC-D18-06`.

## DEC-D18-04 · Agreement đo được HÔM NAY — baseline exact-match vs nhãn tay

**Quyết:** ô DoD *"agreement-check có số vs nhãn tay"* đóng bằng agreement của **bộ chấm exact-match
hiện tại** so với nhãn tay, không phải bằng agreement của judge.

**Vì sao đây là con số đúng chứ không phải con số thay thế cho tiện:** câu hỏi thật mà agreement-check
tồn tại để trả lời là *"judge có đáng tin không"* (`#119` viết đúng chữ đó). Câu đó **không trả lời
được** nếu không biết bộ chấm **hiện tại** đồng thuận với người bao nhiêu. Một judge đạt 0.85 agreement
nghe như tốt, cho tới khi biết exact-match đạt 0.92 — lúc đó bật judge là **hạ chất lượng**. Baseline
không phải bước đệm; nó là mẫu số của mọi kết luận về judge sau này.

Và nó có ba tính chất mà số của judge hôm nay không có: **đo được ngay** (không cần key), **tất định**
(chạy lại ra đúng số cũ), **kiểm được trong CI**.

**Điều kiện lật để có số của judge thật:** (a) `manual_label` của DE về, (b) key Gemini được cấp,
(c) ≥1 case thật sự cần judge. Cả ba đều không nằm trong tay AIE-2 ⇒ ghi vào bảng nợ với chủ và hạn,
không ghi vào DoD hôm nay.

**Nhãn THẬT đòi HAI điều kiện, không phải một — `manual_label` về là chưa đủ.** Bản đầu của DEC này
gán nhãn THẬT chỉ theo *"dữ liệu đã tới"*, và đó là một lỗ: một field có giá trị **không** đồng nghĩa
với một phép so có nghĩa. Đo được hôm nay, và đây là dữ kiện quyết định:

```text
SmokeResult.success        : bool      ← thứ bộ chấm THẬT SỰ trả ra
SmokeResult.expects_refusal: bool
```

Bộ chấm hôm nay **không có** vocabulary `ANSWER`/`REFUSE` — nó trả một `bool` nghĩa là *"case này
chấm đạt hay không đạt"*. Nếu nhãn tay của DE là **nhãn nhánh** (`ANSWER`/`REFUSE`) thì hai vế đang
nằm trên **hai trục khác nhau**, và so trực tiếp cho ra một con số vô nghĩa mà vẫn in ra được. Nếu
nhãn tay là **đúng/sai** thì so thẳng với `success` được, không cần mapping.

⇒ **Hai điều kiện, đủ cả hai mới được gán nhãn THẬT:**

1. `manual_label` đã về trên golden-30 (dữ liệu tồn tại);
2. **vocabulary + trục của nhãn tay đã chốt với DE**, và nếu nó khác trục `success` thì **mapping
   đã được ghi ra** (ask ① câu (b) là chỗ hỏi; câu trả lời phải có trước khi diễn giải số).

Thiếu **bất kỳ** điều kiện nào ⇒ số mang nhãn **CƠ CHẾ**. Đây là quyết định *storage shape ≠ agreement
semantics*: `DEC-D18-01` chốt **chỗ để nhãn đi vào**, và chỉ chỗ đó. Nó **không** chốt nhãn ấy nghĩa
là gì, và không được đọc thành đã chốt.

**Ranh giới phải nói ra trong báo cáo:** khi thiếu một trong hai điều kiện trên, số agreement đo trên
**nhãn tay tự gieo trong fixture** — và khi đó nó là **bài kiểm cơ chế**, không phải phép đo trên dữ
liệu thật. Hai thứ này phải mang hai nhãn khác nhau trong báo cáo; gộp lại là đúng lớp lỗi
`_GoldenAwareLLM` (D17): một con số đo trên double được đọc thành số đo trên thật.

## DEC-D18-05 · Cap ≤100/ngày phải BỀN và fail-closed

**Quyết:** counter bền hoá ngoài tiến trình **bằng file JSON cạnh cache**; đọc không được ⇒ **coi như
đã chạm trần** ⇒ descope.

**File, KHÔNG phải `eval.` table** — bản đầu để ngỏ *"hoặc `eval.` table nếu DB có sẵn"* và đó là một
lựa chọn mà phần còn lại của plan không đỡ được: chữ ký ở T2 là `cap_path: Path`/`cache_path: Path`
(đường dẫn file, không có tham số DSN nào), và một counter trong Postgres kéo test ra khỏi *"tất định,
không mạng"* mà `DEC-D18-02`/`DEC-D18-03` vừa chốt. Một quyết định để ngỏ hai đường trong khi đường
thứ hai không có chỗ trong chữ ký là một quyết định chưa quyết.

**Vì sao không để trong RAM:** một counter in-memory reset mỗi lần khởi động tiến trình. `INV-4` nói
*"≤100 call/**ngày**"* — một đơn vị thời gian, không phải một đơn vị tiến trình. Chạy harness 5 lần
trong ngày với counter RAM là cap thật ≤500, và không dòng code nào sai để ai đó nhìn ra.

**Vì sao fail-closed:** đây là luật đã áp ở **bốn** chỗ khác trong quadrant này — `tenant_scope_ok`
(`events` rỗng ⇒ `False`), `chunks_from_trace` (payload không đọc được ⇒ `None`), `_citation_tenant`
(không parse được ⇒ `None`), `compute_scorecard` (`results` rỗng ⇒ raise). Một counter hỏng mà cho
phép gọi tiếp là chỗ duy nhất trong quadrant fail-**open**, và nó fail-open về phía **tốn tiền thật**.

**Khoá cache:** `(case_id, actual)` — khai sẵn ở `golden_case.py:38` và `judge.py:11`. Giữ nguyên,
không phát minh. `actual` nằm trong khoá vì cùng một case chạy lại với câu trả lời khác là một phép
chấm khác; bỏ nó đi là cache trả lời sai cho lần chạy thứ hai.

**Assumption về đồng thời — khai ra thay vì để nó thành một claim mạnh hơn code.** Counter file JSON
đảm bảo cap ≤100 cho **một writer tại một thời điểm** (harness chạy tuần tự, local). Nó **không**
đảm bảo cho nhiều tiến trình ghi đồng thời — hai harness song song có thể cùng đọc `99` rồi cùng ghi
`100`.

Đo để biết assumption này có đang bị vi phạm không: `pyproject.toml` **không** khai `pytest-xdist`,
không có `-n auto`, không có `numprocesses` ⇒ **không có writer song song trong cấu hình hôm nay**.

**Không thêm lock/SQLite/quota phân tán.** Chưa có bằng chứng nào cho thấy execution model hiện tại
cần chúng, và thêm vào là trả giá cho một bài toán chưa tồn tại. Nhưng cũng **không** được viết
*"cap ≤100/ngày"* trần trong báo cáo như một bất biến tuyệt đối — nó đúng **kèm assumption
single-writer**, và assumption đó phải đi cùng con số.

**Điều kiện phủ định (ngày phải quay lại món này):** ai đó bật `pytest-xdist`, hoặc harness được gọi
từ nhiều tiến trình/CI job song song, hoặc counter chuyển sang chia sẻ giữa nhiều máy. Ghi vào bảng
nợ với đúng điều kiện đó, không đặt hạn theo ngày.

**Ranh giới ngày hôm nay:** cap + cache được dựng và test **bằng double**, không có call thật để đếm.
Bài test đo đúng thứ test được: gọi 100 lần qua double ⇒ lần 101 phải từ chối, và cache hit **không**
được tính vào counter (nếu tính thì cache vô nghĩa).

### Sentinel phải mang `reason` — gom một exception là mất thông tin hành động được

**Quyết:** `JudgeUnavailable(reason=...)` với đúng **ba** giá trị:

| `reason` | Nghĩa | Người đọc phải làm gì |
|---|---|---|
| `CAP_REACHED` | Hết quota ngày | Không làm gì — mai reset. Run vẫn hợp lệ |
| `PROVIDER_UNAVAILABLE` | Không dựng được provider (thiếu key, lỗi xác thực, mất mạng) | Cần **người** cấp phát — ask ③ |
| `STATE_UNREADABLE` | Counter/cache đọc không được ⇒ fail-closed | Cần **dọn** file hỏng; số của run này không tin được |

**Vì sao không gom làm một:** chính plan này lập luận bằng **danh tính trigger** — `DEC-D18-03` viết
*"**2/4 trigger** đã thoả"*, và `DESCOPE.md` liệt trigger thành danh sách có tên chứ không thành một
cờ boolean. Một exception trần cho phép báo cáo nói *"đã tụt nấc"* mà **không nói được vì sao**, trong
khi ba dòng bảng trên đòi **ba hành động khác nhau của con người**. Mất phân biệt đó là biến một tín
hiệu vận hành thành một tiếng ồn.

**Ranh giới — không over-engineer:** đúng **một** field enum trên **một** exception. Không hierarchy
exception con, không mã lỗi số, không payload tự do. Ba giá trị vì có đúng ba hành động; thêm giá trị
thứ tư chỉ khi có hành động thứ tư.

**Hệ quả cho harness (T4):** fallback đi **cùng một nhánh** cho cả ba reason — không rẽ ba đường xử
lý. Cái khác nhau chỉ là **thứ được ghi lại**. Gộp nhánh xử lý mà tách nhãn ghi nhận là đúng mức trừu
tượng cần thiết.

## DEC-D18-06 · Không đổi contract — và đó là lý do `#117` của SWE thành no-op

**Quyết:** D18 **không** mở PR nào sang `contracts`.

`#117` giao SWE: *"`scorecard_threshold` đọc được cả nhánh judge lẫn exact-match — không vỡ khi tụt
nấc"*. Đọc kỹ thì điều kiện để câu đó đúng đã **có sẵn**: `Gate.threshold` là
`GateThreshold(success, citation_accuracy)` — hai trục, **không trục nào của judge**; `judge=None`
là trạng thái hợp lệ đã khoá bằng validator từ `contracts#5`. ⇒ tụt nấc không đổi shape nào mà
threshold đọc.

**Việc thật của `#117` vì thế không phải sửa code mà là một bài test** chứng minh
`gate.verdict` giữ nguyên nghĩa ở cả hai nhánh. Nói thẳng điều này với SWE **sáng nay** (ask ②) đáng
giá hơn để họ tự phát hiện lúc 16h — cùng bài học D17 (*"dump payload trước khi viết ask về payload"*),
lần này áp theo chiều ngược: **đo trước rồi báo, thay vì để người khác đo lại thứ mình đã đo**.

## DEC-D18-07 · `match_mode` — vẫn hoãn, điều kiện lật vẫn CHƯA thoả

**Quyết:** không thêm `match_mode` vào `GoldenCase` hôm nay.

`DEC-D16-06` hoãn nó **tới D18** với điều kiện lật đo được: *"ngày DE giao case cần judge (yêu cầu
≥3 case cần judge)"*. Đo lại sáng nay: **0/30** case có `match_mode`, **0/30** case cần judge — điều
kiện lật **chưa thoả**. Hoãn tiếp không phải là né; giữ nguyên lý lẽ gốc: *thêm một field mà mọi giá
trị đều là `exact` là thêm một nhánh code không có case nào đi qua* (`DEC-D12-02` cấm ở tầng render).

**Khác lần trước ở một điểm, và điểm đó phải ghi:** `DEC-D16-06` đặt hạn D18 và hôm nay là D18, nên
đây là lần **rút một hạn tự đặt lần thứ hai**. Luật tự áp: hạn mới **không** được đặt theo ngày, mà
theo **điều kiện** — `match_mode` land **cùng commit** với bài test đầu tiên dùng nó, tức cùng ngày
case cần judge đầu tiên về. Một hạn theo ngày mà rút hai lần thì lần thứ ba không còn ai tin.

---

# §3 — Work items: thứ tự là quyết định, không phải danh sách

Thứ tự có một ràng buộc cứng: **T1 chặn DE**. Mọi giờ T1 trễ là giờ DE hoặc phải chờ, hoặc emit nhãn
vào một loader nuốt câm nó. T1 đi trước cả deliverable chính.

> **T0 tách làm hai, và lý do là một mâu thuẫn trong chính plan này.** Bản đầu gộp *kiểm nền* với
> *đóng cửa sổ ADR + sửa `TEMPLATE.md` + mở issue umbrella* vào một item 30′ ghi *"làm đầu tiên"* —
> trong khi đoạn mở §3 khai **T1 mới là đường găng vì nó chặn DE**. Việc hành chính không mở đường cho
> ai, mà lại đứng trước thứ đang chặn người khác. Tách theo đúng cái nó phục vụ: **T0a mở đường,
> T0b không**.

## T0a · Kiểm nền + comment hình dạng ngày — **P0** (15′, làm đầu tiên)

- Chạy đủ 6 lệnh §1, dán số vào comment `#118`.
- Comment `#118` ghi rõ **hình dạng ngày** (descope là đường mặc định, có số làm chứng) — để cả nhóm
  đọc được trước khi họ xây phần của mình lên giả định "judge sẽ chạy thật".

Chỉ hai việc này, vì chỉ hai việc này **đổi được hành vi của người khác trong ngày**. Xong T0a là đi
thẳng T1, không dừng.

## T0b · Đóng cửa sổ `ADR-D16-05` + hai việc kèm — **P0 nhưng KHÔNG chặn T1** (30′, sau khi T1 mở PR)

- **Đóng cửa sổ phản đối `ADR-D16-05`**: hạn tự khai là **D18** (*"cửa sổ phản hồi tới D18 — ai phản
  đối thì quay về nguyên văn umbrella §3 và ADR này bị rút"*). Kiểm thread `#113`/`evalhub#18`; im
  lặng ⇒ **thành luật**, ghi một dòng vào decision log và thực hiện **hai việc kèm** ADR đã tự giao:
  (1) `mini-rfc/TEMPLATE.md` thêm dòng trỏ về ADR, (2) đề xuất sửa câu *"bất kỳ"* ở
  `umbrella-contract.md:92-93` **qua issue** (umbrella nằm ở `docs/requirements`, ngoài write-scope).
  Một ADR tự đặt hạn rồi để hạn trôi qua không ai nhắc là ADR chưa bao giờ có hiệu lực.

**Vẫn là P0, vẫn phải xong trong ngày** — hạ nó xuống P1 là để một hạn tự đặt trôi qua, đúng thứ
`DEC-D18-07` vừa lập luận là không được lặp. Cái đổi là **vị trí trong ngày**, không phải mức ưu tiên.
Hạn chót: trước **T7b** (đóng ngày).

## T1 · `GoldenCase`: `extra="forbid"` + `manual_label` — **P0, CHẶN DE, làm trước deliverable** (1h)

`DEC-D18-01`. Thứ tự trong T1 cũng là thứ tự đỏ-trước:

1. **Đỏ trước** — bài `test_manual_label_sai_ten_phai_do`: dựng `GoldenCase(..., manaul_label='X')`,
   assert `ValidationError`. **Đo trên code hôm nay: bài này XANH** (field bị nuốt, không raise) ⇒
   đúng nghĩa đỏ-trước, không phải `ImportError` (không tính, theo kỷ luật test của quadrant).
2. Vá: `ConfigDict(frozen=True, extra="forbid")` + `manual_label: str | None = None`.
3. Bài xanh-sau: nhãn đúng tên đọc ra được; nhãn vắng ⇒ `None` (không phải lỗi — subset, không phải
   toàn bộ 30 case có nhãn).
4. **Bài hồi quy trên dữ liệu thật**: `load_golden_set` trên golden-30 **hiện tại** vẫn xanh (đo
   trước: 8 field, khớp 1:1 ⇒ `extra="forbid"` không làm đỏ gì).

**Docstring `manual_label` phải ghi hai thứ**, vì đây là field mà người khác sản xuất:
- nghĩa của `None` = *"case này chưa được gán nhãn tay"* ≠ *"người gán nhãn là không-có-nhãn"*;
- ai sở hữu **giá trị** (DE, `#115`) vs ai sở hữu **shape + loader** (AIE-2) — nguyên văn `DEC-Q5`.

**Báo DE ngay khi merge** (ask ①): shape đã sẵn, tên field chốt, emit được.

## T2 · `LLMJudge` — cache + cap + descope-sentinel — **P0**, deliverable chính (1h45)

`DEC-D18-02` + `DEC-D18-05`. Ba thứ, và cái thứ ba là cái dễ làm sai nhất:

**(a) Seam.** `LLMJudge(llm: LLM, *, cache_path: Path, cap_path: Path, cap: int = 100)`. Không đọc
env, không dựng provider, không biết Gemini tồn tại.

**(b) Cache** khoá `(case_id, actual)`. Cache hit ⇒ **không** tăng counter (nếu tăng thì cache không
tiết kiệm gì và cap sai đơn vị).

**(c) Descope-sentinel** — `judge.py:13-16` khai rõ hợp đồng: khi chạm cap hoặc provider không dùng
được, module này *"làm trạng thái đó **quan sát được**"*, và **không** tự thực hiện fallback —
fallback là việc của `harness.py`. ⇒ raise `JudgeUnavailable(reason=...)`, **không** trả
`(False, 0.0)`. Trả một tuple hợp lệ là biến *"không chấm được"* thành *"chấm và trượt"* — **cùng
đúng lớp lỗi fail-open mà DE tìm ra ở `chunks_from_trace` hôm qua** (`[]` đọc thành *"hàng rào chặn
sạch"*). Lỗi đó vừa bị bắt trong code của chính mình 24h trước; lặp lại nó ở module kế bên là không
học được gì.

`reason` ∈ {`CAP_REACHED`, `PROVIDER_UNAVAILABLE`, `STATE_UNREADABLE`} — bảng nghĩa + vì sao không gom
làm một ở `DEC-D18-05`. *"Quan sát được"* trong docstring `judge.py` đọc là **quan sát được trạng
thái nào**, không phải quan sát được rằng có-một-trạng-thái-nào-đó.

**Test (tất định, `LLM` double):** cache hit không gọi lại · counter bền qua hai instance · gọi thứ
101 raise **với `reason=CAP_REACHED`** · counter file hỏng ⇒ raise **với `reason=STATE_UNREADABLE`**
(fail-closed) · provider ném lỗi ⇒ raise **với `reason=PROVIDER_UNAVAILABLE`** · cache hit **sau** khi
chạm cap vẫn trả được (cache không cần quota).

**Mỗi bài phải assert `reason`, không chỉ assert loại exception.** Một bài
`pytest.raises(JudgeUnavailable)` trần xanh với **mọi** reason ⇒ nó không canh được gì về danh tính —
đó chính là đường lọt của `M-J6` (§T7).

## T3 · Agreement-check + baseline exact-match — **P0**, ô DoD (1h30)

`DEC-D18-04`. Hàm thuần, không phụ thuộc judge:

```
agreement(nhãn bộ chấm, nhãn tay) -> (agreement_rate, n_compared, danh sách case lệch)
```

**Ba thứ trả về, không phải một.** Một `agreement_rate` trần là **đúng thứ `kit#134` gọi là bằng
chứng dị dạng** — một tỷ lệ không kèm mẫu số. `DEC-D16-03` đã trả giá cho bài học này một lần
(`n_scored_citation` phải đi cạnh `citation_accuracy`); không lặp lại ở trục mới. Danh sách case lệch
là thứ biến con số thành hành động được: 0.85 không nói được gì, *"lệch ở HB-07, HB-19, HB-23"* thì
đọc được ngay là lệch cụm từ hay lệch nhánh refusal.

**Fail-closed:** `n_compared == 0` (chưa case nào có nhãn tay) ⇒ trả `None` cho rate, **không** trả
`0.0`. Cùng luật `Aggregate.citation_accuracy` (`DEC-D16-03`): *không đo được* ≠ *đo được và bằng
không*, và một `0.00` in ra không phân biệt được với một phép đo thật.

**Chạy trên dữ liệu nào — cổng 2/2 của `DEC-D18-04`, không phải 1/1:**

| `manual_label` về? | Trục/vocabulary chốt? | Chạy trên | Nhãn số |
|---|---|---|---|
| ✅ | ✅ | golden-30 | **THẬT** |
| ✅ | ❌ | fixture tự gieo | **CƠ CHẾ** |
| ❌ | — | fixture tự gieo | **CƠ CHẾ** |

Dòng giữa là dòng dễ mất cảnh giác nhất: dữ liệu **đã về**, mọi thứ trông như đủ điều kiện, nhưng
phép so vẫn chưa có nghĩa nếu nhãn tay là nhãn nhánh còn bộ chấm trả `success: bool`. **Có dữ liệu
không đồng nghĩa có phép so.**

**Hàm agreement không tự quyết nhãn này** — nó nhận hai list nhãn và trả ba thứ, hết. Việc gán
THẬT/CƠ CHẾ là của **người viết báo cáo**, và `DEC-D18-04` là chỗ ghi luật gán. Nhét luật đó vào hàm
là để một hàm thuần quyết định một câu về phương pháp mà nó không có dữ liệu để quyết.

## T4 · Harness wiring nhánh judge + CI deterministic — **P0**, ô DoD (1h)

- `EvalHarness.run(..., judge: LLMJudge | None = None)` — **additive, default `None`** ⇒ mọi
  call-site hiện tại chạy nguyên (đã đếm: `cli.py`, 2 test integration, `apps/studio`).
- `judge=None` ⇒ đường exact-match, `CaseResult.judge=None` — **hành vi hôm nay, không đổi một dòng**.
- `JudgeUnavailable` ⇒ **bắt tại harness**, tụt nấc exact-match, và ghi lại là **đã tụt nấc kèm
  `reason`** (không nuốt câm — một run tụt nấc mà trông y hệt run không tụt là một scorecard nói dối
  về phương pháp của chính nó).
- **CI**: khẳng định bằng test rằng CI không có đường nào tới network — `judge` không bao giờ được
  dựng với provider thật trong `conftest`.

**Không có predicate "case cần judge" trong D18 — và đây là bản sửa một tham chiếu treo.** Bản đầu của
T4 viết *"judge có mặt + **case cần judge** ⇒ gọi"*, nhưng `DEC-D18-07` quyết **không** thêm
`match_mode`, và plan không định nghĩa selector nào khác. Tức T4 gọi một predicate mà chính plan từ
chối tạo ra — mâu thuẫn nội bộ, không phải chi tiết bỏ sót.

Sửa theo đúng lý lẽ đã có, **không phát minh field production mới**:

- **golden-30 tiếp tục đi exact-match toàn bộ** — 0/30 case cần judge, nên không có gì để định tuyến.
  Thêm một selector production hôm nay là dựng đường dẫn cho một tập rỗng, đúng thứ `DEC-D18-07` vừa
  từ chối (*"thêm một nhánh code không có case nào đi qua"*).
- **Nhánh judge chứng minh bằng fixture/test seam**: harness nhận một `GoldenSet` fixture có case đi
  qua judge (dựng trong test, không nằm trong golden-30), `LLM` double trả nhãn tất định. Nhánh được
  chạy thật và mutant giết được, mà không cần field nào trên dữ liệu production.
- **Selector chính thức** (`match_mode` hoặc thứ tương đương đã chốt) **land cùng thay đổi** với case
  thật đầu tiên dùng nó — nguyên văn `DEC-D18-07`, không phải một luật mới ở đây.

Điều này **không** làm yếu ô DoD nào: ô 1 đòi *seam + cache + cap*, ô 3 đòi *fallback sẵn* — không ô
nào đòi golden-30 phải đi qua judge.

## T5 · `score_run_from_trace` nhận `retrieved_chunks` — **P1**, nợ đến hạn D18 (1h)

Nợ ghi rõ trong bảng D17: 6 call-site còn đi đường `citations` vacuous, và món nặng nhất là
`score_run_from_trace` **vì `workbench/dev_playground_server.py:189` gọi nó** ⇒ số hiển thị trên
Playground **chưa hưởng bản vá F-6**. Nêu bởi SWE ở review `evalhub#18`.

- Đổi **additive**: `score_run_from_trace(case, events, *, tenant_ids=None)`; có `tenant_ids` ⇒ đi
  đường chunks (`chunks_from_trace(events)`), không có ⇒ đường cũ y nguyên.
- **Báo SWE trước khi merge** (ask ②) — API công khai có consumer ngoài quadrant. Đây là luật đã ghi
  ở chính bảng nợ (*"phải additive + báo trước SWE"*), không phải phép lịch sự.

**Hard gate — T5 KHÔNG được bắt đầu trước khi T1–T4 ở trạng thái merge-ready.** Không phải *"nếu còn
giờ"*; *"còn giờ"* là một điều kiện mềm và nó là cách scope phình ra mà không ai quyết định gì.

**Merge-ready nghĩa là gì, chính xác** — theo tiền lệ D17 chứ không theo cảm tính: `evalhub#18` giao
*"6 commit T0–T4 **+ sổ mutation** + vá review"*, tức **sổ mutation ship trong cùng PR**. ⇒ merge-ready
của T1–T4 gồm đủ bốn thứ:

1. Test của T1–T4 xanh, và mỗi bài mới đã **đỏ trước** trên code hôm nay;
2. `M-J1…M-J6` đã **gieo và chết**, bảng ghi **bài nào đỏ** — tức **`T7a` đã xong**;
3. `mypy` + lint sạch, **gom vào trước khi xin review** (D17: push sau approval làm bay approval);
4. PR mở, mô tả xong.

**`T7b`** (daily-note, comment, close issue, bump con trỏ) **không** nằm trong điều kiện này — nó
đứng sau mọi thứ, kể cả T5/T6. Hai nửa là hai item riêng đúng vì lý do này: nếu chỉ có một `T7` thì
điều kiện (2) trỏ vào một item xếp **sau** T5, tạo vòng *T5 chờ T7, T7 chờ T5*.

**Nếu chưa đạt mốc trên vào lúc T5 định bắt đầu ⇒ không bắt đầu T5**, đẩy sang D19 với đúng lý do đo
được (T-nào chưa xanh). Nợ này đã đứng một ngày; đứng thêm một ngày có chủ và có lý do vẫn tốt hơn
một ô DoD hở.

## T6 · `T9c` dọn alias `_retrieved_citations` — **P2** (30′) · **gate ở thân mục, không phải "nếu còn giờ"**

Bước 1 đã merge ở `kit#146`. Bước 2: đếm lại consumer thật (`scripts/smoke_eval_d6.py:66,249`),
chuyển sang `citations_from_trace`, xoá alias.

**Gate — nghiêm hơn T5 vì ưu tiên thấp hơn:** T6 chỉ bắt đầu sau khi **T5 đã xong hoặc đã được quyết
định đẩy sang D19**. Đây là dọn dẹp thuần, không đóng ô DoD nào, và nó chạm **repo cha** (PR thứ hai,
tức một vòng review nữa). Một món P2 chen trước một món P1 chỉ vì nó nhanh hơn là xếp việc theo độ dễ
chứ không theo giá trị.

Nếu đến cuối ngày chưa tới lượt ⇒ để nguyên, ghi vào nợ D19. `T9c` đã đứng từ D16 và bước 1 đã hạ
cánh; đứng thêm một ngày không đổi gì.

## T7a · Tự gieo mutant — **P0** (45′) · **nằm TRONG merge-ready của T1–T4, chạy TRƯỚC T5**

> **T7 tách đôi, và chỗ này là chỗ phải ghi nó.** §1 và T5 đều khai T7 có hai nửa nằm ở hai vị trí
> khác nhau trong ngày, nhưng bản trước để T7 là **một** item duy nhất đặt sau T5/T6 — đọc theo thứ
> tự văn bản thì mutation chạy **sau** T5, trong khi T5 lại lấy mutation làm điều kiện khởi động. Hai
> nửa phải có hai mục riêng, nếu không cái gate ở T5 không thi hành được.

Khai mutant **trước khi viết test** (kỷ luật đã áp từ D16, và D17 chứng minh giá trị của nó):

| Mutant | Gieo vào | Bất biến bị tấn công | Dự đoán bài đỏ |
|---|---|---|---|
| `M-J1` | `extra="forbid"` → `extra="ignore"` | field lạ phải ồn, không được câm | bài nhãn-sai-tên của T1 |
| `M-J2` | cache hit **có** tăng counter | cache không tiêu quota | bài cache-không-tốn-quota |
| `M-J3` | chạm cap ⇒ trả `(False, 0.0)` thay vì raise | *không chấm được* ≠ *chấm và trượt* | bài descope-sentinel + bài harness-tụt-nấc |
| `M-J4` | counter đọc lỗi ⇒ coi như `0` (fail-open) | state hỏng ⇒ fail-closed | bài counter-hỏng-fail-closed |
| `M-J5` | `n_compared == 0` ⇒ trả `0.0` thay vì `None` | *chưa đo* ≠ *đo được và bằng 0* | bài agreement-mẫu-số-rỗng |
| **`M-J6`** | mọi đường raise dùng **một** `reason` hằng (`CAP_REACHED`) | **danh tính** của trigger, không chỉ sự tồn tại của nó | bài counter-hỏng (`STATE_UNREADABLE`) + bài provider-lỗi (`PROVIDER_UNAVAILABLE`) |

**`M-J6` không phải mutant thêm cho đủ số — nó canh một bất biến mà `M-J3` không chạm.** `M-J3` hỏi
*"có raise không"*; `M-J6` hỏi *"raise đúng cái gì không"*. Hai câu khác nhau, và câu thứ hai có một
**đường lọt cụ thể**: một bài viết `pytest.raises(JudgeUnavailable)` trần sẽ **xanh với mọi `reason`**,
nên `M-J6` sống sót trong khi cả bộ vẫn xanh — đúng hình `M1` của `kb#19` hôm qua (sống với 204 test
xanh). Nó chỉ chết nếu bài test assert **giá trị** `reason`, và đó là lý do T2 đòi mỗi bài assert
`reason` chứ không chỉ assert loại exception.

Điều kiện để `M-J6` tồn tại: `reason` là **một phần contract observability** (`DEC-D18-05`). Nếu điểm
đó bị rút thì `M-J6` rút theo — mutant không được sống lâu hơn bất biến nó canh.

**Bảng phải ghi *bài nào đỏ*, không chỉ *có đỏ hay không*** — luật rút ra từ D17 (`M-F3` dự đoán 2
bài, thực tế 1 bài, và sai lệch đó chỉ lộ vì bộ chạy in tên bài). Script so `DIE`/`SURVIVE` không tự
bắt được.

Xong T7a ⇒ điều kiện (2) của merge-ready thoả ⇒ **mới xét tới T5**.

## T7b · Đóng ngày — **P0** (30′) · **đứng SAU tất cả, kể cả T5/T6**

Daily-note → `docs/reports` + PR, comment + close `#118`, bump con trỏ nếu evalhub tiến.

Chạy cuối cùng vì nó **ghi lại** thứ đã xảy ra: nếu T5 bị đẩy sang D19 thì daily-note phải nói điều
đó, và không thể nói trước khi biết. Đây cũng là chỗ **hạn chót của T0b** — không đóng ngày khi cửa
sổ `ADR-D16-05` chưa được xử lý.

---

# §4 — Bảng nợ đến hạn D18

| Món | Chủ | Trạng thái vào D18 | Xử lý hôm nay |
|---|---|---|---|
| **6 call-site đi `citations` vacuous** — `score_run_from_trace` ⇒ Playground chưa hưởng F-6 | AIE-2 (+SWE consume) | đến hạn | **T5**, additive + ask ② |
| **Recalibrate ngưỡng** — `DEC-D17-04` giữ `0.9/0.95`; điều kiện lật: LLM sinh prose thật ≥30 case | AIE-2 | **chưa lật** — cùng blocker với judge (không key) | Ghi lại, hạn mới theo **điều kiện** không theo ngày; nêu ở ask ③ |
| **`T9c`** xoá alias `_retrieved_citations` | AIE-2 | bước 1 xong (`kit#146`) | **T6**, P2 |
| **`T9b`** bài hồi quy embedding | AIE-2 | chờ DE trả ask ③ của D17 (`#110`) | Nhắc lại trong ask ①; không chặn |
| **`T9a`** `__all__` thiếu 3 hàm D15 | AIE-2 | P2 | Đã đếm lại trong T0a — `__all__` có 17 tên; 3 hàm D15 thiếu là `answer_from_trace` · `score_run_from_trace` · `render_run_cases`. Đếm rộng còn lộ thêm `TraceAnswerError`/`read_run`/`list_runs`/`ddl` chưa export ⇒ món này **lớn hơn nhãn "3 hàm"**, giữ P2 nhưng ghi lại đúng quy mô |
| **`ADR-D16-05`** cửa sổ phản đối | AIE-2 | **hết hạn hôm nay** | **T0b** — im lặng ⇒ thành luật + 2 việc kèm. P0, nhưng chạy **sau** khi T1 mở PR (T0b không chặn đường găng) |
| **Cap ≤100 khi nhiều writer đồng thời** (mới, `DEC-D18-05`) | AIE-2 | assumption single-writer — đo: không `xdist`/`-n auto` trong `pyproject.toml` | Không làm hôm nay. **Điều kiện lật:** ai đó bật `pytest-xdist`, hoặc harness chạy song song nhiều tiến trình/CI job, hoặc counter chia sẻ giữa nhiều máy |
| **Vocabulary/trục của `manual_label`** (mới, `DEC-D18-04`) | **DE** (`#115`) + AIE-2 chốt mapping | chưa chốt — ask ① câu (b) | Không chặn T3 (chạy được ở nhãn CƠ CHẾ). **Chặn việc diễn giải số THẬT** — điều kiện 2/2 của `DEC-D18-04` |
| **`match_mode`** | AIE-2 + DE | điều kiện lật chưa thoả (0/30) | `DEC-D18-07` — hoãn theo **điều kiện**, không theo ngày |
| **Nhánh `results == []`** (D16 để lại) | AIE-2 | **vẫn chưa ai gieo** | Gieo trong **T7a** nếu còn giờ — `compute.py:74` raise, chưa mutant nào chạm |
| **Bài 3 là bài duy nhất canh vế vai `no_leak`** | AIE-2 | điểm mù đã ghi (sổ mutation §2) | Không mở rộng hôm nay; đã có chủ + đã ghi |
| **`manual_label`** vào golden-30 | **DE** (`#115`) | đến hạn hôm nay | **T1 dọn chỗ trước**, ask ① báo shape sẵn |
| **Cấp key Gemini** cho eval | **SWE / người giữ hạ tầng** | chưa có | ask ③ — điều kiện lật của cả judge lẫn recalibrate |
| **Chủ trục INV-1 roles** | **chưa có chủ** — đề xuất SWE, treo từ D12 | vẫn treo | Nhắc lần thứ ba trong comment `#119`; không nhận |

---

# §5 — Ask gửi ai, nguyên văn — **3 owner · 5 request**

> Không @ mentor. Đồng đội cùng cấp thì bình thường.

**① → DE (`#115`, thread `kb`)**

> `GoldenCase` đã sẵn chỗ cho `manual_label` (`str | None`, optional) từ `evalhub#<T1>` — emit được
> ngay, tên field chốt là `manual_label` đúng như `golden_set.py:33` và `DL-16.1` đã chừa.
>
> Kèm một cảnh báo đo được: **trước bản vá này, loader NUỐT CÂM field lạ.** `GoldenCase` không khai
> `extra` nên pydantic mặc định `ignore` — emit `manual_label` vào yaml sẽ nạp thành công, field bị
> vứt, không lỗi nào nổi lên. Đã đóng bằng `extra="forbid"`, nên từ giờ **sai tên field là đỏ tại
> loader** thay vì câm. Nếu đã emit thử trước hôm nay thì kiểm lại — nó không vào.
>
> Hai câu hỏi: (a) subset bao nhiêu case sẽ có nhãn (mẫu số của agreement)? (b) giá trị nhãn là
> nhãn **nhánh** (`ANSWER`/`REFUSE`) hay nhãn **đúng/sai** của câu trả lời?
>
> Câu (b) **không phải câu hỏi cho vui** — nó quyết định số agreement có diễn giải được hay không.
> Đo được ở phía bộ chấm: `SmokeResult` trả `success: bool` (*"case chấm đạt hay không"*) và
> `expects_refusal: bool` — **không có** vocabulary `ANSWER`/`REFUSE`. Nếu nhãn tay là nhãn nhánh thì
> hai vế nằm trên **hai trục khác nhau**, so thẳng ra một con số vô nghĩa mà vẫn in ra được; lúc đó
> cần một **mapping ghi ra thành văn** trước khi bất kỳ số nào được đọc. Nếu nhãn tay là đúng/sai thì
> so thẳng với `success`, không cần gì thêm.
>
> Trước khi có câu trả lời cho (b), số agreement trên golden-30 mang nhãn **CƠ CHẾ** chứ không phải
> **THẬT** — kể cả khi `manual_label` đã về đủ. Dữ liệu tồn tại và phép so có nghĩa là hai điều kiện
> khác nhau.
>
> Nhắc lại ask ③ của D17 (`#110`, bài hồi quy embedding) — chưa có trả lời, không chặn D18.

**② → SWE (`#117`, thread `workbench`)**

> Hai việc, một cái có thể tiết kiệm cả buổi:
>
> (a) **`#117` có thể đã xong sẵn.** Đo trước khi viết: `Gate.threshold` là
> `GateThreshold(success, citation_accuracy)` — **không trục nào của judge**; `judge=None` đã là
> trạng thái hợp lệ khoá bằng validator từ `contracts#5`. ⇒ tụt nấc exact-match **không đổi shape nào**
> mà `scorecard_threshold` đọc. Việc thật có lẽ là **một bài test** chứng minh `gate.verdict` giữ
> nguyên nghĩa ở cả hai nhánh, không phải sửa code. Nếu đo ra khác thì báo lại.
>
> (b) `score_run_from_trace` sẽ nhận thêm `tenant_ids` **keyword-only, default `None`** (đường cũ y
> nguyên khi không truyền). Có truyền ⇒ đi đường chunks và **Playground hưởng bản vá F-6** — hiện tại
> số hiển thị vẫn đi đường `citations` vacuous, đúng như đã nêu ở review `evalhub#18`.

**③ → SWE / người giữ hạ tầng (thread `#119`)**

> Eval cần một key LLM thật để (a) judge có số agreement thật, (b) recalibrate ngưỡng có số — `#106`
> đã thoả nhưng `success_rate = 0.2667` hiện đo **double** chứ không đo agent (`DEC-D17-04`).
>
> Trạng thái đo được: `.env` không tồn tại, `STUDIO_GEMINI_API_KEY` không có trong môi trường,
> `STUDIO_USE_FAKE_PROVIDERS=true` là mặc định. `GeminiProvider` thì đã sẵn sàng — thiếu đúng phần
> cấp phát.
>
> **Không chặn D18** — hôm nay chạy nấc exact-match theo `DESCOPE.md` (2/4 trigger đã thoả), judge
> dựng đủ seam + cache + cap và test tất định bằng double. Cần key để lật hai món trên, không cần để
> đóng DoD hôm nay. Nếu key không cấp được trong S2 thì nói sớm — khi đó "agreement của judge" là một
> ô vĩnh viễn không đóng được và cả nhóm nên biết điều đó thay vì mỗi ngày dời một ngày.

---

# §6 — Rủi ro đã biết

| Rủi ro | Dấu hiệu sớm | Xử lý |
|---|---|---|
| **`extra="forbid"` làm đỏ yaml của DE** vì có field mình chưa biết | `load_golden_set` đỏ trong T1 bước 4 | Đã đo trước: 8 field khớp 1:1, rủi ro **0** trên dữ liệu hiện tại. Nếu DE emit thêm field khác cùng ngày ⇒ khai optional, không quay lại `ignore` |
| **`manual_label` không về trong ngày** | DE chưa push tới 14h | `DEC-D18-04`: số agreement mang nhãn **CƠ CHẾ** thay vì **THẬT**, nói thẳng trong báo cáo. Không hoãn ô DoD, không giả vờ là số thật |
| **`manual_label` VỀ nhưng trục/vocabulary chưa chốt** — nguy hơn ca trên vì nó trông như đã đủ điều kiện | DE push nhãn mà ask ① (b) chưa có trả lời | `DEC-D18-04` đòi **2/2** điều kiện. Dữ liệu về mới là 1/2 ⇒ số vẫn mang nhãn **CƠ CHẾ**. Cạm bẫy cụ thể: nhãn nhánh `ANSWER`/`REFUSE` so thẳng với `SmokeResult.success: bool` cho ra một con số **in được nhưng vô nghĩa** |
| **Gom `JudgeUnavailable` mất `reason`** | `M-J6` sống; bài test chỉ `pytest.raises(JudgeUnavailable)` trần | `DEC-D18-05`: mỗi bài assert **giá trị** `reason`. Ba reason = ba hành động người khác nhau; mất phân biệt là mất tín hiệu vận hành |
| **Claim `cap ≤100` mạnh hơn code** khi có writer song song | Ai đó bật `pytest-xdist` hoặc chạy harness song song | Assumption **single-writer** khai tường minh ở `DEC-D18-05` (đo: không `xdist`/`-n auto` hôm nay). Không thêm lock; ghi điều kiện phủ định vào bảng nợ |
| **T5 khởi động sớm, ăn giờ của P0** | Bắt tay T5 khi T1–T4 chưa merge-ready | Hard gate ở T5: 4 điều kiện merge-ready đo được. *"Nếu còn giờ"* không phải điều kiện |
| **Bịa một `Judge(...)` để làm đầy ô DoD** | Bất kỳ dòng nào dựng `Judge(` ngoài test | Cấm ba lần bởi ba nguồn (`judge.py`, `contracts/scorecard.py`, `ADR B5`). Thêm test guard quét `src/` — cùng hình `test_src_khong_hardcode_duong_dan_kb` |
| **Judge trả tuple thay vì raise khi chạm cap** | `M-J3` sống | Đúng lớp fail-open DE bắt được ở `chunks_from_trace` hôm qua. Mutant khai trước, không để tự phát hiện |
| **Descope bị đọc thành "làm không xong"** | Câu hỏi trong review | Báo cáo phải dẫn `DESCOPE.md` viết **D2** + 2 trigger đo được. Một thang cắt giảm viết trước rồi kích hoạt đúng điều kiện là **quy trình chạy đúng**, không phải thất bại |
| **Số agreement không có mẫu số** | `agreement_rate` trần trong báo cáo | `DEC-D18-04` đòi trả 3 thứ. `kit#134` gọi tên lớp lỗi này rồi |
| **Push làm bay approval** | Approve rồi push tiếp | Gom lint/format/vá review **trước** khi xin review. Đã mắc ở D17 — hai approve bị `DISMISSED`, phải xin lại |
| **Squash sai quy ước repo** | Merge PR nhiều commit | `evalhub` dùng **merge-commit** (`#16`, `#17`). Đã mắc ở D17 với `evalhub#18` |

---

# §7 — Định nghĩa "xong" cho D18

**Ô DoD `#118` — bốn ô, và mỗi ô kèm cách kiểm:**

1. ✅ **`LLM-judge cache+cap≤100`** — `LLMJudge` nhận `LLM` qua seam tiêm vào; cache khoá
   `(case_id, actual)`; counter **bền ngoài tiến trình** + **fail-closed**; chạm cap ⇒ raise
   `JudgeUnavailable(reason=CAP_REACHED)`, không trả tuple. Kiểm: 6 bài tất định, 0 call mạng.
   Con số `≤100` đi kèm **assumption single-writer** (`DEC-D18-05`) — viết trần là claim mạnh hơn code.
2. ⚠️ **`agreement-check có số vs nhãn tay` — đóng ĐƯỢC MỘT NỬA, và nửa kia không đóng được hôm nay.**
   Hàm trả `(rate, n_compared, case_lệch)`; `n_compared == 0` ⇒ `rate = None` không phải `0.0`.

   **Dấu ⚠️ chứ không phải ✅, khớp nguyên văn bảng ở Executive Summary.** Đánh ✅ ở đây trong khi
   exec-summary ghi *"một nửa"* là để hai chỗ trong cùng một tài liệu nói hai câu khác nhau về **cùng
   một ô DoD** — và §7 là chỗ người ta căn vào để tuyên bố ngày đã xong, nên chỗ này sai thì nó sai
   về phía **dễ tuyên bố hoàn thành hơn thực tế**.

   **Nửa đóng được:** agreement của **BỘ CHẤM EXACT-MATCH** vs nhãn tay — số thật, tất định, kiểm
   được trong CI, và là mẫu số cho mọi kết luận về judge sau này. Đây **không** phải giải thưởng an
   ủi; thiếu nó thì con số của judge sau này không diễn giải được.

   **Nửa KHÔNG đóng được:** agreement của **LLM-judge**. Judge chưa được đo agreement lần nào trong
   D18. Ai đọc ô này thành *"judge đã được kiểm chứng"* là đọc sai.

   **Hai trục nhãn, trực giao, không được gộp:**

   | Trục | Giá trị | Đủ điều kiện khi |
   |---|---|---|
   | **Chủ thể** đo | exact-match scorer *(hôm nay)* · LLM-judge *(chưa)* | **đủ 3** điều kiện `DEC-D18-04`: `manual_label` · key · ≥1 case cần judge |
   | **Dữ liệu** đo | **THẬT** golden-30 · **CƠ CHẾ** fixture | **đủ 2** điều kiện `DEC-D18-04`: dữ liệu về · trục đã chốt |

   Báo cáo phải nói **cả hai**: *"agreement của exact-match scorer, đo trên CƠ CHẾ"* là một câu đầy
   đủ; *"agreement 0.87"* thì không.
3. ✅ **`exact-match fallback sẵn`** — `judge=None` ⇒ đường exact-match, hành vi hôm nay không đổi
   một dòng; `JudgeUnavailable` ⇒ harness tụt nấc **và ghi lại là đã tụt, kèm `reason`**. Không đụng
   một byte contract.
4. ✅ **`CI deterministic`** — hệ quả cấu trúc của `DEC-D18-02`: không đường nào tới network trong CI.

**Điều kiện chung, giữ nguyên từ các ngày trước:**

- Mọi bài test mới **đỏ trước** trên code hôm nay (`ImportError` **không tính**).
- Mutation khai **trước** khi viết test; bảng ghi **bài nào đỏ**, không chỉ có-đỏ-hay-không. Mutant
  chỉ tồn tại chừng nào bất biến nó canh còn tồn tại.
- **Mọi món AIE-2 hoãn** có **chủ + hạn + điều kiện lật đo được**. **0 món hoãn vô chủ.**

  Câu này giới hạn ở **tập hoãn của AIE-2** — bản đầu viết trần *"0 món vô chủ"* và nó mâu thuẫn
  trực tiếp với §4, nơi có một dòng ghi **"chưa có chủ"**: *chủ trục INV-1 roles*, treo từ D12.

  Mâu thuẫn đó **không** được gỡ bằng cách gán món đó cho AIE-2 để bảng đẹp. Bộ chấm **quan sát**
  hàng rào, không **tạo** hàng rào — lý do từ chối đã ghi từ D12 và không đổi. Nói đúng trạng thái:
  đây là **nợ ownership liên nhóm chưa giải**, nằm **ngoài** tập hoãn của AIE-2, đã đề xuất chủ (SWE)
  và bị bỏ qua **ba** kỳ. Việc nó chưa có chủ là một **finding phải nêu lại trong `#119`**, không
  phải một ô để lấp. Một bảng nợ tự nhận "0 món vô chủ" trong khi có một dòng vô chủ thì nó đang
  giấu đúng thứ nó tồn tại để phơi ra.
- Ranh giới nói ra thay vì để phát hiện sau, **trên cả hai trục**: (a) **chủ thể** — số này của
  exact-match hay của judge; (b) **dữ liệu** — đo trên golden-30 THẬT hay fixture CƠ CHẾ. Không gộp
  hai trục, không bỏ trục nào.
- PR: merge-commit (không squash), gom lint trước khi xin review, ≥1 approval bất kỳ.

**Thứ KHÔNG được tính là xong:**

- Một `Judge(agreement=...)` hằng số ở bất kỳ đâu ngoài test.
- Một `agreement_rate` không kèm `n_compared`.
- Một số đo trên fixture được trình bày như số đo trên golden-30 thật.
- Một số đo của **exact-match scorer** được trình bày như agreement **của judge**.
- Một số gán nhãn **THẬT** khi mới thoả **1/2** điều kiện `DEC-D18-04` (dữ liệu về nhưng trục chưa chốt).
- Judge "chạy được" bằng cách bỏ qua cap hoặc bỏ qua cache.
- `JudgeUnavailable` raise mà **không** mang `reason`, hoặc mang một `reason` không phản ánh trigger thật.
- **`cap ≤100/ngày` viết trần** trong báo cáo mà không kèm assumption single-writer.
- T5 được bắt đầu khi T1–T4 **chưa** merge-ready (4 điều kiện, đo được từng cái).
- Một selector "case cần judge" trên **dữ liệu production** khi golden-30 vẫn 0/30 case cần judge.
