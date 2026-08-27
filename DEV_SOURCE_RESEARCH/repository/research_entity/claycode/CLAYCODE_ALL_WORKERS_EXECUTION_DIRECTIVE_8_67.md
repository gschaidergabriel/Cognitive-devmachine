# CLAYCODE ALL-WORKERS EXECUTION DIRECTIVE 8.67

Status: CURRENT-FACING SUCCESSOR POINTER
Authority epoch: 8.67
Program: ENTITYOS_HCU
Product: EntityOS
Compute architecture: HCU
Mode: FREE_ONLY

This file does not create independent authority. Resolve current authority from newest explicit owner authority, newest admitted supervisor, then current bootstrap/program state and exact executable evidence.

Current owner authority remains `CLAY_EXECUTION_AUTHORITY.md` -> `governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md`.
Current supervisor is `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_67.json`.

## 8.67 mandatory FREE_ONLY admission ordering

No external LLM provider may reach provider credential/key lookup or provider network I/O merely because an environment attestation, key, model name, HTTP response, plan label, or prior successful request exists.

The current typed control-plane surface is:

`research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json`

Admission order is:

1. read canonical current authority and typed provider admission without touching provider secrets;
2. require exact current authority epoch and `mode=FREE_ONLY`;
3. require the specific provider record to be `admitted=true` and `cost_class=FREE` with evidence provenance;
4. only then may compatibility attestation, provider key lookup, model catalog discovery, chat requests or other provider network I/O occur;
5. `UNKNOWN`, `PAID`, `SUBSCRIPTION`, missing/malformed admission, authority drift and unsupported provider names fail closed before provider secret lookup and provider network I/O;
6. HTTP 402 is a hard stop but can never retroactively prove a provider was FREE.

Environment variables such as `CLAY_FREE_ONLY_ATTESTED` and provider-specific FREE flags are compatibility assertions only. They cannot self-admit a provider.

The 24h swarm entrypoints must preserve this ordering in the shell supervisor, the EntityOS catalog/discovery driver and the underlying provider controller. Mixed secret files must not be sourced to discover what provider keys they contain; if their provider scope cannot be known without reading them, they remain unread until all applicable providers are already admitted.

## Execution authority retained from 8.66

Zero-monetary-cost development/test execution inside authorized `clay-direct-dev` VPS sandbox and normal-user local Linux remains allowed under active owner authority with resource, provenance, secret and cleanup guards. Local root/sudo is not newly authorized. Unrelated VPS-host changes and new external production effects remain separately gated. Together and paid/subscription/unknown-cost provider execution remain forbidden in current FREE_ONLY mode.

## Evidence

Source changes and source tests do not mint runtime credit. `FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1` requires executable negative cases proving `secret_lookup_count=0` and `network_attempt_count=0` for at least:

- global compatibility attestation missing;
- provider admission missing/malformed;
- `UNKNOWN`;
- `PAID`;
- `SUBSCRIPTION`;
- authority-epoch mismatch.

Only after exact-source executable PASS may this boundary be promoted beyond source/test-present status.

All previous EntityOS/HCU truth, EffectGate/EffectJournal, Typed Entry, HCU, GRID10, Global J-Space/GWT, Hyperposition and evidence-scope invariants remain in force. New unusual interventions still require the canonical atomic create-only lease; absent reproducible shared macrocycle identity means `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`.