# ZERO CAPSULE -> INFERENCEPACKET -> UCF BINDING — v1

Status: SOURCE CANDIDATE / MECHANISM SUPPORTED AT ANCESTOR; CURRENT CLOSED-SCHEMA DELTA AWAITS EXACT RUNNER
Date: 2026-08-23

Purpose: close the causal handoff gap between the deterministic `ZERO_WORKSPACE_CAPSULE/v1` and the canonical `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` without creating another truth, state, identity, effect, recovery, UCF, or turn authority.

## One path

`accepted workspace -> ZERO_WORKSPACE_CAPSULE/v1 -> ZERO_INFERENCE_PACKET/v1 -> canonical UCF receipt -> existing UCF+boot ancestry validator`

The packet is a deterministic admission envelope only. It binds:
- `entity_generation`;
- `causal_turn_id`;
- exact workspace-capsule digest;
- opaque task digest;
- Zero identity + GRF digests;
- workspace digest;
- required Zero mode;
- target engine class;
- J-Space mode.

`packet_id` is deterministically re-derived during validation from those identity fields. Replacing `packet_id` and merely recomputing the enclosing `packet_digest` therefore fails closed.

`ZERO_WORKSPACE_CAPSULE/v1`, its nested opaque task object, and `ZERO_INFERENCE_PACKET/v1` are closed typed envelopes. Unknown fields are rejected even when the attacker/caller recomputes the enclosing digest. New semantic fields require an explicit schema/version change rather than silent v1 extension. This prevents digest-consistent extension fields from becoming an undeclared control or instruction channel at a downstream consumer.

The strict composition validator requires the UCF receipt to carry the same causal turn and capsule digest in its digest-covered `binding` object and requires `inference.inference_packet_digest` to equal the exact packet digest.

For `WORKSPACE_BOUND`, UCF `workspace.after_digest` must equal the capsule workspace digest. For `ABSTAINED`, inference cannot execute and neither canonical state nor effects may commit.

## Complement to current main

Current main additionally requires executed UCF cycles to evidence one GWT winner and, for non-plain modes, typed J-Space observation references. A separate matched three-arm discriminator distinguishes observation/projection from causal use.

Those gates do not replace packet ancestry:
- observation/winner evidence answers whether the fabric participated at receipt scope;
- the matched discriminator answers whether intervention changes behavior;
- this chain answers whether the exact consumed InferencePacket descended from the exact fresh Zero workspace capsule under the same generation/turn/workspace lineage.

## Current source identities

- workspace capsule compiler/validator: `5a6eb721bb82595914d8434d3f57dce032b6c3db`;
- workspace capsule regression: `0256ab7e92d7829d8a7becb493bcdb86e36ba4e3`;
- packet compiler/validator: `2001ae22ea94c1b2550d7d4c7d160db953db2082`;
- strict chain: `3a3e7243d81c0472c5b3659ac9f43494281f9d7d`;
- branch chain regression: `b4043cd8f0da65c53b805a467c50c79ff6450e44`.

## Evidence boundary

The ancestor packet compiler blob `c3278a4c46e7af25304f67727d1ed0de9b839aeb` was independently reconstructed and had bounded component evidence:
- `git hash-object` matched the exact blob;
- `py_compile`: PASS;
- standalone capsule/packet/strict-binding matrix: 9/9 PASS;
- packet-id rebinding plus enclosing re-digest: FAIL_CLOSED with `PACKET_ID_BINDING_MISMATCH`.

The current closed-schema delta adds authored regressions for:
- unknown capsule top-level field + recomputed `capsule_digest`;
- unknown nested task field + recomputed `capsule_digest`;
- unknown packet top-level field + recomputed `packet_digest`.

Those new exact blobs have not yet been executed by an actually-started exact-checkout runner in this branch. No ancestor PASS is promoted to the changed blobs. GitHub-hosted fused-head jobs have repeatedly failed before visible steps (`steps=null`), which is execution-admission failure rather than semantic test failure.

This does not establish a live model invocation, J-Space causal use, GWT runtime behavior, Ubuntu runtime acceptance, effect execution, or whole-product PASS. All such runtime credit remains zero until exact admitted execution.
