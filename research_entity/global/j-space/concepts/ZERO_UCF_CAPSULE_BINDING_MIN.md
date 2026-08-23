# ZERO CAPSULE -> INFERENCEPACKET -> UCF BINDING — v1

Status: SOURCE CANDIDATE / MECHANISM SUPPORTED
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

The strict composition validator requires the UCF receipt to carry the same causal turn and capsule digest in its digest-covered `binding` object and requires `inference.inference_packet_digest` to equal the exact packet digest.

For `WORKSPACE_BOUND`, UCF `workspace.after_digest` must equal the capsule workspace digest. For `ABSTAINED`, inference cannot execute and neither canonical state nor effects may commit.

## Complement to current main

Current main additionally requires executed UCF cycles to evidence one GWT winner and, for non-plain modes, typed J-Space observation references. A separate matched three-arm discriminator distinguishes observation/projection from causal use.

Those gates do not replace packet ancestry:
- observation/winner evidence answers whether the fabric participated at receipt scope;
- the matched discriminator answers whether intervention changes behavior;
- this chain answers whether the exact consumed InferencePacket descended from the exact fresh Zero workspace capsule under the same generation/turn/workspace lineage.

## Evidence boundary

Current exact packet compiler blob: `c3278a4c46e7af25304f67727d1ed0de9b839aeb`.
Strict chain blob: `3a3e7243d81c0472c5b3659ac9f43494281f9d7d`.
Current branch repository regression blob: `6729acccdf829a8c4d00299f6525df8b0f5343f9`.

Local exact packet blob reconstruction:
- `git hash-object` matched `c3278a4c46e7af25304f67727d1ed0de9b839aeb`;
- `py_compile`: PASS;
- independent standalone capsule/packet/strict-binding matrix: 9/9 PASS;
- packet-id rebinding plus enclosing re-digest: FAIL_CLOSED with `PACKET_ID_BINDING_MISMATCH`.

The repository regression itself still awaits an actually-started exact checkout runner. GitHub-hosted fused-head jobs remained pre-step admission failures (`steps=null`), so they grant no semantic test or runtime credit.

This does not establish a live model invocation, J-Space causal use, GWT runtime behavior, Ubuntu runtime acceptance, effect execution, or whole-product PASS. All such runtime credit remains zero until exact admitted execution.
