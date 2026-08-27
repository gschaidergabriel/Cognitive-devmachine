# GO — Python verifier environment-isolation falsifier

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay research worker; NOT Frank.  
Canonical parent: `RAE-8.8 / r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Fresh Clay main observed before durable write: `0865cd27d5243d6a658e15b804debc134dbf6edf`  
Fresh Frank implementation main observed before implementation write: `12eb0dd1301793298710e643da8f035a7454ba3d`  
Trigger: exact `go`

## Classification

`TEST_INFRASTRUCTURE_SECURITY_HARDENING` / `NO_FRANK_ARCHITECTURE_CHANGE` / `NO_RELEASE_PROMOTION`.

Exactly one deliberately unusual experiment was introduced in this worker cycle:

`GO-OOB-PYTHONPATH-POISON-VS-ISOLATED-V1`

No second out-of-box experiment is introduced by this worker cycle.

## R0 anchors

The current Frank implementation workflow `.github/workflows/clay-go-python-import-path-equivalence.yml` already carries `PYTHONSAFEPATH=1` and a persisted Hostinger receipt demonstrating that the earlier script-directory-shadow issue is suppressed by safe-path mode. The latest persisted replication before this cycle showed the unsafe script invocation choosing `SCRIPT_DIR_SHADOW` 20/20 and the safe-path lane choosing `EPHEMERAL_DEPS` 20/20.

The workflow still invoked its outer fixture generator, receipt enforcer, and persistence validator through ordinary `python3` stdin execution while relying on the environment-level safe-path control.

## Primary-source refresh

Current CPython command-line documentation states:

- `-P` / `PYTHONSAFEPATH` prevents prepending a potentially unsafe current/script path to `sys.path`;
- `PYTHONPATH` still augments the import search path;
- `-E` ignores `PYTHON*` environment variables;
- `-I` isolated mode implies `-E`, `-P`, and `-s`, removing the script/current directory and user site from import search and ignoring all `PYTHON*` environment variables.

Primary references:
- https://docs.python.org/3.13/using/cmdline.html
- https://docs.python.org/3/using/cmdline.html

## Generated reality / hypothesis

H1: `PYTHONSAFEPATH=1` closes the demonstrated script-directory-prepend gap but does not make security-sensitive verifier processes immune to an inherited or injected `PYTHONPATH`; an attacker-controlled module reachable only through `PYTHONPATH` can still win import resolution.

Strongest counter-reality: safe-path mode plus the current workflow environment is already sufficient for verifier integrity, so a poisoned `PYTHONPATH` cannot influence imports in those Python verifier processes.

Falsifier: run matched interpreter shapes under an explicitly poisoned `PYTHONPATH` and compare current safe-path behavior against `python3 -I`.

## Exactly one bounded unusual experiment

Temporary fixture outside both repositories:

- `poison/probe_dep.py` with `ORIGIN='POISONED_PYTHONPATH'`;
- a probe script imports `probe_dep` and reports `sys.flags.safe_path`, `sys.flags.isolated`, and `sys.path`;
- environment sets both `PYTHONPATH=<poison>` and `PYTHONSAFEPATH=1`;
- lane A: ordinary `python3 <probe.py>`;
- lane B: `python3 -I <probe.py>`;
- compatibility control for the intended workflow patch: `python3 -I -` reading source from stdin and importing stdlib `json`.

Observed local Linux/Python 3.13 mechanism evidence:

- lane A: `safe_path=true`, `isolated=false`, import origin `POISONED_PYTHONPATH`;
- lane B: `safe_path=true`, `isolated=true`, `probe_dep` rejected with `ModuleNotFoundError`; poisoned directory absent from `sys.path`;
- stdin isolated control: stdlib `json` loaded successfully; `PYTHONPATH` remained visible in `os.environ` but was absent from interpreter import search.

The counter-reality is refuted for the tested CPython mechanism. H1 is supported.

## Intervention

Smallest repair applied to `gschaidergabriel/Dr.-Unterweger` main:

commit `1243bd31606df1d52e1865fd7f1cf5d563c499d8` — `security(ci): isolate Python receipt verifiers from PYTHON* env`.

Changed only the three security-sensitive outer/verifier Python entry points in `.github/workflows/clay-go-python-import-path-equivalence.yml` from ordinary stdin Python to `python3 -I - ...`.

The actual three-lane import-path experiment remains non-isolated internally because its purpose is explicitly to vary and measure controlled `PYTHONPATH`/safe-path semantics. Thus the patch hardens the receipt machinery without destroying the measurement under test.

Rollback: revert commit `1243bd31606df1d52e1865fd7f1cf5d563c499d8` if isolated-mode execution breaks a required verifier dependency; preserve that failure as negative evidence and replace ambient dependency resolution with an explicit pinned interpreter/dependency contract rather than re-opening inherited `PYTHON*` authority.

## Outcome and re-entry

Outcome: `RETAIN` security hardening; `NO_CHANGE` to Frank architecture/work-package completion status.

Affected invariants/components:
- F-V01-13 security/recovery/observability test infrastructure;
- provenance/receipt integrity;
- model output != execution authority remains unchanged.

Promotion boundary:
- local mechanism evidence supports the change;
- GitHub Actions run `31779493258` was triggered for exact commit `1243bd31606df1d52e1865fd7f1cf5d563c499d8` and was still queued at observation time, therefore target/self-hosted execution is `UNKNOWN/PENDING`, not PASS;
- no Frank v0.1 package or release gate is promoted by this report.
