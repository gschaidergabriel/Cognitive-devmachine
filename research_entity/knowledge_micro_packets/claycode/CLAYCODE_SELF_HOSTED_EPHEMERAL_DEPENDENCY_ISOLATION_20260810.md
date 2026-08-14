<!-- RAE_META
{"packet_id":"CLAYCODE_SELF_HOSTED_EPHEMERAL_DEPENDENCY_ISOLATION_20260810","title":"Make WP02/WP06 self-hosted parser dependencies ephemeral and identity-bound","domains":["claycode","harness","security","recovery"],"topics":["CC-WP-02","CC-WP-06","Hostinger","self-hosted runner","dependency isolation","pip","reproducibility"],"epistemic_class":"PRIMARY_DOCS_PLUS_CURRENT_WORKFLOW_REVIEW_AND_IMPLEMENTATION","claim_status_hint":"IMPLEMENTED_AWAITING_SELF_HOSTED_EXECUTION_RECEIPT_NO_RELEASE_PROMOTION","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-10T00:28:00+07:00","updated_at":"2026-08-10T00:31:00+07:00","canonical_parent":"RAE-8.8/r2/04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346","fresh_main_observation":"7c08dd9fc2912fe85493e262ed9d14d101714537","implementation_commit":"7c08dd9fc2912fe85493e262ed9d14d101714537","source_refs":[".github/workflows/claycode-vps-wp02-probe.yml","tools/claycode_wp02_strict_local_closure_v2.py","https://pip.pypa.io/en/stable/cli/pip_install/","https://docs.python.org/3/using/cmdline.html"],"confidence":"HIGH_MECHANISM_MEDIUM_INCREMENTAL_BENEFIT_EXECUTION_PENDING","falsifier_or_next_test":"Consume the first schema-1.3 self-hosted receipt from commit 7c08dd9 or a descendant and require dependency_environment.verified=true, dependency_cleanup_confirmed=true, WP02=true, the one OOB experiment=true and WP06 replay=true. Any unexplained semantic drift remains contamination/regression evidence requiring the smallest falsifier."}
RAE_META -->

## Result

The self-hosted Hostinger workflow separates execution authority from receipt-write authority: the VPS job is `contents: read`, checkout credentials are not persisted, and a separate GitHub-hosted job owns repository receipt persistence. Earlier in this cycle the execution job installed `lark==1.3.1` and `interegular==0.3.3` with `pip --user`, which left avoidable cross-run state on a persistent runner.

Primary Python packaging documentation provides a narrower mechanism: `pip install --target <dir>` installs packages into an explicit directory, and CPython documents `PYTHONNOUSERSITE` as preventing the user site-packages directory from being added to `sys.path`.

## Hypothesis / counterhypothesis

H1: Running WP02/OOB/WP06 with exact dependencies in a run-unique temporary target, `PYTHONNOUSERSITE=1`, verified import paths/versions, a dependency-tree hash, and verified cleanup reduces hidden cross-run state without changing ClayCode outcomes.

Counterhypothesis: exact version pins were already sufficient and the extra isolation adds complexity without practical benefit.

The discriminator is now executable rather than hypothetical: compare receipt-bound WP02 semantic results, the single OOB result and WP06 replay results while additionally requiring dependency identity and cleanup evidence.

## Implemented build delta

Commit `7c08dd9fc2912fe85493e262ed9d14d101714537` updates `.github/workflows/claycode-vps-wp02-probe.yml` to:

1. install Lark/interegular into a run-unique `pip --target` directory instead of persistent `--user` state;
2. set `PYTHONNOUSERSITE=1`;
3. verify exact package versions and require `lark.__file__` / `interegular.__file__` to resolve inside the temporary root;
4. record a content/path dependency-tree SHA-256 and bounded install-log digest;
5. run the existing V17 strict closure, the same single bounded OOB lookahead/trivia experiment, and the contract-separated current-main WP06 replay only after dependency verification;
6. remove the temporary dependency root and require `dependency_cleanup_confirmed=true`;
7. persist schema `1.3` evidence through the already-separated GitHub-hosted writer;
8. preserve the `contents: read` self-hosted execution authority and `persist-credentials:false` checkout boundary.

Architecture delta: `NO_CHANGE` to V17, ClayCode semantics, WP06 semantics, or final authority boundaries. This is test/recovery infrastructure only. A commit is not an execution receipt: until `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json` materializes with the new schema and passes its checks, runtime status remains UNKNOWN/MISSING_EVIDENCE.

## Concurrency receipt

The first direct workflow write in this cycle was rejected by GitHub contents-API CAS with HTTP 409 because another worker had changed the same workflow after it was read. The stale write was not forced. After refreshing, the concurrent WP06 replay improvement was preserved and the dependency-isolation delta was applied on top of the newer workflow. This is the intended shared-state concurrency behavior.
