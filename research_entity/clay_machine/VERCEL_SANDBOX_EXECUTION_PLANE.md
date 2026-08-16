# Vercel Sandbox execution plane for Clay Machine / EntityOS

Status: CANDIDATE EXECUTION INFRASTRUCTURE
Date: 2026-08-16
Program: CLAYVERSE_CLAY_MACHINE_ONLY

## Boundary

Vercel Sandbox is an isolated build/test/experiment substrate for the Clay Machine. It is **not** ClayCode language authority, VM semantic authority, or a substitute for the one-file `EntityOS` release artifact. Host/runtime behavior is evidence only for the exact exercised path.

The active program requires build validation, tests and experiments to run in isolated sandboxes only. Vercel Sandbox is therefore a direct fit for the current execution policy and for the preserved CM-07 exact-head execution blocker.

## Verified platform capabilities relevant to EntityOS

Current official Vercel Sandbox documentation plus the supplied `vercel/sandbox` source package (`@vercel/sandbox` 3.0.0) support:

- isolated microVM sandboxes;
- named persistent sandboxes with `Sandbox.get`, `Sandbox.getOrCreate`, automatic filesystem snapshots and resume;
- `snapshotExpiration: 0` for no snapshot expiration and bounded `keepLastSnapshots` retention;
- manual snapshots, snapshot trees and rollback through `currentSnapshotId`;
- sandbox forks that inherit source snapshot/config and can be overridden for experiments;
- ephemeral/non-persistent sandboxes for fresh acceptance/build runs;
- VCR/managed images, including Ubuntu-based images and digest-pinned image references;
- up to 15 published ports per sandbox;
- direct command execution, detached commands, log streaming, interactive/PTy-capable sessions where enabled;
- file read/write/download APIs and CLI copy operations;
- persistent sandbox drives for large caches/data (default maximum documented as 100 GiB unless configured lower);
- explicit network policies: allow-all, deny-all, domain/CIDR allowlists, and HTTP header injection rules;
- per-session and cumulative CPU/runtime/network-transfer observability;
- Linux user/group isolation and shared group directories for multi-agent execution;
- Workflow serialization for Sandbox/command objects across durable Vercel Workflow steps;
- Vercel OIDC authentication in deployed Vercel Functions, avoiding a long-lived Vercel access token in the Sandbox VM.

Current SDK source also documents these resource limits for the supplied 3.0.0 tree: 4 vCPU Hobby, 8 vCPU Pro, 32 vCPU Enterprise; 2048 MiB RAM per vCPU; maximum single-session duration 24 h on Pro/Enterprise and 45 min on Hobby. Persistence across sessions must therefore be implemented by named identity + snapshots/resume, not by claiming one immortal process.

## EntityOS topology

### 1. Canonical persistent cache/baseline sandbox

Name: `clay-entityos-matrix` (configurable).

Purpose:
- warm dependency/build cache;
- retained source-independent tooling;
- reproducible checkpoint lineage;
- long multi-step work continued across sessions.

Policy:
- persistent;
- digest-pinned VCR image for canonical evidence;
- network `deny-all` by default and after every resume;
- bounded no-expiry snapshot retention;
- session/cumulative usage captured as receipts.

### 2. Fresh ephemeral acceptance sandboxes

Purpose:
- prove clean-environment build/run behavior;
- CM-PORT copy-and-run validation;
- reproducibility builds;
- exact PR/commit regression execution;
- crash/restart and negative-path tests without contaminating cache state.

Policy:
- non-persistent unless a failure checkpoint is explicitly retained;
- created from the same digest-pinned image or a declared test image;
- source bytes staged with exact SHA/tree/archive provenance;
- deleted after evidence extraction.

### 3. Forked counter-reality sandboxes

Purpose:
- GRF hypothesis/counterhypothesis discrimination;
- lesion/ablation experiments;
- order-reversal/fusion tests;
- candidate-vs-baseline tests from one identical checkpoint.

Policy:
- fork from an explicit retained checkpoint;
- unique bounded names/tags;
- no canonical promotion from a fork without comparing against its parent checkpoint;
- cleanup mandatory after evidence is captured.

### 4. Multi-agent sandbox users

Use Linux users/groups inside one sandbox only when simultaneous researcher/builder/reviewer execution is useful. Private home directories isolate worker scratch state; `/shared/<group>` carries deliberately shared evidence. This is an execution-isolation mechanism only and must not be confused with Clay semantic modules or authority.

## Direct mapping to current Clay Machine gates

- **CM-07 Environment/stdlib/import semantics:** highest immediate value. Run preserved exact head `07f0bf7bc19e398f4820cd346a58190f98e596c6` in a real actually-started Vercel Sandbox to replace the current billing-blocked runner state with isolated execution evidence.
- **CM-PORT:** create a fresh ephemeral Ubuntu-compatible sandbox, upload/copy only the one-file `EntityOS`, execute it without repository checkout/developer runtime, move/rename/restart and verify provenance.
- **CM-TERM:** exercise direct Linux process/PTY/stdin/stdout/stderr behavior inside an isolated sandbox, including timeout/signal/failure controls; sandbox behavior is host evidence, not Clay semantic authority.
- **CM-DATA:** use file/stream APIs and local loopback processes for measured byte ingress/egress, copy count, hashing, backpressure and latency probes.
- **CM-NET:** use explicit temporary network policies to test real DNS/TCP/TLS/HTTP once canonical Clay effects exist, then force `deny-all` for offline regression/build phases.
- **CM-VIS/CM-AUDIO:** published ports and binary file/stream transfer can support headless sinks and concrete adapters without requiring the sandbox to define media semantics.
- **CM-10 Recovery/observability:** snapshot lineage, rollback, session history, CPU/network usage and bounded artifact digests provide infrastructure evidence for failure/recovery tests.

## Private-source staging rule

Do not put GitHub credentials in shell command arguments, Git config, sandbox environment variables, files, snapshots or receipts.

Preferred path:
1. Vercel Function holds a read-only GitHub credential in Vercel Sensitive Environment Variables.
2. Function verifies the requested repository and full commit SHA against an allowlist.
3. Function fetches commit metadata/archive server-side.
4. Function records requested SHA, resolved SHA/tree and archive SHA256.
5. Function uploads only source bytes into the target sandbox.
6. Sandbox extracts/runs offline.

Vercel network credential injection may be used later for narrowly scoped outbound requests, but server-side source staging is easier to audit for canonical exact-head tests.

## Deployment gate

The Vercel execution plane is not VERIFIED until all of these are real, actually executed results:

1. dependency lockfile generated;
2. `npm ci` succeeds;
3. offline unit/mock tests succeed;
4. TypeScript check succeeds;
5. Next/Vercel build succeeds;
6. VCR image built and immutable digest recorded (or a declared managed digest used for a non-canonical preflight);
7. Vercel Preview deploy succeeds;
8. `/healthz` succeeds;
9. `/mcp` rejects missing/wrong bearer;
10. MCP initialize/discover/tools-list succeeds with correct bearer;
11. Sandbox create/get/resume/checkpoint/rollback executes for real;
12. preserved CM-07 exact-head test actually starts inside Vercel Sandbox;
13. one clean ephemeral EntityOS build/run path executes;
14. artifact download is SHA256-verified outside the sandbox.

Until then the execution plane remains CANDIDATE/TESTING and cannot promote whole-machine PASS.
