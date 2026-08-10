# Plan Day 16 — AIE-2 · Eval harness v1 + scorecard chấm điểm thật + verdict PASS/FAIL · Thứ Hai 10/08/2026

> **Một đính chính về ngày, ghi ra để không ai lần theo số sai:** plan D15 gọi D16 là *"thứ Bảy 08/08"*.
> Sai. Body `#108` và `#109` đều ghi **"Ngày 16 · Thứ Hai 10/08 · Chặng 2 (Sprint 2) · Tuần 4"** —
> issue là spec thẩm quyền, plan cũ là chỗ gõ nhầm.

---

# Executive Summary

**Goal.** Đóng **ba seam `NotImplementedError` cuối cùng** của quadrant — `compute_scorecard`,
`EvalHarness.run`, và đường nạp golden-set — để một recipe chạy qua **30 case thật của DE** ra một
`Scorecard` có `gate.verdict` thật, và **đổi threshold thì verdict đổi**.

**Vì sao D16 khác mọi ngày trước.** Từ D12 tới D15, dòng 🎯 của issue là việc AIE-2 còn **không ô DoD
nào** thuộc AIE-2 (plan D15 §0 ghi rõ: 3/3 ô là của người khác). D16 đảo ngược hoàn toàn:

| Ô DoD chung (`#109`) | Chủ thật | Ghi chú |
|---|---|---|
| Eval harness v1 chạy 30 case | **AIE-2** (`#108`) | của mình |
| scorecard render success+citation+verdict | **AIE-2** (`#108`) | của mình |
| golden-set 30 có nhãn | DE (`#105`) | **đã giao rồi** — xem §1 |
| đổi threshold → verdict đổi | **AIE-2** (`#108`) | của mình |

**3/4 ô DoD là của AIE-2.** Đây là ngày chủ công thật, không phải ngày đứng cuối chuỗi phụ thuộc như
Integration Friday. Không có ai để đổ lỗi lịch, và cũng không có ô nào để tick hộ người khác.

**Nợ đến hạn hôm nay là nợ tự khai.** Không phải mentor giao thêm — chính decision-log và daily-note
của AIE-2 đã ghi hạn **D16** cho **9 món** (§4). Một ngày mà 3 deliverable chính cộng 9 món nợ cùng
đến hạn thì thứ quyết định kết quả là **thứ tự làm**, không phải tốc độ gõ.

**Rủi ro lớn nhất KHÔNG phải là không kịp.** Là **xanh-giả**: `compute_scorecard` land ra một
`aggregate` cộng nhầm mẫu số (đúng lỗi `DEC-04` đo được: `0.90` in ra trong khi số thật `0.833`), rồi
`gate.verdict = PASS` được đọc là bằng chứng. `kit#134` gọi đúng tên: *chỗ hỏng không nằm ở probe, nằm
ở bước từ `8/10` sang tám-mươi-phần-trăm*. Cả plan này được sắp xếp quanh việc chặn đúng một lớp lỗi đó.

---

# §1 — Nền đã kiểm, không giả định

Mọi dòng dưới đây kiểm bằng lệnh đầu ngày, không chép lại từ hôm trước. Dòng nào **có hạn sử dụng**
ghi rõ.

| Việc | Trạng thái đã kiểm | Bằng chứng |
|---|---|---|
| Con trỏ kit | `kit@4c3e55f` — **9/9 submodule khớp `origin/main`**, working tree sạch | `git submodule status` không dòng nào có `+`/`-` |
| D15 đã đóng | `evalhub#14`,`#15` MERGED · `reports#61` MERGED · `kit#142` (bump D15) MERGED · `kit#103` **CLOSED** 07/08 11:10 | `gh pr list`, `gh issue view 103` |
| **Golden-30 của DE** | ✅ **ĐÃ GIAO và đã nằm trong con trỏ kit** — `packages/kb/golden/callisto-handbook-30-draft.yaml`, `kb@1e8774f` | đọc trực tiếp file ở pointer hiện tại |
| Nội dung golden-30 | `golden_set_ref: callisto-golden-30-v1` · **30 case** · **22 trả-lời / 8 từ-chối** (`HB-23`…`HB-30`) · tenant: ankor 19 / borea 11 · vai: hr 12 · public 7 · finance 7 · engineering 4 · **0 case trả-lời có `expected_citation` rỗng** | parse YAML bằng `.venv/bin/python` |
| Shape golden-30 | 8 field, **khớp đúng `GoldenCase`** — `case_id · query · tenant · section_roles · expected_tenant · expected_section_role · expected · expected_citation` | so với `golden_case.py:33-85` |
| `match_mode` | **KHÔNG có** trong golden-30 | grep — xem `DEC-D16-06` |
| Đề bài `week-2/days/day-16.md` | **404** — ngày thứ sáu liên tiếp. Repo requirements chỉ có `00-orientation · README.md · nda-denylist.sh · week-1` | `gh api .../contents` |
| Ba seam | `compute.py:30` · `harness.py:217` · `judge.py:35` — **cả ba còn `raise NotImplementedError`** | đọc file |
| **Loader golden-set** | **KHÔNG TỒN TẠI.** 0 dòng `import yaml` trong `src/studio_evalhub/`. Case đang dựng **in-code** ở `cli.py:46` | grep |
| **`pyyaml`** | Khai ở **`[dependency-groups] dev` của kit gốc** (`pyproject.toml:26`), **KHÔNG** ở `packages/evalhub/pyproject.toml:6-10` | đọc cả hai file |
| Ngưỡng mặc định recipe | `success=0.9, citation_accuracy=0.95` (`workbench/src/studio_workbench/builder.py:169,242`) | grep |
| `golden_set_ref` mặc định recipe | `"callisto-smoke-5-v0"` (`builder.py:106,241,255`) — **chưa trỏ golden-30** | grep — ask SWE, §5 |
| Bài đỏ-by-design | `test_gate_blocks_on_fail` đeo `xfail(strict=True)` (`test_eval_gate.py:44`) | đọc file |

**Đừng tin bảng này, chạy lệnh** (cùng khuôn với bảng chữ ký D11 — bảng nào sẽ mục thì phải đi kèm
cách tự đo):

```bash
# nền: pointer + suite + ba seam còn raise hay không
git -C . submodule status | grep -E '^\+|^-' || echo "pointer: 9/9 khớp"
uv run pytest packages/evalhub/tests -q | tail -3
uv run python -c "
from studio_evalhub import compute_scorecard, EvalHarness, LLMJudge
import inspect,sys
for f in (compute_scorecard,): print(f.__name__, 'raise' if 'NotImplementedError' in inspect.getsource(f) else 'ĐÃ ĐIỀN')
"
# golden-30 có thật trong pointer không (không phải trên một nhánh chưa merge — bài học DEC-Q5)
P=$(git ls-tree origin/main packages/kb | awk '{print $3}')
gh api "repos/AI20K-VGR/agentcore-studio-kb/contents/golden/callisto-handbook-30-draft.yaml?ref=$P" --jq '.size'
```

## Một cái bẫy tên file, phát hiện khi kiểm nền

Tên file là `callisto-handbook-30-**draft**.yaml` nhưng `golden_set_ref` bên trong là
`callisto-golden-30-**v1**`. Header file tự ghi *"D14 build, giao AIE-2 cho eval harness D16"* và đủ
30 case — tức **nội dung không còn là draft**, chỉ tên file còn.

Hệ quả phải xử lý ở loader, không phải bằng cách nhớ: **`golden_set_ref` là khoá, tên file là đường
dẫn.** Loader phải đọc `golden_set_ref` **từ trong file** và **assert nó khớp cái caller yêu cầu**,
không bao giờ suy ref từ tên file. Không có bài test khoá điều này thì ngày DE đổi tên file (bỏ chữ
`draft`) là ngày mọi thứ gãy im lặng — hoặc tệ hơn, chạy một bộ case khác mà không ai biết.

## Bản đồ phụ thuộc D16

```
#105 DE      golden-set 30 có nhãn                        ✅ ĐÃ GIAO (kb@1e8774f)
#106 AIE-1   interpreter chạy 30 case deterministic       ⏳ song song — CHỈ cần cho đường "run thật"
#107 SWE     recipe.golden_set_ref → golden-30            ⏳ song song — CHỈ cần cho đường publish-gate
   └─► #108 AIE-2  harness v1 + compute + verdict         ← ngày hôm nay
```

**Khác D15 ở chỗ quyết định:** AIE-2 không còn đứng cuối chuỗi. Đường tới cả 3 ô DoD của AIE-2 chỉ
cần **golden-30 (đã có)** + `StubAgentRunner` (đã có, `agent_runner.py:98`). `#106` và `#107` là điều
kiện của **đường chạy thật end-to-end**, không phải điều kiện của deliverable AIE-2.

⇒ **Không có gì để chờ.** Nếu D16 hụt thì nguyên nhân nằm trong quadrant này, không nằm ở ai khác.

## Dependency/blocker rule (giữ nguyên từ D15)

> Khi gặp input/dependency từ người khác, **KHÔNG tự đoán hoặc giả định**. Xác định chính xác phần
> nào bị block; **tiếp tục thực hiện các phần độc lập còn lại**. Chỉ **DỪNG** khi đã đến bước thực sự
> cần input đó. Khi DỪNG, báo rõ:
>
> ```
> cần ai → cần gì → vì sao → phần nào đã hoàn tất → phần nào đang block → owner + ETA nếu biết
> ```

---

# §2 — Quyết định phải chốt hôm nay

Từ 03/08 mentor không trả lời câu hỏi kiến trúc (`kit#74` S2) ⇒ nhóm tự quyết + tự viết ADR, và **ADR
là tiêu chí chấm S2**. Sáu quyết định dưới đây phải có mặt trong `docs/decisions/scorecard.md` **trước
khi** code tương ứng land, không phải ghi bù cuối ngày — D15 đã trả giá đúng chỗ đó (3 id `DEC-D15-*`
bị trích ở 8 chỗ **trước khi** có bản ghi, tức là tham chiếu treo suốt một ngày).

> **Đúng sáu id, không phát sinh id thứ bảy trong ngày.** Mọi quyết định nảy ra lúc gõ phải **gắn vào
> một trong sáu** id dưới đây, không mở `DEC-D16-07`. Lý do không phải là gọn: một id sinh ra giữa
> ngày là một id **chưa có ai đọc**, và D15 vừa cho thấy chi phí của nó (3 id treo, 8 chỗ trích, cả
> ngày không truy được). Nếu một quyết định thật sự không gắn được vào sáu id này thì nó **không
> thuộc D16** — ghi vào sổ hoãn kèm chủ + hạn, không nhét vào ngày.

## DEC-D16-01 · Nguồn golden-set: loader nhận **đường dẫn**, không hardcode đường chéo repo

**Quyết:** thêm `studio_evalhub/golden_loader.py` với `load_golden_set(path: Path, *, expect_ref: str) -> GoldenSet`.
Đường dẫn do **caller** truyền (CLI arg / composition root), **không** hằng số
`packages/kb/golden/...` trong `src/`.

**Vì sao:**
1. **Layering.** `.importlinter` xếp 4 quadrant là sibling — `studio_evalhub` không import
   `studio_kb` được. Một đường dẫn file chéo repo là cùng một sự phụ thuộc, chỉ né được lint chứ
   không né được thực tế.
2. **Fresh clone.** `kit#74` chấm bằng *"clone sạch rồi chạy lệnh y nguyên"*. Clone **riêng** repo
   evalhub thì `packages/kb/` không tồn tại ⇒ hằng số đường dẫn là một `FileNotFoundError` được đảm
   bảo trước.
3. **`DEC-Q5` đã chốt phân vai:** DE sở hữu **giá trị**, AIE-2 sở hữu **nơi lưu + loader**. Loader
   nhận đường dẫn là đúng nghĩa đen của câu đó.

**`expect_ref` bắt buộc, không default:** xem bẫy tên file ở §1. Lệch ⇒ raise, không cảnh báo.

### Hợp đồng loader → harness, khoá luôn ở đây

Quyết định "loader nhận path" chỉ có răng nếu **tầng trên nó cũng không được phép biết đường dẫn**.
Nên chốt cả hai đầu, không chỉ đầu loader:

| Tầng | Được biết gì | KHÔNG được biết gì |
|---|---|---|
| `golden_loader.load_golden_set(path, *, expect_ref)` | `path`, `expect_ref` — **do caller truyền, không default** | bất kỳ đường dẫn cụ thể nào |
| `EvalHarness.run(agent_id, golden_set_ref, *, golden_set_path)` | nhận `golden_set_path: Path` **keyword-only, bắt buộc** rồi chuyển xuống loader với `expect_ref=golden_set_ref` | `packages/kb/...`, workspace root, `__file__`-relative |
| Composition root (CLI arg · `apps/studio` · test fixture) | **chỗ DUY NHẤT** biết golden-30 nằm ở đâu | — |

**`golden_set_path` bắt buộc, không default `None`.** Một default là chỗ để ai đó điền đường dẫn kb
"cho tiện" ở lần sửa sau, và khi đó DEC này thành một câu chữ. Chữ ký cũ
`run(agent_id, golden_set_ref)` **vỡ** — chấp nhận có chủ đích: call-site duy nhất là
`test_gate_blocks_on_fail`, mà bài đó đằng nào cũng phải viết lại ở **T7** (`DEC-D16-04`).

**Guard bằng code, không bằng lời** — `test_src_khong_hardcode_duong_dan_kb`: quét mọi file
`src/studio_evalhub/*.py`, assert không chuỗi nào chứa `packages/kb` hay `golden/`. Đây là bất biến
cưỡng chế: nó bắt được cả lần vi phạm **tương lai**, chứ không chỉ chứng minh hôm nay sạch. Bài này
thuộc T1.

## DEC-D16-02 · `pyyaml` phải khai vào `packages/evalhub/pyproject.toml`

**Quyết:** thêm `"pyyaml>=6.0"` vào `[project].dependencies` của evalhub trong cùng PR với loader.

**Vì sao — đây không phải thủ tục.** Chính comment ở `kit:pyproject.toml:22-25` đã ghi lớp lỗi này:

> *"Trước D8 nó chạy được nhờ **ĂN KÉ** extra `uvicorn[standard]` … ai đổi `uvicorn[standard]` →
> `uvicorn` là mọi `import yaml` trong workspace **chết IM LẶNG**."*

Bản vá D8 khai `pyyaml` vào **`[dependency-groups] dev` của kit gốc** — đúng cho một *script* ở kit.
Nhưng loader D16 là **runtime code của một package được cài**, và nó sẽ ăn ké đúng lần thứ hai, chỉ
lùi một tầng: chạy được trong workspace venv vì dev-group kéo `pyyaml` vào lock, chết ngay khi
`studio_evalhub` được cài độc lập. Khai đúng chỗ nó thật sự được dùng — đúng câu comment kia nói.

**Cách tự kiểm:** `uv pip show pyyaml` chạy được **không chứng minh** gì (dev-group đã kéo về). Bằng
chứng đúng là dòng khai trong `packages/evalhub/pyproject.toml`.

## DEC-D16-03 · `Aggregate.n_scored_citation` — additive-optional, PR sang `contracts`

**Quyết:** thêm `n_scored_citation: int | None = None` vào `studio_contracts.Aggregate`. **Không** bump
`SCHEMA_VERSION`.

**Vì sao đây là cách trả nợ `DEC-04` + `DEC-S2-134-03`:** `DEC-04` đã quyết ba tầng (per-case giữ
`1.0` là quy ước · aggregate **loại refusal khỏi mẫu số** · render in `n/a`), nhưng tầng giữa **không
biểu diễn được** bằng `Aggregate` hôm nay — nó chỉ có `success_rate` và `citation_accuracy`
(`contracts/scorecard.py:46-50`). Hệ quả đã ghi thành ghi chú in ra màn hình
(`render.py:36-41` — *"`aggregate` KHÔNG tính lại được từ `results` đã lưu"*): consumer cầm một
`citation_accuracy = 0.90` mà **không có cách nào** biết mẫu số là 30 hay 22.

Con số làm việc này khẩn: bộ 10 báo `0.90` trong khi số thật là **`0.833`**, và phép tính chí tử
`10×1.0 + 20×0.85 = đúng 0.90` ⇒ **một bản đáng FAIL lại PASS ngay ngưỡng `0.9`**. Với golden-30 thì
tỷ lệ refusal là **8/30 = 26.7%** — cùng lớp sai số, quy mô lớn hơn.

**Vì sao không bump:** theo `DEC-01`, nới/thêm optional không bump **với điều kiện đếm được 0 reader
giả định non-null**. Field **mới** thì trần định nghĩa là 0 reader — nhưng vẫn phải **chạy lệnh đếm và
dán kết quả vào PR**, vì đó là hình thức của `DEC-01`, không phải kết luận của nó.

**Đường đi:** PR sang `agentcore-studio-contracts`. Merge gate = **1 approval từ bất kỳ collaborator
`write`** (đo được ở `kb#16` ngày 07/08 — AIE-2 không phải CODEOWNER của kb mà PR vẫn `CLEAN`). Dòng
comment đầu file CODEOWNERS nói ngược, và nó **không khớp** protection đang chạy.

**Rủi ro lịch phải nói trước:** đây là món duy nhất trong ngày **cần người khác bấm nút**. Xử lý ở
§3 T3 (**P1**) — mở PR **sớm nhất có thể trong ngày**, và có đường lùi.

### Ca mẫu số rỗng — cùng DEC này, không mở id mới

`n_scored_citation == 0` (golden toàn refusal) là **cùng một câu hỏi** với phần trên — *"`aggregate`
biểu diễn thế nào khi mẫu số citation không tồn tại"* — nên chốt tại đây thay vì sinh id thứ bảy:

> **`n_scored_citation == 0` ⇒ `aggregate.citation_accuracy = None` và `gate.verdict = "FAIL"`.**
> Không đo được thì không PASS được.

Cùng luật với `not-estimable` của `render.py:76-83` (`n = 0` không cho ra ước lượng nào, `0/0` vẫn mời
người đọc chia một phép chia không tồn tại) và cùng luật fail-closed của `tenant_scope_ok`
(`harness.py:130` — `events` rỗng ⇒ `False`, vì *"không chứng minh được"* phải đọc là chưa đạt).

**Hệ quả kỹ thuật phải land cùng PR, nói ra thay vì để phát hiện lúc chạy:** `None` đòi
`Aggregate.citation_accuracy` nới `float` → `float | None`. Đây **không** phải additive như
`n_scored_citation` — nó đúng là **"ca thứ tư"** mà `DEC-01` mô tả (*tương thích trên dây, KHÔNG
tương thích với reader*), nên phải theo đúng thủ tục `DEC-01`: **đếm reader giả định non-null**. Đã
đếm trước, có **1 reader thật**:

| Reader | Chuyện gì xảy ra với `None` |
|---|---|
| `render.py:201` — `f"{scorecard.aggregate.citation_accuracy:.2f}"` | `TypeError` |

⇒ reader đó **phải được vá trong cùng thay đổi** (in `not-estimable (n = 0)` qua chính
`_count_or_not_estimable`), không để sang PR sau. `DEC-01` cho phép không bump **với điều kiện** 0
reader giả định non-null; ở đây điều kiện được thoả **bằng cách vá reader**, không phải bằng cách
tuyên bố nó không tồn tại. Ghi rõ vì đây đúng là chỗ dễ tự cho qua.

## DEC-D16-04 · Gỡ `xfail(strict=True)` của `test_gate_blocks_on_fail` — có chủ đích, kèm ADR

**Quyết:** khi `EvalHarness.run` trả `Scorecard` thật, **gỡ hẳn marker** (không đổi sang
`strict=False`), **đọc lại assert bên trong**, và ghi ADR về lần đổi marker này.

**Vì sao phải là một quyết định có ghi, không phải một dòng `git diff`:** cơ chế `strict=True` được
dựng ở D9 với đúng mục đích *"lúc seam xong, nó lặng lẽ thành `XPASS` và không ai buộc phải quay lại
xem assert bên trong có còn đúng hợp đồng hay không"* (`test_eval_gate.py:20-24`). Hôm nay **chính là
ngày cơ chế đó bắn** — và cách duy nhất làm nó vô nghĩa là gỡ marker cho suite xanh rồi đi tiếp. Nợ
ADR này đã được `render.py:9` khai trước: *"quyền đổi marker (M6) mới chỉ có ADR **dự kiến** viết ở
D16"*.

**Việc thật khi gỡ, không phải xoá một dòng:** assert hiện tại là
`scorecard.gate.verdict == "FAIL"` cho `agent_id="agent-bad-instructions"`,
`golden_set_ref="golden-set-eval-1"`. **Cả hai giá trị đó không tồn tại.** Gỡ marker mà giữ nguyên
thân bài sẽ ra một `LookupError`/`FileNotFoundError`, không ra `FAIL` — tức bài money-shot phải được
**viết lại** để chạy trên golden-30 thật với một recipe cố tình tệ. Đây là công việc của T7, và nó
lớn hơn vẻ ngoài.

## DEC-D16-05 · Ngưỡng: **đo trước, chốt sau** — và nói thẳng chỗ mâu thuẫn với GUIDE-C

**Quyết — bốn bước, và bước chốt KHÔNG nằm trong D16:**

> **Giữ `0.9/0.95` trong D16** → **đo** trên golden-30 → nếu số liệu cho thấy cần recalibrate thì
> **ghi số liệu + lý do vào sổ hoãn** → **quyết định/chốt ngưỡng ở ngày sau**.

Không đổi ngưỡng trước khi có số, và **không chốt ngưỡng trong cùng ngày đo được số** — đó là hai
luật khác nhau, luật thứ hai là chỗ D16 dừng lại.

**Chỗ mâu thuẫn, nói ra thay vì giấu:** GUIDE-C §3.2 đòi *"ngưỡng literal phải có trước dataset"* —
và điều đó **đã được tuân thủ** (ngưỡng `0.9/0.95` có từ workbench D-nào-đó, dataset về D14). Nhưng
sổ hoãn của chính AIE-2 lại ghi hạn D16 cho *"recalibrate ngưỡng sau golden-30 trên corpus thật"* với
lý do đo được: **bộ 5 → `0.80`, bộ 10 → `0.60` / `0.833` thật ⇒ với mặc định `0.9/0.95` một recipe
TỐT cũng FAIL cả hai trục.**

Hai câu này không mâu thuẫn nếu đọc đúng: GUIDE-C cấm **chọn ngưỡng cho vừa với số vừa đo được**
(fitting), không cấm **sửa một ngưỡng đã chứng minh được là sai đơn vị**. Ranh giới giữa hai việc mỏng,
nên luật tự áp:

> Ngưỡng mới chỉ được chốt kèm **một lý do không nhắc tới điểm của recipe hiện tại**. Nếu lý do duy
> nhất viết ra được là *"để nó PASS"*, thì không đổi ngưỡng — mà ghi FAIL và để FAIL.

**Và một điều kiện cứng, từ `DEC-08`:** trục `citation_accuracy` **hiện đang đo sức mạnh FENCE, không
đo sức mạnh TRUY XUẤT** (null control: vector hằng số 0 bit thông tin vẫn đạt `recall@1 = 6/6`). Chốt
một ngưỡng `citation_accuracy` mới mà không kiểm lại tiền đề đó là chốt một con số cho một thứ khác
với tên của nó.

⇒ **Số đo trục `citation_accuracy` ghi ở D16 mang nhãn `TẠM`**, và điều kiện gỡ nhãn là **T9b xanh**
(bài hồi quy embedding). Nhãn này đi theo **số liệu** vào sổ hoãn, và sẽ đi theo cả **ngưỡng** khi
ngày sau chốt — vì cái nó cảnh báo là *trục này đang đo thứ khác với tên của nó*, chuyện đó không đổi
khi sang ngày mới. Đây là ràng buộc **về nhãn**, không phải về **thứ tự chạy**: T6 là P0 và **không
chờ** T9b (P2, có tiền đề chưa thoả — xem §3 T9b). Trục `success` không dính điều kiện này vì
`DEC-08` chỉ nói về trục citation.

Viết theo hướng này vì hướng ngược lại — *"T6 chạy sau T9b"* — sẽ buộc một ô DoD (P0) phụ thuộc một
món P2 mà **tiền đề của nó nằm ở người khác**. Đó là cách tự tạo blocker giả cho chính mình.

## DEC-D16-06 · `match_mode` — **hoãn tiếp**, có lý do đo được

**Quyết:** **không** thêm `match_mode` vào `GoldenCase` ở D16. Dời sang **D18** (cùng mốc `F-6`
agreement / `kit#118`).

**Vì sao — đây là rút một hạn tự đặt, nên phải có số:** sổ hoãn ghi *"`match_mode` (`exact`/`judge`)
thành field optional khi bộ 30 về"*, hạn D16, chủ AIE-2 + DE. Bộ 30 đã về, nên hạn tới. Nhưng bộ 30
**không có case nào cần judge**: đã kiểm — 0/30 case có field `match_mode`, và cả 30 đều chấm được
bằng `_contains_phrase` (22 trả-lời) hoặc luật refusal (8 từ-chối). Thêm một field mà **mọi giá trị
đều là `exact`** là thêm một nhánh code không có case nào đi qua — đúng lớp "khung rỗng trông như đã
xử lý" mà `DEC-D12-02` cấm ở tầng render.

**Điều kiện lật:** ngày DE giao case cần judge (yêu cầu *"≥3 case cần judge"* trong sổ hoãn, hạn D15 —
**chưa thoả**), `match_mode` land cùng bài test đầu tiên dùng nó. Ghi vào ask §5 để DE biết đây là
tiền đề đang thiếu, không phải AIE-2 quên.

---

# §3 — Work items: thứ tự là quyết định, không phải danh sách

Tổng: **8 khối P0 · 2 khối P1 · 3 món P2**. Thứ tự tối ưu cho *"cắt ở bất cứ đâu vẫn còn một
deliverable đứng được"*, không tối ưu cho *"làm phần thích trước"*.

| # | Khối | Ưu tiên | Ước lượng | Chặn ai | Điều kiện cắt |
|---|---|---|---|---|---|
| T0 | Kiểm nền + comment kế hoạch lên `#108` | **P0** | 30′ | mọi thứ | không cắt |
| T1 | Loader golden-set YAML + guard hardcode-path | **P0** | 1h15 | T2,T4 | không cắt — mọi thứ đứng sau |
| T2 | `compute_scorecard` | **P0** | 1h30 | T4,T5 | không cắt — deliverable chính |
| T4 | `EvalHarness.run` + `no-trace-no-proof` | **P0** | 1h30 | T6,T7 | không cắt — **ô DoD 1** |
| T5 | Render verdict thật + bỏ `todo:` | **P0** | 45′ | — | không cắt — **ô DoD 2** |
| T6 | Test độ nhạy ngưỡng — chứng minh *đổi threshold → verdict đổi* (**không** chốt/recalibrate ngưỡng) | **P0** | 45′ | — | không cắt — **ô DoD 3** |
| T7 | Viết lại money-shot + gỡ `xfail` + ADR | **P0** | 1h | — | không cắt — bỏ dở là suite ĐỎ |
| T10 | Tự gieo mutant + đóng ngày | **P0** | 1h15 | — | không cắt — `kit#74` |
| | **Cộng P0** | | **≈ 8h30** | | |
| T3 | PR `Aggregate.n_scored_citation` sang contracts | **P1** | 45′ | — (có đường lùi) | cắt → D17, T5 in dòng phụ |
| T8 | Spy khoá `DEC-D15-01` | **P1** | 30′ | — | cắt → D17 **kèm ghi lưới đang hở** |
| | **Cộng P0 + P1** | | **≈ 9h45** | | |
| T9a | `__all__` thiếu 3 hàm D15 | **P2** | 15′ | — | cắt → D17 |
| T9b | Bài hồi quy embedding (`DEC-08`) | **P2** *conditional* | 30′ | — | **tiền đề chưa thoả** — xem T9b |
| T9c | Dọn alias `_retrieved_citations` | **P2** *carry-over* | 15′ | — | **không làm trong D16** — xem T9c |
| | **Cộng tất cả** | | **≈ 10h45** | | |

**Vì sao phải chia tầng thay vì để một danh sách 10 dòng.** Cộng cả ba tầng ra **≈ 10h45** — không
phải một ngày làm việc. Một plan liệt kê 13 dòng ngang hàng sẽ được đọc thành *"phải xong hết"*, và
khi hụt thì phần bị bỏ là **phần đang gõ dở lúc hết giờ**, chứ không phải phần đáng bỏ nhất. Chia
tầng là để lúc 16:00 không phải quyết định gì nữa — quyết định đã có ở đây.

**Luật của các tầng:**

- **P0 (8 khối, ≈8h30)** — đóng đủ **3 ô DoD của AIE-2** + giữ suite xanh + giao được. Cắt bất kỳ
  khối nào ở đây là ngày **không đạt**, kể cả khi 3 ô DoD đã tick (T7 bỏ dở ⇒ suite đỏ; T10 bỏ ⇒
  `kit#74` tính 0 vì chưa bump).
- **P1 (2 khối, ≈1h15)** — trả nợ có hạn D16 nhưng **không** chặn ô DoD nào. Cắt được, **với điều
  kiện** ghi hạn mới + lý do vào sổ hoãn. Cắt im lặng thì không phải cắt, là quên.
- **P2 (3 khối, ≈1h)** — nợ nhỏ / có tiền đề ở người khác / cần sửa repo cha trước. **Mặc định là
  không làm trong D16**; làm chỉ khi P0 + P1 đã xong và còn giờ.

**P2 không phải "ít quan trọng hơn"** — T9b là thứ biến `DEC-08` từ một ghi chú thành một phép đo.
Nó ở P2 vì **tiền đề của nó nằm ở người khác** (case tranh chấp trong-fence, ask DE §5), không vì nó
nhỏ. Đây là hai lý do khác nhau và trộn chúng lại là cách một món quan trọng bị rơi mà trông như đã
được xếp hạng đúng.

## T0 · Kiểm nền + comment kế hoạch — **P0** (30′, làm đầu tiên)

1. Chạy đúng khối lệnh ở §1 — dán output thật vào note, **không** chép lại bảng §1.
2. Ghi lại con số baseline: suite hiện tại bao nhiêu `passed / skipped / xfailed`, và **0 XPASS**.
   Con số này là mốc so sánh cho mọi bước sau; không có nó thì không chứng minh được cái gì mới xanh.
3. Comment kế hoạch lên `#108`: 3 deliverable + 6 `DEC-D16-*` + **3 owner/thread (6 request)** của
   §5 + tầng ưu tiên P0/P1/P2. Ngắn.

> ⚠️ **Kiểm trạng thái submodule TRƯỚC KHI SỬA** (`GITFLOWS.md` §8 pitfall #1): sau `git submodule
> update --recursive` thì `packages/evalhub` đang ở **detached HEAD**. Sửa ở đó là cách commit biến
> mất. Bắt buộc: `cd packages/evalhub && git checkout main && git pull && git checkout -b aie-2/d16-<scope>`.

## T1 · Loader golden-set YAML — **P0, chặn mọi thứ** (1h15)

**File mới:** `src/studio_evalhub/golden_loader.py`

```python
def load_golden_set(path: Path, *, expect_ref: str) -> GoldenSet: ...
```

**Đỏ trước** (kỷ luật `test-discipline-mutation-ready`; `ImportError` **không tính** là đỏ, nên tạo
file rỗng có chữ ký trước, rồi mới viết assert).

### T1a · Unit — `tests/test_golden_loader.py`, **KHÔNG chạm `packages/kb`**

Bốn bài dưới đây dựng YAML bằng `tmp_path`, nội dung viết trong chính bài test. Không bài nào biết
golden-30 nằm ở đâu — nếu một bài unit đọc file của DE thì nó không còn là unit test của loader, nó
là test về việc file kia còn tồn tại, và nó sẽ đỏ vì lý do chẳng liên quan gì tới loader (DE đổi tên
file, submodule chưa init, chạy từ clone riêng evalhub).

| Bài | Khoá điều gì | Vì sao bài này tồn tại |
|---|---|---|
| `test_loader_doc_ref_mismatch_raises` | file có `golden_set_ref: X`, caller đòi `Y` ⇒ **raise** | bẫy tên file `-draft` vs ref `-v1` (§1) |
| `test_loader_khong_suy_ref_tu_ten_file` | ghi cùng nội dung ra **hai tên file khác nhau** ⇒ cả hai nạp được với cùng `expect_ref` | chứng minh ref đọc từ **nội dung**, không từ tên |
| `test_loader_thieu_field_raises` | bỏ `expected_section_role` của 1 case ⇒ `ValidationError` | fail-closed, không default âm thầm |
| `test_src_khong_hardcode_duong_dan_kb` | quét `src/studio_evalhub/*.py`, assert không chuỗi nào chứa `packages/kb` / `golden/` | guard của `DEC-D16-01` — bắt cả vi phạm **tương lai**, không chỉ chứng minh hôm nay sạch |

**Fixture bất đối xứng ngay ở tầng unit:** YAML dựng trong `tmp_path` để **3 trả-lời / 1 từ-chối** —
không 2/2. Tỷ lệ cân là chỗ một mutant đảo nhánh vẫn cho ra cùng con số.

### T1b · Integration — `tests/integration/test_golden_30_that.py`, chạy từ workspace

Hai bài này nạp **file thật của DE**, nên chúng là integration: cần workspace có `packages/kb` đã
init. Đường dẫn đến từ **fixture** (`golden_30_path`) resolve từ workspace root, **không** hằng số
trong `src/` — đúng `DEC-D16-01`: composition layer biết đường dẫn, `src/` không.

`skipif` khi file không tồn tại, kèm `reason` nói rõ *"cần `git submodule update --init packages/kb`"*
— **skip có lý do đọc được**, không phải một bài lặng lẽ biến mất.

| Bài | Khoá điều gì | Vì sao bài này tồn tại |
|---|---|---|
| `test_golden_30_that_dung_30_case_va_ref` | `len(cases) == 30` · `golden_set_ref == "callisto-golden-30-v1"` · **22 trả-lời / 8 từ-chối** | DoD ô 1 nói *"30 case"* — phải có một bài đối chiếu con số thật, không suy từ loader |
| `test_golden_30_expects_refusal_khop_nhan_cua_DE` | 8 id refusal đúng `HB-23`…`HB-30` | khoá `expects_refusal` (dẫn xuất) khớp ý định DE khai trong header file |

**Bài thứ hai là bài quan trọng nhất và dễ bỏ sót nhất.** `GoldenCase.expects_refusal` là **thuộc
tính dẫn xuất** (`golden_case.py:88-109`) — nó tính lại nhãn từ 4 field. Nếu cách DE hiểu "case âm"
lệch với công thức đó dù chỉ một case, thì **8 case bị chấm bằng luật của nhánh kia** mà không lỗi
nào nổi lên. Header golden-30 tự khai *"22 dương + 8 âm"* ⇒ có một nhãn độc lập để đối chiếu. Dùng nó.

**Vì sao tách hai tầng thay vì để chung một file:** loader phải hỏng-thì-đỏ **vì loader hỏng**. Trộn
hai loại vào một file thì một lần DE đổi tên file sẽ làm đỏ cả bài unit lẫn bài integration, và người
đọc suite không phân biệt được *"loader vỡ"* với *"dữ liệu đi chỗ khác"* — hai sự cố cần hai phản ứng
hoàn toàn khác nhau.

**Khai trước 3 mutant** (trước khi viết code, theo kỷ luật tự-gieo):

- M-L1: `expect_ref` bị bỏ qua (nạp bất kỳ file nào) → `..._ref_mismatch_raises` (T1a) phải đỏ
- M-L2: `ValidationError` bị nuốt thành `cases=[]` → `..._thieu_field_raises` (T1a) + `..._dung_30_case_va_ref` (T1b) phải đỏ
- M-L3: `expects_refusal` đọc **chỉ** trục T1 (bỏ T6) → `..._khop_nhan_cua_DE` (T1b) phải đỏ *(đây
  đúng là con bug thật đã xảy ra ở D-trước-23/07, ghi ở `golden_case.py:98`)*

⚠️ **M-L3 chỉ có lưới ở tầng integration.** Nếu chạy suite trong môi trường không có `packages/kb`
thì bài đó skip ⇒ mutant M-L3 **sống mà không ai biết**. Ghi vào note cuối ngày môi trường đã chạy
mutation là môi trường nào — cùng lớp với chuyện `77 passed` của D15 đo trong shell không có
`STUDIO_DATABASE_URL_ADMIN`.

**Kèm trong cùng PR:** `DEC-D16-02` — khai `pyyaml>=6.0` vào `packages/evalhub/pyproject.toml`.

## T2 · `compute_scorecard` — **P0**, deliverable chính (1h30)

**File:** `src/studio_evalhub/compute.py` (đang `raise`, `:30`)

**Luật tính, chốt trước khi gõ:**

| Ô | Công thức | Bẫy |
|---|---|---|
| `success_rate` | `k_success / n` với `n = len(results)` = **mọi** case | không loại refusal — refusal có `success` thật |
| `citation_accuracy` | `Σ acc / n_scored` với `n_scored` = **chỉ case nhánh trả-lời** | **`DEC-04`**: refusal có `1.0` là *quy ước vacuous-truth*, vào mẫu số là kéo điểm lên giả |
| `n_scored_citation` | `= n_scored` ở trên | `DEC-D16-03` |
| `gate.verdict` | `PASS` ⟺ `success_rate >= t_s` **AND** `citation_accuracy >= t_c` | `>=` không `>` — `DEC-04` đo đúng ca biên ở `0.9` |

**Vấn đề cấu trúc phải giải, không né được:** `compute_scorecard` nhận `list[CaseResult]`, mà
**`CaseResult` không mang cờ nhánh** (`contracts/scorecard.py:22-30`). Đây chính xác là câu ghi ở
`render.py:36-41`. ⇒ hàm **không thể tự** biết case nào là refusal.

Ba đường, chọn **(b)**:

| | Đường | Đánh giá |
|---|---|---|
| (a) | Suy từ `citation_accuracy == 1.0` | ❌ **CẤM** — `expected_citation == []` ở nhánh trả-lời cũng ra `1.0` (`harness.py:180`). Suy cờ ngữ nghĩa từ giá trị số = breakpoint `#14`, đúng lớp xanh-giả |
| (b) | Thêm tham số `n_scored_citation: int` do caller (harness) truyền vào | ✅ caller **biết** nhánh vì nó cầm `GoldenCase`. Chữ ký đổi = additive keyword-only, `compute_scorecard` chưa có consumer thật ngoài test |
| (c) | Thêm cờ vào `CaseResult` | ❌ đổi contract required-add = breaking, và không cần cho hôm nay |

**Đỏ trước — 6 bài:**
1. `test_compute_loai_refusal_khoi_mau_so_citation` — **bài chí tử**: dựng 10 case (2 refusal `1.0` +
   8 trả-lời `0.85`) ⇒ phải ra `0.85`, **không** `0.88`. Đây là bài dựng lại đúng con số `DEC-04`.
2. `test_compute_success_rate_dem_moi_case` — refusal **có** trong mẫu số của `success_rate`.
3. `test_compute_verdict_pass_o_dung_bang_nguong` — `success_rate == t_s` chính xác ⇒ `PASS` (`>=`).
4. `test_compute_verdict_fail_khi_chi_mot_truc_hut` — 2 chiều: hụt `success` / hụt `citation`.
5. `test_compute_n_scored_citation_bang_0_thi_none_va_fail` — golden toàn refusal ⇒ mẫu số 0.
   Không được ra `1.0` (vacuous PASS) và không được `ZeroDivisionError`.
   ⇒ **`citation_accuracy = None` + `verdict = "FAIL"`** — *không đo được thì không PASS được*.
   Luật này **đã chốt ở `DEC-D16-03`** (khối *"Ca mẫu số rỗng"*), kèm cả hệ quả contract
   (`Aggregate.citation_accuracy` nới `float | None` + vá reader `render.py:201`). **Không mở id
   mới cho ca này.**
6. `test_compute_khong_doi_results_dau_vao` — không mutate input.

**Khai trước 4 mutant:** M-C1 mẫu số citation dùng `len(results)` · M-C2 `>=` → `>` · M-C3 `AND` →
`OR` · M-C4 `n_scored == 0` ⇒ trả `1.0`.

## T3 · PR `Aggregate.n_scored_citation` sang `contracts` — **P1** (45′, **mở sớm trong ngày**)

Đây là món **duy nhất** cần người khác bấm nút ⇒ mở PR **ngay sau T2 xanh**, không để cuối ngày.
Xếp **P1** chính vì lý do đó: thời điểm merge không nằm trong tay AIE-2, nên không ô DoD nào được
phép treo vào nó.

- Sửa `contracts/src/studio_contracts/scorecard.py:46-50`, **hai field trong cùng PR** (`DEC-D16-03`):
  `n_scored_citation: int | None = None` và nới `citation_accuracy: float | None`.
- **Vá reader trong cùng thay đổi:** `render.py:201` đang `f"{...:.2f}"` ⇒ `TypeError` với `None`.
  Đây là điều kiện để `DEC-01` cho phép không bump, không phải việc dọn sau.
- Docstring theo khuôn `recipe_hash` (`scorecard.py:71+`): *field này trả lời câu gì*, *luật consumer*,
  *gap đã biết* — không phải một dòng chú thích.
- **Dán lệnh đếm reader vào PR body** (hình thức của `DEC-01`):
  ```bash
  grep -rn "\.citation_accuracy\b" packages apps scripts tests | grep -v "\.venv"
  ```
- Ping 1 approval. Không @ mentor.

**Đường lùi nếu PR không merge kịp trong ngày** (ghi trước, không ứng biến): `compute_scorecard` vẫn
**tính** `n_scored` và vẫn trả `Scorecard` đúng; chỉ phần **ghi vào `Aggregate`** bị hoãn, và
`render_scorecard` in mẫu số dưới dạng dòng phụ thay vì đọc từ field. Deliverable D16 **không** phụ
thuộc PR này merge — chỉ chất lượng biểu diễn phụ thuộc. Ghi rõ trạng thái vào note cuối ngày thay vì
để nó trông như đã xong.

## T4 · `EvalHarness.run` → `Scorecard` + `no-trace-no-proof` — **P0**, ô DoD 1 (1h30)

**File:** `harness.py:211` (đang `raise`)

**Chữ ký mới, theo hợp đồng đã khoá ở `DEC-D16-01`:**

```python
async def run(
    self,
    agent_id: str,
    golden_set_ref: str,
    *,
    golden_set_path: Path,          # bắt buộc — caller/composition root truyền, KHÔNG default
    runner: AgentRunner,
    tenant_ids: Mapping[str, UUID],
) -> Scorecard: ...
```

Thân hàm gọi `load_golden_set(golden_set_path, expect_ref=golden_set_ref)` — tức `golden_set_ref`
vừa là khoá tra cứu vừa là **assert nội dung file**, không có chỗ nào để hai thứ lệch nhau âm thầm.
`runner` + `tenant_ids` tiêm vào giống `run_smoke:219-225` (seam đã có, không phát minh mới).

Ghép ba thứ đã có: `load_golden_set` (T1) → vòng lặp giống `run_smoke:237-248` → `compute_scorecard`
(T2, truyền `n_scored_citation` đếm từ `case.expects_refusal` — caller **biết** nhánh vì nó cầm
`GoldenCase`, đúng đường (b) đã chọn ở T2).

**Trả nợ `DEC-05` trong đúng khối này** — sổ hoãn ghi *"Hiện thực `no-trace-no-proof` ở tầng
`run_smoke`/`EvalHarness.run`"*, hạn D16. Luật đúng đã được quyết và **không** phải là *"citation rỗng
⇒ FAIL"*:

> **`CaseRun.events == []` ⇒ case FAIL**, bất kể `answer` nói gì. Không có trace quan sát được thì
> không chứng minh được gì.

Cưỡng chế ở **tầng giữ `events`** (vòng lặp trong `run`/`run_smoke`), **không** trong `score_case` —
`score_case` chỉ nhận `list[str]` nên **cấu trúc mà nói** không phân biệt được *"chưa có run"* với
*"có run, không trích gì"* (`DEC-05`, và `score_case` có 3 consumer ngoài quadrant nên chữ ký không đổi).

**Đỏ trước — 5 bài:**
0. `test_run_khong_co_golden_set_path_thi_TypeError` — gọi `run()` thiếu `golden_set_path` ⇒ lỗi ngay
   ở chữ ký. Bài rẻ nhưng nó là thứ giữ `DEC-D16-01` khỏi bị "tiện tay" thêm default sau này.
1. `test_run_tra_scorecard_30_case` — `len(scorecard.results) == 30`, `golden_set_ref` khớp.
   **Integration** (nạp golden-30 thật, cùng fixture `golden_30_path` của T1b); 4 bài dưới là unit
   với golden-set dựng trong `tmp_path`.
2. `test_run_no_trace_no_proof_case_fail` — 1 case có `events=[]` ⇒ case đó `success=False`, **kể cả
   khi answer đúng** (bất biến cưỡng chế: khoá cả ca "answer đúng" để không ai nghĩ nó tình cờ).
3. `test_run_van_phan_biet_no_trace_voi_refusal_khong_trich` — F02 oracle (GUIDE-C `:592`): refusal
   có **1 event, 0 citation** ⇒ **PASS**. Đây là bài phân biệt hai thứ mà luật cũ trộn lẫn.
4. `test_run_recipe_hash_none_van_dung_scorecard` — `recipe_hash` chưa có producer (`DEC-03`), `None`
   là giá trị đúng hôm nay; fail-closed nằm ở **consumer** publish, không ở đây.

**Bài 3 là bài dễ nhất để làm sai và khó nhất để phát hiện.** Nó và bài 2 khác nhau đúng **một
event**, và luật sai sẽ làm cả 8 case refusal của golden-30 đỏ oan — rồi `success_rate` tụt còn
`22/30` và ai đọc sẽ kết luận recipe tệ, chứ không kết luận bộ chấm sai.

## T5 · Render verdict thật — **P0**, ô DoD 2 (45′)

`render_scorecard` (`render.py:165`) đã có sẵn hình dạng đủ ô — D12 khoá trước cho đúng ngày này.
Việc hôm nay:

- Bơm `Scorecard` **thật** vào nhánh không-`None` ⇒ `todo:` biến mất **vì có số thật**, không vì ai
  xoá chữ.
- Thêm dòng `aggregate.n_scored_citation` (nếu T3 merge) — hoặc dòng phụ *"mẫu số citation: 22/30 (đã
  loại 8 refusal)"* nếu chưa.
- **Gỡ / viết lại** `_AGGREGATE_NOT_RECOMPUTABLE` (`render.py:36-41`): chú thích đó nói *"nợ có chủ:
  AIE-2, hạn D16"* — hôm nay là D16. Nợ trả rồi thì chú thích phải đổi, không để nguyên một câu tự mô
  tả là chưa làm.
- **Không đụng** nhánh `scorecard is None` và các test `todo:` của nó: trạng thái "chưa có scorecard"
  vẫn tồn tại thật (recipe chưa chạy eval) ⇒ khung trống vẫn đúng.

**Đỏ trước:** `test_render_scorecard_that_khong_con_todo` + `test_render_khung_trong_van_giu_todo`
(cặp, để không ai "sửa" bằng cách xoá luôn nhánh trống).

## T6 · Test độ nhạy ngưỡng — **P0**, ô DoD 3 (45′)

**T6 là bài test chứng minh DoD, KHÔNG phải nhiệm vụ chốt hay recalibrate ngưỡng.** Thứ phải xong ở
đây là *"đổi threshold → verdict đổi"* chứng minh được bằng code. Ngưỡng `0.9/0.95`
(`builder.py:169,242`) **giữ nguyên trong D16** — T6 không đổi một con số nào của nó.

DoD: *"đổi threshold → verdict đổi"*. Chứng minh bằng **test**, không bằng ảnh chụp màn hình.

- `test_doi_threshold_thi_verdict_doi`: **cùng một** `list[CaseResult]`, chạy `compute_scorecard`
  hai lần với hai bộ ngưỡng ⇒ `PASS` rồi `FAIL`. Đây là bài chứng minh gate có răng.
- `test_verdict_doi_o_dung_hai_phia_cua_nguong`: ngưỡng đặt ngay tại điểm đo ⇒ `PASS`; nhích lên
  `+0.01` ⇒ `FAIL`. Bài này khoá luôn `>=` (M-C2).

**Rồi mới đo thật** trên golden-30, in bảng — đây là **thu thập số liệu**, không phải bước chốt:

| Ngưỡng `success` | Ngưỡng `citation` | verdict | ghi chú |
|---|---|---|---|
| 0.90 | 0.95 | ? | mặc định `builder.py:169` — **giữ nguyên** |
| … | … | … | 3–4 dòng, số thật |

**Nếu golden-30 cho thấy cần recalibrate: ghi số vào sổ hoãn, KHÔNG tự đổi ngưỡng trong D16.** Một
ngưỡng bị hạ xuống trong cùng ngày đo được điểm không phân biệt được với việc chỉnh cho vừa số, và
người đọc scorecard sau này không có cách nào biết thứ tự hai việc đó. Số liệu là deliverable của
T6; quyết định về ngưỡng thì không.

Nếu số ra FAIL với `0.9/0.95` thì **ghi FAIL và để FAIL** — đó là dữ liệu, không phải thất bại của
ngày, và nó chính là dòng bằng chứng để đề xuất recalibrate ở ngày sau (ask SWE ⑤, §5). Số đo trục
`citation_accuracy` ghi kèm nhãn **`TẠM`** vì `DEC-08` (trục này đang đo fence chứ không đo truy
xuất); gỡ nhãn khi T9b xanh — T6 **không chờ** T9b.

## T7 · Viết lại money-shot + gỡ `xfail` + ADR — **P0** (1h)

Theo `DEC-D16-04`. Ba việc, và **việc 1 lớn hơn hai việc kia cộng lại**:

### 1 · Cơ chế tạo FAIL — deterministic, không LLM

Bài phải chứng minh `verdict == "FAIL"` **bằng code chạy được**, nên nguồn FAIL phải tất định. Dùng
đúng seam đã có, không dựng gì mới:

> **`StubAgentRunner` nạp bằng một map "cố tình sai", sinh từ chính golden-set.**
> `StubAgentRunner` (`agent_runner.py:98`) khoá theo `(query, tenant_id)` và raise `LookupError` khi
> thiếu fixture — tức nó **đã** tất định và **đã** fail-closed. Chỉ cần một helper dựng map:

```python
def _bad_runner(golden: GoldenSet, tenant_ids: Mapping[str, UUID]) -> StubAgentRunner:
    """Runner trả câu SAI có chủ đích cho MỌI case — nguồn FAIL tất định của money-shot.

    Hai nhánh sai theo hai kiểu khác nhau, để verdict FAIL không phụ thuộc một luật chấm duy nhất:
      - case trả-lời  → answer KHÔNG chứa cụm `expected`, refused=False  ⇒ success=False
      - case từ-chối  → answer trả lời thật (refused=False)              ⇒ success=False
    """
```

**Ba ràng buộc của helper này, mỗi cái chặn một kiểu FAIL sai lý do:**

| Ràng buộc | Vì sao |
|---|---|
| Mỗi `CaseRun` mang **đúng 1 trace event**, không phải `events=[]` | `events=[]` sẽ làm case FAIL vì luật `no-trace-no-proof` (T4), **không** vì answer tệ. Bài sẽ xanh vì lý do khác với điều nó khẳng định — đúng lớp xanh-giả |
| Answer là câu **trọn vẹn, đọc được**, chỉ sai nội dung (vd trả `"5 ngày làm việc"` khi `expected` là `"3 ngày làm việc"`) | Chuỗi rỗng/`None` sẽ khiến bài đỏ ở tầng parse chứ không ở tầng chấm |
| **Không** đụng `instructions` của recipe | *"Sửa instructions tệ"* là mô tả demo bước 7 ở tầng UI; ở tầng test thì thứ quan sát được là **output**, và `Recipe.instructions` là bút SWE (`R-SPEC A4`) |

**Không dùng LLM thật, không dùng `LLMJudge`** — `judge.py` còn là spec đến D18, và một bài money-shot
phụ thuộc LLM là một bài không tái lập được. Toàn bộ đường FAIL đi qua `_contains_phrase` + luật
refusal, cả hai đều thuần và tất định.

**Assert của bài — bốn dòng, không phải một:**

```python
assert scorecard.gate.verdict == "FAIL"              # money-shot INV-6
assert scorecard.aggregate.success_rate == 0.0       # FAIL vì answer sai, không vì thiếu trace
assert len(scorecard.results) == 30                  # đã chạy hết bộ, không dừng sớm
assert all(len(r.actual) > 0 for r in scorecard.results)  # answer trọn vẹn, không rỗng
```

Ba dòng sau là thứ phân biệt *"gate chặn vì recipe tệ"* với *"gate chặn vì harness hỏng"*. Chỉ assert
dòng đầu thì một `EvalHarness.run` vỡ hoàn toàn cũng cho bài này xanh.

**Bài đối trọng, cùng lúc:** `test_gate_passes_on_good_recipe` — cùng golden-set, runner trả answer
**đúng** ⇒ `verdict == "PASS"`. Không có nó thì `test_gate_blocks_on_fail` không phân biệt được *"gate
chặn đúng"* với *"gate chặn mọi thứ"*, và một `verdict = "FAIL"` hằng số sẽ xanh cả bài.

### 2 · Gỡ marker

`xfail(strict=True)` gỡ **hẳn**, không đổi `strict=False`. Chạy, xác nhận xanh **vì code**.
`golden_set_ref="golden-set-eval-1"` và `agent_id="agent-bad-instructions"` hiện tại **không tồn
tại** — thay bằng golden-set thật + `golden_set_path` (chữ ký mới ở T4).

### 3 · ADR

`docs/decisions/` — *"vì sao gỡ, assert đã đọc lại chưa, cái gì thay thế lưới cũ"*. Câu trả lời cho
vế thứ ba là bài đối trọng ở trên: lưới cũ (`strict=True`) canh *"seam chưa xong"*; lưới mới canh
*"gate có phân biệt PASS/FAIL hay không"*.

**Kiểm chéo bắt buộc:** `test_harness_judge_compute_not_implemented` (`test_eval_gate.py:59`) khẳng
định **cả ba** seam raise. T2+T4 làm **hai** trong ba hết raise ⇒ **bài này sẽ ĐỎ**, đúng như thiết
kế. Sửa đúng cách là **thu hẹp** nó về `LLMJudge.judge` (seam duy nhất còn là spec, hạn D18) và ghi
lại việc thu hẹp — **không** xoá bài. Xoá là mất cái lưới bắt "stub một giá trị giả" cho seam còn lại.

## T8 · Spy khoá `DEC-D15-01` — **P1** (30′)

Sổ hoãn: *"Khoá lại 'render không tự tính' bằng spy, không dựa `raise`"*, hạn D16.

Hôm nay `test_render_case_KHONG_goi_compute_scorecard` xanh **chỉ vì** `compute_scorecard` đang
`raise` — mutation `M8` bị bắt bởi tác dụng phụ, không bởi bài test. **T2 land là lưới đó biến mất
cùng ngày.** Thay bằng spy thật (`monkeypatch` một sentinel vào `render.compute_scorecard`, assert
0 lời gọi).

Đây là ví dụ sạch của một lưới **có hạn sử dụng** được khai trước và trả đúng hạn — nếu bỏ, không ai
biết cho tới lần refactor nào đó làm renderer tự tính và mọi test vẫn xanh.

**Vì sao P1 chứ không P0:** lưới hở **không** làm ô DoD nào sai và **không** làm suite đỏ. Nhưng nếu
cắt thì phải ghi đúng chữ vào sổ hoãn — *"`DEC-D15-01` từ hôm nay không còn lưới; `M8` sẽ sống"* —
chứ không phải *"dời T8 sang D17"*. Hai câu đó mô tả cùng một hành động nhưng chỉ câu đầu nói ra cái
giá.

## T9 · Nợ nhỏ đến hạn — **P2**, mặc định KHÔNG làm trong D16 (1h nếu làm)

Cả ba khối dưới đây có hạn D16, nhưng **không** khối nào chặn ô DoD hay làm suite đỏ. Mặc định là
**hoãn có ghi chép**; chỉ làm khi P0 + P1 đã xong và còn giờ. Cái phải làm hôm nay dù cắt cả ba: **ghi
đúng lý do hoãn + hạn mới** vào sổ hoãn.

**T9a — `__all__` (15′) · P2, cắt được.** `__init__.py:21-35` thiếu 3 hàm D15: `answer_from_trace` ·
`score_run_from_trace` · `render_run_cases`. Có consumer thật rồi (`workbench#19` phải gọi hàm
`_`-prefix). Thêm export + `render_run_cases` vào import block. Cắt được vì consumer **vẫn chạy**
(gọi tên `_`-prefix); cái mất là bề mặt công khai đúng, không phải chức năng.

**T9b — Bài hồi quy embedding (30′) · P2 *conditional*, `DEC-08`.** Sổ hoãn: *"embedding hằng số PHẢI
làm `citation_accuracy` tụt. Không có bài này thì DEC-08 chỉ là một ghi chú, không phải một phép đo."*

⚠️ **Chỉ làm nếu tiền đề thoả.** Bài cần golden-30 có **case tranh chấp trong fence** — ≥2 ứng viên
cùng `tenant` **và** cùng `section_role`, để ranking buộc phải chọn thật. Header golden-30 khai cặp
**chéo-tenant** (`HB-01/02`, `03/04`…), **không** khai tranh chấp **trong-fence**. Kiểm ở T0:

```bash
# đếm case chia sẻ cùng (tenant, expected_section_role) — proxy cho tranh chấp trong fence
.venv/bin/python -c "
import yaml, collections
cs = yaml.safe_load(open('packages/kb/golden/callisto-handbook-30-draft.yaml'))['cases']
c = collections.Counter((x['tenant'], x['expected_section_role']) for x in cs)
n = sum(v for v in c.values() if v >= 2)
print(f'{n}/30 case nằm trong nhóm (tenant, role) có ≥2 case — cần ≥10 theo DEC-08')
print(c)
"
```

**Đây là proxy, không phải phép đo thật** — nói ra thay vì để người đọc tưởng đã kiểm xong: cùng
`(tenant, role)` mới là điều kiện **cần**; điều kiện **đủ** là hai chunk cùng nhóm đó thật sự cạnh
tranh cho cùng một query, và cái đó chỉ đo được khi chạy retrieval. Nếu proxy đã dưới ngưỡng thì
kết luận được ngay là **chưa đủ**; nếu proxy đạt thì vẫn phải xác nhận với DE.

- **Đạt** ⇒ viết bài, giữ trong D16.
- **Không đạt** ⇒ **hoãn D17 kèm output lệnh trên dán vào sổ hoãn** (evidence, không phải lời), và ask
  DE ở §5. **Không** viết một bài luôn xanh vì không có case nào thử được nó — đó là thêm một ô
  `todo:` giả, đúng thứ `DEC-D12-02` cấm.

**T9c — Alias `_retrieved_citations` (15′) · P2 *carry-over*, KHÔNG làm trong D16.** Hạn D16, nhưng
consumer thật còn lại là `scripts/smoke_eval_d6.py:66,249` — **ở repo cha**. Xoá alias mà không sửa
consumer là làm vỡ `main` repo cha, đúng loại vỡ `workbench#4` từng gây.

⇒ **Chuyển thành follow-up hai bước, không phải một món D16:** (1) PR ở **kit** sửa 2 call-site sang
`citations_from_trace`; (2) PR ở **evalhub** xoá alias — **sau khi** (1) merge. Bước (1) là repo cha
nên nó là một PR riêng với vòng review riêng, không nhét vào ngày đã kín.

**Nó KHÔNG được là blocker của D16**, và cũng không được im lặng gia hạn: ghi vào sổ hoãn đúng chữ
*"chờ PR kit sửa call-site; hạn mới D17; chủ AIE-2"* — một hạn mới **có điều kiện lật đọc được**,
khác với dời hạn suông.

## T10 · Tự gieo mutant + đóng ngày — **P0** (1h15)

**Mutation (45′).** `kit#74`: *review không finding = 0 điểm*, mutation chéo 5 bug. Hôm nay code mới
nhiều nhất Sprint 2 ⇒ mặt tấn công lớn nhất. **Khai trước** đủ bộ mutant đã liệt ở T1/T2 (3+4) và
chạy. Mutant **sống** thì ghi vào `docs/mutations/` kèm bài vá — không sửa lặng.

Tự gieo **không thay** được gieo chéo: D15 đã đo — 1/3 lượt do người ngoài gieo, và finding `B2` là
bằng chứng điểm mù của người viết có thật. ⇒ mời một người gieo vào `compute.py`, nêu rõ *"lần cuối
gieo vào đâu, khi nào"* thay vì đưa bảng gợi ý.

**Đóng ngày (30′)** theo quy trình chuẩn:
1. Daily note → `docs/reports/daily-notes/2026-08-10-dholmes0207.md`, PR, merge.
2. Comment kết quả lên `#108` + close (nếu đủ DoD).
3. Bump con trỏ kit — **`kit#74` tính bằng fresh recursive clone**, nên chưa bump là chưa giao. D15
   mất đúng điểm này tới 11:03 hôm sau.
4. `git config user.email` đúng identity trước khi commit.

---

# §4 — Bảng nợ đến hạn D16: 9 món, đối chiếu với work item

Không món nào ở đây do người khác giao. Tất cả là hạn **tự đặt** trong decision-log / daily-note —
nên bỏ món nào cũng phải nói ra, không thể coi là ngoài scope.

| # | Món | Nguồn | Rơi vào | Ưu tiên |
|---|---|---|---|---|
| 1 | `compute_scorecard` hiện thực | `kit#108` · `render.py:8` | **T2** | **P0** |
| 2 | `Aggregate.n_scored_citation` | `DEC-04` + `DEC-S2-134-03` | **T3** | **P1** — cần người khác merge |
| 3 | `no-trace-no-proof` ở tầng `run` | `DEC-05` | **T4** | **P0** |
| 4 | Đo và đề xuất recalibrate ngưỡng sau golden-30 | sổ hoãn | **T6** | **P0** — **chỉ đo trong D16; recalibrate/chốt ngưỡng hoãn ngày sau** |
| 5 | Spy khoá "render không tự tính" | `DEC-D15-01` (lưới có hạn) | **T8** | **P1** |
| 6 | `__all__` thiếu 3 hàm D15 | daily-note D15 | **T9a** | **P2** |
| 7 | Bài hồi quy embedding | `DEC-08` | **T9b** | **P2** *conditional* — tiền đề chưa thoả |
| 8 | Dọn alias `_retrieved_citations` | sổ hoãn | **T9c** | **P2** *carry-over* — cần PR kit trước |
| 9 | `match_mode` optional | sổ hoãn | — | **hoãn D18** (`DEC-D16-06`), có lý do đo được |

**Đọc bảng này cho đúng — theo đúng tầng của §3:**

- **8 khối P0** — `T0` · `T1` · `T2` · `T4` · `T5` · `T6` · `T7` · `T10` ⇒ làm hết, không cắt.
- **2 khối P1** — `T3` · `T8` ⇒ làm nếu kịp.
- **3 khối P2** — `T9a` · `T9b` · `T9c` ⇒ mặc định không làm trong D16.

Chiếu sang 9 dòng nợ ở bảng trên: món 1·3·4 rơi vào P0; món 2·5 vào P1; món 6·7·8 vào P2; món 9 đã
quyết hoãn D18. Tức bảng nợ D16 **sẽ không sạch** cuối ngày, và đó là kết quả đã lường trước chứ
không phải trượt. Điều kiện là mỗi món chưa trả phải có **hạn mới + điều kiện lật đọc được** trong
sổ hoãn.

**Ba món có hạn D16 nhưng KHÔNG phải của AIE-2**, ghi để không tự nhận nhầm:

| Món | Chủ | Ghi chú |
|---|---|---|
| `.env.example` ở gốc kit | **AIE-1** | D15 từng ghi nhầm là vô chủ — CODEOWNERS gốc kit là `@TranBaDat2607` |
| Luật chung cho *`ts` trùng có phải đảo không* (3 bề mặt 3 luật) | **`#104`** cả nhóm | AIE-2 nêu, không tự quyết |
| §3 bảng lệch wireframe → gửi `#102` | AIE-2 | **còn nợ thật** — `DEC-D15-03` giao mới một nửa. 15′, làm trong T0 |

---

# §5 — Ask gửi ai, nguyên văn — **3 owner/thread · 6 request**

| Owner / thread | Request | Chặn gì |
|---|---|---|
| DE `@DongAnh2704` | ① xác nhận đã nhận golden-30 *(không phải request)* · ② `DEC-08` tranh chấp trong-fence · ③ ≥3 case cần judge | ② chặn **T9b** · ③ chặn `match_mode` (D18) |
| SWE `@Dozyboy` | ④ `golden_set_ref` → `callisto-golden-30-v1` · ⑤ ngưỡng `0.9/0.95` · ⑥ §3 bảng lệch wireframe → `#102` | ④⑤ chặn `#107`, **không** chặn D16 của AIE-2 · ⑥ nợ `DEC-D15-03` |
| AIE-1 `@TranBaDat2607` | ⑦ thông báo `#106` không chặn nhau + nhắc breakpoint `#14` | không chặn gì |

**Sáu request đánh số ②–⑦** (① là xác nhận đã nhận, không đòi ai làm gì). **Không request nào chặn ô
DoD của AIE-2 hôm nay** — đó là kết luận đáng giá nhất của bảng: nếu cả ba thread im lặng cả ngày,
P0 vẫn chạy hết.

**Gửi DE (`@DongAnh2704`) — 1 xác nhận + 2 hỏi:**

> 1. Golden-30 đã nhận và đã parse: 30 case, 22 trả-lời / 8 từ-chối (`HB-23`…`HB-30`), shape khớp
>    `GoldenCase` 8 field, 0 case trả-lời có `expected_citation` rỗng. Cảm ơn — nó vào thẳng harness
>    được, không phải sửa gì.
> 2. Hai yêu cầu từ sổ hoãn D15 chưa thấy trong bộ này, hỏi để biết là chưa làm hay là làm rồi mà
>    chưa khai: (a) **`DEC-08`** — *≥1/3 case có ≥2 ứng viên cùng `tenant` + cùng `section_role`*, để
>    ranking buộc phải chọn thật. Không có nó thì `citation_accuracy` đang đo **fence**, không đo
>    **truy xuất** (null control: vector hằng số vẫn `recall@1 = 6/6`), và bài hồi quy embedding
>    không viết được. Đã tự đếm proxy `(tenant, expected_section_role)` trước khi hỏi — kết quả đính
>    kèm; nếu proxy đạt thì vẫn cần xác nhận vì cùng nhóm chưa chắc là cùng cạnh tranh cho một query.
>    (b) **≥3 case cần judge** — đây là tiền đề của `match_mode`, đang hoãn D18 vì 0/30 case cần judge.

**Gửi SWE (`@Dozyboy`) — 3 việc:**

> 1. `#107` ghi *"`golden_set_ref` + `scorecard_threshold` trỏ đúng golden-set AIE-2 dùng"*. Ref đúng
>    là **`callisto-golden-30-v1`** (đọc từ trong file, **không** phải tên file
>    `callisto-handbook-30-draft.yaml`). Mặc định hiện tại ở `builder.py:106,241,255` còn là
>    `callisto-smoke-5-v0`.
> 2. Ngưỡng `0.9/0.95` (`builder.py:169,242`): số đo bộ 5/bộ 10 cho thấy **một recipe tốt cũng FAIL
>    cả hai trục**. Sẽ đo trên golden-30 hôm nay và gửi bảng số trước khi đề xuất đổi — không đổi
>    trước khi có số.
> 3. Nốt nửa còn lại của `DEC-D15-03`: §3 bảng lệch wireframe D12 ↔ `TraceViewer.tsx` (5 dòng), gửi
>    vào `#102`.

**Gửi AIE-1 (`@TranBaDat2607`) — 1 việc:**

> `#106` (30 case deterministic) là điều kiện của đường **chạy thật** end-to-end, không phải điều kiện
> của deliverable AIE-2 hôm nay (đường `StubAgentRunner` đủ để đóng 3 ô DoD). Nên không chặn nhau.
> Nhắc lại breakpoint `#14` hạn D17: `refused = not citations` cho **dương-tính-giả** — câu bịa trọn
> vẹn mà quên đóng ngoặc ⇒ `citations=[]` ⇒ `refused=True` ⇒ case PASS dù agent đã bịa.

*(Không @ mentor. Merge gate là **1 approval từ bất kỳ collaborator `write`** — đo được ở `kb#16`
07/08; dòng comment đầu file CODEOWNERS nói ngược và không khớp protection đang chạy.)*

---

# §6 — Rủi ro đã biết

| # | Rủi ro | Dấu hiệu sớm | Phản ứng đã định |
|---|---|---|---|
| R1 | **Xanh-giả ở `aggregate`** — mẫu số citation gồm cả refusal ⇒ điểm cao giả, một bản đáng FAIL lại PASS | `citation_accuracy` trên golden-30 cao bất thường (> 0.9 ngay lượt đầu) | Bài T2#1 là bài chí tử, viết **trước** code. Đối chiếu tay: 22 case, không phải 30 |
| R2 | **PR contracts không merge kịp** (món duy nhất cần người khác) | 14:00 chưa có approval | T3 là **P1** đúng vì lý do này — đường lùi ở T3, không ô DoD nào phụ thuộc; ghi trạng thái thật vào note |
| R3 | **T7 nổ dây chuyền** — gỡ `xfail` làm `test_harness_judge_compute_not_implemented` đỏ | suite đỏ ngay sau T4 | Đã biết trước, đã định cách xử (thu hẹp về `LLMJudge.judge`, không xoá bài) |
| R4 | **T9b không viết được** vì golden-30 thiếu case tranh chấp trong fence | lệnh đếm proxy ở T0 | **P2 conditional** — hoãn D17 kèm **output lệnh** dán vào sổ hoãn, ask DE ②. Không viết bài luôn xanh |
| R4b | **Nhồi cả 10 khối vào một ngày** ⇒ P0 bị gõ vội, T10 (mutation + bump) bị bóp | 15:00 mà T6 chưa xong | Tầng P0/P1/P2 ở §3 tồn tại đúng để không phải quyết lúc 16:00. Cắt từ P2 lên, không cắt phần đang gõ dở |
| R5 | **Cám dỗ chỉnh ngưỡng cho vừa số** | lý do viết ra được chỉ là *"để nó PASS"* | Luật tự áp ở `DEC-D16-05`. Ghi FAIL và để FAIL |
| R6 | **Không bump con trỏ kit** ⇒ fresh clone không thấy gì ⇒ `kit#74` tính **0** | 17:00 chưa có PR bump | D15 đã mất điểm đúng chỗ này (bump land 11:03 **hôm sau**). Bump là một mục trong T10, không phải việc thừa |
| R7 | **Sửa ở detached HEAD** ⇒ commit biến mất | `git status` trong submodule in `HEAD detached` | T0 bước cuối. `GITFLOWS.md` §8 pitfall #1 |
| R8 | **Tham chiếu treo** — trích `DEC-D16-0x` trước khi bản ghi tồn tại | grep id trong code mà không có trong decision-log | Đúng lỗi D15 (3 id treo suốt một ngày, 8 chỗ trích). Ghi §2 vào decision-log **trước** khi land code |

---

# §7 — Định nghĩa "xong" cho D16

**Ô DoD (`#108`) — chỉ tick ô của AIE-2:**

- [ ] **Eval harness v1 chạy 30 case** — `EvalHarness.run` trả `Scorecard` với `len(results) == 30`,
      case nạp từ file thật của DE qua loader, có test khoá.
- [ ] **scorecard render success + citation + verdict** — `render_scorecard` in số thật, `todo:` biến
      mất **vì có số**, mẫu số citation nói rõ đã loại 8 refusal.
- [ ] **đổi threshold → verdict đổi** — test cùng `results`, hai bộ ngưỡng, `PASS` → `FAIL`.
- [ ] *(không tick)* golden-set 30 có nhãn — ô của DE (`#105`), đã giao.

**Điều kiện chất lượng — thiếu bất kỳ dòng nào thì ngày chưa xong, dù 3 ô trên đã tick:**

- [ ] **8 khối P0 xong đủ**: T0 · T1 · T2 · T4 · T5 · T6 · T7 · T10.
- [ ] Mọi bài test mới **đỏ trước** khi có code (`ImportError` không tính là đỏ).
- [ ] **Unit test loader không chạm `packages/kb`** — bài `test_src_khong_hardcode_duong_dan_kb` xanh,
      và mọi bài đọc golden-30 thật nằm ở tầng integration với `skipif` có `reason` đọc được.
- [ ] Bộ mutant **khai trước**, đã chạy, mutant sống có bài vá — ghi ở `docs/mutations/`. Ghi rõ
      **môi trường chạy mutation** (M-L3 chỉ có lưới khi `packages/kb` đã init).
- [ ] **Đúng 6** `DEC-D16-*` (01…06) trong `docs/decisions/scorecard.md` **trước** khi code tương ứng
      land. **Không** có `DEC-D16-07` — ca mẫu số rỗng nằm trong `DEC-D16-03`.
- [ ] `test_gate_blocks_on_fail` xanh **vì code** qua `_bad_runner` tất định (không LLM), có bài đối
      trọng `test_gate_passes_on_good_recipe`; ADR gỡ marker đã viết.
- [ ] 9 món nợ §4: mỗi món **đã trả** hoặc **hoãn kèm lý do đo được + chủ + hạn mới**. Không món nào
      im lặng trôi. *(Lường trước: 3 món P2 sẽ hoãn — hoãn có ghi chép là đạt, hoãn im lặng là không.)*
- [ ] Suite: `0 XPASS`, và số `passed` lớn hơn baseline T0 **một lượng giải thích được**.
- [ ] Daily note + comment `#108` + **con trỏ kit đã bump** — chưa bump là chưa giao (`kit#74`).
- [ ] 0 món vô chủ trong bảng hoãn cuối ngày, và **kiểm lại chính bảng vừa sửa** (D15: hai commit
      liền nhau cùng tạo một owner-không-thật; cái khó không phải biết luật mà là kiểm lại).

**Nếu phải cắt — cắt từ tầng thấp lên, không cắt phần đang gõ dở:**

`T9c` *(đã mặc định không làm)* → `T9b` → `T9a` → `T8` → `T3`.

**Không bao giờ cắt 8 khối P0.** T1/T2/T4/T5/T6 là ba ô DoD; T7 bỏ dở làm suite ĐỎ (gỡ `xfail` mà
chưa viết lại money-shot); T10 bỏ thì `kit#74` tính **0** vì fresh clone không thấy gì. T0 bỏ thì
không có baseline để chứng minh cái gì mới xanh.
