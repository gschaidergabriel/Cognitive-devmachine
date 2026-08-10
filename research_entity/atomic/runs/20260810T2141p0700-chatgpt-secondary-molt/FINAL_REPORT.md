# ATOMIC FINAL REPORT — MOLT-001

## Decision
**NO ARCHITECTURE PROMOTION.** `ATOMIC-CANDIDATE-MOLT-001 / Monotonic One-Inode Lineage Tail` is a `SUPPORTED_LOCAL_PROXY_RETEST` possibility.

## Selected problem
Fresh EUDI E5 evidence shows that a same-inode ordinary `O_RDWR` capability can mutate bytes in the supposedly immutable root/model prefix, while the split control can permit state writes and deny root writes. The ATOMIC mesh explicitly challenged a physically single-image design to remove that general writable-inode capability.

## Radical mechanism
MOLT removes the mutable byte-range as an architectural primitive. Accepted root/model bytes form an immutable prefix. State exists only as a forward-only sequence of typed, root-bound epoch frames appended at the tail. self.root cognition receives no writable image descriptor. A minimal append broker receives `StateDeltaEnvelope` messages and may append only when a target-host binding proves kernel append-only inode semantics, no `CAP_LINUX_IMMUTABLE`, and a narrow syscall surface. Root/model changes and compaction construct a new candidate image through external release authority; they are never ordinary state writes.

## Why this is structurally different
Naive EUDI separates immutable and mutable regions *spatially* but gives one writer a bidirectional file capability. MOLT replaces spatial trust with a *temporal monotonicity invariant*: ordinary writes may extend history but may not address accepted history. The physical state coordinate is time/epoch, not a rewritable region.

## Executable local discriminator
The Python reference proxy implements image identity, root-bound chained state frames, commit markers, semantic root/authority rejection, recovery to valid prefixes, a cached append broker, replay rejection and resource baselines.

Observed on local Linux kernel 6.18.35:
- naive `O_RDWR + pwrite(offset=0)` modified the immutable prefix;
- the local `O_APPEND` negative control preserved the prefix, but this is not promoted as a security mechanism;
- all 451 byte cuts through a candidate final frame recovered either the prior state or the fully committed state; zero fabricated epochs in this simulated torn-suffix matrix;
- all 712 sampled state-region corruption cases preserved a valid prefix state or rejected/quarantined; zero fabricated state in the measured subset;
- a structurally valid forbidden-root semantic frame was rejected;
- a replayed epoch frame was rejected;
- restart continuity recovered epoch 800 and continued to 810.

## Cost / negative evidence
For 800 fsync-per-transaction microtransactions, MOLT p50/p95/p99 were 1228.2/5370.3/17619.9 us versus 1162.0/4138.6/22369.6 us for a simple append+fsync baseline. Mean slowdown was 1.037x. The larger problem is encoding density: 455.6 bytes/tx versus 27.7, a 16.43x amplification on tiny payloads. The current JSON/hash-frame representation is therefore *not integration-quality*.

Local container privilege could not set `FS_APPEND_FL`; the decisive kernel-enforced append-only property remains unverified locally. External Linux documentation also destroys the tempting shortcut “O_APPEND is enough”: `RWF_NOAPPEND` exists on newer kernels. MOLT therefore requires an inode-level append-only binding plus adversarial target testing, not an O_APPEND convention.

## Prior art
Append-only files, immutable/cryptographically linked databases, transparency logs, event sourcing/WAL, executable+appended-store designs and capability brokers are known mechanisms. MOLT remains only a `NOVEL_COMBINATION_CANDIDATE` in the searched scope; no world-first claim is made.

## Strongest counterhypothesis
A signed split layout or bounded loop-subrange view can provide equal deployment coherence and stronger/simpler least privilege with much lower recovery/compaction/storage complexity. If MOLT cannot beat that under matched target-VPS tests, strict one-inode EUDI should be abandoned or weakened.

## Next falsifier
Run the append-only inode attack on the accepted Hostinger target: provisioning sets and verifies the append-only inode flag; the broker lacks the capability to clear it; cognition has no write fd; then deliberately try non-append open, `pwrite`, `pwritev2(RWF_NOAPPEND)`, `ftruncate`, `fallocate`, alternate asynchronous write paths and FD-passing attacks. Compare prefix integrity, state durability, latency/resources and operational complexity against split and loop-subrange controls.
