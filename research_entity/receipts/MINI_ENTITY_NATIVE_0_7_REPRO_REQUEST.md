# Mini Entity native 0.7 exact reproduction — execution request

Status: `PENDING_RUNNER_EXECUTION`

This file exists to request the canonical default-branch `mini-entity-native-0-7-repro.yml` acceptance gate on an exact PR checkout. It is not evidence of PASS.

Bound base when opened: `e261757fa21538ea24a6ff174b7b55d9929fcb94`.

Required evidence scope:
- exact checkout and transitive native source identity;
- repeated `mini-entity/0.7.0-dev1` native build and ELF identity;
- neutral fresh DB;
- fixture `local_exec` with no secret-file lookup and no network syscall;
- generation/output/study/event rollback fault matrix;
- second clean byte-identical rebuild;
- bounded machine receipt artifact.

The source-closure mutation falsifier is regression-only in this run. The single unusual experiment for the parent `go` was already consumed and recorded on current main; no new unusual experiment is authorized here.

Admission retrigger: PR synchronize event requested after the workflow was confirmed present on default-branch `main`. This line is not executable evidence.
