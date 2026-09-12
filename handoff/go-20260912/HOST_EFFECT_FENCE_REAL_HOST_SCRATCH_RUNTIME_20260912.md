# GO — shared host-effect fence real-host scratch runtime evidence — 2026-09-12

Status: **ACCEPTED_AT_SCOPE / REAL_HOST_SCRATCH_RUNTIME / NO LIVE OR SERVICE MUTATION**

## Why this boundary mattered

The generic Clay local bridge and the Frank machine-specific bridge use separate Git command/result fabrics but can both reach the same physical ai-core host. Separate per-daemon idempotence is therefore insufficient for promotion-bearing live effects. The required invariant is:

`ONE PHYSICAL HOST -> ONE LIVE/SYSTEM EFFECT CRITICAL SECTION`

This is a coordination boundary only. It does not create a second project truth or effect authority.

## Exact source subject

- source branch: `chatgpt-work/local-bridge-single-writer-20260912`
- exact source commit: `a6569fe0386868bdb9455edd4a43448ad0775cbb`
- tested `host_effect_fence.py` SHA-256: `19b9362563576ebd51611de89afd3f941f085a2c725e151e9be4fe9acabf3a91`
- tested `test_host_effect_fence.py` SHA-256: `0c11a9cfdc3b7aa74189116b6ab6ba91ca3dc2504b43b4a43462d9690d30731d`

The first attempt was evidence-invalid because the local bridge checkout did not contain the pinned source object (`Not a valid object name ...`). No product-negative conclusion was taken from that failure.

The corrected run cloned the exact branch wholly inside the declared scratch root and required cloned HEAD to equal the pinned commit before test execution.

## Real-host execution receipt

- command: `go-host-effect-fence-scratch-gate-v2-gpt56sol-20260912`
- result commit: `c874a7190ed4adf56dd8aec2ecbab7a885d0d54a`
- execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`
- effect classification of dispatched command: `SCRATCH_ONLY`
- scratch root: `/home/ai-core-node/.claude/star/visual/.go_evidence/host_effect_fence_gate_v2_gpt56sol_20260912`
- live avatar mutation: **none**
- service mutation: **none**

## Results

Repository/source tests against the pinned implementation:

- 9/9 `unittest` cases PASS.

Additional real multiprocessing discriminator on ai-core:

- `CROSS_PROCESS_LEASE_EXCLUSION_PASS`
  - one process holding a LIVE effect prevented a second process from entering a concurrent LIVE effect.
- `UNVERIFIED_PRIOR_EFFECT_BLOCKS_FRANK_PASS`
  - normal return from ChatGPT's effect body remained `BODY_RETURNED_UNVERIFIED`; a Frank effect was blocked until independent verification.
- `INDEPENDENT_READBACK_UNBLOCKS_NEXT_EFFECT_PASS`
  - after `verify_success()` bound an independent outcome digest, the next Frank effect could proceed.
- `CRASH_TO_UNKNOWN_REPLAY_BLOCK_PASS`
  - forced process exit while the journal row was `RUNNING` left the row nonterminal; startup reconciliation moved it to `UNKNOWN`, and replay remained blocked.
- aggregate: `HOST_EFFECT_FENCE_CROSS_PROCESS_RUNTIME_PASS`
- command terminal: `HOST_EFFECT_FENCE_SCRATCH_RUNTIME_GATE_V2=PASS`

## Evidence promotion

Promoted at exact scope:

- shared HostEffectFence source is no longer merely `SOURCE_READY/RUNTIME_UNVERIFIED`;
- it has bounded **real-host scratch runtime evidence** for process exclusion, unverified-outcome blocking, independent-readback release, and crash-to-UNKNOWN replay protection.

Still zero / not established:

- installation into either live bridge daemon;
- both daemons actually calling the same installed fence;
- service restart/recovery with the shared fence enabled;
- a promotion-bearing live avatar mutation serialized across both fabrics;
- irreversible/system-effect authority;
- whole-avatar/product effect credit;
- HCU/GWT/J-Space/training credit.

## Next exact gate

Do **not** install or restart services merely because this scratch gate is green.

The next legal promotion boundary is a shadow/integration gate proving that **both current daemon implementations** can route effect-classified commands through the same fence contract while preserving their existing separate branch fabrics, command identity, result publication, and machine/owner attribution. Only after that executable integration gate should service installation or live avatar mutation be considered.

This packet is evidence/reconciliation only and does not claim mutation ownership over the bridge implementation branch.