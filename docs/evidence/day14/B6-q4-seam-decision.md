# B6 — D14 Q4 `AgentRunner` seam decision

**Ngày:** 2026-08-06 · **Owner:** AIE-2 · **Plan:** `day-14-aie2.md` §10  
**Trạng thái:** **READY**  
**Decision:** **`OPEN_MINI_RFC`**

## Input → command → output

**Input:** current `AgentRunner` Protocol, adapters, import-layering check, and pre-written
[`MRFC-2026-08-03-agentrunner-protocol-seam.md`](../../mini-rfc/MRFC-2026-08-03-agentrunner-protocol-seam.md).

**Commands:**

```bash
rg -n "^class (EngineAgentRunner|StubAgentRunner)|^class AgentRunner" \
  scripts/smoke_eval_d6.py apps/studio/src packages/evalhub/src packages/evalhub/tests
uv run lint-imports
```

**Output:**

```text
scripts/smoke_eval_d6.py:138:class EngineAgentRunner:
packages/evalhub/src/studio_evalhub/agent_runner.py:76:class AgentRunner(Protocol):
packages/evalhub/src/studio_evalhub/agent_runner.py:100:class StubAgentRunner:
apps/studio/src/studio_app/eval_adapter.py:46:class EngineAgentRunner:

Contracts: 1 kept, 0 broken.
```

## Decision and interpretation

The second adapter trigger exists in the workspace: the standalone smoke composition has its own
`EngineAgentRunner`, in addition to the `apps/studio` composition-root adapter. This is an observed
code fact; it is not a claim that both are production deployments. The current Protocol remains
internal to evalhub and layering is valid, but the “only one adapter” condition is no longer true.

Therefore D14 chooses **`OPEN_MINI_RFC`**. The pre-written RFC is a draft/decision input, not a
submitted contract change. No `AgentRunner` was promoted to `studio_contracts`, no schema was changed,
and no RFC was submitted by this local-only execution.

## Next action

Owner: **AIE-2 + AIE-1**. Update the RFC with the two adapter contexts and resolve its currently open
return-type/`CaseRun` shape question before requesting any shared-contract signatures. D16 can continue
using the internal seam while that decision is reviewed; this decision itself does not block loader or
scorer input work.

