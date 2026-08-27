# Triggerwort 2 — Training/Evaluation Course Delta V37

**Date:** 2026-08-26  
**Trigger:** `triggerwort 2`  
**Persistent entity:** Clay  
**Product:** EntityOS  
**Architecture:** HCU  
**Supervisor authority:** inbox-selected 8.81 delta  
**Status:** CURRENT RESEARCH COURSE DELTA / NONCANONICAL / SUCCESSOR-DYNAMIC  
**Supersedes for this proof question:** the unresolved consumed-snapshot interpretation in V36; does **not** supersede runtime quiescence or physical-GRID10 execution gates.  
**Observed main before write:** `9ef02572ce3fbbc86970bf6e3f02c5eb4c318c00`

## 1. Trigger-2 re-entry result

The highest-precedence current control-plane blocker remains outside this research delta: the FreeSwarm owner emergency stop is source-hard-off but runtime quiescence of pre-existing provider-capable processes is not yet proven. No new provider/runtime experiment is authorized by this document, and no runtime/training credit is minted.

For the training/evidence lane, the highest-information nonduplicate question was narrower:

> Does the repaired physical GRID10 v2 harness already prove that the NODE_RESULT snapshot identity was derived from the S1 snapshot actually consumed by the child, or does it still require a new read-to-result attestation field before its first bounded component run can be credited?

## 2. Exact-source finding: bounded harness versus general ABI

### 2.1 R0 — what the current v2 source directly does

Current `tools/xeno_physical_grid10_acceptance_v2.py`:

1. opens SQLite in read-only mode;
2. explicitly begins one read transaction;
3. reads `epoch`, `generation`, `tasks`, `scopes`, and `leases` through that same connection/transaction;
4. computes `state_digest` from those values;
5. chooses the task from the same in-memory snapshot object;
6. constructs `NODE_RESULT/v1` core fields `generation`, `state_epoch`, and `state_digest` directly from that same snapshot object;
7. constructs the result payload in the same trusted child process;
8. computes `packet_digest = dg(core)` before emission;
9. while the GRID10 barrier is held, the parent checks process/PID binding, an open read transaction, and an O_RDONLY file descriptor to the exact S1 database path.

Therefore, for the **exact pinned trusted child source**, snapshot metadata is not an arbitrary later caller claim: it is mechanically derived inside the same process from the same open read transaction that selected the task and produced the packet.

### 2.2 R1 — scope-split conclusion

**Bounded physical-GRID10 harness claim:** a separately added in-packet consumed-snapshot attestation is **not a prerequisite** for the first exact-source physical-GRID10 v2 component acceptance, provided the repository-bound runtime receipt binds the exact clean source/tree/runtime and the executed source remains the trusted producer described above.

**General `NODE_RESULT/v1` ABI claim:** the same conclusion does **not** generalize. Arbitrary or future producers can populate `generation/state_epoch/state_digest` fields without proving which S1 bytes they actually consumed. The reusable ABI therefore still lacks a general producer/input provenance theorem.

This resolves the prior ambiguity without weakening the fail-closed rule:

`TRUSTED_EXACT_SOURCE_READ_TO_PACKET_DERIVATION != GENERAL_CALLER_METADATA_ATTESTATION`

and preserves the project analogy:

`DECLARED_SNAPSHOT_HASH_IS_NOT_GENERAL_NODE_READ_ATTESTATION`

while recognizing that an exact-source trusted producer can itself be the bounded attestation boundary.

## 3. Why this distinction is technically justified

### SQLite transaction semantics

SQLite documents that a read transaction sees a stable database view for the transaction, and in WAL mode a read transaction continues to see its original snapshot while concurrent commits remain invisible to it. This supports treating the v2 child transaction as the consumed-read boundary when all covered fields are read through that transaction.

Primary sources:

- https://www.sqlite.org/isolation.html
- https://www.sqlite.org/wal.html
- https://www.sqlite.org/c3ref/snapshot.html

The optional `sqlite3_snapshot_*` API can name/reopen WAL snapshots, but it requires `SQLITE_ENABLE_SNAPSHOT` and is not a portable assumption for the Python stdlib runtime. Trigger-2 should therefore not require that C API merely to credit the current bounded harness.

### Provenance structure analogy

SLSA Build Provenance separates the identified process/builder, its resolved inputs/dependencies, invocation parameters, and output subjects. The useful structural analogy is:

`trusted producer identity + consumed input identity + output subject identity`

rather than merely copying an input digest into output metadata.

Primary source:

- https://slsa.dev/spec/v1.2/build-provenance

This is methodology only and mints no EntityOS/HCU credit.

## 4. Minimal future general-ABI contract

Do **not** retrofit this into the current physical-GRID10 v2 acceptance unless a concrete adversarial test demonstrates that exact-source repository binding is insufficient. For the future reusable `NODE_RESULT` producer boundary, the minimal deterministic contract should be equivalent to:

```text
snapshot_subject_digest = H(
  generation,
  state_epoch,
  state_digest,
  exact covered S1 material identity or trusted transaction receipt
)

result_core_digest = H(NODE_RESULT core without attestation/digest)

producer_binding_digest = H(
  producer_source_identity,
  producer_process_generation_identity,
  snapshot_subject_digest,
  result_core_digest
)

packet_digest = H(
  NODE_RESULT core,
  consumed_input_attestation
)
```

Required properties:

- no circular digest dependency;
- attestation binds the **result core** to the **consumed input**;
- producer identity is deterministic/runtime-verifiable, not model asserted;
- original observation identity cannot be silently rewritten during rebase;
- ordinary Xeno nodes gain no S1/S0/effect authority from attestation;
- model cognition may later consume typed outcomes, but does not become the attestation authority.

## 5. Process identity refinement

The current parent-owned `Popen` objects, barrier overlap, ready-PID equality, packet-PID equality, and parent-observed exits are adequate evidence for the bounded process cohort if the exact run is repository-bound.

A raw numeric PID is not a durable general process identity across time because PIDs may be reused. Linux `pidfd` is a stable kernel reference to a specific task and is useful during live verification. For a durable serialized receipt, a future general producer contract may additionally record a process-generation tuple such as:

`boot identity + pid + kernel process start identity`

while using `pidfd` during the live observation window where available.

Method source:

- https://man7.org/linux/man-pages/man2/pidfd_open.2.html

This is **not** a new prerequisite for the first bounded GRID10 v2 component run; it is a reusable-ABI hardening direction.

## 6. New adversarial discriminators

### CSA-013 — trusted-source versus arbitrary-producer split

A producer outside the pinned child source reads stale S1, then copies current `generation/state_epoch/state_digest` into a syntactically valid `NODE_RESULT/v1` packet.

Expected:

- general ABI gate: `REJECT / CONSUMED_INPUT_UNPROVEN`;
- exact physical-GRID10 v2 component run: this adversarial producer is outside the pinned source identity and therefore cannot borrow the trusted-harness credit.

### CSA-014 — exact trusted producer positive control

Pinned v2 child source opens one read transaction, derives snapshot fields and task selection from it, constructs the packet in the same process, and the repository-bound receipt proves clean exact source/tree/runtime.

Expected:

`ELIGIBLE_FOR_BOUNDED_PHYSICAL_GRID10_COMPONENT_REVIEW_ONLY`

Never whole HCU/EntityOS/J-Space/training credit.

### CSA-015 — source substitution

A byte-modified child preserves output shape and all snapshot fields but is not the pinned source hash/tree.

Expected:

`REJECT_REPOSITORY_BOUND_COMPONENT_CREDIT`

regardless of packet correctness.

### CSA-016 — PID reuse / detached receipt

A historical numeric PID is replayed in a later receipt without a live parent/process-generation binding.

Expected:

`REJECT_DURABLE_PROCESS_IDENTITY_CLAIM`

This does not invalidate the short-lived parent-observed Popen/barrier proof in one bounded run.

### CSA-017 — incomplete consumed-state coverage

The trusted child derives `state_digest` from a subset of S1 while later cognition consumes an additional authoritative S1 field not covered by the digest/receipt.

Expected:

`REJECT_GENERAL_CONSUMED_SNAPSHOT_COMPLETENESS_CLAIM`

This creates an explicit completeness requirement: every authoritative S1 input that can affect the result must either be inside the consumed-input digest or separately declared/bound.

## 7. Training-course consequence

No new positive SFT rows are admitted.

The model should not be trained to compute or validate this attestation. It should learn typed runtime outcomes such as:

- `CURRENT_TRUSTED_PRODUCER`
- `CONSUMED_INPUT_UNPROVEN`
- `STALE_REJECTED`
- `SOURCE_IDENTITY_MISMATCH`
- `REBASE_PROVEN`

and respond with the correct cognitive recovery/rejoin behavior.

Hard negative to preserve:

`packet fields match current -> therefore observation is current`

Positive semantic law:

`runtime-proven currentness may be consumed as an input; it is not minted by model narration`.

## 8. Interaction with the current physical-GRID10 gate

This delta **narrows**, rather than expands, the immediate GRID10 work:

1. do not add a second redundant attestation subsystem to the already-pinned v2 harness merely from conceptual caution;
2. first satisfy current supervisor 8.81 runtime-quiescence requirements;
3. re-enter execution authority;
4. execute the exact currently admitted/pinned fused GRID10 source on the authorized non-provider surface;
5. if the exact-source receipt passes, credit only the measured physical-GRID10 component scope;
6. only then run the controlled-load/fan-in/failure-rejoin discriminator;
7. separately harden the general NODE_RESULT producer ABI before arbitrary producers can receive consumed-input currentness credit.

## 9. Hypotheses / counterhypotheses

### H37.1 — exact-source trusted derivation is sufficient for bounded component credit

**Hypothesis:** repository-bound source identity plus the current same-transaction read->packet derivation is sufficient consumed-input evidence for this specific harness.

**Counterhypothesis:** without an explicit transaction/attestation object inside the packet, even the pinned harness cannot prove consumed input.

**Cheapest discriminator:** source-substitution/adversarial-producer test. If the repository-bound runner rejects all non-pinned producer paths and the pinned child has no caller override between snapshot read and packet construction, the counterhypothesis adds no discriminating power for this bounded scope.

### H37.2 — general ABI still needs explicit producer/input binding

**Hypothesis:** once NODE_RESULT packets can come from multiple producers, packet metadata equality is insufficient and an explicit read-to-result provenance boundary becomes necessary.

**Counterhypothesis:** deterministic coordinator admission against current epoch/digest is sufficient for every producer.

**Falsifier:** construct stale-derived payload + current copied metadata. If it is indistinguishable at admission, the general ABI theorem is not closed.

### H37.3 — snapshot completeness is a larger risk than snapshot naming

**Hypothesis:** the dominant future failure will be omitted authoritative inputs that affect cognition but are absent from the snapshot digest, not lack of an opaque SQLite snapshot object.

**Counterhypothesis:** the existing digest already covers every authoritative input that can affect NODE_RESULT semantics.

**Discriminator:** enumerate all S1 reads in the actual cognitive producer path and prove each is inside the consumed-input digest/receipt or separately bound.

## 10. Credit boundary

- new admitted positive rows: `0`
- accepted dataset tokens: `0`
- physical GRID10 runtime credit: `0` pending exact admitted execution
- general NODE_RESULT consumed-input attestation credit: `0`
- checkpoint winner credit: `0`
- J-Space representation/model credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`
- training credit: `0`

## 11. Next exact Trigger-2 action

**Control plane first:** prove FreeSwarm runtime quiescence and no provider-usage delta as required by supervisor 8.81; do not launch a new runtime experiment before that.

**Research lane while runtime is blocked:** audit the exact S1 read set of the current/future real cognitive NODE_RESULT producer and produce a machine-checkable `consumed_input_coverage` manifest. The manifest should fail closed when a newly read authoritative S1 field is absent from the consumed-input digest/receipt. This closes CSA-017 without duplicating the current physical-GRID10 harness.
