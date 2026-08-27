# FRANK Trigger Run — Adversarial Architecture Fusion

**run_id:** `frank-20260809T1926p0700-chatgpt-secondary-adversarial-fusion`  
**trigger:** `frank`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**identity:** Research Entity temporary worker; NOT Frank  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**target host:** Ubuntu Linux developer system only  
**head window examined:** through the 2026-08-09 19:25 +07 concurrent build burst, including `c5466791`, `8d937162`, `44ca9574`, `61896b38`, `571e3361`, `b9c57440`, `9f00129d`, `70a71ef9`, `f6b9068c`, `c8ca2e5d`  
**scientific promotion:** `NONE`

## 1. Purpose

This exact-`frank` cycle reread the newest concurrent FRANK/ClayCode/Harness deltas after the previous dynamic fusion, checked current primary external research, then attacked the newly executable H1 reference slices rather than adding another architectural layer.

The fixed target remains unchanged:

`LOCAL_FRANK = ONE_CLAY_BINARY + ONE_LOCAL_UNIFIEDDB + ONE_CLAY_NATIVE_4B`

with H1 ordinary-code reference semantics first, H2 the same frozen semantics in ClayCode, and H3 consolidation only after differential evidence.

The run found two material integration defects and one concurrent negative->fix sequence. None justifies a new ClayCode syntax feature or scientific-generation promotion.

## 2. Current positive execution delta

### ActiveAssembly is now executable reference semantics

`research_entity/harness/reference/active_assembly.py` plus `test_active_assembly.py` has an executed hosted-Linux component receipt:

- 8/8 tests passed;
- deterministic assembly hash under permutations;
- bounded item budget;
- stale-epoch exclusion;
- omitted detail retains re-expansion refs;
- capability visibility remains non-authoritative;
- cognitive packets cannot mint bearer authority;
- a 5,000-trial constructed source-echo fixture retained explicit independent counterevidence in 5,000/5,000 ancestry-aware cases versus 4,212/5,000 naive top-3 cases.

This is useful H1 reference-component evidence, not target-Ubuntu or live-FRANK evidence.

### Loop dynamics has two separately useful reference lines

The older `loop_dynamics_quality_gate.py` adds readout-quality controls:

- residual estimator identity/version;
- residual uncertainty;
- measurement age/freshness;
- explicit uncertain routing;
- 9/9 component tests plus 100,000 property cases with zero violations under its registered invariant set.

The newer `loop_dynamics_reference.py` adds stronger dynamical semantics:

- explicit `CONVERGING_FIXED_POINT`, `PRODUCTIVE_LIMIT_CYCLE`, `STALLED`, `DIVERGING_OR_OVERTHINKING`, `CHAOTIC_OR_UNCLASSIFIED` regimes;
- convergence requires both low state delta and low residual pressure;
- oscillation and overthinking enter classification;
- recurrence budget and rollback behavior are explicit;
- every decision remains `PROPOSAL_ONLY`.

These two lines currently complement one another but are not yet one frozen H1 oracle.

## 3. Red-team finding A — ActiveAssembly conflict observability can be defeated by ancestry cap

### Counterexample

The current compiler first identifies contradictory values for a `claim_key`, but inserts those representatives through the same `add()` function that enforces `max_per_ancestry`.

Construct:

- packet A: `claim_key=k`, `claim_value=yes`, `ancestry_family=famA`;
- packet B: `claim_key=k`, `claim_value=no`, `ancestry_family=famA`;
- both current epoch, enough total `max_items` budget;
- `max_per_ancestry=1`.

The first conflict representative consumes the family quota and the second contradictory value is omitted. This occurs even when overall item budget remains available.

Therefore the current implementation does **not** universally satisfy the architecture statement:

`unresolved contradiction remains visible when budget permits`.

The ancestry cap is correctly preventing duplicated ancestry from masquerading as independent evidence, but it is currently also acting as a visibility eraser for a contradiction that happens to share ancestry.

### Required semantic distinction

`shared ancestry => not independent evidence`

must remain true, but it does **not** imply:

`shared ancestry => hide one contradictory proposition`.

Recommended H1 contract:

1. general salience/redundancy selection remains ancestry-capped;
2. unresolved conflict observability is a separate semantic requirement;
3. when both contradictory values cannot occupy ordinary item slots, emit a deterministic conflict capsule/metadata record containing both packet/value identities, ancestry relation, uncertainty and re-expansion refs;
4. shared-ancestry conflict receives zero independent-replication credit merely because both sides are visible;
5. test conflict preservation under `max_per_ancestry=1`, tight total budgets, multiple conflicts, stale branches and duplicate packet IDs.

### Falsifier

If a simpler representation can preserve both propositions, shared ancestry and bounded context with lower cost and identical downstream conflict recall, use the simpler representation. The finding requires conflict observability, not a specific conflict-capsule implementation.

## 4. Red-team finding B — two loop controllers form a semantic fork

### What the older quality gate gets right

`loop_dynamics_quality_gate.py` correctly learned from the 50,000-episode synthetic experiment that residual-pressure routing is unsafe unless the residual readout itself has quality identity. It therefore checks estimator identity/version, uncertainty and measurement age before allowing candidate convergence.

The underlying synthetic result is informative but deliberately non-promotional: delta-only halting generated 23.208% overall false convergence and 100% false convergence on the constructed STALLED class; the typed pressure-aware controller removed that failure at low noise, but false convergence reappeared as residual-readout noise increased. That negative result is precisely why readout quality/freshness was made explicit.

### What the newer dynamics reference gets right

`loop_dynamics_reference.py` fixes a different weakness:

- convergence now requires `low delta AND low residual`, rather than low residual alone;
- productive oscillation can continue;
- divergence/overthinking can abort/rollback;
- exhausted budget routes instead of blindly continuing.

This is a better regime classifier.

### The integration defect

The newer controller does **not** carry forward the older gate's:

- `residual_estimator_id`;
- `residual_estimator_version`;
- `measurement_age_cycles`;
- explicit stale/missing-estimator routing.

It carries a generic `uncertainty` field but does not use that field in `classify_regime()` or `decide_recurrence()`.

Thus a stale or high-uncertainty low-delta/low-pressure readout can again become `HALT_CANDIDATE_CONVERGED` in the newer line, even though the previous experiment explicitly identified readout quality as a required guard.

Conversely, the older quality gate has weaker regime semantics: its convergence branch does not require low state delta, and its `oscillation_indicator` does not participate in the decision.

Neither implementation should independently become the H1 release oracle.

### Required fused H1 controller

Freeze one controller with both families of semantics:

**Typed dynamics:**
- loop identity/family/timescale;
- state epoch;
- state delta;
- residual pressure;
- recurrence count/budget;
- marginal utility/cost;
- oscillation/metastability indicator;
- overthinking/divergence indicator;
- rollback/checkpoint reference.

**Readout quality:**
- residual estimator identity;
- estimator version / calibration identity;
- readout uncertainty;
- measurement age/freshness;
- provenance/evidence refs;
- controller policy/threshold identity and hash.

**Fail-closed ordering:**
1. reject or route invalid/non-finite/out-of-domain readouts;
2. route missing/stale/over-uncertain estimator state;
3. classify divergence/overthinking;
4. classify convergence only from low delta + low residual under valid readout quality;
5. classify stall from low delta + material residual;
6. preserve productive bounded cycles when margin/budget supports continuation;
7. route unclassified cases rather than inventing convergence;
8. every recurrence decision remains compute-routing proposal state, never external-effect authority.

### Required discriminators

- high delta + low residual must not be candidate convergence;
- low delta + high residual must be STALLED candidate;
- stale/missing/high-uncertainty estimator cannot emit candidate convergence;
- NaN/Inf/negative/out-of-range readouts fail closed;
- oscillation only changes policy when its estimator is valid;
- threshold/policy changes change receipt identity;
- event-driven and fixed-budget controls remain baselines;
- frozen-trajectory simple post-hoc readout is compared against jointly trained/learned halting before any learned gate is promoted.

## 5. External research fusion

Current primary research sharpens the same boundary rather than selecting a FRANK mechanism.

- Kohli et al., `arXiv:2604.07822`, report that scaling recurrent-depth inference iterations can improve deeper compositional reasoning, but also identify **overthinking** where excessive recurrence degrades predictions. This supports keeping productive recurrence and overthinking as distinct measurable regimes.
- Popescu, Borde & Liò, `arXiv:2607.20519`, separate trajectory formation from exit readout and find that simple post-hoc readouts on fixed-prior/frozen trajectories can match or outperform learned halting gates in their studied settings. This directly supports FRANK's requirement for frozen-trajectory/readout baselines before training a sophisticated halting controller.
- Fixed-Point Reasoners (`arXiv:2606.18206`) supplies a useful fixed-point-halting baseline, but does not justify treating fixed-point convergence as a universal FRANK cognitive-quality criterion; FRANK still needs productive-cycle and outcome/cost baselines.

No external paper is treated as live-FRANK evidence.

## 6. Multimodal 4B physical-backing discriminator

Current official Qwen material shows `Qwen3.5-4B` as a 4B causal language model with a Vision Encoder and an image-text-to-text interface. Its configuration exposes a separate vision configuration while the text core is a hybrid Gated DeltaNet/full-attention architecture.

This creates a worthwhile **physical backing** discriminator for FRANK's fixed semantic Digital Retina/MVC architecture:

`separate visual backing baseline`
versus
`same target Qwen-class 4B supplies numerical visual features`.

The semantic Retina/MVC surfaces, provenance, open-set behavior, lesion/rescue and rollback remain unchanged either way. Physical reuse is promoted only if target-Ubuntu latency/RAM, feature-version stability, open-set behavior and failure-correlation tests beat the separate baseline.

This is not a Qwen3.5-4B model-selection decision.

## 7. Authority closure — negative -> concurrent fix

During this run the first `claycode_base_runtime.py` candidate was found to accept the `process.exec` program allowlist as a caller argument. A holder of generic `process.exec` capability could therefore choose the allowlist itself; the corresponding first adversarial suite only tested a caller-chosen positive and negative allowlist and did not expose the laundering flaw.

Before this run finalized, concurrent ClayCode work fixed the issue:

- capability policy is now fixed at mint time and hashed into the opaque handle;
- process executable scope is no longer caller-provided;
- async arbitrary-callable laundering is removed in favor of policy-scoped operations;
- filesystem/database prefix and numerical limits can be capability-bound;
- an adversarial regression explicitly checks that the caller cannot widen process allowlists or inject arbitrary async callables.

Subsequent commits further bind process authority to canonical executable paths and reject basename collisions.

Therefore this is recorded as a **blocker discovered and concurrently eliminated**, not as an open current blocker.

The remaining security requirement is still stronger than Python object identity: the production Ubuntu acceptance path needs OS/process-level ambient-right restriction and effect-closure testing. Linux Landlock is a current primary mechanism worth evaluating because it can stack unprivileged filesystem/network restrictions on processes. It is a candidate substrate, not architecture authority.

## 8. ClayCode / BASE interpretation

At the examined workspace state, `CC-WP-01-SPEC-FREEZE` is the only release-package PASS. New WP03/04/07/08/09/10/11 candidates and Ubuntu-CI definitions are substantial implementation evidence, but the project accounting law correctly prevents them from becoming package PASS until their required production/target receipts exist.

A particularly good infrastructure change in this burst is failure-receipt preservation: WP03 CI now records execution/failure artifacts before enforcing the failing gate. Negative implementation evidence therefore remains part of the reproducible build history instead of disappearing when CI exits nonzero.

No semantic redesign is justified by this run. Both new red-team findings are expressible as H1/H2 contract/test corrections under frozen BASE semantics.

## 9. Updated highest-information cascade

1. **Fuse the loop controller fork before H1 freeze promotion.** One oracle must combine regime semantics with estimator quality/freshness/policy identity.
2. **Fix ActiveAssembly conflict observability.** Ancestry caps may suppress replication credit, never silently erase an unresolved opposite proposition.
3. **Close WP02 production parser/canonical receipt.** Later H2 equivalence still depends on one exact canonical source/IR identity.
4. **Consume, do not duplicate, current WP03/04/runtime/authority CI work.** Promote only from receipts.
5. **Execute V2 ordinary-code H1 freeze + Golden Traces.** ActiveAssembly and fused loop dynamics become two frozen components of that spine.
6. **Matched H1 discriminators:** broad retrieval vs prepared Assembly; event-driven/fixed vs typed recurrence; self-verification vs provenance-bound strong-peer verification; separate vs same-4B vision backing.
7. **Ubuntu target tests:** compiler/runtime/SQLite/concurrency/authority/Landlock or equivalent sandbox/recovery/model backend.
8. **H2 translated semantic differential, then H3 consolidation.** Any H2 expressibility failure reopens the smallest BASE semantic point instead of weakening FRANK.

## 10. Promotion / non-claims

- No r3 scientific-generation promotion.
- No H1 release PASS.
- No ClayCode package promotion from candidate/hosted-CI evidence alone.
- No adaptive-recurrence promotion.
- No claim that ActiveAssembly ranking is optimal.
- No Qwen3.5-4B final model selection.
- No consciousness inference.

## 11. Final synthesis

The newest evidence supports the architecture direction while exposing a predictable risk of high-concurrency development: **locally correct components can reintroduce already-solved semantic failures when parallel lines are not fused.**

For FRANK, the immediate architecture work is therefore not to add more mechanisms. It is to make the current ordinary-code H1 reference internally single-valued:

`one ActiveAssembly conflict contract`
+
`one LoopDynamics/ReadoutQuality controller contract`
+
`one sealed effect-authority contract`
+
`one event/epoch/replay identity`

before those semantics are frozen into Golden Traces and transferred into ClayCode H2.

**Research write:** committed as an adversarial integration delta. Existing BASE14/H1 dynamic work remains authoritative; no duplicate work event was created.