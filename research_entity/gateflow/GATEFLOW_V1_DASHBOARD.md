# GateFlow v1 — live dashboard

Snapshot: 2026-08-11 00:59:30 +07  
Target repo observed: `gschaidergabriel/Dr.-Unterweger@25328c0f1924c98b197dfaf1205060667e9a21d8`  
Formal Frank workspace: `2026-08-10T23:15:00+07:00` / ~3.0357% resolver credit  
Workspace-control lag at this snapshot: ~104.5 minutes  
Mode: **PROMOTION_PRESSURE**

## Primary optimization surface

All three metrics are mandatory together:

| Metric | Current |
|---|---:|
| Accepted gate weight delta / 1M tokens | `null` — exact current-window denominator/admission delta not materialized |
| Accepted gate weight delta / worker-hour | `null` — worker-hour denominator not materialized |
| **Risk Retired / 1M tokens** | `null` — numerator exists; exact current-window token denominator not materialized |
| Risk Retired units — total acceptance-path value | **16.0** |
| └ fully retired risk units | **13.0** |
| └ promotion-block containment units | **3.0** |

A `null` normalized value is intentional. GateFlow does not fabricate denominators.

## Risk ledger

### Fully retired on executable/Target evidence

| Failure domain | Severity | Evidence | Credit | Closure |
|---|---:|---|---:|---|
| fork child inherited process-local Gate capability and could exercise effect authority | P1 | Target VPS | 5.0 | #241 / target main `c7dbfac…` |
| lockfile unlink/recreate admitted a second physical execution lock object | P1 | Target VPS | 5.0 | #225 / target main `4b5874c…` |
| ClayCode generic angle tokens collided with relation tokens on real Frank surface | P2 | Target VPS | 3.0 | #236 |

### Promotion blocked, residual risk still open

| Failure domain | Severity | Evidence | Credit | Next closure |
|---|---:|---|---:|---|
| valid old UnifiedDB snapshot can resurrect a stale DB-local execution generation | P1 | Target VPS | 3.0 | #240 external generation-floor candidate + exact-current recovery integration |

### Open risks — deliberately **0 credit**

| Failure domain | Evidence so far | Why zero |
|---|---|---|
| whole state-root pathname swap may create a second directory anchor | mechanism/test obligation | no accepted Target repair |
| explicit `pass_fds` can keep a flock-backed anchor alive after issuer crash | local executable mechanism | Target reachability/repair not yet accepted |
| fork child may keep an orphaned physical lock after issuer hard exit | mechanism/test obligation | Target discriminator pending |
| `SCM_RIGHTS` can transfer the same flock-backed open-file-description | local executable mechanism | must prove transferred FD cannot mint Frank execution/effect capability |

Duplicate reproductions of one failure domain cannot multiply Risk Retired credit.

## Semantic WIP leases

| Lease scope | Gate | State | Freshness | Owner / role | Next event |
|---|---|---|---|---|---|
| `F02.typed_ir.nominal_resolution` | F02 typed_ir | STALE_BASE | RED | #237 implementation | rebase on post-#236 current parser/frontend; strict exact-source + Target replay |
| `F09.effect_fence.v6_fresh_main_fusion` | F09 effect fence | REPAIR_CANDIDATE | GREEN | fresh-main v6 branch | fuse effect sidecar onto current Gate primitive; B1/B2/B3+fork+multi-effect+ClayCode Target matrix |
| `F09.physical_anchor.core_replacement_and_fork` | F09 substrate | FRESH_MAIN_VERIFIED | GREEN | target main promotion | preserve as substrate; do not reopen retired risks without new causal evidence |
| `F13.execution_anchor.descendant_fd_liveness` | F13 recovery | LOCAL_VERIFIED | GREEN | #242/#243 falsifier lane | accepted Target-VPS discriminators; then non-leak invariant or brokered ownership decision |
| `F04.recovery.external_generation_floor` | F04 continuity | REPAIR_CANDIDATE | AMBER | #240 implementation | target recovery regression + fresh-main Gate integration + whole-VM failure-domain decision |
| `F01.self_root.identity_replay_boot` | F01 identity | STALE_BASE | RED | #227 implementation / #231 promotion | dependency-cone refresh then exact-current identity/boot replay |
| `F04.sqlite.storage_safety` | F04 storage | TARGET_VERIFICATION_PENDING | AMBER | #222 implementation | exact-current storage Target receipt -> explicit F04 admission proposal |
| `F13.repo_static_integrity.current_main` | F13 integrity | NEGATIVE_EVIDENCE | GREEN | unassigned | repair path-aware classification + V17 DDL migration boundary, rerun deep-integrity gate |

A second implementation worker in the same lease scope must `JOIN`, `COUNTERTEST`, `SUPERSEDE`, or `WAIT`. Independent failure domains may have independent scopes even inside the same formal subcheck.

## Promotion train — current ranked queue

1. **F09 fresh-main effect-fence fusion** — historical #238 is Target-PASS but ancestry-stale; rebuild the effect sidecar against current process-incarnation Gate instead of cherry-picking stale Gate semantics.
2. **F13 current-main static-integrity repair** — one known current Target integrity failure remains; classify colocated tests correctly and isolate V17 DDL behind explicit migration authority.
3. **F02 typed_ir nominal-resolution replay** — #236 changed the parser substrate after #237 branched; rebase and rerun rather than treating the earlier queue result as credit.
4. **F04 recovery generation floor** — close the already reproduced rollback-resurrection failure domain with exact-current Target evidence.
5. **F04 storage safety** — convert existing storage work into explicit F04 admission if fresh-current evidence holds.
6. **F01 identity/boot** — refresh only after dependency-cone comparison; avoid blind rebase work if current runtime changes are disjoint.

## Diff -> gate compiler

`tools/gateflow.py` + `GATEFLOW_V1_RULES.json` conservatively map changed paths to possible work-package/subcheck surfaces and list evidence templates. Mapping is many-to-many by design: for example a recovery file may affect both F04 continuity and F13 recovery. A match never grants PASS.

## Hard boundaries

GateFlow does **not**:

- change the owner-fixed Frank v0.1 finished contract;
- mutate Frank's Harness;
- silently change workspace percentage;
- authorize final/paid training;
- mint runtime/effect authority;
- treat stale Target PASS as current promotion evidence.

The workspace remains formally ~3.0% until explicit adjudication writes accepted subcheck/gate state. GateFlow's job is to shorten and measure the path from evidence to that adjudication without optimizing away difficult risk discovery.
