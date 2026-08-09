# 666 Level-0 Run Report — PF Watchdog / Boot-Stability Failure Lineage

## Scope
Bounded Project-Frankenstein historical lineage, selected after live center pulse and non-overlap checks. Source commits were not previously indexed in the RAE by exact hash at claim time.

## Historical causal chain
1. `e63ea0cfa2a6beea05ba03082ca12d1fae66774d`: a systemd-active llama-server could be HTTP-hung. The guard added `/health` probes, three-consecutive-failure gating and force restart. At frozen PF head the mechanism survives with a 90-second startup grace, while the file is marked deprecated in favor of Neural Immune supervision.
2. `2dc02b095f0f2fff13421217b303528e43c47a04`: Genesis could crash-loop because blocking sensor work starved the systemd watchdog. The repair moved to monotonic watchdog servicing before/after ticks and between sensors. Source-reported pre-fix rate (~18 crashes/hour) was not reproduced here.
3. `7bf44fb459bff12b70108ebffe04d61d7789ad84`: hardcoded non-installed services caused watchdog/immune restart cascades. The repair resolves installed services before constructing trackers/circuit breakers. This mechanism survives in frozen-head Neural Immune code.

## Current architecture consequence
Clay/Harness must distinguish five states: capability installed, process active, endpoint responsive, dependency ready, semantic ready. Optional absence is not failure. Long operations need explicit phase/deadline receipts rather than relying only on process heartbeat. Supervisor actions require causal provenance and anti-cascade budgets.

## Required regressions
- active process + hung endpoint
- cold-load startup grace
- absent optional vs absent required service
- long healthy operation vs genuinely stuck operation
- restart-log feedback/cascade isolation
- boot-order permutation convergence to the same ready-state hash

## One-module implication
A one-module binary does not eliminate boot order. It internalizes it. H3 therefore needs an explicit initialization DAG, deterministic phase receipts, rollback and last-known-good initialization state.

## Owner correction handled during run
The project owner stated that `all frank data 1.tar.xz` was deleted and must not be analyzed. Live Drive root verification confirmed 14 folders and zero files. A final owner-deletion receipt and post-deletion root epoch were committed; the historical tarball blocker task was marked superseded. The tarball is not a Level-0 blocker or obligation.

## Durable artifacts
- `research_entity/archive_assimilation/receipts/666_20260809T1237p0700_chatgpt_secondary_pf_watchdog_boot_stability_lineage.json`
- `research_entity/rooms/center_events/20260809T1237p0700_666_pf_watchdog_boot_stability_delta.json`
- `research_entity/archive_assimilation/receipts/666_20260809T1233p0700_owner_deleted_tarball_scope_final.json`
- `research_entity/archive_assimilation/manifests/DRIVE_CLAY_ROOT_EPOCH_20260809T1233p0700.json`

Global exact Level-0 credit added: `0%`. Full Project-Frankenstein history/tree and combined release denominator remain unfrozen.
