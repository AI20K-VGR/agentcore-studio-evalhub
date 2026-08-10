---
id: studio.decision-log.scorecard
type: decision-log
contract: scorecard
pen: AIE-2 — Lưu Tiến Duy
freeze: FREEZE-READY   # chưa FROZEN — xem "Còn mở" bên dưới
---

# Decision-log — scorecard (AIE-2)

> **Chỗ đặt: repo của bút** (đây), không ở kit. Theo lần lặp cuối của
> [kit#130](https://github.com/AI20K-VGR/agentcore-studio-kit/pull/130) — *"kit stays pure index, no
> repo's content duplicated here"* — và khớp chỗ DE (`kb`) với SWE (`workbench`) đã đặt. Bản index
> cross-repo ở `kit:docs/decisions/README.md`.
>
> **Đổi chỗ hai lần trong ngày, ghi lại cả hai để không ai phải suy lại:** (1) ban đầu định gom một
> `kit:docs/decision-log.md` chung — bỏ vì kit#130 chốt 1 file/1 hợp đồng; (2) rồi đặt ở
> `kit:docs/decisions/scorecard.md` — bỏ vì kit#130 **closed** và lần lặp cuối chốt kit chỉ giữ index.
> Cả hai lần đổi đều là **theo team**, không phải đổi ý một mình.
>
> ---
>
> Khung nội dung theo [kit#130](https://github.com/AI20K-VGR/agentcore-studio-kit/pull/130) (@Dozyboy)
> và **ADR-D11-01** ([#84](https://github.com/AI20K-VGR/agentcore-studio-kit/issues/84)). File này là
> **bản tổng cross-repo**; chi tiết kỹ thuật + câu chữ clause nằm ở
> [`agentcore-studio-evalhub/docs/contracts/scorecard.v1.md`](https://github.com/AI20K-VGR/agentcore-studio-evalhub/blob/main/docs/contracts/scorecard.v1.md).
>
> **Về cách đánh id:** `recipe.md` dùng `DL-R*`. File này dùng `DEC-*` vì các id đó **đã được trích ở
> nhiều chỗ khác** trước khi có khung chung — trong `scorecard.v1.md`, trong `scorecard-v0.md` §3, và
> trong docstring test (`test_smoke_runner.py`). Đổi id bây giờ sẽ làm chết những chỗ trích đó.

## D11 · 2026-08-03

| # | Quyết định | Lý do | PR / bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-01** | Nới `required` → `optional` **KHÔNG bump** `SCHEMA_VERSION`, **điều kiện**: đếm được **0 reader giả định non-null**. Nếu > 0 ⇒ breaking cho reader dù guard payload xanh | `contracts/__init__.py:5-12` chỉ liệt kê **3** loại breaking (rename · removal · required-add) ⇒ ca này là **ca thứ tư**: *tương thích trên dây, KHÔNG tương thích với reader*. `test_freeze_guard.py:36` chỉ đo chiều required-add ⇒ cơ chế hiện có **không phát hiện** ca này. Đo: **0 reader / 4 constructor** toàn test fixture; `331 → 333 passed` đúng +2 test mới; mypy `110 file` không đổi | ADR-D11-02 · `grep -rn "\.judge\b\|judge=" packages apps scripts tests` | ✅ quyết (phần áp cho `judge`) · 🟡 clause chung chờ 4 bút, hạn D12 |
| **DEC-02** | `CaseResult.judge: Judge \| None = None`. `None` = *"case chấm KHÔNG qua LLM-judge"* — giá trị trung thực **duy nhất** trước S3. Hằng số `Judge(...)` bị **cấm** | `judge.py:6-9` cấm giá trị hằng; `agreement` đo *scorer có đồng ý với nhãn tay hay không*, nên với case exact-match FAIL nó **không xác định** — không phải 1.0, không phải 0. Điền 1.0 là bịa phép đo và **không phân biệt được** với judge thật đồng thuận 100% ⇒ hỏng âm thầm mọi aggregate trên `agreement` (INV-4). GUIDE-C `:855-887` | [contracts#1](https://github.com/AI20K-VGR/agentcore-studio-contracts/pull/1) (@Dozyboy mở, AIE-2 xác nhận với tư cách giữ bút) | 🟡 chờ merge |
| **DEC-03** | `Scorecard.recipe_hash: str \| None = None`, kèm luật consumer: publish coi `None` là *"không verify được ⇒ từ chối"* (**fail-closed**) ⇒ optional là đủ, **không** cần required-add | Ruling **D-24** (`02-MATRIX.md:284`): *"Add `recipe_hash` to `Scorecard`"*, owner AIE-2. Hôm nay giá 1 dòng; sau freeze giá 4 chữ ký. Điểm yếu nói thẳng: **land một field chưa có producer** — `Recipe` chưa có `version`/hash (`recipe.py:79-94`) dù `wb.recipe_versions` đã tồn tại (`workbench/.../schema.py:39`) | PR riêng (AIE-2) — **chưa mở tại thời điểm ghi dòng này** | 🔴 chưa mở PR |
| **DEC-04** | `citation_accuracy` nhánh từ-chối, **ba tầng**: per-case giữ `1.0` **là quy ước, có pin test** · aggregate **loại khỏi mẫu số** · render in `n/a` | Số: bộ 10 báo `0.90` vs thật **`0.833`** (+0.067; 3 case đã đỏ SC-04/07/09 vẫn góp `1.00`). Phép tính chí tử (GUIDE-C Q8): `10×1.0 + 20×0.85 = đúng 0.90` ⇒ với `>=` một bản **đáng FAIL** lại PASS ngay ngưỡng 0.9. Không đổi per-case: `SmokeResult.citation_accuracy` phải giữ `float` — 3 renderer `:.2f` sẽ `TypeError` với `None`; và quy ước vacuous-truth tồn tại **cả hai nhánh** (`harness.py:167`) | `test_refusal_citation_accuracy_is_pinned_convention_not_measurement` (mới, D11) · GUIDE-C §6.4.2 đòi pin, §9 ghi **chưa tồn tại** | ✅ quyết + pin xanh |
| **DEC-05** | `no-trace-no-proof`: invariant đúng là *"không có trace quan sát được ⇒ FAIL"*, **KHÔNG** phải *"citation rỗng ⇒ FAIL"*. Cưỡng chế ở **tầng giữ `events`**, không ở `score_case`. Chữ ký `score_case` **không đổi**. Hiện thực D16 | `score_case` chỉ nhận `retrieved_citations: list[str]` (`harness.py:145`) ⇒ **cấu trúc mà nói** không phân biệt được *"chưa có run"* vs *"có run, không trích gì"*; `tenant_scope_ok` phân biệt được **vì nhận `events`** (`harness.py:119-120`). Nguyên nhân là **tầng**, không phải cẩu thả. Luật cũ ngược oracle **F02** (GUIDE-C `:592`: *"refused, cited nothing ⇒ the case PASSES"*). Fixture `test_determinism.py:113` dựng ca từ-chối bằng `events=[_event([])]` — **một event, zero citation** = F02, không phải no-trace | xfail `test_smoke_runner.py` **đổi neo** sang `run_smoke` với `CaseRun.events == []`, giữ `strict=True` · docstring `test_refusal_success` sửa từ *"ghi hành vi hiện tại"* → *"khoá luật đúng"* | ✅ quyết · cặp test mâu thuẫn thành cặp đã-quyết |
| **DEC-06** | Chữ ký = **Approve trên PR** (xác thực GitHub); decision-log chỉ ghi **dấu vết**. **Bỏ** ý định làm bảng tự-điền trong file contract, và **bỏ** ý định làm `sig-<github-id>.md` per-người | Theo ADR-D11-01 + kit#130. Bảng tự-điền: ai sửa file cũng gõ được tên người khác. `sig-*.md` per-người: lập luận gốc của nó là *"một người gõ hộ 4 dòng thì `git log --format='%an'` ra một tên"* — tách theo **hợp đồng** (kit#130) đã giải quyết chính xác điều đó, nên `sig-*.md` thành **dư**. Xin thêm **một cột `<repo>@<sha>`**: chữ ký không nêu bytes nó ký thì là trang trí | ADR-D11-01 · kit#130 | ✅ theo team |
| **DEC-Q3** | `section_roles` resolve **server-side**, harness dựng phiên mang quyền rồi chạy case — **không** truyền `case.section_roles` thẳng vào `kb.search` | Chữ trong doc AIE-2 đã đúng (`golden_case.py:110-116`); phần còn thiếu là **code của người khác**: lỗ nằm ở recipe tự khai roles (`executors.py:138` đọc `node.params.get("section_roles")`), và `Recipe` là bút SWE | `scorecard-v0.md` §3 Q3 | 🟡 hoãn — chủ **SWE + DE**, hạn **D17** |
| **DEC-Q4** | **KHÔNG** promote `AgentRunner` lên `studio_contracts.protocols` hôm nay | Thêm seam thứ 4/5 vào layer đáy là **mở rộng bề mặt freeze đúng ngày đóng băng nó**; `AgentRunner` (`agent_runner.py:76`) chạy tốt như Protocol nội bộ và `lint-imports` đã `1 kept, 0 broken` ⇒ layering **không** đòi promote; adapter sống ở composition root `apps/studio`. Phương án bỏ: promote ⇒ 4/4 chữ ký cho **mỗi** lần đổi shape seam, trong lúc seam còn tiến hoá qua D14/D16 | `docs/mini-rfc/MRFC-2026-08-03-agentrunner-protocol-seam.md` (**PRE-WRITTEN**, cố ý chưa nộp) | 🟡 hoãn — chủ **AIE-2 + AIE-1**, hạn **D14** |
| **DEC-Q5** | `eval.golden_sets` (`schema.py:20-25`, bút AIE-2) là **nguồn sự thật**. DE **sinh + gán nhãn**, giao YAML ở `packages/kb/golden/`; AIE-2 **nạp**. `obs.golden_sets` bỏ | Lý do là **quyền**, không phải sở thích — và là Q-D của chính DE (`trace-event.v0.md:242`): *"`obs.golden_sets` nằm trong `apps/studio/` — không phải fence-lane của DE. DE điền bằng cách nào?"* Đáp: **không điền được**. Ranh giới: DE sở hữu **giá trị**, AIE-2 sở hữu **nơi lưu + loader** (§2.6). Loader hết blocker: `pyyaml>=6.0` khai tường minh `pyproject.toml:26` từ `kit#65` | `scorecard-v0.md` §3 Q5 · review trên [kb#10](https://github.com/AI20K-VGR/agentcore-studio-kb/pull/10) · **DE xác nhận CÓ** trên [evalhub#11](https://github.com/AI20K-VGR/agentcore-studio-evalhub/pull/11#issuecomment-5177279745) `2026-08-04 09:42Z` | ✅ **DE đã xác nhận (04/08)** — xem khối dưới bảng |
| **DEC-07** | Rút một tiền đề của chính AIE-2: leak-check mức UUID **KHÔNG** cần đổi contract | `scorecard-v0.md:335-337` viết *"cần `tenant_id` per-chunk → đổi contract → mini-RFC + 4/4 chữ ký"*. Đo lại: dữ liệu **đã có từ D5** ở `outputs["chunks"]` (`interpreter.py:265-268`; `KbSearchResultItem.tenant_id: UUID`), **4 consumer đang đọc**. Thiếu là **một dòng hợp đồng** (`trace-event.v0.md:77` khai `outputs` là *"⏸ hoãn S2"*), **0 bump, 0 mini-RFC**. Định giá quá cao làm việc bị hoãn vô cớ | `scorecard-v0.md` §2.8 (giữ cả câu sai + phần rút) | ✅ rút, có ghi lại |
| **DEC-08** | Khai vào hợp đồng (§3.1) rằng `citation_accuracy` đo **sức mạnh FENCE**, KHÔNG đo **sức mạnh TRUY XUẤT**, trên bộ golden hiện tại | Null control của **AIE-1** (`engine#15`), **AIE-2 đã tự tái lập** bằng `measure_chunk_embed.py --null`: vector hằng số **0 bit thông tin** đạt `recall@1 = 6/6` **bằng đúng** bag-of-words dim=8/256 thật; cột *"top1 không hoà"* = **0**. Nguyên nhân: fence tự quyết **4/6 case** (sau lọc `tenant_id`+`section_role` chỉ còn 1 ứng viên ⇒ ranking không quyết định gì), 2 case còn lại thắng nhờ hoà điểm + thứ tự sort. ⇒ metric **không phát hiện được hồi quy embedding**: gateway thật về mà embedding tệ hơn stub thì điểm vẫn `6/6`, tức một trục của gate `AND` **không có răng**, và ngưỡng `0.95` (`workbench:src/studio_workbench/builder.py:49` — **repo workbench, không phải evalhub**; trong evalhub `0.9/0.95` chỉ có trong test fixture) đo một thứ khác với thứ tên nó gợi ra. Ghi giới hạn vào freeze thay vì đợi sửa: một hợp đồng khai đúng thứ nó chưa chứng minh được thì **mạnh hơn** — không khai thì D16 sẽ có người đọc `0.95` là bằng chứng retrieval, đúng lớp **xanh-giả** với `refused` dương-tính-giả | [evalhub#6 comment](https://github.com/AI20K-VGR/agentcore-studio-evalhub/pull/6) (@TranBaDat2607) · [engine#15](https://github.com/AI20K-VGR/agentcore-studio-engine/pull/15) `docs/design-notes/aie1-day11.md` §3 · `scorecard.v1.md` §3.1 | ✅ đã khai vào hợp đồng |

## D15 · 2026-08-07

> **Ba id này đã bị trích ở 8 chỗ TRƯỚC khi có bản ghi** — `render.py:64,113`, `test_render_run_cases.py`
> (×4), `trace-viewer-delta-d15.md:10`. Tức suốt ngày D15 chúng là **tham chiếu treo**: ai lần theo
> `DEC-D15-03` sẽ không tìm thấy gì và có quyền kết luận là bịa ra lúc viết. Ghi bổ sung ở đây, và
> ghi luôn cả việc nó bổ sung muộn — xoá vết thì mất đúng phần đáng học.
>
> **Cả ba là quyết định TỰ CHỐT.** Từ 03/08 mentor không trả lời câu hỏi kiến trúc, nhóm tự quyết và
> tự viết ADR. Không có chữ ký thứ hai ở đây, và điều đó được nói ra chứ không giấu.

| # | Quyết định | Lý do | PR / bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-D15-01** | `render_run_cases` **hiển thị**, không **tính**. Nó nhận `list[SmokeResult]` caller đã chấm và không gọi sang tầng tính — cụ thể **không** gọi `compute_scorecard`, không dựng `Scorecard`, không quyết `gate` | Nối tiếp `DEC-D12-03`. Hai lý do tách nhau: (1) `compute_scorecard` là mốc **D16** (`kit#108`), land sớm làm `test_gate_blocks_on_fail` (`xfail(strict=True)`) **XPASS ⇒ FAIL**; (2) một renderer tự tính là một nguồn số **thứ hai** cho cùng một run — đúng lỗi `DEC-04` phần 1 mô tả, nơi cộng lại từ `results` ra `0.90` trong khi số thật là `0.833` | `test_render_case_KHONG_goi_compute_scorecard` · mutation **M8** (`self-render-d15.md` §2.2) | ✅ quyết · ⚠️ **lưới có hạn sử dụng**: M8 hiện bị bắt vì `compute_scorecard` đang `raise`, không phải vì suite phát hiện lời gọi. Khi `kit#108` hiện thực nó, bất biến này mất lưới ⇒ khoá lại bằng spy. Chủ AIE-2, hạn **D16** |
| **DEC-D15-02** | Bảng per-case in **`k/n` thô**, tuyệt đối **không** in tỷ lệ tổng, không `%`, không ngưỡng, không khoảng tin cậy. Hai mẫu số **tách rời**: `n_success` = mọi case · `n_citation` = chỉ case nhánh trả-lời | `DEC-S2-134-03` đòi tách `k_citation / n_citation_scored` và loại refusal trước đã, mà `Aggregate` hôm nay **chưa có chỗ** cho `n_scored_citation` (nợ có chủ: AIE-2, D16, xem `DEC-04`). In một tỷ lệ tổng khi mẫu số chưa tách là đúng lỗi `kit#134` mô tả: *chỗ hỏng không nằm ở probe, nằm ở bước từ `8/10` sang tám-mươi-phần-trăm*. `n = 0` ⇒ in `not-estimable`, **không** `0/0` — `0/0` vẫn mời người đọc chia một phép chia không tồn tại | `test_render_case_in_k_tren_n_tho_KHONG_in_ty_le_tong` (có assert `"%" not in out`) · `..._mau_so_citation_loai_refusal...` · `..._rong_la_not_estimable...` · mutation **M1/M3/M4/M5** | ✅ quyết + 4 mutant bắt |
| **DEC-D15-03** | Đọc *"playground-trace UX **ghép vào** viewer"* (dòng 🎯 `kit#103`) là **đối chiếu ra danh sách lệch hai chiều rồi giao cho chủ bề mặt**, KHÔNG phải AIE-2 dựng UI | Ba ràng buộc, không phải khẩu vị: (1) **quyền** — viewer là `#100` (DE), playground là `#102` (SWE); vào code người khác giữa Integration Friday là cách nhanh nhất để vỡ ngày của ba người; (2) **`kit#74`** chấm kỷ luật ranh giới quadrant, nên tự dựng UI là mất điểm chứ không được điểm; (3) **bề mặt web chưa tồn tại** — `apps/web/src` 11 file, 0 file nhắc `trace` (kiểm 07/08). Đối chiếu cần hai phía, nên phía đối chiếu được là `studio_kb.trace_reader.render_timeline` (D5, bút DE, đã merge và đọc đúng `obs.trace_events` mà bộ chấm vừa đọc) | `docs/design-notes/trace-viewer-delta-d15.md` — §1 (6 dòng) + §2 (4 dòng) đối với bề mặt **CLI**, §3 (5 dòng) đối với **viewer web** `TraceViewer.tsx` (web#3 @ `011b5534`) · §1/§2 giao cho DE ở [kb#16](https://github.com/AI20K-VGR/agentcore-studio-kb/pull/16#issuecomment-5214089501) | 🟡 **đối chiếu XONG cả hai bề mặt, giao còn một nửa** — §3 chưa gửi `#102`. Chủ AIE-2, hạn **D16** |

**Vì sao `DEC-D15-03` đáng là một decision chứ không phải một dòng ghi chú:** nó **thu hẹp** phạm vi
một động từ trên issue. Mọi lần thu hẹp scope đều phải để lại vết có lý do kiểm chứng được, nếu không
thì nó không phân biệt được với việc làm không hết. Ba ràng buộc ở cột *Lý do* đều kiểm được bằng
lệnh, không phải bằng lời.

## D16 · 2026-08-10

> **Sáu id, ghi TRƯỚC khi code tương ứng land** — ngược hẳn D15, nơi 3 id bị trích ở 8 chỗ trước khi
> có bản ghi và thành tham chiếu treo suốt một ngày. Không có `DEC-D16-07`: ca *"mẫu số citation
> rỗng"* nằm trong `DEC-D16-03`, không tách id.
>
> Cả sáu là quyết định **tự chốt** (mentor không trả lời câu hỏi kiến trúc từ 03/08, `kit#74` S2).

| # | Quyết định | Lý do | PR / bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-D16-01** | Nguồn golden-set: `load_golden_set(path: Path, *, expect_ref: str) -> GoldenSet` — **caller truyền đường dẫn**, `src/studio_evalhub/` tuyệt đối không mang hằng số `packages/kb/...`. `EvalHarness.run` nhận `golden_set_path: Path` **keyword-only, KHÔNG default**; composition root (CLI/`apps/studio`/fixture) là chỗ **duy nhất** biết golden-30 nằm ở đâu. `expect_ref` bắt buộc, lệch ⇒ **raise** | Ba lý do kiểm được: (1) **layering** — `.importlinter` xếp 4 quadrant là sibling; một đường dẫn file chéo repo là **cùng một** phụ thuộc, chỉ né được lint chứ không né được thực tế; (2) **fresh clone** — `kit#74` chấm bằng *"clone sạch rồi chạy lệnh y nguyên"*, mà clone riêng evalhub thì `packages/kb/` không tồn tại ⇒ hằng số đường dẫn là một `FileNotFoundError` được đảm bảo trước; (3) `DEC-Q5` đã chốt phân vai **DE sở hữu giá trị · AIE-2 sở hữu nơi lưu + loader**. `expect_ref` bắt buộc vì **bẫy tên file có thật**: file tên `callisto-handbook-30-**draft**.yaml` nhưng `golden_set_ref` bên trong là `callisto-golden-30-**v1**` ⇒ suy ref từ tên file là chạy nhầm bộ case mà không lỗi nào nổi lên. Default `None` cho `golden_set_path` bị loại vì nó là chỗ để ai đó điền đường dẫn kb *"cho tiện"* ở lần sửa sau, và khi đó DEC này thành một câu chữ | `tests/test_golden_loader.py` — `..._doc_ref_mismatch_raises` · `..._khong_suy_ref_tu_ten_file` · **`test_src_khong_hardcode_duong_dan_kb`** (bất biến cưỡng chế: quét `src/*.py`, bắt cả vi phạm **tương lai**) · mutation **M-L1** | ✅ quyết |
| **DEC-D16-02** | `pyyaml>=6.0` khai vào `[project].dependencies` của **`packages/evalhub/pyproject.toml`**, cùng PR với loader | Không phải thủ tục — chính `kit:pyproject.toml:22-25` đã ghi tên lớp lỗi này: *"trước D8 nó chạy được nhờ **ĂN KÉ** extra `uvicorn[standard]` … ai đổi `uvicorn[standard]` → `uvicorn` là mọi `import yaml` trong workspace **chết IM LẶNG**"*. Bản vá D8 khai vào `[dependency-groups] dev` của **kit gốc** — đúng cho một *script* ở kit, sai cho **runtime code của một package được cài**: loader sẽ ăn ké đúng lần thứ hai, chỉ lùi một tầng (chạy được trong workspace venv vì dev-group kéo `pyyaml` vào lock, chết ngay khi `studio_evalhub` cài độc lập). **`uv pip show pyyaml` chạy được KHÔNG chứng minh gì** — bằng chứng đúng là dòng khai trong pyproject của evalhub | `packages/evalhub/pyproject.toml` `[project].dependencies` | ✅ quyết |
| **DEC-D16-03** | `Aggregate.n_scored_citation: int \| None = None` (additive-optional) + nới `Aggregate.citation_accuracy: float \| None`, **KHÔNG** bump `SCHEMA_VERSION`. **Cùng DEC, không mở id mới — ca mẫu số rỗng:** `n_scored_citation == 0` ⇒ `citation_accuracy = None` **và** `gate.verdict = "FAIL"`. *Không đo được thì không PASS được*. **Mở rộng sau review AIE-1 (contracts#5):** hai bất biến trên được **cưỡng chế bằng `model_validator`** chứ không chỉ khai trong docstring — `Aggregate` chặn *rate và mẫu số mâu thuẫn*, `Scorecard` chặn *trục chưa đo + `verdict = "PASS"`*. Validator **một chiều** có chủ đích: `FAIL` với trục đã đo vẫn hợp lệ, nên contract là **sàn** dưới kết quả chứ không thành nơi thứ hai quyết verdict | Trả nợ `DEC-04` + `DEC-S2-134-03`: `DEC-04` quyết ba tầng nhưng **tầng giữa không biểu diễn được** bằng `Aggregate` hôm nay (`contracts/scorecard.py:46-50` chỉ có `success_rate` + `citation_accuracy`) ⇒ consumer cầm `citation_accuracy = 0.90` mà **không có cách nào** biết mẫu số là 30 hay 22. Số làm việc này khẩn: bộ 10 báo `0.90` trong khi thật là **`0.833`**, và `10×1.0 + 20×0.85 = đúng 0.90` ⇒ một bản **đáng FAIL** lại PASS ngay ngưỡng `0.9`; golden-30 có **8/30 = 26.7%** refusal, cùng lớp sai số, quy mô lớn hơn. Ca mẫu số rỗng cùng luật với `not-estimable` (`render.py:76-83`) và fail-closed của `tenant_scope_ok` (`harness.py:130`). **Nới `citation_accuracy` là "ca thứ tư" của `DEC-01`** (tương thích trên dây, KHÔNG tương thích với reader) ⇒ phải đếm reader: đã đếm, **1 reader thật** — `render.py:201` `f"{...:.2f}"` sẽ `TypeError`. Điều kiện *"0 reader giả định non-null"* được thoả **bằng cách vá reader trong cùng thay đổi**, không bằng cách tuyên bố nó không tồn tại | [contracts#5](https://github.com/AI20K-VGR/agentcore-studio-contracts/pull/5) **MERGED** `b642af1` · lệnh đếm reader dán trong PR body · vá `render.py` cùng PR · guard shape mới ở chính `contracts/tests/` | ✅ **xong — merged 10/08 09:29Z, 4/4 chữ ký** (AIE-1 · DE · SWE, cả ba approve trên đúng commit head `dac8d87`, không cái nào STALE) |
| **DEC-D16-04** | Gỡ **hẳn** `xfail(strict=True)` (không đổi `strict=False`) và **viết lại thân bài** `test_gate_blocks_on_fail`; nguồn FAIL là `StubAgentRunner` nạp map *"cố tình sai"* sinh từ golden-set — **tất định, không LLM**. Kèm bài đối trọng `test_gate_passes_on_good_recipe`. **Cùng luật, cùng id — không mở `DEC-D16-07`:** `test_smoke_runner.py::test_tu_choi_khong_co_trace_phai_fail_closed` cũng mang `xfail(strict=True)` với hạn tự khai **D16**, và T4 làm nó XPASS ⇒ gỡ marker + đọc lại assert trong cùng ADR | `strict=True` được dựng ở D9 với đúng mục đích *"lúc seam xong, nó lặng lẽ thành XPASS và không ai buộc phải quay lại xem assert bên trong có còn đúng hợp đồng hay không"* — **hôm nay là ngày cơ chế đó bắn**, và cách duy nhất làm nó vô nghĩa là gỡ marker cho suite xanh rồi đi tiếp. Việc thật không phải xoá một dòng: assert hiện tại dùng `agent_id="agent-bad-instructions"` + `golden_set_ref="golden-set-eval-1"`, **cả hai không tồn tại** ⇒ giữ nguyên thân bài sẽ ra `LookupError`, không ra `FAIL`. Bài đối trọng là bắt buộc: thiếu nó thì `test_gate_blocks_on_fail` không phân biệt được *"gate chặn đúng"* với *"gate chặn mọi thứ"*, và một `verdict = "FAIL"` hằng số cũng xanh | ADR `docs/decisions/` — *vì sao gỡ · assert đã đọc lại chưa · cái gì thay lưới cũ* (lưới cũ canh *"seam chưa xong"*, lưới mới canh *"gate có phân biệt PASS/FAIL không"*) | ✅ quyết |
| **DEC-D16-05** | Ngưỡng: **giữ `0.9/0.95` trong D16** → **đo** trên golden-30 → nếu cần recalibrate thì **ghi số + lý do vào sổ hoãn** → **chốt ở ngày sau**. Không chốt ngưỡng trong cùng ngày đo được số. Số đo trục `citation_accuracy` mang nhãn **`TẠM`**, gỡ nhãn khi bài hồi quy embedding (T9b) xanh | GUIDE-C §3.2 đòi *"ngưỡng literal phải có trước dataset"* — đã tuân thủ (ngưỡng có từ workbench, dataset về D14). Sổ hoãn lại ghi hạn D16 cho recalibrate với lý do đo được: **bộ 5 → `0.80`, bộ 10 → `0.60` / `0.833` ⇒ với `0.9/0.95` một recipe TỐT cũng FAIL cả hai trục**. Hai câu không mâu thuẫn nếu đọc đúng: GUIDE-C cấm **chọn ngưỡng cho vừa số vừa đo** (fitting), không cấm **sửa một ngưỡng đã chứng minh sai đơn vị**. Ranh giới mỏng nên có luật tự áp: *ngưỡng mới chỉ được chốt kèm một lý do **không nhắc tới điểm của recipe hiện tại**; nếu lý do duy nhất viết ra được là "để nó PASS" thì **ghi FAIL và để FAIL**.* Điều kiện cứng từ `DEC-08`: trục `citation_accuracy` **hiện đo sức mạnh FENCE, không đo TRUY XUẤT** (null control: vector hằng số 0 bit thông tin vẫn `recall@1 = 6/6`) ⇒ chốt ngưỡng cho trục đó khi chưa kiểm lại tiền đề là chốt một con số cho một thứ khác với tên của nó. Nhãn `TẠM` đi theo **số liệu**, không ràng buộc **thứ tự chạy**: T6 là P0 và **không chờ** T9b (P2, tiền đề ở người khác) — hướng ngược lại là tự tạo blocker giả cho một ô DoD | `test_doi_threshold_thi_verdict_doi` · `test_verdict_doi_o_dung_hai_phia_cua_nguong` · bảng số đo golden-30 (T6) | ✅ quyết — **đo trong D16, chốt ngày sau** |
| **DEC-D16-06** | **Không** thêm `match_mode` vào `GoldenCase` ở D16. Dời **D18** (cùng mốc `F-6` agreement / `kit#118`) | Đây là rút một hạn **tự đặt** nên phải có số: đã đếm trên golden-30 — **0/30** case có field `match_mode`, và cả 30 chấm được bằng `_contains_phrase` (22 trả-lời) hoặc luật refusal (8 từ-chối). Thêm một field mà **mọi giá trị đều là `exact`** là thêm một nhánh code không có case nào đi qua — đúng lớp *"khung rỗng trông như đã xử lý"* mà `DEC-D12-02` cấm ở tầng render. **Điều kiện lật:** ngày DE giao case cần judge (yêu cầu *"≥3 case cần judge"*, hạn D15 — **chưa thoả**), `match_mode` land cùng bài test đầu tiên dùng nó | `python -c "any('match_mode' in c ...)"` → `False` (đo 10/08) · ask DE ③ | ✅ quyết — hoãn **D18**, có lý do đo được |

### ADR-D16-04 · Gỡ hai marker `xfail(strict=True)` — bản ghi của lần gỡ

> Đây là **ADR mà `DEC-D16-04` yêu cầu**, không phải một id thứ bảy. `render.py:9` đã khai nợ này từ
> D12: *"quyền đổi marker (M6) mới chỉ có ADR **dự kiến** viết ở D16"*. Trả ở đây.

**Gỡ cái gì.** Hai marker, cùng một cơ chế, hai hợp đồng khác nhau:

| Bài | Marker canh gì | Land ở |
|---|---|---|
| `test_gate_blocks_on_fail` (`test_eval_gate.py`) | *"`EvalHarness.run` chưa có verdict"* | T7 |
| `test_tu_choi_khong_co_trace_phai_fail_closed` (`test_smoke_runner.py`) | *"tầng giữ `events` chưa fail-closed"* (`DEC-05`) | T4 |

Cái thứ hai **không** nằm trong câu chữ gốc của `DEC-D16-04` — plan D16 chỉ gọi tên bài thứ nhất.
Nó được xử **cùng id** vì đúng một lý do: nó là **cùng một quyết định** (*"ngày cơ chế bắn thì gỡ
marker và đọc lại luật"*), chỉ khác bài. Mở `DEC-D16-07` cho nó là tách một quyết định làm hai id mà
nội dung không khác gì nhau — đúng thứ §2 cấm.

**Vì sao gỡ, chứ không phải vì sao được phép gỡ.** `strict=True` được dựng ở D9 với mục đích ghi
trong chính docstring của nó: *"lúc seam xong, nó lặng lẽ thành `XPASS` và không ai buộc phải quay
lại xem assert bên trong có còn đúng hợp đồng hay không"*. D16 là ngày cơ chế đó **bắn thật** — pytest
in `[XPASS(strict)]` cho cả hai bài, ở hai thời điểm khác nhau (T4 và T7). Cách duy nhất làm cơ chế
đó vô nghĩa là gỡ marker cho suite xanh rồi đi tiếp. Nên phần thật của việc này là vế sau:

**Assert đã đọc lại chưa — và cả hai bài đều PHẢI SỬA, không bài nào chỉ mất một dòng marker:**

- `test_gate_blocks_on_fail`: `agent_id="agent-bad-instructions"` và `golden_set_ref="golden-set-eval-1"`
  **chưa bao giờ tồn tại**. Giữ nguyên thân bài sẽ ra `LookupError`, không ra `FAIL` — bài sẽ đỏ vì
  lý do chẳng liên quan gì tới gate. Viết lại trên golden-30 thật + `_bad_runner` tất định (không
  LLM: `judge.py` còn là spec đến D18, và một money-shot phụ thuộc LLM là bài không tái lập được).
  Assert từ **1 dòng lên 5**: ba dòng giữa phân biệt *"gate chặn vì recipe tệ"* với *"gate chặn vì
  harness hỏng"* — chỉ giữ dòng đầu thì một `EvalHarness.run` vỡ hoàn toàn cũng cho bài xanh.
- `test_tu_choi_khong_co_trace_phai_fail_closed`: assert cũ chỉ có `success is False`. Nó xanh **cả
  khi** bộ chấm hỏng theo hướng ngược — luật sai kiểu *"citation rỗng ⇒ FAIL"* cũng cho case này
  `False`, và khi đó cả 8 case refusal trung thực của golden-30 đỏ oan mà bài vẫn xanh. Một assert
  không phân biệt được hai nguyên nhân thì không khoá được nguyên nhân nào.

**Cái gì thay lưới cũ.** Lưới cũ (`strict=True`) canh **trạng thái của seam** — một thứ có hạn sử
dụng theo định nghĩa. Lưới mới canh **hợp đồng**, nên không hết hạn:

| Bài | Lưới mới | Mutant chứng minh có răng |
|---|---|---|
| money-shot | bài đối trọng `test_gate_passes_on_good_recipe` — cùng 30 case, cùng ngưỡng, biến duy nhất là chất lượng answer | `verdict` hằng số `"FAIL"` ⇒ đối trọng đỏ |
| no-trace | cặp đối chứng khác nhau **đúng một event**: `events=[]` ⇒ FAIL, thêm 1 event zero-citation ⇒ PASS (F02) | đổi luật thành *"citation rỗng ⇒ FAIL"* ⇒ 4 bài đỏ |

**Một bài bị thu hẹp, không bị xoá.** `test_harness_judge_compute_not_implemented` khẳng định **cả
ba** seam còn raise; T2+T4 điền hai, nên nó phải đỏ — đúng thiết kế. Thu hẹp về seam duy nhất còn là
spec và **đổi tên theo phạm vi mới** (`test_judge_seam_van_con_notimplemented`; giữ tên cũ là để lại
một cái tên nói dối về thứ nó kiểm). Xoá bài là mất lưới bắt *"stub một giá trị giả"* — đã kiểm bằng
mutation: cho `judge` trả `Judge(label="pass", agreement=1.0)` hằng số ⇒ bài đỏ.

**Hai lưới hết hạn cùng ngày, thay bằng spy.** `test_render_scorecard_KHONG_goi_compute_scorecard` và
`test_render_case_KHONG_goi_compute_scorecard` khoá *"render không tự tính"* bằng một bằng chứng
**gián tiếp**: `compute_scorecard` đang `raise`, nên *"render gọi nó"* và *"bài đỏ"* trùng nhau.
`DEC-D15-01` đã khai trước rằng lưới này mất hiệu lực ngày T2 land. Thay bằng spy **hai vế**, vì một
vế không đủ: **tĩnh** (`compute_scorecard` không có trong `vars(render)`) bắt `from … import …` —
kiểu vi phạm mà `monkeypatch` **không** với tới vì tên đã bind lúc import; **động** (sentinel + assert
0 lời gọi) bắt tra cứu trễ qua module — kiểu mà vế tĩnh không thấy. Cả hai vế đã kiểm bằng mutation
riêng.

**Vì sao ADR này đáng tồn tại:** ba trong năm bài trên là lưới **có hạn sử dụng được khai trước** và
đến hạn đúng D16. Một dự án ghi được ngày lưới hết hạn nhưng không ghi lại lúc thay nó thì lần sau
không ai tin cái hạn nữa.

### Vá sau review `kb#18` (N1) — luật `no_leak` rẽ theo trục, KHÔNG mở id mới

Đây là **sửa một lỗi**, không phải một quyết định mới — nên nó không cần id, và `DEC-05` (nhánh
từ-chối fail-closed) **không đổi một chữ**. Ghi ở đây vì nó đổi hành vi chấm điểm và vì con số nó
sửa đã suýt được báo cáo ra ngoài.

`score_case` dùng **một** biểu thức `_citation_tenant(c) != expected_tenant` cho **cả hai** trục
hàng rào. Đúng cho T1; sai cho T6, nơi `expected_tenant == tenant` khiến biểu thức đọc thành *"cấm
trích mọi chunk của chính kho người hỏi"*. Hỏng **hai chiều**: agent từ chối đúng mà có retrieval
hợp lệ bị FAIL oan; và ngược lại, agent **rò chunk kho khác** rồi từ chối lại lọt PASS.

Đo trên golden-30 (4/8 case từ-chối là T6 thuần — `HB-24/26/27/30`): trần `success_rate` của một
agent hoàn hảo kẹt ở **`26/30 = 0.8667`**, `verdict = FAIL`. Sau vá: `30/30`, `PASS`. Nếu `#108`
chốt số trước khi vá thì `0.867` sẽ được đọc là *"agent tệ"* chứ không phải *"bộ chấm sai"*.

**Giới hạn còn lại, không vá được ở tầng này:** `chunk_id` không mã hoá vai (`golden_case.py:69-71`)
và case từ-chối có `expected_citation = []` ⇒ T6 **vẫn không kiểm được đúng thứ nó nói về**. Thứ
kiểm được chỉ là sanity theo slug tenant. Đóng thật cần vai đi kèm citation ở tầng contract — chưa
có producer, và đó là một quyết định của ngày khác.

Phát hiện bởi **review chéo** (`kb#18`), không phải bởi 21 mutant tự gieo. Lý do 21 mutant không
thấy: cả bài unit T6 lẫn fixture integration đều truyền citation **rỗng**, mà `all([])` là `True`
vô điều kiện. Chi tiết + luật rút ra ở `docs/mutations/eval-harness-d16.md` §6.

**Vì sao đúng sáu id và không có id thứ bảy:** một id sinh ra giữa ngày là một id **chưa có ai đọc**.
D15 vừa cho thấy giá của nó (3 id treo, 8 chỗ trích, cả ngày không truy được). Quyết định nào không
gắn được vào sáu id trên thì **không thuộc D16** — nó đi vào bảng *Hoãn* kèm chủ + hạn, không nhét
vào ngày.

## Còn mở — chặn `FROZEN` thật sự

| # | Nội dung | Chờ ai | Hạn |
|---|---|---|---|
| F-1 | [contracts#1](https://github.com/AI20K-VGR/agentcore-studio-contracts/pull/1) (`judge` → optional) merge | @TranBaDat2607 / @hieubui2409 (CODEOWNERS) | D11 |
| F-2 | PR `recipe_hash` (DEC-03) mở + merge | AIE-2 mở · CODEOWNERS merge | D11 |
| F-3 | 4/4 Approve trên hai PR trên | SWE · DE · AIE-1 · AIE-2 | D11 |
| F-4 | Clause **carrier `citations` chỉ trên `llm-step`** — hành vi engine đã đúng và **đã có test engine khoá** (`test_trace_event_emission.py:152`), nhưng clause chưa tồn tại ⇒ bảo đảm hiện tại là **hành vi**, không phải **cấu trúc** | **AIE-1** | D12 |
| F-5 | Clause **`outputs["chunks"]`** thành invariant có tên (DEC-07) | **DE** | D15 |
| F-6 | **Nguồn nhãn tay** cho `Judge.agreement` — field đích đã có (`scorecard.py:19`), field **nguồn không tồn tại**, hằng số bị cấm ⇒ **chặn mọi ô judge**. **Đổi chủ 04/08:** trước ghi `mentor`, nhưng mentor **không tác động** vào quá trình (chỉ nhận kết quả + chấm) ⇒ món gán cho người-không-hành-động thì không bao giờ nhích. Chủ đúng theo `DEC-Q5`/§2.6: **AIE-2** định nghĩa `agreement` đo gì + format + chỗ lưu; **DE** sinh nhãn tay cùng golden-30 (D15) | **AIE-2** — phần định nghĩa + chỗ lưu, **đã chốt**. Phần *sinh nhãn tay* → **DE**, ✅ **DE xác nhận `DEC-Q5` 04/08 09:42Z** (trước đó ghi *ĐỀ XUẤT, chưa xác nhận* — sống 74 phút, xem khối `DEC-Q5` dưới) | D18 |

**Chưa lật `freeze: FROZEN`** — F-1…F-3 chưa đủ cả ba. Trạng thái báo cáo là **freeze-ready**.

> ### ⚠️ Một chỗ tự-mâu-thuẫn, do @DongAnh2704 bắt khi review `evalhub#10`
>
> PR `evalhub#10` sửa lỗi *"gán việc cho người không hành động"* (mentor) — nhưng khi gán phần **sinh
> nhãn tay** của `F-6` cho DE, nó dựa vào `DEC-Q5`, mà **`DEC-Q5` chính nó đang 🟡 chờ DE xác nhận**.
>
> DE nói đúng, và nói đúng tên hiện tượng: *"đang xây quyết định mới trên một quyết định mà chính người
> bị gán việc chưa xác nhận — hơi giống **chiều ngược** của đúng vấn đề PR này đang sửa."*
>
> Hai lỗi cùng một lớp: **một ô chủ-sở-hữu không có thật**. Khác nhau ở chỗ mentor sẽ *không bao giờ*
> hành động, còn DE thì *chưa nói có hay không* — nhưng cả hai đều làm bảng theo dõi **trông như đã được
> quản lý** trong khi chưa.
>
> **Sửa:** tách `F-6` thành hai phần — phần AIE-2 **đã chốt**, phần DE ghi rõ **ĐỀ XUẤT, CHƯA xác nhận**,
> và điều kiện lật là **DE chốt `DEC-Q5`**. Không tự coi là final.
>
> Ghi lại vì đây là lần thứ hai trong hai commit liền nhau tôi tạo một owner-không-thật — bằng chứng
> rằng cái khó không phải *biết luật*, mà là **kiểm lại chính bảng vừa sửa**.
>
> **Vòng hai của cùng finding (@DongAnh2704 trên `evalhub#11`) — sửa một chỗ không phải là sửa.** Vòng
> đầu tôi chỉ sửa **2 file** (`decisions/scorecard.md` + `design-notes/aie2-day11.md` risk-table) và để
> nguyên `docs/contracts/scorecard.v1.md` §9 — tức **file FROZEN, nguồn thẩm quyền cao nhất, vẫn đọc như
> đã chốt** trong lúc decision-log nói chưa. DE gọi đúng: đây là pattern `evalhub#10` từng làm đúng
> (đồng bộ cả 3 file) mà `evalhub#11` làm dở dang. **Đồng bộ đủ 4 chỗ:** `scorecard.v1.md:352` · bảng
> đính chính `scorecard.v1.md:367` · `aie2-day11.md:128` (risk-table) · `aie2-day11.md:63` (câu
> ranh-giới golden-set — DE **không** nêu chỗ này, nhưng nó cùng lớp: phát biểu ranh giới `DEC-Q5` như
> một sự thật đã có). Dòng Sổ chốt 04/08 trong contract **không sửa** — append dòng mới, vì sổ
> append-only và xoá vết lỗi là xoá đúng phần đáng học.
> **Luật rút ra:** một trạng thái *"chưa chốt"* phải đúng ở **mọi** file nêu nó; chỗ lệch duy nhất còn
> lại là chỗ người đọc sẽ tin, và nó luôn là file có thẩm quyền cao nhất.

> ### ✅ `DEC-Q5` — DE xác nhận CÓ, `2026-08-04 09:42Z` (caveat trên sống đúng **74 phút**)
>
> @DongAnh2704 trả lời trên [evalhub#11](https://github.com/AI20K-VGR/agentcore-studio-evalhub/pull/11#issuecomment-5177279745):
> *"nên xác nhận CÓ … xác nhận `DEC-Q5` chỉ là **ghi nhận thực tế đã đang xảy ra**. Không xác nhận mới
> là điểm lệch giữa doc và code."* ⇒ điều kiện lật đã ghi ở khối trên (*"DE chốt `DEC-Q5`"*) **đã thoả**.
>
> **Bằng chứng DE đưa, và kết quả tôi tự kiểm lại — không nhận nguyên văn:**
>
> | DE nói | Kiểm lại | Kết |
> |---|---|---|
> | comment `eval.golden_sets` đã viết *"produced by DE's doc-factory, consumed by AIE-2's harness.py"* | ✅ có thật, nhưng ở `packages/evalhub/src/studio_evalhub/schema.py:8` — **không** phải `packages/evalhub/src/studio_kb/schema.py` như DE dẫn (đường dẫn đó không tồn tại) | ✅ nội dung đúng · đường dẫn sai |
> | `packages/kb/golden/callisto-handbook-30-draft.yaml` đã tồn tại, nhãn trích từ doc-factory, verify bằng `scripts/annotate_golden.py` chạy `StaticKbSearch` thật | ✅ có thật — nhưng **chỉ trên nhánh `origin/day12/de-doc-factory`**, `kb` `main` vẫn ở `93b97c6` (D11). 9 case skeleton, `golden_set_ref: callisto-handbook-30-draft`, tiền tố `HB-` (additive, không đụng `SC-01..SC-10`), dựng trên corpus Handbook mới (42 doc/140 chunk) | ✅ đúng · **chưa merge** |
> | golden-30 đầy đủ là D16, sinh **sau** corpus D13 | ✅ khớp thoả thuận D11 (`kb:plans/sprint2_overview.md:123`, D16 = 10/08) và header của chính file draft tự ghi *"SKELETON, KHÔNG PHẢI BỘ ĐỦ"* | ✅ |
>
> ⇒ **Hai đính chính nhỏ, ghi lại vì chúng đổi cách đọc bằng chứng:** (1) đường dẫn DE dẫn sai package
> nên ai `cat` theo sẽ không thấy gì và có thể kết luận bằng chứng không có; (2) *"đang làm rồi"* đúng
> **trên một nhánh chưa merge** — nên `DEC-Q5` chốt được, nhưng **không** được báo là *"golden-set đã có
> trong `main`"*.
>
> **Cái nhận được — cụ thể, không phải cảm giác:** phần **DE** của `F-6` từ 🟡 *ĐỀ XUẤT* thành **có chủ
> thật**; nền D18 (`kit#118` agreement-check) có nguồn nhãn; và tiền đề `HB-` additive nghĩa là cutover
> D13 **không** làm vỡ `smoke-5`/`smoke-10` của tôi qua đường golden-set — rủi ro còn lại chỉ là
> `chunk_id` của corpus cũ, phải re-run mới biết.
>
> **Cái vẫn còn treo:** DE nói thẳng *"giờ merge cụ thể ngày mai thì repo không ghi … tôi không thể tự
> bịa ra một giờ"* — đúng, và đó là câu tôi đặt sai người. ⇒ chuyển thành **mặc định của tôi**: sáng D13
> re-run e2e + smoke **trước** khi làm việc khác, không chờ ai báo giờ.

## Hoãn — mọi món có chủ + hạn (0 món vô chủ)

| Món | Chủ | Hạn |
|---|---|---|
| Cách biểu diễn DEC-04 trong `Aggregate` (nullable vs `n_scored_citation`). Ghi đúng chữ: *"`aggregate` không tính lại được từ payload `results` đã lưu"* | AIE-2 | D16 |
| Hiện thực `no-trace-no-proof` ở tầng `run_smoke`/`EvalHarness.run` (DEC-05) | AIE-2 | D16 |
| **Recalibrate ngưỡng `success`/`citation_accuracy`** — `DEC-D16-05` chốt *đo trong D16, quyết ở ngày sau*. **Đã đo trên golden-30 (10/08), số dưới đây, và kết luận là CHƯA ĐỦ CƠ SỞ để đổi ngưỡng.** Xem khối *"Số đo T6"* ngay dưới bảng này. Ngưỡng `0.9/0.95` **giữ nguyên**. **Điều kiện lật (đọc được, không phải "chờ thêm"):** có số từ **một agent thật** chạy 30 case — tức `#106` (interpreter AIE-1) xong; mọi số D16 đều đo trên `StubAgentRunner` nên chúng đo **bộ chấm**, không đo agent | AIE-2 | **D17** (điều kiện: `#106`) |
| Giao **golden-30** (`callisto-golden-30-v1`, sinh SAU corpus D13). Nhận chia lô 20@D15 + 10@sáng D16 **nếu chia lô có trong log**. Không nhận *"sẽ có"* | **DE** | D15 |
| **Yêu cầu MỚI cho golden-30 (từ DEC-08):** ≥1/3 case phải có **≥2 ứng viên cùng `tenant` + cùng `section_role`**, để ranking buộc phải chọn thật. Hiện chỉ **2/6** case có tranh chấp trong fence, nên `citation_accuracy` đang đo fence chứ không đo truy xuất. Đây là yêu cầu khác với 4 yêu cầu đã nêu (phủ 2 tenant · refusal T1/T6 · `section_roles` đa dạng · ≥3 case cần judge) | **DE** | D15 |
| **Bài test hồi quy embedding** — sau khi golden-30 có case tranh chấp, viết bài khoá *"embedding hằng số PHẢI làm `citation_accuracy` tụt"*. Không có bài này thì DEC-08 chỉ là một ghi chú, không phải một phép đo | AIE-2 | D16 |
| Dọn alias `_retrieved_citations` — comment `harness.py:237-247` ghi *"KHÔNG dọn trước D11 freeze"*, **hạn đó hết hôm nay** nên phải cấp hạn mới. Consumer thật còn lại: `scripts/smoke_eval_d6.py:66,249` | AIE-2 | D16 |
| `match_mode` (`exact`/`judge`) thành field **optional** trên `GoldenCase` khi bộ 30 về. `GoldenCase` là kiểu **nội bộ quadrant** (`golden_case.py:8`) ⇒ **không bao giờ** cần mini-RFC | AIE-2 + DE | D16 |
| Breakpoint #14 — `refused = not citations` cho **dương-tính-giả**: câu bịa trọn vẹn mà quên đóng ngoặc ⇒ `citations=[]` ⇒ `refused=True` ⇒ **SC-04 PASS dù agent đã bịa**. Trên bài kiểm hàng rào, **xanh-giả nguy hiểm hơn đỏ-giả** | **AIE-1** | D17 |
| **Chủ trục INV-1 roles** — #74 §6: *"needs an owner at D11 freeze. AIE-1 or SWE"*. AIE-2 **không nhận**: bộ chấm **quan sát** hàng rào, không **tạo** hàng rào. Đề xuất **SWE** (#112/D17 đã gán *"Own INV-1: session_id resolve {tenant,user,roles} server-side"*) | **chưa có chủ** — đề xuất SWE | gán **D12** |
| Job CI so con trỏ kit với `main` từng submodule (đã lệch mất điểm 2 lần: `kit#73`, `kit#76`/`#77`) | AIE-2 (issue follow-up) | S2 |

### ADR-D16-05 · Thay đổi contract nào thật sự cần mini-RFC — hai luật đang mâu thuẫn

> **Không phải id thứ tám cho một quyết định cũ.** `DEC-D16-01…06` nói *"thay đổi này làm hay không"*;
> dòng này nói *"luật nào quyết định điều đó"* — một tầng khác, và nó áp cho **cả bốn** hợp đồng chứ
> không riêng scorecard. Ghi ở đây vì `mini-rfc/TEMPLATE.md` sống trong repo này và là vật bị sửa.

**Hai câu, cùng chủ đề, không khớp nhau:**

| Nguồn | Trigger mini-RFC |
|---|---|
| `umbrella-contract.md:92-93` + `INV-5` (dòng 220) | *"Đổi **bất kỳ** contract nào = mini-RFC + 4/4 chữ ký + decision-log"* |
| `mini-rfc/TEMPLATE.md:11-13` (AIE-2 viết, D11) | chỉ **rename · removal · required-add** trên hợp đồng đã `FROZEN`; kèm bảng 4 ca **miễn** tường minh |

Template dẫn chính umbrella §3 làm nguồn nhưng **hẹp hơn** nó. Hai năm cách đọc, chưa ai đối chiếu.

**Việc làm lộ ra mâu thuẫn.** `contracts#5` (D16) mang hai thay đổi: nới `Aggregate.citation_accuracy`
sang `float | None`, và thêm `Aggregate.n_scored_citation` optional. Đọc theo umbrella §3 ⇒ cần
mini-RFC. Đọc theo template ⇒ rơi **đúng hai dòng đầu** của bảng miễn (*"thêm field optional mới"* ·
*"nới required → optional"*). Một mini-RFC đã suýt được viết theo cách đọc rộng.

**Quyết định: áp cách đọc của `TEMPLATE.md`.** Trigger là ba dạng breaking, không phải mọi thay đổi.

**Vì sao, theo thứ tự sức nặng:**

1. **Cách đọc rộng tự mâu thuẫn.** *"Bất kỳ thay đổi nào"* đọc chặt gồm cả sửa một docstring trong
   `scorecard.py` — không ai định nghĩa như vậy. §3 nằm dưới tiêu đề *"4 SCHEMA FREEZE"*: thứ bị đóng
   băng là **shape**, không phải bytes của file.
2. **Cái §3 bảo vệ là consumer không vỡ.** Theo `contracts/__init__.py:5-12`, có đúng ba cách consumer
   vỡ. Ca thứ tư (*tương thích trên dây, không tương thích với reader*) đã có luật riêng —
   `DEC-01`/`ADR-D11-02` — với **điều kiện đo được**: đếm 0 reader giả định non-null. Additive-optional
   thì theo định nghĩa không reader nào vỡ được. Không còn ca nào để mini-RFC bắt.
3. **Giá của cách đọc rộng đã trả một lần rồi.** `scorecard-v0.md:335-337` từng định giá một thay đổi
   **chỉ-doc** thành *"đổi contract → mini-RFC + 4/4 chữ ký"*, rồi phải **rút** công khai. Chính
   `TEMPLATE.md:21` ghi lại ca đó làm dòng thứ tư của bảng miễn. Lặp lại là bỏ qua bài học đã ghi.
4. **Bất đối xứng chi phí.** Mini-RFC tốn 4 người đọc; điều kiện an toàn nó xác lập thì một lệnh `grep`
   đo được trong 5 giây, và lệnh đó **đã bắt buộc phải dán vào PR** theo `DEC-01`.

**Ranh giới — ADR này KHÔNG nói "khỏi cần gì":**

- **Decision-log vẫn bắt buộc cho mọi thay đổi contract.** Vế đó của §3 không bị thu hẹp một chữ.
- **Lệnh đếm reader vẫn bắt buộc dán vào PR.** Nó là *hình thức* của `DEC-01`, không phải kết luận —
  và nó chính là thứ thay chỗ mini-RFC. Bỏ nó là bỏ luôn cơ sở của ADR này.
- **Nới `required` → `optional` mà đếm ra > 0 reader ⇒ quay lại đường mini-RFC**, không có ngoại lệ.
- **Ba dạng breaking vẫn cần mini-RFC + 4/4 chữ ký.** Không đổi một chữ.
- **4/4 chữ ký vẫn nên xin** cho thay đổi contract kể cả khi được miễn mini-RFC — precedent
  `contracts#1`/`#3` đều làm vậy. Đó là **bảo hiểm rẻ**, không phải điều kiện merge (gate thật đo được
  là **1 approval**: `contracts#5` chuyển `APPROVED`/`CLEAN` với một approval từ người **không** phải
  CODEOWNER).

**Trạng thái — đây là cách đọc một luật CHUNG, nên chưa phải luật cho tới khi team không phản đối.**
AIE-2 tự quyết và tự ghi (mentor S2 không trả lời câu hỏi quy trình), kèm cửa sổ phản hồi tới **D18**.
Ai phản đối thì quay về nguyên văn umbrella §3 và ADR này bị rút — ghi rõ để không ai đọc nó thành
việc đã rồi.

**Hai việc kèm:**

1. `mini-rfc/TEMPLATE.md` thêm một dòng trỏ về ADR này, để người mở template thấy ngay cách đọc đã
   chốt thay vì suy lại.
2. Câu *"bất kỳ"* ở `umbrella-contract.md:92-93` nên sửa cho khớp — nhưng umbrella nằm ở
   `docs/requirements` (submodule chung, **không** thuộc write-scope quadrant này), nên **đề xuất qua
   issue kit**, không tự sửa. Tới khi nó được sửa, mâu thuẫn vẫn tồn tại trên giấy và ADR này là chỗ
   ghi cách xử.

### Số đo T6 — độ nhạy ngưỡng trên golden-30 (10/08), `DEC-D16-05`

**Đọc bảng này với một câu cảnh báo đặt trước, không đặt sau:** cả ba runner đều là
`StubAgentRunner`. `#106` (interpreter AIE-1) chưa xong, nên **chưa có agent thật nào chạy 30 case**.
Ba cột số dưới đây vì thế đo **bộ chấm**, không đo agent — chúng chứng minh gate có răng, và **không**
nói được ngưỡng `0.9/0.95` là cao hay thấp đối với một recipe thật.

Cấu hình runner, ghi ra để tái lập được:

- **`tot`** — trả lời đúng mọi case, trích đúng `expected_citation`; refusal có 1 event/0 citation (F02).
- **`hon-hop`** — tổng hợp có chủ đích để tạo điểm đo **giữa** hai cực: mọi refusal đúng, `1/6` case
  trả-lời sai answer, `1/7` case trả-lời đúng nhưng trace không trích được chunk kỳ vọng.
- **`te`** — sai mọi nhánh (answer sai ở nhánh trả-lời, trả lời thật ở nhánh từ-chối).

| runner | ngưỡng success | ngưỡng citation | `success_rate` đo | `citation_accuracy` đo **`TẠM`** | verdict |
|---|---|---|---|---|---|
| `tot` | 0.90 | 0.95 | 1.0000 | 1.0000 | **PASS** |
| `hon-hop` | 0.90 | 0.95 | 0.8667 | 0.8636 | **FAIL** |
| `hon-hop` | 0.80 | 0.80 | 0.8667 | 0.8636 | **PASS** |
| `hon-hop` | 0.85 | 0.80 | 0.8667 | 0.8636 | **PASS** |
| `hon-hop` | 0.80 | 0.85 | 0.8667 | 0.8636 | **PASS** |
| `te` | 0.90 | 0.95 | 0.0000 | 0.0000 | **FAIL** |
| `te` | 0.00 | 0.00 | 0.0000 | 0.0000 | **PASS** |

**Bốn dòng `hon-hop` là ô DoD 3 ở quy mô thật:** `results` **không đổi** giữa bốn lượt (cùng
`0.8667 / 0.8636`), chỉ ngưỡng đổi, và verdict lật `FAIL → PASS`. Không phải hai bộ dữ liệu khác
nhau — nên kết luận chỉ có một cách đọc.

**Nhãn `TẠM` cho cột `citation_accuracy`** (`DEC-08`): trục này hiện đo **sức mạnh FENCE**, không đo
**sức mạnh TRUY XUẤT** — null control cho thấy một vector hằng số 0 bit thông tin vẫn đạt
`recall@1 = 6/6`. Điều kiện gỡ nhãn: bài hồi quy embedding xanh (T9b, tiền đề nằm ở DE).

**Kết luận của T6, viết ra để không ai đọc bảng này thành một đề xuất:** số liệu **không đủ cơ sở**
để recalibrate. Nó cũng **không** xác nhận câu cũ trong sổ hoãn (*"với `0.9/0.95` một recipe TỐT cũng
FAIL cả hai trục"*) — runner `tot` PASS ở đúng ngưỡng đó. Nhưng `tot` tốt **theo định nghĩa**, nên
điều đó cũng không bác được câu kia. Hai chiều đều chưa kết luận được, và lý do giống nhau: chưa có
agent thật. Ngưỡng `0.9/0.95` **giữ nguyên trong D16**, đúng `DEC-D16-05`.

## Dấu vết chữ ký (ADR-D11-01 lớp 2 — KHÔNG phải chỗ ký)

Chữ ký thật = **Approve trên PR**. Bảng này chỉ **chép lại** trạng thái có thật trên GitHub.

Luật đếm (ADR-D11-01 + giới hạn cơ học ở [kit#84 §5](https://github.com/AI20K-VGR/agentcore-studio-kit/issues/84)):
GitHub **không cho tác giả tự-approve**, nên trần là **tác giả tự ký + 3 Approve từ 3 người còn lại**.

**Đồng bộ 2026-08-04 07:55Z — 4/4 PR đủ 3/3, và cả 12 chữ ký đều ở đúng head của PR (0 stale):**

| PR | `<repo>@<sha>` | AIE-1 | AIE-2 | DE | SWE |
|---|---|---|---|---|---|
| `contracts#1` (`judge` → optional) | `contracts@2b95ca9` | ✅ 04-08 | ✅ 03-08 | ✅ 04-08 | ✍️ tác giả |
| `contracts#3` (`recipe_hash`, D-24) | `contracts@dcea5b4` | ✅ 04-08 | ✍️ tác giả | ✅ 04-08 | ✅ 04-08 |
| `evalhub#6` (hợp đồng `scorecard.v1`) | `evalhub@150d6bd` | ✅ 03-08 | ✍️ tác giả | ✅ 04-08 | ✅ 04-08 |
| `evalhub#7` (design-note + 5 mutation) | `evalhub@c4fc9e7` | ✅ 04-08 | ✍️ tác giả | ✅ 04-08 | ✅ 04-08 |

Verify độc lập — **đừng tin bảng này**, chạy lệnh. Nó đối chiếu `commit_id` của mỗi Approve với `head`
để lộ chữ ký **stale** (Approve bị dismiss khi tác giả push):

```bash
for x in "contracts 1" "contracts 3" "evalhub 6" "evalhub 7"; do
  set -- $x
  gh pr view $2 --repo AI20K-VGR/agentcore-studio-$1 --json reviews,headRefOid \
    --jq '.headRefOid[0:7] as $h | .reviews[] | select(.state=="APPROVED")
          | "'"$1"'#'"$2"'  \(.author.login)  \(.commit.oid[0:7])  \(if .commit.oid[0:7]==$h then "hợp lệ" else "STALE" end)"'
done
```

> **Bảng này SẼ mục, và đó là lý do có lệnh ở trên** — finding của @Dozyboy khi review `evalhub#6`:
> *"ghi cứng 0/4 chữ ký thật tại thời điểm viết... ai đọc file mà không chạy lệnh sẽ thấy trạng thái
> cũ"*. Nó đã mục thật: bản trước ghi **0/4** trong khi thực tế đã là 3/3 trên cả 4 PR.
>
> **Nợ:** CI job tự sync bảng này từ `gh pr view --json reviews` thay vì sửa tay — đề xuất của
> @Dozyboy, chủ **AIE-2**, hạn **D12**. Tới lúc đó, mỗi lần sửa tay phải ghi lại mốc đồng bộ như dòng
> **"Đồng bộ ... 07:55Z"** ở trên, để người đọc biết bảng cũ tới đâu.
