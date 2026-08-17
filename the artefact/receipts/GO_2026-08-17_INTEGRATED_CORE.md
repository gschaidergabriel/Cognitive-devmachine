# GO receipt — integrated ClayVerse core — 2026-08-17

## Scope

Base research main: `16ce79adde5e47f37d98c806386352bb57a1f8c0`.

This cycle created the first executable integrated product candidate under `the artefact/`. It ports the useful UCM2 event-authority mechanism into the new ClayVerse product path rather than promoting UCM2 as a separate target.

## Candidate contracts exercised

- one ClayVerse identity shared by sessions A and B across restart;
- persistent memory in one SQLite/WAL UnifiedDB-style authority;
- hash-chained, monotonic event stream with tamper rejection;
- ClayGraph as a rebuildable projection from authoritative `LINK` events;
- explicit argv process effect with `shell=False`;
- causal order: request -> outcome -> verification -> causal re-entry -> credit update;
- failed verification produces no credit;
- durable `PENDING` effect reservation before execution so ambiguous crash recovery fails closed instead of replaying an external effect;
- always-on manager integrity loop is the default container process.

## Exact isolated-local evidence

Authorized isolated local environment: Linux x86_64, Python 3.13.5.

Exact candidate blob IDs used for the final regression:

- `the artefact/clayverse.py`: `2b2075506c9d5b265010a3c81f58d85d71fbc303`
- `the artefact/tests/test_clayverse.py`: `089b3c695d4201c054d507860b20e10a55d02c9c`
- `the artefact/Dockerfile`: `3caebb58c615504b232761d09ffdcc7684be93a4`
- `the artefact/README.md`: `763648c8f47995f107b6284fe339a925796bd2ca`

Command:

`python3 -m unittest discover -s tests -v`

Result: **9/9 PASS**.

Built-in selftest also passed with identity `CLAYVERSE`, two sessions (`A`, `B`), persisted `bootstrap=alive` memory, a derived `HAS_MEMORY` graph edge, and a verified real `/bin/echo clayverse` process effect.

## Exactly one unusual experiment

`EFFECT_ID_INTENT_COLLISION`:

1. execute and verify effect id `collision` with argv `/bin/echo first`;
2. reuse the same authority key with a different argv that would create a marker file;
3. expected: fail closed before second host execution;
4. observed: `EFFECT_ID_CONFLICT`, epoch unchanged, marker file absent.

The later crash-window discriminator is regression-only: a persisted `PENDING` reservation was reopened after restart and rejected with `EFFECT_RECOVERY_REQUIRED`; it did not execute a second unusual intervention.

## Adversarial finding repaired in-cycle

The first green version committed `EFFECT_REQUEST` before host execution but did not reserve the effect id durably until successful completion. A crash after host execution but before result persistence could therefore replay the effect after restart. The final candidate repairs this by reserving `PENDING` before execution and refusing automatic replay of ambiguous pending effects.

## Tooling boundary

No VPS/self-hosted/production-host testing was performed. No Claude Code assistance was used. Together was not used.

The available Vercel connector in this session exposed deployment/project/log/documentation operations but no executable Vercel Sandbox start/run surface. The isolated local test environment permitted by `AGENTS.md` was therefore used for executable evidence.

No Docker/Podman/Buildah/nerdctl/skopeo/umoci binary was available in the isolated local environment, so the Dockerfile was not image-built in this cycle. Source/runtime tests are not a whole-container PASS.

## Acceptance

Candidate status: **IN_PROGRESS**.

Still open: exact OCI image build/run evidence, Clerk boundary, Hyperposition/GWT integration, full ClayCode/EntityOS substrate integration, controlled network/data/visual/audio surfaces, inference-engine integration, stronger external durability/attestation, portability/resource tests, and final deployment acceptance.

This receipt does not claim whole ClayVerse PASS.
