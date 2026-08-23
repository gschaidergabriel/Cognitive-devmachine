# HCU architecture v0.1 — modular ~0.8B Hyperposition compute fabric

Status: `SOURCE_ARCHITECTURE_CANDIDATE`
Runtime credit: `0`
Host target: owner-supplied KVM 4 deployment profile

## 1. Purpose

The Hyperposition Computational Unit (HCU) turns a small CPU VPS into a modular inference fabric made from many approximately-0.8B cognition tiles. The design goal is not to pretend that 4 CPU cores behave like a GPU. The goal is to make a measured, schedulable grid whose tiles can stay resident, time-share decoding, preserve alternative hypotheses and contribute to one persistent Mini Entity world-model loop.

## 2. Core topology

```text
                     FREE LLM / local model candidate feeds
                                      |
                                      v
                            provenance + ingress gate
                                      |
                                      v
+---------------------------------------------------------------------+
|                    HCU packet / tile fabric                          |
|                                                                     |
|  [ingest] [world] [causal] [goals] [planner] [cf-A] [cf-B]         |
|  [Zero twin] [critic] [uncertainty] [verifier] [synthesis] ...      |
|                                                                     |
|       resident pool <-> active decode slots <-> cold tile pool       |
+----------------------------+----------------------------------------+
                             |
                             v
                 Hyperposition alternatives / evidence
                             |
                             v
                 Unified J-Space / GWT selection
                             |
                             v
                    canonical validation boundary
                             |
                             v
                        MiniUnifiedDB
                             |
                             v
                EntityOS/Mini Entity effect authority
```

The arrows are typed causal interfaces, not permission inheritance.

## 3. Physical versus logical tiles

A **physical tile** is an admitted approximately-0.8B model runtime instance with exact model/tokenizer/runtime identity.

A **logical tile** is a role + state + queue + causal identity. Multiple logical tiles may use the same exact base model bytes if the runtime supports read-only shared/mmap pages. Shared weights do not imply shared mutable tile state.

The HCU may therefore expose more logical modules than simultaneously active physical decoders. That is the preferred way to scale a 16 GB / 4-core VPS without duplicating identical weights unnecessarily.

Distinct checkpoints remain allowed, but their measured RSS and storage cost must be charged independently.

## 4. Initial logical roles

The first topology defines these roles:

1. `feed_ingest` — normalize free-model/local-model candidate packets and provenance;
2. `world_projection` — read bounded canonical world state and build derived working projection;
3. `causal_update` — propose causal edge/state-transition candidates;
4. `goal_proposer` — propose bounded dynamic goals under owner/system constraints;
5. `plan_generator` — produce candidate action/observation plans;
6. `counterfactual_a` — simulate one alternative future branch;
7. `counterfactual_b` — simulate an independent alternative branch;
8. `zero_twin` — simulate bounded Zero cognitive/decision state for diagnosis;
9. `adversarial_critic` — seek failure modes and counterhypotheses;
10. `uncertainty_calibrator` — estimate/calibrate uncertainty and horizon effects;
11. `evidence_verifier` — check provenance and validation obligations;
12. `synthesis` — produce a GWT/Hyperposition coalition candidate.

These are assignments, not twelve required permanently distinct weight sets.

## 5. Scheduling

The scheduler has three resource pools.

### Resident pool

Tiles whose model pages/runtime are kept ready in memory. Admission is based on measured peak RSS plus active-context reserve.

### Active decode slots

The subset currently decoding. CPU scheduling is the hard limiter on the KVM 4 profile. The initial planning profile assumes two CPU threads per active tile and therefore only two simultaneous active decoders on four cores. This is a provisional assumption, not a benchmark result.

### Cold pool

Exact model/checkpoint variants stored on disk and loaded/evicted according to measured utility and pressure. Cold capacity is informational only until model artifact sizes are measured.

The scheduler must never overcommit memory merely to maximize nominal tile count. On uncertainty it reduces active/resident slots and preserves service/recovery headroom.

## 6. Packet contract

Tile-to-tile communication must be typed and attributable. A packet should include at least:

```json
{
  "schema": "HCU_PACKET/v1",
  "packet_id": "...",
  "causal_id": "...",
  "episode_id": "...",
  "generation": 0,
  "source_tile": "...",
  "target_role": "...",
  "epistemic_class": "UNTRUSTED_CANDIDATE",
  "payload_digest": "sha256:...",
  "provenance": {},
  "payload": {}
}
```

Mutable shared scratch memory is not a substitute for packet provenance.

## 7. Persistent world-model loop

The HCU may run a long-lived loop:

```text
canonical observation
-> bounded world projection
-> causal update candidates
-> goal candidates
-> competing plans
-> counterfactual branches
-> Zero-twin predictions
-> critics/calibration
-> Hyperposition set
-> GWT/selection candidate
-> validation
-> canonical write or reject/unknown
-> next observation
```

The durable truth is not the simulator. Canonical evidence remains in MiniUnifiedDB. The HCU's world graph/cache can be rebuilt from canonical state plus admitted receipts.

## 8. Time model

Past, present and future must remain typed:

- `OBSERVED_PAST` — canonical past evidence/state;
- `CURRENT` — admitted current state;
- `SIMULATED_FUTURE` — generated branch only;
- `COUNTERFACTUAL` — explicitly non-actual branch;
- `UNKNOWN` — insufficient evidence.

A future branch may carry a confidence estimate, but the estimate is not factual truth. Horizon distance can be one prior feature; calibration must use actual subsequent outcomes and preserve model/provider/version identity.

## 9. Dynamic goals

HCU may propose goals but may not silently grant itself new authority.

Every autonomous goal proposal must be bound to:

- owner/system constraints;
- causal reason/evidence;
- scope;
- expiry/review condition;
- expected utility or information gain;
- forbidden effects/capabilities;
- validation criterion.

A goal proposal is not an effect authorization.

## 10. Zero cognitive twin

`zero_twin` is a model of Zero, not Zero itself.

It may predict likely reasoning/action states and propose improvements. Its outputs remain hypotheses until discriminated against real observed Zero behavior. It must not write identity state, rewrite policy, or self-apply modifications.

## 11. Free LLM/token feed

External free-model output enters only through the existing Mini Entity adaptive inference/provider fabric.

Required treatment:

```text
provider/model response
-> provenance packet
-> candidate-only epistemic class
-> dedup/conflict checks
-> optional multi-model comparison
-> Hyperposition/hypothesis/world-model input
-> evidence validator
-> canonical write only if independently admitted
```

Model consensus alone is not verification.

## 12. Capacity strategy for KVM 4

The owner host has 16 GB RAM and 4 CPU cores. The v0 planning profile reserves system/DB/orchestrator headroom and uses provisional unverified per-tile footprints to choose a safe starting resident/active count.

`capacity_planner.py` intentionally computes the count instead of hard-coding it. With the current *planning* values in `KVM4_PROFILE.json`, the expected output is approximately:

- resident tiles: 11;
- simultaneously active decode tiles: 2;
- cold distinct ~0.6 GB artifacts on remaining disk: up to 266.

These numbers are **not runtime measurements**. Exact admitted benchmarking may raise or lower them substantially. Shared read-only model pages may allow many logical roles without one full duplicate weight allocation per role.

## 13. Failure behavior

Fail closed / degrade safely on:

- memory pressure or OOM risk;
- stale generation;
- unbound model/tokenizer/runtime identity;
- malformed packet/provenance;
- provider billing ambiguity under `FREE_ONLY`;
- missing canonical evidence;
- conflicting world-model branches;
- uncertain external-effect outcome.

Degradation order should prefer fewer active tiles, then fewer resident tiles, then narrower simulation depth. It must not bypass canonical state/effect gates.

## 14. Acceptance path

1. source/contract validation;
2. exact tile artifact binding;
3. single-tile memory/throughput measurement;
4. 2/4/... resident scaling;
5. active-slot scheduling measurement;
6. shared-page behavior measurement if used;
7. packet/provenance/replay/generation tests;
8. world-model persistence/rebuild tests;
9. free-feed candidate-only tests;
10. Zero-twin falsification tests;
11. restart/recovery;
12. explicit deployment authorization for the VPS.

Until that sequence is executed on an admitted surface, HCU remains source architecture plus planning estimates.
