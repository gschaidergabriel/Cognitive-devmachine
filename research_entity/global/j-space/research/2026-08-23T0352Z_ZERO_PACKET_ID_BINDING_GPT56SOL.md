# ZERO adversarial review — packet_id semantic binding

Date: 2026-08-23
Trigger: `zero`
Organ: GPT-5.6 Sol
Branch: `zero/20260823-capsule-ucf-binding-gpt56sol`

## R0 observed

After live-main fusion, parallel review commit `a5c14d086162ddbd1ac52410c3c3f4ab69f0b792` found a second-order packet self-consistency gap: `compile_packet()` derived `packet_id` from the identity binding, but `validate()` only required the supplied id to look like a SHA-256. A caller could replace `packet_id`, recompute `packet_digest`, and retain an internally self-consistent but falsely identified packet.

## Repair adjudication

RETAIN. Current packet compiler blob:
`c3278a4c46e7af25304f67727d1ed0de9b839aeb`.

Validation now re-derives:

`SHA256("ZERO_PACKET_ID/v1\\0" || canonical_json(identity_binding))`

and requires exact equality with `packet_id`. Abstention additionally requires `required_zero_mode=ABSTAIN`, and optional Zero/GRF digests are validated when present.

Parallel test commit `f9bb3372b06137a464a3d401049fcc1f81606d03` added the repository poison regression. Current branch test blob:
`6729acccdf829a8c4d00299f6525df8b0f5343f9`.

## Independent bounded re-check

The repaired packet was independently reconstructed from the GitHub patch; local `git hash-object` exactly matched `c3278a4c46e7af25304f67727d1ed0de9b839aeb`.

A separate local standalone matrix exercised the capsule/packet/strict-binding mechanism:
- relevant files `py_compile`: PASS;
- 9/9 tests PASS;
- new poison: replace `packet_id`, recompute enclosing `packet_digest`, validate same capsule -> FAIL_CLOSED with `PACKET_ID_BINDING_MISMATCH`.

An independently authored equivalent repository-test byte sequence hashed to `69c73cc23403387e896b9a9cb4bc830e3b10d1ef`; it was **not** written because branch commit `f9bb3372...` already supplied the same discriminator as blob `6729accc...`. This avoids a duplicate permanent path.

The branch repository regression still requires an actually-started exact checkout runner. Current hosted jobs fail before visible steps, so no full-suite/runtime credit is inferred.

## Authority / credit

No new authority introduced. MiniUnifiedDB and deterministic authority/effect gates remain canonical; model/J-Space/GWT results remain candidate/measurement only.

Runtime/model/J-Space/Whole-GWT/Claude/product credit: ZERO.
