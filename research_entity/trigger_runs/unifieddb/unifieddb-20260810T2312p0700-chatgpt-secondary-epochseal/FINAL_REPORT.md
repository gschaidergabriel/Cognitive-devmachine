# UnifiedDB run — EpochSeal Hybrid v1

Run: `unifieddb-20260810T2312p0700-chatgpt-secondary-epochseal`  
Target: `self.root / Frank v0.1`  
Component: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`  
Research status: **CANDIDATE / TESTING — no target promotion**

## Executive result

This run converts UnifiedDB from a broad unification concept into one executable discriminator: **EPOCHSEAL_HYBRID_V1**.

The candidate keeps exact state/event/effect/re-entry truth in one authoritative epoch-sealed semantic store and treats ClayGraph, FTS, vector/ANN and activation surfaces as explicitly rebuildable projections carrying `derived_from_epoch` and generation identity. Exact reads are bound to one `source_epoch`; associative ranks may nominate candidates but do not become truth or effect authority.

A local executable probe passed 11/11 boolean continuity checks including stale-epoch rejection, idempotency replay rejection, epoch-chain integrity, crash-before-commit rollback, restart integrity, query-receipt epoch binding, derived-index lag detection, and verified-outcome to provenance-bound re-entry linkage.

A four-architecture local synthetic comparison favored the hybrid hot path under the tested conditions:

- specialized authoritative split: p50 2686 us; crash divergence reproduced;
- logical unified API over split stores: p50 4205 us; partial commit detectable but not atomic;
- canonical + rebuildable sidecar: p50 1223 us; canonical truth preserved with 3-epoch induced sidecar lag;
- physical consolidation: p50 1355 us; atomic rollback passed but common-mode failure radius is larger.

These numbers are **local synthetic evidence only** and do not justify target promotion.

## High-impact external finding

Fresh SQLite primary documentation published in 2026 records a rare WAL-reset data-race corruption bug affecting SQLite 3.7.0 through 3.51.2. It is fixed in 3.51.3+ with documented backports to 3.50.7 and 3.44.6. Therefore the exact SQLite runtime on the accepted target VPS is now a correctness gate.

Candidate policy:

- fixed SQLite runtime -> WAL + `synchronous=FULL` may be benchmarked;
- vulnerable/unverified runtime -> rollback journal + `synchronous=FULL` fallback;
- no WAL fast-path promotion from assumption or distro name.

Primary sources:

- https://www.sqlite.org/wal.html
- https://www.sqlite.org/isolation.html
- https://www.sqlite.org/sessionintro.html
- https://www.sqlite.org/stricttables.html
- https://www.sqlite.org/fts5.html
- https://github.com/pgvector/pgvector

## Target implementation effect

A reversible Frank-target candidate was created in `gschaidergabriel/Dr.-Unterweger` as PR #182 (`91ea8194912c8483c240c723da980850c5cafff0`). It adds an executable continuity probe and a self-hosted workflow. The candidate explicitly does not claim whole-Frank acceptance.

An existing `Frank Deep Integrity` check associated with the PR completed with failure and no usable step log was retrieved in this run. That failure is preserved as unresolved CI evidence. It is not silently attributed to UnifiedDB, and no VPS continuity receipt is promoted from it.

## Architecture decision

Current best next-test architecture:

`ClayCode semantic authority -> canonical epoch-sealed state store -> epoch-bound rebuildable ClayGraph/FTS/vector projections -> bounded query/assembly receipts -> GWT/action/effect -> verified outcome -> provenance-bound re-entry`

This is deliberately not a universal one-engine claim. `KEEP_ISOLATED` remains correct for credentials, provider-side state, model files/KV and any store whose recovery/capability boundary is safer outside the canonical DB.

PostgreSQL + pgvector remains a strong comparator because it can co-locate transactional relational state with exact or approximate vector retrieval and PITR. It is **NOT_TESTED_ON_TARGET** in this run and therefore is not selected over the hybrid.

## Required next falsifiers

1. Record exact target VPS `sqlite3.sqlite_version`, Python SQLite binding, compile options and journal mode.
2. Run the new continuity probe on the accepted self-hosted VPS and preserve artifact/resource receipt.
3. Classify the PR #182 `Frank Deep Integrity` failure; repair only if the failure is causally related.
4. Re-run matched hybrid vs physical consolidation vs current baseline on target with p50/p95/p99, CPU/RSS/I/O and recovery timing.
5. Crash during write/checkpoint/rebuild; verify epoch chain, `quick_check`, last-known-good rollback and stale writer rejection.
6. Add real provider timeout-after-acceptance reconciliation and prove `verified outcome -> effect receipt -> provenance re-entry -> DONE`.
7. Bind ClayGraph/GWT/Hyperposition read surfaces to declared `source_epoch` / `derived_from_epoch` and execute shuffled/no-reentry controls.
8. Only then consider changing F-V01-04 from OPEN to measured IN_PROGRESS/PASS evidence.

## Scientific conclusion

The run supports semantic/logical unification and a single authoritative continuity plane. It **refutes** the naive idea that a unified API over multiple authoritative stores is enough for atomic cognitive state. It does **not** yet prove that one physically consolidated database is globally superior. The current candidate maximizes correctness and reversibility while opening a measurable path to lower hot-path cost.
