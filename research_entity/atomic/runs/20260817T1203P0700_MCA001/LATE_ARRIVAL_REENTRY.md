# MCA-001 late-arrival re-entry

Late-arrival canonical research head observed after the initial candidate packet: `cb61431e8f06fd0ac7d76751801e9003863f6630`.

Material changes since the run base:

- `UnifiedDB` schema advanced to v5 with a single `meta.entity_generation`.
- real boot/recovery advances that global generation and fences both permanent user sessions together;
- `assert_live_generation(session_id, generation)` requires the per-session value and global entity value to agree;
- a diagnostic `--once` state probe does not advance the live generation;
- `entityos.exec` already has a label-independent global automatic effect lease.

## Adjudication

`MCA-001` is **RETAIN_AND_REVISE**, not superseded.

The new global generation is a strong lifetime/recovery fence. It does not by itself distinguish an immutable contradiction-preserving knowledge append from a destructive resolution/retraction/absence-dependent decision inside one live generation. MCA v0.2 therefore composes *under* the current global generation:

1. every MCA operation must belong to the current live entity generation;
2. any real boot/recovery generation advance invalidates all in-flight MCA work;
3. monotone append is only a proposed relaxation of ordinary same-generation knowledge-state coordination;
4. nonmonotone operations still require exact context validation and a lease;
5. `EXTERNAL_EFFECT` remains strictly under the current EffectGate / `effect:entityos.exec` lease and gains no authority from MCA.

New required falsifier: begin two in-flight candidate operations, force the admitted recovery/boot generation advance, then prove both stale operations fail closed regardless of polarity.

No current `the artefact/` implementation is changed by this branch.
