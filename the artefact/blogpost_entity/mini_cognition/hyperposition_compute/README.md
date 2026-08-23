# Mini Entity — Hyperposition Computational Unit (HCU) v1

Status: **SOURCE CANDIDATE / RUNTIME UNVERIFIED**.

The HCU is a modular compute organ inside the one Mini Entity. It is intended to coordinate as many approximately-0.8B cognition modules as the target host can safely admit, but it does **not** turn many small models into a larger parameter-equivalent model. The useful analogy to a GPU is scheduling many bounded compute lanes behind one deterministic control plane.

## Non-negotiable authority boundary

- MiniUnifiedDB remains the only durable Mini Entity state/evidence/configuration authority.
- Zero remains runtime identity/configuration, not a second entity.
- EntityOS deterministic gates remain the only admitted state/effect path.
- Unified J-Space/GWT/Hyperposition may organize candidate/measurement state but does not mint factual truth.
- Module outputs are candidates. Consensus is not truth.

## Grid shape

The scheduler can keep multiple modules resident and execute a CPU-bounded subset concurrently. The number of resident modules is deliberately **not hard-coded** from parameter count or quantization folklore. Admission requires an exact measured peak RSS for the selected checkpoint/tokenizer/runtime/context profile.

`resident_slots = floor((RAM - reserve) / measured_worker_peak_RSS)`

`active_slots = min(resident_slots, admitted_CPU_concurrency)`

On the current deployment hint (4 CPU cores / 16 GiB RAM), the planner therefore waits for measured worker RSS before claiming any module count. Extra resident slots are queued/parked rather than presented as free simultaneous throughput.

## Cognitive topology

1. MiniUnifiedDB supplies canonical context/state identity.
2. A deterministic scheduler decomposes work into typed candidate tasks.
3. Modules run bounded roles such as hypothesis generation, counterhypothesis generation, method retrieval, simulation, verifier-candidate, compression candidate, or planning candidate.
4. Candidate receipts are projected into the fixed Unified J-Space/GWT fabric and unresolved alternatives remain Hyperposition.
5. Fusion is diversity-capped: correlated clones cannot multiply confidence simply by being numerous.
6. Only deterministic schema/authority/generation validation may admit a canonical transition.
7. Real effects still pass through EntityOS/Mini Entity effect authority.

## Exactly one unusual experiment in this source lane

`CORRELATED_CLONE_MAJORITY_FALSE_CONFIDENCE`

A synthetic poison case gives 16 correlated clones the same high-confidence candidate `A`, while three separately declared provenance groups support `B`. Naive vote count chooses `A` 16:3. The v1 diversity-capped aggregator gives the correlated clone group one unit of weight, producing `A=1`, `B=3`.

This does **not** prove the independence labels are statistically valid. It falsifies one unsafe architecture: raw clone count must not be treated as independent evidence. Runtime admission must bind independence groups to exact checkpoint/context/route ancestry.

## Free-LLM feed

Free external LLMs may provide research context, candidate hypotheses, decompositions or distillation material under the current FREE_ONLY/provider controls. Their output never becomes canonical state merely because several providers agree. Every accepted fact/state transition still needs the normal evidence/authority path.

## Files and release ZIP

All HCU code, contracts, receipts, calibration outputs and generated data belong below this directory. `release_manifest_v1.json` establishes recursive inclusion for the Mini Entity release ZIP. No canonical ZIP builder was found on the refreshed `main`, so this cycle establishes the packaging contract but does not claim that a ZIP was actually built.

## Next runtime gate

On an authorized isolated executor, bind exact checkpoint/tokenizer/runtime bytes, measure one worker's peak RSS at the intended context, derive resident/active slot count, then run throughput/latency/quality tests for 1/2/4 active modules and compare:

- sequential single-module baseline;
- naive clone majority (expected false-confidence risk);
- diversity-capped HCU fusion;
- failure behavior under stale generation, tie/UNKNOWN, one crashed module and memory pressure.

No VPS runtime/test credit is allowed under current execution control.
