<!-- RAE_META
{"packet_id":"CLAYCODE_WP02_HASH_LOCKED_DEPENDENCY_CANDIDATE_20260810","title":"Hash-lock the ephemeral WP02 Hostinger dependency set","domains":["claycode","security","reproducibility","recovery"],"topics":["CC-WP-02","CC-WP-06","Hostinger","self-hosted runner","pip","hash checking"],"epistemic_class":"PRIMARY_DOCS_PLUS_CURRENT_REPO_AND_BUILD_ARTIFACT","claim_status_hint":"SUPPORTED_INTEGRATION_CANDIDATE_AWAITING_MATCHED_SELF_HOSTED_RECEIPT","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-10T00:38:00+07:00","canonical_parent":"RAE-8.8/r2/04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346","fresh_main_observation":"512bf299496144160efddf41ddc1d0e7e0a6bf81","artifact_commit":"0f4a570cb43125dc625358ef9906e76241b1049e","capability_event_commit":"fcd42b83ccb49769554b290a867fb678a0122711","confidence":"HIGH_MECHANISM_MEDIUM_INCREMENTAL_BENEFIT_EXECUTION_PENDING"}
RAE_META -->

## Result

Current main already hardened the persistent Hostinger self-hosted WP02/WP06 lane by replacing `pip --user` with a run-unique `pip --target` directory, `PYTHONNOUSERSITE=1`, module-path/version verification, dependency-tree hashing and verified cleanup. A concurrent worker then retriggered that lane at commit `512bf299496144160efddf41ddc1d0e7e0a6bf81`; no new schema-1.3 persisted receipt was visible at the start of this packet.

Fresh primary documentation adds one remaining reproducibility/security gap: pip's repeatable-install and secure-install guidance distinguishes exact version pinning from local hash checking. Version pins constrain which release is requested, while `--require-hashes` binds the accepted distribution bytes to locally declared hashes; `--only-binary :all:` avoids an unexpected source distribution path for this pure-Python test dependency set.

PyPI release metadata observed on 2026-08-10 provides the wheel SHA-256 values now materialized in `research_entity/claycode/base/CC_WP02_RUNNER_REQUIREMENTS_LOCK.txt`:

- `lark==1.3.1` wheel: `c629b661023a014c37da873b4ff58a817398d12635d3bbb2c5a03be7fe5d1e12`
- `interegular==0.3.3` wheel: `b0c07007d48c89d6d19f7204972d369b2a77222722e126b6aa63aa721dc3b19c`

## Hypothesis / strongest counterhypothesis

H1: adding `--require-hashes --only-binary=:all:` against the committed lock file to the existing ephemeral `--target` install will reduce supply-chain and cross-run ambiguity without changing ClayCode WP02/OOB/WP06 semantic outcomes.

Counterhypothesis: exact version pins, PyPI's distribution immutability/TLS path, module identity verification and the post-install dependency-tree digest already provide enough practical reproducibility for this lane; hash locking adds maintenance cost without detecting any meaningful drift.

## Cheapest discriminating test

Do not race-edit the workflow while the retriggered Hostinger job is active. At the next safe-point refresh:

1. consume the first valid schema-1.3 isolated Hostinger receipt from current main as the baseline;
2. integrate `CC_WP02_RUNNER_REQUIREMENTS_LOCK.txt` with `pip install --require-hashes --only-binary=:all: --target ... -r ...`;
3. rerun the same WP02 strict closure, the same **single** bounded `GO-OOB-WP02-TRIVIA-METAMORPHIC-V1` experiment and the same WP06 current-main replay;
4. require identical semantic PASS outcomes, exact locked versions, module paths inside the ephemeral root, cleanup=true, and a new receipt field binding the requirements-lock SHA-256;
5. compare wall time/resource rows; reject the change if it creates material instability or semantic drift with no security/reproducibility gain.

## Architecture / implementation consequence

- ClayCode semantics: `NO_CHANGE`.
- Frank Harness semantics: `NO_CHANGE`.
- WP02/WP06 acceptance status: `NO_PROMOTION` until actual receipt exists.
- Test/recovery architecture: candidate improvement only.
- Tool/API recommendation: targeted `pip --require-hashes + --only-binary=:all:` on top of the existing ephemeral target lane; event `CAPREC-CLAYCODE-WP02-PIP-HASHLOCK-20260810`.
- Rollback: remove the lock-file integration and return to the current ephemeral exact-version lane; no ClayCode semantic bytes need change.

## Primary sources

- GitHub secure use / self-hosted runner hardening: https://docs.github.com/en/actions/reference/security/secure-use
- GitHub self-hosted runner reference: https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- pip repeatable installs: https://pip.pypa.io/en/stable/topics/repeatable-installs/
- pip secure installs: https://pip.pypa.io/en/stable/topics/secure-installs/
- pip install `--target`: https://pip.pypa.io/en/stable/cli/pip_install/
- Python `PYTHONNOUSERSITE`: https://docs.python.org/3/using/cmdline.html
- PyPI lark 1.3.1 JSON: https://pypi.org/pypi/lark/1.3.1/json
- PyPI interegular 0.3.3 JSON: https://pypi.org/pypi/interegular/0.3.3/json

This packet is a durable research/implementation delta, not a claim that the self-hosted run has completed.
