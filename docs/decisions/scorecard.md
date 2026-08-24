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

## D18 · 2026-08-12

> **Ghi bổ sung ngày 13/08 (D19/T0b), và ghi luôn cả việc nó bổ sung muộn.** Bảy id dưới đây suốt
> ngày D18 chỉ tồn tại trong `docs/plans/day-18-aie2.md` — một file **chưa nằm trong commit nào** cho
> tới hôm nay. Trong khi đó comment đóng [kit#118](https://github.com/AI20K-VGR/agentcore-studio-kit/issues/118)
> đã dẫn `DEC-D18-04` ra ngoài. Tức người tra id đó từ ngoài repo sẽ không tìm thấy gì và **có quyền
> kết luận là bịa ra lúc viết** — đúng nguyên văn cái bẫy mục `D15` đã tự nêu và vẫn giẫm lại. Xoá
> vết thì mất đúng phần đáng học.
>
> **Sổ này còn thiếu `D17`** (`DEC-D17-01/02/03/05` chưa có mặt; chỉ `DEC-D17-04` xuất hiện, và ở
> mục *Còn mở* chứ không ở một mục ngày). Đo: `grep -c "DEC-D17" → 2`. Chủ **AIE-2**, chưa xếp lịch —
> ghi ra ở đây thay vì để nó thành lỗ thứ hai không ai đếm.
>
> **Cả bảy là quyết định TỰ CHỐT.** Từ 03/08 mentor không trả lời câu hỏi kiến trúc. Không có chữ ký
> thứ hai ở đây.

| # | Quyết định | Lý do | PR / bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-D18-01** | `GoldenCase`: `extra="forbid"` **và** khai `manual_label: str \| None = None` trong **cùng một** thay đổi, không tách | Tách ra thì mỗi vế hỏng một kiểu: `extra="forbid"` một mình làm yaml của DE **đỏ ngay** khi họ emit (chặn DE); khai `manual_label` một mình thì field vào được nhưng **mọi typo tương lai vẫn câm** (`manual_labels`, `manaul_label` — nuốt sạch, và đó chính là lỗi đã xảy ra). Đi cùng nhau: nhãn đúng tên đi vào được, nhãn sai tên **đỏ tại loader** kèm tên field in ra. Không cần mini-RFC — `GoldenCase` là **kiểu nội bộ quadrant** (`golden_case.py:8`, nhắc lại ở `DEC-D16-06`), không đụng `studio_contracts`. Rủi ro `extra="forbid"` **đo được là 0**: golden-30 có đúng 8 field khớp 1:1 | `golden_case.py:44` (`ConfigDict(frozen=True, extra="forbid")`) · `:100` (`manual_label`) · [evalhub#19](https://github.com/AI20K-VGR/agentcore-studio-evalhub/pull/19) merged `cbb5e36` · mutation **M-J1** (`extra="forbid"` → `"ignore"`) **DIE** trên **3 bài** | ✅ merged |
| **DEC-D18-02** | `LLMJudge` nhận `LLM` qua **seam tiêm vào**, KHÔNG import `studio_app`. Composition root (CLI / `apps/studio` / fixture) là chỗ **duy nhất** biết provider thật | Cùng lý lẽ `DEC-D16-01`, không phải luật mới: (1) `.importlinter` xếp 4 quadrant **sibling**, provider thật sống ở `apps/studio` tức **phía trên** evalhub — import ngược là lint đỏ, và đường vòng (`importlib`, đọc env thẳng) là **cùng một phụ thuộc, chỉ né được lint chứ không né được thực tế**; (2) `kit#74` chấm bằng *fresh clone* — clone riêng evalhub thì `apps/studio` không tồn tại; (3) tiền lệ trong chính repo: `AgentRunner` đã là seam đúng hình đó | `judge.py:43` (`from studio_contracts.protocols import LLM`) · `:145` (`__init__(self, llm: LLM, *, cache_path, cap_path, cap=100)`) · [evalhub#20](https://github.com/AI20K-VGR/agentcore-studio-evalhub/pull/20) merged `afe35a5` | ✅ merged · ô DoD *CI deterministic* đóng như **hệ quả cấu trúc**, không phải một việc riêng |
| **DEC-D18-03** | Descope là đường **MẶC ĐỊNH** của D18, không phải phương án dự phòng: chạy ở nấc exact-match, judge dựng đủ + test đủ nhưng **0 call LLM thật** trong ngày và **0 call trong CI, bao giờ cũng** | `DESCOPE.md` (viết D2, không phải viết hôm đó) liệt 4 trigger; đo sáng D18 **hai** trigger đã thoả: *nhà cung cấp LLM không dùng được* (không key, `USE_FAKE_PROVIDERS=true`) và *CI cần tất định*. Một thang cắt giảm viết sẵn từ D2 mà đến ngày trigger thoả lại không kích hoạt thì nó **chưa bao giờ là thang cắt giảm** — nó là một trang văn bản. Cùng hình `DEC-D16-04` | Descope **không đụng một byte** contract: `judge=None` đã mang đúng nghĩa *"case chấm KHÔNG qua LLM-judge"* từ `DEC-02` ⇒ dẫn thẳng tới `DEC-D18-06` | ✅ |
| **DEC-D18-04** | Ô DoD *"agreement-check có số vs nhãn tay"* đóng bằng agreement của **bộ chấm exact-match hiện tại**, không phải của judge. Nhãn **THẬT** đòi **2/2** điều kiện (dữ liệu về **và** trục/vocabulary đã chốt), thiếu một ⇒ nhãn **CƠ CHẾ** | Baseline không phải bước đệm, nó là **mẫu số** của mọi kết luận về judge sau này: một judge đạt `0.85` nghe như tốt cho tới khi biết exact-match đạt `0.92` — lúc đó bật judge là **hạ chất lượng**. Cổng 2/2 vì một field **có giá trị** không đồng nghĩa một phép so **có nghĩa**: bộ chấm trả `SmokeResult.success: bool` (*đạt/không đạt*), nhãn nhánh `ANSWER`/`REFUSE` nằm trên **trục khác** — so thẳng cho ra một số **in được nhưng vô nghĩa** | `agreement.py:76` — hàm thuần trả **ba** giá trị (`rate` · `n_compared` · `lệch`), không trả `rate` trần (`kit#134`) · mutation **M-J5** (`n_compared == 0` ⇒ `0.0` thay vì `None`) **DIE** trên **2 bài** | ✅ quyết · ⚠️ **tên con số đổi trong ngày**, xem dòng dưới bảng |
| **DEC-D18-05** | Cap ≤100/ngày **bền ngoài tiến trình bằng file JSON** cạnh cache (KHÔNG `eval.` table); đọc không được ⇒ **coi như đã chạm trần** ⇒ descope. Khoá cache `(case_id, actual)` | Counter RAM reset mỗi lần khởi động tiến trình, mà `INV-4` nói ≤100 call/**ngày** — một đơn vị **thời gian**, không phải đơn vị **tiến trình**: chạy harness 5 lần trong ngày là cap thật ≤500 và **không dòng code nào sai** để ai nhìn ra. File chứ không table vì chữ ký là `cap_path: Path`/`cache_path: Path` (không tham số DSN nào) và một counter trong Postgres kéo test ra khỏi *"tất định, không mạng"* mà `DEC-D18-02`/`-03` vừa chốt. Fail-closed vì đây là chỗ **duy nhất** trong quadrant mà fail-open đi về phía **tốn tiền thật** — 4 tiền lệ đã fail-closed: `tenant_scope_ok`, `chunks_from_trace`, `_citation_tenant`, `compute_scorecard` | `judge.py:145` (`cap_path`, `cap: int = 100`) · `:70`, `:86` (đọc "thứ không phải PASS" ⇒ `False`) · mutation **M-J2 · M-J3 · M-J4 · M-J6 · M-J7 · M-J8** **DIE** | ✅ · **assumption single-writer khai tường minh** — cap ≤100 chỉ đảm bảo cho **một writer tại một thời điểm**; hai tiến trình song song có thể cùng đọc `99` rồi cùng ghi `100`. Nợ có **điều kiện lật**: ai đó bật `pytest-xdist`/`-n auto`, hoặc harness chạy song song nhiều tiến trình/CI job |
| **DEC-D18-06** | D18 **không** mở PR nào sang `contracts` — và đó là lý do `kit#117` (SWE) thành **no-op** | `#117` giao SWE *"`scorecard_threshold` đọc được cả nhánh judge lẫn exact-match"*; điều kiện để câu đó đúng **đã có sẵn**: `GateThreshold` là `(success, citation_accuracy)` — **hai trục, không trục nào của judge**, và `judge=None` là trạng thái hợp lệ đã khoá bằng validator. ⇒ tụt nấc **không đổi shape nào** mà threshold đọc. Việc thật của `#117` vì thế không phải sửa code mà là **một bài test** chứng minh `gate.verdict` giữ nguyên nghĩa ở cả hai nhánh | `contracts/src/studio_contracts/scorecard.py:150-154` (`GateThreshold.success` · `.citation_accuracy`) · 0 diff chạm `packages/contracts/` trong D18 | ✅ · đo trước rồi báo, thay vì để người khác đo lại thứ mình đã đo |
| **DEC-D18-07** | **Không** thêm `match_mode` vào `GoldenCase` — hoãn tiếp, và hạn mới đặt theo **ĐIỀU KIỆN** chứ không theo ngày: `match_mode` land **cùng commit** với bài test đầu tiên dùng nó | `DEC-D16-06` hoãn nó tới D18 với điều kiện lật đo được (*"ngày DE giao case cần judge, ≥3 case"*). Đo lại sáng D18: **0/30** case có `match_mode`, **0/30** case cần judge ⇒ **chưa thoả**. Lý lẽ gốc giữ nguyên: *thêm một field mà mọi giá trị đều là `exact` là thêm một nhánh code không có case nào đi qua*. Điểm phải ghi: đây là lần **rút một hạn tự đặt lần thứ hai** — một hạn theo ngày mà rút hai lần thì lần thứ ba không còn ai tin | `DEC-D16-06` (hạn cũ) · đếm trên golden-30 | 🟡 hoãn **theo điều kiện** · kiểm lại D19: điều kiện **chưa đổi** |

**`DEC-D18-04` đổi tên con số ngay trong ngày, và đó là phần đáng ghi nhất của D18.** Sau khi
`manual_label` của DE về (`kb#21`) và bump được con trỏ kb, phép đo trên **dữ liệu thật** cho:

```text
agreement kb ↔ evalhub trên golden-30:   n_compared = 10   rate = 1.0   lệch = []
trước khi bump con trỏ kb:               n_compared = 0    rate = None            ← KHÔNG phải 0.0
```

`rate = 1.0` **không** phải một điểm số tốt — nó là dấu hiệu con số đang đo thứ khác với cái tên nó
mang. Kiểm chứng: `manual_label` trùng khít `expects_refusal` ở **10/10** case có nhãn (phía `kb` còn
có guard khoá cứng sự trùng đó), mà `expects_refusal` là thuộc tính **dẫn xuất** từ
`expected_tenant`/`tenant`/`expected_section_role`/`section_roles` — dữ liệu golden-30 **tự khai**.
⇒ nhãn tay **không mang thông tin nào độc lập** với bộ case, nên gọi nó là *"human–machine agreement"*
là **tuyên bố một phép đo không tồn tại**.

Con số được đặt lại đúng thứ nó đo: **`kb ↔ evalhub semantic-fence agreement`** — hai repo suy ra
cùng một ngữ nghĩa (*case này thuộc nhánh trả-lời hay từ-chối*) bằng **hai bản cài đặt độc lập**, nên
so chúng là một **regression detector cho semantic drift**, không phải một phép chấm. Giá trị đó có
tiền lệ đã trả giá: trước 23/07 `expects_refusal` bỏ trục T6 chéo-vai, nên case chéo-vai cùng tenant
rơi nhầm nhánh trả-lời-được và agent từ chối **đúng** bị chấm FAIL — một bộ dò lệch hai phía sẽ bắn
ngay hôm đó. Ranh giới còn lại, nói thẳng: **judge chưa được đo agreement lần nào**, thiếu cả key lẫn
case cần judge (`DEC-D18-04` điều kiện (b) và (c)).

## D19 · 2026-08-13

> **Vào sổ muộn — ghi ra thay vì lấp.** Bảy quyết định này chốt trong ngày D19 và land qua
> [evalhub#22](https://github.com/AI20K-VGR/agentcore-studio-evalhub/pull/22) (merged `24066c6`,
> approve @DongAnh2704), nhưng **không được ghi vào sổ hôm đó**. Phát hiện khi rà sổ ở D20:
> `grep -c "DEC-D19" docs/decisions/` → **0**, trong khi `grep` toàn repo → **88 lần dẫn**. Một
> quyết định được dẫn 88 lần mà không có mục nào định nghĩa nó là **nợ sổ**, không phải nợ việc.
>
> **Cả bảy là quyết định TỰ CHỐT** — từ 03/08 mentor không trả lời câu hỏi kiến trúc.

| # | Quyết định | Lý do | PR / bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-D19-01** | *"Không tự tính lại"* = **cấm suy `cost` từ `tokens` × đơn giá**. **Cộng dồn** `cost` đã lưu **không** phải tính lại — nó là phép **đọc** | Hai nơi tính ra một giá trị thì ngày luật đổi một chỗ, không mặt nào biết mặt nào đúng. Nhưng đọc câu này thành *"cấm mọi phép toán trên cost"* là **ngõ cụt**: nó cấm luôn phép cộng, mà không cộng thì không có `Σcost` nào tồn tại. Ranh giới đúng: cấm **dẫn xuất**, cho phép **tổng hợp** | `run_report.py` · [evalhub#22](https://github.com/AI20K-VGR/agentcore-studio-evalhub/pull/22) merged `24066c6` | ✅ merged |
| **DEC-D19-02** | `RunCost` + `run_cost_from_trace()` sống ở `studio_evalhub/run_report.py` — **không** thêm field vào `SmokeResult`, **không** đụng `contracts` | Thêm field vào `SmokeResult` là đổi shape một kiểu đã có consumer ngoài quadrant; đưa lên `contracts` là **4/4 chữ ký cho mỗi lần đổi shape**. Cả hai giá quá cao cho một đại lượng chỉ có **một** mặt đọc | `run_report.py` (`RunCost` frozen, thuần) · 0 diff chạm `packages/contracts/` trong D19 | ✅ merged |
| **DEC-D19-03** | Luật cộng chốt cứng `round(sum, 6)`, hằng số `_COST_ROUND_NDIGITS = 6`, docstring trỏ thẳng `kb/src/studio_kb/cost.py` | Hai repo cộng cùng một đại lượng thì `ndigits` phải là **một hằng số dùng chung có tên**, không phải một con số lặp lại ở hai chỗ. Khai là **nợ có điều kiện lật** vì lúc chốt, neo phía kb còn trỏ **nhánh PR** `kb#22` | `run_report.py` (`_COST_ROUND_NDIGITS`) · mutation `ndigits 6→7` **DIE** (fixture `0.12345678` phân biệt được cả 5/6/7/8) | ✅ merged · ⚠️ **điều kiện lật đã THOẢ ở D20**: `kb#22` MERGED, `round(·,6)` có trên `kb origin/main` `cost.py:102`. Nhưng con trỏ `packages/kb` trong kit còn sau **13 commit** ⇒ workspace chưa thấy |
| **DEC-D19-04** | Bất biến *"cùng-1-số"* khẳng định trên **giá trị `float` sau `round(·,6)`**, KHÔNG trên chuỗi in ra. Renderer in ít hơn 6 chữ số phải **ghi nhãn là bản rút gọn** | So chuỗi là so **cách trình bày**, không so **giá trị**: hai mặt cùng đúng vẫn khác chuỗi nếu một bên `.2f` một bên `.6f`, và hai mặt cùng sai vẫn khớp chuỗi nếu cả hai cùng cắt về `.2f` | bề mặt evalhub in `.6f` | ✅ merged |
| **DEC-D19-05** | Bề mặt cost của evalhub **không bao giờ in một số `0` trần**. Hai trạng thái của số 0 phân biệt **trong chính output**, phân loại bằng điều kiện đo được trên `events` | *Chưa đo được* ≠ *đo được và bằng 0*. Cùng luật `DEC-D16-03` (`rate=None ≠ 0.0`) và `DEC-D12-02`, chỉ khác trục. Một `0.00` in ra đi thẳng vào báo cáo như một phép đo | `render_run_cost.py` · mutation `priced-drop-prompt` · `priced-drop-completion` · `priced (+ → -)` **DIE** bằng 2 test bất đối xứng chỉ-prompt / chỉ-completion | ✅ merged |
| **DEC-D19-06** | Ô DoD *"cost cùng-1-số"* đóng ở **đường đọc**; phần **số thật** khai **KHÔNG đóng được**. Hai câu, không gộp | `interpreter.py:73` `_NO_COST = 0.0` ⇒ mọi cost trên đường thật là `0.0`. Đường đọc đúng **không** làm số đúng. Gộp hai câu thành *"cost-lineage xong"* là báo cáo thiếu | Điều kiện lật **hai vế cùng lúc**: `price_mismatches` **rỗng** trên một run golden thật **VÀ** `Σcost > 0` | ⚠️ **nửa đóng, giữ nguyên tới D20** · chủ vế số thật: **AIE-1** (`kit#121`) |
| **DEC-D19-07** | Failure-mode list của **phía eval** (`docs/design-notes/aie2-day19-eval-failure-modes.md`), **không chép** danh sách của DE — chỉ những mode mà **bộ chấm** nhìn thấy và danh sách DE **không** nhìn thấy | Chép lại danh sách người khác là tạo ra một bản sao sẽ mục độc lập với bản gốc. Mỗi mode bắt buộc có neo `file:line` kiểm được | `docs/design-notes/aie2-day19-eval-failure-modes.md` (`E-1`…`E-8`) | ✅ merged |

**Mutation D19:** battery vét cạn **75 mutant**, survivor `13 → 9` sau vá, suite `218 → 222 passed`.
9 survivor còn lại **không còn lỗ thật**: 6 tương đương chứng minh được, 2 cận-biên miền không thật,
1 nợ coverage đã ghi nhận (`amain not-in → in`).

## D20 · 2026-08-14

> **GATE-2.** Sáu quyết định. Bằng chứng là commit **local, CHƯA merge** tại thời điểm ghi — nhánh
> `aie-2/d20-gate2-verdict` (evalhub) và `aie-2/d20-gate2-verdict-from-live-spine` (`apps/studio`).
> Ghi trạng thái đúng lúc đọc thay vì viết sẵn *"merged"*.

| # | Quyết định | Lý do | Bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-D20-01** | Chỗ nối GATE-2 sống ở **composition root** (`apps/studio/tests/`), **không** ở evalhub. Chỉ **thêm file test mới** — không sửa `src/studio_app/`, `eval_adapter.py`, `e2e_smoke_eval.py` | `.importlinter:18-21` xếp `studio_kb \| studio_engine \| studio_workbench \| studio_evalhub` **sibling cùng layer** ⇒ `studio_evalhub` **cấu trúc mà nói** không import được `PgKbSearch` hay `interpreter`. Phép nối cần cả ba trong **một tiến trình** ⇒ `studio_app` là chỗ **duy nhất** hợp lệ. Tiền lệ, không phải ngoại lệ mới: `test_spine_scored_from_postgres.py` sống ở đó từ **D7**, bút AIE-2, merge qua PR#2, **cùng lập luận**. `.importlinter` ràng buộc `src/`, **không quét `tests/`** | `apps/studio@b866bc2` · `19b7f4d` | ✅ quyết · ⏳ chưa merge |
| **DEC-D20-02** | `recipe_hash` — evalhub **NHẬN** giá trị, tuyệt đối **không tự dẫn xuất**. `compute_scorecard(..., recipe_hash: str \| None = None)` keyword-only, additive, truyền thẳng | Băm **cái gì** chính là câu *"scorecard này chứng nhận cái gì"*, mà `Recipe` là **bút SWE** (`DEC-03`). Hai cạnh sắc **đo được**, không phải lo xa: (a) `Edge.from_` mang `Field(alias="from")` ⇒ `model_dump_json()` ra `{"from_":…}` còn `by_alias=True` ra `{"from":…}` — **hai chuỗi byte cho cùng một recipe**; (b) ngày `Recipe` thêm **một field tuỳ chọn**, mọi scorecard đã lưu **mất hiệu lực trong im lặng** — không lỗi, không cảnh báo. Cùng luật `DEC-D19-01` (*đọc, không tính lại*), khác trục | `evalhub@7684658` · bất biến **cưỡng chế** bằng `test_src_khong_tu_dan_xuat_recipe_hash` (quét AST cấm `hashlib`/`model_dump_json` trong `src/`) · mutation **M-G2 KILLED** | ✅ quyết · ⏳ chưa merge |
| **DEC-D20-03** | Verdict `FAIL` từ run thật là **kết quả ĐÚNG**. **Không** hạ ngưỡng, **không** đổi fixture cho đẹp. Báo cáo bắt buộc **hai câu, không gộp** | Ba neo có trước hôm nay: `DEC-D17-04` (điều kiện lật ngưỡng đã đo, kết luận **KHÔNG ĐỔI**) · D11 `§4` (chiều lệch đúng của một hàng rào là **xuống**) · GUIDE-C `§3.2` (ngưỡng chốt **trước** dataset). Hạ số vào **đúng ngày gate** là hiệu chỉnh theo thứ mình muốn nhìn thấy | Đo: `success_rate=0.1667` · `citation_accuracy=0.2273` · `n_scored_citation=22` · `verdict=FAIL` · **120 row** `obs.trace_events`. Ngưỡng `0.9/0.95` **0 diff** | ✅ |
| **DEC-D20-04** | Agreement báo **ba giá trị** (`rate` · `n_compared` · `lệch`) **+ một câu nói nó đo gì**; và khai thẳng đang ở nấc descope, **bằng SỐ** | Một `rate` trần không mẫu số là đúng thứ `kit#134` gọi là **bằng chứng dị dạng**. `rate=1.0` đọc một mình nghe như *"đồng thuận tuyệt đối trên golden-30"*, sự thật mẫu số là **10/30**. Và nó **không** phải human–machine agreement: `manual_label` trùng khít `expects_refusal` 10/10, mà `expects_refusal` **dẫn xuất từ chính dữ liệu golden** ⇒ nhãn tay không mang thông tin độc lập. Cái nó đo là **đồng thuận ngữ nghĩa hàng rào kb ↔ evalhub** — regression detector cho semantic drift | `evalhub@2640b9b` · mutation **M-G5 KILLED** · **FINDING:** đếm định tuyến judge trên run thật = **17/22**, plan dự đoán **0** ⇒ tiền đề *"selector cho một tập rỗng"* (dùng để **hoãn việc** ở D18) **chỉ đúng trên đường stub** | ✅ |
| **DEC-D20-05** | `eval.scorecards` + `eval.golden_sets` thêm `tenant_id NOT NULL` + `ENABLE`/**`FORCE`** RLS **hôm nay**. Phạm vi: **chỉ** `schema.py` của evalhub | `kb#24` lật `eval.scorecards` sang **CẦN RLS**, tiêu chí là **bản chất data** không phải *ai đọc*: `harness.py:463` đổ `actual`/`expected` vào `results JSONB` ⇒ chứa **answer-text của tenant**. Land **trước** writer đầu tiên = một dòng DDL trên bảng rỗng; land **sau** = migration trên bảng nhiều tenant **cộng** một câu hỏi không trả lời được (*"dữ liệu đã ghi thuộc tenant nào"*). D20 là ngày `Scorecard` thật đầu tiên tồn tại ⇒ **ngày cuối món này còn rẻ** | `evalhub@3a7df0b` · 2/2 bảng `rls=t force=t` (đo bằng `pg_class`) · mutation **M-G6 KILLED** | ✅ quyết · ⏳ chưa merge · ⚠️ **TRỄ 4 ngày** so với hạn D16 mà D11 `§5` tự đặt |
| **DEC-D20-06** | plan-vs-actual đối chiếu **D11 nguyên trạng** — không sửa design-note cho khớp thực tế — và **bắt buộc có dòng D11 SAI** | Một bảng chỉ có dòng đúng là một bảng **tự chấm**, không phải một đối chiếu. Và một plan-vs-actual chỉ chấm những gì plan cũ đã liệt kê thì **không đo được cái plan cũ bỏ sót** ⇒ bắt buộc có **bảng thứ năm** cho rủi ro D11 không nhìn thấy | `evalhub@4d9481a` — 5 bảng, **4 dòng đánh dấu D11 SAI**, 3/4 lệch **cùng một chiều: định giá quá cao ⇒ hoãn vô cớ** | ✅ |
| **DEC-D20-08** | `GateThreshold` ràng buộc `ge=0.0, le=1.0` tại **contract**, không tại `compute.py`. Biên `0.0`/`1.0` giữ **hợp lệ** (`ge/le`, không `gt/lt`). `SCHEMA_VERSION` **giữ** `0.2.0-draft`. **Không** đụng `ScorecardThreshold` (`recipe.py`, bút SWE) | Ngưỡng ngoài `[0,1]` không phải "khắt khe" hay "lỏng" — nó **vô nghĩa**, và `success_rate >= -999` đúng với **mọi** agent. Đặt ở contract vì mọi caller đi qua đây, kể cả caller **không qua route** (script, `EvalHarness.run` gọi thẳng, producer sau này); vá `recipe.py` (§7 mục 1) chỉ đóng đường **qua mạng**. Vùng xám **không lách**: `test_freeze_guard.py:7-10` định nghĩa breaking bằng **cơ chế** (*"an old payload fails validation"*) và siết khoảng có **đúng chữ ký đó** ⇒ lập luận không-breaking dựa trên **dữ liệu** (0 call-site ngoài `[0,1]` toàn workspace), không dựa trên *"không phải rename/required-add"* | Đo **trước** khi vá: `GateThreshold(-999,-999)` chấp nhận · 3/3 case `success=False citation=0.0` ⇒ `gate.threshold=(-999,-999)`, **`verdict=PASS`**; đối chứng cùng dữ liệu `(0.9,0.95)` ⇒ `FAIL`. Phủ trước khi vá: **21 call-site** ngưỡng ở test evalhub, đúng **2 giá trị**, **0** ca ngoài khoảng. `contracts#6` · mutation **M-T1/M-T2 KILLED** (`M-T2 ge→gt` chạy thật) | ✅ quyết · ⏳ chưa merge · 🔍 nguồn: thẩm định VinSOC `kit#129`, §6 Điều 3 |

> **`DEC-D20-08` ghi SAU phần còn lại của D20** — quyết lúc ~07:30 sau khi bản thẩm định VinSOC lên
> `kit#129` (06:50), không phải cùng đợt với `DEC-D20-01…06`. Ghi đúng thứ tự thời gian thay vì trộn
> vào cho liền mạch. Số `07` đã thuộc AIE-1 (`kit#126`, một run = MỘT recipe) nên nhảy sang `08`.
>
> Đây là món **không** do bộ quét tìm ra: VinSOC chỉ chấm `ScorecardThreshold` ở `recipe.py`. Bản
> sinh đôi ở `scorecard.py` — **bút của chính lane này** — lộ ra khi áp §6 Điều 3 (*"nguyên tắc này
> còn áp được cho trường nào nữa mà tôi đang bỏ sót?"*) vào chính ô ngưỡng. Cả file `scorecard.py`
> có đúng **1** `Field(...)`, và nó nằm ở một biến **đếm** (`n_scored_citation`, `:85`), không ở hai
> biến **quyết PASS/FAIL**.

**Mutation D20: `M-G1`…`M-G6` — 6/6 KILLED, 0 survivor** ([`docs/mutations/gate2-d20.md`](../mutations/gate2-d20.md)).

**Kết quả đáng ghi nhất của ngày, và nó là một phép đo chứ không phải một nhận xét:** dưới `M-G1`
(`compute_scorecard` trả hằng `verdict="FAIL"`), **bài live VẪN XANH** — chỉ bài đối chứng runner-tốt
đỏ. `FAIL` là giá trị **dễ trúng nhất**: mọi cài đặt hỏng đều ra `FAIL`. Nếu hôm nay chỉ làm đúng
những gì ô DoD **chữ nghĩa** đòi (*"eval v1 ra verdict"*), ô đó đã **đóng bằng một hằng số**, suite
vẫn xanh, và không ai biết. ⇒ Bài đối chứng không phải phần thêm; nó **là điều kiện** của ô.

**3/6 mutant lộ ra lỗi trong bài test của chính mình, 0/6 lộ bug trong code sản phẩm** — nặng nhất là
`match="verdict"` khớp vào `agent_id` mà `publish()` nội suy vào thông điệp, chứ không vào lý do chặn.

## D23 · 2026-08-19

> Hai quyết định, cả hai sinh ra từ việc `apps/studio#20` sắp nối `judge=` vào đường production —
> tức từ chỗ một tham số đã có từ D18 lần đầu có caller thật. Bằng chứng là nhánh
> `aie-2/d22-judge-no-trace-fence` (evalhub) tại thời điểm ghi, **chưa merge**.

| # | Quyết định | Lý do | PR / bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-D23-01** | Judge **không được hỏi** khi case trượt vì một cổng fail-closed **cấu trúc** — cụ thể `case_run.events == []` (`DEC-05`). Cổng ở `_duoc_hoi_judge`, đặt **trước** lời gọi, không phải bỏ verdict sau | `_hoi_judge` chỉ đưa judge `expected` + `actual`; judge **không quan sát `events`**, nên nó không có cơ sở nào để nói về một luật nói về **trace**. Trước cổng: case nhánh trả-lời có `events == []` mà `answer` **chứa đúng cụm** `expected` sẽ trượt nấc 1 đúng theo `DEC-05` ⇒ được hỏi judge ⇒ text khớp ⇒ `PASS` ⇒ `DEC-05` bị lật, **tất định**, không cần judge phán sai lần nào. *Trước* chứ không *sau* vì `cap ≤100/ngày` (`INV-4`, `DEC-D18-05`) là quota chia sẻ bền ngoài tiến trình: hỏi rồi bỏ verdict cho cùng một `Scorecard` nhưng tiêu mất một lần gọi | `harness.py::_duoc_hoi_judge` · `tests/test_judge_khong_lat_duoc_no_trace.py` (3 bài) · mutation **`M-T1`…`M-T4` 4/4 DIE** ([`judge-no-trace-d23.md`](../mutations/judge-no-trace-d23.md)); `M-T4` (hỏi-rồi-bỏ) chỉ bị **1** bài giết ⇒ vế "không hỏi" có lưới riêng | ✅ quyết · **khai đúng phạm vi: fence, KHÔNG phải bug-fix** — đo trên golden-30 qua spine thật, no-trace = **0/22** nên bản vá không đổi một con số nào hôm nay; nó chặn ca `DEC-05` **có việc** (runner hỏng, trace writer chết) |
| **DEC-D23-02** | Assumption **single-writer** của `DEC-D18-05` **không còn giữ** khi call-site là HTTP route. Nhận cuộc đua ở S2, **không** thêm lock/quota phân tán | `_doc_counter`/`_ghi_counter` là đọc-sửa-ghi một file JSON không lock, `_ghi_cache` ghi lại **toàn bộ** file. `apps/studio#20` đặt `LLMJudge` vào `_evaluate`, gọi từ **cả** `/evaluate` lẫn `/publish` — 2 request đồng thời đan xen read→modify→write ⇒ cap vượt trong im lặng, cache entry bị ghi đè. Không ném gì, không trả gì lạ. Luận cứ bảo vệ cũ (*"`pyproject.toml` không khai `pytest-xdist`"*) nói về **tiến trình test**, không nói gì về tiến trình server. Chưa vá vì `DEC-D18-05` ranh giới không-over-engineer vẫn đúng: chưa có bằng chứng >1 admin dùng `/publish` đồng thời | `judge.py:239-274` (`_doc_counter`/`_ghi_counter`) · `judge.py:236` (`_ghi_cache` ghi cả file) · `apps/studio#20` | ~~🟡 nợ có điều kiện lật~~ → **✅ đã vá, đóng lệch tiêu chí "phải có số"** — xem `D27`. 🟡 nợ **mới, hẹp hơn** vẫn còn: deploy đổi sang >1 worker/replica |

**Trục còn mở, có số đỡ chứ không phải bỏ sót:** `answer.refused is True` cũng bị judge lật được y như
no-trace. Không chặn ở `DEC-D23-01` vì hai lý do: đo được **0/22** case golden-30 trượt vì `refused`
(runner thật, `ExtractiveFakeLLM`); và `refused is False` là **một phần của phán quyết nội dung** theo
chính docstring `score_case`, nên chặn nó là một quyết định MỚI chứ không phải bảo vệ một quyết định
có sẵn. Điều kiện lật: một runner làm `refused` lên >1/22, hoặc một judge được cho xem `events`.

**Số `0/22` đo trên bộ mặc định production, và chỉ bộ đó.** `callisto-golden-30-v1` + corpus
`docs/callisto/` — đúng mặc định ở `workbench/builder.py` (4 chỗ, đều `callisto-golden-30-v1`) và
`load_callisto()`. **Chưa đo** trên `callisto-2.0-golden-30-v1` (corpus 2.0, 80 doc / 800 chunk, `kb#32`
đã pin, và `evalhub#29` là replay fixture cho chính bộ đó) ⇒ thêm một điều kiện lật cho **cả** `DEC-D23-01`
và trục `refused`: **ngày `golden_set_ref` mặc định cutover sang 2.0, đo lại `17/0/0`**. Ghi ra vì cutover
đang đi, không phải một khả năng xa.

## D26 · 2026-08-22

> Hai quyết định, cùng sinh ra từ việc `apps/studio` đã land **GAP-1** (`app#40`, 2026-08-21) —
> `ENABLE`+`FORCE ROW LEVEL SECURITY` trên `obs.trace_events`. Con trỏ `apps/studio` ở kit tại thời
> điểm ghi vẫn là `898504c` (**trước** GAP-1), nên hai quyết định dưới đây nói về một trạng thái
> **sẽ đến ở lần bump con trỏ**, chưa phải trạng thái của workspace hôm nay. Đó cũng chính là lý do
> phải chốt bây giờ chứ không đợi: ngòi nổ là lần bump, không phải ngày `app#40` merge.

| # | Quyết định | Lý do | PR / bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-D26-01** | `read_run_unscoped`/`list_runs_all_tenants` **từ chối trả lời** (`UnscopedReadUnavailable`) khi `row_security_active('obs.trace_events')` đúng, thay vì trả `[]`. **KHÔNG** vá bằng cách set `app.tenant_id` rồi lặp từng tenant | Policy GAP-1 là `tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid`. Hai hàm này **cố ý** không set biến đó ⇒ phép so trả `NULL` ⇒ mọi dòng bị lọc ⇒ SELECT **thành công**, trả `[]`, không cảnh báo. `[]` là chế độ hỏng tệ nhất vì không phân biệt được với *"bảng chưa có run nào"*; đi thêm một bước, `run_cost_from_trace` biến nó thành `RunCostError("events rỗng")` — đúng ngữ pháp, **sai nguyên nhân**. Hướng "lặp từng tenant" bị loại **không phải vì tốn công**: `read_run_unscoped` tồn tại để `tenant_scope_ok` (`harness.py:187`) bắt run mà node đầu mang `ankor` còn node sau mang `borea` — lọc theo một tenant khiến RLS giấu **đúng những event lạ mà phép kiểm đó đi tìm** ⇒ `tenant_scope_ok` trả `True` cho run hỏng thật. Đó là hồi quy bảo mật, không phải bản vá | `evalhub#37` · `run_report.py::_assert_doc_xuyen_tenant_duoc` (dùng built-in `row_security_active`, gộp sẵn 4 biến số: `ENABLE`/`FORCE`/owner/`BYPASSRLS`) · `tests/test_unscoped_read_fail_closed.py` (3 bài, tự dựng + tự khôi phục tiền đề RLS nên tất định ở **cả hai** phía lần bump con trỏ) · đo đỏ-trước: 2 bài `DID NOT RAISE`; mutation gỡ guard ⇒ đúng 1 bài đỏ · tái hiện sống: 6 bài `test_cost_cung_1_so.py` đỏ với `RunCostError("events rỗng")` khi DB test có RLS | ✅ quyết · vế **thứ hai** (từ chối trả lời) đã land · vế **thứ nhất** (role Postgres riêng có `BYPASSRLS` cho bộ chấm) là nợ có chủ — chạm `docker/postgres-init/00-roles.sql` + `docker-compose*.yml` ở **kit** và `grant_app_privileges()` ở **apps/studio**, PR riêng, **chặn lần bump con trỏ `apps/studio`** |
| **DEC-D26-02** | Ghi nhận: sau `app#41`, dispatcher tool ở đường chấm **phân đôi theo `self._recipe`** — nhánh (a) `recipe=` được tiêm (`routes/publish.py::_evaluate`) dùng `RealToolDispatch` thật; nhánh (b) `recipe=None` (eval-harness rời route, vd `scripts/smoke_eval_d6.py:231`) vẫn rơi về `WhitelistToolDispatch` stub. **Không** đòi `app#41` sửa | Nhánh (b) dựng `create_recipe_d4(...)` với `tool_whitelist=["kb_search"]` mặc định, mà `RealToolDispatch` không hỗ trợ `kb_search` (tool đó đi `KbRetrieveExecutor`, không qua `ToolDispatch`) ⇒ tiêm vào sẽ đổi `unsupported tool: kb_search` thành lỗi cứng cho mọi test hiện có, và đổi cả recipe được băm (`certified_recipe()`, D16 golden-batch determinism). Lý do hợp lý, nhưng hệ quả phải ghi ra: **cùng một recipe, chấm qua nhánh (b) cho kết quả khác chạy qua `/chat`** nếu golden set có node `tool-call` dùng `calculator`/`current_datetime` | `apps/studio#41::eval_adapter.py` · `engine#35` (seam `dispatch(tool, params)`) · fixture `create_recipe_d4` là bút **SWE** (`packages/workbench`) | 🟡 nợ có **điều kiện lật**: ngày golden set thêm case dùng `calculator`/`current_datetime`. Chưa vỡ hôm nay vì golden hiện **0** case như vậy — nhưng đó là thuộc tính của **fixture hôm nay**, không phải bất biến được khoá |

## D27 · 2026-08-23

> Một quyết định, sinh ra từ review `evalhub#40` (@TranBaDat2607) trên bản vá `DEC-D23-02`: PR đóng
> `evalhub#33` bằng suy luận trong khi chính issue đó cấm điều này — *"Cách nào cũng phải **có số**,
> không đóng bằng suy luận."* Ghi lại lý lẽ đầy đủ ở đây thay vì chỉ trong PR body, đúng luật đã rút
> ra ở `D11`: một quyết định có giá phải sống trong decision log, không phải chỉ trong lịch sử PR.

| # | Quyết định | Lý do | PR / bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-D27-01** | Đóng `DEC-D23-02` (vế single-process) **không đo số lần `/evaluate`/`/publish` chồng nhau thật** — lệch có chủ đích khỏi tiêu chí "phải có số" mà chính `evalhub#33` đặt ra | Hai đường đóng issue #33 đòi bằng chứng: (1) vượt cap thật, hoặc (2) không bằng chứng sau khi chạy thật + ghi phép đo. Chưa đo được cả hai — `apps/studio` chưa deploy production đủ lâu để quan sát, và không có công cụ đếm request chồng nhau sẵn có. Lý do chấp nhận lệch: bản vá (`asyncio.Lock` khoá theo cặp `(cache_path, cap_path)`, `judge.py`) **không có nhược điểm đo được** ở phạm vi hiện tại — không đổi hành vi khi chỉ có 1 request tại một thời điểm (trường hợp phổ biến nhất), không thêm dependency, không đổi chữ ký `LLMJudge`, chi phí là `judge()` chồng nhau chạy tuần tự thay vì song song (chấp nhận được vì cap ≤100/ngày vốn đã giới hạn tần suất). Khi cái giá của việc vá bằng 0 và cái giá của việc **không** vá là một lớp lỗi im lặng (`INV-4` vỡ không ai biết), đợi đo trước khi vá là giữ đúng thủ tục mà không giữ đúng mục đích của thủ tục — bar "phải có số" của `DEC-D18-05`/`evalhub#33` được đặt ra để chặn **over-engineer khi giá vá không rẻ**, không phải để chặn một bản vá rẻ có bằng chứng cấu trúc (đọc code, không phải đo tải) | `evalhub#40` · review @TranBaDat2607 (yêu cầu chính mục này) · `judge.py::_LOCKS`/`_lay_lock` · `test_llm_judge.py::test_hai_request_chong_nhau_*` (2 bài, đỏ trước/xanh sau vá, dùng `asyncio.Event` không `sleep`) | ✅ quyết · **phạm vi hẹp lại, không đóng trọn `DEC-D23-02`**: vế single-process (khoá được bằng lock trong tiến trình) đã vá; vế **đa tiến trình** (uvicorn `--workers`>1, hoặc >1 replica cùng mount `judge_cache_path`/`judge_cap_path`) vẫn 🟡 — `asyncio.Lock` không vượt qua ranh giới tiến trình, cần file lock hoặc chuyển cap/cache sang Postgres, và đó **vẫn** là quyết định có giá cần đo trước (đổi test ra khỏi "tất định, không mạng" — `DEC-D18-02/03`), không phải extension miễn phí của bản vá này |

## D28 · 2026-08-24 — cost "một số, ba mặt": điều kiện lật thành máy kiểm, và đọc lại ô GATE-3

> Sinh ra từ `kit#167` mục 3 — ô GATE-3 mentor **tự tay test**: *"số cost phải khớp ở cả ba chỗ nó
> xuất hiện (trace, bảng cost, scorecard)"*.
>
> **Ghi ra một lần trượt của chính mình, vì nó là bài học về cách dùng sổ.** Khi rà ô này tôi đi
> thẳng vào code, đo được `price_mismatches()` bắt mọi `llm-step` của run thật, rồi trình bày như
> một phát hiện mới — kể cả trong issue mở sang engine. Đọc lại sổ thì `DEC-D19-06` **đã ghi đúng
> chuyện đó** từ 13/08, kèm chủ sở hữu và điều kiện lật viết sẵn. Sổ có sẵn câu trả lời; tôi không
> đọc trước khi đào. Ba mục dưới đây là phần **thật sự mới**, sau khi trừ đi thứ D19 đã nói.

| # | Quyết định | Lý do | PR / bằng chứng | Trạng thái |
|---|---|---|---|---|
| **DEC-D28-01** | Điều kiện lật của `DEC-D19-06` (*"`price_mismatches` rỗng trên một run golden thật **VÀ** `Σcost > 0`"*) từ nay là **bất biến máy kiểm**, không còn là câu chữ trong sổ. Bài sống ở **kit gốc**, `xfail(strict=True)` | Điều kiện lật viết ra từ D19 nhưng **chưa ai từng chạy** `price_mismatches()` trên một trace thật — nên nó là một lời hứa, không phải một cái cổng. Ở kit gốc vì ba mặt nằm ở ba quadrant và `.importlinter` xếp chúng sibling **cấm import lẫn nhau**: không file test nào trong một repo con nhìn được cả `studio_kb.cost` lẫn `studio_evalhub.run_report` cùng lúc. Chọn `xfail(strict=True)` chứ không `skip`: ngày nối giá xong, bài **XPASS ⇒ đỏ**, buộc người sửa gỡ cờ và ghi lại — `skip` thì im lặng mãi | [kit#213](https://github.com/AI20K-VGR/agentcore-studio-kit/pull/213) merged `8531ac3` · `tests/test_cost_one_number_three_surfaces.py` 3 bài · đo: run 2 lượt qua `run_agent_loop` cho `tokens=Tokens(prompt=113, completion=9)` với `cost=0.0`, `cost_of(tokens)=0.001035`, `price_mismatches → 2 event_id` · kiểm chiều ngược: mô phỏng nối giá tại điểm emit ⇒ `XPASS(strict)` ⇒ đỏ | ✅ quyết · bài **chống rỗng** đi kèm (`test_the_run_actually_carries_tokens`) là bắt buộc: tokens toàn `0` thì `cost_of` ra `0`, khớp `cost=0`, và bài chính xanh **vì không có gì để so** — đúng giả định mà docstring `price_mismatches` đang dựa vào và nó đã hết đúng |
| **DEC-D28-02** | Đọc **"scorecard"** trong `kit#167` mục 3 là **báo cáo scorecard** (`render_scorecard`/`render_run_cost`), **KHÔNG** phải kiểu `Scorecard` ở `packages/contracts`. Mặt thứ ba **đã tồn tại**, không cần thêm field | Không tự chọn cho tiện — hai quyết định cũ đã khoá hướng này: `DEC-D19-02` (không thêm cost vào `contracts`: *"4/4 chữ ký cho mỗi lần đổi shape"* cho một đại lượng chỉ có một mặt đọc) và `DEC-D19-05` (bề mặt cost **không bao giờ in một số `0` trần** — `render.py::_cost_value` phân biệt *chưa-nối-giá* với *đo-được-bằng-0* ngay trong output). Thêm `cost` vào `Scorecard` còn dựng sẵn chỗ cho ai đó gate lên một trục đang bằng `0.0`: gate đó PASS mọi thứ tới ngày nối giá rồi FAIL mọi thứ hôm sau. **Phải ghi ra** vì không ghi thì ô GATE-3 mơ hồ đúng chỗ nhạy — người chấm đọc "scorecard" theo nghĩa contract sẽ kết luận mặt thứ ba **không tồn tại** | `render.py::_cost_value` (`DEC-D19-05`) · `DEC-D19-02` · `packages/contracts/scorecard.py` không có field `cost` (kiểm bằng grep, chữ `cost` duy nhất trong file nằm trong một comment về lạm phát điểm) | ✅ quyết — quyết một mình theo `DEC-Q5`: từ 03/08 mentor không trả lời câu hỏi kiến trúc. 🟡 **điều kiện lật**: ngày cost trở thành **trục được gate** (không chỉ trục được báo cáo) thì phải xét lại `DEC-D19-02`, và lúc đó là mini-RFC 4/4 chữ ký vì chạm contract |
| **DEC-D28-03** | Nợ *"vế số thật"* của `DEC-D19-06` **neo lại** vào [engine#38](https://github.com/AI20K-VGR/agentcore-studio-engine/issues/38). Neo cũ (`kit#121`) **không dùng được nữa** | `DEC-D19-06` ghi *"chủ vế số thật: AIE-1 (`kit#121`)"*. Nhưng `kit#121` là **issue-của-ngày** (Day 19, giao việc), và nó **CLOSED** khi ngày đó đóng — nợ mất neo theo dõi từ lúc ấy mà sổ vẫn trỏ vào đó. Đây là lớp lỗi riêng, đáng ghi: **neo một món nợ dài hạn vào một issue có vòng đời một ngày** thì món nợ biến mất khỏi mọi danh sách trong khi sổ vẫn trông như đang theo dõi nó. Neo mới mang thêm một dữ kiện chưa từng được ghi ở D19 — xem cột bên phải | `engine#38` · **chướng ngại layering**: §4.1 nói áp giá **một lần tại điểm emit**, nhưng điểm emit ở `studio_engine` còn bảng giá (`cost_of`, *"NGUỒN GIÁ DUY NHẤT"*) ở `studio_kb`, và `.importlinter` cấm hai quadrant import nhau ⇒ `agent_loop.py` **không với tới được**. Đây không phải quên nối một dòng, và nó giải thích vì sao nợ này đứng yên từ D19 | 🟡 chờ AIE-1 (+ DE, bảng giá là file của DE) chốt 1 trong 3: **(a)** chuyển bảng giá xuống `contracts` — trùng hướng `render.py::_cost_value` đã ghi sẵn (*"Q-A (`cost_of` → contracts)"*), chạm contract ⇒ mini-RFC · **(b)** sink tính cost ở `apps/studio/obs/trace_writer.py` (composition root, import kb được) — nhưng docstring file đó đang cấm chính điều này · **(c)** engine giữ bản sao đơn giá — **không khuyến nghị**, đúng thứ `price_mismatches` sinh ra để bắt |

**Việc AIE-2 còn nợ ở trục này, khai rõ thay vì để trống:** chưa đo `Σcost > 0` trên một run golden
thật — không đo được, vì vế đó chặn ở `engine#38`. Khi engine nối giá xong, `DEC-D28-01` sẽ tự đỏ và
đó là lúc chạy nốt phép đo, không sớm hơn.

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

### DEC-D17-04 · Recalibrate ngưỡng — điều kiện lật cũ ĐÃ THOẢ, kết luận vẫn là KHÔNG ĐỔI

**Quyết:** giữ `0.9/0.95`. **Đóng** điều kiện lật cũ (*"chờ `#106`"*) vì nó đã thoả, và mở một điều
kiện lật **mới** — vì số đo được không dùng để hiệu chỉnh ngưỡng.

**Điều kiện cũ thoả nhưng số không dùng được.** Sổ hoãn ghi *"điều kiện lật: có số từ **một agent
thật** chạy 30 case — tức `#106` xong"*. `#106` CLOSED (`engine#20`, `engine@6857885`). Chạy lại
hôm nay: `run_golden_batch.py` → **`30/30 khớp nhãn golden`**.

**Nhưng `30/30` KHÔNG chuyển thành `success_rate` của scorecard.** Đo thật qua `EvalHarness.run` trên
chính output đó (golden-30, `StubAgentRunner` nạp từ interpreter thật):

| `thr_success` | `thr_citation` | `success_rate` | `citation_accuracy` | `n_scored` | verdict |
|---|---|---|---|---|---|
| 0.90 | 0.95 | 0.2667 | 1.0000 | 22 | **FAIL** |
| 0.30 | 0.95 | 0.2667 | 1.0000 | 22 | **FAIL** |
| 0.2667 | 1.00 | 0.2667 | 1.0000 | 22 | **FAIL** |
| 0.20 | 0.95 | 0.2667 | 1.0000 | 22 | **PASS** |
| 0.20 | 1.00 | 0.2667 | 1.0000 | 22 | **PASS** |

`success_rate = 0.2667 = 8/30` — **đúng 8 case từ-chối đạt, 22 case trả-lời trượt hết**. Nguyên nhân
đã truy: `_GoldenAwareLLM` (`run_golden_batch.py:~105`) là double trả **câu canned**
*"Theo tài liệu đã truy xuất, câu trả lời có căn cứ tại [chunk_id]"* — nó **không bao giờ** chứa cụm
`expected` (vd `"3 ngày mỗi tuần"`), nên `_contains_phrase` trượt ở cả 22 case.

⇒ **`30/30` của `run_golden_batch.py` nghĩa là *citations + refused khớp nhãn*, KHÔNG phải *agent trả
lời đúng*.** Hai phép đo khác nhau, và trước hôm nay chúng bị đọc lẫn.

**Cái đo được là thật, cái không đo được cũng phải nói ra:**

- `citation_accuracy = 1.0000` trên `n_scored = 22` là **tín hiệu thật** — double trích đúng chunk.
- `success_rate = 0.2667` **không đo chất lượng agent** — nó đo prose của một double không sinh prose.

**Không đủ cơ sở đổi ngưỡng, và lý do mạnh hơn giả định ban đầu.** Bản plan sáng nay suy đoán số sẽ
là `1.000/1.000` (*"agent hoàn hảo, không có phương sai"*). Đo xong thì sai: không phải thiếu phương
sai, mà là **trục `success` chưa có dữ liệu hợp lệ nào để hiệu chỉnh**. Chỉnh `0.9` xuống `0.2` cho
verdict PASS sẽ là fitting theo một artefact của test-double — đúng thứ `DEC-D16-05` tự cấm.

**Điều kiện lật MỚI (thay câu cũ trong sổ hoãn):**

> Có số từ một LLM **sinh prose thật và không biết trước nhãn** trên ≥30 case (đường `#116`/D18 hoặc
> demo-flag live trong cap), **và** `success_rate` phản ánh nội dung câu trả lời chứ không phản ánh
> khuôn câu của double. Trước đó mọi đề xuất đổi ngưỡng là chỉnh-cho-vừa-số.

Nhãn **`TẠM`** trên trục `citation_accuracy` (`DEC-08`) **giữ nguyên**, chưa gỡ.

**Bảng ngưỡng vẫn chứng minh gate có răng:** verdict lật giữa `0.30` (FAIL) và `0.20` (PASS) trên
cùng một bộ `results`; và `thr_citation = 1.00` với `citation_accuracy = 1.0000` cho **PASS** — khoá
đúng `>=`, không phải `>`.

**Kiểm không-hồi-quy:** chạy đúng bảng trên với `harness.py` **trước** bản vá `F-6` (`419d29f`) ra
**số y hệt** (`0.2667 / 1.0000 / 22`, 5/5 dòng). Bản vá T2/T3 không đổi một con số nào ở đây — đúng
như dự đoán, vì 8/8 case âm không có chunk lệch kho/lệch vai nên luật mới cho cùng verdict qua
đường khác.

### T4b · Fence trên đường Postgres — phép đo RIÊNG, không suy từ `StaticKbSearch`

Số `0/8 chunk-khác-kho` ở plan §1 đo trên `StaticKbSearch` (lọc bằng vòng `for` trong RAM). `#110`
lật seam chính thức sang `PgKbSearch` (lọc trong SQL + RLS) — **hai impl khác nhau**, nên tính chất
của bản này không tự động đúng cho bản kia. Đo lại, DB thật (`docker-compose.test.yml`, 5433,
`studio_app`/`studio_owner`, 140 chunk seed):

| Đường đo | Impl | tổng chunk / 8 case âm | lệch-kho | lệch-vai |
|---|---|---|---|---|
| control | `StaticKbSearch` | 40 | 0 | 0 |
| fence thật, `kb@main` | `PgKbSearch` | 40 | **0** | **0** |
| fence thật, `kb#19` (`494bf41`) | `KbSearchService` → `PgKbSearch` | 40 | **0** | **0** |

Ba đường đồng thuận. Đo **không chờ `#110` merge** — nhánh PR fetch sẵn ở local.

**Đọc cho đúng phạm vi:** đây là **quan sát** thứ retrieval đã trả về, **không** phải chứng minh
retrieval *không thể* trả thứ khác. Nó không chứng minh fence RLS-UUID; leak-test thật vẫn là
`#110`/`#112`. Cái nó chứng minh: trên bộ 8 case âm này, hàng rào **đang** giữ cả hai trục, và từ
hôm nay điều đó **được đo** thay vì được giả định.

## Hoãn — mọi món có chủ + hạn (0 món vô chủ)

| Món | Chủ | Hạn |
|---|---|---|
| Cách biểu diễn DEC-04 trong `Aggregate` (nullable vs `n_scored_citation`). Ghi đúng chữ: *"`aggregate` không tính lại được từ payload `results` đã lưu"* | AIE-2 | D16 |
| Hiện thực `no-trace-no-proof` ở tầng `run_smoke`/`EvalHarness.run` (DEC-05) | AIE-2 | D16 |
| **Recalibrate ngưỡng `success`/`citation_accuracy`** — `DEC-D16-05` chốt *đo trong D16, quyết ở ngày sau*. **Điều kiện lật cũ (`#106`) ĐÃ THOẢ 11/08 và đã đo — kết luận vẫn là KHÔNG ĐỔI, xem `DEC-D17-04`.** Ngưỡng `0.9/0.95` **giữ nguyên**. Số đo qua scorecard: `success_rate = 0.2667` (8/30), `citation_accuracy = 1.0000` trên `n_scored = 22`. `success_rate` **không đo chất lượng agent** — `_GoldenAwareLLM` là double trả câu canned không chứa cụm `expected`, nên 22 case trả-lời trượt `_contains_phrase`. **Điều kiện lật MỚI:** số từ một LLM **sinh prose thật, không biết trước nhãn** trên ≥30 case (`#116`/D18 hoặc demo-flag trong cap) | AIE-2 | **D18** (điều kiện: LLM sinh prose thật) |
| Giao **golden-30** (`callisto-golden-30-v1`, sinh SAU corpus D13). Nhận chia lô 20@D15 + 10@sáng D16 **nếu chia lô có trong log**. Không nhận *"sẽ có"* | **DE** | D15 |
| **Yêu cầu MỚI cho golden-30 (từ DEC-08):** ≥1/3 case phải có **≥2 ứng viên cùng `tenant` + cùng `section_role`**, để ranking buộc phải chọn thật. Hiện chỉ **2/6** case có tranh chấp trong fence, nên `citation_accuracy` đang đo fence chứ không đo truy xuất. Đây là yêu cầu khác với 4 yêu cầu đã nêu (phủ 2 tenant · refusal T1/T6 · `section_roles` đa dạng · ≥3 case cần judge) | **DE** | D15 |
| **Bài test hồi quy embedding** — sau khi golden-30 có case tranh chấp, viết bài khoá *"embedding hằng số PHẢI làm `citation_accuracy` tụt"*. Không có bài này thì DEC-08 chỉ là một ghi chú, không phải một phép đo | AIE-2 | D16 |
| Dọn alias `_retrieved_citations` — comment `harness.py:237-247` ghi *"KHÔNG dọn trước D11 freeze"*, **hạn đó hết hôm nay** nên phải cấp hạn mới. Consumer thật còn lại: `scripts/smoke_eval_d6.py:66,249` | AIE-2 | D16 |
| `match_mode` (`exact`/`judge`) thành field **optional** trên `GoldenCase` khi bộ 30 về. `GoldenCase` là kiểu **nội bộ quadrant** (`golden_case.py:8`) ⇒ **không bao giờ** cần mini-RFC | AIE-2 + DE | D16 |
| Breakpoint #14 — `refused = not citations` cho **dương-tính-giả**: câu bịa trọn vẹn mà quên đóng ngoặc ⇒ `citations=[]` ⇒ `refused=True` ⇒ **SC-04 PASS dù agent đã bịa**. Trên bài kiểm hàng rào, **xanh-giả nguy hiểm hơn đỏ-giả** | **AIE-1** | D17 |
| **Chủ trục INV-1 roles** — #74 §6: *"needs an owner at D11 freeze. AIE-1 or SWE"*. AIE-2 **không nhận**: bộ chấm **quan sát** hàng rào, không **tạo** hàng rào. Đề xuất **SWE** (#112/D17 đã gán *"Own INV-1: session_id resolve {tenant,user,roles} server-side"*) | **chưa có chủ** — đề xuất SWE | gán **D12** |
| **6 call-site còn đi đường `citations` vacuous** — `F-6` chỉ đổi hành vi ở `run()`/`run_smoke()`; `score_run_from_trace` · `run_report` · 4 script `apps/studio` vẫn đi `_NOT_PROVIDED`. Đáng chú ý: `score_run_from_trace` chính là hàm `workbench/dev_playground_server.py::_score_run()` gọi ⇒ **số hiển thị trên Playground chưa được hưởng bản vá**. Nêu bởi SWE ở review `evalhub#18`. **Điều kiện lật:** đổi chữ ký `score_run_from_trace` để nhận `retrieved_chunks`/`tenant_ids` — nó là API công khai có consumer ngoài quadrant nên phải additive + báo trước SWE | AIE-2 (+ SWE consume) | **D18** |
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

**Trạng thái (D16, khi mở) — đây là cách đọc một luật CHUNG, nên chưa phải luật cho tới khi team
không phản đối.** AIE-2 tự quyết và tự ghi (mentor S2 không trả lời câu hỏi quy trình), kèm cửa sổ
phản hồi tới **D18**. Ai phản đối thì quay về nguyên văn umbrella §3 và ADR này bị rút — ghi rõ để
không ai đọc nó thành việc đã rồi.

#### ✅ CỬA SỔ ĐÓNG 12/08 (D18) — 0 phản đối ⇒ ADR **có hiệu lực**

Điều kiện rút đã công bố trước là *"ai **phản đối** thì ADR này bị rút"*. Đo lúc đóng, quét cả 5
thread `ADR-D16-05` từng xuất hiện (`kit#83` · `#84` · `#108` · `#113` · `#114`) cộng `evalhub#18`
(body + comment + 4 review) cộng `kit#118`/`#119`: **0 phản đối**. Điều kiện rút không thoả ⇒ ADR đứng.

**Phản hồi thực chất có đúng một, và nó nằm ở `kit#114` — KHÔNG ở `#113` cũng không ở `evalhub#18`.**
Ghi lại chỗ này vì nó là bài học quy trình: cửa sổ được công bố ở thread A, phản hồi rơi vào thread B,
và một lần kiểm chỉ-đúng-thread-đã-công-bố sẽ kết luận "im lặng" **sai sự thật**. Cửa sổ sau phải khai
rõ nơi nhận phản hồi, hoặc phải quét theo định danh ADR chứ không theo thread.

DE (`kit#114`, 11/08 10:28) — nguyên văn *"ack `ADR-D16-05` (**không phản đối**)"* và *"Đồng ý cách
đọc hẹp — trên lập luận"*, kèm **hai điểm**, cả hai đều **không phải phản đối nội dung**:

1. **Van "đếm reader" bắt người *import*, không bắt người *giả định non-null*.** Hỏi thẳng:
   `contracts#5` đã đếm-non-null và dán chưa; nếu chưa thì *"nó là breaking đeo phù hiệu miễn"*.
   **Đã kiểm — rồi, và chặt hơn mức lo ngại.** PR body `contracts#5` dán cả hai lệnh `grep`, và không
   dừng ở đếm import: nó chỉ đích danh **1 reader production** — `studio_evalhub/render.py` format
   `:.2f`, tức đúng ca **vỡ `TypeError` trên `None`** dù "đọc field bình thường" — rồi **vá reader đó
   trong cùng thay đổi**. Nguyên văn: *"Điều kiện của `DEC-01` được thoả bằng cách vá reader, không
   phải bằng cách tuyên bố nó không tồn tại."* ⇒ điểm 1 thoả trên chính tiền lệ đang xét. Yêu cầu dán
   lệnh đếm **kèm kết luận non-null** giữ nguyên cho mọi lần sau.
2. **Đề nghị nâng lazy-consensus lên ack tường minh 4/4 người giữ bút** — *"im lặng có thể là 'chưa
   đọc', không phải 'đồng ý'"*. **Ghi nhận là process-improvement, áp cho ADR SAU, KHÔNG hồi tố ADR
   này.** Lý do: đổi bar phê chuẩn sau khi cửa sổ đã đóng theo điều kiện công bố trước là đổi luật
   giữa chừng — đúng lớp lỗi mà chính ADR này vá. Ghi lại làm nợ quy trình, không làm điều kiện đóng.

Trạng thái ack tường minh tại thời điểm đóng, ghi để ADR sau có mốc: **DE ✅ 1/4** · SWE ⬜ · AIE-1 ⬜
(chỉ *ghi nhận đang treo* ở tổng hợp `kit#114`, không phải ack) · AIE-2 = tác giả.

**Hai việc kèm:**

1. ✅ **XONG.** `mini-rfc/TEMPLATE.md` đã mang dòng trỏ về ADR này ngay từ `bde93de` (cùng commit với
   chính ADR, D16); D18 cập nhật wording từ *"cửa sổ phản đối"* sang trạng thái **đã có hiệu lực** để
   người mở template không đọc một cửa sổ đã đóng thành đang mở.
2. ⬜ **CHƯA LÀM — nợ mở.** Câu *"bất kỳ"* ở `umbrella-contract.md:92-93` nên sửa cho khớp, nhưng
   umbrella nằm ở `docs/requirements` (submodule chung, **không** thuộc write-scope quadrant này), nên
   **đề xuất qua issue kit**, không tự sửa. Issue **chưa được tạo** tính tới D18 — nội dung đã soạn,
   còn chờ mở. DE cũng yêu cầu đúng món này: *"cần một owner + issue theo dõi, đừng để trôi — không
   thì người đọc umbrella trước vẫn gặp 'bất kỳ' và tái tranh luận từ đầu."* Bút đề xuất: AIE-2.
   Tới khi nó được sửa, **mâu thuẫn vẫn tồn tại trên giấy** và ADR này là chỗ ghi cách xử.

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
