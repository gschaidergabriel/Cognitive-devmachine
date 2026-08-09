# FRANK — Context-Budget ActiveAssembly Build + Adversarial Selection Benchmark

Run: `frank-20260809T1934p0700-chatgpt-secondary-context-budget`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Identity: Research Entity temporary worker; NOT Frank  
Canonical parent: RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Target: Frank v0.1 on Ubuntu Linux developer system  
Execution surface this run: hosted Linux reference environment, not Andreas target host  
Scientific promotion: NONE

## 1. Why this delta was selected

The current FRANK target is still the evidence-gated one-local-core direction:

`ONE_CLAY_BINARY + ONE_LOCAL_UNIFIEDDB + ONE_CLAY_NATIVE_4B`.

The immediately preceding ActiveAssembly cascade made a bounded small-model cognitive slice executable and ranked a matched retrieval-vs-Assembly benchmark as a high-value open discriminator. Concurrent work then upgraded packet identity/replay semantics to ActiveAssembly v1.1. This run re-fused that change before mutating code.

A concrete resource mismatch remained: the compiler bounded **item count** but not the actual model-facing context cost. For a local 4B, packet count is not a sufficient proxy for token/KV/context pressure. A handful of large packets can exceed the intended cognitive slice while many short packets may fit.

P0 target-host three-ledger work remains open because this hosted worker did not have Andreas target-PC execution. This run therefore selected the highest-value discriminator that could actually be built and falsified here without pretending target-host execution.

## 2. External research synthesis

The external evidence does not justify the slogan "more context is better".

- `Lost in the Middle` (arXiv:2307.03172) demonstrates that long-context availability does not imply uniformly reliable access to relevant evidence across positions.
- AdaGReS (arXiv:2512.25052) explicitly treats context selection as a **set-level token-budget problem**, penalizing redundancy rather than merely taking top-k chunks.
- SARA (arXiv:2507.05633) provides another mechanism family for preserving fine-grained evidence while compressing/selecting under tight context budgets.
- `Know Before You Fetch` (arXiv:2606.29959) treats retrieval depth itself as a calibrated budget-allocation decision and shows token/latency tradeoffs vary with model/system scale.
- `DRAGged into Conflicts` (arXiv:2506.08500) shows that conflicting retrieved sources remain a substantive failure mode; explicit conflict handling improves behavior but does not solve it completely.
- `Adaptive Depth in Looped Transformers` (arXiv:2607.20519) independently supports the current FRANK recurrence law that trajectory formation and halt/readout selection should be separated during evaluation rather than assuming a learned adaptive gate is automatically superior.
- The official Qwen `Qwen3.5-4B` model card confirms a current 4B-class multimodal model exists. This is candidate/runtime-relevance evidence only; this run does not select it as Frank's final Clay-native 4B and does not replace target-host measurement.

The shared implication for ActiveAssembly is narrower and testable:

`hard model-facing resource budget + explicit conflict/provenance semantics + budget-matched selection baselines` is justified as an H1 research surface.

The evidence does **not** validate FRANK's exact packet score, ancestry cap, ranking phases, or final context allocation policy.

## 3. Build performed

Rebased on the newest ActiveAssembly v1.1 identity/collision semantics and implemented reference schema `frank.active-assembly.v1.2`.

Changes:

1. Added deterministic positive integer `AssemblyPacket.context_cost`.
2. Included `context_cost` in packet identity, so the same `packet_id` cannot silently change its model-facing cost without a collision.
3. Added optional hard `max_context_cost` to `compile_active_assembly`.
4. Kept `max_context_cost=None` backward-compatible with the existing count-only mode.
5. Made the context budget non-bypassable even by `CONFLICT_VISIBILITY` representatives.
6. Preserved re-expansion references for packets excluded by context cost.
7. Added explicit `context_cost_used`, `context_cost_remaining`, and categorized `omitted_reasons` receipts.
8. Preserved v1.1 packet fingerprinting, exact-duplicate idempotency, packet-id collision fail-closed semantics, ancestry/conflict roles and the rule that ActiveAssembly never mints execution authority.

This is a resource-boundary improvement. It is not a claim that the selector is now optimal.

## 4. Executed tests

Hosted Linux regression command:

`python -m unittest research_entity.harness.tests.test_active_assembly research_entity.harness.tests.test_active_assembly_context_budget -v`

Result available in this worker environment: **16 passed, 0 failed**.

New tests cover:

- hard model-facing context budget;
- default count-only compatibility;
- fail-closed invalid packet costs;
- fail-closed invalid context budget;
- re-expansion after context exclusion;
- conflict visibility obeying the same hard context budget;
- permutation-invariant assembly identity under the budget;
- context cost participating in packet-id collision identity.

Evidence label: `H1 / HOSTED_LINUX_REFERENCE`. It is not `LIVE_PC_FRANK` and not target Ubuntu hardware evidence.

## 5. Adversarial 25,000-episode benchmark

A deterministic synthetic benchmark was built rather than testing only favorable echo fixtures.

Parameters:

- seed `20260809`;
- 5 scenarios;
- 5,000 episodes/scenario;
- 25,000 total episodes;
- model-facing cost budget `18` abstract units;
- max items `6`;
- comparison methods: budgeted Top-k, MMR-like redundancy-aware baseline, budgeted ActiveAssembly, previous count-only ActiveAssembly.

Scenarios deliberately include both favorable and hostile cases:

- `clean`;
- `echo_conflict`;
- `misinfo_swarm`;
- `concentrated_family` — several distinct necessary facts legitimately share one ancestry family;
- `variable_cost` — one expensive high-score packet competes with multiple cheaper useful facts.

### Resource result

The old count-only Assembly exceeded the matched cost budget in:

- clean: `94.72%`;
- concentrated-family: `51.74%`;
- echo/conflict: `90.22%`;
- misinformation swarm: `42.10%`;
- variable-cost: `100%`.

The new budgeted Assembly respected the hard budget by construction. This supports the narrow implementation claim that item count alone is an inadequate resource invariant in these fixtures.

### Selection result — deliberately mixed

The benchmark did **not** validate the whole ActiveAssembly selection heuristic.

Budgeted ActiveAssembly utility:

- clean `0.99993`;
- echo/conflict `0.87820`;
- misinformation swarm `0.99127`;
- concentrated-family `0.52740`;
- variable-cost `0.59100`.

Budgeted MMR-like utility:

- clean `0.98760`;
- echo/conflict `0.91238`;
- misinformation swarm `0.59400`;
- concentrated-family `0.99320`;
- variable-cost `0.61407`.

Budgeted Top-k utility:

- clean `0.99993`;
- echo/conflict `0.33685`;
- misinformation swarm `0.03095`;
- concentrated-family `0.99853`;
- variable-cost `0.59100`.

These are synthetic mechanism metrics, not language-model answer scores.

## 6. Negative result that changes the architecture hypothesis

The important falsification is `concentrated_family`.

FRANK's current **global ancestry cap** is useful against echo amplification, but it can suppress distinct task-critical facts merely because they come from the same provenance family. In the constructed counterexample, ActiveAssembly utility fell to `0.5274`, while budgeted Top-k reached `0.99853` and MMR-like selection `0.9932`.

Therefore:

`ancestry diversity != universal evidence diversity`.

Ancestry should remain provenance/anti-echo information, but the final selector should not yet freeze a global ancestry quota as target semantics. Candidate replacements include claim-/semantic-local redundancy penalties, set-level marginal gain, or another deterministic mechanism that preserves independent counterevidence without suppressing legitimate multi-fact sources.

This run intentionally **did not patch around the benchmark** with an ad-hoc claim-local rule and then call the problem solved. That would optimize to a synthetic fixture before frozen H1/target-4B evidence exists.

## 7. Second negative result: value per context cost

In `variable_cost`, the current score-first Assembly reaches `0.591`, while the simple MMR-like budgeted comparator reaches `0.61407`.

This suggests another open mechanism hypothesis:

`raw packet_score` is insufficient when packet costs vary materially.

The eventual policy may need a marginal future-utility-per-cost term or a set-level optimization. But the research evidence also warns against assuming one universal budget controller is optimal; the next step is matched frozen H1 traces and later target-4B/user outcome evidence, not another unvalidated heuristic constant.

## 8. Architecture delta

Accepted now:

`bounded ActiveAssembly` means bounded by **both semantic item constraints and an explicit model-facing context-cost envelope** when a target cost estimate is available.

Not accepted now:

- global ancestry cap as final target selector semantics;
- MMR as the final selector;
- any particular embedding or lambda;
- synthetic utility as a proxy for Andreas outcomes;
- current Qwen3.5-4B as final target model;
- learned recurrence halting as superior to fixed/post-hoc baselines;
- any promotion of H1 or BASE.

Architecture fidelity assessment:

`IMPROVED_RESOURCE_BOUNDARY_WITH_SELECTION_QUALITY_STILL_OPEN`.

## 9. Hypotheses / counterhypotheses

### H-FRANK-CB-001

A hard model-facing context-cost budget is required in addition to packet count.

Current state: synthetic mechanism + general external support; target open.

Falsifier: matched target-tokenizer H1/4B traces show count-only never violates the preregistered resource envelope, or cost estimation causes more correctness/recovery harm than it prevents.

### H-FRANK-CB-002

Global ancestry caps are too coarse for final context selection.

Current state: synthetic counterexample support; open.

Counterhypothesis: real FRANK traces are dominated by echo/re-entry redundancy, and the simplicity/robustness of a global cap outweighs the synthetic distinct-fact loss.

### H-FRANK-CB-003

Final selection should optimize marginal future utility under context/KV/latency cost rather than raw packet score alone.

Current state: external + synthetic support; open.

Counterhypothesis: a simple deterministic score-first selector matches more complex set-level methods on real traces at lower implementation/replay risk.

## 10. Exact next discriminator

Do not mutate the selector again from these synthetic fixtures alone.

Next high-information experiment:

1. bind `context_cost` to the actual candidate 4B tokenizer / serialized Assembly form;
2. freeze real H1 episodes with provenance, conflicts and re-expansion targets;
3. replay identical candidate pools through:
   - score-first Top-k;
   - current ActiveAssembly;
   - MMR-like redundancy baseline;
   - set-level redundancy-aware selector;
   - optional adaptive budget allocation;
4. hold model/context budget constant;
5. measure verified future task outcome, correction recurrence, conflict recall, provenance fidelity, omission severity, re-expansion success, tokens/KV, latency, update amplification and stale-state recovery;
6. only then alter final ancestry/redundancy semantics.

P0 H-WP-02 target-host three-ledger differential also remains open and should not be erased by this hosted P2 work.

## 11. Non-claims

- No Andreas target-host execution occurred.
- No target 4B was benchmarked.
- No target tokenizer cost was measured.
- No BASE/H1/H2/H3 gate was promoted.
- The misinformation fixture is not proof of real misinformation robustness.
- ActiveAssembly/GWT/recurrence is not evidence of phenomenal consciousness.
- Cognitive selection never confers external effect authority.
