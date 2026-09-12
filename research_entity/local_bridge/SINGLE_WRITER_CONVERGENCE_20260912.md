# Local bridge host-effect convergence — 2026-09-12

Status: **INTEGRATION_BLOCKER / NO SERVICE MUTATION YET**

## Observed executable evidence

Real-host forensics on `ai-core-node` observed two simultaneously active user services:

1. `clay-local-bridge.service`
   - `ExecStart=/usr/bin/python3 /home/ai-core-node/.local/share/clay-local-bridge/bin/daemon.py`
   - SHA-256 `22d56fddd760bbda096e8cd58b8d826dbfbfd7df46155a62ef98f64d5ecdbacf`
   - `Restart=always`
   - generic branches `chatgpt-local-control` / `chatgpt-local-results`

2. `frankenstein-local-bridge.service`
   - `ExecStart=/usr/bin/python3 /home/ai-core-node/.claude/star/local_bridge_daemon.py`
   - SHA-256 `836173805c8919492c1d52540c50f8b97dfd5beb8d02196d5630dbce52da342f`
   - `Restart=on-failure`
   - machine-specific branches `chatgpt-local-ai-core-node-control` / `chatgpt-local-ai-core-node-results`
   - explicit machine/owner binding

Both use their own SQLite `done` identity machinery. The machine-specific daemon has no observed cross-daemon lock. The generic daemon's static keyword hit on `lease` is explained by Git `--force-with-lease`; it is not evidence of a host-effect lease.

The generic daemon also exposes a material crash window in the observed source ordering: result synchronization/receipt publication occurs before the command is inserted into its durable `done` table. A crash in that interval can leave a published effect result without durable replay suppression.

The machine-specific result checkout was also observed dirty while bridge work was active, with uncommitted logs/receipts/commands. That is projection/commit-latency evidence, not by itself proof of lost results.

## Corrected risk classification

The two daemons do **not** poll the same Git control branch, so simultaneous process existence alone does not prove duplicate execution of one command.

The real shared boundary is lower:

> Both daemons are effect-capable on the same physical host and currently have no proven shared host-effect authority.

Therefore two separate command fabrics can independently issue valid-looking mutations against the same live avatar/files/services. Per-daemon `done` databases cannot prevent this cross-fabric race.

This is the exact ChatGPT + Frank coordination boundary: they may remain two workers/fabrics, but live host effects must serialize through one physical-host authority.

## Mandatory invariant

`ONE PHYSICAL HOST -> ONE LIVE/SYSTEM EFFECT CRITICAL SECTION`

This does **not** require one daemon process.

Allowed concurrently:

- `READ_ONLY` probes;
- `SCRATCH_ONLY` experiments confined to explicit scratch roots;
- independent repository research/build work.

Serialized through the shared host fence:

- `LIVE_MUTATION`;
- `SYSTEM_MUTATION`;
- any command whose effect class cannot be proven narrower.

## Reuse current Clay effect semantics

Do not create a competing product effect model. Reuse the existing Clay invariants:

- command/effect identity is immutable;
- stale generation or stale subject fails closed;
- leases are checked at the effect boundary;
- unknown effect outcomes are not blindly replayed;
- execution-body return is not equivalent to verified external result.

`host_effect_fence.py` in this branch is a bridge-coordination adapter around those semantics, not canonical project truth.

It adds the missing cross-daemon physical-host boundary:

1. shared `flock` for live/system effects;
2. shared SQLite coordination journal;
3. `command_id + command_sha256` immutability;
4. exact path/hash subject preconditions after lock acquisition;
5. `BODY_RETURNED_UNVERIFIED` after normal effect-body return;
6. independent readback digest required for `VERIFIED_SUCCEEDED`;
7. exact replay suppression only after verified success;
8. `UNKNOWN` crash/exception state blocks replay until explicit reconciliation;
9. scratch-root confinement for parallel scratch work.

## Integration target

Both bridge daemons should eventually call the same installed HostEffectFence path for effect-bearing commands.

A safe schema successor should add, at minimum:

```text
effect_class: READ_ONLY | SCRATCH_ONLY | LIVE_MUTATION | SYSTEM_MUTATION
subject_preconditions: [{path, sha256}, ...]
scratch_root: <absolute path or null>
touched_paths: [<absolute path>, ...]
```

For legacy commands whose `op=exec` can mutate arbitrary host state, `effect_class` must not silently default to READ_ONLY. Until callers explicitly classify them, treat them as effect-unknown for promotion-bearing use.

## Required executable gate before adoption

The source in this branch is **SOURCE_READY, RUNTIME_UNVERIFIED**. Do not install it on the host or merge it as authority merely because the design is plausible.

Required tests:

1. READ_ONLY leaves the effect journal untouched.
2. SCRATCH_ONLY rejects a touched path escaping its declared scratch root.
3. live subject hash drift fails before effect body execution.
4. one live effect excludes a concurrent live effect from the other bridge/process.
5. normal effect-body return leaves `BODY_RETURNED_UNVERIFIED` and blocks the next live effect.
6. independent readback moves exactly that command to `VERIFIED_SUCCEEDED`.
7. exact command replay after verified success is suppressed with zero second effect.
8. same command ID + different content hash fails closed.
9. exception/crash window becomes `UNKNOWN` and cannot replay.
10. startup converts abandoned PREPARED/RUNNING rows to UNKNOWN.
11. explicit reconciliation is required before retry.
12. both current daemon integrations pass the same gate while using their existing separate branch fabrics.

Only after those pass should daemon/service integration occur.

## Service topology after convergence

Do **not** stop a daemon merely to achieve cosmetic single-process topology.

Two active daemons are acceptable if:

- their Git fabrics remain distinct where intended;
- both share the same physical-host effect fence;
- both preserve exact machine/owner/command attribution;
- result publication remains branch-correct;
- live/system effects cannot overlap;
- unknown outcomes block both fabrics.

If a daemon cannot be adapted to the shared fence safely, then demote that daemon to read-only/standby or retire it. That choice should follow executable evidence, not naming convention.

## Runtime-credit fence

Until the cross-daemon host-effect discriminator closes:

- existing historical receipts remain evidence at their exact scope;
- new read-only/scratch local results remain usable at their exact scope;
- irreversible/live promotion must not rely on independent per-daemon idempotence alone;
- canonical-eye live installation remains blocked;
- body/depth-warp scratch-runtime work may continue.

## Current bounded avatar consequences

Existing positive evidence is preserved:

- canonical eye HTTP serving route is byte-bound to the masked Relief2 asset;
- deterministic eye semantic-shadow build passes;
- isolated expression eye compositing passes;
- body AMD/WebGL runtime/cadence evidence passes at bounded scope;
- body final-display signal sweep selected scale `4` as a measurable low-amplitude candidate;
- depth-warp `A=1.00` has the stronger current mechanical envelope; `A=1.25` fails five roll positions;
- live `buehne.html` remains at SHA-256 `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e` in the latest bound avatar receipts.

Still open before canonical-eye live promotion:

1. robust special-expression blink runtime discriminator without CDP transport invalidity;
2. matched/frozen canonical-eye A/B visual discriminator;
3. executable shared host-effect fence gate and integration into both effect-capable bridge paths.

No whole-avatar, GRID10/GWT/J-Space, effect, training, or whole-product credit is minted by this checkpoint.
