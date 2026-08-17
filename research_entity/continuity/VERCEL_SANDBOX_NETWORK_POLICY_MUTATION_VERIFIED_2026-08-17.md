# Vercel Sandbox post-create network-policy mutation — VERIFIED CAPABILITY

Observed: 2026-08-17
Trigger: `go` at 2026-08-17T15:02+07:00
Organ: GPT-5.6 Sol
Classification: **PRIMARY-DOCUMENTATION CAPABILITY VERIFIED / NOT RUNTIME-EXECUTED IN THIS RECEIPT**

## Question

The prepared SQLite remediation for ClayVerse needs a bounded bootstrap phase with package-network access, followed by a fail-closed switch to `deny-all` before exact ClayVerse source binding and regression execution.

The critical discriminator was whether Vercel Sandbox supports replacing egress policy **after** Sandbox creation rather than requiring one immutable creation-time policy.

## Current primary Vercel evidence

Current official Vercel Sandbox documentation explicitly exposes post-create network-policy replacement:

- JavaScript/TypeScript Sandbox API: the formerly named `sandbox.updateNetworkPolicy()` path is documented as deprecated in favor of generic `sandbox.update({ networkPolicy })`.
- Python Sandbox SDK: `update_network_policy(network_policy)` is documented to replace the Sandbox egress policy after creation.
- REST/API SDK: session network-policy update endpoints document full replacement of the current policy, including `allow-all`, `deny-all`, and custom rules.

Primary documentation locations observed:
- `https://vercel.com/docs/sandbox/concepts/persistent-sandboxes`
- `https://vercel.com/docs/sandbox/python-sdk-reference`
- `https://vercel.com/docs/rest-api/sandboxes/update-network-policy`
- `https://vercel.com/docs/rest-api/sdk/sandboxes/update-network-policy`

## Consequence for the SQLite remediation

The following execution design is API-supported in principle:

1. create a bounded non-persistent Sandbox with only the bootstrap network access required for deterministic package provisioning;
2. provision the chosen SQLite-capable distro Python/runtime and verify `import sqlite3` plus exact interpreter/package identity;
3. replace the running Sandbox egress policy with `deny-all`;
4. verify the resulting policy state is actually `deny-all` before target source is admitted/executed;
5. bind exact current ClayVerse source/blob/harness identities;
6. execute the focused regression under `deny-all`;
7. capture stdout + stderr, command, interpreter/package identity, policy transition/result, exit code and stop state;
8. stop the Sandbox in `finally`.

This is preferable to weakening ClayVerse product security or misclassifying the built-in Vercel `python3.13` runtime as SQLite-capable after the observed `_sqlite3` failure.

## Evidence boundary

This receipt verifies **documented platform capability**, not an executed policy transition on this account and not a ClayVerse test PASS.

The exact runtime gate remains open until an actually-started authorized Sandbox demonstrates:

`bootstrap network -> SQLite-capable interpreter preflight -> policy transition -> observed deny-all -> exact current product regression`.

The connected ChatGPT Vercel surface still does not expose direct Sandbox lifecycle actions or the account's remaining included Sandbox allowance. FREE_ONLY therefore still forbids inventing zero-cost eligibility for another run.

No VPS/self-hosted/production-host testing. No Together API. No ACTIVE MicroClay promotion. No owner-gated paid/final training.