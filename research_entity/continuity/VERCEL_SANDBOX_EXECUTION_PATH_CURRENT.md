# Vercel Sandbox execution path — CURRENT

Status: **CURRENT BRIDGE CONFIRMED / CLAYVERSE SANDBOX ADMISSION PASS / PRIVATE-SOURCE CREDENTIAL BLOCKED**  
Observed: 2026-08-17 19:27 +07:00

## Current truth

Do **not** infer `Vercel Sandbox unavailable` because the connected ChatGPT Vercel connector does not export direct `sandbox.create` / `sandbox.exec` lifecycle actions.

The authorized execution bridge is confirmed and has actually started Vercel Sandbox microVMs:

`Dr.-Unterweger Git preview -> Vercel build orchestration -> VERCEL_OIDC_TOKEN -> @vercel/sandbox -> Sandbox.create -> runCommand -> stop`.

The Vercel Preview/build machine is orchestration only. Runtime credit exists only for behavior actually observed at the admitted isolated boundary, and product-runtime credit requires product assertions to execute.

Canonical staging project:
- repository: `gschaidergabriel/Dr.-Unterweger`;
- retained controller: draft PR **#810**;
- Vercel project: `dr-unterweger`;
- project id: `prj_ifIgM9X7jqIQS8mNIGllImziePPG`.

VPS, self-hosted and production-host testing remain forbidden. Together remains forbidden.

## Exact current ClayVerse execution closure

The currently observed admitted closure is execution provenance over Research `main` plus the retained #611 and fused #622 execution-relevant bytes:

- Research base: `f7eb4df7600b0f4de1a6381a04acf5d1057d8f9b`;
- closure commit: `5e5adce0591058608bbd7381ecf570a39b282f0d`;
- closure tree: `1e02285d77b08e6edd86f9017d0ceac5db262cf2`;
- #611 terminal blob: `c185009f8af84e1288747d8352645777a36b2053`;
- #611 focused-test blob: `b6bb645dd07645f21ca2e5574f8392c9f13beafc`;
- #622 generator-workflow blob: `ad34476c0092b7e724240c927a7cb14858d1a8dc`;
- #622 source-binding-test blob: `ed77f5c9446295fa973512ddf7e9d11ea3292010`.

This closure is not a second product authority. Later Research documentation/receipt commits do not retroactively change its observed bytes. Before the next real compute, refresh and rebind once to the then-current canonical Research/#611/#622 identity.

## Current executable evidence

### First admitted current-closure run

- PR810 controller commit: `5d89ebb4d7a15c679a6c37861fb3a1352cc812df`;
- Vercel deployment: `dpl_21efibLYnww6hhrEMp5SAh6enCsQ`;
- Vercel build started, cloned exact controller source, installed dependencies and entered `npm run vercel-build`;
- guard v3 admitted retained-runner source/provenance markers;
- current-target patch v4 rebound the runner to closure `5e5adce…` / tree `1e02285d…`;
- `Sandbox.create` returned `sandbox_admission=PASS_CREATED`;
- execution then failed closed before private-source fetch because `GITHUB_READ_TOKEN` was absent;
- `source_stage=BLOCKED_MISSING_GITHUB_READ_TOKEN`;
- error: `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`;
- Sandbox stopped successfully;
- `source_runtime_credit=0`; `oci_runtime_credit=0`.

Receipt:
`the artefact/receipts/2026-08-17_GO_1924_PR810_SANDBOX_ADMISSION_PRIVATE_SOURCE_TOKEN_BLOCK_GPT56SOL.json`.

### Replicated and hardened current-closure run

Strongest directly observed replication:

- PR810 controller commit: `2e5505983172e582a50f4f72bebd561bc650ff5a`;
- Vercel deployment: `dpl_7BkVnngPJUPiVyrqwFarGFZDevAG`;
- guard v4 admitted the exact retained-runner Git blob `1298ca8002704414f86cd0c036d44e5b32be2918` plus existing provenance markers;
- current-target patch v5 retained closure `5e5adce…` / tree `1e02285d…`;
- Sandbox lifetime was explicitly expanded to `2700000` ms above the retained explicit-step ceiling `2490000` ms;
- `Sandbox.create` again returned `sandbox_admission=PASS_CREATED`;
- the same fail-closed boundary fired before private-source fetch: `BLOCKED_MISSING_GITHUB_READ_TOKEN` / `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`;
- Sandbox stopped successfully;
- `source_runtime_credit=0`; `oci_runtime_credit=0`.

Receipt:
`the artefact/receipts/2026-08-17_GO_1925_PR810_SANDBOX_CREDENTIAL_BLOCK_REPLICATION_GPT56SOL.json`.

An intermediate guard-v4 replication is also preserved at deployment `dpl_HWjU1DGTiXaMcYD4mT5waFsT53Us` with its bounded receipt.

Current observed PR810 head after the strongest measured run is `02f9157a15485b49f96dd4d4b20201fe148db710`; it adds a deterministic timeout-budget fence test. Do not transfer runtime credit from `2e550598…` to this newer source-only head unless it is separately executed and bound.

## Current classification

`SANDBOX_ADMISSION_PASS_PRIVATE_SOURCE_CREDENTIAL_BLOCK_REPLICATED`

The earlier classifications `FREE_DAILY_PREVIEW_DEPLOYMENT_CAP_REACHED` and `upgradeToPro=build-rate-limit` are **historical provider observations**, not the current ClayVerse execution blocker. Current admitted runs prove that Vercel build/Sandbox admission was available for the exact bound closure at the times above.

This is **not** ClayVerse TEST_FAIL and **not** whole-product PASS.

The current runs stopped before:
- private Research source fetch;
- private EntityOS source fetch;
- EntityOS reconstruction/reproduction;
- full exact source regression;
- OCI build;
- image digest/dependency inventory;
- in-image #611 tmux behavior;
- hardened `service --once` product assertions.

Therefore source/OCI runtime credit remains zero.

## Credential boundary

The next prerequisite is precise:

**Provision `GITHUB_READ_TOKEN` as an appropriate sensitive Vercel Preview build credential for the retained PR810 branch.**

Security law:
- credential remains in the Vercel host/build orchestration process;
- never commit it to GitHub;
- never print/log its value;
- never forward it into the disposable Sandbox;
- only source bytes whose exact commit/tree identity was verified host-side may cross into the Sandbox;
- missing/uncertain credential continues to fail closed.

The current connector surface does not expose Vercel project-environment-variable mutation, so this session cannot safely provision that credential itself.

## Next accepted execution sequence

After credential provisioning:

`refresh current Research main/#611/#622 -> rebind retained PR810 once -> fail-closed guard/current wrapper -> Sandbox.create -> host-side exact private Research + EntityOS verification -> stage only verified archive bytes -> reconstruct/attest/reproduce exact locked EntityOS -> full exact source regression -> build exact ClayVerse OCI -> capture image digest + APT/tmux/Claude/Python identities -> deny network -> run in-image #611 double-reapply/full policy attestation for gabriel and andreas -> hardened service --once + adjacent regressions -> execute/materialize/verify #622 canonical Python hash lock and selected-wheel manifest -> switch Docker to --require-hashes only after accepted lock evidence -> rebuild/rebind exact image -> continue native-Claude, startup/readiness, Clerk/browser/PTY, managed-hook lifecycle, persistence/recovery and dual-session concurrency/global-generation gates`.

Do not create a parallel controller, generic host execution path, or second EntityOS staging authority merely to bypass the credential boundary.

## Historical runtime note — bare Python 3.13 / SQLite

Earlier MicroClay diagnostics on Vercel's bare `runtime: 'python3.13'` reached real Sandboxes but failed while importing Python `sqlite3` with:

`ModuleNotFoundError: No module named '_sqlite3'`

That historical result is a runtime dependency failure before product assertions, not a MicroClay semantic failure, and does not transfer to current v3 product claims. UnifiedDB/SQLite-dependent product validation should use the exact ClayVerse OCI candidate or another admitted digest-bound SQLite-capable image.

## Worker law

For every Clay/ClayVerse worker:
- `DIRECT_CHATGPT_MCP_SANDBOX_LIFECYCLE_NOT_EXPORTED` != `VERCEL_SANDBOX_UNAVAILABLE`;
- distinguish provider/Preview admission failure from Sandbox admission, runtime dependency failure and product semantic failure;
- bind exact source/artifact/image identity, commands, exit codes, diagnostics, network policy and Sandbox stop state;
- a Sandbox start alone does not mint ClayVerse product-runtime PASS;
- an absent private-source credential after Sandbox admission is a credential/pre-source blocker, not TEST_FAIL;
- refresh fast-moving Research/PR identities before the next admitted compute;
- stop bounded Sandboxes after use;
- no VPS/self-hosted/production testing;
- Together forbidden.

## Preferred operational wording

`Vercel Sandbox execution path CONFIRMED via Git-preview orchestration + @vercel/sandbox/OIDC. For the exact current ClayVerse closure, Sandbox.create has succeeded repeatedly. The current blocker is not Sandbox/provider admission but the absent host-side GITHUB_READ_TOKEN required to fetch and verify the private Research/EntityOS sources before they enter the disposable Sandbox. Source/OCI product-runtime credit remains zero because execution stops before source staging and product assertions. Provision the sensitive Preview credential without forwarding/logging it, refresh/rebind exact source once, then continue the retained OCI acceptance batch.`
