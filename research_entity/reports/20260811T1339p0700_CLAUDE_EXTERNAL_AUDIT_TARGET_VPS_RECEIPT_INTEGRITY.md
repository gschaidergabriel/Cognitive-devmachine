# External audit — target-VPS receipt integrity vs. enforced mechanism

Date: 2026-08-11 13:39 +07:00
Origin actor: `claude-code` / Anthropic / Claude Opus 5 (1M) — external reviewer session, not a booted Clay organ
Identity: `EXTERNAL_ADVERSARIAL_REVIEWER`
Audited target: `gschaidergabriel/Dr.-Unterweger` working checkout on `clay@digital-retina`
Audited artifact set: the three receipt families quoted most prominently in the 2026-08-11 handoff snapshot
Status: `FINDINGS_CONFIRMED_BY_LOCAL_EXECUTION / NO_PROMOTION_REQUESTED / NO_TARGET_REPO_MUTATION`

## 0. Why this report exists

The project owner asked for an independent check of whether the work performed on the accepted
target VPS is *correct*, not whether it is *present*. This audit therefore ignored receipt prose and
read the programs that produce the receipts. Two mechanisms were additionally re-executed and one was
deliberately sabotaged to test whether the stated guarantee is actually enforced.

The headline result is asymmetric and should not be compressed into a single verdict:

**The enforced mechanisms are consistently stronger than the receipts that describe them.**
Reading only the receipts understates the engineering and overstates the measurements — in that order.

## 1. What was executed (evidence class: local execution on the accepted target lane)

All runs below were performed on `digital-retina` (the accepted target VPS), Python 3.12.3,
in a `/tmp` copy of the runner checkout. The runner working tree was not modified
(`git status --porcelain` empty after the audit). The copy was deleted. No external effect was
performed and no canonical database was touched.

| Probe | Re-executed result | Snapshot claim | Verdict |
|---|---|---|---|
| `runtime/frank_effect_authority_v1/target_vps_probe.py` | 20/20, false-allow 0.0, refusal 0.0 | identical | reproduces |
| gate latency p50/p99 | 0.20 / 0.47 µs | 0.28 / 0.45 µs | reproduces (same order) |
| `tests/frank_single_instance_presence_gate.py` | `race_contenders 12, race_winners 1, race_busy 11`, `sqlite_integrity ok` | identical | reproduces |
| `tests/effect_reentry_done_v17_candidate_gate.py` | PASS, 18/18 checks | identical | reproduces |

Reproduction is confirmed. Nothing in this audit suggests fabricated numbers.

## 2. Finding A — `MEASUREMENT_REPORTING_INFLATION` (systemic, all three families)

### A1. Denominators that cannot fall

`runtime/frank_effect_authority_v1/target_vps_probe.py` defines:

```python
def check(name, condition, out):
    out[name] = "PASS" if condition else "FAIL"
    if not condition:
        raise AssertionError(name)
```

A failing check raises before the receipt is written. The run therefore terminates either at
`20/20` or with no receipt at all. **A receipt reading `14/20` cannot exist by construction.**
`counts.passed / counts.total` carries exactly one bit: "the oracle reached the end".

The same pattern is stronger in the V17 candidate gate. Its `checks` dict contains 18 named
entries, of which **14 are hardcoded `True` literals** and only 4 (`rollback_preserved_v14`,
`rollback_preserved_v16`, `rollback_removed_candidate_tables`,
`base_runtime_still_opens_after_candidate_rollback`) are computed from observed state. The
verification for the other 14 happens earlier via bare `assert`; reaching the dict is treated as
proof. A reader — including the handoff snapshot — sees eighteen measurements where there are four.

Measured consequence: under `python3 -O` every `assert` is stripped. The V17 gate then emits the
identical `status` and an identical `18/18` while 14 of its checks are unconditional constants.

### A2. `EXECUTABLE_POLICY_ORACLE` is not executing the semantic source

The effect-authority probe binds itself to `claycode/frank_effects.clay` only through literal
substring containment:

```python
missing = [x for x in required_markers if x not in semantic]
```

Thirteen marker strings are searched. Nothing is parsed, type-checked, lowered or executed. The
Python `EffectGate` and the ClayCode declaration are two independent artifacts whose correspondence
is never established. **The semantics of `decide_effect` in the `.clay` source could be inverted and
the probe would still emit PASS as long as the signature lines remain textually present.**

The receipt nevertheless carries
`evidence_class: DIRECT_FRANK_V0_1_EFFECT_AUTHORITY_EXECUTABLE_POLICY_ORACLE` and the snapshot
repeats it. This is the project's own `typed frontend != complete compiler` falsifier occurring
inside the flagship gate. Recommended reclassification:
`PYTHON_POLICY_ORACLE_WITH_CLAY_SIGNATURE_PRESENCE_CHECK`.

### A3. The latency figure measures the cheapest branch

The 20,000-sample loop calls `perf_gate.evaluate(read)` with the *same* `read` object through the
`READ_ONLY` branch — the first comparison after `UNKNOWN_EFFECT` in the if-chain, fully warm. The
reported `gate_latency_us` is the cost of one enum comparison in CPython, not the latency of the
authority gate over its decision space. It should not be quoted as a system property. A defensible
version samples the full request matrix, including the destructive paths with confirmation
application.

## 3. Finding B — the enforced mechanisms are better than their receipts

This section is as important as Finding A and must not be dropped when the audit is summarized.

### B1. Non-cognitive authority is genuinely enforced, not merely declared

`EffectGate.evaluate()` accepts `model_confidence`, `gwt_ignition`, `claygraph_salience` and
`translator_effect_hint` as request fields and **never reads any of them**. The accompanying hash
test is sharp rather than decorative: 1000 randomized single-field mutations across 22 policy
fields change `request_hash()` in 1000/1000 cases, while mutating all four cognitive fields leaves
the hash identical. The directive
"model/GWT/Needle/translator/graph/reward cannot mint authority" is therefore an enforced and
independently falsifiable property of the implementation. This is the strongest single result in
the audited set.

Confirmation binding is also real: one-shot nonce, expiry, and exact
`request_hash`/`effect_class`/`target`/`action` equality, with replay verified as
`ALLOW` then `DENY` on the same receipt.

### B2. The presence lease is database-enforced, not process-local

`tests/frank_single_instance_presence_gate.py` uses real `ThreadPoolExecutor` workers released by a
`threading.Barrier`, and `runtime/state/frank_presence_runtime.py` serializes through
`BEGIN IMMEDIATE` with epoch increment guarded by `WHERE ... AND lease_epoch=?`. Mutual exclusion
lives in SQLite's write lock and in optimistic fencing, not in a Python-level lock. This would hold
across processes.

Residual gap: the contenders are threads in one process, so cross-process and cross-host
acquisition are argued rather than demonstrated. A `multiprocessing` variant would close this
cheaply.

### B3. V17 carries a real prior negative baseline — and defense in depth

The V17 candidate receipt references `FRANK-V01-EFFECT-REENTRY-GAP-31406627821`. That receipt
exists in the target repo and is a genuine expected-negative discriminator. It names the falsified
claim explicitly:

> "Current effect lifecycle structurally enforces provenance-bound verified-outcome re-entry
> through explicit DONE."

and records the concrete hole (`empty_unbound_reentry_payload_accepted: true`,
`runtime_treats_reentered_as_complete: true`, `trace_verifier_reason: "OK"`,
`schema_has_explicit_done_state: false`). The mechanism was built afterwards to close exactly that
gap. **Prove the predecessor fails, then claim the successor passes** — this is correct method and
should be propagated to the other work packages, several of which currently have no negative
baseline at all.

More importantly, the V17 guarantee is **not** carried by application code. An adversarial
experiment was run: the Python attempt-identity check in
`runtime/state/effect_terminal_runtime_v17_candidate.py:137` was replaced with `if False:` in a
disposable copy. The gate still refused the malformed re-entry — the rejection came from the schema:

```
sqlite3.IntegrityError: V17_REENTRY_CANONICAL_BINDING_MISMATCH
```

`UNIFIEDDB_V17_EFFECT_REENTRY_DONE_CANDIDATE.sql` installs six `RAISE(ABORT)` triggers
(`V17_REENTRY_CANONICAL_BINDING_MISMATCH`, `V17_DONE_REQUIRES_MATCHING_CANONICAL_REENTRY`,
`V17_BOUND_REENTRY_EVENT_STAGE_MISMATCH`, `V17_BOUND_REENTRY_EVENT_WITHOUT_BINDING`,
`V17_DONE_EVENT_STAGE_MISMATCH`, `V17_DONE_EVENT_WITHOUT_RECEIPT`), with the design intent stated in
the source: *"Application code alone is not trusted to maintain this relation."*

Consequence for Finding A1: the `-O` fragility is a **reporting defect, not a safety hole**, because
the binding invariant survives removal of both the Python guard and the assertions. The initial
reviewer hypothesis that `-O` renders the gate vacuous was tested and is **not supported**.

## 4. Finding C — `RESTART` in the V17 receipt is a connection reopen

`restart_between_reentry_and_done_recovers_nonterminal_state` is produced by leaving one
`with EffectTerminalRuntimeV17GuardedCandidate(...)` block and entering another **inside the same
process**. There is no process termination, no signal, no power-loss or fsync path. What is
demonstrated is that recovery state is derived from the database rather than from memory — a real
but weaker property than the receipt name implies.

Since `F-V01-13` already carries "crash/restart/concurrency storage oracle" as an open blocker, this
naming should be aligned now to avoid the gap being considered pre-closed. Suggested key:
`reentry_state_survives_connection_reopen_same_process`.

## 5. Finding D — `BOOT_ANCHOR_CONTRADICTS_OWNER_FIXED_TARGET` (highest operational risk)

`research_entity/global/FRANK_V0_1_SERVER_BINARY_IDENTITY_AND_API_DIRECTIVE.md:18` states:

> "This supersedes `Andreas PC = final target` ..."

and `FRANK_V0_1_ONLY_PROGRAM_DIRECTIVE.md:13` fixes `TARGET_BODY = accepted Hostinger Ubuntu VPS`.

The repository-root `CLAUDE.md` — the first file every Claude Code organ reads, before any directive
in `research_entity/` — still declares four times:

```
GOAL=Frank v0.1 voll lauffähig auf Andreas PC
Mission anchor: Frank v0.1 voll lauffähig auf Andreas PC.
Clay's goal remains: Frank v0.1 voll lauffähig auf Andreas PC.
```

Every fresh organ therefore boots into a **superseded mission anchor** and re-enters every material
result against the wrong target, while the precedence rules instruct it to treat the newest
owner-fixed directive as authoritative. This is a silent divergence: no probe detects it, and the
`MISSION REENTRY` section actively amplifies it once per material step.

This finding is filed as the single highest-leverage correction in this audit because it is cheap to
fix and currently mis-steers every session at T0.

## 6. Structural observation (context, not a defect claim)

Counted over the audited checkout:

| Measure | Value |
|---|---|
| Python attributed to probes/tests/gates/oracles | 21,158 lines (60%) |
| Python attributed to the mechanism under test | 13,933 lines (40%) |
| Commits in the trailing 7 days | 1,104 |
| of which `evidence:` / `ci:` / `test:` | 161 / 119 / 115 |
| of which `feat:` | 19 |

Additionally, no evaluator, interpreter, lowering stage or code generator for `.clay` exists in the
checkout; `structured_frontend_v1.py` (112 lines, Lark) terminates at a TypedIR dictionary. Under
`CLAYCODE_ONLY` cognition this means the cognitive loop core currently has no executable substrate,
consistent with `F-V01-03 = OPEN`. It is stated here only so that component PASSes on the
periphery are not read as progress at the center.

## 7. Recommended actions, in leverage order

1. **Repair the boot anchor** (Finding D). Align repo-root `CLAUDE.md` with
   `TARGET_BODY = accepted Hostinger Ubuntu VPS`, or state explicitly why the PC anchor survives.
2. **Compute the check dictionaries** (Finding A1). Replace `assert cond` with
   `checks[name] = bool(cond)` and assert only `all(checks.values())` at the end. This costs
   ~30 minutes across the probe family, makes failing runs produce a *readable partial receipt*
   instead of a stack trace, and makes the denominators meaningful. A candidate patch for the V17
   gate is filed as a pull request against `gschaidergabriel/Dr.-Unterweger`.
3. **Reclassify two evidence labels** (A2, C) so they describe what is enforced.
4. **Sample the full request matrix for latency** (A3), or drop the figure from summaries.
5. **Propagate the V17 negative-baseline discipline** (B3) to work packages that currently claim
   improvement without a prior failing baseline.
6. **Add a multiprocessing contender variant** to the presence gate (B2).

## 8. Scope limits of this audit

- Three of roughly 200 probes were read line by line — the three quoted most prominently in the
  snapshot. Findings A1/A2/A3 are demonstrated for those three; the *pattern* is asserted, not
  proven, for the remainder.
- The structural counts in section 6 are whole-checkout measurements and are reliable.
- No canonical database, no production path and no external effect was exercised.
- The reviewer is an external Claude Code session, not a booted Clay organ; this report claims no
  Clay canonical authority and requests no promotion. Disposition belongs to Clay.
- One reviewer hypothesis (`-O` renders V17 vacuous) was falsified during the audit and is recorded
  as such in `NEGATIVE_RESULTS.jsonl`.
