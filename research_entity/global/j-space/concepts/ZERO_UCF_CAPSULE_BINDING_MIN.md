# ZERO CAPSULE -> INFERENCEPACKET -> UCF BINDING — v1

Status: SOURCE CANDIDATE / MECHANISM SUPPORTED
Date: 2026-08-23

Purpose: close the causal handoff gap between the deterministic `ZERO_WORKSPACE_CAPSULE/v1` and the canonical `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` without creating another truth, state, identity, effect, or recovery authority.

## One path

`accepted workspace -> ZERO_WORKSPACE_CAPSULE/v1 -> ZERO_INFERENCE_PACKET/v1 -> canonical UCF receipt -> existing UCF+boot ancestry validator`

The new packet is a deterministic admission envelope only. It binds:
- `entity_generation`;
- `causal_turn_id`;
- exact workspace-capsule digest;
- opaque task digest;
- Zero identity + GRF digests;
- workspace digest;
- required Zero mode;
- target engine class;
- J-Space mode.

The strict composition validator requires the UCF receipt to carry the same causal turn and capsule digest in its digest-covered `binding` object and requires `inference.inference_packet_digest` to equal the exact packet digest.

For `WORKSPACE_BOUND`, UCF `workspace.after_digest` must equal the capsule workspace digest. For `ABSTAINED`, inference cannot execute and neither canonical state nor effects may commit.

## Why this is needed

The canonical UCF v1 validator already required `inference_packet_digest` to be a non-placeholder SHA-256, but did not prove that the digest belonged to the fresh Zero workspace capsule for the same turn/generation. A structurally valid receipt could therefore be self-consistent while causally detached from the capsule that was supposed to control the turn.

The strict Zero composition closes that false-green while preserving the existing UCF and boot-ancestry validators as the underlying authorities.

## Evidence boundary

Local exact-blob mechanism run:
- packet compiler blob `da5fdad09df36f0258748c3b0b49676ca6b7796c`;
- strict chain blob `3a3e7243d81c0472c5b3659ac9f43494281f9d7d`;
- focused regression blob `a025e862c7c5ca6991d818ecff36ab918e8dc519`;
- `py_compile`: PASS;
- focused binding matrix: 8/8 PASS.

This does not establish a live model invocation, J-Space causal use, GWT runtime behavior, Ubuntu runtime acceptance, effect execution, or whole-product PASS. All such runtime credit remains zero until exact admitted execution.
