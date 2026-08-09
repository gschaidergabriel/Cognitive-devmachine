# ClayCode Research Run — 20260809T1505p0700

## Identity and parent

- trigger: `claycode`
- actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- canonical parent: revision 2
- canonical state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- current ClayCode input: `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`
- promotion decision: **NO BASE OR CURRENT-STACK PROMOTION**

## Research question

Can current G9 V3 safely express and lower dynamically changing FRANK/UnifiedDB/ClayGraph state without allowing schema drift, stale graph topology, or unadmitted materializations to masquerade as CURRENT state?

The run focused on four discriminating questions derived from current FRANK, Harness, ClayGraph and UnifiedDB evidence rather than adding broad syntax:

1. named-field versus positional SQL lowering under schema evolution;
2. PATCH versus COMPLETE_SNAPSHOT graph projection semantics and explicit retraction closure;
3. typed source/materialization admission identity before CURRENT publication;
4. whether dynamic work/capability requirements justify new grammar primitives at all.

## Mesh grounding / Fusion 1

All nine current scientific branches were included through the run interconnect manifest. Deep inputs included the live FRANK deep-bugsearch delta, H1 reference-Harness contract, ClayGraph V2 schema, UnifiedDB V9 dynamic work fabric, GWT/Hyperposition emergence readout contracts and current G9 V3.

Current G9 V3 already has generic positive/negative `Delta`, source/graph epochs, capability-bearing effects and explicit truth/authority boundaries. The live FRANK audit nevertheless exposed a narrower missing contract: a producer can publish a later graph projection without proving that omitted prior-current relations were either intentionally retained (PATCH) or explicitly retracted (complete snapshot). The same audit also found materialization/source-admission and SQL-binding defects.

`FRANK_ARCHITECTURE.claycode.json` was searched but not found. Per protocol, the run used current executable/runtime evidence and current FRANK contracts rather than inventing the artifact.

## Hypotheses and counterhypotheses

### H_CC_NAMED_20260809 — OPEN_REFINED
Named-field lowering plus schema preflight reduces silent schema-drift corruption at evolving UnifiedDB boundaries versus positional tuple lowering.

Counterhypothesis: positional lowering is equally safe when an exact schema contract is frozen and verified before execution.

### H_CC_RETRACT_20260809 — OPEN_REFINED
A producer declaring `COMPLETE_SNAPSHOT` semantics must close the projection under retraction: prior-current members absent from the new complete output become explicit negative/retraction deltas before the new graph epoch can become CURRENT.

Counterhypothesis: the existing invalidation queue/projector can already guarantee equivalent stale-edge removal without a distinct projection-completeness contract in ClayCode IR.

### H_CC_ADMISSION_20260809 — OPEN_REFINED
Derived CURRENT publication should bind to an admitted source/materialization identity (source revision/tree, schema/materializer identity and receipt) rather than relying only on graph/source epochs.

Counterhypothesis: an external boot admission gate plus existing provenance is sufficient and ClayCode-level identity would duplicate responsibility.

### H_CC_SYNTAX_BLOAT_20260809 — OPEN_UNRESOLVED
Dedicated work/capability grammar might improve reliability, but no current evidence shows that it beats generic typed records/interfaces plus UnifiedDB V9 semantics.

## External triangulation

- Official SQLite INSERT semantics establish the key distinction behind the mutation test: omitting a column list binds values by table column position and requires table-wide arity, while an explicit column list binds values to named columns and allows omitted fields to receive defaults/NULL where legal.
- Differential Dataflow provides established prior art for treating changing collections as incremental differences rather than assuming a new output can be handled as additive state only. This supports the general delta/retraction design direction but does not by itself prove ClayGraph semantics.
- SLSA provenance independently supports the general requirement that produced artifacts be traceable to source/build lineage. It is used only as triangulation for admission/materialization identity, not as proof of the FRANK-specific field layout.

## Executable experiments

### Local sandbox — SQLite 3.46.1

A minimal G9 record parser extracted:

`WorkSpec { work_id:Text; spec_rev:Int; title:Text; }`

It produced two lowerings:

- named: `INSERT INTO work_spec (work_id, spec_rev, title) VALUES (?, ?, ?)`
- positional: `INSERT INTO work_spec VALUES (?, ?, ?)`

Observed mutation matrix:

- baseline: both correct;
- add defaulted fourth column: named succeeds and default populates; positional fails arity check;
- reorder target columns: named remains semantically correct; positional executes but silently yields wrong logical values;
- add required no-default column: named execution also fails, while a schema-preflight pass identifies the missing required field before execution.

Projection experiment:

- epoch 1 CURRENT = `{A-B, A-C}`
- epoch 2 declared complete output = `{A-B}`
- additive projection leaves stale `A-C`;
- retraction-closed projection emits `A-C` as retracted and leaves no stale relation.

Local result SHA-256: `2479b33cf0206fa708534ab63dc834bb7c7c2256a84b76eae164342bf301d7d8`.

### E2B isolated replication — SQLite 3.40.1

The same semantic test was executed through the repository's verified E2B bridge. Exit code was `0`; all discriminating outcomes reproduced, including silent positional misbinding after column reorder and stale `A-C` under naive additive projection.

Result: `research_entity/runtime/tool_results/claycode-20260809t1505-e2b-named-retraction.json`.

This gives two execution surfaces and two SQLite versions for the same failure classes. It still does **not** establish target-machine FRANK behavior.

## Fusion 2 / research delta

A run-local candidate was created at `CLAYCODE_DELTA_CANDIDATE.clay` with three refinements:

1. `ProjectionMode = PATCH | COMPLETE_SNAPSHOT` plus a `ProjectionCommitReceipt`. Only complete snapshots imply `previous_current_domain - new_output -> retracted`; PATCH omission is explicitly non-deleting.
2. `AdmissionIdentity` as a typed interface candidate binding CURRENT publication to admitted source/materialization lineage. Exact fields remain OPEN pending H1 target-machine tests.
3. `SchemaBinding` compiler policy: typed record-to-schema lowering uses named columns and performs pre-execution compatibility checks for unknown source fields and missing required target fields.

No new `work` or capability-resolution keyword was selected. That restraint is itself a negative result: current V9 storage/runtime semantics and generic G9 record/rule machinery may already be enough.

## Goodman anti-echo result

- `H_CC_NAMED_20260809`: **REFINED** — independently reproduced; default policy candidate, not universal ABI rule.
- `H_CC_RETRACT_20260809`: **REFINED** — stale-edge counterexample reproduced; completeness contract is narrower than unconditional deletion semantics.
- `H_CC_ADMISSION_20260809`: **REFINED** — general lineage requirement triangulated independently; exact ClayCode placement/fields still require H1 evidence.
- `H_CC_SYNTAX_BLOAT_20260809`: **UNRESOLVED** — no grammar growth without a benchmark.

Full review: `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

## Tooling negative result and repair

The current `research_interconnect_preflight.py` defines ClayCode priority as:

`frank -> clay -> harness -> claygraph -> unifieddb -> ...`

while `goodman_filter_check.py` required a hardcoded prefix omitting `harness`. This made the validator inconsistent with the current generator/protocol. The checker was repaired to include Harness in the required prefix; commit: `77cbe4ddfc924174930f7732833bf356f8500a2b`.

This is Research Entity tooling maintenance only. It is not FRANK self-Harness modification and contributes `TOOLING_GAIN`, not evidence for a scientific mechanism.

## Cross-branch feedback

- **FRANK:** admission/materialization identity and graph retraction remain release-integrity blockers; proposal/effect authority remains separate.
- **Clay:** coherent semantic epoch publication should require retraction-closed complete projections before exposure as CURRENT.
- **Harness:** add stale-edge, schema-reorder/default/required-field and source-admission differential fixtures to H1/H2.
- **ClayGraph:** projection receipts need explicit PATCH vs COMPLETE_SNAPSHOT semantics or an equivalent proven contract.
- **UnifiedDB:** named-field lowering + schema preflight is the current safer compiler-policy candidate at evolving typed-record boundaries.
- **GWT:** stale activation from a prior graph epoch must not become current workspace evidence.
- **Hyperposition:** preserve superseded/historical alternatives without leaving them active-current.
- **Emergenz:** causal topology tests must pin source, graph and admission identities so stale topology cannot contaminate lesion/rescue results.
- **ClayCode:** keep the candidate run-local until target-machine/H1-H2 differential evidence closes the remaining falsifiers.

## Generation result

Material gain classes achieved:

- `LANGUAGE_GAIN`: explicit projection-completeness/admission/schema-binding candidate semantics;
- `TOOLING_GAIN`: Goodman validator drift found and repaired;
- `RISK_COVERAGE_GAIN`: silent positional schema corruption and stale graph relation failure classes covered by executable tests;
- `NEGATIVE_RESULT`: no evidence for new dynamic-work/capability grammar keywords.

Executable evidence exists on local and isolated E2B surfaces, satisfying the run's executable-research requirement. This is a valid research delta, not a BASE language release.

## Unresolved / next falsifiers

1. Execute the exact FRANK target-machine T3 stale-edge/source-admission matrix.
2. Add H1/H2 differential fixtures for schema mutation and complete projection semantics.
3. Measure named-field/schema-preflight compile/runtime cost against verified frozen positional ABI lowering.
4. Test crash/replay/concurrent publication so a failed partial projection cannot publish mixed CURRENT epochs.
5. Determine whether AdmissionIdentity belongs in core IR, compiler signatures or a runtime boundary contract; avoid duplicate authority layers.
6. Benchmark dedicated work/capability syntax before any grammar expansion.

## Promotion decision

**NO CURRENT-STACK OR BASE PROMOTION.**

G9 V3 remains the current research candidate. This run adds open/refined hypotheses, executable receipts, a run-local language candidate and one Research Entity tooling repair. Promotion waits for target-machine and H1/H2 differential evidence.
