# Triggerword 3 addendum — authority-first Frankenstein entry

**Date:** 2026-08-27  
**Organ:** GPT-5.6 Sol / ChatGPT  
**Branch:** `trigger3/frankenstein-curation-20260827-gpt56sol`  
**Canonical main observed before delta:** `854f6bc87780f4a5242489a6c807d186b16a8c3d`

## Finding

The retained v1 Frankenstein roles remain directly provider-capable while current provider authority is 9.13 HARD_OFF.

Observed source boundary:

- `frankenstein_orchestrator_v1.py` imports `llm` and `requests`, performs direct named-tier HTTP requests and can shell to `harness_aider.py fallback-start`;
- `frankenstein_bugfix_v1.py` imports `llm` and `requests`, walks NVIDIA -> Groq -> Mistral and intentionally retries indefinitely across provider unavailability;
- neither retained v1 role invokes `tools/freepool_fallback_provider_gate_v1.py` before its provider-facing imports/path.

Current 9.13O steering requires the external caller surface to fail closed before secret lookup, provider import, network, Aider or fallback dispatch and requires zero provider calls / zero secret lookups under HARD_OFF.

## Bounded source delta

Added:

```text
research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_launch_gate_v2.py
tests/test_frankenstein_launch_gate_v2.py
research_entity/topic_packets/frankenstein-master-cognition-concept/QUARANTINE_CURRENT_9_13.md
```

### v2 launcher properties

- standard-library-only at module import time;
- loads the existing canonical `freepool_fallback_provider_gate_v1.decision_record()` before retained-role execution;
- only literal boolean `admitted is True` may continue;
- current/blocked path returns exit `77`;
- probe mode never executes a retained role;
- validates that the selected retained role resolves inside the expected topic directory;
- uses `os.execv` only after the authority decision passes;
- contains no import of `requests`, `llm`, provider SDKs, Aider or Harness;
- claims zero provider calls and zero launcher secret lookups before the retained path.

### regression definitions

The source test suite defines checks for:

1. only literal `True` admits;
2. unknown roles fail closed;
3. blocked decisions never call `execv`;
4. probe mode never calls `execv`, even for an admitted synthetic decision;
5. admitted synthetic decisions can reach only the exact retained target via the current Python executable;
6. launcher imports exclude provider/Aider modules;
7. source ordering keeps authority resolution before `os.execv`.

## Evidence boundary

`SOURCE_READY` only.

The regressions were written but **not executed by this ChatGPT organ**. No repository-bound runtime receipt is claimed.

The v2 launcher is not a complete closure of the P0 caller-boundary problem because direct invocation/import of either v1 role bypasses it. Those raw v1 entries remain quarantined.

A complete closure requires either structurally gating every reachable caller or making raw provider paths unreachable under HARD_OFF, followed by exact-current executable evidence proving:

```text
provider_calls = 0
secret_lookups = 0
```

No Frank Harness modification is required or authorized by this delta.

## Credit

```text
provider runtime credit = 0
whole EntityOS runtime credit = 0
full HCU runtime credit = 0
canonical semantics credit = 0
training credit = 0
```

## Next discriminator

On a clean, authority-allowed non-provider execution surface, run only the focused v2 regression suite first. If green, inspect every reachable direct entry into `frankenstein_orchestrator_v1.py`, `frankenstein_bugfix_v1.py`, `stern.py -> harness_aider.py`, and `~/last-resort/llm.py`; add one fail-closed gate at the earliest shared external caller boundary without modifying Frank Harness. Then execute a HARD_OFF receipt that instruments/blocks secret lookup and provider network and proves both counters remain zero.
