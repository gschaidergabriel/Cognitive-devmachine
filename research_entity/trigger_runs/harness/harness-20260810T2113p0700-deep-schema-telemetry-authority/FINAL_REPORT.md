# Harness deep cycle — schema ownership, telemetry resource authority, CI falsification

**Run:** `harness-20260810T2113p0700-deep-schema-telemetry-authority`  
**Actor:** chatgpt-secondary / OpenAI / GPT-5.6 Sol  
**Program:** `FRANK_V0_1` only  
**Target:** `self.root` / Frank v0.1 on accepted Hostinger Ubuntu VPS  
**Promotion:** **NONE** — direct target source continues moving; final candidate still requires exact-SHA target replay

## 1. Live Hostinger baseline narrowed the failure

The current persisted `runtime/vps_integrity/latest.log` repeatedly showed the target runner `digital-retina` executing the broad Deep Integrity suite successfully except for `repo_static_integrity`. The failing rule was the historical blanket assumption that every runtime `executescript()` outside the canonical state migrator is forbidden.

The failing owners were bounded disposable/in-memory mechanism probes plus MCP telemetry. Other displayed gates remained PASS, including Python compile, transaction census/replay, deep integrity v11, migration atomicity, device state gate, causal re-entry and additional regression families.

Therefore the earlier generic interpretation `red Deep Integrity -> unknown whole-runtime failure` was replaced by the narrower executable finding:

```text
TARGET_RUNTIME_EXECUTION = WORKING
OBSERVED_FAILING_GATE = REPO_STATIC_SCHEMA_OWNER_CLASSIFICATION
WHOLE_RUNTIME_COLLAPSE = NOT_SUPPORTED
```

## 2. Pull-request Actions were falsified as a semantic instrument

A zero-dependency PR control workflow was created with:

- no checkout;
- no Python;
- no project code;
- one `printf` command only.

Its GitHub-hosted `pull_request` job also failed and exposed no returned steps. Therefore red PR Actions in this repository cannot currently discriminate candidate source correctness from CI/transport failure.

Consequences:

- red runs on earlier ingress/security PR #105 were downgraded from source-negative evidence to infrastructure-negative/undifferentiated evidence;
- red runs on schema-owner PRs likewise cannot be treated as candidate falsification;
- promotion still requires an independent exact-SHA target receipt.

Branch-push and candidate self-hosted receipt sentinels were also added in the old candidate lane, but their expected persisted receipts were not observed. Their status remains `NOT_EXECUTED_OR_NOT_PERSISTED`, never PASS.

## 3. First schema-owner repair found a deeper telemetry authority problem

The first repair hypothesis was to classify exact noncanonical `executescript()` owners rather than blanket-reject them. Source review then exposed a more important issue: the original `TelemetryStore` selected its DB from a constructor path or `FRANK_TELEMETRY_DB`, opened that SQLite path, and executed telemetry schema there.

Current systemd deployment already mitigated the obvious production path with:

```text
ProtectSystem=strict
ReadWritePaths=/srv/frank-telemetry
```

but the Python runtime contract itself was weaker than the deployment boundary.

This changed the research question from:

```text
"Which files may contain executescript()?"
```

to:

```text
"Which resource may obtain telemetry schema authority, and how is that ownership proven before schema execution?"
```

## 4. Adversarial resource-authority candidate

The research candidate developed the following path/inode invariants:

1. production/default/environment telemetry paths must be absolute;
2. production/default/environment telemetry paths must resolve below `/srv/frank-telemetry`;
3. explicit constructor paths are fixture-only and must resolve below the OS temporary root;
4. canonical `FRANK_UNIFIED.sqlite` and `FRANK_CLAYGRAPH.sqlite` basenames are denied;
5. symlink/parent-traversal escapes are rejected after path resolution;
6. an existing target must be a regular file;
7. an existing target must have `st_nlink == 1`, rejecting hardlink aliases;
8. existing `(st_dev, st_ino)` is snapshotted before SQLite open;
9. file existence, regular/single-link status and dev/inode identity are rechecked after `sqlite3.connect` and before schema authority is invoked;
10. disappearance/replacement during the pre-open/open interval fails closed.

This narrows, but does not claim to formally eliminate, every possible filesystem race. OS namespace/permission isolation remains part of the trust boundary.

## 5. Executed discriminators

### Targeted regression matrix

Latest research-side semantic reproduction after hardlink and replacement-race hardening:

```text
schema-owner / audit regressions: 14 / 14 PASS
runtime path / inode / race regressions: 13 / 13 PASS
total targeted: 27 / 27 PASS
```

The runtime suite includes:

- production root escape;
- relative production path;
- relative fixture path;
- canonical DB basename;
- symlink escape;
- directory target;
- hardlink alias;
- actual constructor environment-variable path;
- valid temporary schema roundtrip;
- deterministic existing-file replacement between precheck and SQLite open.

The replacement-race control verified that the protected original SQLite inode retained only its pre-existing `protected` table; telemetry schema was not applied to it.

### Deterministic path-property fuzz

```text
seed: 4815162342
cases: 50,000
accepted: 23,083
blocked: 26,917
baseline property violations: 0
```

Mutation control:

```text
mutation = remove root-ownership check, keep canonical-basename denial
mutation violations = 22,980
first detected case = 1
first path = /tmp/telemetry-537999457.sqlite3 as production environment path
```

The corpus is therefore strongly sensitive to removal of its core resource-ownership invariant.

## 6. Stale allowlist was also falsified

Path-based owner classification alone can silently age: a currently harmless probe may change while retaining superficial markers such as `tempfile`.

The research candidate therefore tested exact reviewed Git-blob binding for active schema owners. Any byte drift becomes `SCHEMA_OWNER_BLOB_DRIFT` until re-review. An inactive earlier effect-lifecycle schema owner was removed from preapproval entirely: if `executescript()` reappears there, it becomes UNCLASSIFIED.

This produced a useful design principle even though the exact reviewed-owner implementation was later superseded by a better mainline architecture:

```text
security exception path + class + superficial marker is weaker than
security exception path + semantic boundary + source identity/re-review
```

## 7. Parallel mainline work produced a better DDL architecture

During this run, current main independently changed MCP telemetry architecture:

- `TelemetryStore` no longer embeds or directly executes schema text;
- a dedicated `telemetry_schema_migrator.py` became the schema-authority surface;
- current `repo_static_integrity_audit.py` explicitly allows only the canonical state migrator and the dedicated telemetry migrator as production `executescript()` authority;
- disposable/in-memory probes are classified separately and checked for isolation;
- a new target-VPS `Frank Telemetry Schema Authority V1` workflow was added with read-only executor, disposable roundtrip, live telemetry read-only inspection, repo static audit and isolated evidence persistence.

This mainline solution is architecturally superior to merging the old PR #122 wholesale because it separates DDL authority from ordinary runtime storage logic.

Therefore:

```text
PR_122_MERGE_CANDIDATE = SUPERSEDED
PR_122_VALUE = RESEARCH / MUTATION / RESOURCE-AUTHORITY EVIDENCE
MAIN_SCHEMA_MIGRATOR_ARCHITECTURE = RETAIN
```

## 8. Remaining gap in current main

After the migrator split, current main `TelemetryStore` still selected:

```text
Path(path or FRANK_TELEMETRY_DB)
-> mkdir parent
-> sqlite3.connect(writeable)
-> apply_telemetry_schema(connection)
```

without source-level root/canonical-name/hardlink/inode-race validation.

Thus DDL authority and resource authority are distinct:

```text
SCHEMA AUTHORITY: solved by dedicated migrator on current main
RESOURCE AUTHORITY: still open in current main source
```

The current hardened systemd unit reduces immediate exploitability, but alternate launch paths or future sandbox drift could re-expose the weaker Python contract.

## 9. Clean current-main follow-up: PR #148

A fresh branch was created from current main:

`clay/frank-v01-telemetry-path-authority-20260810`

Draft PR **#148** preserves the new `telemetry_schema_migrator.py` design and changes only resource authority.

It adds:

- dedicated production telemetry root;
- temp-only explicit fixture capability;
- absolute path requirement;
- canonical Frank DB basename denial;
- regular/single-link target validation;
- pre/post-open existing-file identity validation;
- fail-closed file disappearance/replacement handling.

Existing `test_telemetry_schema_authority.py` is extended with root escape, canonical-name, hardlink and deterministic replacement-race cases.

More importantly, the already-existing target-VPS `telemetry_schema_authority_vps_gate.py` is extended so `PASS_TELEMETRY_SCHEMA_AUTHORITY_V1` now additionally requires a live `path_authority=PASS` discriminator. The live target DB remains read-only in that gate.

This means that if/when the candidate is integrated, the existing main-only Hostinger workflow can produce a target-bound receipt for both:

```text
schema authority separation
+
resource/path authority separation
```

## 10. Identity/effect interaction

Current effect-authority work is substantially more advanced and has target-VPS evidence, but current main still carried pre-owner-fixed `Frank.id` identity semantics during this research window. Separate PR #102 is already the active self.root/server-binary identity migration lane and was not duplicated.

Consequently:

- effect/security receipts remain component evidence;
- identity migration must integrate first;
- then effect/security/API/restart/resource-authority tests must be replayed under exact self.root identity before terminal v0.1 acceptance.

## 11. Current evidence ranking

### Strongly supported

- main target VPS executes the broad Deep Integrity suite;
- old static schema-owner policy was the repeatedly isolated observed failure;
- blanket `executescript()` rejection conflated production DDL authority with disposable mechanism-probe DDL;
- telemetry resource identity is a separate authority dimension from schema authority;
- root-ownership, hardlink and replacement-race tests are mutation-sensitive in the research reference;
- current main's migrator split is a better DDL architecture than the old PR #122 approach.

### Candidate only

- exact source-level path/inode policy of PR #148;
- its cost/compatibility under the live MCP service;
- whether inode pre/post checks provide enough incremental value beyond the current systemd sandbox.

### Not established

- PR #148 target-VPS PASS;
- full Frank v0.1 acceptance;
- self.root-integrated replay of this security boundary;
- final model/training acceptance.

## 12. Next exact discriminator

1. retain main's dedicated telemetry schema migrator;
2. review/rebase PR #148 against the next stable main head if necessary;
3. execute the existing `Frank Telemetry Schema Authority V1 VPS` workflow on the exact integrated source;
4. require `source_authority=PASS`, `path_authority=PASS`, disposable roundtrip PASS, live telemetry `READ_ONLY/READY`, and repo static integrity PASS on one exact SHA;
5. then replay after self.root identity PR #102 integration;
6. only then allow this component to contribute current-source target acceptance.

## 13. Durable evidence

Append-only evidence written during this cycle:

- `research_entity/frank_v0_1/evidence/20260810T2150p0700_harness_sqlite_schema_owner_ci_transport.json`
- `research_entity/frank_v0_1/evidence/20260810T2213p0700_harness_schema_owner_inode_blob_tail.json`
- this final report

Research issue #192 and target PRs #122/#148 contain the branch-level re-entry trail.

**Final disposition:** `FRANK_V0_1_TEST_DELTA + SECURITY_ARCHITECTURE_DELTA + NEGATIVE_RESULT`; **no production promotion.**
