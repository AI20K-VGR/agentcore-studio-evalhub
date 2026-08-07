# B7 — D14 evidence note and D16/D18 handoff

**Ngày:** 2026-08-06 · **Owner:** AIE-2  
**Plan:** `day-14-aie2.md` §11–§14  
**Trạng thái:** **READY** — B1–B6 đều đã có evidence; B3 đã nhận current PG measurement với giới
hạn fixed candidate/config được ghi rõ.

## Artifact index

| ID | Artifact | Status |
|---|---|---|
| B1 | [workspace/source snapshot](B1-workspace.md) | **READY** |
| B2 | [trace carrier acceptance](B2-trace-carrier.md) | **READY** — DB round-trip evidenced |
| B3 | [retrieval measurement evidence](B3-retrieval-evidence.md) | **READY** — current PG measurement, bounded |
| B4 | [Golden-30 coverage acceptance](B4-coverage-acceptance.md) | **READY** — 30/30 |
| B5 | [judge optional ADR](B5-judge-optional-adr.md) | **READY** — `NO_BUMP` |
| B6 | [Q4 seam decision](B6-q4-seam-decision.md) | **READY** — `OPEN_MINI_RFC` |

## FACT

- Current root is `f1cc23b`, a local parent-pointer commit that includes the KB bump to merged kb#15
  main commit `b57ba78` and the D14 daily-note pointer; it is not pushed. Evalhub is `a60855d`, engine is `f50cab9`, and workbench is
  `e8a9899`. Baseline is `50 passed, 1 skipped, 2 xfailed, 0 XPASS`; ruff and import-linter are
  clean.
- KB#15 is merged. The current Golden30 source contains exactly 30 cases: 22 answerable and 8
  refusal. B4 is therefore complete at `30 FILLED + 0 MISSING`; AIE-2 did not generate or relabel any
  case.
- Current static evidence on the fixed candidate set gives `20/22` answerable expected citations at
  rank 1, with HB-09 at rank 4 and HB-20 at rank 3. This is not a current PG measurement or a
  population/threshold claim.
- AIE-1 supplied a current PG measurement at KB `b57ba78` using real Docker Postgres/pgvector,
  `PgKbSearch`, `BagOfWordsEmbedding`, `EMBEDDING_DIM=8`, and explicitly selected `top_k=10`: answerable
  `recall@1=5/22`, `recall@3=8/22`, `recall@5=11/22`, `recall@10=18/22`, `MRR=0.36`, with missing
  `HB-10`, `HB-11`, `HB-21`, `HB-22`; refusal fence is `8/8` with no citation denominator.
- The measurement ran through `PgKbSearch` directly. Engine/evalhub SHAs are provenance only for this
  report; no end-to-end `EngineAgentRunner`/`EvalHarness.run()` or live semantic gateway claim is made.
- The 30 cases are candidate/draft with no held-out split. The measurement script was ad hoc and
  untracked, with no CI link; this limits reproducibility but does not invalidate the named local run.
- AIE-1 supplied current-KB CI evidence for `PgTraceWriter → PgTraceReader`: run `31088981284`, head
  `b57ba78`, `186 passed, 2 xfailed, 0 skipped, 0 failed`; the non-default `TraceEvent` payload was
  read back equal field-by-field. The DB suite also covers event ordering/0-gap and tenant isolation;
  its spine integration fixture runs the real engine through writer, Postgres, and reader with a test
  LLM double.
- Current trace probing emits one `run_id` per in-memory case and four ordered events:
  `kb-retrieve → llm-step → tool-call → end`. `outputs["chunks"]` is on `kb-retrieve`; grounded
  `citations` are on `llm-step`. Stable hashes repeat; full event hashes are not stable because IDs
  and time are generated.
- `CaseResult.judge` is already optional; the reader audit found zero non-null production readers, so
  B5 rules `NO_BUMP`. `judge=None` remains the only honest pre-judge value.
- Two `EngineAgentRunner` implementations are present, so B6 rules `OPEN_MINI_RFC`; the existing RFC
  remains pre-written/local and no contract promotion was made.
- `studio-web#2` is approved and clean at commit `9a2ead95`, but the PR is not merged; therefore the
  web pointer remains `265fdd3` and was not changed in the local parent pointer.

## FINDING

- D13 and D14 snapshots have different SHAs/branch. D13 measurements are referenced with their own
  source SHAs and are not silently relabeled as current-SHA measurements.
- The former D13 F-4 is not a current blocker: the `citations` carrier clause is owned by AIE-1 and is
  present in engine `trace-citations.v0.md`, with the C-1 engine test locking `llm-step`-only carriage.
  The stale D13 note saying its owner was unassigned is not carried forward.
- The current static fixed-set probe is useful for ranking/fence inspection only. The historical PG
  measurement in A2-bis gives 2/7 at rank 1 and 2/7 outside top-5 under `EMBEDDING_DIM=8`; this is a
  configuration-scoped drift finding, not a population claim or a label rewrite.
- AIE-1 confirms `refused` is not a top-level `TraceEvent` field. Current engine output carries it as
  nested `TraceEvent.outputs["refused"]`, and the adapter maps the final-state value into
  `AgentAnswer.refused`; the current spine DB test reads the nested value back. The rule remains
  `refused = not citations`: a producer-defined structural signal, not an independent no-leak oracle.

## BLOCKER

**None for D14 evidence intake.** B2 persisted trace and B3 current PG measurement are now READY.
The remaining decisions are downstream: D16/DE must decide whether to create a held-out split and how
to set a threshold. Neither may be inferred from `recall@10=81.8%` or `MRR=0.36`.

Golden30 completion, trace persistence, and current PG measurement are no longer D14 blockers: kb#15
is merged, the current KB CI round-trip is green, the measurement ran locally on real Postgres/pgvector,
and the local root pointer has been updated to its merge commit. The parent pointer is local and
unpushed, so it still needs the normal parent PR/mentor flow before becoming shared branch state.

## NEXT ACTION

- **D16 receives:** B7 first; then B1–B6; the trace carrier split, fixed-set/static-vs-PG measurement
  caveats, complete 30-case matrix, `NO_BUMP` judge rule, and `OPEN_MINI_RFC` seam decision.
- **AIE-1:** measurement handoff is complete; no further B3 input is required for D14.
- **D16/DE:** decide held-out coverage and any threshold under the named PG config; do not convert this
  candidate-set result into a population claim.
- **Web follow-up:** wait for `studio-web#2` to merge before considering a web gitlink bump; it is
  separate from the completed D14 evidence intake.
- **D18 receives:** the not-estimable judge fields and the rule that no agreement constant may be
  assigned.

## OWNER

| action | owner | ETA |
|---|---|---|
| trace semantic/persistence handoff | AIE-1 / `@TranBaDat2607` | accepted via CI run 31088981284 |
| current PG measurement / F-8 baseline | AIE-1 / `@TranBaDat2607` | accepted; local Docker run 2026-08-06 |
| D16 loader/scorer | D16 AIE-2 lane | D16; date not supplied here |
| D18 judge calibration | D18 AIE-2 lane | D18; date not supplied here |
| parent pointer PR for local `f1cc23b` | AIE-2 / normal parent-repo flow | not opened in this execution |

## EVIDENCE

- [B1](B1-workspace.md) — current source SHAs, status, test baseline.
- [B2](B2-trace-carrier.md) — current carrier mapping and DB round-trip CI evidence; live-provider scope limit.
- [B3](B3-retrieval-evidence.md) — current Docker PG measurement, per-case ranks, fence results,
  historical comparison, and estimability boundary.
- [B4](B4-coverage-acceptance.md) — current 30-row coverage matrix, all source rows filled.
- [B5](B5-judge-optional-adr.md) — reader audit and `NO_BUMP` ruling.
- [B6](B6-q4-seam-decision.md) — `OPEN_MINI_RFC` trigger and next action.
- D13 inputs — `A2-intake`, `A2bis-intake-pg-validation`, `A4-trace-handoff`, `A5-coverage-matrix`,
  `A6-evidence`. **Chưa publish, cố ý không để link:** bộ A-series còn nằm local trong
  `.local-reviews/day13/` của máy AIE-2, và một link tới đó sẽ 404 với mọi người đọc khác — đúng lớp
  lỗi mà D15/T1 đang vá. Số liệu D13 mà B7 thật sự dùng đã được trích thẳng vào phần FACT/FINDING ở
  trên, nên bản này đọc được độc lập.

## D14 scope fence

Not done in this execution: `compute_scorecard`, `EvalHarness.run`, LLM judge implementation, scorer
leak-check changes, engine/KB/workbench/contracts changes, threshold/gate verdicts, or publish/rollback
wiring. No population or threshold `PASS` claim is made from the candidate-set PG measurement.
