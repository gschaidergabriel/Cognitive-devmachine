# Frankenstein master cognition — current authority status

**Trigger-3 baseline:** `main@854f6bc87780f4a5242489a6c807d186b16a8c3d`  
**Current supervisor selector observed:** `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` schema `9.13`, delta `9.13O_NON_AUTHORITY`  
**Selected provider state:** `FREE_ONLY_HARD_OFF_ALL_PROVIDER_ROUTES_FALSE_TOGETHER_FORBIDDEN_NO_PAID_FALLBACK`

This file does not replace owner/supervisor authority. It exists so a reader entering this topic packet cannot mistake source presence for current execution permission.

## Current disposition

| Artifact | Source status | Runtime/execution status under current baseline | Credit |
|---|---|---|---|
| `CONCEPT.md` | research concept/source | non-authoritative design input | 0 whole-product credit |
| `frankenstein_packages_v1.py` | source present; package/dispenser logic tested in latest commit | non-provider logic is a donor/component; not whole orchestration acceptance | 0 whole-product credit |
| `frankenstein_orchestrator_v1.py` | source present; non-network orchestration tests reported green | **QUARANTINED / NON-OPERATIVE** while direct provider/fallback paths remain | 0 provider/whole-product credit |
| `frankenstein_bugfix_v1.py` | source present; non-network logic tests reported green | **QUARANTINED / NON-OPERATIVE** while direct NVIDIA/Groq/Mistral paths remain | 0 provider/whole-product credit |
| `BUILD_ORCHESTRATION_PLAN_20260827.json` | historical/current source of the design sequence | provider and Together allowances are **STALE NON-AUTHORITY** under 9.13 | 0 execution/training credit |

## Why the latest 29-test result is not deployment acceptance

The latest commit reports 29 tests across package dispenser, Bauleiter and Bugfix logic. The added tests are described as non-networked orchestration/logic tests. That is useful component evidence.

It does **not** establish:

- current provider authorization;
- zero secret lookups under hard-off;
- zero provider/network calls under hard-off;
- clean non-provider review of provider-authored post-hard-off core changes;
- actual 72-hour process survival;
- whole EntityOS/HCU runtime acceptance;
- training permission or training success.

## Exact current conflict

The Bauleiter/Bugfix implementation uses the external free-pool/provider surface and direct provider-tier logic. Current 9.13 steering requires the external caller boundary to fail closed **before**:

```text
secret lookup
provider import / provider-side initialization
network
Aider
external fallback dispatch
```

Under hard-off, an executable acceptance receipt must demonstrate at minimum:

```text
provider_calls = 0
secret_lookups = 0
```

The current source does not receive that credit merely because its network calls are monkeypatched in unit tests.

## Together plan statement is retired as current authority

`BUILD_ORCHESTRATION_PLAN_20260827.json` states that exactly one Together training run is authorized. Current 9.13 authority says:

```text
Together: forbidden
remaining paid runs authorized: 0
paid fallback: forbidden
```

Therefore the plan's Together statement is preserved as historical provenance but is **contradicted/retired as current execution authority**. A marker file or confirmation mechanism inside that old plan cannot mint a new authorization.

## Required revival path

Do not delete the donor work. Repair the boundary.

1. Resolve the newest canonical provider authority before any external/provider boundary.
2. Fail closed before secret lookup, provider import/init, network, Aider or fallback dispatch.
3. Under current hard-off, prove `provider_calls=0` and `secret_lookups=0` in an exact-source executable receipt.
4. Remove/quarantine Together-run assumptions from the active orchestration path.
5. Do **not** modify Frank's own Harness to make this pass; gate the external orchestration/caller surface.
6. Independently review and re-execute post-hard-off provider-authored core changes on a clean non-provider checkout before assigning retained runtime credit.
7. Only a future explicit authority change may re-enable provider execution; the code must still re-resolve that authority at runtime rather than trusting this document.

## Evidence law

```text
SOURCE PRESENT != AUTHORIZED TO RUN
TEST PASS != HIGHER-SCOPE PASS
REQUEST != EFFECT
MODEL OUTPUT != WORLD FACT
HISTORICAL AUTHORITY != CURRENT AUTHORITY
PROVIDER-FREE LABEL != CURRENT ROUTE ADMISSION
```

The topic packet should remain useful as a donor/research packet while its provider-calling execution lane is hard-off.