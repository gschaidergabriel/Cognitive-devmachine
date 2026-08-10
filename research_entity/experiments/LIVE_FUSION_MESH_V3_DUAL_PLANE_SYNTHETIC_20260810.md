# Live Fusion Mesh V3 Dual-Plane — Synthetic Research Receipt

Date: 2026-08-10  
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol  
Evidence class: **SIMULATION_ONLY**  
Promotion authority: **NONE**  
Subject: stronger live fusion through dense low-cost control-plane beacons plus sparse targeted full-payload routing.

## Hypothesis

A dual-plane mesh can improve relevant-branch recall and shorten silent stale windows without reverting to expensive full-payload broadcast:

1. every material KnowledgeDelta emits one compact provenance-bound ImpactBeacon to all registered branches;
2. branches independently evaluate relevance against their freshest raw/current work and dependency surfaces and return an impact acknowledgement;
3. full payload remains dependency-/semantic-targeted and is additionally pulled by branches declaring AFFECTED;
4. UNKNOWN/STALE acknowledgements trigger bounded repair rather than being silently treated as current.

## Strongest counterhypothesis

If ClayGraph, UnifiedDB/raw-work projections and branch-local checks share the same missing dependency ancestry, the second plane adds control traffic but cannot recover the same correlated blind spot. In that regime V3 may collapse to V2 recall and should not be promoted.

## Fresh external evidence used

Primary/current sources retrieved 2026-08-10:

- Picsou: Enabling Replicated State Machines to Communicate Efficiently, OSDI 2025. Cross-Cluster Consistent Broadcast uses precise quorum acknowledgements and targeted resend semantics; reported up to 24x better performance than prior approaches in evaluated settings. https://www.usenix.org/conference/osdi25/presentation/frank
- Enzyme: Incremental View Maintenance for Data Engineering, arXiv:2603.27775 (2026). Production IVM uses cost-based planning to select refresh strategies rather than one fixed incrementalization policy. https://arxiv.org/abs/2603.27775
- Deriving Semantic Checkers from Tests to Detect Silent Failures in Production Distributed Systems, OSDI 2025. Demonstrates the importance of semantic runtime checking for silent distributed-system failures rather than treating transport/runtime success as semantic correctness. https://www.usenix.org/conference/osdi25/presentation/lou

These sources motivate architecture/testing ideas only; they do not directly validate Clay/Frank behavior.

## Matched synthetic setup

Script: `research_entity/experiments/live_fusion_mesh_v3_dual_plane_sim.py`

- seed: `20260810`
- deltas: `5000`
- branches: `9`
- central dependency-edge missing rate: `0.08`
- branch-local shadow missing rate: `0.08`
- beacon relative network cost unit: `0.03` per branch-beacon vs `1.0` full-payload unit
- methods: broadcast, tag-only, V2 dependency-aware, V3 dual-plane
- normal run: central and local missing-edge processes have independent ancestry

The V3 simulator is an extension/reimplementation of the V2 synthetic model. Its RNG stream is not claimed to be byte-identical to the earlier V2 script; comparisons below are matched inside this V3 run.

## Normal matched result

| method | micro recall | perfect-event recall | full payloads / delta | beacons / delta | weighted network cost / delta | missed required deliveries |
|---|---:|---:|---:|---:|---:|---:|
| broadcast | 1.000000 | 1.000000 | 9.0000 | 0.0000 | 9.0000 | 0 |
| tag-only | 0.590077 | 0.620600 | 1.7530 | 0.0000 | 1.7530 | 6089 |
| V2 dependency-aware | 0.963040 | 0.924600 | 2.8610 | 0.0000 | 2.8610 | 549 |
| V3 dual-plane | **0.996230** | **0.988800** | 2.9596 | 7.2036 | **3.175708** | **56** |

Derived synthetic deltas:

- V3 reduces missed required deliveries from 549 to 56 versus matched V2: about **89.8% fewer misses** in this independent-shadow model.
- V3 weighted network cost is about **11.0% higher than V2** under the declared 0.03 beacon-cost assumption.
- V3 weighted network cost remains about **64.7% lower than full broadcast** under the same synthetic cost model.
- The result supports V3 as a **research candidate**, not an architecture promotion.

## Exactly one out-of-the-box experiment

Name: `fully_correlated_projection_blind_spot`

Intervention: force the missing dependency edges of central and branch-local routing projections to be fully correlated. This deliberately attacks the hidden assumption that a second routing surface is informative simply because it is separately queried.

Result under the simulator:

- V2 micro recall: `0.976203`
- V3 micro recall: `0.976203`
- V2 missed required deliveries: `354`
- V3 missed required deliveries: `354`
- V3 still pays the beacon overhead.

Interpretation: **V3 provides no recall benefit when the two relevance checks share the same blind-spot ancestry.** Therefore multi-source routing checks must preserve provenance diversity; `ClayGraph + a second projection derived from the same stale source` is not an independent safety check.

This is a useful negative result and a promotion blocker until real-repo replay measures projection ancestry and correlated-failure behavior.

## Architecture delta

Candidate added:

`research_entity/global/CLAY_LIVE_FUSION_MESH_V3_DUAL_PLANE_CANDIDATE.clay`

Key delta:

`dense compact control plane -> branch-local impact acknowledgement -> sparse full-payload data plane -> ack closure + anti-entropy repair`

Important invariants:

- ack count does not increase evidence strength;
- AFFECTED/NOT_AFFECTED is routing state, not truth;
- delivery != reconstruction != use != effect != causal credit;
- correlated projection blindness remains explicit and measurable;
- Frank gains no self-Harness authority;
- candidate remains rollbackable to V2/current owner-fixed mesh.

## Required real next test

Run current repository work/branch/claim events through matched broadcast/tag-only/V2/V3 replay and inject:

1. missing ClayGraph dependency edge;
2. stale projection epoch;
3. correlated missing edge across ClayGraph + secondary projection;
4. duplicate delta;
5. dropped beacon/ack;
6. out-of-order causal predecessor;
7. crash/restart with open AckClosure.

Capture raw latency/resource/network rows, provenance hashes, relevant-branch recall pre/post repair, permanent misses, false AFFECTED/NOT_AFFECTED acknowledgements and recovery correctness.

Verdict: `SUPPORTED_AS_RESEARCH_CANDIDATE_NOT_PROMOTED`.
