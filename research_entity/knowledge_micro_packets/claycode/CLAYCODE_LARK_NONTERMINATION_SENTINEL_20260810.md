<!-- RAE_META
{"packet_id":"CLAYCODE_LARK_NONTERMINATION_SENTINEL_20260810","title":"Bounded-termination sentinel for ClayCode WP02 parser dependency","domains":["claycode","harness","recovery","compiler"],"topics":["CC-WP-02","Lark","LALR","nontermination","watchdog","Hostinger"],"epistemic_class":"CURRENT_PRIMARY_ISSUE_PLUS_LOCAL_EXECUTION_AND_REMOTE_TEST_DELTA","claim_status_hint":"SUPPORTED_TEST_OBLIGATION_REMOTE_RECEIPT_PENDING_NO_RELEASE_PROMOTION","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-10T00:47:00+07:00","canonical_parent":"RAE-8.8/r2/04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346","implementation_commits":["69b09c4427acd1afb73c31221882e94b7db5b7b5","0f0b70a97df71c2fbcd51c100d45df0968e473b3"],"source_refs":["https://github.com/lark-parser/lark/issues/1585","https://lark-parser.readthedocs.io/en/latest/parsers.html","tools/claycode_wp02_oob_lark_nontermination_sentinel.py",".github/workflows/claycode-go-lark-nontermination-sentinel.yml"],"confidence":"HIGH_FOR_DEPENDENCY_HAZARD_AND_TEST_OBLIGATION_LOW_FOR_CLAYCODE_IMPACT_UNTIL_REMOTE_PRODUCTION_RECEIPT"}
RAE_META -->

# Result

Current primary Lark evidence contains open issue `lark-parser/lark#1585` reporting an infinite loop/nontermination case for LALR and CYK on the minimal recursive-priority grammar `start.1: "a" | start start*` with input `aa`; the issue reports Earley as terminating for the reproducer. This is dependency-level evidence, not a ClayCode semantic failure.

A bounded local diagnostic on this worker's Linux execution surface with CPython 3.13.5 and Lark 1.3.1 reproduced the LALR arm as a watchdog timeout while the same grammar under Earley and a simple LALR negative-control grammar both terminated successfully. The bounded experiment result was PASS for its narrow hypothesis. Approximate arm wall times observed in the single experiment were: LALR issue arm ~1.51 s to watchdog, Earley rescue ~0.60 s, simple LALR control ~0.57 s. These timings are diagnostic local rows only; they are not Hostinger or Andreas-target performance measurements.

# Hypothesis / strongest counterhypothesis

H1: ClayCode WP02 should treat parser bounded termination as an explicit acceptance/test property because the pinned parser dependency can exhibit input-dependent nontermination outside the known ClayCode corpus. A hard process watchdog plus regression sentinel can contain the dependency failure mode without changing ClayCode semantics.

Counterhypothesis: the upstream reproducer is irrelevant to the frozen ClayCode grammar/input language, and adding a watchdog/sentinel only adds test complexity without preventing any reachable production failure.

Cheapest discriminator: run the exact current production WP02 closure under an outer hard timeout on the real Hostinger Ubuntu lane and execute the one dependency sentinel as a separate non-promoting test. If production WP02 terminates/passes while the dependency sentinel reproduces the hazard with rescue/control closure, retain the sentinel as dependency regression coverage and keep architecture `NO_CHANGE`. If a frozen ClayCode input can make production WP02 exceed the bound, isolate the smallest grammar/input counterexample before any semantic redesign.

# Build / test delta

Implemented:

- `tools/claycode_wp02_oob_lark_nontermination_sentinel.py` at commit `69b09c4427acd1afb73c31221882e94b7db5b7b5`;
- `.github/workflows/claycode-go-lark-nontermination-sentinel.yml` at commit `0f0b70a97df71c2fbcd51c100d45df0968e473b3`.

The remote workflow preserves read-only self-hosted execution, `persist-credentials:false`, ephemeral pinned parser dependencies, an outer 90 s production-WP02 watchdog, exactly one bounded OOB experiment, dependency cleanup, artifact transport, and a separate GitHub-hosted receipt writer.

At packet creation time neither `research_entity/claycode/remote_vps/go_oob_lark/LATEST.json` nor the standard `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json` had materialized. Therefore remote runtime status for these newly triggered lanes is `PENDING_OR_UNKNOWN`, not PASS.

A concurrently added bounded issue-to-workflow dispatch bridge was used through issue #50 to request the existing standard WP02 Hostinger probe. Dispatch acceptance and actual runner execution remain separate evidence classes and require their own receipts.

# Fusion / architecture consequence

Architecture delta: `NO_CHANGE`.

Test obligation: `WP02_BOUNDED_TERMINATION_AND_DEPENDENCY_NONTERMINATION_SENTINEL`.

Recovery implication: parser work executed in acceptance/CI lanes should have a bounded outer deadline and emit explicit timeout classification rather than hanging indefinitely. A watchdog timeout is failure evidence, never silent retry/success.

No original Frank organ is replaced or fused by this result, so the historical-organ baseline replacement gate is not invoked by this narrow compiler-dependency hardening. The broader BASE/Harness release gates remain unchanged.

# Next falsifier

Consume a commit-bound Hostinger receipt. Require exact tested SHA, verified ephemeral dependencies/cleanup, production WP02 bounded completion/pass, and the sentinel's expected hazard+rescue+control pattern. Any production timeout or semantic drift becomes a new smallest-counterexample task; otherwise preserve the sentinel as regression coverage with no language redesign.
