# GO WP02/WP06 execution delta — 2026-08-10 00:27 +07

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay research worker; NOT Frank.  
Canonical parent: `RAE-8.8 / r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Fresh main observed before final durable writes: `394456c76e59dcd0f9f07d6db8d609ec162c4760`  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffaehig auf Andreas PC` under Ubuntu developer-system semantics.

## Result

This cycle produced an executable test/authority delta, not a release promotion.

1. Added the one bounded out-of-the-box experiment required by `go`: `tools/claycode_wp02_oob_trivia_metamorphic.py` (`d3d0378db5a6ff57085c800084adea17513c1752`). It generates a deterministic seeded family of horizontal space/tab perturbations around the V17 call-vs-dotted-relation boundary and requires call-tree identity under admitted trivia while the relation lesion remains semantically distinct. It edits no grammar and has explicit rollback/removal semantics.
2. Hardened `.github/workflows/claycode-vps-wp02-probe.yml` so the persistent self-hosted Hostinger execution job has `contents: read`, `actions/checkout` uses `persist-credentials: false`, and repository receipt persistence occurs only in a separate GitHub-hosted `contents: write` job after artifact transport and tested-SHA validation. Current workflow commit: `394456c76e59dcd0f9f07d6db8d609ec162c4760`.
3. Added `tools/claycode_wp06_current_main_replay.py` (`fc65cd8cd1ce6386e36876cbab073cf212d6bbfb`). It preserves the target-contract separation between V17 declarative WP02 evidence and the separately versioned typed-fn executable compiler slice. A single replay receipt binds selected V17 SHA, typed-fn grammar SHA, compiler SHA and current-main commit, then replays deep-expression, acyclic-call, native-C/Werror, object, Unicode/NUL and evaluator/native differentials.
4. Revised the shared BASE14 work item (`6aeeb9e80b8dd2c03fac8814cee360b8180d762f`) to remove ambiguous wording that could have forced the pure compiler to parse V17. V17 remains the sole declarative WP02 promotion candidate; typed-fn compiler evidence remains separate and cannot be relabeled as WP02.

## Hypothesis / strongest counterhypothesis

H1: the remaining BASE bottleneck is executable evidence closure rather than another ClayCode semantic redesign. V17 can close the declarative WP02 contract under strict/direct boundary falsifiers, while the already-hardened production compiler can retain its contract-separated typed-fn grammar and show current-main differential stability.

Counterhypothesis: V17 still exposes a contextual-lexer/lookahead boundary regression, or the newest production compiler hardening regresses when replayed on current-main; either failure must keep the affected gate open and trigger the smallest possible repair rather than a broad grammar rewrite.

The discriminating remote lane now executes both evidence classes without conflating them.

## Live primary-source fusion

Primary documentation used this cycle:

- Lark strict mode: https://lark-parser.readthedocs.io/en/latest/how_to_use.html
- Lark contextual-LALR example: https://lark-parser.readthedocs.io/en/latest/examples/advanced/conf_lalr.html
- GitHub Actions compromised-runner guidance: https://docs.github.com/en/actions/concepts/security/compromised-runners
- GitHub Actions automatic `GITHUB_TOKEN` permissions: https://docs.github.com/actions/how-tos/security-for-github-actions/security-guides/automatic-token-authentication
- GitHub artifact sharing between jobs: https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts
- actions/checkout credential behavior: https://github.com/actions/checkout/blob/main/README.md

Fusion:
- `strict=True` plus `interegular` remains mandatory for LALR conflict/collision evidence, but V17's regex lookahead means direct boundary tests remain independently necessary; a green generic collision pass cannot replace them.
- A persistent self-hosted runner should not need repository write authority merely to execute a measurement. Artifact transport permits the measurement job and persistence authority to be separated.

## Exactly one bounded out-of-box experiment

Experiment ID: `GO-OOB-WP02-TRIVIA-METAMORPHIC-V1`.

Status at this report write: **STAGED, EXECUTION RECEIPT MISSING**. The script is committed and wired into the Hostinger workflow, but no persisted `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json` exists yet. This is not counted as PASS or FAIL.

No second out-of-box experiment was introduced by this worker cycle.

## Measurement state

The current strict closure runner has independently been hardened by another Clay organ (`27e061460db0aa4c477e1d014d15554970f09a3c`) to capture elapsed time, child user/system CPU, faults, I/O, context switches and cumulative child max RSS for the WP02 sub-processes. The current workflow additionally records runner/platform/Python identity, exact tested GitHub SHA, selected grammar identity, execution-authority state, OOB result and WP06 replay result.

The WP06 replay itself records per-test elapsed/user/system CPU plus process max RSS and host/compiler identities. No remote numerical measurement is claimed until the transported Hostinger receipt exists.

## Current negative evidence / blockers

- `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json` returned GitHub 404 throughout this cycle, including after the current workflow commit. Classification: `MISSING_EVIDENCE`, not parser failure.
- No arbitrary workflow-dispatch capability is exposed to this worker. Push-triggered workflow code was materialized, but execution completion is not inferred from the push.
- Physical registered Andreas Ubuntu target acceptance remains mandatory and separate from the Hostinger VPS.
- Formal BASE package states are unchanged by these commits alone. No proxy/preliminary receipt is promoted to target acceptance.
- No final/paid model training was authorized or attempted.

## Architecture / test consequence

Architecture delta: `NO_CHANGE` to V17 or ClayCode semantics.

Test/authority deltas: `PROMOTED_TO_EXECUTABLE_TEST_INFRASTRUCTURE` only.

- exact selected V17 identity is preserved;
- direct lookahead/contextual-lexer boundary falsifiers are preserved beside strict/interegular;
- WP06 typed-fn grammar ancestry is explicit rather than silently transferred;
- self-hosted execution authority is reduced to read-only;
- receipt persistence is isolated to a separate hosted writer;
- negative/missing evidence stays first-class.

## Next frontier

1. Consume the first current schema-1.2 `LATEST_WP02_STRICT.json`; verify exact tested commit, exact V17 SHA, pinned Lark/interegular, strict/full-corpus/canonical components, OOB result and WP06 replay rows/resources.
2. If any component fails, repair only the smallest falsified surface and preserve the receipt as negative evidence.
3. If the remote preliminary evidence is clean, execute the registered physical Andreas Ubuntu BASE14 target path: strict WP02 target receipt, runtime/compiler bridge, all ten applications including real GUI, FULL_FRANK handoff, recovery/authority checks and independent WP14.
4. Only declared receipt gates may change formal work-package status.

Promotion: NONE. Research/test infrastructure and shared work revision: COMMITTED.
