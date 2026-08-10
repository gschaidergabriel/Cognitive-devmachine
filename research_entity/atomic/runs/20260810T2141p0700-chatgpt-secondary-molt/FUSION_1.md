# Fusion 1 — current problem surface

The highest-leverage fresh falsification is physical, not cognitive: EUDI can detach execution through sealed memfd and preserve restart lineage, but the same writable inode capability required by naive in-place state updates also reaches immutable root/model bytes. The split control retains ordinary filesystem least privilege that naive EUDI loses.

This is a cross-package blocker touching identity, UnifiedDB continuity, ClayCode lowering and security/recovery. Hashes detect corruption but do not prevent it. A byte-range check inside the same compromised writer is too weak because the writer retains a general capability. The search target is therefore a mechanism that changes the *geometry of mutability* rather than merely adding another check.

Current strongest baseline: split immutable root/model + writable state database. Current failing baseline: one EUDI inode opened O_RDWR by the state runtime. Mandatory candidate property: ordinary self.root cognition must not possess a primitive capable of rewriting accepted prefix bytes.

The architecture question is not “can a one-file image work?” E1/E3 already says a boot handoff can work. The discriminating question is “can one persistent inode preserve a meaningful least-privilege barrier without simply recreating a second physical state file?”
