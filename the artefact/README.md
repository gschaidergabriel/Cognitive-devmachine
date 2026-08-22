# the artefact — Multi-use Mini Entity pipeline all-in-one

`the artefact/` is the canonical product workspace for the owner-directed Mini Entity program.

The active target is deliberately small and replaceable:

1. one application-neutral and inference-neutral native `mini_entity.clay` executable;
2. one SQLite MiniUnifiedDB as canonical persistent state/config/evidence authority;
3. one optional replaceable generic 0.5B ClayCode cognition checkpoint.

`zero_blog` is only the replaceable shipped preset. Application, personality, provider, model, presentation wording and prompts are runtime data, not executable or checkpoint identity.

Current authority:

- `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`
- `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`
- `research_entity/rooms/PROGRAM_STATE.json`

Current acceptance is **IN_PROGRESS**. Source presence, a component test, a corpus, a training job or a fluent model trace never implies whole-product acceptance.

## Architecture law

The native executable owns only generic machinery: evidence/source preprocessing, canonical run/state envelope, inference dispatch, immutable truth/secret/admission gates, exactly-once source consumption, generation CAS and atomic persistence.

MiniUnifiedDB owns continuing canonical state and runtime configuration. Switching preset, inference backend, local weights, provider, prompt, role, goal or personality must not fork or reset continuity.

Epistemic law:

```text
UNKNOWN != ZERO != ERROR != MEASURED
REPORTED != MEASURED
MODEL_OUTPUT != CANONICAL_TRUTH
MODEL_PROPOSAL != EFFECT_AUTHORITY
```

The optional cognition checkpoint is replaceable inference data. It must not acquire canonical state/effect authority or a fixed name/job/persona/application.

## Cognition lane

SFT v2 is canonical for any paid training attempt; SFT v1 is historical.

Canonical SFT v2 campaign:

- 1,650 examples total;
- train 1,485 / 1,485 exact-unique;
- validation 165 / 165 exact-unique;
- exact cross-split message overlap: 0;
- prompt cross-split overlap: 0;
- structural invalid: 0 train / 0 validation;
- train SHA-256: `3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93`;
- validation SHA-256: `ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62`.

The owner-required primary base remains `Qwen/Qwen2.5-0.5B`; `Qwen/Qwen2.5-0.5B-Instruct` is the secondary ablation. The current Together Full-FT route remains blocked until an architecture-compatible admitted qwen2 template/runner exists and the exact HF revision is bound into campaign identity. Do not silently substitute Qwen3.5-0.8B merely because it is close in size.

No paid training job has been started in this `go`; spend is USD 0.

## Native 0.7 evidence

The historical exact source-bound native 0.7 ELF established same-environment repeat-build identity and ordinary runtime contracts, including atomic rollback and concurrent generation CAS. That historical ELF also executable-falsified three defects:

1. replaceable presentation strings embedded in the binary;
2. parent-environment secrets reaching `local_exec`;
3. canonical profile-v2 semantic fail-open before commit.

Current `main` has already incorporated the presentation-neutral and clean-child-environment repairs. Those source changes do not retroactively turn the historical red ELF green.

### Current fusion PR #851

The active native convergence path is PR #851, branch `gpt56sol/go-native-fusion-current-20260822-1512`. It replaces the temporary `block all profile-v2` placeholder with one canonical profile-v2 compile/envelope + immutable post-inference gate path while retaining the newer main-side presentation and `local_exec` isolation work.

The gate requires configured output-contract shape, canonical/packet hash echo where enabled, admitted evidence references and VERIFIED-only state claims. Persisted JSON string leaves are scanned recursively for configured leak patterns and the active secret before commit, including nested/future contract fields.

This `go` found and repaired an additional epistemic defect in the semantic evaluator: division by zero previously collapsed to numeric `0.0`. That violated `UNKNOWN != ZERO`. The current PR path now returns expression-evaluation failure for denominator zero, so the metric remains `UNKNOWN`.

`test_native_metric_div0_unknown.py` requires a model claim based on that value to fail as `UNVERIFIED_STATE_CLAIM_NO_COMMIT`, with:

- generation unchanged;
- no output row;
- no study row;
- source event still unconsumed.

The current PR also carries recursive persisted-output leak regressions and a dedicated semantic-gate workflow candidate.

### Exact evidence boundary

The newest fusion bytes have **not** earned runtime PASS yet.

Earlier PR-triggered jobs terminated before visible step execution (`steps=null`, `logs_url=null`). Those runs are classified as **EXECUTION_ADMISSION_FAILURE / ZERO TEST CREDIT**, not semantic test failures. For the newest PR head, no started workflow run was observable at this documentation update.

Therefore the current scope is:

```text
SOURCE FUSION CANDIDATE
+ bounded div-zero falsifier/repair evidence
+ deterministic test obligations
!= exact fusion runtime PASS
```

The next accepted native gate is an actually-started authorized isolated exact-head run that binds the source closure, builds the ELF and executes semantic/div-zero/recursive-leak/local-env/source-closure plus rollback/CAS regressions. Only then may the historical native blockers be retired for the new artifact identity.

## Inference backends

The product remains inference-neutral:

- remote/provider API from runtime profile;
- loopback OpenAI-compatible local API where admitted;
- local model weights through configured shell-free `local_exec` argv.

Changing backend/model must not reset MiniUnifiedDB state. Secrets remain runtime-only and must never become canonical output/state.

## 0.5B promotion gate

A completed training job would still be only a candidate. Promotion requires matched executable evidence including:

- strict ClayCode envelope on held-out OOD;
- at least 95% semantic gate pass;
- exact typed omega/tool arguments without guessed repair;
- Hyperposition preserved until evidence resolves alternatives;
- no fixed weight-bound persona under runtime identity/job changes;
- stale generation/unknown-effect fail-closed behavior;
- tuned 0.5B improvement over untuned 0.5B and comparison with a larger general model;
- GGUF Q4_K_M conversion;
- measured peak process RSS < 1 GiB at context 2048;
- successful use through generic `local_exec` without state reset.

No consciousness, AGI, superiority or mathematical-correctness claim follows from the cognition representation or from fine-tuning success.

## Current frontier

```text
NATIVE
current main presentation neutrality + local_exec isolation
-> PR #851 one canonical profile-v2 PipelineGate
-> exact started isolated source-bound build/run
-> semantic/div-zero/recursive-leak/source-closure/local-env regressions
-> atomic rollback + generation CAS
-> only then artifact promotion

COGNITION
leakage-free SFT v2 + runtime-binding + typed-omega gates
-> remove/avoid stale implicit training-template assumptions
-> bind exact HF revision
-> obtain admitted qwen2-compatible Full-FT path
-> owner/budget-gated SFT
-> held-out/base/larger-model benchmark
-> Q4_K_M
-> measured <1 GiB RSS
-> generic local_exec integration
```

Do not let either lane claim the other lane's acceptance.
