# SPAWN RESEARCH RUN — ClayGraph · Reversal-Aware Binding (RAB)

**run_id:** `spawn-20260809T1742p0700-chatgpt-secondary-claygraph-rab`  
**trigger:** `spawn`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**stochastic origin branch:** `claygraph`  
**candidate:** `RAB-0.1 — Reversal-Aware Binding`  
**decision:** **OPEN / HOLD — research delta committed; no accepted ClayGraph or canonical promotion**

## 1. Stochastic genesis

The branch was selected using the registered weighted `spawn` distribution and an OS-backed CSPRNG. Integer draw `88` landed in the ClayGraph interval `88-92`. No seed is claimed because the draw used `secrets.SystemRandom`.

After current-mesh grounding and duplicate filtering, five materially distinct ClayGraph microdirections were enumerated. A second OS-CSPRNG draw selected index `0`, `CG-SP1 — reversal-aware fast/slow binding`. No reroll was used.

Exact selection details are preserved in `SPAWN_RECEIPT.json`.

## 2. Research question

> Can ClayGraph rapidly adapt to a genuine relation reversal while refusing a false reversal created by correlated/duplicated source echo, without deleting the prior valid relation or turning activation into truth?

This question was selected because it sits directly on an unresolved boundary between:

- G3's negative result that naive salience/propagation can create self-confirming attractors;
- the G9 Dynamic Binding Lattice candidate's fast/slow and provenance-diversity semantics;
- Hyperposition's separation of fast routing from slow topology promotion;
- UnifiedDB's replay/selection identity requirements;
- FRANK/GWT recurrence, where repetition or re-entry must not be mistaken for causal support.

## 3. Current-state grounding

### ClayGraph

The accepted `CLAYGRAPH_LATEST.claycode.json` remains generation 0 / `SEED_BASELINE`; it has scalar typed edge weighting and a separate activation overlay. The newer runtime V2 overlay adds hyperrelations and projection/selection/receiver receipts, but activation remains derived and non-authoritative.

The most important prior ClayGraph negative result comes from G3/IBCA: graph propagation hurt a precise exact lookup in a small staged benchmark, and naive positive salience can become a self-confirming attractor. Therefore this run retains exact/high-confidence BYPASS or sharply capped graph gain rather than trying to make every query dynamic.

### ClayCode

The current G9 Dynamic Binding Lattice is already an OPEN research candidate. It distinguishes fast binding from slow binding, requires causal/outcome support for slow consolidation, penalizes duplicated ancestry through `PROVENANCE_DIVERSITY`, preserves conflict/inhibition, and requires reversible promotion. This spawn does not duplicate that candidate. It isolates one hard falsification problem inside it: **genuine reversal versus source echo**.

Current BASE governance says `less change, more compile`. RAB is therefore represented as a shadow candidate contract, not a new language syntax mandate.

### FRANK / GWT / Emergenz

Fresh FRANK loop research proposes epoch-bound derived loop topology and explicitly rejects truth promotion from repeated loop use. Fresh GWT R8 distinguishes trajectory/recurrence state from convergence, authority and emergence. Fresh Emergenz research requires common-driver/source-confound controls, intervention, lesion/rescue, shuffled controls and OOD validation before causal promotion.

RAB is compatible with those boundaries: it is a retrieval/topology stability mechanism, not an emergence measure or causal-proof mechanism.

## 4. External research synthesis

External evidence was used as mechanism context, not as target validation.

- **Temporal Graph Networks** (`arXiv:2006.10637`) are a strong dynamic-graph baseline showing that event time and evolving node state can be first-class rather than flattened into a static graph.
- **Continual Learning, Fast and Slow / DualNets** provides a relevant fast-adaptation / slow-consolidation design family. The transfer is architectural analogy only; it does not validate ClayGraph's exact mechanism.
- **Adaptive Memory Realignment under Concept Drift** (`arXiv:2507.02310`) and online change-point work motivate selective adaptation when a distribution or relation changes rather than treating all history as equally current.
- **GraphRAG knowledge-poisoning work** (`arXiv:2508.04276`) supplies adversarial pressure: a graph can propagate a small poisoned source into larger retrieval effects, so repetition/connectivity cannot authenticate itself.
- Recent provenance-aware multi-source KG work supplies a compatible engineering principle: source identity and derivation provenance should remain explicit rather than being collapsed into repeated statements.

None of these sources establishes RAB superiority for FRANK. They justify the discriminator family and baselines.

## 5. Candidate mechanism

RAB has six core rules:

1. **Context is part of binding identity.** If A implies `+` in context X and `-` in context Y, this may be a valid bifurcation rather than a reversal.
2. **Fast state may react immediately.** Recent contradictory observations can alter transient activation/retrieval without changing durable topology.
3. **Durable reversal starts in SHADOW.** A candidate does not overwrite the current binding immediately.
4. **Generic promotion requires provenance diversity.** Repeated contradictions from one ancestry/source family do not count as multiple independent supports.
5. **Previous state is archived/suppressed, not deleted.** Version intervals and rollback/replay remain possible.
6. **Exact authoritative updates are a separate path.** A legitimate one-source exact update must not be forced to fake multi-source diversity; it uses its own evidence/authority semantics rather than generic associative promotion.

The complete shadow-only candidate is in `RAB_CANDIDATE_CONTRACT.clay`.

## 6. Executable mechanism tests

Both experiments are **constructed local synthetic tests**, not live FRANK/Harness evidence.

### EXP-SPAWN-CG-RAB-001 — four-scenario comparison

Arms:

- global signed EMA;
- context-aware signed EMA;
- ungated dual fast/slow state;
- RAB: fast state + bounded reversal window + provenance-diverse slow promotion.

Scenarios:

- genuine global reversal;
- false reversal burst from one duplicated `echo_family`;
- stable context bifurcation;
- reversal then restoration.

Noise: `5%`, `10%`, `20%`; 200 replicates per scenario/noise cell.

#### Genuine reversal

At 5% noise:

- context EMA accuracy `0.974396`, adaptation lag `6.08`;
- RAB accuracy `0.972896`, lag `6.11`.

At 10%:

- context EMA `0.973313`, lag `6.23`;
- RAB `0.970000`, lag `6.415`.

At 20%:

- context EMA `0.965875`, lag `7.005`;
- RAB `0.958521`, lag `7.315`.

RAB therefore did **not** improve ordinary true-reversal adaptation. At moderate noise it was close; at high noise it became measurably worse.

#### Correlated source echo

At 5% noise, a 25-step false contradictory burst all descended from one `echo_family`:

- context EMA echo error `0.5139`;
- ungated dual fast/slow `0.4678`;
- RAB `0.0114`.

At 10%:

- EMA `0.5355`;
- ungated dual `0.5054`;
- RAB `0.0319`.

At 20%:

- EMA `0.5903`;
- ungated dual `0.5928`;
- RAB `0.1088`.

This is the strongest positive mechanism result: a provenance-diverse gate can block a false slow reversal that raw frequency and ordinary fast/slow integration accept.

#### Context bifurcation — important negative

At 10% noise:

- global EMA accuracy `0.318333`;
- context EMA `0.993458`;
- RAB `0.988896`.

So the main solution to context bifurcation is simply **context identity**. RAB adds no demonstrated benefit there and should not be sold as a universal dynamic-graph improvement.

### EXP-SPAWN-CG-RAB-002 — provenance-diversity ablation

A second experiment swept the minimum distinct source-family requirement `k=1..5`, 500 replicates per cell.

At 10% noise:

- `k=1`: true lag `6.422`, echo error `0.52040`;
- `k=2`: true lag `6.422`, echo error `0.15528`;
- `k=3`: true lag `6.422`, echo error `0.03408`;
- `k=4`: true lag `6.468`, echo error `0.00588`;
- `k=5`: true lag `6.974`, echo error `0.00116`.

At 20% noise:

- `k=3`: true lag `7.320`, echo error `0.12856`;
- `k=4`: true lag `7.360`, echo error `0.03448`;
- `k=5`: true lag `8.010`, echo error `0.01144`.

Within this constructed benchmark, `k=3-4` captures most echo protection with little true-reversal lag cost through moderate noise, while `k=5` begins a clearer adaptation penalty. This **does not calibrate a production threshold**.

The scripts are persisted as `EXPERIMENT_RAB.py` and `EXPERIMENT_RAB_PROVENANCE_ABLATION.py`; aggregates are in `EXPERIMENT_RESULTS.json`.

## 7. What the experiments actually discriminate

The result does **not** show that a multi-axis lattice is globally better than a scalar graph.

It does show a narrower mechanism:

`raw repetition count` and `independent evidence support` are operationally different variables.

Under a constructed correlated-source failure, a scalar/ungated fast-slow system cannot distinguish twenty repeated copies from twenty independent supports unless source ancestry enters the state transition. RAB can.

The price is stability/plasticity tension: stronger diversity requirements reduce false reversal but can slow true reversal when evidence is noisy or source-sparse.

## 8. Counterhypotheses that survive

1. **Scalar sufficiency:** a better context-aware signed scalar model plus robust-source weighting may match RAB with less machinery.
2. **Context-only explanation:** some apparent gains from dynamic binding disappear once context is correctly represented.
3. **Over-stabilization:** in sparse/high-noise real traces, provenance diversity may delay needed adaptation too much.
4. **False independence:** provenance-family IDs can be wrong or adversarially diversified; a naive diversity counter is gameable.
5. **Single authoritative update:** some real reversals should be accepted from one exact authoritative source, requiring a typed exception rather than arbitrary multi-source consensus.

These remain OPEN and are part of the next test package.

## 9. BASE-stage consequence

Do **not** modify accepted ClayGraph or reopen ClayCode syntax design from this run.

Highest-information BASE action:

- use `RAB_CANDIDATE_CONTRACT.clay` as an expressibility/counterexample fixture for current G9 parser/canonical IR/type/effect/evaluator work;
- require current semantics to carry context, provenance family, binding-version validity, SHADOW/CONFLICT/UNKNOWN, promotion receipt and rollback identity;
- only if the existing compiler path cannot represent/execute those semantics should a language change be proposed.

This matches the program's current `less change, more compile` law.

## 10. H1/H2 discriminator package

When Reference Harness H1 becomes available, run matched-cost arms on frozen episodes:

1. scalar context-aware edge;
2. ungated fast/slow binding;
3. RAB provenance-diverse gate;
4. RAB with provenance gate lesioned;
5. RAB rescue restoring the gate.

Fixtures:

- true reversal;
- duplicate source echo;
- multiple nominal sources with shared ancestry;
- provenance-family spoof / false independence;
- context bifurcation;
- single authoritative exact update;
- stale/out-of-order replay;
- rollback and rebuild;
- source sparsity and high-noise OOD.

Primary outcomes:

- verified task gain;
- true-reversal adaptation lag;
- false-reversal rate;
- context preservation;
- echo sensitivity;
- replay equivalence;
- rollback success;
- update amplification;
- latency/RAM cost.

H2 must reproduce the same semantic transitions in ClayCode and differential-test them against H1. No semantic benefit is established until the simpler baselines are beaten at matched cost.

## 11. Mesh feedback

The run returns a durable delta to all nine current research branches. Most important:

- **ClayGraph:** OPEN RAB hypothesis; archive/version instead of overwrite.
- **ClayCode:** express current semantics first; no syntax mandate.
- **Harness:** future reversal/echo/spoof/replay ablation package.
- **UnifiedDB:** provenance-family/source-epoch/version/promotion identity must be replayable; duplicates are not independent evidence.
- **FRANK:** repeated recurrence/re-entry must not consolidate slow memory by itself.
- **Hyperposition:** context alternatives should remain simultaneously representable.
- **GWT:** no change to receiver-causal boundary; graph promotion is upstream state only.
- **Emergenz:** source echo is a confound, not causal evidence.
- **ClayResearch:** retain the stability/plasticity Pareto frontier; richer state is not universally superior.

See `BRANCH_FEEDBACK_MANIFEST.json`.

## 12. Decision

**RAB-0.1 = OPEN / HOLD.**

The run produced a material research delta because it found a sharp failure mode where provenance diversity matters and quantified a corresponding adaptation cost. It did not produce target-runtime evidence, accepted-graph superiority, a ClayCode language counterexample, or a canonical scientific-generation change.

The next discriminating step is therefore not more speculative topology design. It is:

> **compile the RAB semantic fixture through current BASE ClayCode, then after BASE execute the reversal-vs-source-echo lesion/rescue package in H1 and reproduce it in H2.**
