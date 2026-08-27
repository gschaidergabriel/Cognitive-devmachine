# ATOMIC FINAL REPORT — Counterfactual Jet Commutator (CJC)

## Result
This invocation produced a substantially larger executable candidate than the previous ATOMIC run: **ATOMIC-CANDIDATE-CJC-001 / Counterfactual Jet Commutator**.

CJC generalizes the previous CCF possibility by asking not only whether `A;B` and `B;A` produce the same observed state, but whether they remain equivalent throughout the represented **counterfactual lesion/context space**. It also reuses the same sparse polynomial representation for causal-use/interaction readouts, creating a testable bridge to the concurrent CPD possibility.

## Executable discovery that changed the design
The first attempted formulation was wrong: with only A and B and ordinary leave-one-out intervention, equal full outputs cannot by themselves reveal order-specific credit. The code falsified that idea. The mechanism was revised to contextual masked order effects.

Canonical witness: `x=1; A=*2; B=+1; C=set(0)`. Both full orders end at `x=0`, so a state-only commutator says safe. Lesion C exposes `A;B=3` versus `B;A=4`. CJC represents this as a nonzero commutator polynomial whose value at the observed all-enabled point is zero.

## Executable implementation delivered
The versioned packet contains:
- sparse Boolean-jet algebra and state/epoch identity;
- exact transition operators ADD, SET, SCALE, COPY_ADD, SWAP plus opaque fail-closed surface;
- contextual CJC classifier plus exhaustive reference and causal-credit replay;
- strict TypedIR/CallContract adapter with anti-inference gates;
- direct Frank-v0.1 coordination fabric/gate;
- consolidated deterministic + randomized differential tests;
- compact reproducible context-scaling benchmark;
- one-command `RUN_CJC.py` runner;
- ClayCode-first semantic candidate.

The full local development suite reached **35/35 PASS**. The compact persisted repo suite separately reached **17/17 PASS**, including 2,500 randomized differential cases. A repo-layout simulation of `RUN_CJC.py` passed tests, demo and benchmark together.

## Primary proxy measurements
Primary pair benchmark, N=20,000:
- exact CJC classification accuracy: 1.0;
- hidden causal noncommutativity: 784 cases;
- current-state-only baseline falsely marked all of those safe: 3.92% of all cases;
- conservative read/write baseline: 1,016 false conflicts and 0 unsafe commute in the generated class.

Counterevidence is preserved: generic Python CJC is much slower than exhaustive replay at tiny context.

Context scaling:
- 2 total UseRefs / 4 truth-table points: exhaustive replay much cheaper;
- 8 UseRefs / 256 points: CJC crosses ahead in the primary run;
- 10 UseRefs / 1,024 points: exhaustive reference/CJC wall time = **5.24x**.

Five independent replication seeds add 25,000 pair cases:
- every exact-eligible classification matched exhaustive reference;
- hidden rate mean 3.684% (range 3.24–3.90%);
- first crossover contexts were [6, 8, 6, 6, 8];
- every replication crossed by context length <= 8.

Negative controls fail closed for stale epoch, opaque semantics and symbolic budget overflow. External-effect pairs route to the normal effect gate. CJC mints no authority.

## Direct Frank v0.1 gate
A new direct `FrankV01CoordinationGate` consumes current execution identity plus exact CJC transitions and produces:
- `INDEPENDENT_EXACT`;
- `COORDINATE_STATE_ORDER`;
- `COORDINATE_HIDDEN_CAUSAL`;
- `FALLBACK_UNKNOWN`;
- `FALLBACK_EFFECT_GATE`;
- `REJECT_STALE_STATE`.

The executable demo isolates an independent `D` transition while A/B/C form a coordination component because A/B are hidden-causal under the masking context and B/C visibly depend on order. `authority_minted=false` throughout.

## Live owner supersession
During this run the repository moved to a single active **Frank v0.1-only** program. H1/H2/H3 and a separate Harness product are historical/diagnostic only. The candidate and final next-test plan were rebound accordingly: CJC must now be tested directly against current Frank v0.1 transition traces.

## Prior art / novelty
Known components include semantic commutativity, multilinear/Harsanyi interaction decompositions, provenance polynomials and counterfactual attribution. No equivalent complete CJC runtime composition was found in the searched scope. Classification remains **NOVEL_COMBINATION_CANDIDATE**, not world-first.

## Decision
**NO ARCHITECTURE PROMOTION.** Status `SUPPORTED_PROXY_RETEST`.

Strongest remaining falsifier: measure real current Frank-v0.1 exact-eligibility coverage and compare CJC against a conventional compiler commutativity scheduler + occasional exhaustive replay + separate causal credit under matched native/target-VPS correctness, latency, CPU/RAM, recovery and stale-state tests.
