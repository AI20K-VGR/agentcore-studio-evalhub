# Tự gieo mutant vào T3 — `render_run_cases` + `answer_from_trace`

**Ngày:** 2026-08-07 (D15) · **Người gieo:** AIE-2 (chủ quadrant tự gieo vào code của chính mình)
**Mục tiêu đo:** suite viết ở T3 có **răng** không, hay chỉ đang mô tả lại code.

> **Khai TRƯỚC khi chạy.** Bảng §1 dưới đây được viết và commit vào file này **trước** khi bất kỳ
> mutant nào được gieo. Không có bước này thì phép đo không có giả thuyết để bác bỏ: nhìn kết quả
> rồi mới nói *"đúng như tôi nghĩ"* là chấm điểm sau khi đã biết đáp án.

## Điều kiện của một mutant hợp lệ

1. Nó là một **failure mode có ý nghĩa** — một cách hàm này có thể sai thật trong đời thật, không
   phải đổi tên biến.
2. Nó được khai **trước**, kèm **bài cụ thể được kỳ vọng sẽ đỏ**. Một mutant không nêu được bài nào
   phải đỏ thì chưa đủ điều kiện gieo.
3. Nó gieo được **sạch** — không `SyntaxError`, không `ImportError`, không lỗi thu thập test.
   **Collection failure KHÔNG BAO GIỜ tính là `caught`**, kể cả khi pytest báo đỏ và kể cả khi đỏ
   đúng số bài mong đợi. Đã trả giá một lần ở `into-engine-d11.md` M5 lượt 1 (comment `# MUTANT M5`
   chèn giữa dict literal ⇒ 13 collection error, phải gieo lại).

**Mutant tương đương và mutant không liên quan được PHÂN LOẠI, không tính vào số.** Không cố đủ một
con số bằng mutation vô nghĩa: 5 là sàn cho *nỗ lực tìm failure mode*, không phải sàn cho *số dòng
trong bảng*.

## Bẫy đo, đã trả giá ở lượt trước

| bẫy | vì sao | cách tránh |
|---|---|---|
| ANSI màu | regex `FAILED` khớp rỗng trên chuỗi có escape code | `--color=no` **và** đọc exit code |
| `.pyc` cũ | bytecode cache khoá theo `(mtime giây, size)` — sửa trong cùng giây, cùng độ dài ⇒ chạy code cũ | `PYTHONDONTWRITEBYTECODE=1` |

---

## §1 · Khai trước — `mutant → bài phải đỏ`

Baseline trước khi gieo: `69 passed, 1 skipped, 2 xfailed, 0 XPASS`.

| ID | Gieo vào | Mutation | Failure mode thật nó mô phỏng | **Khai: bài phải ĐỎ** |
|---|---|---|---|---|
| **M1** | `render.py` `render_run_cases` | dòng đếm success in `f"{n}/{k}"` thay `f"{k}/{n}"` | hoán vị tử/mẫu — `1/5` đọc thành `5/1`, một run trượt gần hết trông như vượt chỉ tiêu | `test_render_case_in_k_tren_n_tho_KHONG_in_ty_le_tong` |
| **M2** | `render.py` `render_run_cases` | bỏ nhánh `expects_refusal`, cột citation luôn in `f"{r.citation_accuracy:.2f}"` | mất `DEC-D12-01`: dòng từ-chối in `1.00`, con số đẹp nhất bảng nằm trên một dòng chưa đo gì | `test_render_case_tu_choi_in_n_a_chu_khong_in_1_00` |
| **M3** | `render.py` `render_run_cases` | `n_citation = len(results)` thay `len(answerable)` | gộp refusal vào mẫu số citation — vi phạm `DEC-S2-134-03`, đúng lỗi `kit#134` mô tả | `test_render_case_mau_so_citation_loai_refusal_chu_khong_dung_tong_case` · `test_render_case_in_k_tren_n_tho_KHONG_in_ty_le_tong` |
| **M4** | `render.py` `_count_or_not_estimable` | bỏ nhánh `n == 0`, luôn trả `f"{k}/{n}"` | `n=0` in `0/0` — mời người đọc chia một phép chia không tồn tại | `test_render_case_rong_la_not_estimable_KHONG_in_0_phan_tram` · `test_render_case_toan_refusal_thi_citation_la_not_estimable` |
| **M5** | `render.py` `render_run_cases` | `k_citation` đếm `>= 0.5` thay `== 1.0` | nới định nghĩa *"trích đủ citation"* — case đạt một nửa được đếm là đạt, tử số phồng im lặng | `test_render_case_in_k_tren_n_tho_KHONG_in_ty_le_tong` |
| **M6** | `run_report.py` `answer_from_trace` | nhiều `llm-step` ⇒ lấy `llm_steps[0]` thay vì raise | chấm nhầm bước trong recipe nhiều bước LLM — bảng điểm trông đúng mà đo sai đối tượng | `test_answer_from_trace_nhieu_llm_step_thi_raise_chu_khong_chon_bua` |
| **M7** | `run_report.py` `answer_from_trace` | thiếu `llm-step` ⇒ trả `AgentAnswer(answer="", ...)` thay vì raise | run **không đọc được** bị đếm vào mẫu số như một run đã đo và trượt | `test_answer_from_trace_thieu_llm_step_thi_raise_chu_khong_tra_chuoi_rong` |
| **M8** | `render.py` `render_run_cases` | gọi `compute_scorecard(...)` trong thân hàm | kéo mốc D16 lên sớm ⇒ `test_gate_blocks_on_fail` (`xfail(strict=True)`) XPASS ⇒ FAIL | `test_render_case_KHONG_goi_compute_scorecard` |

**8 mutant, không phải 5.** Con số không phải mục tiêu — 8 là số failure mode có ý nghĩa tìm được
mà gieo sạch được. Mutant từng cân nhắc rồi **bỏ**, ghi ở §3.

---

## §2 · Kết quả thực đo

Baseline: `69 passed, 1 skipped, 2 xfailed, 0 XPASS`, exit `0`.
Mọi lượt: `--color=no`, đọc exit code, `PYTHONDONTWRITEBYTECODE=1`. **0 collection error** ở cả 9 lượt.

| ID | exit | khai: bài phải đỏ | thực: bài đỏ | khớp? |
|---|---|---|---|---|
| M1 | 1 | `..._in_k_tren_n_tho_...` | `..._in_k_tren_n_tho_...` · `..._toan_refusal_...` | **lệch — rộng hơn khai** |
| M2 | 1 | `..._tu_choi_in_n_a_...` | `..._tu_choi_in_n_a_...` | ✅ đúng y |
| M3 | 1 | `..._mau_so_citation_loai_refusal...` · `..._in_k_tren_n_tho_...` | thêm `..._toan_refusal_...` | **lệch — rộng hơn khai** |
| M4 | 1 | `..._rong_la_not_estimable...` · `..._toan_refusal_...` | y hệt | ✅ đúng y |
| M5 | 1 | `..._in_k_tren_n_tho_...` | y hệt | ✅ đúng y |
| M6 | 1 | `..._nhieu_llm_step_thi_raise...` | y hệt | ✅ đúng y |
| M7 | 1 | `..._thieu_llm_step_thi_raise...` | y hệt | ✅ đúng y |
| M8 | 1 | `..._KHONG_goi_compute_scorecard` | **11 bài** | **lệch — rộng hơn khai rất nhiều** |
| **M9** | **0** | **khai: KHÔNG bài nào đỏ (dự đoán SỐNG SÓT)** | **không bài nào đỏ** | ✅ dự đoán đúng — và đây là finding |

**8 bắt · 1 sống sót đúng như dự đoán · 0 tương đương bị đếm nhầm · 0 collection error.**

### §2.1 · M9 — mutant sống sót, và vì sao nó là kết quả có giá trị nhất của lượt này

Một sweep 8/8 do **chính người viết test** gieo thì đo được rất ít: nó chỉ chứng minh *"những bất
biến tôi nghĩ ra đều được cưỡng chế"*, không chứng minh *"hàm này đúng"*. Nên M9 được thêm với một
giả thuyết ngược hẳn — **khai trước là nó sẽ SỐNG**:

```python
# gốc
return score_case(case, answer_from_trace(events), citations_from_trace(events))
# M9
return score_case(case, answer_from_trace(events), answer_from_trace(events).citations)
```

Tức chấm bằng citation **agent tự khai** thay vì citation quan sát được từ trace. Kết quả: `69
passed`, exit `0` — **không một bài nào đỏ**.

Đây là một lỗ thật, không phải một mutant giả:

- Nó là **đúng thứ D5 (`#24`) cấm**. `AgentAnswer.citations` là *cái LLM nói nó đã trích*; trace là
  *mặt quan sát thật*. `harness.py:163` ghi thẳng: *"KHÔNG dùng `answer.citations` (agent tự khai)"*.
- Hệ quả nếu land: một agent **bịa** citation sẽ tự chấm cho mình `citation_accuracy` tuyệt đối, và
  bảng điểm không có cách nào biết.
- Nguyên nhân lộ ra ngay khi hỏi đúng câu: `score_run_from_trace` **chưa có một bài test nào gọi
  tới nó**. Suite T3 khoá rất kỹ hai đầu (`answer_from_trace` 7 bài · `render_run_cases` 12 bài) mà
  bỏ trống đúng chỗ hai đầu **nối vào nhau**.

**Đã vá trong cùng ngày**, hai bài mới ở `tests/test_answer_from_trace.py`:

| bài | khoá gì |
|---|---|
| `test_score_run_from_trace_cham_bang_citation_TRACE_chu_khong_bang_agent_TU_KHAI` | fixture bất đối xứng **theo nguồn**: trace mang chunk ĐÚNG, lời tự khai mang chunk SAI ⇒ hai nguồn cho hai kết quả khác nhau, bài phân biệt được |
| `test_score_run_from_trace_khong_doc_gi_ngoai_events` | negative control: cùng `case`, cùng `answer`, chỉ đổi citation **trong trace** ⇒ điểm phải đổi. Bản thu nhỏ của phép so mà `test_spine_scored_from_postgres.py` (D7) chạy trên DB thật |

Gieo lại M9 sau khi vá: **2 bài đỏ**, exit `1`. Suite sau khi vá: `71 passed, 1 skipped, 2 xfailed`.

### §2.2 · M8 — bắt được, nhưng bắt bằng một cơ chế có hạn sử dụng

Khai 1 bài đỏ, thực tế **11 bài** đỏ. Lý do lệch không phải suite mạnh hơn dự kiến, mà là:
`compute_scorecard` hiện `raise NotImplementedError`, nên mọi bài gọi `render_run_cases` đều vỡ theo
dây chuyền. Bài được khai (`test_render_case_KHONG_goi_compute_scorecard`) **có** đỏ, nên M8 tính là
`caught` — nhưng cơ chế bắt thật sự là *"nó raise"*, không phải *"suite phát hiện render đã gọi sang
tầng tính"*.

⇒ **Finding có hạn: D16.** Khi `kit#108` hiện thực `compute_scorecard`, nó thôi raise, và lúc đó
**không còn bài nào** chứng minh `render_run_cases` không gọi sang tầng tính. Bất biến *"render
không tự tính"* phải được khoá lại bằng một cơ chế không dựa vào exception — ví dụ
`monkeypatch`/spy đếm số lần gọi. Ghi vào việc D16, chủ AIE-2.

Đây đúng loại thứ mà `into-engine-d11.md` gọi là *"dòng lệch declared-vs-actual mới là finding"* —
M3 ở lượt đó khai ĐỎ mà ra XANH 30/30 và lộ ra `clamp ts` không có lưới. Lần này lệch theo chiều
ngược nhưng cùng bản chất: **con số `caught` che mất câu hỏi *bắt bằng cái gì***.

### §2.3 · M1 và M3 — lệch nhẹ, rộng hơn khai

Cả hai đỏ thêm `test_render_case_toan_refusal_thi_citation_la_not_estimable` ngoài dự kiến.

- **M1** (hoán `k`/`n`): với fixture toàn-refusal, `1/2` thành `2/1` ⇒ bài đó cũng bắt được.
- **M3** (mẫu số citation dùng `len(results)`): với fixture toàn-refusal, `n_citation` thành `2` thay
  vì `0`, nên hàm in `0/2` thay vì `not-estimable` ⇒ bài đó cũng bắt được.

Không phải lỗi, nhưng ghi lại vì nó sửa mô hình trong đầu người viết: bài `toan_refusal` hoá ra là
một bài **đa mục đích** — nó khoá cả nhánh `n=0` từng phần lẫn tính đúng của hai mẫu số. Chỗ đó là
chỗ mạnh nhất của suite hiện tại, không phải bài phụ như tên gọi gợi ý.

### §2.4 · Ghi chú trung thực về cách gieo M8

M8 **không gieo được bằng một dòng**: thêm lời gọi `compute_scorecard(...)` mà không thêm import sẽ
cho `NameError`, tức mutant chết vì lý do sai (lỗi tên, không phải hành vi). Nên lượt này thêm **hai**
chỗ cùng lúc — dòng import và lời gọi — để mutant đúng nghĩa *"render gọi sang tầng tính"*. Khai ra
đây vì một mutant cần hai chỗ sửa thì không còn là mutation một-điểm, và người đọc có quyền biết.

---

## §3 · Mutant đã cân nhắc rồi bỏ — phân loại, KHÔNG tính vào số

| ứng viên | phân loại | vì sao không đếm |
|---|---|---|
| `if not events:` → `if len(events) == 0:` trong `answer_from_trace` | **equivalent** | `events: list` ⇒ hai vế đồng nhất trên mọi giá trị dựng được. Không chứng minh gì về suite |
| `e.node_type is NodeType.LLM_STEP` → `== NodeType.LLM_STEP` | **equivalent** | `NodeType` là enum, `is` và `==` trùng nhau trên mọi thành viên |
| đổi độ rộng cột (`:<20` → `:<24`) | **irrelevant** | không phải failure mode — không có cách nào một bảng lệch 4 ký tự làm ai đọc sai một con số |
| đổi thứ tự hai dòng metadata `golden_set_ref`/`trace_source` | **irrelevant** | cùng lý do |
| **R5** — `cost=float(row[10])` → `cost=row[10]` (lượt hai, §5) | **equivalent** — *xếp vào đây SAU khi gieo, không phải trước* | Gieo rồi mới biết: pydantic lax mode ép `Decimal → float` nên hành vi không đổi. Đây là lần duy nhất một mutant được reclassify **sau** khi chạy — ghi ra vì phân loại sau khi biết kết quả là chỗ dễ tự lừa nhất, và cách chống là nói thẳng nó xảy ra. Chi tiết + finding về docstring: §5.2 |

Cùng luật đã áp ở `into-engine-d11.md`: `refused is False` → `not refused` được ghi là `equivalent`,
không đếm là *"sống sót"* mà cũng không đếm là *"bắt được"*. Và cùng luật mà DE đã chốt cho
collection error: một sweep báo *"bắt được 13"* bằng `SyntaxError` là một sweep nói dối.

**Không cố đủ một con số bằng mutation vô nghĩa.** Bốn dòng trên nếu đem gieo sẽ nâng "số mutant" lên
13 mà không thêm một bit thông tin nào về chất lượng suite.

---

## §4 · Phản hồi của chủ quadrant

Lượt này chủ quadrant **tự gieo vào code của chính mình**, nên mục này trùng người gieo — đó chính là
giới hạn của phép đo và nó phải được nói ra: một sweep tự gieo chỉ đo được *"những bất biến tôi nghĩ
ra đều được cưỡng chế"*. M9 tồn tại chính là để chống lại điểm mù đó, và nó đã tìm thấy một lỗ thật —
nhưng một M9 do người khác nghĩ ra sẽ nhắm vào chỗ mà người viết **không** nghĩ tới được.

⇒ Vế *"the owner has to show their tests catch them"* của `kit#74` vẫn **chưa xảy ra** với quadrant
AIE-2: chưa ai ngoài AIE-2 gieo vào `evalhub`. Đã xin ở T7 (`#103`), ưu tiên trước **D18** để còn kịp
vá. Khi có người gieo, mục này append bằng commit của chính người đó — *"Both of you write down what
happened"*.

---

## §5 · Lượt hai — gieo vào `_row_to_event` (tầng đọc DB)

**Khai TRƯỚC khi gieo**, commit riêng, cùng luật §1. Append sau §4 vì đây là lượt sau, không phải
sửa lại lượt trước.

Lý do có lượt này: lượt đầu chỉ chạm `render_run_cases` và `answer_from_trace`. Cả hai nhận
`TraceEvent` **đã dựng sẵn**, nên đoạn `list[tuple]` của psycopg → `list[TraceEvent]` chưa từng bị
đo. Đó lại đúng là đoạn hỏng **im lặng** nhất của `run_report.py`: `_row_to_event` đọc theo chỉ số,
thứ tự chỉ số do chuỗi `_READ_RUN` quyết, hai chỗ cách nhau 30 dòng và không có gì buộc chúng khớp.
Con số `9 mutant` của lượt đầu che mất đúng câu hỏi *gieo vào đâu* — cùng bài học `M8` đã dạy về
`caught`.

Baseline trước khi gieo: `76 passed, 1 skipped, 2 xfailed, 0 XPASS`.

| ID | Mutation | Failure mode thật nó mô phỏng | **Khai: bài phải ĐỎ** |
|---|---|---|---|
| **R1** | hoán `event_id=row[0]` ↔ `run_id=row[1]` trong `_row_to_event` | hoán hai cột **cùng kiểu `str`** — pydantic không kêu, bảng vẫn in, chỉ mọi `run_id` từ đó trỏ nhầm | `test_row_to_event_khop_thu_tu_cot_cua_READ_RUN` |
| **R2** | hoán thứ tự hai cột **trong chuỗi `_READ_RUN`**, KHÔNG đụng hàm | drift một phía: ai sửa SQL mà quên hàm. Đây là chiều mà một bảng giá trị chép tay **không** bắt được | `test_row_to_event_khop_thu_tu_cot_cua_READ_RUN` |
| **R3** | `citations=row[11]` → `citations=row[11] or []` | biến *"không áp dụng"* thành *"đã trích, rỗng"* ngay tầng đọc — xoá một dấu hiệu chất lượng trước khi bộ chấm kịp nhìn thấy | `test_row_to_event_citations_NULL_giu_None_chu_khong_thanh_list_rong` |
| **R4** | dựng `Tokens(prompt=row[9]["completion"], completion=row[9]["prompt"])` | hoán vai hai số token — đúng lỗi vừa bắt được khi review `kb#16` (F3), lần này ở tầng đọc; D19 (`kit#120`) dựng cost-lineage trên chính hai số này | `test_row_to_event_tokens_khong_hoan_prompt_va_completion` |
| **R5** | bỏ `float(...)`, để nguyên `Decimal` | — | **khai: SỐNG SÓT.** `TraceEvent.cost: float` + pydantic lax mode sẽ tự ép `Decimal → float`, nên `isinstance(cost, float)` vẫn đúng. Gieo để đo xem `float()` kia là **bất biến được cưỡng chế** hay chỉ là **lời khai trong docstring** |

R5 khai ngược có chủ ý, cùng vai với `M9` ở lượt đầu: một sweep mà mọi mutant đều chết chỉ chứng
minh *"những bất biến tôi nghĩ ra đều được cưỡng chế"*. Con được khai là sẽ sống mới nói được điều
khác về suite.

### §5.1 · Kết quả thực đo

Baseline `76 passed, 1 skipped, 2 xfailed`, exit `0`. Mọi lượt `--color=no` + đọc exit code +
`PYTHONDONTWRITEBYTECODE=1`. **0 collection error** ở cả 5 lượt. File gốc khôi phục nguyên vẹn sau
mỗi lượt (có assert).

| ID | exit | khai | thực | khớp? |
|---|---|---|---|---|
| R1 | 1 | `..._khop_thu_tu_cot_...` | y hệt, 1 bài | ✅ đúng y |
| R2 | 1 | `..._khop_thu_tu_cot_...` | **5 bài** — cả nhóm | **lệch — rộng hơn khai** |
| R3 | 1 | `..._citations_NULL_giu_None...` | y hệt, 1 bài | ✅ đúng y |
| R4 | 1 | `..._tokens_khong_hoan_...` | y hệt, 1 bài | ✅ đúng y |
| **R5** | **0** | **khai: SỐNG SÓT** | **sống sót** | ✅ dự đoán đúng — và dẫn tới một reclassify |

**4 bắt · 1 sống sót đúng dự đoán · 0 collection error.**

### §5.2 · R5 sống sót, nhưng nó là **equivalent** — không phải một lỗ

Đây là chỗ con số dễ nói dối theo chiều ngược với `M9`. `M9` sống sót **và** là lỗ thật. R5 sống sót
**và không phải lỗ** — vì bỏ `float(...)` đi thì hành vi **không đổi chút nào**:

```python
cost=float(row[10])   # gốc
cost=row[10]          # R5 — Decimal("0.25")
```

`TraceEvent.cost: float`, `model_config` **không** bật strict ⇒ pydantic lax mode tự ép
`Decimal → float`. Bằng chứng không phải suy luận: dưới R5, chính bài
`test_row_to_event_cost_Decimal_thanh_float` — bài **assert `isinstance(event.cost, float)`** — vẫn
**XANH**. Tức cái đang cưỡng chế bất biến đó là **pydantic**, không phải dòng `float()` của bộ chấm.

⇒ Xếp R5 vào §3 (**equivalent**), **không** đếm là *"1 lỗ sống sót"*. Đếm nó sẽ là thổi phồng đúng
kiểu mà `M8` đã cảnh báo theo chiều ngược: con số che mất câu hỏi *nó nói lên cái gì*.

**Nhưng lượt gieo vẫn ra một finding thật, chỉ là finding về DOC chứ không về code.** Docstring
`_row_to_event` viết *"`cost` là `NUMERIC` ⇒ psycopg trả `Decimal`, ép `float` để khớp contract"* —
câu đó làm người đọc tưởng lời gọi `float()` là thứ **giữ** bất biến. Nó không giữ; pydantic giữ.
Một người sau này dọn code, thấy `float()` "thừa", xoá đi — suite vẫn xanh, và họ sẽ kết luận là
mình vừa xoá đúng. Họ đúng **hôm nay**, và sai vào ngày ai đó bật `strict=True` trên `TraceEvent`.

**Xử:** giữ lời gọi `float()` (rẻ, và là lưới cho ngày strict mode), sửa docstring để nói đúng nó là
lớp phòng hờ **trùng** với pydantic chứ không phải lớp duy nhất. Không thêm test — một bài cố khoá
`float()` sẽ thực chất đang khoá hành vi coercion của pydantic, tức đo thư viện của người khác.

### §5.3 · R2 — bắt được, nhưng rộng hơn khai

Khai 1 bài, thực tế **5 bài** — cả nhóm `test_row_to_event.py`. Lý do: helper `_row()` dựng row theo
`_columns()` đọc từ chính `_READ_RUN`, nên đảo thứ tự cột trong SQL làm **mọi** fixture xê dịch cùng
lúc, không riêng bài đối chiếu.

Không phải lỗi, nhưng ghi vì nó sửa mô hình trong đầu người viết: bất biến *"hai phía phải khớp"*
hoá ra được cưỡng chế bởi **cách dựng fixture**, không phải bởi một assert cụ thể nào. Đó là lưới
rộng hơn dự kiến — nhưng cũng nghĩa là khi nó đỏ, 5 dòng đỏ **không** chỉ ra được phía nào đã drift.
Ai gặp nó đọc §5 này trước, đừng đi tìm 5 lỗi.
