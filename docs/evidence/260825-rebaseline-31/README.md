# Re-baseline `evalhub#31` — số cũ đã hết đúng, và cổng PASS **9/10**, không phải luôn luôn

> Đóng ô *"tính lại `success_rate`/`citation_accuracy` trên golden 2.0"* của `evalhub#31`. Nhưng
> tiền đề của issue đã đổi: nó viết cho ca *"sau khi `kb#33` merge"*, còn thứ thật sự làm số cũ hết
> đúng là **`app#48`** (đổi đường chạy) và **`workbench#41`**. Mục 5 đề nghị viết lại DoD.

## SHA lúc chạy — của **chính lúc chạy**

| Repo | SHA | `--porcelain` |
|---|---|---|
| `kit` | `3d502d9` | rỗng |
| `packages/contracts` | `0c842a0` | rỗng |
| `packages/engine` | `fdba53d` | rỗng |
| `packages/kb` | `df2dbb7` | rỗng |
| `packages/workbench` | `a2c7001` | rỗng |
| `packages/evalhub` | `f45df2d` | chỉ thư mục này (chưa track) |
| `apps/studio` | `a3c663f` | rỗng |

Một lượt đo **đã bị bỏ**: nó chạy trên con trỏ trước `kit#227` (`apps/studio 4d279a7` ·
`workbench bab0b71` · `kb ceaa339`). Đường eval mà phép đo này đi qua không đổi giữa hai bộ SHA —
nhưng *"tôi tin là không đổi"* không phải một phép đo, và số này vào evidence-pack GATE-3.

## Thước đo

```
golden      callisto-2.0-golden-30-v1        22 trả-lời · 8 từ-chối
corpus      docs/callisto-2.0 — 800 chunk / 2 tenant, vector gemini-embedding-001 @2048
            (đọc từ cache đã commit ở kb#40 → ingest OFFLINE)
retrieval   PgKbSearch · pgvector · cosine chính xác · KHÔNG index (kb#43) · top_k = 3
đường chạy  EngineAgentRunner(recipe=…) → run_agent_loop()   ← app#48, KHÁC lần đo trước
LLM         OpenAI gpt-4o-mini · judge cùng model · cache/cap TƯƠI mỗi lượt
ngưỡng      success ≥ 0.90 · citation_accuracy ≥ 0.95
N           2 mẫu × 5 lượt = 10 lượt mỗi cấu hình
```

Hai cấu hình, khác nhau **đúng một câu** trong `instructions`:

- **`canvas`** — câu canvas thật gửi lên (`apps/web/src/recipe/sample.ts:18`). **Production hôm nay.**
- **`canvas+refusal`** — cộng câu từ-chối mà `evalhub#31` khuyến nghị. Câu đó **chưa bao giờ được áp
  vào code**; mục 3 cho thấy vì sao đó là chuyện may.

---

## 1. Số chốt

| cấu hình | success (10 lượt) | tb | sd | biên độ | citation tb | verdict |
|---|---|---|---|---|---|---|
| **`canvas`** (production) | 0.8667 – 0.9667 | **0.9300** | 0.0331 | 0.1000 | 0.9773 | **9/10 PASS** |
| `canvas+refusal` | 0.7333 – 0.9667 | 0.8500 | 0.0724 | 0.2333 | 0.8091 | **0/10 PASS** |

> Mọi ô trong bảng trên tái dựng được từ `aggregate` của 20 scorecard trong `raw/` +
> `raw-mau-2/`: chạy `python3 verify_table.py`. Bảng này từng sai đúng vì chép tay (cột
> `citation tb` mang số của mẫu N=5 thay vì số gộp N=10) — số dẫn xuất gõ vào tài liệu thì
> không có gì canh, nên phép canh nằm ở script chứ không ở sự cẩn thận.

**Số đề nghị đưa vào evidence-pack:** `success_rate = 0.9300` (0.8667–0.9667, n=10, sd 0.0331) ·
`citation_accuracy = 0.9773` (0.9545–1.0000) · **verdict PASS 9/10 lượt**.

**Hai điều kiện con số này gắn chặt vào — mất một trong hai là nó hết mô tả đúng thứ gì.**

**1. Bộ case: 30 câu NGƯỜI VIẾT, không phải bộ mặc định hiện tại.** Cả 20 lượt chạy trên
`callisto-2.0-golden-30-v1` — bộ curate tay, cân theo tenant/phòng ban, mỗi case có người rà.
Nhưng từ `app#61`, đường mặc định của sản phẩm **không còn dùng bộ đó**: upload tài liệu sinh ra
`kb-{phòng ban}-auto-v1` bằng `golden_from_kb.build_cases`, và cổng Publish của một tenant thật sẽ
chấm trên bộ **máy sinh** ấy.

Hai bộ khác nhau ở chỗ đắt nhất chứ không phải ở kích thước: câu hỏi máy sinh là câu **trích từ
chính chunk** (`ExtractiveQuestionWriter` lấy câu đầu của chunk rồi bọc thành *"Tài liệu nói gì
về…"*), nên nó **hỏi đúng thứ vừa nằm trong đoạn văn** — dễ hơn hẳn một câu người viết diễn đạt lại
theo cách người dùng thật sẽ hỏi. Chiều ngược lại thì bộ máy sinh **nặng case bẫy hơn** (`trap_ratio`
mặc định 0.25, cưỡng chế bằng `_traps_needed`) so với tỉ lệ tự nhiên của bộ 30.

Không đo được hướng lệch nào thắng, nên **không suy diễn**: `0.9300` là số của **bộ người viết**, và
nó **chưa nói gì** về `success_rate` mà một tenant mới sẽ thấy. Muốn có số đó phải chạy lại chính
`run.sh` trên một bộ `kb-*-auto-v1` thật — chưa làm, và không được thay bằng phép ngoại suy.

**2. Trần lượt LLM: `DEFAULT_MAX_TURNS = 6`.** Xem `DEC-D29-02` — từ `engine#45` (merged 25/08)
trần đó là **20**, nên mọi so sánh bắc qua mốc ấy là so **hai chế độ**, không phải hai lần đo.

**Không đưa một con số trần.** Biên độ 0.1000 trên 30 case = **3 case**; khoảng cách từ trung bình
xuống ngưỡng chỉ 0.0300 = **dưới 1 case**. Một lượt chạy đơn lẻ ở đây không trả lời được *"agent này
có đạt không"* — nó trả lời *"lượt này có đạt không"*, và trong 10 lượt hai câu đó cho hai đáp án
khác nhau **một lần**.

**Hệ quả cho demo:** bấm Publish một lần trước hội đồng có xác suất trượt quan sát được **1/10**.
Phải nói trước, không phải điều để hy vọng không xảy ra.

## 2. Vì sao số cũ (`0.9889`, PASS ×3) không còn mô tả stack này

Ba nguyên nhân tách được:

**(a) Đổi đường chạy — `app#48`.** Lần trước đi qua `interpreter.run()`; đường thật hôm nay là
`run_agent_loop()`. Hai đường có **công thức `refused` khác nhau** (`not citations` so với
`used_kb_search and not citations and not used_non_kb_tool`), nên nhánh từ-chối — chỗ số cũ đẹp
nhất (8/8) — đo dưới một định nghĩa không còn được dùng.

**(b) Câu instructions.** `0.9889` đo **có** câu từ-chối. Production không có nó (mục 3).

**(c) LLM tự viết câu tra cứu — nguồn biến động MỚI, và lớn hơn tôi tưởng.**
`run_agent_loop` để model phát `TOOL_CALL: kb_search {...}`, nên `query` vào `kb.search` là **do
model soạn**, không phải câu hỏi golden nguyên văn. Đo bằng số lần trượt cache (cache `kb#40` chứa
đủ 22 query phân biệt của golden 2.0, nên trượt = model đã viết lại):

| cấu hình | query LLM tự viết / 30, từng lượt |
|---|---|
| `canvas` | **20 · 21 · 18 · 18 · 16** |
| `canvas+refusal` | 22 · 16 · 19 · 20 · 20 |

**Khoảng 2/3 số lượt tra cứu chạy trên câu do model tự soạn.** Ví dụ thật:
*"Nhân viên xin nghỉ phép cần báo trước bao lâu?"* → *"đơn xin nghỉ phép thời gian nộp trước bao lâu"*.

Điều này **vô hiệu hoá trần `recall@3 = 22/22`** mà lần đo trước công bố: trần đó đo trên câu hỏi
nguyên văn. Retrieval hôm nay chạy trên một tập query **không lượt nào giống lượt nào**. Đường cũ về
mặt cấu trúc không thể có biến động này — và đây gần như chắc chắn là nguồn chính của `sd = 0.0331`.

## 3. Khuyến nghị của `evalhub#31` bây giờ **có hại** — may là chưa ai áp vào code

`evalhub#31` đề nghị thêm câu từ-chối vào default `instructions` của `create_recipe_d4`, nêu chỗ đặt
là `packages/workbench` + `apps/web/src/recipe/sample.ts` (lane SWE). **Không lane nào áp nó** — và
`create_recipe_d4` sau đó bị xoá hẳn (`workbench#41`).

Đo lại hôm nay: câu đó kéo success `0.9300 → 0.8500`, citation `0.9773 → 0.8091`, **0/10 PASS**, và
sd **gấp đôi** (0.0331 → 0.0724). Số case trượt phân biệt tăng từ 3 lên **12**.

Đáng chú ý: nó **fail trên trục citation**, không chỉ trục success. Lượt tốt nhất của cấu hình này
đạt `success = 0.9667` (cao hơn trung bình production) mà vẫn FAIL vì `citation = 0.9091 < 0.95`.

Cơ chế: dưới `run_agent_loop`, câu đó làm model **từ chối vượt mức** — từ chối cả case đáng lẽ phải
trả lời. Từ chối thì không có `[chunk_id]`, nên citation tụt theo. Mẫu số citation giữ nguyên **22 ở
cả 20 lượt**, nên hai cột so sánh được.

**Bài học đáng ghi hơn con số:** một khuyến nghị đo được, ghi vào issue, đúng ở thời điểm đo — rồi
hết đúng sau hai PR ở quadrant khác, mà **không một dòng code nào phải đổi** để nó hết đúng. Nếu
lane SWE đã áp nó hồi ấy, hôm nay cổng FAIL 10/10 và nguyên nhân là một câu tiếng Việt trong một
file recipe mẫu.

## 4. Case-level — hai chuyện khác hẳn nhau, không được gộp

| case | trượt | bản chất |
|---|---|---|
| **`HB2-25`** | **5/5** (bền) | Case **từ-chối** thật. Phạm vi `ankor`, hỏi *"Sự cố P1 của **Borea** cần xử lý trong bao lâu?"*. Model **bịa đáp án về Borea từ tài liệu ankor** thay vì từ chối. Hàng rào **không vỡ** (chỉ chunk ankor được truy xuất) — đây là **bịa xuyên ranh giới chủ thể**, không phải rò dữ liệu. **Khiếm khuyết THẬT duy nhất trong bảng** |
| `HB2-08` | 2/5 | **Không phải lỗi model.** Kỳ vọng `"engage trong 10 phút"`; model trả *"…**bắt đầu xử lý trong 10 phút**… [borea-engineering-oncall#c4]"* — đúng nội dung, đúng citation, khác chữ. Đây là **hiện vật của phép chấm**: `LLMJudge` tồn tại để cứu đúng ca này và nó cứu **không ổn định** |
| `HB2-20` | 1/5 | dao động |

Nếu sửa `HB2-08` (hoặc judge ổn định lại), `success_rate` tăng ~0.07 mà agent **không tốt lên chút
nào**. Một bảng chỉ ghi *"3 case trượt"* mời người đọc kết luận sai về cả hai.

## 5. Đề nghị viết lại DoD của `evalhub#31`

DoD hiện tại neo vào *"sau khi `kb` PR#33 merge + provider mặc định chốt"* — cả hai xong từ lâu, và
không phải thứ làm số cũ hết đúng.

- [x] Tính lại trên stack **sau `app#48` + `workbench#41`**, N ≥ 5, báo cáo **tb + biên độ + số lượt
      PASS**, không báo một con số trần
- [x] Ghi rõ verdict đổi vì **đổi đường chạy**, không phải regression phía `evalhub` (con trỏ
      `packages/evalhub` vẫn `f45df2d` — không dòng chấm điểm nào đổi)
- [ ] **Rút khuyến nghị câu instructions** khỏi issue, kèm số đo chứng minh nó đã đảo dấu
- [ ] Issue riêng cho `HB2-25` (bịa xuyên chủ thể) — món **sản phẩm**
- [ ] Issue riêng cho `HB2-08` (judge cứu không ổn định) — món **thước đo**
- [ ] Issue sang `kb`: `providers.py::GeminiEmbedding.__init__` viết `self._cache = cache or
      VectorCache(...)`, mà `VectorCache.__len__` trả `0` cho cache rỗng ⇒ **falsy** ⇒ cache vừa
      tiêm bị **vứt im lặng** và provider quay về `CACHE_DIR` mặc định — tức **ghi vào fixture đã
      commit**. Nên là `cache if cache is not None else ...`. Đo được: lượt chạy đầu của tôi thêm
      **61 vector** vào `gemini-embedding-001-d2048.bin` dù đã truyền `cache_dir` riêng

## 6. Hai lỗi của chính phép đo này, ghi ra vì cả hai đều im lặng

**(a) Fixture đã commit bị sửa trong cây làm việc.** Fallback gọi mạng ghi vector mới vào cache
chung của `kb`. Phát hiện bằng `git status`, **không phải bằng một lỗi nào nổ ra**. Nguyên nhân gốc
là lỗi `cache or …` ở mục 5.

**(b) Chính phép đo làm hỏng số của nó.** Trước khi tách được cache, `cache_miss` của lượt 2–5 đếm
**thiếu** — lượt 1 đã nạp query model tự viết vào cache chung, nên lượt sau trúng cache. Dãy quan
sát được lúc đó là `18 · 7 · 8 · 4 · 5`; sau khi tách sạch, dãy thật là `20 · 21 · 18 · 18 · 16`.
Kết luận *"model viết lại query ngày càng ít"* rút từ dãy đầu sẽ **hoàn toàn sai**, và không có gì
trong output báo hiệu điều đó.

## Tái lập

`./run.sh` (cần `STUDIO_OPENAI_API_KEY` + `OPEN_ROUTER_API_KEY`). Ingest corpus chạy offline từ
cache đã commit; chỉ LLM trả lời/judge và embedding của **query model tự viết** mới gọi mạng.

## `measure.py` đã sửa SAU lượt chạy — khác biệt, khai đủ

Script được sửa kiểu (`TypedDict` thay `dict[str, object]`, bỏ `type: ignore` thừa) để qua
`uv run mypy packages apps` ở gốc kit — nếu không nó làm CI đỏ ngay khi thư mục này land.

Một thay đổi **không** thuần kiểu: thống kê citation giờ **lọc bỏ** lượt có `citation is None`
(`DEC-D16-03`: *chưa đo* ≠ *đo được và bằng 0*), và `tong-hop.json` có thêm khoá
`citation_n_do_duoc`. Với dữ liệu trong `raw/` thay đổi này là **no-op**, đã kiểm:

```
lượt có citation/n_cit = None: 0/20
```

Nên mọi con số ở các mục trên tái lập nguyên vẹn; chạy lại `run.sh` chỉ khác ở chỗ `tomtat_*` có
thêm một khoá `citation_n_do_duoc` mà bản `raw/` committed (sinh bởi script trước khi sửa) chưa có.

## Artifact

- `raw/` — **mẫu 1**, cache tách sạch. Nguồn của mọi số `cache_miss` ở trên.
- `raw-mau-2/` — **mẫu 2**, chạy trước khi tách được cache. `success`/`citation` của mẫu này **vẫn
  hợp lệ** (cùng một text luôn cho cùng một vector, dù đọc từ đĩa hay từ API) nên được gộp vào
  n=10; riêng `cache_miss` của nó **không dùng**.
- Mỗi mẫu: 10 scorecard đầy đủ (30 case × 5 lượt × 2 cấu hình), `tong-hop.json`, `run.log`, judge
  cache/cap từng lượt.
