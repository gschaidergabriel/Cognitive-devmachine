# H-WP-17 — Owner-fixed target-contract preflight gate

Run: `harness-20260810T2030p0700-chatgpt-secondary-hwp17-target-contract-gate`  
Trigger: `harness`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Program stage: `BASE_CLAYCODE_RELEASE`  
Canonical parent: `r2:04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Result

Built and executed an H1 release-audit preflight gate that rejects a Reference Harness architecture freeze when it does not contain the current 2026-08-10 owner-fixed self.root target semantics.

The gate checks at minimum:

- `target_host == TARGET_VPS`;
- production token API component identity;
- bidirectional `DE_TO_CLAY` / `CLAY_TO_DE` translator component identities;
- proactive/autotelic agency component identity;
- authority-separated web ingress component identity;
- governed Research Entity bridge component identity;
- explicit invariant presence for `self.root`, `CLAYCODE_ONLY`, `TARGET_VPS`, token boundary, proactive agency and `UNTRUSTED_EXTERNAL_DATA`.

## Executed evidence

Local deterministic unit suite: **2/2 PASS**.

Observed 2026-08-09 H1 freeze probe: **BLOCK_AS_DESIGNED** with exit code 1 and three failure classes:

1. `TARGET_HOST_STALE` — observed `UBUNTU_LINUX_DEVELOPER_SYSTEM`, expected `TARGET_VPS`;
2. `OWNER_FIXED_MODULES_MISSING` — token API, both German/Clay translators, proactive agency, Research Entity bridge and web-ingress guard absent from the observed freeze module list;
3. `OWNER_FIXED_INVARIANTS_MISSING` — no explicit current target invariant tokens for self.root, ClayCode-only cognition, target VPS, token boundary, proactive agency and untrusted-web authority.

This is a release-audit conformance result, not target-VPS runtime acceptance.

## Cross-branch fusion

The result is consistent with fresh mesh evidence:

- Frank already produced an executable self.root identity-conformance discriminator and observed expected failure against stale target-repository identity semantics.
- ClayCode WP03 reports that owner-fixed Agency/Web structures fit the current typed-IR surface in the tested slice, while real production fixtures remain required.
- Recent ClayGraph, UnifiedDB, Hyperposition and Emergenz deltas cover Agency/identity/topology/causal surfaces relevant to the same H1 denominator expansion.
- Sibling H-WP-10 effect-authority component was completed immediately before this run and was not duplicated.

Shared ancestry is preserved: these are not counted as independent scientific replications of an owner-fixed target directive.

## Hypothesis / counterhypothesis

**Primary:** an explicit 2026-08-10 compatibility overlay or refreeze that adds the current server/API/translator/agency/web/self.root contracts will make H1 release auditing target-consistent without discarding previously earned H1 component work.

**Strongest counterhypothesis:** the new contracts may already be implemented elsewhere in executable H1 runtime paths and the old freeze is only stale documentation. If so, executing this gate against a newly materialized authoritative freeze generated from current runtime should PASS without substantive runtime redesign.

**Discriminator:** regenerate/materialize the authoritative H1 architecture freeze from current runtime/contracts, run `tools/harness_target_contract_gate.py`, then execute boot/API/translator/Agency/web-ingress/restart fixtures on target-VPS semantics. A PASS requires both structural coverage and runtime receipts.

## Architecture decision

`NO_PROMOTION_YET`.

The old 2026-08-09 freeze remains historical evidence and previously earned component work remains valid where semantics are unchanged. What is refuted is only the assumption that the unmodified old freeze is complete enough to stand as the current owner-fixed H1 release baseline.

## Required next Harness work

1. create a compatibility overlay/refreeze from current owner-fixed directives;
2. include current self.root/TARGET_VPS/API/translator/Agency/Web/Research-DB state and causal edges;
3. feed ClayCode WP03 typed fixtures into H1 and later H2 differential replay;
4. run the new gate on the real repository file in CI/target checkout;
5. execute target-VPS boot/API/auth/translator/Agency/web-ingress/restart/recovery tests;
6. only then continue H-WP-17 toward a release decision.

## Limits

- no target-VPS execution was performed by this run;
- the connected GitHub surface did not expose a local checkout, so the observed old-freeze probe was distilled from source-bound fields returned by GitHub;
- no H1/H2 gate was promoted;
- no paid/final model training was started.
