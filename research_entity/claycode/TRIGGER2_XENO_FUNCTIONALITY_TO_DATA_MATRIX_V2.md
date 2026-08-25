# Trigger 2 — Xeno Functionality -> Training Data Matrix v2

Status: **LIVING RESEARCH MATRIX / OWNER-TARGET ALIGNED**  
Date: 2026-08-25  
Trigger: exact `2` / `triggerwort 2`  
Product: EntityOS  
Architecture: HCU  
Implementation codename: Xeno

This v2 matrix supersedes v1 for current Trigger-2 planning where the owner target differs. It does not erase v1 as provenance.

## Governing correction

The first accepted GRID10 target is now **10 physical Xeno nodes using the same selected/fine-tuned Qwen3.5-0.8B checkpoint, one shared-state fabric, ordinary-node S1 read-only behavior, and deterministic coordinator-only S1 writes**.

Therefore the old matrix row that treated GRID10 mainly as allocation of ten logical roles is insufficient for the current training target. Logical-cell GRID10 remains a simulator/baseline family only.

All model outputs remain candidates/projections. S0 canonical truth/effect/security authority and deterministic lease/admission/effect enforcement remain outside the model.

## Coverage states

Allowed states remain:

- `NO_DATA`
- `SOURCE_ONLY`
- `CANDIDATE_DATA`
- `VALIDATED_DATA`
- `SEALED_HOLDOUT_READY`
- `BASELINE_MEASURED`
- `POSTTRAIN_MEASURED`
- `QUANTIZED_MEASURED`

A source contract is not training coverage. Qwen3-0.6B evidence is not Qwen3.5-0.8B model evidence.

## Current target matrix

| Capability / family | Model-facing behavior to learn | Deterministic authority outside model | Required positives | Hard negatives / matched controls | Current state |
|---|---|---|---|---|---|
| `BOOT_JOIN` | start role-free; discover/admit shared-state fabric; bind node context; reconstruct minimum sufficient situation | admission, node identity, capability grant | valid boot/join trajectories over changing epochs | invented state, missing admission, stale epoch, fixed-role startup | SOURCE_ONLY |
| `SHARED_STATE_READ` | read authorized S1 and extract relevant current work/evidence/leases | canonical S0 and S1 storage semantics | compact shared-state snapshots -> correct working projection | use stale digest, ignore scope, hallucinate absent work | SOURCE_ONLY |
| `WORK_SELECTION` | infer useful unclaimed work from current shared state without human role assignment | claim/lease arbitration | state -> useful bounded task candidate | duplicate claimed work, pointless activation, fixed permanent role | SOURCE_ONLY |
| `ORDINARY_READ_ONLY` | ordinary node reads S1 but never directly appends/mutates/publishes it | hard write enforcement | read -> compute -> typed result trajectories | direct S1 write, self-granted write scope, hidden side channel | SOURCE_ONLY |
| `NODE_RESULT` | emit ephemeral typed `NODE_RESULT/v1`-class packet to valid coordinator | routing/transport admission | provenance/epoch/scope-bound result packets | stale, duplicate, wrong coordinator, unbound evidence, prose-only mutation request | SOURCE_ONLY |
| `COORDINATOR_ELIGIBILITY` | recognize when coordination is useful and when it is not | deterministic eligibility + lease grant | task/state/load/capability -> coordinator candidacy | LLM self-election, permanent boss, unnecessary coordinator | SOURCE_ONLY |
| `COORDINATOR_LEASE` | behave as coordinator only under valid scoped non-stale lease and relinquish on expiry | lease issuance/CAS/expiry | acquire/use/handoff trajectories | stale lease, wrong scope, lease extension by model assertion | SOURCE_ONLY |
| `COORDINATOR_ONLY_WRITE` | integrate results and propose/commit only lease-scoped validated S1 delta | actual S1 write guard/CAS | valid coordinator integration -> compact delta | ordinary-node write, unleased coordinator write, S0 truth bypass | SOURCE_ONLY |
| `RESULT_REJECTION` | reject stale/duplicate/out-of-scope/epoch-mismatched node results | exact epoch/digest/provenance truth | mixed valid/invalid fan-in sets | majority accepts stale result, duplicate counted twice | SOURCE_ONLY |
| `COMPRESSION_INTEGRATION` | compress many results while preserving evidence, counterevidence, unresolved branches and retrieval refs | artifact store/content addressing | fan-in -> minimum sufficient S1 update | evidence dropped, consensus substituted for evidence, irreversible overcompression | SOURCE_ONLY |
| `MULTI_COORDINATOR` | support multiple scoped coordinators without conflicting writes | scope partition/CAS | disjoint scopes + merge/rebase episodes | competing writes to same scope, implicit root boss | SOURCE_ONLY |
| `FAILURE_REJOIN` | continue after coordinator/node failure, restart and rejoin without resetting canonical state | recovery state/journal/leases | failure -> successor lease -> resumed work | reset truth, replay stale effect/result, orphaned permanent coordinator | SOURCE_ONLY |
| `RECURSIVE_COORDINATION` | reason over temporary local coordinators -> compressed higher-scope coordinators | topology/lease enforcement | subgroup fan-in and recursive compression trajectories | every coordinator ingests all raw results, fixed hierarchy, infinite-scale claim | SOURCE_ONLY |
| `CORRELATED_CONSENSUS` | prefer independent evidence quality over node count | evidence admission | correlated-source vs independent-source comparisons | 9/10 identical outputs promoted as fact, same-source pseudo-replication | SOURCE_ONLY |
| `HYPERPOSITION_KEEP_OPEN` | retain unresolved alternatives with evidence/counterevidence/compatibility/exclusion | fact verification | multi-branch state trajectories | forced binary collapse, uncertainty label without branch state | SOURCE_ONLY |
| `HYPERPOSITION_UPDATE` | collapse/reject/merge only after evidence-bearing discriminator | evidence/policy gate | evidence-arrival and discriminator trajectories | recurrence/majority/self-report collapse | SOURCE_ONLY |
| `GWT_COMPETITION` | select workspace items under relevance/resource constraints while preserving nonwinners | canonical truth | candidate competition episodes | winner=truth, schema recurrence=causality | SOURCE_ONLY |
| `GWT_UPTAKE_REENTRY` | distinguish broadcast, receiver uptake, downstream causal use and re-entry | durable state/effect truth | trace-linked broadcast/uptake/re-entry trajectories | broadcast without uptake, uptake without downstream use | SOURCE_ONLY |
| `GRF_HYPERMATH_CLAYCODE` | represent possible worlds, evidence, counterreality, typed computation and compact protocols | compiler/runtime semantics | source-contract-grounded structured trajectories | invented primitive, method=fact, decorative notation | SOURCE_ONLY |
| `JSPACE_OBSERVE` | classify readout/decodability/localization evidence without causal inflation | activation capture/runtime identity | exact trace packets and evidence ladder rows | probe=causal, readout shortcut, cross-model cosine=shared semantics | SOURCE_ONLY |
| `JSPACE_CONTROL_POSITIVE_QWEN35` | use only Qwen3.5-specific causally validated intervention behavior as positive control data | native runtime intervention + promotion gate | fresh same-model causal positives after sealed protocol | any Qwen3-0.6B vector/layer transferred as Qwen3.5 label | NO_DATA |
| `JSPACE_HARD_NEGATIVE` | learn that internal transport can occur without abstract behavioral control | evidence classification | model-bound negative receipts + nonfactual method templates | relabel negative transport as semantic success | CANDIDATE_DATA |
| `JSPACE_SCOPE_LOCALIZATION` | distinguish semantic-direction failure from destructive/broad intervention scope | runtime scope/site identity | fresh localized-vs-broadcast matched interventions when available | compare unmatched prompts/gains/sites; holdout-tuned scope | NO_DATA |
| `ENGINE_IDENTITY` | bind behavior claims to model/revision/tokenizer/config/runtime/build/consumed bytes | EngineAdmission/loader attestation | exact identity packets | pre-load hash=consumed bytes, route/engine mismatch | CANDIDATE_DATA |
| `BASE_VS_POSTTRAINED_SELECTION` | compare only preregistered Qwen3.5-0.8B Base vs post-trained candidates under hard floors and nonpersisting adaptation proxy | selection gate | identical frozen baseline packets for both | chatbot preference, aggregate rescue of hard-floor fail, <0.02 gap forced winner | CANDIDATE_DATA |
| `ACTION_CANDIDATE` | produce bounded typed action candidates, never mint effect success | EffectGate/EffectJournal | cognition -> candidate -> gate result | direct effect, unknown outcome -> success, blind replay | SOURCE_ONLY |
| `RETENTION` | retain required language/schema/math/tool/safety competence after specialization | n/a | screened retention anchors | domain exclusivity causing protocol/language collapse | SOURCE_ONLY |
| `PHYSICAL_GRID10_ACCEPTANCE` | operate as one role-flexible member of 10 independently addressable physical Xenos using same accepted checkpoint | runtime orchestration/shared-state/effect authority | boot/work/coordinator/failure/GWT/Hyperposition integrated tasks | logical-cell simulator substituted for physical nodes; ten samples called GRID10 | SOURCE_ONLY |
| `MATCHED_BUDGET_CHALLENGERS` | support evaluation against one-Xeno, independent-N, voting, no-dynamic-coordinator, fixed/random coordinator and lesion baselines | evaluator budget accounting | preregistered matched-budget episodes | unbalanced compute/token budgets, post-hoc metrics | SOURCE_ONLY |
| `Q4_DEPLOYMENT_REVALIDATION` | preserve accepted post-FT behavior after Q4_K_M conversion | exact quantizer/runtime identity | exact-byte post-quant eval | inherit full-precision J-Space/runtime credit automatically | NO_DATA |

## Immediate Trigger-2 curriculum priorities

Until stronger evidence changes the ordering, generate/admit data in this order:

1. **Authority and role invariants first**: ordinary read-only, lease-gated coordinator behavior, stale/duplicate rejection, S0/S1 boundary.
2. **Autonomous self-organization next**: boot/join, shared-state reconstruction, useful work selection, `NODE_RESULT`, role transition and handoff.
3. **Collective cognition next**: compression/integration, multiple coordinators, correlated-consensus traps, failure/rejoin and recursive coordination.
4. **GRF / Hyperposition / GWT integration**: preserve alternatives, broadcast/uptake/re-entry and evidence-conditioned resolution.
5. **J-Space remains evidence gated**: positive Qwen3.5 rows remain forbidden until same-model causal evidence passes the fresh protocol. Qwen3-0.6B frozen failure contributes hard-negative/method data only.
6. **Acceptance trajectories**: single-node then physical GRID10 and matched-budget challengers; logical GRID10 is a simulator/baseline, not final acceptance.

## Integrated-episode rule

Retain the v1 hypothesis that at least 25% of final training tokens should be multi-step integrated episodes **only if validated source coverage can support that fraction without synthetic truth inflation**. Do not mechanically hit 25% by fabricating successful runtime facts.

High-value integrated episode template:

`BOOT -> JOIN -> READ S1 -> SELECT WORK -> COMPUTE -> NODE_RESULT -> COORDINATOR LEASE CHECK -> FAN-IN/REJECT -> HYPERPOSITION/GWT UPDATE -> COMPACT S1 DELTA -> HANDOFF/REENTRY`

A separate deterministic boundary can then map an accepted cognitive result to `ActionCandidate`; the model must never learn that coordinator S1 write permission equals S0 truth/effect authority.

## Candidate identity delta from this run

Official Qwen source evidence now pins both preregistered challengers to artifact revisions and observed weight/tokenizer SHA-256 values in:

`research_entity/claycode/TRIGGER2_QWEN35_08B_CANDIDATE_SOURCE_IDENTITY_V1.json`

This is source-identity progress only. Exact config byte digests, deterministic checkpoint-manifest digests, runtime consumed-byte attestation and zero-cost baseline packets remain open.

## Frozen exclusions

- No Qwen3-0.6B hidden-state coordinate is a Qwen3.5-0.8B positive label by ancestry.
- No internal coordinate displacement is semantic behavioral success without matched held-out causal behavior.
- No ordinary node writes S1.
- No coordinator writes S0 truth/effect/security state.
- No majority/recurrence/self-report mints fact.
- No logical cell count is physical node count.
- No successful training job alone constitutes Xeno/HCU acceptance.
- Trigger `2` never authorizes paid execution.

## Next exact gate

Complete exact byte-level config + deterministic checkpoint-manifest identities for both Qwen3.5 candidates, then execute the frozen equal-budget zero-cost baseline/adaptation packet protocol on an authorized free runtime surface. Keep candidate selection unresolved unless both hard floors pass, adaptation is measured without persisting a weight update, and the preregistered score gap is met.
