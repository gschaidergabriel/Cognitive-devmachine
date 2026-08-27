# Frankenstein 72h orchestration — authority quarantine (9.13)

**Classification:** CURRENT_SOURCE / NEGATIVE_RESULT / SOURCE_READY_FIX / RUNTIME_UNVERIFIED  
**Observed canonical base before this Trigger-3 delta:** `854f6bc87780f4a5242489a6c807d186b16a8c3d`  
**Current authority source:** `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`  
**Current steering delta:** `research_entity/claycode/autonomous/SUPERVISOR_STEERING_9_13O_DELTA_2026-08-27T2341P0700_GPT56SOL.json`

## Why the 72h scripts are quarantined

The newly added `frankenstein_orchestrator_v1.py` and `frankenstein_bugfix_v1.py` are useful implementation donors, but their provider-capable paths are not currently executable authority.

At the observed base they import `~/last-resort/llm.py` and `requests` directly. The Bauleiter can also invoke `~/.claude/star/harness_aider.py fallback-start`. Under supervisor 9.13 the provider state is HARD_OFF: all provider routes are false, Together is forbidden, paid fallback is forbidden, and provider execution must remain quiescent.

Therefore:

- **do not invoke either original script directly** while HARD_OFF remains current;
- the stale Together allowance in `BUILD_ORCHESTRATION_PLAN_20260827.json` is historical/non-authoritative plan text and grants zero current execution credit;
- the direct Nemotron/Groq/Mistral fallback design is non-operative under current authority;
- do not modify Frank's own Harness to solve this boundary;
- preserve the original files as evidence/donor history rather than rewriting their provenance away.

## New canonical launch surface proposed by this Trigger-3 delta

Use:

```bash
python research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_authority_launcher_v1.py bauleiter -- --once
```

or:

```bash
python research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_authority_launcher_v1.py bugfix -- --max-iterations 1
```

The launcher is standard-library-only on its pre-admission path. It executes `tools/freepool_fallback_provider_gate_v1.py` first and fails closed on any denial, stale/malformed result, missing gate, timeout, or ambiguity. A blocked receipt declares:

- `provider_calls = 0`
- `secret_lookups = 0`
- `target_imports = 0`
- `target_processes_started = 0`

Only an explicit current gate result with exit `0` and `admitted=true` is allowed to reach a target process.

## Evidence scope

This document and the launcher/tests are **source-level repair**, not a runtime promotion. No external provider call is needed or permitted to validate the blocked path. Until exact-current repository-bound execution of the launcher tests is observed and recorded, claim only:

`SOURCE_READY_HARD_OFF_BOUNDARY_REPAIR`

Do **not** claim:

- provider runtime PASS;
- 72h orchestration runtime PASS;
- BASE/EntityOS/HCU promotion;
- training credit;
- canonical semantics promotion.

## Falsifier / acceptance gate

The repair fails if, under the current 9.13 HARD_OFF inbox, a repository-bound test can demonstrate any of the following before the launcher returns blocked:

1. provider-capable target module imported;
2. secret lookup attempted;
3. provider/network request attempted;
4. Aider/fallback process started;
5. target process started;
6. malformed/unknown authority treated as admitted.

The minimum positive acceptance witness is the opposite: exact-current test execution returns exit `77` with the zero-boundary receipt and no target/provider side effects.

## Relationship to the broader Frankenstein curation pass

This quarantine is intentionally visible in the research story. It is a first-class negative result: an otherwise working orchestration implementation can still be non-operative because its execution boundary does not match current authority. The engineering lesson is architectural, not cosmetic: **capability must be admitted before the caller reaches secrets, imports, network, or effects.**
