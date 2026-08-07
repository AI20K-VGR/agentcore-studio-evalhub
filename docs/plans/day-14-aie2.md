# Plan Day 14 — AIE-2 · Trace evidence, retrieval handoff và decision pack

**Ngày:** 2026-08-06  
**Mode:** execution plan  
**Owner:** AIE-2  
**Scope:** D14 only; đọc kết quả từ trace, acceptance evidence và quyết định seam. Không implement scorer,
judge hoặc golden-30.

> D14 của AIE-2 là ngày **tiêu thụ bằng chứng** do DE/AIE-1 cung cấp: xác nhận evalhub đọc đúng trace
> carrier, phân biệt data finding với engine finding, chuẩn bị coverage cho D16 và đóng các quyết định
> còn hạn D14. AIE-2 không sửa label của DE và không sửa interpreter để làm evidence xanh.

## 1. Mục tiêu và kết quả cuối ngày

### Vì sao

D16 sẽ bắt đầu từ một bộ dữ liệu và một trace đã được hiểu đúng. Nếu evalhub đọc nhầm carrier — ví dụ
đọc citation từ `AgentAnswer.citations` thay vì event, hoặc suy `refused` từ số chunk — mọi score sau đó
đều có thể xanh giả. D14 cần đóng đường đọc và ghi rõ phần nào đã chứng minh, phần nào vẫn chưa đo được.

### Cần làm

Hoàn tất bảy kết quả:

1. Snapshot workspace, corpus và các SHA dùng để đọc evidence.
2. Xác nhận trace carrier với AIE-1 theo từng field, không suy diễn field còn thiếu.
3. Đọc measurement output của AIE-1 theo source/config và bằng chứng sẵn có; không biến sample thành claim
   về population.
4. Acceptance-check coverage matrix 30 slot: 9 case hiện có và 21 slot còn thiếu.
5. Viết ADR cho luật đổi `judge: required → optional` và kiểm tra reader non-null.
6. Quyết định D14 về Q4 `AgentRunner` Protocol seam: giữ nội bộ hay mở mini-RFC nếu đã xuất hiện
   adapter thứ hai.
7. Đóng evidence note và handoff cho D16, kèm owner/ETA cho mọi blocker.

### Không phải mục tiêu

- Không implement `compute_scorecard`, `EvalHarness.run` hoặc LLM judge.
- Không tạo đủ 30 golden case; DE sở hữu case value/label, D16 mới chốt golden-30.
- Không sửa `expected`, `expected_citation` hoặc trace producer để xoá discrepancy.
- Không promote `AgentRunner` lên `studio_contracts` nếu chưa có trigger kiến trúc thật.

### DoD tổng

Evidence B1–B7 tồn tại, mở độc lập được, có command/input/output hoặc blocker cụ thể; mỗi artifact có
kết luận `READY` hoặc `BLOCKED`, và mọi blocker có owner cùng ETA. Không có claim “PASS” chỉ dựa trên
test shape hoặc một trace sample.

## 2. Ràng buộc cố định

| Ràng buộc | Luật D14 |
|---|---|
| Source of truth | Dùng kit SHA, KB SHA, engine SHA và evalhub SHA được ghi ở B1; không đọc bản copy không có SHA. |
| Golden input | 9 case `HB-01..HB-09` vẫn là draft/skeleton; 30 case đầy đủ thuộc D16. |
| Ownership | DE sở hữu case value/label; AIE-1 sở hữu interpreter/trace producer; AIE-2 sở hữu intake, consumer validation và evidence. |
| Citation source | Chấm/kiểm citation từ event carrier trong trace, không tin citation tự khai trên `AgentAnswer`. |
| Retrieval source | `kb-retrieve.outputs["chunks"]` là retrieved set; không suy retrieved set từ LLM answer. |
| Refusal | Chỉ ghi `refused` theo carrier đã freeze; không tự đổi convention vì sample hiện tại. |
| Citation denominator | Refusal không phải citation observation; `n=0` phải ghi `not_estimable`. |
| Measurement claim | Ghi source/config và bằng chứng sẵn có; planned/actual `n`, candidate/held-out, source/cluster và tuning rounds nếu được cung cấp; thiếu thì ghi `UNKNOWN`/`NOT_ESTIMABLE`, không tự tạo blocker. |
| Contract | Không thêm field, rename field hoặc bump schema trong evalhub chỉ để phục vụ D14. |
| Scope fence | Không sửa engine, KB, workbench, contracts hoặc golden label trong lane AIE-2. |
| Prep vs ship | Plan và review artifacts nằm trong `docs/plans/`/`.local-reviews/`, local-only; không mở PR deliverable chỉ để ship plan. |

## 3. Artifact contract

Các artifact dưới đây dùng local-only path `.local-reviews/`. Tên file là đề xuất cố định để D16 có thể
đọc lại mà không hỏi lại AIE-2.

| ID | Artifact | Nội dung bắt buộc |
|---|---|---|
| B1 | `.local-reviews/day14/B1-workspace.md` | root/evalhub/KB/engine SHA, branch/status, commands, test baseline |
| B2 | `.local-reviews/day14/B2-trace-carrier.md` | sample trace hash/link và mapping `field \| carrier \| consumer \| status \| notes` |
| B3 | `.local-reviews/day14/B3-retrieval-evidence.md` | measurement source/config, available evidence, findings, limitations và estimability |
| B4 | `.local-reviews/day14/B4-coverage-acceptance.md` | 30 target rows: 9 existing + 21 missing, status, owner, ETA và provenance |
| B5 | `.local-reviews/day14/B5-judge-optional-adr.md` | reader audit, quyết định `judge` optional, compatibility/bump ruling, next action |
| B6 | `.local-reviews/day14/B6-q4-seam-decision.md` | decision `KEEP_INTERNAL` hoặc `OPEN_MINI_RFC`, kèm trigger/next action nếu có |
| B7 | `.local-reviews/day14/B7-evidence.md` | index B1–B6, FACT/FINDING/BLOCKER/NEXT ACTION, handoff D16 |

Mỗi artifact phải ghi `input → command → output → interpretation`. Nếu không có input, ghi `BLOCKED`,
lý do, owner và ETA; không thay bằng `PASS` hoặc “đang chờ” không có hạn.

## 4. Dependency intake đầu ngày

### Cần nhận từ D13

- A6/evidence handoff của D13 hoặc các artifact tương đương.
- KB/corpus provenance và SHA.
- 9-case status của `HB-01..HB-09`.
- Smoke comparison sau KB cutover.
- Coverage matrix 30 slot hoặc danh sách 21 slot còn thiếu.

### Cần hỏi AIE-1

Xin một trace/fixture đại diện và mapping cho các field sau:

| Field | Câu hỏi cần trả lời |
|---|---|
| `outputs["chunks"]` ở `kb-retrieve` | Đây có phải toàn bộ retrieved set của run không? Shape chunk gồm những gì? |
| `citations` | Event nào là carrier chính? Citation đã grounded với retrieved set chưa? |
| `tenant_id` | Lấy từ session hay recipe/node params? |
| `node_type` | Có đủ phân biệt `kb-retrieve`/`llm-step` để consumer chọn carrier không? |
| `refused` | Nằm ở output node nào, semantic đã freeze chưa? |
| `run_id`/event list | Một case có đúng một run và thứ tự event deterministic không? |

Nếu AIE-1 chưa có trace sample, tạo B2 ở trạng thái `BLOCKED` theo từng field; không lấy fixture cũ làm
bằng chứng thay thế mà không ghi rõ SHA và khác biệt.

### Cần hỏi DE

- 9 case nào đã được kiểm provenance bằng doc-factory?
- Citation nào là expected thật, citation nào chỉ là draft?
- Có source/cluster/independent unit metadata không?
- Query nào answerable, query nào refusal T1/T6?
- Ngày dự kiến giao đủ 30 case là ngày nào?

Mọi câu trả lời phải được chuyển thành fact trong B3/B4, không để ở chat-only.

## 5. T1 — Pre-flight và baseline

### Vì sao

Trước khi đọc một con số, phải biết con số đó thuộc kit/corpus/engine nào. D13 đã có nhiều pointer và
local plan tracking; không được trộn local HEAD với root gitlink.

### Cách làm

Chạy và lưu output vào B1:

```bash
git status --short --branch
git rev-parse HEAD
git submodule status
git -C packages/evalhub status --short --branch
git -C packages/evalhub rev-parse HEAD
git -C packages/evalhub rev-parse origin/main
git -C packages/kb rev-parse HEAD
git -C packages/engine rev-parse HEAD
uv run pytest packages/evalhub/tests -q
uv run ruff check packages/evalhub
```

Nếu baseline khác expected của D13, ghi `FINDING` với diff; không sửa expected để đưa test về xanh.

### DoD

B1 có đủ SHA, status, command và output thực tế. Có một kết luận rõ: `READY` hoặc `BLOCKED` với owner + ETA.

## 6. T2 — Trace carrier acceptance

### Vì sao

Evalhub phải đọc đúng dữ liệu producer phát ra trước khi D16 xây harness. Một field được “thấy trong
fixture” nhưng không có producer contract hoặc không có scope/run binding thì chưa phải evidence.

### Cách làm

Lập bảng B2 với các cột:

```text
field | carrier | consumer | status | notes
```

File/line chỉ ghi trong `notes` khi cần debug; không phải cột bắt buộc.

Kiểm tra tối thiểu:

- Xác nhận carrier và tất cả field được producer contract định nghĩa hoặc claim; không mặc định yêu cầu
  `chunk_id`, `tenant_id`, `section_role` hoặc `score` nếu contract không claim các field này.
- Nếu contract định nghĩa `kb-retrieve.outputs.chunks` là retrieved set, xác nhận đó là danh sách retrieved
  chunks, không phải danh sách LLM đã trích.
- Nếu producer contract claim `citations`, xác nhận citations lấy từ đúng event carrier và chỉ được xem là
  grounded khi đối chiếu được với retrieved set.
- Nếu có `tenant_id`, xác nhận tenant của event khớp session scope; recipe claim không được xem là
  authorization proof.
- Nếu có `node_type`, xác nhận dùng được để phân biệt carrier; tool output có key `citations` không được
  tính là citation.
- Nếu có `refused`, chỉ map khi semantic đã được producer xác nhận; nếu chưa, ghi `shape-only`.
- Nếu contract định nghĩa `run_id` hoặc event ordering, xác nhận các event thuộc cùng run và có thứ tự;
  không suy diễn binding ngoài contract.
- Với optional metadata, verify nếu có; nếu không có, ghi `NOT_PROVIDED` thay vì tạo blocker.

Không sửa code nếu field thiếu. Ghi `BLOCKED` chỉ khi thiếu carrier, field bắt buộc theo producer contract
hoặc core evidence; optional metadata thiếu chỉ ghi `NOT_PROVIDED`. Mọi blocker phải có owner, impact tới
D16 và ETA cần thiết.

### DoD

B2 có mapping cho các field producer contract định nghĩa/claim; optional metadata không có được ghi
`NOT_PROVIDED`. Chỉ ghi blocker cho carrier, field bắt buộc theo contract hoặc core evidence bị thiếu.
Không có dòng “confirmed” chỉ vì test constructor hoặc test fixture parse được.

## 7. T3 — Retrieval measurement evidence review

### Vì sao

D14 có measurement chunking × embedding từ AIE-1, nhưng AIE-2 cần xác định nó đang đo cái gì: retrieval
quality thật, fence behavior, hay chỉ là smoke ranking. Nếu không tách ba thứ này, scorecard D16 sẽ nhận
một baseline sai tầng.

### Cách làm

Đối chiếu measurement report với:

- measurement source/config;
- available trace/case evidence;
- findings và limitations;
- estimability của từng kết quả.

Metadata như candidate count, held-out status, top-k, expected chunk hoặc provenance chi tiết chỉ ghi
khi dependency đã cung cấp. Nếu thiếu, ghi `UNKNOWN` hoặc `NOT_ESTIMABLE`; không tạo blocker chỉ vì
thiếu metadata ngoài scope D14.

Với từng case, ghi tối thiểu:

```text
case_id | available evidence | status | finding/limitation
```

Phân loại kết quả:

- `RETRIEVAL_EVIDENCE`: ranking chọn đúng trong một tập có nhiều candidate hợp lệ;
- `FENCE_EVIDENCE`: chunk ngoài tenant/role bị loại trước ranking;
- `NOT_ESTIMABLE`: measurement hoặc metadata hiện có chưa đủ để đưa ra claim;
- `DRIFT`: khác baseline cần truy nguyên về corpus/chunking/embedding/adapter/trace;
- `BLOCKED`: thiếu measurement input hoặc producer evidence cốt lõi, không phải chỉ thiếu metadata.

Không gọi `6/6` là quality guarantee. Report phải ghi rõ sample size và giới hạn của bộ đo.

### DoD

B3 có source/config, available evidence, findings, limitations và estimability. Mọi metadata không được
cung cấp đều bị hạ thành `UNKNOWN` hoặc `NOT_ESTIMABLE`, không tự tạo blocker.

## 8. T4 — Coverage acceptance cho Golden-30

### Vì sao

Golden-30 là input D16. AIE-2 phải đảm bảo biết mình đang thiếu gì trước khi scorer nhìn thấy kết quả;
không được chọn thêm case sau khi xem score.

### Cách làm

Tạo hoặc refresh B4 với đúng 30 dòng:

- `HB-01..HB-09`: ghi status và provenance hiện có;
- `HB-10..HB-30`: ghi `MISSING` nếu chưa có, kèm owner, ETA và provenance (`UNKNOWN` nếu chưa được cung cấp).

Không tự sinh 21 case và không đổi nhãn DE trong T4. Nếu coverage thiếu, đó là dependency D16 với owner
DE, không phải lý do để AIE-2 lấp bằng case giả.

### DoD

B4 có đủ 30 rows/slots; mỗi row có status, owner, ETA và provenance. Thiếu provenance ghi `UNKNOWN`,
không tạo blocker chỉ vì thiếu metadata ngoài dependency hiện có.

## 9. T5 — ADR `judge: required → optional`

### Vì sao

Payload cũ có thể vẫn validate sau khi field thành optional, nhưng reader cũ có thể vẫn giả định non-null.
Đây là “wire-compatible nhưng reader-incompatible”, nên không được suy ra rằng không bump schema chỉ vì
Pydantic parse vẫn xanh.

### Cách làm

Audit reader bằng lệnh:

```bash
rg -n "\.judge\b|judge=" packages apps scripts tests
rg -n "Judge\(" packages apps scripts tests
```

Ghi vào B5:

- danh sách reader/constructor đã kiểm;
- reader nào xử lý `None`;
- reader nào còn giả định non-null;
- quyết định có/không bump `SCHEMA_VERSION`;
- migration/compatibility rule cho D16;
- test cần thêm hoặc test đã đủ;
- owner/ETA nếu còn reader chưa xử lý.

Quy tắc mặc định: `judge=None` nghĩa là case chưa qua LLM-judge; không bịa `Judge(agreement=1.0)`.

Nếu cần sửa tracked decision-log, chỉ sửa sau khi decision owner/review đã rõ. Bản draft/analysis giữ ở
B5, không biến plan thành contract mới.

### DoD

B5 có ruling rõ `NO_BUMP` hoặc `BUMP_REQUIRED`, có bằng chứng reader count và next action. Không để trạng
thái “optional nhưng chưa biết reader” ở dạng đã đóng.

## 10. T6 — Quyết định Q4 AgentRunner seam

### Vì sao

Mini-RFC đã được viết sẵn nhưng D11 chủ ý chưa promote. D14 là mốc kiểm tra điều kiện mở, không mặc định
phải thêm Protocol vào contracts.

### Cách làm

Đưa ra đúng một decision dựa trên trigger hiện có:

- `KEEP_INTERNAL` nếu chưa có adapter thứ hai và D16 không bị chặn khi giữ seam nội bộ.
- `OPEN_MINI_RFC` nếu đã có adapter thứ hai hoặc dependency D16 thực sự cần seam chung.

Không submit hoặc chuẩn bị RFC chỉ để tick một ô D14. B6 chỉ cần ghi decision, lý do và next action nếu
đã có trigger thực sự.

### DoD

B6 có một trong hai decision `KEEP_INTERNAL` hoặc `OPEN_MINI_RFC`. Nếu chưa đủ input để quyết định,
ghi `BLOCKED` kèm owner + ETA; không cần consumer table hoặc RFC preparation khi chưa có trigger.

## 11. T7 — Evidence note và handoff D16

### Vì sao

D16 cần bắt đầu từ bằng chứng đã phân loại, không phải đọc lại toàn bộ chat/plan và tự đoán blocker.

### Cách làm

B7 index B1–B6 theo format:

```text
FACT:
FINDING:
BLOCKER:
NEXT ACTION:
OWNER:
ETA:
EVIDENCE:
```

B7 phải ghi rõ:

- trace carrier nào đã xác nhận và carrier nào chỉ shape-only;
- measurement nào estimable/not-estimable;
- 9 case nào ready, 21 slot nào missing;
- ADR ruling và Q4 ruling;
- dependency DE/AIE-1/SWE/mentor;
- việc D16 nhận: loader/scorer input/threshold follow-up;
- việc D18 nhận: subjective cases/judge calibration;
- việc không làm lại ở D14.

### DoD

B7 mở độc lập được, link đủ B1–B6, mọi blocker có owner/ETA, không còn câu claim không có command/SHA/
case/trace hỗ trợ.

## 12. Lịch thực thi trong ngày

| Khung | Việc | Đầu ra |
|---|---|---|
| Đầu giờ | T0 dependency intake, request trace + D13 handoff | danh sách input/blocked rõ owner |
| 09:00–10:00 | T1 pre-flight/baseline | B1 |
| 10:00–12:00 | T2 trace carrier acceptance | B2 + blocker AIE-1 |
| 13:00–14:30 | T3 measurement evidence review | B3 |
| 14:30–15:30 | T4 coverage acceptance | B4 |
| 15:30–16:15 | T5 ADR judge optional | B5 |
| 16:15–16:45 | T6 Q4 seam decision | B6 |
| 16:45–17:30 | T7 evidence, handoff, daily note | B7 + D16 handoff |
| Cuối ngày | Finish verification | READY/BLOCKED có lý do |

Nếu dependency AIE-1/DE chưa sẵn sàng cho T2/T3, chuẩn bị blocker package/evidence với owner + ETA,
sau đó tiếp tục B1/B4/B5 và các task độc lập; không chờ toàn bộ ngày và không giả lập trace để làm B2
xanh.

## 13. Finish verification

- [ ] B1 có root/evalhub/KB/engine SHA và test baseline.
- [ ] B2 có field mapping cho chunks, citations, tenant, node type, refused, run id.
- [ ] B3 có measurement source/config, available evidence, findings, limitations và estimability status.
- [ ] B4 có đúng 30 rows/slots, 9 existing + 21 missing, status/owner/ETA/provenance.
- [ ] B5 có reader audit và ruling `NO_BUMP`/`BUMP_REQUIRED`.
- [ ] B6 có decision `KEEP_INTERNAL` hoặc `OPEN_MINI_RFC`; nếu blocked thì có owner/ETA.
- [ ] B7 index đủ B1–B6, format FACT/FINDING/BLOCKER/NEXT ACTION.
- [ ] Không có scorer/judge/golden-30 implementation trong D14.
- [ ] Không sửa label để xoá discrepancy.
- [ ] Mọi blocker đều có owner và ETA.
- [ ] Daily note ghi đúng `READY` hoặc `BLOCKED` với owner/ETA nếu dependency chưa giao.

### Trạng thái đóng ngày

- `READY`: B1–B7 đủ để handoff, không còn blocker không owner.
- `BLOCKED`: một hoặc nhiều artifact phụ thuộc dữ liệu chưa giao; blocker có owner + ETA, và các task độc lập
  đã được hoàn tất.

Không dùng `PASS` chỉ vì pytest xanh; test shape không thay thế trace evidence.

## 14. Scope handoff

### D16 nhận từ D14

- trace carrier mapping đã xác nhận;
- retrieval evidence và caveat về sample/estimability;
- coverage matrix 30 slot;
- ADR `judge` optional và reader rule;
- Q4 seam decision;
- danh sách blocker với owner/ETA.

### D18 nhận từ D14

- danh sách case cần subjective label;
- các field judge còn thiếu hoặc chưa estimable;
- constraint không được gán agreement constant.

### D14 không nhận từ ngày sau

- scorer implementation và eval-gate verdict: D16;
- LLM judge/cache/agreement: D18;
- publish/rollback wiring: SWE/S3;
- fence implementation: D17.

### Quy tắc handoff

B7 là entry point. Người nhận bắt đầu bằng B7, sau đó mở B1–B6; không suy trạng thái từ plan này nếu
artifact thực tế có finding mới.
