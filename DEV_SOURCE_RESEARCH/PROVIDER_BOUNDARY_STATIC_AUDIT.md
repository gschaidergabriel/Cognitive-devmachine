# Frankenstein provider-boundary static audit

**Scope:** source-only, non-network Triggerword-3 audit against canonical `main` `854f6bc87780f4a5242489a6c807d186b16a8c3d`.

**Evidence class:** `CURRENT_SOURCE` + `NEGATIVE_RESULT`.

**Runtime credit:** none. This audit does not execute a provider, read a secret, or prove runtime quiescence.

## Authority condition

`research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` at the observed head states:

- provider routes admitted: `false`
- Together: forbidden
- paid fallback: forbidden
- Free-Swarm emergency stop: active
- runtime quiescence required before new provider execution
- Frankenstein 72h provider orchestration: quarantined/non-operative

It also names the real external FreePool caller boundary as a P0 open issue.

## Finding A — orchestrator imports provider machinery before any gate

Path:

`research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_orchestrator_v1.py`

The module startup path:

1. inserts `~/last-resort` into `sys.path`;
2. imports `llm as pool_llm`;
3. imports `requests`;
4. defines `call_specific_tier()` which iterates `pool_llm._tiers()` and performs `requests.post(...)` using bearer keys;
5. defines `dispatch_helper_task()` which invokes `~/.claude/star/harness_aider.py fallback-start`.

There is no canonical provider-authority gate **before those provider imports** in the observed source preamble. Because the current law requires the gate before secret lookup, provider import, network, Aider, or fallback dispatch, a later runtime check would not repair this ordering invariant.

Status: `NEGATIVE_RESULT / P0 AUTHORITY-BOUNDARY ORDERING GAP`.

## Finding B — Bugfix role has the same pre-gate import problem plus an unbounded provider wait loop

Path:

`research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_bugfix_v1.py`

The module startup path:

1. inserts `~/last-resort` into `sys.path`;
2. imports `llm as pool_llm`;
3. imports `requests`;
4. configures explicit tiers `nvidia -> groq -> mistral`;
5. `_call_one_tier()` performs direct `requests.post(...)` using keys returned by `pool_llm._tiers()`;
6. `wait_for_any_tier_available()` loops indefinitely with exponential backoff until a provider succeeds.

Under current HARD_OFF, “retry forever” is not a resilience feature: the correct behavior is deterministic fail-closed **before entering provider machinery at all**.

Status: `NEGATIVE_RESULT / P0 AUTHORITY-BOUNDARY ORDERING GAP`.

## Why local unit tests cannot close this

A test can prove package sequencing, backoff logic, SQLite state transitions, or helper orchestration while monkeypatching/mocking network paths. None of that proves:

```text
canonical authority resolved
  -> provider gate evaluated
  -> HARD_OFF => zero provider imports requiring credentials
  -> zero secret lookups
  -> zero network calls
  -> zero Aider/fallback dispatch
```

Therefore the existing reported green orchestration tests remain component/source evidence only.

## Existing gate source is not enough by itself

Relevant current gate-family sources include:

- `tools/claycode_autonomous_provider_gate.py`
- `tools/freepool_fallback_provider_gate_v1.py`

Their existence does not prove the Frankenstein callers route through them before the forbidden boundary. Current supervisor state explicitly preserves this distinction.

## Required future acceptance shape

A future source repair should be accepted only if all of the following are true at exact source identity:

1. canonical authority is resolved without provider imports, secret lookup, or provider network I/O;
2. a single deterministic decision returns `DENY` under current HARD_OFF;
3. provider-specific modules are imported lazily **only after ALLOW**;
4. secret/key discovery occurs only after ALLOW;
5. Aider/fallback dispatch occurs only after ALLOW;
6. a repository-bound test proves under HARD_OFF:
   - `provider_calls == 0`
   - `secret_lookups == 0`
   - `aider_dispatches == 0`
   - `network_calls == 0`
7. test receipt binds HEAD, tree, `dirty=false`, source hashes, stdout and stderr;
8. provider-authored post-HARD_OFF core changes receive independent clean non-provider review/reexecution before runtime credit.

## Non-goals

This Triggerword-3 audit does **not** modify Frank's Harness, enable providers, consume credentials, run a provider preflight, or claim that a source patch would by itself restore runtime credit.

## Result

```text
FRANKENSTEIN_PROVIDER_BOUNDARY_STATIC_AUDIT/v1
source_scope: exact canonical main 854f6bc87780f4a5242489a6c807d186b16a8c3d
orchestrator: FAIL_CLOSED_ORDERING_GAP
bugfix: FAIL_CLOSED_ORDERING_GAP
provider_execution_performed: false
secret_lookup_performed: false
runtime_credit_promoted: false
next_gate: canonical authority gate must precede provider import/secret/network/Aider boundary
```
