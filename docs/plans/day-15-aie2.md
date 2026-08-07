# Plan Day 15 — AIE-2 · Scorecard skeleton đọc trace run thật + playground-trace ghép viewer · Thứ Sáu 07/08/2026

> **Viết tối D14 (06/08), trước khi ngày bắt đầu** — khác D12 (viết 16:30 khi ngày đã trôi một nửa).
> Lý do: D15 là **Integration Friday** và D16 (thứ Bảy 08/08) là ngày nặng nhất Sprint 2
> (`kit#108` eval harness v1). Không còn chỗ cho một ngày trôi rồi mới lập kế hoạch.

# Executive Summary

**Goal.** Đóng đúng hai động từ 🎯 của `#103` — *"Scorecard skeleton đọc trace của run thật"* và
*"playground-trace UX ghép vào viewer"* — bằng code chạy được trong `packages/evalhub`, **không**
kéo `compute_scorecard` (D16) lên sớm và **không** đụng quadrant người khác.

**Vì sao ngày này không được là ngày evidence thứ ba liên tiếp.** D12 render skeleton, D13 zero-code,
D14 zero-code. `O3.1` (deliverable completeness, `w=0.1275`, ô nặng nhất) đứng yên ba ngày, và ba
seam `EvalHarness.run` / `compute_scorecard` / `LLMJudge.judge` vẫn `NotImplementedError` y như cuối
S1. Lập luận từng ngày đều đúng, nhưng cộng lại thì toàn bộ `O3.1` dồn vào D16 — mà D16 còn phụ
thuộc golden-30 của DE (ETA 08/08). D15 phải trả lại một phần nợ đó.

**Nền đã xác nhận trước khi lập kế hoạch** (không giả định):

| | |
|---|---|
| Pointer `kit@2809cbb` | **8/8 submodule khớp `origin/main`** — không cần bump |
| `packages/evalhub` | `a60855d` · `50 passed, 1 skipped, 2 xfailed`, 0 XPASS |
| Đề bài `week-2/days/day-15.md` | **404 — ngày thứ năm liên tiếp.** API `contents` chỉ có `00-orientation · README.md · nda-denylist.sh · week-1`. Body `#103` là spec thẩm quyền, mục này **đóng**, không hỏi ai |

---

# §0 — Đọc scope: hai động từ, và không ô DoD nào là của AIE-2

`#103` có 3 ô DoD, cả 3 là **DoD chung của `#104`**, không ô nào thuộc AIE-2:

| Ô DoD trên `#103` | Chủ thật |
|---|---|
| Trace viewer render timeline+tokens+cost+citations | `#100` — DE |
| tenant filter tại retrieve 0-leak (đầu) | `#100` — DE |
| Integration Friday 4-mảng recording | `#104` — cả nhóm |

Việc AIE-2 nằm ở dòng 🎯, đúng **hai động từ**. Đây là lần thứ tư liên tiếp mô hình này lặp lại
(D12 → D13 → D14 → D15), nên áp thẳng bài học: **không tick ô nào của người khác**, đọc dòng 🎯 làm
scope thật.

Bản đồ Integration Friday để biết mình phụ thuộc ai:

```
#101 AIE-1  6 executor chạy batch thật, emit trace đúng schema + citations từ kb-retrieve
   └─► #100 DE     trace viewer (timeline · tokens · cost · citations) + tenant filter tại retrieve
          └─► #102 SWE   playground: bấm Test → interpreter chạy → viewer hiện; run_id/agent_id khớp
                 └─► #103 AIE-2  bộ chấm đọc trace của CHÍNH run đó + đối chiếu wireframe D12
```

AIE-2 nằm **cuối chuỗi** ⇒ rủi ro lịch cao nhất. Giảm rủi ro bằng DEC-D15-01 dưới đây: deliverable
không chờ ai.

## Dependency/blocker rule

Luật vận hành cho chuỗi phụ thuộc ở trên, áp cho **mọi** input đến từ người khác trong ngày:

> Khi gặp input/dependency từ người khác, **KHÔNG tự đoán hoặc giả định**. Xác định chính xác phần
> nào bị block; **tiếp tục thực hiện các phần độc lập còn lại**. Chỉ **DỪNG** khi đã đến bước thực
> sự cần input đó. Khi DỪNG, báo rõ:
>
> ```
> cần ai → cần gì → vì sao → phần nào đã hoàn tất → phần nào đang block → owner + ETA nếu biết
> ```
>
> Khi input về thì **tiếp tục từ đúng checkpoint**, không chạy lại phần không cần thiết.

Sáu trường của dòng báo DỪNG là cùng bộ trường mà T8 đòi khi trạng thái ngày là `BLOCKED` — báo
trong ngày và báo lúc đóng ngày dùng chung một dạng, không phải viết lại hai lần.

---

# §1 — Quyết định phải chốt hôm nay

Mỗi quyết định kèm **phương án bỏ** và **lý do bỏ** — từ S2 mentor không trả lời câu hỏi kiến trúc,
nên lý do bỏ là thứ duy nhất chứng minh đã cân.

## DEC-D15-01 · "Đọc trace của run thật" hiện thực ở đâu

**Chọn:** thêm đường render **per-case từ trace thật** trong `packages/evalhub` — nhận
`list[SmokeResult]` + metadata run (`run_id`, `golden_set_ref`, nguồn trace), in bảng từng case với
số **thật**, thay vì `todo:`.

**Ràng buộc cứng đã kiểm:** `.importlinter` xếp 4 quadrant là **sibling** ⇒ `studio_evalhub`
**KHÔNG** import được `studio_kb`, nên `PgTraceReader` nằm ngoài tầm với. Điều này **không phải
blocker**: evalhub đã dependency-inverted sẵn — `citations_from_trace(events)` và
`score_case(..., retrieved_citations=...)` nhận dữ liệu từ caller.

**Tiền lệ có sẵn, không phát minh lại:** `apps/studio/tests/test_spine_scored_from_postgres.py` (D7)
đã nối `PgTraceReader → CaseRun → score_case` tại composition root và tự ghi rõ lý do phải nằm ở đó.
D15 nối tiếp **vế còn thiếu**: `SmokeResult[] → render`.

**Bỏ 1:** gọi `compute_scorecard` hôm nay. Bỏ vì nó là mốc D16 (`kit#108`), và land sớm làm
`test_gate_blocks_on_fail` (`xfail(strict=True)`) **XPASS ⇒ FAIL** — đúng lý do đã ghi ở
`render.py:6-9`, không phải lý do mới nghĩ ra.

**Bỏ 2:** import `studio_kb` vào evalhub cho tiện. Bỏ vì vỡ layering contract, và `make lint` bắt
ngay — nhưng quan trọng hơn: nó xoá đúng ranh giới ownership mà cả Sprint 2 đang được chấm.

**Bỏ 3:** để toàn bộ wiring ở `apps/studio`. Bỏ vì `apps/studio` CODEOWNERS = **mentor** (GITFLOWS
§2); một PR mở chiều thứ Sáu có thể kẹt qua cuối tuần, mà D16 là thứ Bảy. Deliverable phải nằm
trong repo mình own.

## DEC-D15-02 · D15 in `k/n` thô, KHÔNG in tỷ lệ tổng

**Chọn:** bảng per-case + đếm thô dạng `k/n`, kèm nhãn *"fixed-set, chưa phải population estimate"*.

**Bỏ:** in `success_rate` / `citation_accuracy` tổng ngay khi có số thật. Bỏ vì hai lý do đã chốt:

- `DEC-S2-134-03` — citation denominator phải tách `k_citation / n_citation_scored` và loại refusal;
  hôm nay `Aggregate` chưa có chỗ cho `n_scored_citation` (nợ có chủ, hạn D16, `DEC-04`).
- In một tỷ lệ tổng khi chưa tách mẫu số là **đúng lỗi `kit#134` mô tả**: chỗ hỏng không nằm ở
  probe, nằm ở bước từ `8/10` sang `"80%"`.

Cùng họ với `DEC-D12-02` (*ô chưa đo được in `todo:`, không in `0.00`*): một con số đọc-được-thành-
đã-đo mà chưa đo đúng cách thì tệ hơn một ô trống.

## DEC-D15-03 · "Ghép vào viewer" = đối chiếu, không phải dựng UI

**Chọn:** đối chiếu wireframe D12 (`docs/design-notes/playground-trace-ux-d12.md`) với viewer thật
của DE (`#100`), ra **danh sách lệch**: field bộ chấm cần mà viewer chưa hiện, và field viewer hiện
mà bộ chấm không dùng.

**Bỏ:** tự dựng UI. Bỏ vì viewer là `#100` (DE), playground là `#102` (SWE) — cùng lý do đã áp ở D12
khi wireframe được khai là **ĐỀ NGHỊ, không phải spec**. Vào code người khác giữa Integration Friday
là cách nhanh nhất để vỡ ngày của ba người.

## DEC-D15-04 · Không tick ô DoD nào trên `#103`

Xem §0. Ghi rõ trong comment đóng ngày để người đọc không tưởng AIE-2 bỏ sót.

---

# §2 — Work items

Thứ tự cố ý: T1–T2 là nợ luật S2 phải trả trước khi làm việc mới, vì chúng rẻ và chúng đang **trừ
điểm mỗi ngày để đó**.

## T1 · Vá hai link chết của D14 — **P0, làm đầu tiên**

Luật `kit#74`: *"Closing an issue whose artifact I cannot find in a fresh clone counts against you,
not for you."* Hiện có đúng hai chỗ vi phạm, đã xác minh bằng API:

| Chỗ | Trạng thái | Vá |
|---|---|---|
| Comment đóng `#98` trỏ `evalhub/blob/main/docs/plans/day-14-aie2.md` | **404 trên GitHub, nhưng file CÓ THẬT trên đĩa** (418 dòng). Nguyên nhân: `.gitignore:16` = `docs/plans/*` với allowlist chỉ có `day-11`/`day-12` ⇒ D13 (376 dòng) và D14 (418 dòng) **bị nuốt im lặng**, không bao giờ vào git | Sửa `.gitignore`: thêm `!docs/plans/day-13-aie2.md`, `!day-14`, `!day-15` — hoặc đảo luật thành allowlist rõ ràng. **Một dòng, không phải viết lại plan** |
| Daily note D14 trỏ `../../../.local-reviews/day14/B7-evidence.md` | `.local-reviews/` nằm trong `.git/info/exclude` — **vô hình với mọi clone**, kể cả của đồng đội | Publish B1–B7 vào `evalhub/docs/evidence/day14/` **hoặc** bỏ link và dán số thẳng vào note |

**Bài học chung của hai dòng trên:** cả hai đều là *"artifact có thật, đường dẫn không tồn tại với
người đọc"*. Cùng một lớp lỗi, hai cơ chế khác nhau (`.gitignore` allowlist quên cập nhật ·
`.git/info/exclude` cấp máy). Sau khi vá, thêm một bước vào checklist đóng ngày: **mọi link trong
comment đóng issue phải kiểm bằng `gh api`, không bằng mắt.**

Đây là ô `O3.3` — đúng ô đã lấy mất band A ở S1 vì ba lỗi filing, và đúng ô đã được kéo lên A ở bản
re-score. Để nó tái phát là mất đúng thứ vừa lấy lại được.

## T2 · Comment kế hoạch lên `#103` đầu ngày

Nêu: hai động từ 🎯 · 3 ô DoD là của `#104` nên không tick · phụ thuộc `#101`→`#100`→`#102` ·
deliverable không chờ ai (DEC-D15-01). Giữ thói quen D12: kế hoạch lên issue **trước**, không phải
báo cáo sau.

## T3 · Deliverable 1 — render per-case từ trace run thật

Trong `packages/evalhub/src/studio_evalhub/render.py`:

- hàm mới nhận `list[SmokeResult]` + metadata run, in bảng: `case_id · expects_refusal · success ·
  citation_accuracy` (refusal in `n/a` theo `DEC-D12-01`) + dòng đếm `k/n` thô;
- **giữ nguyên** `render_scorecard` hiện có — không đổi chữ ký, 16 test `test_render.py` phải xanh
  không sửa;
- nguồn `SmokeResult` là `score_case` chạy trên `citations_from_trace(events)` của một run thật.

Chứng minh "run thật" bằng một trong hai đường, **ưu tiên đường 1 vì không chờ ai**:

1. trace đã bền hoá trong Postgres từ D14 (`PgTraceWriter → obs.trace_events`), đọc lại tại
   composition root như `test_spine_scored_from_postgres.py` đã làm;
2. run live của `#101` nếu AIE-1 land kịp trong ngày.

**Định nghĩa xong:** in được bảng có số thật của một `run_id` có thật, và người khác chạy lại lệnh
trong plan này ra đúng bảng đó.

### T3 · Quy trình viết — test trước, không phải code trước

T3 là hàm **chưa tồn tại**, nên đây là chỗ duy nhất trong ngày làm được đúng nghĩa test-trước
(T4 là siết test cho code đã có). Năm bước, không đảo thứ tự:

**Bước 1 · Viết test đỏ khi `render.py` chưa có một dòng nào.** Đặt tên theo house style đang có
trong `tests/test_render.py` — nói **bất biến**, không nói hành động:

```
test_render_case_in_so_that_cua_run_chu_khong_in_todo
test_render_case_tu_choi_in_n_a_chu_khong_in_1_00              ← nối DEC-D12-01
test_render_case_in_k_tren_n_tho_KHONG_in_ty_le_tong           ← DEC-D15-02
test_render_case_KHONG_goi_compute_scorecard                   ← nối test_render_scorecard_KHONG_goi_*
test_render_case_rong_la_not_estimable_KHONG_in_0_phan_tram    ← n=0, kit#134
test_render_case_khong_doi_gia_tri_tren_object                 ← nối test cùng tên của render_scorecard
test_render_scorecard_cu_khong_doi_hanh_vi                     ← pin 16 test cũ, chống hồi quy
```

**Bảy dòng trên là *candidate contract cases*, KHÔNG phải quota.** Chúng liệt kê các bất biến cần
được bảo vệ, không phải số bài phải đạt. Được phép **gộp** hai dòng vào một bài nếu một bài khoá
được cả hai bất biến, và được phép **bỏ** một dòng nếu protection đó đã có bài khác bao phủ — miễn
là ghi lại bất biến nào đi đâu. Điều **không** được làm: thêm bài chỉ để đủ bảy. Một suite phình ra
vì đếm là đúng thứ mentor đã nói không làm dịch điểm (*"Counting things never moves a grade by
itself"*); thứ tính điểm là **bất biến nào được cưỡng chế**, không phải số hàm `test_*`.

**Bước 2 · `ImportError` KHÔNG tính là đỏ hợp lệ.** Chạy lần đầu sẽ đỏ vì thiếu import — đó chưa
phải bằng chứng gì. Viết stub trả `""` để cái đỏ chuyển thành **semantic assertion**, rồi mới đi
tiếp. Đây là tiêu chí tự đặt ở S1 (*"failure phải là semantic assertion, không phải `ImportError`"*),
không phải luật mới.

**Bước 3 · Fixture phải phân biệt được thứ renderer chịu trách nhiệm — KHÔNG trộn renderer với
scorer.** T3 là hàm **hiển thị**, không phải hàm tính. Nên luật fixture ở đây là: mỗi giá trị mà
renderer chịu trách nhiệm in ra phải **khác nhau đủ để nhận ra khi bị hoán vị hay bị bóp về hằng**.
Cụ thể — `case_id` khác nhau, có **cả** case answerable **và** case refusal, `success` không đồng
loạt `True`, `citation_accuracy` không đồng loạt cùng một số, và `k ≠ n` ở dòng đếm. Fixture mà mọi
cột đọc giống nhau thì mutant hoán cột hay hardcode một giá trị vẫn xanh.

**H2 asymmetry (`|expected| ≠ |retrieved| ≠ |giao|`) chỉ áp khi fixture thật sự có citation metric
được tính** — đó là luật của **scorer**, thuộc T4. Ép nó vào fixture của renderer là áp một quy tắc
sai tầng: renderer nhận `citation_accuracy` như một số đã có sẵn trên `SmokeResult`, nó không tính
tử/mẫu nên không có gì để bất đối xứng.

**Bước 4 · Bất biến cưỡng chế bằng code (H5).** Test nào khai *"in đủ mọi ô"* thì lặp trên
`SmokeResult.model_fields`, **không** gõ tay danh sách. Đúng cái bẫy đã dính ở D12 khi thêm field
thứ 6.

**Bước 5 · Implement tới khi xanh.** Không thêm gì ngoài thứ test đòi.

**Không** áp property/metamorphic (H3) cho T3: renderer là hàm thuần chuỗi, quan hệ duy nhất có
nghĩa là *"số in ra khớp giá trị trên object"* — `test_render_khong_doi_gia_tri_tren_object_chi_doi_hien_thi`
đã khoá rồi, thêm nữa là test cho có. H3 để dành cho `compute_scorecard` ở D16, nơi nó giết cả **họ**
mutant mẫu số chứ không giết từng cá thể.

## T3b · Tự gieo mutant vào T3 — khai trước, và KHÔNG cắt khi hết giờ

Sau khi T3 xanh: khai bảng *mutant → bài phải đỏ* **trước** khi chạy, rồi gieo vào chính hàm vừa
viết. **Cố gắng tìm ≥5 failure mode/mutant có ý nghĩa; KHÔNG bắt buộc đủ 5 nếu không còn mutant hợp
lệ.** Gợi ý: hoán vị `k`/`n` · bỏ nhánh `expects_refusal` (in `1.00` thay `n/a`) · in `0.00` thay
`todo:` khi rỗng · off-by-one khi đếm · gọi `compute_scorecard`.

**Điều kiện của một mutant hợp lệ:** nó phải là một **failure mode có ý nghĩa** — một cách hàm này
có thể sai thật trong đời thật — và phải khai **trước** kèm **bài cụ thể được kỳ vọng sẽ đỏ**. Một
mutant không nêu được bài nào phải đỏ thì chưa đủ điều kiện gieo, vì lúc đó phép đo không có giả
thuyết để bác bỏ.

**Mutant tương đương và mutant không liên quan phải được PHÂN LOẠI, không được tính vào số.** Ví dụ
đã gặp: `refused is False` → `not refused` là **equivalent** (`refused: bool = False` trên model
frozen ⇒ hai vế đồng nhất trên mọi giá trị dựng được), nên nó không chứng minh gì về suite — ghi rõ
là `equivalent`, không đếm là "sống sót" mà cũng không đếm là "bắt được". Cùng luật với collection
error mà DE đã chốt: một sweep báo *"bắt được 13"* bằng `SyntaxError` là một sweep nói dối.

⇒ **Không cố đủ 5 bằng mutation vô nghĩa.** Bốn mutant có ý nghĩa kèm phân loại đầy đủ đáng giá hơn
bảy mutant trong đó ba cái là đổi tên biến. Con số 5 là sàn cho *nỗ lực tìm failure mode*, không
phải sàn cho *số dòng trong bảng*.

**Mutant không inject được thì BỎ, chọn failure mode khác — không cố cứu nó.** Nếu một mutant chỉ
gieo được bằng cách gây `SyntaxError`, `ImportError` hoặc lỗi thu thập test, thì nó không đo được
điều gì về suite: bài đỏ vì file không load nổi, không phải vì bất biến bị vi phạm. Ghi lại là đã
thử và bỏ, rồi chọn một failure mode khác gieo được sạch. **Collection failure KHÔNG BAO GIỜ tính là
`caught`** — kể cả khi pytest báo đỏ, kể cả khi đỏ đúng số bài mong đợi. Đã trả giá một lần ở M5
lượt 1 (comment `# MUTANT M5` chèn giữa dict literal ⇒ 13 collection error).

**Dòng lệch declared-vs-actual mới là finding**, không phải số bắt được — M3 khai ĐỎ ra XANH 30/30
chính là cách phát hiện `clamp ts` không có lưới. Bẫy phải tránh: `--color=no` **và** đọc exit code
(ANSI làm regex `FAILED` khớp rỗng); `PYTHONDONTWRITEBYTECODE=1` (`.pyc` khoá theo `(mtime giây,
size)`).

Ghi vào `docs/mutations/self-render-d15.md`. **Hết giờ thì cắt T5/T6, không cắt T3b** — nó là bước
duy nhất chứng minh bốn bước trên có tác dụng, và nó là artifact cho `S2.4` + nửa còn thiếu của cơ
chế mutation (§T7).

## T4 · Deliverable 2 — siết test trước khi bị gieo (H2 + H5)

Chuẩn bị cho mutation chéo, và nó cũng là lưới cho chính code T3:

- **H2 · fixture bất đối xứng.** Ép `|expected|`, `|retrieved|`, `|giao|` **đôi một khác nhau** trong
  **mọi fixture citation liên quan tới metric/property đang harden** — tức fixture nào thật sự nuôi
  phép tính `citation_accuracy`. Hiện `test_answerable_partial_citation_accuracy` là `2/1/1` — recall
  và count trùng nhau ở một nửa lớp mutant mẫu số.

  **KHÔNG** refactor fixture không liên quan chỉ để thoả một quy tắc hình thức: fixture của
  `test_contains_phrase_*` (đo token-matching), `test_tenant_scope.py` (đo nhất quán tenant) hay
  `test_render.py` (đo hiển thị) không tham gia phép tính mẫu số, nên đổi chúng là diff rác — làm
  review khó đọc và làm loãng đúng chỗ cần nhìn. Tiêu chí quyết định: *fixture này có đi vào biểu
  thức `len(expected & set(retrieved)) / len(expected)` không?* Không thì để nguyên.
- **H5 · bất biến cưỡng chế bằng code, không bằng lời.** Bài nào nói *"mọi/every X"* phải lặp trên
  nguồn programmatic. Đã làm đúng một lần ở D12 (`test_equality_actually_discriminates` →
  `SmokeResult.model_fields`); quét lại suite tìm chỗ còn khai bằng chữ.

Nền đo có sẵn: gieo thử 8 mutant vào `harness.py` cho **7 bắt · 1 tương đương · 0 sống sót thật**.
Suite hiện có răng; việc của T4 là chuyển từ *"bắt được mutant này"* sang *"mutant loại này không
sống được"*.

Hai bẫy DE đã trả giá, áp lại khi tự gieo: ANSI làm regex `FAILED` khớp rỗng (dùng `--color=no`
**và** đọc exit code), `.pyc` khoá theo `(mtime giây, size)` (`PYTHONDONTWRITEBYTECODE=1`).

## T5 · Deliverable 3 — đối chiếu wireframe D12 ↔ viewer thật của DE

Ra bảng lệch hai chiều, mỗi dòng trỏ **một field trace có thật hôm nay** (không field tưởng tượng —
cùng luật đã áp cho wireframe D12). Gửi DE dưới dạng **đề nghị**, không phải yêu cầu.

Neo đã có từ D14: retrieved chunks ở `TraceEvent.outputs["chunks"]` (`kb-retrieve`), grounded
citations ở `TraceEvent.citations` (`llm-step`), bốn key `chunk_id`/`section_role`/`tenant_id`/
`score` **đã freeze** (AIE-1 xác nhận D13), `refused` là carrier hợp lệ nhưng **semantic chưa
freeze** (Breakpoint #14) ⇒ chỉ dùng cho wiring/observability.

## T6 · Diễn tập fresh recursive clone — **Integration Friday là đúng ngày**

Luật `kit#74`: *"I clone your repo fresh and run your commands exactly as written. If it does not run
from a clean recursive clone, it does not count as delivered."* Chưa ai trong nhóm diễn tập việc này
trong cả Sprint 2.

```
git clone --recursive → make setup → docker compose -f docker-compose.test.yml up -d --wait
→ MỘT lệnh → ra bảng per-case của T3
```

Ghi runbook ngắn: DSN, fixture, env var, submodule SHA. Vấp ở D15 còn 5 ngày để sửa; vấp ở D20 là
mất trắng. Đây cũng là bằng chứng tốt nhất cho ô *"Integration Friday 4-mảng recording"* của `#104`
mà không cần tick hộ ai.

## T7 · Mutation chéo — đòi nốt nửa còn thiếu

Cơ chế `kit#74` yêu cầu **hai chiều**; hiện mới có một:

- **Đã gieo:** `docs/mutations/into-engine-d11.md` — 5 mutation vào engine, khai-trước, 2/5 lệch
  declared-vs-actual, tự khai cả lỗi người gieo (M5 lượt 1 `SyntaxError` ⇒ vô hiệu, đã gieo lại).
- **Thiếu 1:** mục `## Phản hồi của chủ quadrant` **vẫn trống sau 3 ngày** → nhắc
  @TranBaDat2607 append bằng commit của chính mình (*"Both of you write down what happened"*).
- **Thiếu 2:** **chưa ai gieo vào `evalhub`.** Quét cả 5 repo: chỉ evalhub có `docs/mutations/`.
  Nghĩa là vế *"the owner has to show their tests catch them"* chưa từng xảy ra với quadrant AIE-2.
  Xin một người gieo, ưu tiên trước D18 để còn kịp vá.

## T8 · Đóng ngày

Daily note same-day phải có đủ **ba** thứ, thiếu một là note không tính (`kit#74`: *"A daily note
with no number and no diagnosis does not count either"*):

1. **Số** — đo trong phiên, không chép từ ngày trước;
2. **Chẩn đoán** — số đó nghĩa là gì, và vì sao nó khác con số hôm qua;
3. **Trạng thái ngày: `READY` hoặc `BLOCKED`** — nêu thẳng ở đầu mục "Việc đã làm", không để người
   đọc tự suy từ các dòng xanh bên dưới.

**Nếu `BLOCKED` thì mỗi món chặn phải có `owner` + `ETA`.** Một blocker không có chủ và không có hạn
là một blocker sẽ còn nguyên ngày mai. Owner đọc từ CODEOWNERS chứ không đoán; ETA phải là ngày cụ
thể, không phải *"khi nào xong"*. D13 đã làm đúng mẫu này (8 blocker, mỗi cái một chủ) — giữ nó.

Kèm: bump pointer `packages/evalhub` nếu có PR merge · comment đóng `#103` nêu rõ **không tick ô DoD
nào** và vì sao · mọi link trong comment phải resolve được từ fresh clone (bài học T1).

---

# §3 — Ask gửi ai, nguyên văn

Gộp câu, gửi khi người nhận đang online, kèm sẵn nhánh hệ quả để họ chỉ phải chọn — cách đã rút
`DEC-Q5` từ blocker xuống 74 phút ở D12.

**AIE-1 — @TranBaDat2607**
1. Append `## Phản hồi của chủ quadrant` vào `into-engine-d11.md` (T7). Một artifact hai tác giả.
2. `#101` batch thật có emit `run_id` ổn định đọc lại được từ `obs.trace_events` không? Bộ chấm cần
   `run_id` để đọc lại trace, không đọc RAM.

**DE — @DongAnh2704**
1. Viewer `#100` hiện đang render field nào — để đối chiếu wireframe (T5), tránh đề nghị trùng thứ
   đã có.
2. Xác nhận golden-30 vẫn ETA **08/08 (D16)**; nếu trượt thì `kit#108` phải đổi thứ tự.

**SWE — @Dozyboy**
1. `#102` `run_id`/`agent_id` khớp giữa recipe và trace — đây là khoá để bộ chấm nối bảng điểm về
   đúng recipe. Nếu hai bên sinh id khác nhau, báo sớm trong ngày.

**Không route gì qua mentor.** Từ S2 nhóm tự quyết; mục `week-2` 404 đã đóng bằng phương án lui.

---

# §4 — Hoãn: chủ + hạn, 0 món vô chủ

| Món | Chủ | Hạn | Ghi chú |
|---|---|---|---|
| `compute_scorecard` + gate verdict 2 nhánh | AIE-2 | **D16** `kit#108` | Test boundary `>=` vs `>` phải có case đúng-tại-ngưỡng; mẫu số tách theo `DEC-S2-134-03` |
| `EvalHarness.run` → `Scorecard` | AIE-2 | D16 | Đi qua runner thật, không fixture kết quả dựng sẵn |
| Wilson diagnostic (stdlib, không thêm dependency) | AIE-2 | D16 | Diagnostic, **không** đổi gate v1 — `DEC-S2-134-01` |
| `LLMJudge.judge` + calibration screen | AIE-2 | D18 `kit#118` | Chưa calibration ⇒ `ADVISORY`, `DEC-S2-134-04` |
| F-6 · nhánh refusal 3 conjunct mang 1 bit | AIE-2 | D16/D17 | Đọc `outputs["chunks"]` thay `citations` |
| F-4 · `e2e_smoke_eval.py:274` báo sai T6 là "fence thủng" | **chưa có chủ** | xin chốt D15 | Ghi là vô-chủ-có-hạn, không bỏ im |
| ICC / cluster-adjusted CI | AIE-2 | sau S2 | Cần cluster metadata + route decision |
| Self-assessment 12 ô | AIE-2 | **D19** | Mentor publish matrix sáng D19; nộp trước gate 24h |

---

# §5 — Rủi ro đã biết

| Rủi ro | Xác suất | Giảm thế nào |
|---|---|---|
| AIE-2 cuối chuỗi `#101→#100→#102→#103`, upstream trượt | cao — Integration Friday | DEC-D15-01 đường 1: đọc trace **đã bền hoá** từ D14, không chờ run live |
| `apps/studio` CODEOWNERS = mentor, PR kẹt qua cuối tuần | trung bình | Deliverable T3 nằm trong `evalhub`; chỉ chạm `apps/studio` nếu dư thời gian |
| D16 (thứ Bảy) phụ thuộc golden-30 của DE | trung bình | Hỏi ETA trong T2; T4 viết test trước bằng fixture tay để gỡ phụ thuộc |
| Ngày trôi vào evidence, `O3.1` đứng yên ngày thứ tư | **cao — đã xảy ra 3 lần** | T3 là deliverable code, đặt trước T5/T6 trong thứ tự làm |
| Push thêm commit làm bay approval | trung bình | Gom lint/format/`ruff` **trước** khi xin review |

---

# §6 — Định nghĩa xong cho D15

```
[ ] T1   hai link chết của D14 đã vá, kiểm bằng API chứ không bằng mắt
[ ] T3   test contract viết TRƯỚC, đỏ bằng assertion semantic (không phải ImportError), rồi mới implement
[ ] T3   render per-case in số THẬT của một run_id có thật; lệnh tái lập ghi trong note
[ ] T3b  mutant có ý nghĩa tự gieo, KHAI TRƯỚC + nêu test kỳ vọng đỏ; equivalent/irrelevant phân loại riêng, không quota số lượng
[ ] T4   fixture bất đối xứng chỉ ở metric/property đang harden + bất biến cưỡng chế; evalhub xanh, 0 XPASS
[ ] T5   bảng lệch wireframe ↔ viewer, mỗi dòng trỏ field trace có thật
[ ] T6   fresh recursive clone chạy được MỘT lệnh ra bảng; runbook đã ghi
[ ] T7   đã gửi ask mutation hai chiều
[ ] T8   note same-day có số + chẩn đoán + READY/BLOCKED; nếu BLOCKED thì mỗi blocker có owner + ETA ngày cụ thể
```

**Thứ tự cắt khi hết giờ:** T5 → T6 → T7. **Không** cắt T3b.

**Không** nằm trong định nghĩa xong: `compute_scorecard`, aggregate tổng, verdict, judge, golden-30
đủ 30 case. Bốn món đó là D16–D18 và việc kéo chúng lên D15 sẽ phá đúng bốn ô đắt nhất trong grid.
