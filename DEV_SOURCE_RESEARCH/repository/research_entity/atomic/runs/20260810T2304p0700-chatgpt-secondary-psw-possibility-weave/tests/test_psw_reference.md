# PSW reference test manifest

Reference implementation: `implementation/psw_reference.py`

## Positive invariants

- reconstruct each sparse branch exactly from immutable base + branch delta;
- FULL_COPY, SPARSE_OVERLAY_MEMO and PSW pure outputs are byte/value-identical for the declared state model;
- exact read signatures define the only allowed computation-sharing equivalence in the proxy;
- PSW and overlay memo must execute exactly one transition per unique exact read signature;
- current `self.root` and current base epoch pass branch admission.

## Negative / falsification controls

1. Hidden-read fault: transition uses `a,b`, signature exposes only `a`; two branches equal on `a` but differ on `b`; shared cache must produce a concrete wrong output and therefore demonstrate unsoundness.
2. Payload-only merge fault: identical materialized payload but distinct `hypothesis_id`/provenance must show why physical equality cannot imply epistemic identity.
3. Stale base epoch: reject.
4. Wrong native identity `Frank`: reject; human surface name is not the native branch identity.
5. Unknown/dynamic material read set: no lifting.
6. External read/write/security-sensitive transition: no unresolved multi-branch execution.

## Scaling matrix

- fields: 64, 256, 1024;
- branches: 4, 16, 64, 256, plus 1024 at F=256/1024;
- divergence: 0, 1%, 5%, 10%, 25%, 50%;
- pure transition read-set: 4, 16;
- total main scaling cells: 168.

## Replication

Representative F=1024/N=256/read16 regime repeated with six seeds for every divergence level.

Additional held-out adaptive-selector evaluation: 48 separately seeded cells across F=256/1024, N=64/256, read4/16 and all six divergence levels.

## PASS / FAIL interpretation

A technical PASS means the reference harness preserves branch reconstruction and fails closed on the listed unsafe controls. It does **not** mean PSW architecture is accepted.

The architecture-level acceptance law is stronger: PSW must show a unique benefit against `SPARSE_OVERLAY_MEMO`. That condition was not met, so the architecture decision is NO_PROMOTION even though the reference semantics passed its safety assertions.
