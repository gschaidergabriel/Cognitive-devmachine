# GO effect-authority receipt-integrity discriminator and repair lane

Date: 2026-08-11T15:13Z+
Origin actor: chatgpt-secondary
Provider: OpenAI
Model: GPT-5.6 Sol
Trigger: exact `go`
Research entity: Clay (`frank-project-global-research-entity`)
Research subject: Frank

## Scope and authority boundary

This run is evidence-plumbing research/build/test work. It does not change Frank effect-authority policy semantics, does not perform an external effect, does not mutate canonical Frank runtime state, does not authorize final/paid training, and does not grant Frank/self.root Harness mutation authority.

Exactly one bounded out-of-box experiment was consumed in this invocation:

`LATE_POLICY_FAILURE_RECEIPT_BLACKHOLE`

Any later reuse of the same exact discriminator in this lane is an ordinary repair regression, not another OOB experiment.

## Fresh state / non-overlap

Working repository: `gschaidergabriel/Dr.-Unterweger`.

The run first merged target-verified PR #309 into main as merge commit:

`cd5cec575282eb8bd81a8f8e5a9116f47141abf0`

PR #309 repaired the V17 candidate gate so named checks are computed from observed runtime behavior and FAIL receipts survive named gate failures. Its own report explicitly identified the same eager-failure anti-pattern as still present in:

`runtime/frank_effect_authority_v1/target_vps_probe.py`

Fresh open-work search found no active worker repairing that exact probe at the time this lane was claimed.

## Hypothesis

The direct Frank-v0.1 effect-authority target probe preserves a structured diagnostic receipt when a late observed invariant fails.

## Strongest counterhypothesis

`check()` writes FAIL only into an in-memory dict and immediately raises `AssertionError`; because result serialization occurs after all checks, a late real check failure destroys the structured receipt even though earlier evidence has already been collected.

## Single OOB intervention

Branch:

`chatgpt/go-effect-receipt-blackhole-oob-20260811`

Draft PR:

`Dr.-Unterweger#344`

Initial discriminator head:

`6ee4cbf6e9cb38bac9f8c5a023da810a05d4b366`

The discriminator first runs the untouched real target probe against the real semantic source `claycode/frank_effects.clay` and requires a normal PASS receipt. It then changes only the test-harness `check` function for one late named observation:

`destructive_false_allow_rate_zero_before_confirmation`

No EffectGate decision rule, semantic source, canonical DB state, or external effect is changed.

## Accepted-target OOB receipt

GitHub Actions run: `31505700016`
Job: `93826599489`
Exact tested head: `6ee4cbf6e9cb38bac9f8c5a023da810a05d4b366`
Runner: `clay`
Machine: `digital-retina`
OS/kernel: Linux / Ubuntu kernel `6.8.0-117-generic`
Python: `3.12.3`

Baseline:

- return code: 0
- structured receipt: present
- status: `PASS_DIRECT_FRANK_V0_1_EFFECT_AUTHORITY_POLICY_MATRIX`

Injected late failure:

- observed error: `destructive_false_allow_rate_zero_before_confirmation`
- escaped as: `AssertionError`
- structured FAIL receipt: absent
- classification: `SUPPORTED_RECEIPT_BLACKHOLE_ON_LATE_OBSERVED_FAILURE`
- policy mutated: false
- semantic source mutated: false
- canonical state mutated: false
- external effect performed: false

Exact content identities:

- target probe SHA-256: `a548a00077c1c6a40028e6a4a7c93a7a8eaee678bc21e6933a29dc9be493a0d5`
- semantic source SHA-256: `fb1e7316f0987e917da4385e50dd5b1037a02500c2cdbbb2266f36a74bfd0d88`

Resource shadow:

- wall: 0.21 s
- user CPU: 0.20 s
- system CPU: 0.01 s
- max RSS: 21,120 KiB

## Result

The hypothesis was refuted for the measured pre-repair target probe. The strongest counterhypothesis is supported for the exact named-check failure channel.

This is a reporting/evidence-integrity defect. It is not evidence that the underlying effect-authority policy allows an unsafe effect.

## Ordinary repair candidate

Repair commit on PR #344:

`52b86d1b4d3c70698567362b074148c6b4649556`

Regression-hardening commit:

`96f3e924f04a3181258ff2ad365ba35275384e0f`

Repair delta:

- observed named check failures are accumulated instead of raised out of `check()`;
- semantic marker presence becomes a named observed check instead of a bare pre-receipt assertion;
- PASS/FAIL status, counts and `failed_checks` are serialized for named observed gate failures;
- healthy exit remains 0; any named check failure returns exit 1;
- receipt schema advances to 1.1;
- the receipt explicitly does NOT claim guaranteed serialization for arbitrary unexpected runtime exceptions.

The ordinary repair regression uses the same already-consumed discriminator and accepts repair only if all are true:

1. untouched baseline remains PASS with rc=0;
2. exact forced named check yields rc=1;
3. no `AssertionError` escapes;
4. structured receipt exists;
5. receipt status starts `FAIL_`;
6. `failed_checks` contains the exact forced check;
7. `tests[forced_check] == FAIL`.

At report creation time the exact repaired target run is queued on the shared self-hosted runner. Repair promotion remains pending that target receipt; this report must not be read as target-verified repair closure until a later durable delta says so.

## External knowledge refresh used for routing, not for this defect claim

The same GO refreshed primary SQLite and Python startup documentation to avoid duplicating the active storage lane. Current SQLite documentation places the WAL-reset fix boundary at 3.51.3+, while Python documentation distinguishes isolated mode `-I` from `-S` site disabling. Concurrent storage workers already own those discriminators/repairs, so this worker did not duplicate them.

## Architecture consequence

For executable evidence gates, a named observed invariant must not be considered measured only because execution reached a later PASS dictionary. Material gates should preserve a structured FAIL receipt for expected/named failure channels and use exit status as the workflow gate. Unexpected runtime crashes remain a separate continuity/recovery obligation rather than being silently claimed as covered.

## Next falsifier / handoff

Required before this lane can close:

- accepted-target run on exact repair head;
- healthy baseline PASS/rc0;
- same forced late check produces structured FAIL/rc1 with exact failed-check identity;
- no overlapping mainline edit to the same probe before merge;
- merge only after those conditions remain true on current main compatibility.

No whole Frank-v0.1 acceptance is claimed.
