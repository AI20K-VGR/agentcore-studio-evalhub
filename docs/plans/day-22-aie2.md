# Plan Day 22 — AIE-2 · Fixture replay golden-30: làm bước 6–7 tất định trước mốc Day-25 · Thứ Ba 18/08/2026

> **Issue:** không có đề bài rời theo ngày — `kit#167` chốt *"Sprint 3 không có đề bài rời theo ngày, việc hằng ngày nhóm tự chia"*. Neo về `kit#167` (bước 5→8) và `kit#170` (bảng tự soạn của nhóm).
> **Repo WRITE:** `agentcore-studio-evalhub` · `agentcore-studio-app` · kit READ
> **Vai:** bút của **bộ chấm**. Việc hôm nay không phải làm điểm cao hơn — nó là làm cho một con số **tái lập được**.

---

# Executive Summary

Ba thứ của buổi demo đang cùng đứng trên **một lượt gọi LLM sống**, và biên độ nhiễu của lượt đó đã
đo được là **±1 case**. Số đo D21 (golden-30, `o4-mini`, tiêm LLM trực tiếp vào `EngineAgentRunner`):

```text
                     fake        o4-mini     o4-mini + judge
nhánh từ-chối        0/8         6/8         5/8
nhánh trả-lời        20/22       16/22       20/22
tổng                 20/30       22/30       25/30   = 0.8333
citation_accuracy    0.9091      0.9091      0.9091  (n=22, giống hệt cả 3 cột)
gate.verdict         FAIL        FAIL        FAIL
```

Lượt 1 và lượt 2 cùng model, cùng prompt, cùng retrieval: nhánh từ-chối `6/8` rồi `5/8`; mẫu số judge
4 rồi 5 case; ổn định `HB-09`·`HB-14`·`HB-18`, lật `HB-10`·`HB-15`·`HB-22`.

⇒ **`22/30 → 25/30` không quy được cho judge**, và một lượt gọi sống trước mặt cấp trên là tung đồng
xu. Việc hôm nay đóng đúng chỗ đó: ghi một lượt thật rồi **phát lại**, giữ mọi tầng khác là bản thật.

---

## §1 · Ghi ở seam nào — và vì sao KHÔNG phải seam `AgentRunner`

`StubAgentRunner` replay được `CaseRun` sẵn có, nhưng nó thay luôn **interpreter · retrieval · trace** —
đúng những tầng buổi demo tồn tại để trình. Nên ghi ở seam thấp hơn: **`LLM.complete()`**
(`studio_contracts.protocols`).

Mọi thứ khác giữ bản thật (engine · `PgKbSearch` · `PgTraceWriter` · `EvalHarness` ·
`compute_scorecard`); chỉ lời gọi model được phát lại.

## §2 · Hình dạng fixture + ba quyết định đi kèm

```jsonc
{
  "meta": {"model": "o4-mini", "recorded_at": "…", "golden_set_ref": "callisto-golden-30-v1"},
  "calls": {
    "<sha256(prompt + NUL + json.dumps(kwargs, sort_keys=True))>": {
      "response": "…", "prompt_tokens": 812, "completion_tokens": 47
    }
  }
}
```

**DEC-D22-01 · Khoá = `sha256(prompt + "\0" + json.dumps(kwargs, sort_keys=True))`.**

Prompt một mình **không đủ**: `executors.py:351` gọi `complete(prompt, **kwargs)`, và `kwargs["model"]`
được tiêm từ `recipe.agent_config.model` (`:349-350`); recipe cũng khai được `params["kwargs"]`
(`:324`). Hôm nay mọi impl đều bỏ qua kwargs (`FixtureLLM:132` `del prompt, kwargs`; `GeminiProvider`
dùng `self._model`) nên hành vi không đổi — nhưng ngày một gateway đọc `kwargs["model"]`, *cùng prompt +
khác model* sẽ được phục vụ **cùng một response đã ghi**: một đáp án sai không có gì báo. Đưa kwargs vào
khoá thì lệch thành **miss ⇒ raise**, không thành câu trả lời im lặng.

Prompt đã chứa chunk đã truy xuất, nên nếu retrieval đổi thứ tự thì khoá cũng trượt. Đó là **tính
năng**: nó biến *"retrieval có tất định không"* từ một nghi ngờ thành một lần miss quan sát được.

*Về serialization, đã kiểm chứ không giả định:* `sort_keys` sắp **đệ quy** nên thứ tự khai không vào
khoá; `float` dùng repr ngắn nhất round-trip; `ensure_ascii` mặc định ⇒ escaping tất định. `Node.params`
là `dict[str, object]` (**không** validate giá trị), nên một recipe dựng bằng Python vẫn có thể nhét
`set`/`UUID`/object vào — khi đó `json.dumps` raise `TypeError`, và **`TypeError` đó được để thoát ra**,
không bọc, không coerce. **Cấm `default=str`**: `__repr__` mặc định mang địa chỉ bộ nhớ, đo 3 tiến trình
liên tiếp ra 3 khoá khác nhau ⇒ mọi replay ở tiến trình khác thành miss.

**DEC-D22-02 · Miss ⇒ `raise`, fail-closed.** Không rơi về `ExtractiveFakeLLM`, không gọi mạng. Rơi về
fake là đúng lớp xanh-giả đã bắt ở nhánh judge (`app#20`): chạy xong vẫn ra số, không ai biết số đó
đến từ đâu. Cùng luật `_doc_json` của `judge.py` — *đọc được nhưng không dùng được ≡ không đọc được*.

**DEC-D22-03 · Ghi cả token.** Trục `cost cùng-một-số` của demo phải giữ số thật; một replay chỉ trả
text sẽ làm bảng cost về 0 và ô đó **xanh mà rỗng**.

## §3 · Bốn task

### T1 · `studio_evalhub/replay.py` — `RecordingLLM` + `ReplayLLM`

Cả hai thoả `LLM` protocol. Chỉ phụ thuộc `studio_contracts.protocols` ⇒ không phạm layering
(`.importlinter`: evalhub → contracts hợp lệ), và `apps/studio` ở tầng trên import được.

**Vì sao không tái dùng `FixtureLLM`** (`engine/demo_stubs.py:116-146`, đã có bài fail-loud
`test_fixture_missing_fails_loud.py`): nó khoá theo `case_id` nên một case chỉ giữ được **một**
`response` — không chứa nổi cả prompt agent lẫn prompt judge của cùng case; nó không có phía ghi; và
nó ở `packages/engine`, bút AIE-1.

Bài: miss ⇒ raise · hit ⇒ trả **đúng byte** · ghi rồi đọc lại tròn vòng · fixture hỏng ⇒ raise chứ
không coi như rỗng · kwargs khác ⇒ khoá khác (ghim `DEC-D22-01`).

### T2 · Ghi fixture — **hai lượt**, không phải một

Chỗ dễ hỏng nhất của cả plan: bước *degrade → re-eval → BLOCK → rollback* **sinh prompt mới**
(instructions nằm trong prompt — `executors.py:336` `build_prompt(query, retrieved_chunks,
instructions)`) ⇒ một fixture chỉ có lượt gốc sẽ miss và vỡ **ngay giữa demo**. Ghi cả hai vào cùng
file:

| Lượt | Recipe | Vai trò trong demo |
|---|---|---|
| **A** | recipe gốc, **judge ON** | bước 6 → scorecard; bước 7 → publish nếu qua ngưỡng |
| **B** | instructions đã làm tệ | bước 7 → verdict FAIL → chặn + rollback về v1 |

Cùng lý do trên, A và B **không thể trùng khoá**: instructions đổi ⇒ mọi prompt đổi ⇒ không cần
namespace A/B, và thêm namespace là abstraction không có trigger.

**Ràng buộc thứ tự, mới sau `workbench#27` (chiều 18/08):** PR đó gộp hai bản `with_query` từng lệch
nhau ở `apps/studio` (`chat.py` bơm `query` vào **mọi** node `kb-retrieve`, `eval_adapter.py` chỉ bơm
node **đầu tiên**) thành `studio_workbench.recipe_ops.with_query`, và chọn semantics *mọi node*. Với
`create_recipe_d4` (đúng **một** node `kb-retrieve`) hai cách cho kết quả y hệt ⇒ golden-30 không đổi
số. Nhưng nếu canvas dùng cho demo có **≥2** node `kb-retrieve` thì prompt của các case sẽ đổi ⇒ mọi
khoá fixture miss. **Đếm số node `kb-retrieve` của canvas demo trước khi tốn key chạy T2**, và nếu nó
≥2 thì ghi fixture **sau** khi PR nối dây của SWE land, không phải trước.

Ghi lượt A với judge **ON** là bắt buộc, không phải tuỳ chọn: `judge.py:201` phát prompt riêng theo
template `_PROMPT` (`:45-51`), nên fixture ghi khi judge OFF sẽ **thiếu hẳn** những call đó và T3 sẽ
raise. Judge được hỏi **sau** khi case đã chấm và không đổi prompt của agent, nên bản ghi judge-ON là
**tập trên** của bản judge-OFF — một fixture phục vụ được cả hai chiều.

### T3 · Quy tác dụng judge — đóng ô `INV-4`

Phát lại **cùng** fixture A hai chiều `judge=None` / `judge=LLMJudge(...)`. Chênh lệch lúc đó là của
judge, không của nhiễu. Đây là phép đo mà note D21 **từ chối tuyên bố** vì chưa có fixture; giờ có.

**Dùng `cache_path`/`cap_path` tươi cho mỗi lượt replay.** `judge.judge()` đọc cache **trước** cap và
trước provider (`judge.py:191-194`), nên nếu cache của lượt ghi còn lại thì nhánh judge-ON trả lời từ
cache và **không chạm fixture** — vẫn tất định, nhưng tất định vì lý do khác với điều đang được đo.

### T4 · Đường để route dùng được — cần AIE-1

Đề xuất thêm `replay` làm một giá trị của `llm_provider` StrEnum trong `app#19`: một enum member + một
nhánh trong `build_llm()`, không phải cơ chế mới. Hỏi thẳng trên `app#19`. **Không chặn T1–T3.**

## §4 · Luật liêm chính — viết TRƯỚC khi chạy

**Ghi đúng lượt đầu tiên và giữ nguyên, bất kể điểm.** Chạy nhiều lượt rồi chọn lượt đẹp nhất chính là
*"hiệu chỉnh theo thứ mình muốn nhìn thấy"* mà `DEC-D20-03` cấm. Lượt A ra FAIL thì demo trình FAIL.

**Fixture làm số tái lập được, không làm số đẹp lên.** Ngưỡng chốt trước, lý do ghi trước.

## §5 · Rủi ro phải nêu ngay: bước 7 hiện KHÔNG tới được

**Cập nhật chiều 18/08 — lý do 409 vừa đổi, và đổi theo chiều làm rủi ro này sắc hơn.** `workbench#27`
(SWE) đã viết producer `recipe_hash(recipe)` = `sha256(recipe.model_dump_json(by_alias=True))`, nên
`publish()` sắp không còn từ chối vì *thiếu hash* nữa. Cổng chặn dịch từ `recipe_hash is None` sang
`gate.verdict == "FAIL"` — tức từ một lỗi hạ tầng thành **đúng con số của bộ chấm**.

Ngưỡng của recipe là `success 0.9` · `citation_accuracy 0.95` (`RunRequest` mặc định ·
`create_dynamic_recipe` · `DEC-D16-05`/`DEC-D17-04`). Số tốt nhất đo được là `0.8333` / `0.9091`.

⇒ Ở ngưỡng đang khai, lượt A ra **FAIL** ⇒ **không có `publish` thành công nào**. Và
`_reassert_last_published` là **no-op khi chưa từng publish** (`workbench/publish.py:167-173`) ⇒
*"BLOCK → rollback"* của bước 8 sẽ chạy nhưng **không rollback về đâu cả**.

Hai đường ra, cả hai đều cần quyết định của người khác, không tự chọn ở đây:

1. **Ngưỡng**: AIE-1 chốt `scorecard_threshold` kèm lý do ghi trước (ô đã có trong `kit#170`). Hạ ngưỡng
   để demo xanh là thứ `DEC-D20-03` cấm — nên lý do phải đứng độc lập với con số vừa đo.
2. **Seed một `v1` đã publish** trước buổi demo bằng một scorecard có thật đạt ngưỡng, để bước 8 có bản
   để quay về. Cần chủ `wb.recipes` (SWE) xác nhận đường seed không phá gate.

Nêu ở đây vì fixture **không sửa được** chuyện này — nó chỉ làm chuyện này **hiện ra ổn định** thay vì
lúc đỏ lúc xanh.

## §6 · DoD

- [ ] `ReplayLLM` miss ⇒ raise, có bài ghim.
- [ ] Chạy golden-30 replay **hai lần liên tiếp** ⇒ `Scorecard` bằng nhau **từng byte**. (Đo được vì
      `Scorecard` không mang field thời gian/danh tính run nào: `agent_id` · `golden_set_ref` ·
      `results` · `aggregate` · `gate` · `recipe_hash`.) Sau `workbench#27`, `recipe_hash` **không còn
      `None`** trên đường thật — phép so byte giờ phủ luôn field đó, và nó vẫn tất định vì
      `recipe_hash()` là hàm thuần trên recipe gốc (`frozen=True`, `query` đã gỡ) chứ không phụ thuộc
      lượt chạy.
- [ ] Fixture chứa **cả** lượt A và B; chạy trọn `publish → degrade → FAIL → chặn` không lần miss nào.
- [ ] Judge ON/OFF trên cùng fixture ⇒ số chênh lệch có nghĩa, ghi vào daily note.
- [ ] `use_fake_providers` mặc định **không đổi**; `pytest packages/evalhub/tests` không đổi số lượng
      ngoài bài mới (INV-4: CI không phụ thuộc model).
- [ ] Fixture **được commit** — clone tươi Day-25 phải có, không phụ thuộc máy ai.
- [ ] `ruff check` + `mypy` sạch.

## §7 · Ranh giới + ước lượng

Không sửa `harness.py` · `compute.py` · `judge.py`. Không đụng `build_llm()` (T4 là đề xuất, không phải
PR của plan này). Không đổi ngưỡng. Cache của judge là chuyện khác — khoá `(case_id, actual)`, không
phải prompt.

| Task | Ước lượng | Phụ thuộc |
|---|---|---|
| T1 | ~1h | — |
| T2 | ~45' (~60–65 call × 2 recipe) | key OpenAI, chạy **một** lần |
| T3 | ~30' | T1, T2 |
| T4 | — | AIE-1 (`app#19`) |
