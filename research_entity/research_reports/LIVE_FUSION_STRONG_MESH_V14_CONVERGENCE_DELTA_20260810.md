# V1.4 convergence delta — 2026-08-10

Status: SHADOW_CANDIDATE_NOT_PROMOTED

This file intentionally creates a fresh PR #166 head after parent PR #156 advanced from the original fork point `2f7d34545cdd86b2c289f5b7697633b5d7814d6f` to observed head `cc30ea26de3ce2b535f15fe6b0871caae8555590`. The goal is to force the pull-request merge-ref CI lane to evaluate V1.4 against the current parent rather than treating the original fork snapshot as sufficient.

Live-fusion feedback changed the role of this branch:

- PR #156 now has an explicit Mesh/Transport bridge and treats semantic target selection as a separate Mesh control-plane concern.
- Another live worker consumed V1.4's false-current-dependency negative result and produced the V15 Dependency Evidence Gate: soft/associative dependency evidence may increase visibility but cannot alone mint a blocking interrupt; current hard witness is required for a dependency-only interrupt.
- PR #167 records the resulting convergence: Mesh V2 semantic routing/anti-entropy -> V15 witness gate -> PR #156 transport/replay/re-entry -> PR #165 work lease/fencing/pre-effect reservation.
- V1.4 is retained as the dependency-reach / low-signal / false-edge differential arm. It is no longer proposed as an independent production semantic routing owner.

The original V1.4 11/11 local mechanism tests and 48-pair synthetic fixture remain evidence only for the exact candidate logic. They are not current-parent CI evidence, Hostinger evidence, real-worker evidence or architecture promotion.

No second out-of-box experiment is added; this exact GO run already used `OOB_HIDDEN_DEPENDENCY_LESION_RESCUE`.
