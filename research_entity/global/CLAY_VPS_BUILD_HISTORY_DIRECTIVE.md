# Clay VPS Build History Directive

**Status:** PROJECT-OWNER FIXED OPERATION LAW
**Owner instruction date:** 2026-08-10
**Scope:** all Research-Entity-created or materially changed VPS builds, experiments, services, model variants, benchmarks, deployments, generated code/configuration and runtime artifacts

## Fixed rule

Everything materially built, changed, executed or deployed by the Research Entity on the VPS must leave a **versioned metadata/provenance history in a dedicated local Git repository on the VPS**.

Default history repository:

`/srv/clay-history`

This repository is an append-only operational/build ledger. It complements source repositories and Clay UnifiedDB; it is not a replacement for either.

## Required build/event metadata

Every material event must record as applicable:

- stable event/build id;
- timestamp and monotonic ordering metadata;
- actor/provenance (`clay-vps-mcp`, worker/request id where available);
- action kind;
- working directory and target component;
- command argv without secret values;
- source repository identity, branch and exact Git HEAD when applicable;
- dirty working-tree state/diff hash when applicable;
- parent build/event commit;
- input artifact/model/config hashes;
- output artifact/binary/model/log hashes where observable;
- model and mmproj identity for inference/benchmark work;
- dependency/tool/runtime versions where material;
- exit/result state, latency/duration and error class;
- service/process identity for persistent processes;
- benchmark/test identifiers and receipt references;
- deployment release identity and rollback predecessor;
- links/references to corresponding Clay/UnifiedDB/ClayGraph/research receipts when available.

## Large-artifact law

Large artifacts such as GGUF/model weights, datasets, caches and binaries must not be blindly duplicated into Git history.

Store:

`content address (SHA-256) + absolute/semantic path + size + mtime/build identity + provenance`

Small textual receipts/manifests may be copied into the history repository when useful.

## Secret law

Never commit:

- `CLAY_MCP_TOKEN`;
- `FRANK_API_TOKEN`;
- SSH private keys;
- access tokens/API keys;
- cookies/session credentials;
- secret environment values.

Only secret **names/presence state** may be recorded when needed for reproducibility.

## Git-history law

The history repository itself is append-only under normal Research-Entity authority:

- no `reset --hard`;
- no history rewrite/rebase;
- no force push;
- no commit deletion;
- no destructive cleanup;
- no rewriting a prior event to make a failed build disappear.

Corrections are new commits referencing the superseded/incorrect event.

Negative builds, failed tests, crashes and rejected candidates remain part of history.

## Automatic capture

`infra/clay_vps_mcp` must automatically mirror its mutating/execution audit stream into this Git history repository. The history recorder must preserve an independent cursor so crash/restart can resume without losing or duplicating events. Each event is content-addressed and idempotently materialized.

For long-running Research-Entity-owned processes, the history recorder should capture both START and terminal/observed completion state when available.

## Relationship to Frank 24/7 target

Every deployed Frank instance must be traceable to:

- exact service release/build event;
- source commit(s);
- model hash;
- mmproj/vision hash where applicable;
- runtime/config hash excluding secrets;
- API surface version;
- health/restart/recovery receipts;
- predecessor deployment.

This makes the currently running Frank answerable as:

`which exact build is live, from what source/model/config, what changed from its predecessor, what tests passed, and how to roll back?`

## Compact invariant

`EVERY_MATERIAL_VPS_EFFECT -> VERSIONED_PROVENANCE_COMMIT`

and

`FAILED_BUILD != ERASED_HISTORY`
