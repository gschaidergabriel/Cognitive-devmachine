# Frankenstein v1 — current execution quarantine

Status: **QUARANTINED / NON-OPERATIVE UNDER CURRENT 9.13 HARD_OFF**

This file is a current-facing safety/evidence marker. It does not rewrite the historical source or its reported tests.

## Why

Current `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` selects 9.13O steering over provider-authority epoch 9.13. That steering records:

```text
FREE_ONLY
all provider routes false
Together forbidden
no paid fallback
```

It explicitly quarantines the provider-calling 72-hour Frankenstein Bauleiter/Bugfix orchestration.

The retained v1 scripts contain direct or indirect provider-entry behavior:

- `frankenstein_orchestrator_v1.py` imports the free-pool `llm` layer, imports `requests`, directly selects a provider tier, and can invoke `harness_aider.py fallback-start`;
- `frankenstein_bugfix_v1.py` imports the free-pool `llm` layer and `requests`, then walks NVIDIA -> Groq -> Mistral with persistent backoff.

Reported green source/component tests do not grant current execution authority.

## Current safe entry

Use only:

```text
frankenstein_launch_gate_v2.py
```

That launcher resolves the repository's existing:

```text
tools/freepool_fallback_provider_gate_v1.py
```

before importing/executing either retained v1 role. Under current HARD_OFF it must stop with exit 77.

## Important limitation

The v2 launcher is an authority-first **safe entry point**, not proof that every possible caller is closed.

Direct execution or import of the v1 scripts bypasses the v2 launcher and therefore remains quarantined.

The P0 caller-boundary blocker is not closed until every reachable provider path is either:

1. forced through a current canonical authority gate before secret lookup/provider import/network/Aider/fallback dispatch; or
2. made structurally unreachable under HARD_OFF;

and exact executable evidence proves:

```text
provider_calls = 0
secret_lookups = 0
```

under the current authority and exact source identity.

Do not modify Frank's own Harness to claim this closure. Gate the external orchestration/caller surface.

## Evidence credit

This quarantine marker and v2 launcher are source/control-plane deltas only until exact-source regressions execute.

They grant zero:

- provider runtime credit;
- EntityOS whole-runtime credit;
- HCU full-runtime credit;
- canonical-semantics credit;
- training credit.
