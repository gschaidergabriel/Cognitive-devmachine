# Level-0 Shard — Project-Frankenstein Autonomous Research

## Scope

This shard recovers Project-Frankenstein's autonomous idle-research mechanism from its first implementation through frozen HEAD and maps it against the current RAE evidence/provenance standard.

## Historical lineage

### Introduction — 2026-02-25

Commit `d2c08bacbfd6a7ffae309a190e707582a809a351` added an idle-driven research loop:

`idle thought -> research-worthiness decision -> bounded plan -> restricted tools -> synthesis -> memory -> autonomy reward`

Limits included 15 minutes user idle, one-hour cooldown, five sessions/day and ten tool calls/session. The implementation described the tool set as low-risk/read-only, but already included `memory_store` and sandboxed `code_execute`, so the label did not match the actual effect set.

### Persistence failures and repair

Commit `92791d1cf0c2580688da1666d6e32386beaa5139` documents that autonomous research had been POSTing memories to a nonexistent `/memory/store` endpoint (404). The fix wrote the synthesis directly to `consciousness.db`; it also added a missing `threading` import.

Commit `07f8e26a296cf5bdcd4add14ee42ab501d09422b` later records another autonomous-research HTTP 404 repair through direct Titan Python calls. The repeated endpoint drift is a concrete ancestor of the current requirement for typed, tested contracts and read-after-write receipts.

## Frozen-head state

At frozen HEAD `abba90a5767d85abc8a1ac340bae92842dab35c1`:

- `services/autonomous_research.py` remains present;
- `services/consciousness_daemon.py` calls `_maybe_autonomous_research()` every third idle-thought count;
- cooldown is 30 minutes, max five sessions/day;
- tool scope includes web, memory, files, code, experiments, hypotheses and paper search/read;
- `web_fetch` has a curated domain whitelist;
- the decision prompt strongly encourages research unless the thought is purely emotional.

This is a verified source integration hook. It does not by itself establish how many historical live sessions actually completed.

## Current frozen-head authority defect

Autonomous code execution invokes the general executor with `skip_approval=True` and `sandbox_code_execution=True`.

The frozen-head executor explicitly behaves as follows:

- if Firejail exists, wrap code with filesystem/network/resource restrictions;
- if Firejail does **not** exist, `_build_firejail_cmd()` returns the raw inner command and logs that bash/code execution will run unsandboxed.

Therefore the research path is not fail-closed on sandbox availability. This is conditional on the host lacking Firejail; source alone does not establish whether the historical live host hit that branch.

Modern invariant:

`requested_sandbox && sandbox_unavailable => refuse execution`

not fallback-to-unsandboxed.

## Evidence-chain limitation

The historical research session DB stores session-level fields such as question, plan, tool-call count, synthesis, status and duration. The execution path concatenates/truncates step results and truncates the combined results before synthesis. The memory path stores the synthesis as a reflection.

This is useful orchestration, but it is not an evidence-complete research ledger. The module does not establish durable per-step raw evidence bodies/hashes/source classes/claim states/negative-result links.

Modern invariant:

`synthesis != evidence`

The full lineage should be:

`research run -> step -> capability request -> raw evidence -> source hash/class -> claim/negative result -> synthesis -> validated memory promotion`

## Reusable mechanisms

- curiosity/idle trigger for slow-loop research;
- hard daily/session/tool budgets;
- bounded research plans;
- explicit tool allowlists and web domain allowlists as defense layers;
- experiment/hypothesis/paper tools inside the research loop;
- persistent research session state.

These are reusable only under current capability, provenance and fail-closed semantics.

## Branch implications

- **FRANK:** curiosity may propose research; it does not grant effects. Reward novelty/process discipline separately from truth.
- **Harness:** test no-sandbox refusal, persistence write/readback, per-tool source receipts and budget enforcement.
- **ClayCode:** research plan steps are typed capability requests, not generic read-only tools.
- **UnifiedDB:** make raw evidence and derived synthesis separate first-class objects.
- **ClayGraph:** research results become provenance-weighted claims, not truth edges.
- **GWT:** autonomous research can be a slow-loop re-entry source, not consciousness evidence.
- **Emergenz:** research/experiments supply interventions; question generation alone is not emergence.

## Coverage

- exact Level-0 coverage credit: `0.0`;
- new historical earned-work hours: `0.0` pending row-level deduplication;
- full PF history/tree denominator remains unfrozen.

Durable receipt:
`research_entity/archive_assimilation/receipts/666_20260809T1416p0700_chatgpt_secondary_pf_autonomous_research_lineage.json`
