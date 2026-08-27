# UnifiedDB / Database Pulse — V3/V4 Swarm Delta

Date: 2026-08-10 +07:00  
Origin: chatgpt-secondary / OpenAI / GPT-5.6 Sol  
Status: TESTING / NO_CANONICAL_PROMOTION

This delta updates the immediately preceding adaptive-preprocessor/maintenance fusion after
new concurrent-worker results arrived on `main`.

## New strongest Pulse candidate direction

The prior `PulseActiveFieldV2` repair remains useful evidence because it proved the original
V1 pre-limit/lexicographic truncation defect was real. It is no longer the simplest surviving
candidate.

`DatabasePulseRuntimeV3` now preserves the owner-fixed Database Pulse scheduler, provenance,
re-entry, replay, model-quarantine and no-effect-authority contract while removing the second
`pulse_active_field` candidate table. Candidate ordering is computed over authoritative
StateLedger rows before LIMIT and may be accelerated by a rebuildable SQLite partial/expression
rank index. Creating/verifying the physical index must not mutate semantic ledger roots.

Its adversarial tests explicitly cover:

- late-sorted highly salient `memory:zzzz-critical` survives the candidate budget;
- `query_truncated` remains truthful;
- UNKNOWN and CONFLICT counts remain visible without promoting them to KNOWN focus;
- no model/tool/effect calls in zero-model mode;
- optional model output is stored as UNKNOWN hypothesis only;
- physical index creation leaves semantic epoch/state/trace roots unchanged;
- scheduler pause/resume survives process reopen;
- stale basis fails before selection;
- truthful re-entry differs causally from NO_REENTRY lesion;
- same pulse id remains idempotent.

This is a material architecture simplification: the repaired semantics can potentially live on
the authoritative state table plus a disposable physical index instead of a second candidate
projection table.

## V4 makes the physical index adaptive

`PULSE_ADAPTIVE_AUTHORITATIVE_RANK_PATH_V4` separates semantic correctness from physical
acceleration. The deterministic score expression and pre-LIMIT ranking semantics stay the
same whether the index exists or not.

The physical mode is selected using U16 compile economics plus conservative Pulse lifetime
history:

- sparse history -> `ONLINE_NO_COMPILE`;
- short expected lifetime -> `ONLINE_NO_COMPILE`;
- churn shock -> recent-floor estimate can cancel compile;
- long stable horizon with positive guarded amortization -> `COMPILED_INDEX`;
- index build failure -> `ONLINE_COMPILE_FAILED_FALLBACK`;
- truthful re-entry must be semantically identical online vs compiled.

Therefore Pulse itself is moving toward an adaptive preprocessor whose semantic path is always
correct and whose physical accelerators are optional measured implementations.

## Relationship to SPM-S1

SPM-S1 remains orthogonal and candidate-only. V4 decides whether the authoritative candidate
rank path merits a physical rank index. U16 and Maintenance Economics S1 decide whether deeper
compiled semantic fields merit materialization and, if so, whether full-generation or
segmented copy-on-write maintenance is cheaper under measured locality.

Do not merge these decisions:

1. candidate ranking correctness;
2. candidate rank physical acceleration;
3. semantic possibility compilation;
4. compiled-field maintenance strategy;
5. evidence-gap deepening;
6. truth/effect authority.

They must remain separately measurable and lesionable.

## Strongest current architecture shorthand

```text
StateLedger / UnifiedDB truth
  -> Database Pulse Runtime V3 semantics
     -> V4 ONLINE or optional physical rank index by horizon economics
  -> coherent/cycle-pinned semantic access
  -> U14 cheapest-safe read primitive
  -> U15 typed sufficiency-gap deepening
  -> U16 ONLINE vs COMPILE
     -> if compiled: FULL generation or SPM-S1 by maintenance economics/locality
  -> provenance-bearing bounded ActiveAssembly
  -> GWT/model
  -> verified outcome / causal re-entry
  -> telemetry updates future horizon/locality decisions
```

## Fair superiority test is now explicit

The new `UNIFIEDDB_CLAYGRAPH_CROSS_ENGINE_BENCHMARK_CONTRACT.md` prevents a false victory over
naive conventional stores. SQLite, PostgreSQL and graph-native lanes (when reproducibly
available) must receive normal indexes, transactions, views/materialization/triggers and
application receipt logic needed to implement equivalent semantics. Clay can claim a workload-
specific or architecture-level advantage only if matched semantics survive correctness,
fault/recovery, replay, concurrency and resource comparisons. Universal database superiority
remains unsupported absent broad independent evidence.

## Evidence status

Repository implementation/tests/workflows exist for V3/V4 and SPM/maintenance controllers.
At this delta's write time, dedicated SPM-S1 / Maintenance-Economics-S1 /
Maintenance-Horizon-S1 Hostinger receipt files were still absent, so they remain TESTING rather
than remote PASS.

The correct next promotion order is:

1. exact-commit Ubuntu execution receipts;
2. rank-index V3/V4 vs ActiveFieldV2 and online path matched measurements;
3. real Pulse lifetime/locality traces;
4. policy regret against simple fixed policies;
5. cross-engine matched-semantics benchmark;
6. downstream cognition/task/token/context effects;
7. final Andreas Ubuntu acceptance.

No canonical promotion or effect-authority change is authorized by this delta.
