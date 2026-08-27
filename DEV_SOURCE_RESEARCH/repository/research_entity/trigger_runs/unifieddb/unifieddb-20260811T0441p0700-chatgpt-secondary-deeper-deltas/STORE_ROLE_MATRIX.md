# STORE ROLE MATRIX — deeper UnifiedDB delta run

| Store / receipt plane | Role | Authority | Freshness rule | Rollback rule |
|---|---|---:|---|---|
| UnifiedDB | canonical semantic/logical Frank state | YES | selected semantic head + schema identity + current/recovery execution gates | external rollback-domain-independent floor required for whole-domain rewind |
| ClayGraph | derived/rebuildable topology/projection | NO | separate projection watermark/source semantic epoch; stale => quarantine/rebuild/fallback | may roll back/rebuild without minting semantic truth |
| U12 materialization certificate | executable schema/migration pair identity | LIMITED ADMISSION ONLY | exact ordered schema-chain/pair digest and CURRENT lifecycle | detects schema/migration divergence, not arbitrary same-certificate payload rollback |
| selected semantic lineage head | one-current-sibling selector | YES for lineage selection | exact parent CAS/root binding | cannot alone detect state+selector rollback together |
| external recovery floor | rollback discriminator outside protected rollback domain | YES for recovery admission | monotonic semantic head/generation and canonical schema/build identity | must fail closed when unavailable/ahead; must not become second semantic DB |
| V14/V17 effect receipts | effect/outcome/re-entry terminal history | YES within effect domain | exact attempt/outcome plus causal closure | terminal validity must be stable after ordinary later semantic supersession |
| GWT/prediction/receiver/causal rows | causal-support evidence | SUPPORT, not standalone authority | must obey causal ordering and exact effect linkage | post-hoc self-minted rows must not retroactively prove pre-action use |

## Storage-mode fork

### Profile A — system SQLite 3.45.1, rollback journal DELETE + synchronous FULL
- currently supported as a target-tested storage-safety component candidate;
- avoids the known upstream WAL-reset bug class without claiming a downstream patch;
- importantly, SQLite can provide atomic multi-database ATTACH commits with rollback journals, creating a new option for atomic UnifiedDB + ClayGraph projection-watermark/batch commits;
- costs must be measured because super-journal/fsync and writer serialization may increase p95/p99 latency.

### Profile B — private fixed SQLite 3.53.4 + WAL
- PR #288 tests this path; current target workflow is queued, not evidence yet;
- potentially better reader/writer concurrency and preserves WAL behavior;
- multi-file ATTACH transactions are not crash-atomic across database files in WAL, so Graph freshness remains an explicit derived-state protocol rather than a cross-file atomicity assumption.

Decision law: journal mode is now an architecture/performance/recovery choice, not merely a SQLite-version safety switch.
