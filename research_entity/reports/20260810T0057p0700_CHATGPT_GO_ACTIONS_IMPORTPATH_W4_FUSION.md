# GO — Actions queue / Python import-path / W4 confidence fusion — 2026-08-10 00:57 +07

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay Research Entity worker; NOT Frank.  
Canonical parent: `RAE-8.8 / r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Fresh Clay main observed immediately before write: `c882c36fe8a16031eeb3e36af295826b6a72550d`  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffaehig auf Andreas PC` under Ubuntu developer-system semantics.

## Executive result

No ClayCode/Frank semantic or release gate is promoted in this continuation.

Highest-confidence current state:

- BASE remains `1/14` formally PASS; WP02 and all downstream BASE package promotions remain receipt-gated.
- V17 remains the selected WP02 grammar line.
- Python import-path isolation is now a required receipt-trust guard: `PYTHONPATH + PYTHONNOUSERSITE` alone does not make verifier-shaped and `python tools/script.py` execution import-equivalent under a same-name script-directory shadow.
- GitHub Actions has two separately observed degraded surfaces: GitHub-hosted jobs can fail before any visible step, while same-repository self-hosted jobs can be instantiated and remain queued awaiting allocation. Exact account/policy/runner cause is not yet verified.
- Real Qwen3-4B V1 Hostinger execution remains admitted diagnostic evidence; Qwen V2 and subsequent calibration remain receipt-gated.
- A new Frank implementation delta correctly prevents uncalibrated verbalized confidence from minting low-uncertainty W4 convergence evidence, but its remote V2 execution receipt remains absent.
- Physical Andreas Ubuntu target acceptance remains mandatory and absent.

## Exactly one OOB experiment for this worker go-cycle

The only unusual experiment introduced by this worker cycle is:

`GO-OOB-PYTHON-IMPORT-PATH-EQUIVALENCE-V1`

Local matched mechanism test, 20 repetitions per lane:

- verifier-like Python invocation: intended ephemeral dependency selected `20/20`;
- actual `python tools/probe.py` shape with `PYTHONPATH + PYTHONNOUSERSITE`: same-directory shadow selected `20/20`;
- identical actual-script invocation with `PYTHONSAFEPATH=1`: intended ephemeral dependency selected `20/20` and `sys.flags.safe_path=true`.

Local timing rows were retained in `research_entity/reports/20260810T0041p0700_CHATGPT_GO_PYTHON_IMPORT_PATH_EQUIVALENCE.md`; they are noisy local-container telemetry and are not Hostinger performance evidence.

No current `tools/lark.py` or `tools/interegular.py` was observed. Therefore the result is a latent reproducibility/test-isolation failure mode, not evidence of current ClayCode parser contamination.

Primary CPython documentation supports the mechanism: normal script execution can prepend the script directory ahead of `PYTHONPATH`, while `-P` / `PYTHONSAFEPATH` suppresses the potentially unsafe prepended path; `PYTHONNOUSERSITE` controls the user-site directory and is not an equivalent guard.

Architecture consequence: `NO_CHANGE`.  
Test-infrastructure consequence: require `PYTHONSAFEPATH=1`, `python -P`, or an explicitly demonstrated equivalent isolation contract for the actual Python tool processes whose dependency identity is being certified.

## Remote replication attempts of the same experiment

### Clay-repository lane

Committed `.github/workflows/claycode-go-python-import-path-equivalence.yml` at `5f51cb10f8b49f8676ad26768cfc3313c790ed39` with read-only self-hosted execution, non-persisted credentials and a separate hosted writer.

Expected `research_entity/claycode/remote_vps/go_oob_python_import_path/LATEST.json` had not materialized at the last read. This remains `UNKNOWN/MISSING_EVIDENCE`.

### Dr.-Unterweger Hostinger lane

Committed `.github/workflows/clay-go-python-import-path-equivalence.yml` at `gschaidergabriel/Dr.-Unterweger@2b59ae7e5c1d10202b69c2b42193b92c33ab1d2f`. The self-hosted job contains only temporary Python fixtures and performs no checkout, so it requires no Clay repository read access.

Expected `runtime/vps_integrity/clay_import_path_latest.json` had not materialized at the last read.

To distinguish writer failure from self-hosted execution status, a temporary PR-only observable transport was created without merge:

- PR: `gschaidergabriel/Dr.-Unterweger#51`;
- head: `986f3113d498f96bd97ac56ad25363a385b1ae2f`;
- workflow run: `31327682615`;
- self-hosted job: `93280573923`;
- job state across direct observations: `queued`, no conclusion, no steps/logs yet;
- PR closed without merge after evidence capture.

This proves the workflow/run/job was admitted far enough for an explicit self-hosted job object to exist. It does **not** prove Hostinger executed the experiment. The supported state is `SELF_HOSTED_JOB_QUEUED_ALLOCATION_UNKNOWN`.

No second OOB experiment is counted: the PR lane is only an observation transport for the same preregistered experiment.

## Actions orchestration evidence fusion

Shared current-main evidence independently reproduced GitHub-hosted pre-step failure in both repositories. Runs instantiate, but affected hosted jobs can end in `failure` with no visible steps and unavailable log blobs. A separate direct self-hosted job can instead remain `queued`.

Primary GitHub documentation says:

- standard GitHub-hosted private-repository jobs consume account minutes and may become billing/budget constrained;
- GitHub workflow troubleshooting explicitly includes billing/budget review;
- self-hosted runner execution itself does not consume GitHub-hosted billable minutes;
- repository-level self-hosted runners are dedicated to one repository, whereas higher-scope runners may serve authorized multiple repositories.

Therefore:

H1a: account billing/budget or hosted Actions admission can explain the hosted pre-step failure. `PLAUSIBLE_NOT_VERIFIED`.

H1b: Clay/Dr self-hosted queue state is caused by runner allocation/availability/scope. `PLAUSIBLE_NOT_VERIFIED`.

Counterhypothesis: the self-hosted runner is merely occupied/transiently unavailable, while hosted pre-step failure is an unrelated billing/policy condition. This remains live because the same Hostinger machine has prior real FRANK and Qwen receipts but the observable replication job remained queued.

Do not collapse these into one root cause without direct settings/runner evidence.

Safe operator falsifiers:

1. inspect GitHub personal billing / Actions budget / payment state;
2. inspect repository Actions policy for both repositories;
3. inspect self-hosted runner online/busy/labels/repository assignment, especially Clay repository visibility;
4. after orchestration is restored, consume only exact-SHA execution receipts.

## W4 / Qwen confidence control delta

Fresh Dr.-Unterweger implementation commit:

`302066f7642afc9cd3568b284bfae5c1448ea748` — `fix(model): reject uncalibrated confidence as W4 convergence evidence`.

The implementation preserves generic W4 semantics but changes the real-Qwen V2 evidence mapping:

- historical observed verbalized confidence is not treated as calibrated correctness probability;
- residual uncertainty supplied to W4 is set to `1.0` while the estimator is uncalibrated;
- the deterministic regression demonstrates the previous metadata could admit `HALT_CANDIDATE_CONVERGED` at uncertainty `0.08`, whereas the guarded mapping produces `READOUT_UNCERTAIN` / `ROUTE_READOUT_UNCERTAIN`;
- answer keys do not enter the controller-side convergence-quality discriminator;
- historical V1 remains diagnostic-only.

Interpretation: this is a justified controller-evidence-quality repair triggered by a real confidently-wrong Qwen trajectory. It is not evidence that the generic W4 convergence law itself is wrong and not permission for model confidence to become effect authority.

Remote V2 execution receipt `gschaidergabriel/Dr.-Unterweger:runtime/vps_integrity/real_qwen4b_prebuilt_v2_latest.json` was still absent at the last explicit read, so the implementation delta is not yet remotely accepted.

Architecture consequence for Clay: preserve the principle `activation/stability/self-confidence != truth`; any model-derived residual estimator needs admitted calibration/provenance before receiving low uncertainty in the loop controller.

## ClayCode / BASE consequence

Current supervisor state already incorporates two supported preliminary receipt guards:

1. Python safe-path equivalence;
2. bounded Lark termination/watchdog semantics.

The current production WP02 workflow observed during this cycle still exported `PYTHONNOUSERSITE=1` but did not yet export `PYTHONSAFEPATH=1` or invoke its `tools/*.py` processes with `-P`. No production workflow race-edit was performed here because current execution/dispatch state is degraded and concurrent workers are already changing the same frontier.

WP02 formal state stays `OPEN` until a schema-current, exact-tested-SHA, V17-bound Hostinger receipt exists and passes all required component rows. Hostinger remains preliminary evidence only. Physical Andreas Ubuntu target receipts remain a separate hard gate.

## Durable deltas / negative evidence

Durable results from this worker continuation:

- import-path falsifier report: `85fa66375cec9266480756e3afa7e52f063b494d`;
- Clay remote-replication workflow: `5f51cb10f8b49f8676ad26768cfc3313c790ed39`;
- Dr Hostinger remote-replication workflow: `2b59ae7e5c1d10202b69c2b42193b92c33ab1d2f`;
- temporary PR observation transport: closed, not merged;
- this fusion report.

Negative evidence retained:

- standard Clay WP02 Hostinger receipt absent;
- Clay import-path remote receipt absent;
- Dr import-path remote persistence receipt absent;
- real-Qwen V2 receipt absent;
- physical Andreas target autoprobe receipt absent;
- direct PR-observable self-hosted job remained queued during the observation window.

`MISSING/QUEUED != FAIL != PASS`.

## Next frontier

1. Resolve Actions hosted pre-step admission and self-hosted runner allocation/scope as separate capability questions.
2. On first actual self-hosted receipt, verify safe-path, exact V17 SHA, dependency identity/cleanup, bounded termination, strict/full-corpus/canonical rows and WP06 replay before any WP02 promotion.
3. Apply safe-path/hash-lock hardening only at a CAS-safe point and rerun matched semantics; treat drift as negative evidence.
4. Consume the real-Qwen V2 receipt when it exists and test whether the uncalibrated-confidence guard removes false convergence without introducing unnecessary recurrence/route inflation.
5. Proceed to the registered physical Andreas Ubuntu ten-application + FULL_FRANK + WP14 chain only after BASE preliminary closure.
6. No paid/final training until owner authorization.

Architecture delta this cycle: `NO_CHANGE_TO_CLAYCODE_SEMANTICS`; `W4_EVIDENCE_MAPPING_HARDENING_PENDING_REMOTE_RECEIPT`.
