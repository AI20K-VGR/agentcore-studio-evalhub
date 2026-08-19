# Plan Day 23 — AIE-2 · Nối `judge` vào production, nhưng đóng cổng `DEC-05` TRƯỚC · Thứ Tư 19/08/2026

> **Issue:** không có đề bài rời theo ngày — `kit#167` chốt *"Sprint 3 không có đề bài rời theo ngày, việc hằng ngày nhóm tự chia"*. Việc hôm nay neo về `apps/studio#20` (đã có chữ xác nhận của AIE-1 ngày 18/08) và phần đuôi kế hoạch 4 bước ở `kit#176`.
> **Repo WRITE:** `agentcore-studio-evalhub` · `agentcore-studio-app` · `agentcore-studio-kit`
> **Vai:** bút của **bộ chấm**. Hôm nay không thêm một tầng chấm nào — hôm nay là làm cho tầng chấm đã có **không nói dối được**.

---

# Executive Summary

`apps/studio#20` là một PR nối dây đúng một dòng: `_evaluate` dựng `LLMJudge` rồi truyền `judge=` vào
`EvalHarness.run()`. Tham số đó có từ D18 và **chưa từng có caller thật**. Đọc lại chỗ tiêu thụ trước
khi nối thì thấy nối dây không phải việc trung tính:

```text
harness.py:_hoi_judge   nhận  (case.expected, scored.actual)      ← KHÔNG có `events`
harness.py:_score_case_run   hạ success khi case_run.events == []  ← DEC-05, "bất kể answer nói gì"
harness.py:run          if not scored.success: → hỏi judge → model_copy(success=verdict)
```

Ba dòng đó cạnh nhau cho một đường lật **tất định**: case nhánh trả-lời có `answer` **chứa đúng cụm**
`expected` nhưng `events == []` sẽ trượt nấc 1 đúng theo `DEC-05`, rồi được hỏi judge, rồi judge —
làm **đúng** việc của nó — trả `PASS`, và `DEC-05` bị tháo. Không cần judge phán sai lần nào.

Nên thứ tự hôm nay không phải sở thích: **đóng cổng ở `evalhub` trước, nối dây ở `apps/studio` sau.**
Đảo lại thì có một cửa sổ mà `main` của kit có judge chạy trên đường publish nhưng chưa có cổng — và
đó là fail-open **sống thật**, khác hẳn cửa sổ đỏ CI của `kit#176` hôm qua.

Cùng lớp bài học với `app#26` hôm qua: ở đó, nối `recipe_hash()` vào `publish()` mà không tiêm
`recipe=` biến một hệ fail-closed (luôn 409) thành fail-open (publish thành công kèm chứng nhận sai
đối tượng). **Bật một tầng lên trước khi bịt chỗ nó có thể nói dối là mẫu lỗi lặp lại lần thứ hai
trong hai ngày.** Ghi ra ở đây để lần thứ ba nhận ra nhanh hơn.

---

## §1 · Đo trước, và số đo nói ngược điều dễ tưởng

Chạy golden-30 qua spine thật (`EngineAgentRunner` + `PgKbSearch` + `PgTraceWriter` + Postgres,
`ExtractiveFakeLLM`), phân lớp **lý do trượt** của 22 case nhánh trả-lời:

| Lý do trượt | Số case |
|---|---|
| content-miss (`_contains_phrase` không khớp) | **17** |
| `answer.refused is True` | **0** |
| no-trace (`events == []`) | **0** |

Con số `17` khớp đúng số đã ghi trong docstring `EvalHarness.run` từ D20 — dùng làm **đối chứng cho
chính cách dựng phép đo**, không phải một số mới.

Hai kết luận, và cả hai đổi cách viết PR:

1. **no-trace = 0/22 ⇒ bản vá hôm nay là fence, KHÔNG phải bug-fix.** Nó không sửa một con số nào
   đang sai. `DEC-05` tồn tại đúng cho ca **runner hỏng** (trace writer chết, engine đoản mạch), và
   trước bản vá thì judge tháo `DEC-05` **đúng vào lúc `DEC-05` có việc**. Khai là fence.
2. **refused = 0/22 ⇒ trục đó để mở là quyết định có số đỡ**, không phải bỏ sót.

---

## §2 · Cổng đặt TRƯỚC lời gọi, không phải bỏ verdict sau

```python
def _duoc_hoi_judge(case, case_run, scored) -> bool:
    if case.expects_refusal or scored.success:
        return False
    return bool(case_run.events)          # ← cổng DEC-05
```

Hai cách cho **cùng một `Scorecard`**. Cái phân biệt là **quota**: `cap ≤100/ngày` (`INV-4`,
`DEC-D18-05`) là hạn mức chia sẻ, **bền ngoài tiến trình** — một lần gọi tiêu cho một case mà verdict
chắc chắn bị bỏ là một lần gọi mất hẳn. Nên bất biến đúng không phải *"verdict không được dùng"* mà là
*"judge không được hỏi"*, và nó cần **lưới riêng đếm số lần gọi**.

Vế đó không suy ra được từ vế kết quả, và đã gieo mutant để chứng minh chứ không khai suông — xem §3
T2.

---

## §3 · Bốn task

### T1 · `harness.py` — cổng `_duoc_hoi_judge` + 3 bài

Fixture **bất đối xứng theo hai trục độc lập**: `NT-01` trượt *chỉ vì* no-trace (text khớp), `NT-02`
trượt *chỉ vì* content (có trace), `NT-03` không trượt gì. Cân ba ca theo cùng một kiểu thì một cổng
đọc sai trục vẫn ra cùng số lần gọi judge — đúng lớp lỗi `M-G7` đã dạy ở D20.

| Bài | Khoá gì |
|---|---|
| `test_no_trace_judge_khong_lat_duoc_cong_dec05` | Kết quả: `NT-01` giữ `False` dù judge trả `PASS` |
| `test_no_trace_judge_khong_he_duoc_goi` | **Số lần gọi** = 1, và prompt đó là `NT-02` chứ không `NT-01` |
| `test_doi_chung_duong_case_content_miss_co_trace_van_lat_duoc` | Đối chứng dương: judge vẫn lật được ca hợp lệ |

### T2 · Sổ mutation `docs/mutations/judge-no-trace-d23.md`

**4/4 killed**, và ghi thẳng ra một điều bất lợi cho chính bộ test: `M-T1` (bỏ cổng) / `M-T2` (cổng
trả `False` luôn) / `M-T3` (đảo cổng) bị **cả ba** bài giết ⇒ xét riêng chúng thì ba bài **trông như
dư hai**.

`M-T4` mới là mutant tách chúng ra — cổng đặt **sai chỗ**: vẫn hỏi judge, chỉ bỏ verdict cho ca
no-trace. `Scorecard` trùng khít bản có bản vá, nên gieo ra **2 passed, 1 failed**: chỉ bài đếm số lần
gọi đỏ. Nếu sổ chỉ có `M-T1..M-T3` thì bỏ bài đó đi vẫn thấy *"3/3 killed"*.

### T3 · `DEC-D23-01` + `DEC-D23-02` vào `docs/decisions/scorecard.md`

- **`DEC-D23-01`** — cổng judge × `DEC-05`; kèm khai phạm vi (fence, không bug-fix) và trục `refused`
  để mở với số `0/22`.
- **`DEC-D23-02`** — assumption **single-writer** của `DEC-D18-05` **không còn giữ** khi call-site là
  HTTP route. `_doc_counter`/`_ghi_counter` là đọc-sửa-ghi JSON **không lock**, `_ghi_cache` ghi lại
  **toàn bộ** file; `_evaluate` được gọi từ **cả** `/evaluate` lẫn `/publish` ⇒ 2 request đồng thời
  làm cap vượt **trong im lặng** và cache entry bị ghi đè. Luận cứ bảo vệ cũ (*"không khai
  `pytest-xdist`"*) nói về **tiến trình test**, không nói gì về tiến trình server.

Nhận cuộc đua ở S2 — ranh giới không-over-engineer của `DEC-D18-05` vẫn đúng — nhưng nợ giờ có **điều
kiện lật** viết ra: >1 admin bấm Publish/Evaluate đồng thời, hoặc uvicorn `--workers` > 1.

### T4 · `apps/studio#20` — nối dây, sau khi cổng đã vào con trỏ

`_evaluate` dựng `LLMJudge(build_llm(), cache_path=…, cap_path=…)` và truyền `judge=`. Hai đường dẫn
lấy từ **2 field mới trong `Settings`** (có default) — repo chưa có convention nào cho file state ghi
được: `_GOLDEN_SET_DIR` là đường **đọc**, `Dockerfile` chỉ có `WORKDIR /app`, compose không mount
volume nào cho app. Vì chạm `settings.py` là rộng hơn câu *"chỉ đụng đúng call-site"* của AIE-1 nên đã
xin thêm 1 dòng xác nhận trên issue, **chưa mở PR trước khi có**.

Hai bài theo DoD của issue, và lý do phải **hai** chứ không một là một phép đo: `ExtractiveFakeLLM`
gặp prompt judge (không có mark `[chunk]`) trả `"Không có đoạn trích nào để trả lời."`, `_doc_verdict`
thấy không phải `PASS`/`FAIL` ⇒ raise `PROVIDER_UNAVAILABLE`. Nên trên CI mặc định
(`use_fake_providers=true`) judge **luôn** tụt nấc, và một bài chỉ khẳng định *"đã vào nhánh judge"*
sẽ xanh mà không phân biệt được judge-hoạt-động với judge-tụt-nấc.

---

## §4 · Luật liêm chính — viết TRƯỚC khi chạy

1. **Đỏ trước, và chứng minh bằng mutant chứ không bằng câu chữ.** Docstring bài test khai *"phải đỏ
   trên code trước bản vá"* thì phải có mutant gieo đúng ca đó trong sổ.
2. **Khai đúng loại thay đổi.** `no-trace = 0/22` ⇒ gọi nó là fence. Gọi là *"vá một fail-open"* mà
   không nói con số 0 là để người đọc tự suy ra một thứ sai.
3. **Không chặn một trục chưa đo.** Trục `refused` để mở vì `0/22`, và vì `refused is False` là **một
   phần của phán quyết nội dung** theo chính docstring `score_case` — chặn nó là quyết định MỚI, không
   phải bảo vệ một quyết định có sẵn.
4. **Không sửa `judge.py` để chữa một chỗ hở của `harness.py`.** Cổng thuộc tầng định tuyến; nới
   `except` ở tầng sinh tín hiệu sẽ biến descope thành thùng rác (bài học D18/T7a).

---

## §5 · Rủi ro phải nêu ngay

**R1 — cửa sổ fail-open nếu đảo thứ tự.** CI của repo `apps/studio` reconstruct evalhub từ **kit
main**. Nên bốn bước phải đúng thứ tự: evalhub PR merge → **bump con trỏ evalhub ở kit** → `app#20`
merge → bump con trỏ `apps/studio`. Vào `app#20` trước khi kit pin bản có cổng là dựng đúng cái cửa sổ
§Executive Summary vừa mô tả.

**R2 — không push thêm vào nhánh của một PR đang chờ review.** Branch protection dismiss review khi có
commit mới. Bump con trỏ evalhub phải là **PR riêng**, không nối vào PR bump `apps/studio`.

**R3 — `DEC-D23-02` chưa vá.** Ghi nhận, có điều kiện lật, không tự nhận là đã đóng.

**R4 — `uv.lock` của kit cũ hơn con trỏ `apps/studio`.** Phát hiện lúc chạy suite tại chỗ: clone sạch
`uv run` sẽ re-resolve và cài `openai` (extra mà `apps/studio` khai từ `app#19`), rồi `mypy` báo
`providers/openai.py:30: Unused "type: ignore"`. CI xanh chỉ vì cả 5 chỗ dùng `uv sync --frozen` —
dùng lock as-is, **không** kiểm mới/cũ; `--locked` mới là cờ bắt được. Fresh clone và CI đang cho hai
kết quả `mypy` khác nhau. Không thuộc quadrant này — cần issue cho `app#19`/lock.

---

## §6 · DoD

- [x] `_duoc_hoi_judge` chặn ca `events == []`, đặt **trước** lời gọi judge.
- [x] 3 bài, trong đó **1 bài đếm số lần gọi** — không suy ra được từ bài assert kết quả.
- [x] Mutant `M-T1…M-T4` gieo thật, **4/4 killed**; `M-T4` ghi rõ chỉ **1** bài giết.
- [x] Phép đo phân lớp lý do trượt trên golden-30 qua spine thật: `17 / 0 / 0`.
- [x] `DEC-D23-01` + `DEC-D23-02` vào decision log, kèm điều kiện lật.
- [x] `evalhub` **248 passed** (245 + 3), `mypy` 45 file sạch, `ruff` sạch, `lint-imports` 0 broken.
- [x] PR `evalhub#30` mở, `ci / test-reconstructed` **pass**.
- [ ] Bump con trỏ `evalhub` ở kit — **chờ `evalhub#30` có 1 approval**.
- [ ] `apps/studio#20` — **chờ chữ của AIE-1** cho 2 field `Settings`, và chờ bước bump ở trên.
- [ ] Bump con trỏ `apps/studio` lần cuối.

---

## §7 · Ranh giới + ước lượng

**Không làm hôm nay, và mỗi món có lý do:**

| Món | Vì sao không |
|---|---|
| Chặn trục `answer.refused` | `0/22`, và là quyết định mới chứ không phải bảo vệ quyết định có sẵn (`DEC-D23-01`) |
| Lock cho cap/cache | `DEC-D23-02` ghi nhận; vá bằng lock là sửa `judge.py`, ngoài phạm vi cả DoD `app#20` lẫn câu AIE-1 cho |
| Cho judge xem `events` | Đổi chữ ký `judge()`; và nếu judge phán được về trace thì `DEC-05` mới là thứ phải bàn lại, không phải cổng này |
| `agreement` cho case đã qua judge | `CaseResult.judge` vẫn `None` — `Judge` đòi `agreement: float`, mà `judge()` không nhận nhãn tay (`DEC-02`, `DEC-D18-04`) |
| Nới nấc 1 (biến thể `expected`) | Giá trị thuộc DE (`DEC-Q5`); và `extra="forbid"` nên field phải land ở `GoldenCase` trước khi DE emit |

**Ước lượng đã tiêu:** T1–T3 xong (cổng + 3 bài + 4 mutant + 2 DEC + sổ). T4 chưa mở PR — chặn bởi
một dòng xác nhận và một bước bump con trỏ, cả hai không nằm trong tay quadrant này.
