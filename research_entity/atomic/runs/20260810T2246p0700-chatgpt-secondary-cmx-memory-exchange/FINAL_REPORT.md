# ATOMIC FINAL REPORT — CMX-001 / Counterfactual Memory Exchange

## Decision
**NO ARCHITECTURE PROMOTION. `ATOMIC-CMX-001` is `TESTED_PROXY_REFUTED_AS_DEFINED`.**

## Why this problem was selected
The current live mesh had already moved strongly on single-spawn, same-session execution, token ingress, recovery, effect fencing, ClayCode WP04 and a concurrent translator ATOMIC run. The unified workspace still leaves F-V01-11 Memory/Reward/Goals open, while the loop-core contract explicitly requires outcome-gated causal credit, slow reward/homeostatic updates and memory re-entry. This invocation therefore selected long-horizon procedural memory under drift, context budget and self-echo pressure, while excluding factual/identity/authority memory from utility competition.

## Candidate
CMX treated procedural memory as a bounded exchange. Retrieved memories pay a small context rent. After a verified outcome, a memory may earn or lose capital from the marginal utility of the actual decision versus a leave-one-out shadow decision without that memory. Repetition without verified outcome cannot create positive credit. Capital can influence procedural retrieval only; it can never become truth, SELF, user intent or effect authority.

## External collision
Broad novelty collapsed. Expected-value replay priority, context reinstatement, conflict-aware long-term memory, utility-driven forgetting, net-value-per-byte curation, cost-sensitive routing and reward-trained memory updates are all established or current research directions. Particularly close is 2026 RoMeRL, which explicitly targets a memory-reward trap caused by misleading shared utility for co-retrieved memories. CMX is therefore classified `KNOWN_NEAR_ANALOGUE`, not world-first.

## Executable discriminator
A deterministic Python reference ran a local synthetic procedural-memory benchmark with 6 seeds × 1,600 turns for each cell, two concept-drift points, 80% self-echo writes, stale-memory injection, bounded memory capacity and evidence-noise levels 0%, 2%, 5%, 10% and 15%. It compared semantic similarity, provenance weighting, reward weighting, newest-exact-verified/supersession, and CMX. A separate ablation matrix removed coupon, rent, adaptive budget or provenance. Replay/idempotency and semantic-authority controls were also executed.

## Main measurements
At clean evidence, newest-verified scored 0.8979 accuracy versus CMX 0.8362. At 10% noisy evidence, newest-verified scored 0.8316 versus CMX 0.8170. Only at 15% noise did CMX cross it, 0.8056 versus 0.7927.

That crossover does **not** rescue the mechanism. At the 10% discriminator point, full CMX scored 0.8170; removing the counterfactual coupon improved accuracy to 0.8237, and removing rent improved it to 0.8267. Therefore the two defining pieces of CMX did not receive positive causal support in the proxy.

The local selection microbenchmark was also unfavorable: newest-verified required about 5032 ns/query versus CMX about 53055 ns/query. Representative JSON metadata was 87 bytes conventional versus 175 bytes CMX. These are Python proxy costs, not VPS/end-to-end numbers.

## Recovery and authority controls
The idempotent credit ledger produced the same final digest under forward and reverse replay despite 200 duplicate receipts, while 100 stale-epoch credit events were rejected. A deliberately huge procedural capital value did not change the unit's truth or effect-authority classes. Those controls passed, but they are safety properties, not evidence that CMX is useful.

## Strongest counterhypothesis
The counterhypothesis survives: versioned newest-valid verified memory plus explicit provenance/supersession is the first baseline Frank should beat. Where outcome observations are noisy enough that newest-valid becomes unstable, denoising/aggregation and uncertainty-aware baselines must be tested before any market-like credit system. The 15% crossover is therefore a new *problem-region signal*, not a CMX victory.

## Architecture consequence for Frank v0.1
Do not implement CMX as the default F-V01-11 memory architecture. Preserve a hard semantic split: factual evidence, identity anchors and authority receipts are not utility-priced memory. For procedural/strategy memory, begin with source-bound versions, explicit supersession, bounded retrieval and verified outcome traces. Add learned/utility scoring only after a real Frank benchmark shows it beats the simple baseline. If a future utility mechanism is tried, its reward must remain downstream of verified outcome and causal-use receipts, and self-echo/repetition must not self-mint value.

## Next discriminator
Use real Frank procedural traces when the loop-core exists. Compare newest-version/supersession, provenance+recency, uncertainty-aware aggregation, and utility-weighted memory under clean and noisy outcomes, concept drift, self-generated summaries, restart/replay and bounded context. CMX should only be reopened if its counterfactual coupon and rent become *positive* ablations and produce unique defect coverage or a Pareto cost/accuracy gain.

No final/paid training was started. Whole Frank v0.1 acceptance remains unclaimed. No self.root Harness mutation authority was exercised.
