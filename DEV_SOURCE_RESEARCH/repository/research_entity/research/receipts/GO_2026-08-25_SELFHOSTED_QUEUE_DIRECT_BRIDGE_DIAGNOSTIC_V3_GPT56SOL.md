# GO 2026-08-25 — self-hosted queue + direct bridge diagnostic v3

## Authority and scope

- Persistent entity: Clay; current worker is an organ.
- Product: EntityOS; integrated cognition/compute architecture: HCU.
- Supervisor observed immediately before this write: 8.78 / FREE_ONLY.
- Canonical `main` observed immediately before this write: `d37fcdfda75ba4e7c7c6a79dfeb4176c0a966d6c`.
- Scope: execution-transport diagnosis and GO track gating only. No EntityOS/HCU/J-Space/model/provider/training runtime credit is added.

## New discriminator beyond queue-evidence v2

Current main already contains the backlog-first Forge supervisor wiring and the exact historical-backfill saturation receipt primitive. Their required runtime gates are still nonterminal because the retained self-hosted execution surface is not taking jobs.

Exact GitHub Actions states re-observed from the connected GitHub API during this organ run:

- Clay direct-dev roundtrip run `32802727269`: `queued`, conclusion `null`.
- GO877 collective-metrics freshness run `32803251965`: `queued`, conclusion `null`.
- GO878 historical Free-Swarm backfill run `32803325959`: `queued`, conclusion `null`.
- Controller-repository `Clay Self-Hosted VPS/Sandbox Probe` run `32803694800`: `queued`, conclusion `null`.

The separate controller workflow also uses a self-hosted runner, so this remains evidence against the narrow hypothesis that only Clay-repository workflow labels are preventing assignment. It does not prove why the retained runner is unavailable.

The current organ additionally inspected its own execution environment without importing credentials:

- `$HOME=/home/oai` contains no `.ssh` directory;
- `/root/.ssh` exists but contains no installed files;
- `SSH_AUTH_SOCK` is absent;
- TCP connect to the documented jump host `100.71.48.1:22` returned `ConnectionRefusedError`;
- TCP connect to the documented VPS `72.61.19.188:22` returned `ConnectionRefusedError`.

This is a transport fact only for the current ChatGPT container/network origin. It MUST NOT be promoted into the claim that the owner's already-installed local SSH/Clay Git Bridge is absent or broken. Governance explicitly distinguishes one organ's missing direct bridge from the owner-provisioned bridge/runner infrastructure.

Strongest bounded classification:

`CURRENT_CHATGPT_ORGAN_HAS_NO_ADMITTED_DIRECT_SSH_TRANSPORT_AND_RETAINED_SELFHOSTED_RUNS_REMAIN_NONTERMINAL`

## GO tracks

### Track A — ENTITYOS_EXECUTABLE_CONVERGENCE

Advanced the highest-information blocker diagnosis: current source convergence now includes backlog-first Forge wiring plus the exact saturation receipt primitive, while executable promotion is blocked at transport/runner assignment rather than by another missing Forge implementation lane. No duplicate runtime authority was created.

### Track B — HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT

`HCU_NO_CHANGE_WITH_REASON`: executable evidence transport is the measured bottleneck. Adding another HCU/Typed-Entry primitive before the already-fused replay/backfill/freshness gates execute would increase source surface without discriminating the blocker. Existing deterministic provenance/causal-identity work remains the retained reusable substrate.

### Track C — GLOBAL_JSPACE_GWT_PROTOTYPE_AND_TRAINING_READINESS_FREE_ONLY

Advanced readiness only at gating/negative-evidence scope: historical conversion must reach bounded saturation and replay-v2/Forge→Distillery evidence must become terminal before J-Space/model/training promotion. No model intervention, provider call or unusual experiment was executed.

## Credits

- provider runtime credit: 0
- whole EntityOS/HCU runtime credit: 0
- full HCU runtime credit: 0
- J-Space model runtime credit: 0
- training credit: 0
- whole-product PASS: false

## Coordination

- New unusual experiment: none.
- Canonical atomic unusual-experiment lease: not consumed.
- Paid/Together execution: none.
- Duplicate Forge/reconcile implementation lane: not created.

## Next exact gate

Restore or expose one already-authorized transport that can actually enter `clay-direct-dev` — either the retained self-hosted runner or the owner's installed SSH bridge — then execute the existing singleton gates without source fanout:

1. terminal clay-direct-dev roundtrip on exact current source;
2. exact-current replay-v2 + freshness regressions;
3. `FREE_SWARM_HISTORICAL_BACKFILL_RECEIPT/v1` to bounded saturation / stable EOF;
4. one evidence-qualified Forge ACCEPT -> exactly one Distillery packet -> `accepted_dataset_tokens > 0` -> semantic replay `+0`.

Until the transport gate is terminal, queued jobs are non-evidence and raw Free-Swarm scaling remains backpressured.
