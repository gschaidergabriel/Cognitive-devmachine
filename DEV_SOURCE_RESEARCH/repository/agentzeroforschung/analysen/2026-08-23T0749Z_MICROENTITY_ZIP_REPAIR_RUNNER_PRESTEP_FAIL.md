# GO — MicroEntity ZIP repair runner failed before steps

Date: 2026-08-23

## Bound state

- canonical research head observed before first write: `2963c8d5714539e09ebedb3651f2ad1a5d411a2e`
- canonical research head rejoined before replication fusion: `862f62bd1f8bcf903f226f241f670002a2a05f79`
- repair PR: `#1232`
- exact repair head: `b458750719b4125121d2c15be122fa2bea71dd24`
- `MICROENTITY_CURRENT.zip` at repair head: still the known truncated 7,515-byte blob `e3eb5d33c70c2c1dc9b03d430b6114a5630d868b`
- manifest contract: exactly 12 required archive members
- independently recorded locally verified target from merged PR #1229: 19,256 bytes, SHA-256 `6aa96f23c1d0874b8cc2c6012a5bad3a59a5428af7660e184cf91d47db968bf0`

## Executable infrastructure evidence — attempt 1

The repair workflow was actually triggered on the exact repair head:

- workflow: `hcu-zip-binary-repair`
- run id: `32619882436`
- conclusion: `failure`
- job: `rebuild`
- job id: `97146343788`
- visible steps: `[]`
- job-log retrieval: unavailable/no log blob

Therefore the deterministic rebuild script itself did **not** execute. This is pre-step runner/admission infrastructure evidence, not a package-content failure and not artifact-repair credit.

## Independent replication — attempt 2

During a later exact user-triggered `go`, the failed job was explicitly re-run through the GitHub Actions API without changing the repair head or workflow logic.

- same workflow run id: `32619882436`
- re-run request: accepted (`success=true`)
- new job id: `97165557382`
- final status: `completed`
- conclusion: `failure`
- visible steps: `null`

The second job again failed before any visible step execution. This independently replicates the control-plane/runner-admission failure on the same exact repair head. It does not exercise the ZIP builder and therefore does not change package-content credit.

## Falsified interpretations

`workflow failure => ZIP rebuild script failed` is false for both observed attempts.

`one transient runner miss explains the blocker` is weakened by the second independent re-run with the same pre-step outcome.

The strongest bound statement is now:

`exact repair head -> two admitted GitHub workflow attempts -> no visible job steps in either attempt -> no rebuilt binary materialized`.

## Coordination / unusual experiment accounting

The re-run is ordinary independent infrastructure replication, not a new product intervention. No upstream `macrocycle_id` was supplied to this worker, so global unusual-experiment uniqueness remains `UNRESOLVED_NO_UPSTREAM_ID` under `GO_MACROCYCLE_IDENTITY_CONTRACT.md`; no post-hoc macrocycle id is invented.

## Promotion rule

PR #1232 MUST NOT merge while the branch still contains the truncated package blob.

Required before promotion:

1. materialize `MICROENTITY_CURRENT.zip` from exactly the 12 versioned `PACKAGE_MANIFEST.json` members;
2. verify exact member set and order;
3. verify ZIP CRC;
4. bind ZIP byte size, SHA-256, Git blob SHA, package-manifest digest, source commit and source tree in `PACKAGE_ARTIFACT_RECEIPT/v1`;
5. verify branch blob differs from the known truncated blob and matches the rebuilt source bytes;
6. remove the temporary write-capable repair workflow before merge;
7. refetch branch and post-merge main and verify artifact/receipt identity.

## Current next discriminator

Do not spend another identical GitHub-hosted runner retry unless runner conditions materially change. Prefer an actually-started authorized zero-cost isolated executor that can materialize the deterministic 12-member ZIP, or a direct repository-object write path that first reconstructs and verifies the exact 19,256-byte source-derived archive.

Package repair grants artifact-integrity credit only. It grants no runtime/model/HCU/J-Space/GWT or whole-product credit.

FREE_ONLY remains hard; no provider execution, paid action, Together use, VPS/self-hosted/production test, model execution or training was used in this replication.
