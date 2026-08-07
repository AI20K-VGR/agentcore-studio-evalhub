# B5 — ADR: `judge: required → optional`

**Ngày:** 2026-08-06 · **Owner:** AIE-2 · **Plan:** `day-14-aie2.md` §9  
**Trạng thái:** **READY** — reader audit found zero production readers assuming non-null; ruling is
`NO_BUMP`.

## Input → command → output

**Input:** current `packages/contracts/src/studio_contracts/scorecard.py`, evalhub harness/render/judge,
tests, decision log, and scorecard contract docs.

**Commands:**

```bash
rg -n "\.judge\b|judge=" packages apps scripts tests
rg -n "Judge\(" packages apps scripts tests
uv run pytest packages/contracts/tests/test_roundtrip.py -q
uv run pytest packages/evalhub/tests/test_scorecard_roundtrip.py packages/evalhub/tests/test_render.py -q
```

**Output:** the grep found `CaseResult.judge` references in docs/comments and test fixtures, but no
production reader dereferencing `result.judge`; `Judge(...)` constructors occur in contract/test
fixtures and test assertions. Relevant checks:

```text
packages/contracts/tests/test_roundtrip.py: 11 passed
packages/evalhub/tests/test_scorecard_roundtrip.py packages/evalhub/tests/test_render.py:
10 passed, 1 skipped
```

## Reader/constructor audit

| reader/constructor | `None` handling | evidence | status |
|---|---|---|---|
| `CaseResult` in `packages/contracts/src/studio_contracts/scorecard.py` | `judge: Judge \| None = None` | current contract source | **CONFIRMED** |
| `render_scorecard` | renders aggregate/gate; does not dereference `CaseResult.judge` | current `packages/evalhub/src/studio_evalhub/render.py` + grep | **CONFIRMED** |
| `EvalHarness` / `compute_scorecard` | no current `CaseResult` production construction; `run`/compute remain `NotImplementedError` | current harness/compute source | **NOT_IMPLEMENTED, not a non-null reader** |
| `LLMJudge` | only a future producer; no `Judge(...)` constant is allowed | current `judge.py` + test guard | **CONFIRMED** |
| contract/evalhub test fixtures | pass explicit real-shaped `Judge` or explicit `None` | round-trip/render test output above | **CONFIRMED** |

## Decision

**`NO_BUMP`.** Making an existing required field optional is wire-compatible: old payloads carrying a
real `Judge` remain valid, and omitted `judge` parses as `None`. Current reader audit count is **0
non-null readers**. The fact that `judge.py` and D18 are not implemented is not evidence to fabricate a
judge result.

Rule for D16/D18: `judge=None` means “this case did not run through the LLM judge”; create a `Judge`
only after a real judge run and its agreement evidence exists. Never use `Judge(agreement=1.0)` or any
other constant.

## Compatibility / next action

- No `SCHEMA_VERSION` bump is required by this ruling.
- D16 loader/scorer must preserve omitted `judge` as `None` and must not infer a judge from exact-match
  or refusal cases.
- D18 owns real judge calls, hand-label comparison and calibration; no blocker remains in this ADR.

