# Frankenstein provider authority boundary

> `CURRENT_SOURCE + NEGATIVE_RESULT + PREPARED_REPAIR`. This document is a curation/engineering map, not execution authority.

## Current fact pattern

At the Triggerword 3 curation snapshot, current supervisor authority is provider epoch **9.13 HARD_OFF**:

```text
provider routes = false
Together = forbidden
paid fallback = forbidden
```

The current Frankenstein topic packet also contains provider-capable scripts:

```text
frankenstein_orchestrator_v1.py
frankenstein_bugfix_v1.py
```

Those scripts were created with useful package/continuity/rollback logic, and their creating commit reports 29 local tests green. Their existing test suites explicitly monkeypatch network/provider calls. Therefore those tests establish bounded non-network component behavior; they do not establish the provider authority boundary.

Current 9.13O steering consequently classifies the 72-hour provider-calling orchestration as quarantined/non-operative.

## What this Triggerword 3 branch adds

A new source-ready entry candidate:

```text
research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_authority_launcher_v1.py
```

It calls the already-existing canonical standard-library gate:

```text
tools/freepool_fallback_provider_gate_v1.py
  -> tools/claycode_autonomous_provider_gate.py
  -> research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
```

before importing or executing either provider-capable Frankenstein target.

On any blocked, malformed, missing, ambiguous or timed-out gate result the launcher returns exit `77` and emits a receipt declaring:

```text
provider_calls = 0
secret_lookups = 0
target_imports = 0
target_processes_started = 0
```

The corresponding source test is:

```text
tests/test_frankenstein_authority_launcher_v1.py
```

It is designed to assert the current HARD_OFF path blocks before the target/provider boundary and that a synthetic admitted gate reaches the target only after the gate.

## Evidence boundary

The launcher and its tests are **source-ready on this branch**. They do not receive runtime PASS merely because the source looks correct.

Promotion requires an observed clean non-provider test run at exact branch/commit identity with stdout/stderr/exit-code binding. No provider call is required or permitted to test the HARD_OFF path.

## Residual bypass: why this is not yet full closure

The historical provider-capable target files still exist. A caller that explicitly invokes them directly can bypass the new launcher unless every operational entrypoint is migrated or the target modules themselves are refactored so provider-capable imports/calls cannot occur before canonical authority admission.

Therefore the current state is:

```text
safe fail-closed launcher candidate: SOURCE_READY
full Frankenstein caller-boundary closure: NOT YET PROVEN
72h provider orchestration execution authority: FALSE
provider-path runtime credit: 0
```

Do not hide this residual path by claiming the launcher alone makes direct invocation impossible.

## Next exact discriminator

On a clean current non-provider checkout:

1. resolve exact current `main` and current `SUPERVISOR_INBOX.json`;
2. run only `tests/test_frankenstein_authority_launcher_v1.py` first;
3. verify the real HARD_OFF case returns `77` with all four zero-boundary counters;
4. statically enumerate every repository path that invokes either Frankenstein target, `harness_aider.py fallback-start`, or `~/last-resort/llm.py`;
5. prove each operational Frankenstein entrypoint routes through the canonical gate before secret lookup/provider import/network/Aider/fallback;
6. if direct target imports are still operational, refactor provider imports/calls behind a pre-import/pre-network gate while preserving non-network unit-testability;
7. rerun the original 29 non-network tests plus the new authority tests;
8. persist an exact-source receipt and keep provider runtime credit at zero unless a future authority explicitly re-admits provider execution.

## Do not solve the wrong problem

Current steering says not to modify Frank's own Harness merely to make this finding disappear. The defect is the external caller/orchestration authority boundary. Preserve the Harness as evidence/donor source unless newer explicit authority changes that instruction.
