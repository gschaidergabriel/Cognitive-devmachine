# PLATFORM PORTABILITY CONTRACT

## Goal

Build Linux-first without locking the cognitive/application architecture to Linux.

## Four-part representation for every platform-dependent mechanism

For each capability define:

1. **Semantic contract** — what behavior the rest of the system requires.
2. **Portable interface** — stable API/data/transition contract exposed upward.
3. **Platform adapter** — Linux/Windows/macOS/BSD/mobile/embedded implementation.
4. **Target optimization** — optional platform-specific fast path that may not change required semantics silently.

## Examples

### Service/process supervision
Semantic contract: start/stop/restart/health/dependency/order/resource-policy/recovery receipts.
Linux adapter candidates: systemd, cgroups, namespaces.
Other platforms: platform-native service managers and process/job primitives.

### IPC
Semantic contract: typed message/state transfer, identity, ordering where required, backpressure, failure semantics, observability.
Implementations may include shared memory, Unix sockets, pipes, TCP/QUIC, named pipes, platform message systems or embedded queues.

### Isolation/capabilities
Semantic contract: least authority, explicit capability grant, expiry/revocation, external effect gate and audit trail.
Linux primitives are implementation candidates, not the definition itself.

### Storage
Semantic contract: identity, version/history, provenance, durability class, transaction/recovery semantics.
SQLite, RocksDB, PostgreSQL, event logs, graph stores or custom Clay stores are competing implementations.

## Promotion tests

A portable interface is accepted only if:
- it preserves the semantics required by higher layers;
- failure/recovery behavior is explicit;
- security authority does not become ambiguous;
- it does not impose unacceptable overhead;
- target-specific capabilities can still be reached through typed extensions when needed.

A platform-specific mechanism is promoted as architectural rather than merely implementation-specific only after competing environments or equivalent implementations are tested.

## Portability ladder

P0 — Linux reference implementation
P1 — Linux distributions/kernel variants
P2 — second desktop/server OS implementation
P3 — third OS family / different process-security model
P4 — edge/mobile/embedded constraint test
P5 — distributed heterogeneous deployment

The Research Entity may advance different contracts independently along this ladder.
