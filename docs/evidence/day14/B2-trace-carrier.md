# B2 — D14 trace carrier acceptance

**Ngày:** 2026-08-06 · **Owner:** AIE-2, với persisted-trace evidence từ AIE-1  
**Plan:** `day-14-aie2.md` §6  
**Trạng thái:** **READY** — carrier mapping và `PgTraceWriter → PgTraceReader` persistence
round-trip đã có evidence ở current KB main. CI cũng có spine test chạy interpreter thật qua writer,
database và reader; LLM trong test là fixture/double, không phải live provider run.

## Input → command → output

**Input:** current source snapshot trong [B1](B1-workspace.md); producer contract
[`TraceEvent`](https://github.com/AI20K-VGR/agentcore-studio-contracts/blob/main/src/studio_contracts/trace.py), engine clause
[`trace-citations.v0.md`](https://github.com/AI20K-VGR/agentcore-studio-engine/blob/main/docs/contracts/trace-citations.v0.md), current
`interpreter.py`, `eval_adapter.py`, current in-memory smoke evidence, và AIE-1 persisted-trace CI
evidence tại KB `b57ba78`.

**Persisted-trace test:**

```text
packages/kb/tests/test_trace_reader.py::test_db_doc_lai_nguyen_ven_tung_truong
PgTraceWriter.write(...) → PgTraceReader.read_run("run-payload", ANKOR_ID)
assert events == [goc]  # equality trên toàn bộ Pydantic TraceEvent
```

**CI output thực tế do AIE-1 cung cấp:**

- CI run: [31088981284](https://github.com/AI20K-VGR/agentcore-studio-kb/actions/runs/31088981284)
- head SHA: `b57ba78ab936061cc487b76f1d6a47684f993a01`
- result: `186 passed, 2 xfailed, 0 skipped, 0 failed in 2.53s`
- DB group chạy với pgvector container và DSN thật; không bị fixture skip.
- Payload test có `outputs["chunks"]`, hai citations, UUID tenant, tokens khác 0 và cost khác 0;
  round-trip được so sánh toàn bộ model, không chỉ một vài cột.
- Các DB test cùng file còn kiểm tra thứ tự/0-gap, cách ly theo `run_id`, và không đọc chéo tenant.
- Cùng CI suite có `packages/kb/tests/test_spine_live.py`: chạy `studio_engine.run()` với
  `PgTraceWriter`, đọc lại bằng `PgTraceReader`, so sánh event DB với event trong RAM, kiểm tra
  citation đọc từ DB và kiểm tra refusal từ event đọc từ DB. Đây là integration fixture với LLM
  double, không phải production live-provider evaluation.

**In-memory producer probe:** `EngineAgentRunner.run_case` trên SC-01 và SC-05 cũng đã được chạy
hai lần. Mỗi mẫu có một `run_id` và bốn event theo thứ tự `kb-retrieve → llm-step → tool-call →
end`; stable hashes lặp lại, còn full event hashes thay đổi vì ID/time được tạo mới.

## Carrier mapping

| field | carrier | consumer | status | notes |
|---|---|---|---|---|
| `outputs["chunks"]` | `TraceEvent.outputs` trên `node_type=kb-retrieve` | D16 retrieval/fence reader; current evalhub chưa dùng list này trong `citations_from_trace` | **CONFIRMED** | In-memory sample có `list[3]`; persisted DB test ghi/đọc lại payload `chunks`. Retrieved và grounded là hai observation khác nhau. |
| `citations` | `TraceEvent.citations` trên `node_type=llm-step` | current `citations_from_trace`; D16 citation consumer | **CONFIRMED** | In-memory sample chỉ mang citations ở `llm-step`; persisted DB test xác nhận citations được giữ nguyên khi đọc lại. |
| `tenant_id` | `TraceEvent.tenant_id`; cũng có trong từng chunk của `outputs["chunks"]` | `tenant_scope_ok`, trace reader, D16 scope check | **CONFIRMED** | DB test dùng UUID và test riêng xác nhận cùng `run_id` nhưng khác tenant trả `[]`. Recipe tenant không phải authorization proof. |
| `node_type` | `TraceEvent.node_type` | carrier selection và timeline reader | **CONFIRMED** | DB test xác nhận payload/event; test order xác nhận walk `kb-retrieve → llm-step → tool-call → end`. |
| `refused` | Không phải top-level field của `TraceEvent`; engine hiện đặt nó trong `TraceEvent.outputs["refused"]` ở `llm-step`, rồi adapter map cùng giá trị vào `AgentAnswer.refused` | refusal scorer / D16 eval-result consumer | **CONFIRMED — carrier distinction** | `PgTraceWriter/PgTraceReader` không có cột riêng cho `refused`, nhưng nested output được persist/read lại. Current `test_spine_live.py` đọc event từ DB và assert `llm.outputs["refused"]`. Producer rule hiện tại là `refused = not citations`; đây là structural signal, không phải independent no-leak oracle. |
| `run_id` / event list | `TraceEvent.run_id` trên mọi event; `PgTraceReader` đọc theo `(run_id, tenant_id)` và order theo timestamp/event id | D16 run binding và timeline reader | **CONFIRMED** | Current CI đã read-back `run-payload`; DB tests thêm order, 0-gap và tenant isolation. Không phải live production-provider run. |

Optional metadata không được producer contract claim không bị biến thành blocker. Không thêm field
`refused` vào trace contract chỉ để phục vụ D14.

## Interpretation and scope limit

B2 đủ để D16 dùng các carrier sau: retrieved chunks từ `kb-retrieve.outputs`, grounded citations từ
`llm-step`, tenant/run binding từ `TraceEvent`, và đọc lại persisted event theo `(run_id, tenant_id)`.
`PgTraceWriter → PgTraceReader` đã được chứng minh trên current KB main bằng DB-backed CI test với
payload không mặc định.

Evidence này chứng minh integration fixture `studio_engine.run() → PgTraceWriter → Postgres →
PgTraceReader`; không phải production live-provider evaluation và không phải một phép đo PG retrieval.
Không gộp hai giới hạn đó vào kết luận persistence hiện tại.
