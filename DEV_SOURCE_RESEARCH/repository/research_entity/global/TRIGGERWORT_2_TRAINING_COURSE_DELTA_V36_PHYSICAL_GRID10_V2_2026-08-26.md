# Triggerwort 2 — Training/Evaluation Course Delta V36

**Date:** 2026-08-26  
**Trigger:** `triggerwort 2`  
**Persistent entity:** Clay  
**Product:** EntityOS  
**Architecture:** HCU  
**Supervisor authority:** 8.81 delta  
**Status:** CURRENT RESEARCH COURSE DELTA / NONCANONICAL / SUCCESSOR-DYNAMIC  
**Supersedes for current-course interpretation:** `research_entity/global/TRIGGERWORT_2_TRAINING_COURSE_DELTA_V35_SUPERVISOR_8_81_2026-08-26.md`  
**Observed main before write:** `2fca4005a3e9aa3732189897e38947dda27c9b45`

## 1. Re-entry result

The current runtime architecture changed materially after V35:

- `tools/xeno_physical_grid10_acceptance_v2.py` landed at `0011673f34bc55b838f52420376df6d68e40d9be`.
- It replaces the old sequential physical-GRID10 proof with ten `subprocess.Popen` children, a common release barrier, distinct PID checks, parent/child PID binding and interval-overlap checks.
- It also adds exact current `generation + state_epoch + state_digest` admission semantics and rejects stale epoch or wrong digest instead of silently treating stale evidence as current.
- A new FREE_ONLY repository-bound execution request pins exact source `0011673f34bc55b838f52420376df6d68e40d9be` and explicitly keeps whole-HCU, EntityOS, J-Space and training credit at zero.
- No exact runtime receipt for the repaired v2 source was observed in this re-entry. Therefore physical GRID10 runtime credit remains zero until such a receipt exists and is reviewed.

## 2. Architecture -> training diff

### 2.1 Physical process proof stays outside learned cognition

Ten simultaneous OS processes, PID identity, barrier overlap and SQLite read-transaction behavior are deterministic shell/runtime properties. They must not become semantic labels such as `ten processes => true`, nor fixed Xeno roles.

The model-side requirement remains topology-flexible:

`current S1 + typed runtime status -> useful local cognition -> NODE_RESULT/v1`

The same checkpoint must remain usable for variable N and must not infer authority from process count, PID, resident weight copies or decode concurrency.

### 2.2 Stale-result recovery becomes current eval semantics

The deterministic fabric decides CURRENT versus STALE/REJECTED/PROVEN_REBASE. The model learns the response to that typed outcome, not hash/CAS authority itself.

Required mirrored eval family:

- `CURRENT -> continue useful cognition`
- `STALE_REJECTED -> re-read current S1 -> recompute/replan -> new NODE_RESULT`
- `GENERATION_CHANGED -> discard stale local plan -> rejoin current generation`
- `REBASE_PROVEN -> use provenance-preserving runtime result without inventing freshness`
- `LEASE_REVOKED -> stop coordinator publication and fall back to ordinary-node semantics`

Hard negatives:

- old observation is relabeled current after only copying the new epoch/digest fields;
- model self-grants rebase validity;
- model treats lease possession as S0 truth or effect authority;
- model treats repeated peer agreement as evidence of freshness.

### 2.3 Important credit split: simultaneous liveness != simultaneous admitted cognitive flow

The v2 barrier phase proves the candidate property "ten Xeno OS processes are simultaneously live on one shared read-only S1 snapshot" at source level. The barrier packets are deliberately not admitted after coordinator lease creation advances S1. The later ten admitted packets are freshly re-read in separate process invocations before each coordinator CAS commit.

Therefore, even after a clean exact-source v2 runtime PASS:

- **physical GRID10 liveness component** may become eligible for bounded component credit at the exact measured scope;
- **concurrent result-flow/fan-in/contention cognition** is still unproven and requires a later controlled-load experiment where overlapping live nodes produce results under an explicitly defined admission/revalidation policy;
- **whole HCU / EntityOS / J-Space / training** credit remains zero.

This distinction must be preserved in training research so the curriculum does not learn an architecture claim broader than the executable evidence.

### 2.4 Consumed snapshot identity remains a separate proof question

`state_epoch` and `state_digest` fields declare an observation identity. Exact source-bound execution makes those declarations materially stronger in this specific harness because the same trusted child code reads the SQLite snapshot and constructs the payload. But arbitrary caller-authored NODE_RESULT metadata is not a general consumed-input attestation theorem.

General ABI promotion therefore remains blocked until one of the following is explicit and tested:

1. a trusted producer boundary whose exact source/runtime identity is part of the acceptance contract; or
2. a provenance-preserving read-to-result attestation that binds producer identity, exact consumed S1 material/digest and emitted packet/output identity.

External methodology analogy only: SLSA provenance treats resolved input dependencies and output subjects as separate provenance objects under an identified trusted builder. This supports the structural distinction `declared metadata != verified production provenance`; it does not mint EntityOS/HCU credit.

Method sources:
- `https://slsa.dev/spec/v1.2/build-provenance`
- `https://www.sqlite.org/isolation.html`

## 3. Checkpoint / model-source course update

`fix(trigger2): add Qwen checkpoint source-integrity gate v3` landed at `cb47c70557d5627820a9ef2756c8e9e71fd472bb`.

Training interpretation:

- snapshot/source identity validity, loader smoke evidence, consumed selection input identity and final checkpoint winner are separate gates;
- current loader receipts do not prove exact consumed weights + rendered prompt + token tensor selection identity;
- checkpoint winner remains `NONE/UNRESOLVED`;
- no training/J-Space/model credit is minted by the source gate itself.

This separation is now mandatory for future Trigger-2 checkpoint evaluation.

## 4. Runtime failure / proof-gap reinjection

### H36.1 — physical liveness is necessary but insufficient for concurrent cognitive-fabric claims

**Hypothesis:** the current v2 component is sufficient to prove the first physical GRID10 liveness property after exact repository-bound execution, while concurrent cognitive throughput/fan-in needs a distinct controlled-load acceptance.

**Counterhypothesis:** because all ten nodes share one read-only snapshot at one barrier, no further concurrency-specific cognition proof is needed.

**Cheapest discriminator:** after v2 exact runtime PASS, run a bounded controlled-load fixture where ten overlapping child processes emit results during a common active window, measure coordinator fan-in/S1 contention, and preserve exact observation/admission identity without silent relabel/rebase.

### H36.2 — trusted source-bound producer may be sufficient locally but not as a general NODE_RESULT theorem

**Hypothesis:** for the isolated pinned harness, exact clean source identity plus trusted read->payload code may be enough for bounded component acceptance, while the reusable NODE_RESULT ABI still needs a stronger producer/input provenance contract.

**Counterhypothesis:** exact packet epoch/digest and packet digest are sufficient for all NODE_RESULT producers.

**Cheapest discriminator:** construct an adversarial producer that derives payload from old S1 bytes but rewrites packet epoch/digest to current values. A general admission gate must reject unless trusted producer provenance or explicit read-to-result attestation closes the gap.

### H36.3 — stale recovery should be evaluated as typed state transition, not narration

**Hypothesis:** Xeno generalization will improve when stale/rejoin cases require executable typed state transitions rather than prose rules.

**Counterhypothesis:** meta-rule narration is sufficient for a 0.8B model to infer correct recovery behavior.

**Cheapest discriminator:** matched-token family-disjoint eval comparing rule narration versus instantiated `state_before -> runtime_signal -> state_after -> NODE_RESULT` targets.

## 5. Artifact lifecycle changes

- `tools/xeno_physical_grid10_acceptance_v1.py`: `SUPERSEDED_FOR_CURRENT_PHYSICAL_GRID10_PROOF`.
- `tools/xeno_physical_grid10_acceptance_v2.py`: `CURRENT_SOURCE_CANDIDATE_PENDING_EXACT_RUNTIME_RECEIPT`.
- old fbab596 pinned execution: `STALE_DIAGNOSTIC_ONLY_ZERO_CREDIT`.
- `research_entity/execution_requests/2026-08-26_TRIGGER2_PHYSICAL_GRID10_V2_VPS_EXECUTION_PIN_0011673_GPT56SOL_0205P0700.json`: `CURRENT_EXECUTION_REQUEST_PENDING_RUNTIME_RECEIPT`.
- general consumed-snapshot attestation: `BLOCKED / ZERO_GENERAL_CREDIT`.
- Qwen checkpoint source-integrity gate v3: `CURRENT_SOURCE_GATE / NO_WINNER_CREDIT`.
- positive training admission: `BLOCKED`.

## 6. Data-generation decision

No new positive training rows are admitted in this cycle.

Reason: the highest-information current action is to close exact executable process/snapshot/provenance gates and then reinject the measured failures/successes into eval/training. Generating more positive corpus now would risk encoding assumptions broader than the runtime evidence.

Current credits after this delta:

- new admitted positive rows: `0`
- accepted dataset tokens: `0`
- checkpoint winner credit: `0`
- J-Space representation/model credit: `0`
- physical GRID10 runtime credit: `0` pending exact runtime receipt
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`
- training credit: `0`

## 7. Next exact Trigger-2 order

1. Ingest and audit the first exact runtime receipt pinned to `0011673f34bc55b838f52420376df6d68e40d9be`; preserve failure if it does not pass every declared v2 property.
2. If bounded physical GRID10 liveness passes, promote only that component scope.
3. Run the next controlled-load discriminator for simultaneous result flow/fan-in/contention and coordinator failure/rejoin; do not conflate it with the liveness proof.
4. Resolve the general consumed-snapshot/provenance theorem with trusted-producer or explicit read-to-result attestation semantics.
5. Continue BASE/POSTTRAINED/TARGET_MEASURED exact greedy matched evaluation only under the new checkpoint source-integrity gate; keep winner unresolved until consumed input identity and decisive axes are current.
6. Keep the leaky binding generator quarantined; do not reopen positive Forge->Distillery training yield until lineage/nuisance/input-identity gates are current.
