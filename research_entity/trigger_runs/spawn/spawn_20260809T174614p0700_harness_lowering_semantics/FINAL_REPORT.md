# SPAWN FINAL REPORT — Harness Lens: ClayCode Lowering Semantic Preservation

Run: `spawn_20260809T174614p0700_harness_lowering_semantics`

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol

Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

Origin branch: `harness`

Current program stage: `BASE_CLAYCODE_RELEASE`

Selected microdirection: **ClayCode lowering preservation of authority/provenance/epistemic fields**

## 1. Spawn receipt

The exact `spawn` trigger was resolved from the current GitHub registry and current weighted distribution.

OS-CSPRNG branch draw:

- draw: 57.50%
- selected branch: `harness`
- distribution: claycode 50 / harness 10 / frank 10 / gwt 6 / emergenz 6 / hyperposition 5 / claygraph 5 / unifieddb 4 / clayresearch 4

Six current-stage harness microdirections were generated after reading the BASE program, Harness workspace, ClayCode workspace and current ClayCode stack. The OS-CSPRNG microdirection draw selected index 3 (zero-based): ClayCode lowering preservation of authority/provenance/epistemic fields.

No indexed previous `SPAWN_RECEIPT.json` was returned by current GitHub code search. This is recorded as an indexing/novelty limitation rather than proof that no prior spawn run exists.

## 2. Why this question matters now

BASE ClayCode is explicitly in a compile/realize phase. It must deliver a real lowering pipeline, runtime/ABI/FFI, effect/capability gateway and translation-validation receipts. H2 later rebuilds the same frozen FRANK semantics in ClayCode and uses differential Harness execution as an oracle.

Therefore the immediate question is not whether to invent more ClayCode syntax. It is:

> Which Clay semantic fields must survive lowering, in what relation, and how can the compiler prove that optimization did not silently change authority, epistemic state or causal provenance?

This also avoids duplicate work: `H-WP-02-STATE-LEDGER` is currently actively claimed by another Harness worker. This run does not modify or claim that package.

## 3. Main result

The research supports a **field-classified LoweringWitness / translation-validator contract** rather than a metadata-only strategy and rather than a new language semantic primitive.

### Critical preservation classes

| Field class | Required relation across pure lowering | Recommended target representation | May be silently dropped? |
|---|---|---|---|
| AUTHORITY | monotone attenuation: target <= source | first-class capability/resource handle or checked runtime object | no |
| EFFECT_RESOURCE | semantic effect/resource equivalence | optimizer/runtime-visible operation or effect gateway | no |
| EPISTEMIC_STATE | exact equality unless an explicit semantic inference/state transition occurs | tagged first-class value/state | no |
| PROVENANCE | exact preservation OR deterministic hash/epoch-bound externalization | first-class when causally used; otherwise canonical ledger reference + derivation hash + epoch | no |
| TRACE_DEBUG_ONLY | no semantic obligation | metadata/sidecar | yes, if truly non-semantic |

The preservation contract is intentionally field-specific. A universal equality rule is too strict because capability authority can legitimately narrow and provenance can be externalized. A generic metadata rule is too weak because ordinary compiler transformations can legally erase metadata attached to an eliminated instruction.

## 4. External engineering triangulation

Current primary engineering sources converge on four useful mechanisms:

1. LLVM does not make arbitrary metadata part of executable semantics and transformations can drop metadata they cannot preserve.
2. MLIR distinguishes operation semantics/inherent state from discardable attributes and provides explicit conversion/materialization machinery; it does not automatically prove Clay-specific semantic equivalence.
3. Side effects/resources that matter to optimization correctness need explicit semantic modeling rather than invisible assumptions.
4. Capability systems and translation-validation systems provide relevant patterns: authority as resource-bound unforgeable/attenuable capability, and compiler correctness as per-transformation refinement/validation rather than trust in the optimizer.

These are analogues and engineering precedents, not independent proof that the proposed ClayCode contract is complete.

## 5. Executable mechanism evidence

### SP-EXP-LWR-001A — LoweringWitness mutation checker

A reference checker was executed in the current hosted runtime and then committed as `lowering_witness_reference_test.py`.

Observed:

- valid baseline: 0 errors
- intentional mutations: 12
- mutations rejected: 12/12
- exhaustive permission-set monotonicity cases over {read, write, exec}: 64
- oracle mismatches: 0

Mutation families included authority removal/broadening/rebinding, constraint/delegation/revocation changes, epistemic upgrade/drop, provenance removal/forgery and semantic-envelope tampering.

Evidence class: **synthetic deterministic mechanism test**. It does not prove the real ClayCode compiler.

### SP-EXP-LWR-001B — ordinary optimization erases custom metadata

A minimal LLVM IR fixture attached `!clay.auth` custom metadata containing epistemic/provenance text to a constant-foldable `add` instruction.

Executed with:

`clang -O2 -S -emit-llvm`

Observed with clang 17.0.0:

- the `add` was optimized away;
- the function became a direct `ret i32 2`;
- no `clay.auth`, `epistemic` or provenance custom metadata remained in the optimized IR.

This is a concrete counterexample to the hypothesis that instruction-bound custom metadata is, by itself, a sufficient carrier for critical Clay semantics.

It does **not** show that all metadata is always erased.

## 6. Hypothesis adjudication

### Supported / selected

- Critical authority/epistemic/effect semantics must be first-class or protected by an explicit translation-validation obligation.
- Authority preservation should be monotone attenuation, not unconstrained equality or textual-name matching.
- Epistemic UNKNOWN/CONFLICT/REVOKED-like states must remain exact across a pure lowering step; changing them is a semantic operation, not compiler housekeeping.
- Provenance may be externalized only if the executable/result is deterministically bound to the exact derivation hash and source epoch.
- A LoweringWitness belongs in compiler/runtime realization work under current ClayCode semantics unless a real executable counterexample proves a language semantic gap.

### Counterhypotheses not selected

- "Check everything before lowering and then forget it." Rejected because FRANK later requires delayed effects, replay, recovery, outcome/re-entry and H1/H2 differential verification.
- "Custom target metadata is enough." Counterexample found.
- "Every field must be byte-identical." Too strict; capability attenuation and provenance externalization are legitimate when explicitly validated.
- "A successful LoweringWitness grants execution authority." Rejected by the existing authority boundary. A translation proof cannot mint a capability.

## 7. Candidate LoweringWitness contract

A future executable compiler object should minimally bind:

- source Clay/IR semantic hash;
- canonical IR hash;
- target artifact/IR hash;
- compiler/runtime version;
- optimizer-pipeline hash;
- per-field preservation obligations and verifier results;
- resource/capability identity and relevant revocation epoch;
- provenance ledger reference, derivation hash and source epoch where externalized;
- overall PASS/FAIL.

Core laws:

- `target_authority <= source_authority`
- `pure_lowering(epistemic) == source_epistemic`
- `provenance = exact OR hash_epoch_bound_externalization`
- `effect/resource_semantics remain optimizer-visible`
- `LoweringWitness != execution_authority`

## 8. Negative result

`NR-SPAWN-LWR-001`:

> Generic custom LLVM metadata alone is not a sufficient carrier for critical Clay authority/epistemic semantics across optimization.

This negative result should remain alive even if a future backend happens to preserve a particular metadata instance; the compiler contract cannot depend on incidental pass behavior.

## 9. Research Center feedback

Material feedback was written to all affected branches:

- `claycode`: NEW_CONSTRAINT — implement field-classified translation validation in CC-WP-06/07/11/13; no semantic redesign yet.
- `harness`: NEW_HYPOTHESIS — H2 mutation/differential tests must intentionally drop/broaden critical lowered fields and fail closed.
- `frank`: NEW_CONSTRAINT — mark architecture fields that are lowering-critical.
- `unifieddb`: NEW_CONSTRAINT — externalized provenance requires exact artifact/hash/epoch binding and cannot replace execution-time semantic state.
- `claygraph`: NEW_CONSTRAINT — graph relevance/provenance must never become authority through lowering.
- `clayresearch`: NEW_CONSTRAINT — maintain an explicit semantic-vs-external-binding-vs-debug classification across backends.
- `gwt`, `emergenz`, `hyperposition`: NO_CHANGE to their mechanisms; preservation applies if their causally relevant state is compiled.

No stage gate is passed by this run.

## 10. Next discriminating experiment

`SP-EXP-LWR-002` is the highest-information next step:

1. implement the LoweringWitness in the real ClayCode compiler path;
2. execute on the Ubuntu developer-system target;
3. record source -> canonical IR -> optimized target -> execution receipt identities;
4. inject independent mutations that drop/broaden authority, change epistemic state, forge/drop provenance binding and hide effect/resource semantics;
5. require fail-closed validation before target execution;
6. run normal positive programs through the same validator to measure false positives and overhead;
7. feed results into CC-WP-06/11/13 and later H-WP-03/H-WP-20.

Only that target-compiler evidence can support a BASE/H2 semantic-preservation claim.

## 11. Limitations

- No final ClayCode compiler exists at the current BASE gate.
- No real ClayCode compilation was run on Andreas' Ubuntu target from this hosted worker.
- No live FRANK runtime evidence was generated.
- No complete SMT proof was produced.
- Current GitHub search did not expose indexed prior spawn receipts, so novelty checking is incomplete.
- A materialized Harness `ROOM_STATE.json` was not found at the expected path; current live-worker state was taken from `HARNESS_WORKSPACE.json`.

## 12. Durable artifacts

This run wrote:

- `SPAWN_RECEIPT.json`
- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESES.json`
- `EVIDENCE_MANIFEST.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `LOCAL_TEST_RECEIPT.json`
- `lowering_witness_reference_test.py`
- `clay_metadata_test.ll`
- `FINAL_REPORT.md`

The run intentionally does not update canonical revision or claim scientific promotion. Its contribution is a falsifiable compiler/Harness constraint, a negative result against metadata-only preservation, reproducible local mechanism evidence and a target-host next experiment.
