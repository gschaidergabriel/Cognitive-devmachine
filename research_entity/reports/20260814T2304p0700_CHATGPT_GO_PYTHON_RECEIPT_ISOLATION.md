# GO research delta — Python receipt isolation on self-hosted runner

Date: 2026-08-14T23:04+07:00
Trigger: `go`
Worker: ChatGPT GPT-5.6 Sol temporary Clay organ
Program: FRANK_V0_1
Affected gate: F-V01-13-SECURITY-RECOVERY-OBSERVABILITY
Product work item: gschaidergabriel/Dr.-Unterweger#578

## R0 — observed reality

Current product main at `gschaidergabriel/Dr.-Unterweger` contains `.github/workflows/clay-go-python-import-path-equivalence.yml` and recent VPS replication evidence. Commit `1243bd31606df1d52e1865fd7f1cf5d563c499d8` changed the workflow's three stdlib-only Python receipt/driver invocations from plain `python3` to `python3 -I`. Subsequent receipt commit `4e463f9495d304de4e833f6e9e8609baddaf79b2` records a self-hosted Ubuntu replication whose intended baseline shows script-directory shadowing under ordinary script execution and successful suppression under the safe-path lane.

The workflow still emits `supported_test_infrastructure_delta=ADD_PYTHONSAFEPATH_OR_PYTHON_MINUS_P_TO_SELF_HOSTED_PYTHON_TOOL_EXECUTION_AND_RECEIPT`, which is broader than current Python semantics support.

## Primary external evidence

Python 3.14 command-line documentation states:
- `-P` / `PYTHONSAFEPATH` prevents prepending a potentially unsafe path to `sys.path`.
- `-I` is isolated mode and implies `-E`, `-P`, and `-s`; it ignores all `PYTHON*` environment variables and removes script/current-directory and user-site path injection.
- `-S` separately disables automatic `site` initialization.

Python `site` documentation states that normal site initialization attempts to import system `sitecustomize`, which may execute arbitrary site-specific customization.

GitHub Actions documentation states that self-hosted runners are not guaranteed to be ephemeral/clean and may retain compromise from untrusted workflow execution. Therefore interpreter flags are a defense layer, not host-attestation proof.

## R1 — leading hypothesis

For stdlib-only receipt verifiers, `-I` is the correct minimum defense against both unsafe path prepending and untrusted `PYTHON*` environment variables. `-P`/`PYTHONSAFEPATH` is only equivalent for the narrower threat model where `PYTHONPATH` and other `PYTHON*` variables are already trusted/controlled.

## R3 — strongest counter-reality

Blindly replacing all Python execution with `-I` may break legitimate project-local imports because the script directory and `PYTHONPATH` are intentionally excluded. Also, `-I` alone does not disable system `sitecustomize`; a persistently compromised self-hosted runner remains outside the guarantee.

## Exactly one bounded unusual experiment

Experiment ID: `GO-OOB-PYTHONPATH-POISON-EQUIVALENCE-20260814`

Temporary local fixture only. Four lanes shared one script-directory module shadow and one attacker-controlled `PYTHONPATH` module:

| lane | observed import |
|---|---|
| baseline | `SCRIPT_DIR` |
| `PYTHONSAFEPATH=1` | `EVIL_PYTHONPATH` |
| `python -P` | `EVIL_PYTHONPATH` |
| `python -I` | neither injected path; `ModuleNotFoundError` for the local dependency |

Outcome: RETAIN hypothesis / REFUTE equivalence claim. `-P` and `PYTHONSAFEPATH` do not ignore malicious `PYTHONPATH`; `-I` does. The `-I` lane also demonstrates the compatibility cost: legitimate local dependencies must be provided through an explicitly trusted packaging/import mechanism.

No second unusual experiment was executed in this macro-cycle.

## Collapse / fused design delta

1. Keep `-I` for stdlib-only receipt verifiers and trust-boundary Python that must ignore `PYTHON*` environment state.
2. Evaluate `-I -S` for stdlib-only verifiers that do not require site initialization, so system `sitecustomize` is removed from that verifier's dependency surface.
3. Do not describe `-P` or `PYTHONSAFEPATH` as equivalent to `-I`; they are narrower controls.
4. For project-dependent tools, prefer a source-pinned/attested venv or package install plus explicit dependency provenance rather than globally weakening receipt-verifier isolation.
5. Add a regression lane with poisoned `PYTHONPATH` to future self-hosted receipt tests.
6. Preserve host-trust boundary: passing interpreter-path tests does not prove a persistent self-hosted runner is uncompromised.

## Promotion state

State: `SUPPORTED_RESEARCH_DELTA`, not release PASS.

Evidence needed for promotion:
- product workflow patch implementing the narrowed wording and a poisoned-`PYTHONPATH` regression;
- target self-hosted receipt proving the patched lane on current source;
- if `-I -S` is adopted, explicit proof that required stdlib-only verifier dependencies remain available and site initialization is not required;
- separate host/build/runtime attestation remains required for Frank v0.1 acceptance.

## Re-entry

Opened product issue `gschaidergabriel/Dr.-Unterweger#578` with repair and acceptance criteria. This finding should be treated as an F-V01-13 test-infrastructure/provenance hardening item; it does not close the package and does not supersede SQLite, semantic-lineage, crash/restart, artifact-attestation, or real-provider blockers.