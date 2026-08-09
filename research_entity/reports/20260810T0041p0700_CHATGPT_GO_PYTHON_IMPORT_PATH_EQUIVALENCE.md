# GO — WP02 Python import-path equivalence falsifier

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay research worker; NOT Frank.  
Canonical parent: `RAE-8.8 / r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Fresh main observed immediately before durable write: `0f0b70a97df71c2fbcd51c100d45df0968e473b3`  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffaehig auf Andreas PC` under Ubuntu developer-system semantics.

## Classification

`TEST_INFRASTRUCTURE_REPRODUCIBILITY_GAP` / `NO_CLAYCODE_SEMANTIC_CHANGE` / `NO_RELEASE_PROMOTION`.

This report records the exactly one deliberately unusual experiment introduced by this worker's current `go` macro-cycle:

`GO-OOB-PYTHON-IMPORT-PATH-EQUIVALENCE-V1`

No second out-of-box experiment is introduced by this worker cycle.

## Fresh state and observed execution lane

Current `.github/workflows/claycode-vps-wp02-probe.yml` uses a run-unique `pip --target` dependency directory, exports `PYTHONNOUSERSITE=1`, prepends that directory through `PYTHONPATH`, verifies `lark` and `interegular` module paths with a stdin Python process, then executes the actual probes as `python3 tools/<script>.py`.

Current repository checks for `tools/lark.py` and `tools/interegular.py` returned 404. Therefore there is no observed current dependency shadow by those exact filenames. The issue below is a latent path-equivalence/reproducibility gap, not evidence of current contamination or compromise.

Current real Hostinger baseline independently records Python `3.12.3` on Linux `6.8.0-117-generic` x86_64 and a 21/21 passing FRANK integrity matrix. This experiment does not relabel that evidence.

## Primary runtime evidence

CPython documentation states that normal script execution prepends the script directory to `sys.path` before `PYTHONPATH`; `-P` / `PYTHONSAFEPATH` suppresses that potentially unsafe prepended path. `PYTHONNOUSERSITE` disables user-site packages but is not the same control.

Primary references:
- https://docs.python.org/3/library/sys_path_init.html
- https://docs.python.org/3/library/sys.html#sys.path
- https://docs.python.org/3/library/site.html
- https://docs.python.org/3/using/cmdline.html

## Hypothesis / strongest counterhypothesis

H1: the current dependency verifier and the actual `python3 tools/*.py` executions are not import-path equivalent. A same-directory module shadow can be invisible to the verifier yet win resolution in the actual script invocation. Enabling `PYTHONSAFEPATH=1` (or `python -P`) should restore the intended precedence of the ephemeral dependency target.

Counterhypothesis: explicit `PYTHONPATH=<ephemeral-target>` plus `PYTHONNOUSERSITE=1` is already sufficient, so verifier-like and actual-script invocation resolve the same dependency under a same-name script-directory shadow.

## Exactly one bounded OOB experiment

A temporary isolated fixture was constructed outside the repository:

- ephemeral dependency directory containing `probe_dep.py` -> `ORIGIN='EPHEMERAL_DEPS'`;
- script directory containing a same-name `probe_dep.py` -> `ORIGIN='SCRIPT_DIR_SHADOW'`;
- actual probe script imports `probe_dep` and emits origin, `sys.path[0]`, and `sys.flags.safe_path`;
- environment always set `PYTHONNOUSERSITE=1` and `PYTHONPATH=<ephemeral-deps>`;
- three matched invocation modes, 20 repetitions each.

Execution runtime for this bounded discriminator: local Linux container, `/usr/bin/python3`, Python 3.13.5. This is mechanism evidence only and is not Hostinger performance evidence.

### Results

| lane | intended question | result | N | p50 wall ms | p95 wall ms | min ms | max ms |
|---|---|---:|---:|---:|---:|---:|---:|
| verifier_like | `python -c` / verifier-shaped invocation | `EPHEMERAL_DEPS` 20/20 | 20 | 558.958 | 1655.262 | 87.825 | 1802.728 |
| actual_current | `python tools/probe.py` with current env controls | `SCRIPT_DIR_SHADOW` 20/20 | 20 | 76.076 | 220.106 | 33.859 | 257.829 |
| actual_safe | same script invocation plus `PYTHONSAFEPATH=1` | `EPHEMERAL_DEPS` 20/20 | 20 | 159.820 | 704.059 | 49.766 | 854.805 |

Timing is retained for completeness but is noisy container telemetry and is not used for the semantic decision. The discriminating outcome is dependency origin.

Observed single-run path semantics were also consistent:
- verifier-like: `safe_path=false`, ephemeral dependency selected;
- actual current: `safe_path=false`, script-directory shadow selected;
- actual safe: `safe_path=true`, ephemeral dependency selected.

## Interpretation

H1 is supported for the tested CPython mechanism. The current verifier proves dependency identity under its own invocation shape, but that proof is not sufficient to prove identical module resolution for subsequent `python3 tools/*.py` processes.

This does **not** show that current ClayCode probes imported the wrong Lark/interegular modules. The current repository has no `tools/lark.py` or `tools/interegular.py` at observation time. It shows that the isolation contract is incomplete against future accidental or adversarial same-directory module shadows.

The narrow repair is test/runtime hardening, not language redesign:
1. add `PYTHONSAFEPATH=1` globally to the self-hosted WP02/WP06 execution shell, or invoke relevant scripts with `python3 -P`;
2. record and require `sys.flags.safe_path == true` in the dependency/execution receipt;
3. preserve the current exact-version/ephemeral-root/module-path/tree-hash/cleanup checks;
4. rerun WP02 + the already-defined OOB trivia test + WP06 replay on Hostinger;
5. any semantic drift after the path change is negative evidence requiring the smallest falsifier.

Do not claim this control is a full runner sandbox. It closes only the demonstrated Python import-path equivalence gap.

## Architecture / work consequence

Architecture delta: `NO_CHANGE` to V17, ClayCode semantics, Frank architecture, or authority boundaries.

Test obligation: `ADD_SAFE_PATH_TO_SELF_HOSTED_WP02_WP06_EXECUTION_AND_RECEIPT`.

Formal package state: unchanged. `CC-WP-02` and downstream BASE release gates remain receipt-gated.

Remote receipt state immediately before this report: `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json` still missing (GitHub 404), therefore `MISSING_EVIDENCE`, not FAIL.

Rollback: remove/disable the safe-path hardening if it breaks an explicitly required import contract, preserve that failure as negative evidence, and restore the last-known-good workflow while the import contract is repaired explicitly rather than via ambient script-directory resolution.
