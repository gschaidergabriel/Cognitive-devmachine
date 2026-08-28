# GO 2026-08-25 — self-hosted queue evidence boundary v2

## Authority and scope

- Persistent entity: Clay; current worker is an organ.
- Product: EntityOS; integrated cognition/compute architecture: HCU.
- Supervisor observed immediately before this write: 8.78 / FREE_ONLY.
- Canonical `main` observed immediately before this write: `bfdbc20b7134b8f73f0e8897dc29e16b8cc6ffc6`.
- Scope: execution-transport diagnosis and three-track GO gating only. No EntityOS/HCU/J-Space/model/training runtime credit is added.

## New discriminator beyond v1

The previous queue-boundary receipt could not distinguish a Clay-repository routing mismatch from unavailability of the retained self-hosted runner itself. This cycle exercised the already-documented controller repository path instead of creating a new executor.

The retained controller workflow `gschaidergabriel/Dr.-Unterweger/.github/workflows/frank-self-hosted-probe.yml` was retriggered by the bounded source-neutral comment change commit `6ad6af25038f8b7be07e660b2c47ea14a9de7c5f`. The resulting `Clay Self-Hosted VPS/Sandbox Probe` run is `32803694800` and was observed `queued` with no conclusion. That workflow uses plain `runs-on: self-hosted`, so the simultaneous queueing is evidence against the narrow hypothesis that only the Clay repository's label set is preventing assignment.

Existing Clay-repository runtime gates were also observed nonterminal:

- clay-direct-dev roundtrip run `32802727269`: `queued`;
- collective-metrics freshness run `32803251965`: `queued`;
- GO878 historical Free-Swarm backfill run `32803325959`: `queued`.

This is still infrastructure/scheduling evidence, not product failure. The strongest bounded classification is:

`REGISTERED_SELFHOSTED_EXECUTION_SURFACE_NONTERMINAL_ACROSS_CONTROLLER_AND_CLAY_REPOSITORIES`

A runner-offline/unavailable explanation is now more plausible than a Clay-repository-only label mismatch, but runner status was not directly observable from the connected GitHub surface, so it is not promoted to fact.

## Direct bridge availability on this organ's tool surface

The current ChatGPT container has an `ssh` executable but no `$HOME/.ssh` directory/config. Therefore this organ cannot use the owner's preconfigured local SSH jump identity from this container without importing secrets, which is forbidden. This does **not** mean the documented owner bridge is absent from the owner's machine/VPS environment.

## Live conversion state re-observed

At the exact inspected main state, live Free-Swarm metrics report `39,781,535` cumulative tokens; Forge reports `1` accepted delta; Distillery remains at `0` accepted packets and `0` accepted dataset tokens. `GO_COLLECTIVE_METRICS.json` is still the old 8.71 / 7,302,860-token snapshot. Therefore raw-token scale remains backpressured and the freshness/backfill/Distillery conversion gates remain the correct priority.

## GO tracks

### Track A — ENTITYOS_EXECUTABLE_CONVERGENCE

Advanced the execution diagnosis from repository-local queue ambiguity to cross-repository self-hosted nonterminal evidence. Existing replay-v2, freshness and historical-backfill source lanes remain the singleton implementation paths; no duplicate lane was created.

### Track B — HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT

`HCU_NO_CHANGE_WITH_REASON`: current highest-information blocker is admitted executable evidence transport, while replay-stable causal identity/backfill identity work is already moving on main. Adding another HCU/Typed-Entry source primitive before those runtime gates execute would not resolve the measured bottleneck.

### Track C — GLOBAL_JSPACE_GWT_PROTOTYPE_AND_TRAINING_READINESS_FREE_ONLY

Advanced readiness indirectly by preserving conversion backpressure: no new raw scale, provider run, model intervention or unusual experiment was launched. Training/J-Space promotion stays blocked until replay-v2 + historical Forge→Distillery closure produce executable causal evidence.

## Credits

- whole EntityOS/HCU runtime credit: 0
- full HCU runtime credit: 0
- J-Space model runtime credit: 0
- training credit: 0
- provider runtime credit added by this cycle: 0
- whole-product PASS: false

## Next exact gate

Restore or expose one already-authorized transport that can actually enter `clay-direct-dev` (retained controller self-hosted runner or owner's installed SSH bridge), then run the existing gates in order without source fanout:

1. terminal clay-direct-dev roundtrip;
2. terminal exact-source collective-metrics freshness and replay-v2 migration regressions;
3. historical workers.jsonl backfill to bounded saturation;
4. one evidence-qualified Forge ACCEPT -> exactly one Distillery packet -> `accepted_dataset_tokens > 0` -> semantic replay `+0`.

Until step 1 is terminal, queued jobs remain non-evidence and additional raw Free-Swarm token scaling should stay paused.