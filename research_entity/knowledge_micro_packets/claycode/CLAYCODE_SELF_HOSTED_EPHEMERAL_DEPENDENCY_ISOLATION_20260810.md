<!-- RAE_META
{"packet_id":"CLAYCODE_SELF_HOSTED_EPHEMERAL_DEPENDENCY_ISOLATION_20260810","title":"Make WP02/WP06 self-hosted parser dependencies ephemeral and identity-bound","domains":["claycode","harness","security","recovery"],"topics":["CC-WP-02","CC-WP-06","Hostinger","self-hosted runner","dependency isolation","pip","reproducibility"],"epistemic_class":"PRIMARY_DOCS_PLUS_CURRENT_WORKFLOW_REVIEW","claim_status_hint":"SUPPORTED_HARDENING_CANDIDATE_NO_RELEASE_PROMOTION","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-10T00:28:00+07:00","canonical_parent":"RAE-8.8/r2/04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346","fresh_main_observation":"394456c76e59dcd0f9f07d6db8d609ec162c4760","source_refs":[".github/workflows/claycode-vps-wp02-probe.yml","tools/claycode_wp02_strict_local_closure_v2.py","https://pip.pypa.io/en/stable/cli/pip_install/","https://docs.python.org/3/using/cmdline.html"],"confidence":"HIGH_MECHANISM_MEDIUM_INCREMENTAL_BENEFIT","falsifier_or_next_test":"Run matched self-hosted WP02+OOB+WP06 lanes with current --user dependency installation and an ephemeral --target/PYTHONNOUSERSITE lane; require identical semantic outcomes and verify the ephemeral lane removes its dependency directory after receipt creation. Treat any unexplained result drift as contamination evidence, not automatically as a ClayCode semantic regression."}
RAE_META -->

## Result

The current self-hosted Hostinger workflow correctly separates execution authority from receipt-write authority: the VPS job is `contents: read`, checkout credentials are not persisted, and a separate GitHub-hosted job owns the write. The same execution job currently installs `lark==1.3.1` and `interegular==0.3.3` with `python3 -m pip install --user` before WP02 strict closure, the bounded trivia falsifier and the new WP06 current-main replay.

That is executable, but it creates avoidable cross-run state on a persistent self-hosted runner. A previous or failed run can leave user-site packages behind, and the next run mutates the same user install again. Exact version pins constrain package versions, but they do not make the execution environment ephemeral or prove cleanup/recovery.

Primary Python packaging documentation provides a narrower mechanism: `pip install --target <dir>` installs packages into an explicit directory, and CPython documents `PYTHONNOUSERSITE` as preventing the user site-packages directory from being added to `sys.path`.

## Hypothesis / counterhypothesis

H1: Running the WP02/OOB/WP06 probe with exact dependencies installed into a run-unique temporary target, `PYTHONNOUSERSITE=1`, verified import paths/versions, a dependency-tree hash, and verified cleanup will reduce hidden cross-run state without changing ClayCode outcomes.

Counterhypothesis: because Lark/interegular are already exact-version pinned and the lane is otherwise controlled, the additional isolation adds complexity without detecting any practical result drift.

Cheapest discriminator: matched same-commit runs. Compare WP02 semantic receipts, OOB result, WP06 replay result and resource rows. The ephemeral run must also record dependency versions, module paths, a deterministic tree digest and successful deletion of the temporary dependency root.

## Build consequence

Architecture delta: `NO_CHANGE` to V17, ClayCode semantics, WP06 semantics, or authority boundaries.

Hardening candidate:
1. replace persistent `pip --user` in the self-hosted probe with run-unique `pip --target` installation;
2. export `PYTHONNOUSERSITE=1` and put only that target ahead of normal imports;
3. verify `lark.__file__` and `interegular.__file__` resolve under the temporary root and versions equal the pinned contract;
4. hash the installed dependency tree and retain only the digest/metadata in the receipt;
5. delete the temporary dependency root before finalizing the receipt and record cleanup success;
6. keep the existing read-only self-hosted execution + separate hosted receipt writer unchanged.

This is a reproducibility/recovery improvement, not a release gate by itself. Existing remote receipts remain evidence for exactly what they measured; they should not be retroactively relabeled as failures merely because this stronger isolation is available.

## Concurrency receipt

An attempted direct workflow update was rejected by GitHub contents-API CAS with HTTP 409 because another worker had changed the same workflow after it was read. The stale write was not forced. The refreshed workflow was then observed to contain a useful concurrent improvement: exact current-main WP06 replay was added after WP02/OOB. This packet therefore records the non-overlapping dependency-isolation delta instead of overwriting the newer worker's change.
