<!-- RAE_META
{"packet_id":"KMP-U2-RECOVERY-SELECTION","title":"Canonical replay and selection integrity are separate correctness obligations","domains":["unifieddb","claygraph","frank","gwt"],"epistemic_class":"RUNTIME_MECHANISM_TEST_PLUS_EXTERNAL_CONVERGENCE","status_hint":"OPEN","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json","research_entity/trigger_runs/unifieddb/unifieddb-20260808T2212p0700-chatgpt-secondary-r3/EVIDENCE_LEDGER.md"],"verification_required":true}
RAE_META -->

## Result
In 1,200 E2B recovery trials, unsynchronized two-store commits ended torn in 533 cases. A canonical commit plus durable outbox had 554 intentionally pending derived updates before replay and 0 mismatches after replay; a one-engine transaction also had 0 mismatches. The outbox path cost more in the in-memory write benchmark (18.199 us p50 versus 6.866 us for the monolith).

Separately, a 700-case PPR-like selector test kept fact records authentic while changing graph structure: naive selection changed in 516 cases; trusted-structure reselection recovered the constructed baseline in 700/700. This converges with Fei et al. 2026 Selection Integrity, but is not an independent reproduction of their full systems.

## Implication
Replay integrity and selection integrity are both required. A view can be perfectly replayable yet select the wrong authentic facts, and a safe selector can still operate on stale/unreplayable derived state.
