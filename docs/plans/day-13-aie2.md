# Plan Day 13 — AIE-2 · Golden-set intake, trace handoff và KB cutover

**Ngày:** 2026-08-05  
**Mode:** execution plan  
**Owner:** AIE-2  
**Scope:** D13 only; handoff cho D14/D16/D18, không implement công việc của các ngày sau.

> Root đã merge PR#137 ở `5c6f6d8`. Root gitlink evalhub là `60fe89d`; local branch
> `docs/day13-plan-aie2` đang ở `96e3110` để giữ tracked Day11/12. Local divergence này có chủ ý và
> không được reset trong D13.

## 1. Execution outcome

### Why

D16 chỉ đáng tin nếu input, citation provenance, trace carrier và regression baseline của D13 được
kiểm bằng artifact cụ thể. D13 không phải ngày xây scorer; đây là ngày làm sạch ranh giới và nguồn đo.

### What

Hoàn tất sáu kết quả:

1. Workspace/corpus snapshot đúng SHA.
2. Intake review cho 9 golden draft `HB-01..HB-09`.
3. Smoke-5/smoke-10 non-regression comparison sau KB cutover.
4. Trace handoff với AIE-1 hoặc blocker có owner/ETA.
5. Coverage matrix cho target golden-30.
6. Evidence note đủ để D14 tiếp tục mà không suy diễn.

### How

Thực hiện theo thứ tự T1 → T2 → T3 → T4 → T5 → T6. Mỗi task phải tạo hoặc cập nhật một artifact
được định danh ở §3. Nếu dependency thiếu, ghi blocker vào evidence và tiếp tục phần không phụ thuộc;
không tự đổi label, contract, engine hoặc threshold để đi tiếp.

### DoD

Artifacts A1–A6 tồn tại, có command/input/output hoặc blocker cụ thể, có owner cho phần còn thiếu.

## 2. Fixed execution constraints

### Why

Các quyết định này đã được chốt trước D13. Đặt chúng một lần ở đây để work item và checklist không lặp
lại hoặc vô tình mở rộng scope.

### What

| Constraint | D13 rule |
|---|---|
| Source of truth | Dùng `agentcore-studio-kb@51df3a4`, SHA `51df3a4`; không dùng bản copy local khác. |
| Golden input | Giữ nguyên `GoldenCase` 8 field; 9 case hiện tại là draft/skeleton, chưa phải golden-30. |
| Sample scope | D13 intake có `n_planned=9` để validate input; D16 mới chốt `n_planned=30` cho fixed evaluation. |
| Provenance | `expected_citation` phải truy được về doc-factory/annotation và `chunk_id` thật. Không sửa label để test xanh. |
| Measurement | Ghi planned/actual `n`, independent unit/source nếu có, strata, scorer, candidate/held-out status và tuning rounds. Thiếu thì ghi `unknown`, không đoán. |
| Reporting | D13 chỉ ghi fixed-set regression evidence; không claim population guarantee. `30/30` không được dùng như lower-bound `>=0.90`. |
| Citation metric | Refusal có convention `citation_accuracy=1.0`, không phải citation observation. Mẫu số citation phải là answerable/scored cases. `n=0` là `not_estimable`. |
| Scope boundary | Không implement `compute_scorecard`, `EvalHarness.run`, LLM judge, Wilson/ICC/Clopper–Pearson/Bayesian hoặc CI hard gate. Roadmap D16/D18 giữ nguyên. |
| Ownership | DE sở hữu case/label; AIE-1 sở hữu interpreter/trace producer; AIE-2 sở hữu intake, validation và handoff evidence. |

### How

Mọi exception so với bảng trên được ghi thành blocker/decision request trong A6; không sửa tại chỗ
trong evalhub để làm plan xanh.

### DoD

Không có task D13 nào yêu cầu thay đổi shared contract, scorer/judge implementation, KB pipeline,
engine interpreter hoặc golden labels.

## 3. Artifact contract

### Why

Execution plan phải để lại bằng chứng có thể kiểm, không chỉ một câu “đã review”.

### What

Các artifact local-only dùng chung evidence folder:

| ID | Artifact | Nội dung bắt buộc |
|---|---|---|
| A1 | `.local-reviews/day13/A1-workspace.md` | root SHA, origin SHA, gitlink/local HEAD, KB SHA, commands, test output |
| A2 | `.local-reviews/day13/A2-intake.md` | bảng 9 case, 8 field, duplicate/vocabulary/provenance/refusal checks, finding per case |
| A3 | `.local-reviews/day13/A3-smoke-comparison.md` | command/fixture, case count, baseline/post-cutover score, citation diff, drift classification |
| A4 | `.local-reviews/day13/A4-trace-handoff.md` | trace hash/link hoặc blocker; field table cho chunks, citations, tenant, role, refused |
| A5 | `.local-reviews/day13/A5-coverage-matrix.md` | 30 target rows/slots, coverage, owner, provenance, measurement status, missing 21-case list |
| A6 | `.local-reviews/day13/A6-evidence.md` | index A1–A5, open dependencies, owner/ETA, status của constraints ở §2 |

### How

Artifact ghi command đầy đủ, SHA, input reference và output nguyên văn hoặc bảng kết quả. Khi không có
input cần thiết, ghi `BLOCKED`, lý do, owner và ETA; không ghi `PASS` thay thế.

### DoD

Mỗi artifact có thể mở độc lập, truy ngược được về SHA/fixture/case, và A6 liên kết đủ A1–A5.

## 4. Execution sequence

### Why

T2–T5 phụ thuộc workspace và input đúng. Chạy sai thứ tự sẽ khiến drift của corpus bị nhầm thành bug
evalhub hoặc khiến coverage được đánh giá trên draft chưa xác thực.

### What

| Step | Task | Entry condition | Exit artifact |
|---|---|---|---|
| 1 | T1 Pre-flight | PR#137 đã merge | A1 |
| 2 | T2 Intake | A1 có SHA/corpus đúng | A2 |
| 3 | T3 Smoke comparison | A1 + fixture baseline | A3 |
| 4 | T4 Trace handoff | A1 + runner/fixture | A4 |
| 5 | T5 Coverage matrix | A2 + DE delivery status | A5 |
| 6 | T6 Evidence/handover | A1–A5 hoặc blocker | A6 |

### How

Nếu bắt đầu muộn, giữ thứ tự T1–T4 trước khi làm matrix. Không bỏ pre-flight, intake, smoke hoặc trace
để nhảy sang code scorer.

### DoD

Sequence kết thúc tại A6; không có task ngoài D13 được mở chỉ vì một dependency chưa trả lời.

## 5. T1 — Pre-flight và baseline

### Why

Cần phân biệt trạng thái kit sau PR#137 với local branch đang giữ tracked Day11/12 trước khi đọc bất kỳ
con số nào.

### What

Xác nhận root, mọi submodule, KB SHA, evalhub local HEAD và baseline test.

### How

Chạy và lưu output:

```bash
git status --short --branch
git rev-parse HEAD
git submodule status
git -C packages/evalhub status --short --branch
git -C packages/evalhub rev-parse HEAD
git -C packages/evalhub rev-parse origin/main
uv run pytest packages/evalhub -q
```

Expected facts hiện tại:

```text
root HEAD       = 5c6f6d8
evalhub gitlink = 60fe89d
evalhub local   = 96e3110 / docs/day13-plan-aie2
KB              = 51df3a4
baseline        = 50 passed, 1 skipped, 2 xfailed, 0 XPASS
```

### DoD

A1 có đủ command/output, giải thích `M packages/evalhub` là local Day11/12 tracking, và ghi mọi
tracked change khác nếu có. Nếu baseline khác expected, T1 không PASS; phải tạo finding.

## 6. T2 — Golden intake review

### Why

D16 không thể đọc một draft có citation/label sai như thể đó là lỗi scorer. Intake phải tách data finding
khỏi implementation finding.

### What

Validate `HB-01..HB-09` theo model hiện tại:

- `case_id` duy nhất, prefix `HB-`;
- tenant chỉ thuộc vocabulary `ankor`/`borea`;
- `section_roles` và `expected_section_role` hợp lệ;
- case answerable có `expected` và citation phù hợp;
- case T1/T6 có `expected="refusal"`, citation rỗng và `expects_refusal` đúng;
- citation khớp output doc-factory/KB `chunk_id`;
- query/citation không trỏ vào 5 doc gốc bị cấm sửa;
- ghi answerable/refusal count và source/document/query-family nếu DE cung cấp.

### How

Parse bằng `GoldenCase` hiện tại, kiểm duplicate/vocabulary/provenance theo từng row. Không thêm field
vào model, không sửa YAML/annotation trong evalhub. Mismatch phải ghi `case_id`, query, expected, actual,
corpus SHA, owner và proposed next action.

### DoD

A2 có đúng 9 row, mỗi row có trạng thái PASS/BLOCK/FINDING cho các kiểm trên. Không có citation hoặc
hand label được sửa thủ công trong repo.

## 7. T3 — Smoke/e2e non-regression sau cutover

### Why

Corpus D12 là biến đầu vào mới; cần biết score/citation thay đổi vì KB, fixture, adapter/trace hay scorer
trước khi gọi đó là regression.

### What

So sánh smoke-5/smoke-10 baseline với post-cutover trên cùng command, fixture, thứ tự case và expected.

### How

Ghi command, kit SHA, KB SHA, số case, per-case success, citation list/accuracy và aggregate. Nếu có
drift, phân loại theo thứ tự: corpus/chunk numbering → embedding fixture → adapter/trace → evalhub.
Không cập nhật expected để xoá diff.

### DoD

A3 có bảng baseline/post-cutover theo case và kết luận `NO_DRIFT` hoặc finding có nguyên nhân/owner.
Không chấp nhận một dòng “pass” không có số.

## 8. T4 — Trace handoff với AIE-1

### Why

Evalhub phải biết đọc đúng carrier trước D14/D16; không được suy `refused`, citation hoặc scope từ một
field khác chỉ vì fixture hiện tại thiếu dữ liệu.

### What

Xác nhận một trace/fixture cho các field:

| Field | Mục đích |
|---|---|
| `outputs["chunks"]` ở `kb-retrieve` | retrieved chunks/UUID/role |
| `citations` ở event carrier | grounded citation input |
| `tenant_id`, `node_type` | scope và carrier validation |
| `refused` ở `llm-step` | answer/refusal branch |
| event list/run id | no-trace-no-proof và determinism |

### How

Lưu sample hash/link và mapping field → consumer trong A4. Trace sample chỉ chứng minh shape/carrier;
không dùng nó để claim independence, production coverage hoặc held-out nếu đã dùng chọn/tinh chỉnh.
Nếu field thiếu, hỏi AIE-1 bằng blocker có owner/ETA; không sửa interpreter trong lane evalhub.

### DoD

A4 có sample và mapping đầy đủ, hoặc có blocker cụ thể cho từng field thiếu. Không có field nào được đánh
dấu “đã xác nhận” chỉ từ suy luận.

## 9. T5 — Coverage matrix cho target golden-30

### Why

Golden-30 cần được kiểm acceptance trước khi giao đủ case; nếu không, D16 sẽ phải chọn coverage sau khi
đã thấy score.

### What

A5 có 30 target rows/slots, trong đó 9 case hiện có và 21 slot ghi `MISSING`/owner/ETA nếu chưa giao.
Mỗi row theo dõi:

- tenant: Ankor/Borea;
- role: public/hr/finance/engineering;
- T1 cross-tenant và T6 cross-role;
- retrieval/citation complexity;
- exact-match/subjective hand-label status;
- determinism/provenance;
- planned `n`, independent source/cluster status, scorer;
- candidate selection, held-out và tuning-round status.

### How

DE sở hữu case value/label; AIE-2 sở hữu matrix/consumer checks. Coverage phải được ghi trước khi chạy
selection. Không tính CI/ICC ở đây và không dùng matrix để tự sinh 21 case còn thiếu.

### DoD

A5 có đủ 30 rows/slots, owner cho mọi missing item và provenance status.

## 10. T6 — Evidence note và handover

### Why

D13 chỉ hoàn thành khi teammate có thể tiếp tục D14 mà không hỏi lại AIE-2 hoặc nhầm blocker data thành
bug code.

### What

A6 index A1–A5 và ghi:

- open dependency, owner, ETA;
- `k_success/n_cases` nếu có;
- `k_citation/n_citation_scored/n_refusal` hoặc `citation_metric=not_estimable`;
- production-gap/independence status;
- artifact chưa hoàn tất và next action;
- trạng thái các constraint tại §2, không chép lại methodology background.

### How

Viết theo format `FACT / FINDING / BLOCKER / NEXT ACTION`. Link tới artifact, command và SHA; không đưa
methodology background vào evidence note nếu không ảnh hưởng finding D13.

### DoD

A6 mở được độc lập, link đủ A1–A5, mọi blocker có owner/ETA và không còn câu claim không có artifact
chứng minh.

## 11. External dependencies

### Why

Các input sau nằm ngoài quyền tự sửa của AIE-2 nhưng ảnh hưởng trực tiếp tới việc đóng D13.

### What / How

| Owner | Request | Nếu chưa có cuối ngày |
|---|---|---|
| DE / @DongAnh2704 | Xác nhận KB `51df3a4`, annotation source, 9-case status, golden-30 date, source/cluster metadata nếu có | A6 ghi blocker; không sửa label/citation |
| AIE-1 / @TranBaDat2607 | Trace/fixture có chunks, citations, tenant_id, node_type, refused | A4 ghi field thiếu + ETA; không sửa engine |
| SWE / @Dozyboy | Xác nhận recipe tenant/role vocabulary không lệch corpus D12 | A6 ghi finding; không mở contract |
| Mentor/integrator | Xác nhận `week-2` page nếu tiếp tục 404 có thể bỏ qua ở D13 | Dùng kit#93/#94 + roadmap và ghi caveat |

### DoD

Mỗi request có response hoặc blocker trong A6; không có dependency mơ hồ kiểu “đang chờ”.

## 12. Finish verification

### Why

Checklist cuối ngày chỉ nên kiểm artifact và trạng thái thực tế, không lặp lại rationale của work item.

### What

Kiểm sự tồn tại, tính truy nguyên và trạng thái của A1–A6; không tạo thêm artifact mới ở bước này.

### How

Mở từng artifact từ A6, đối chiếu command/SHA/owner và đánh dấu checklist dưới đây. Nếu thiếu bằng chứng,
chuyển D13 sang `BLOCKED/PARTIAL`.

### Verify

- [ ] A1 tồn tại và chứa root/KB/evalhub SHA + baseline test output.
- [ ] A2 có đúng 9 row và trạng thái từng validation.
- [ ] A3 có per-case baseline/post-cutover comparison hoặc drift finding.
- [ ] A4 có trace sample mapping hoặc blocker theo field.
- [ ] A5 có 30 target rows/slots, owner của missing items và provenance status.
- [ ] A6 link đủ A1–A5, có owner/ETA cho mọi blocker.
- [ ] Không có thay đổi ngoài scope §2 trong D13.
- [ ] Plan và artifacts vẫn nằm ở local-only path; không có PR pointer mới cho PR#137.

### DoD

D13 PASS khi toàn bộ mục trên được verify. Nếu mục nào chưa đạt, trạng thái là `BLOCKED/PARTIAL`
với next action cụ thể, không đóng task bằng nhận xét chung chung.

## 13. Scope handoff

### Why

Handoff phải chỉ rõ D13 kết thúc ở đâu để không kéo công việc D16/D18 vào cùng ngày.

### What

- **D14 nhận:** corpus/golden provenance, smoke comparison, trace carrier và coverage matrix.
- **D16 nhận:** golden-30 sau khi DE giao đủ, scorer implementation và threshold decision đã có.
- **D18 nhận:** subjective cases và judge calibration decision.

### How

A6 là handoff entry point; người nhận bắt đầu bằng đọc A6 rồi mở artifact liên quan, không suy từ plan
đơn lẻ.

### DoD

D13 đóng với A6 và các dependency status; không implement hoặc commit deliverable thuộc D14/D16/D18.
