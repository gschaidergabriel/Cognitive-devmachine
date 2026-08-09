# GO WP02 standalone differential delta — 2026-08-10 00:44 +07

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay research worker; NOT Frank.  
Canonical parent: `RAE-8.8 / r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Fresh shared-state head observed before this write: `f52998e97f8ee4b12ef0e6a6e1e6413a33604265`  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffaehig auf Andreas PC` under Ubuntu developer-system semantics.

## Result

This cycle materialized one bounded, reversible out-of-the-box WP02 differential and a dedicated receipt-bound Hostinger execution lane. It does **not** promote WP02, BASE, H1/H2/H3 or Frank release state.

Committed test artifacts:

- `tools/claycode_wp02_oob_standalone_equivalence.py` introduced at commit `b5314e94f26320e0bce304640b2936dcb78e0a8a`.
- `.github/workflows/claycode-go-oob-standalone.yml` introduced at commit `cc3ac96d876d98adcc4e1dae0f4cd823858b7e8b`.

The workflow uses the already-selected Hostinger + GitHub Actions self-hosted Ubuntu lane but is isolated from the concurrent main WP02 strict-closure workflow by a separate workflow and concurrency group. The self-hosted job has `contents:read`, checkout credentials are not persisted, dependencies are installed into an ephemeral target, and the hosted writer alone owns receipt persistence.

## Shared-state refresh / coordination

During this cycle the repository advanced concurrently. New owner-fixed swarm directives require field-matched tool/API recommendations and explicit capability selections, and forbid Together/Together.ai until explicit owner override. Existing shared coordination selected the receipt-bound Hostinger self-hosted Ubuntu lane for WP02 and rejected ChatGPT local sandbox as target-class evidence, arbitrary workflow dispatch as unavailable on the then-current connector surface, and direct SSH as unavailable/unauthorized.

This worker therefore reused the selected Hostinger lane rather than creating a competing execution authority. A concurrent worker also added `research_entity/claycode/base/CC_WP02_RUNNER_REQUIREMENTS_LOCK.txt`; this experiment consumes that hash-locked Lark 1.3.1 / interegular 0.3.3 dependency contract rather than duplicating an unlocked install policy.

## Live primary-source research

Current Lark documentation was rechecked before materializing the experiment.

Source-derived findings:

- Lark strict mode for LALR raises on Shift/Reduce and regex collisions and requires `interegular`; strict construction alone is not a complete falsifier for advanced regex/lookahead behavior.
- Lark documents generation of a stand-alone LALR(1) parser with `python -m lark.tools.standalone` and documents the generated `Lark_StandAlone` interface.
- Lark's contextual lexer uses parser-state expectations to constrain terminal matching, so translation/deployment equivalence is a meaningful independent check for V17's call-vs-dotted-prefix lookahead boundary.

Primary refs used in the live turn:
- official Lark How-To / strict mode;
- official Lark tools / stand-alone parser;
- official stand-alone example;
- official contextual-LALR example.

## Hypothesis / strongest counterhypothesis

H1: V17's current declarative semantics are stable across Lark's dynamic strict LALR/contextual runtime and its generated stand-alone LALR representation for the admitted G9/Dialect corpus and the exact Needle call/prefix boundary matrix.

Counterhypothesis: stand-alone generation/runtime changes token selection or tree construction at the V17 contextual/lookahead boundary, yielding a different accept/reject result or a different parse-tree identity. Any such differential keeps WP02 open and triggers the smallest possible parser/grammar repair; it is not averaged away.

## Exactly one bounded out-of-box experiment

Experiment ID: `GO-OOB-WP02-STANDALONE-PARSER-EQUIVALENCE-V1`.

Intervention:
- build the current V17 grammar dynamically with strict LALR/contextual Lark;
- generate a stand-alone parser from the same exact grammar bytes;
- parse each case twice in each implementation;
- compare acceptance, deterministic repeat tree identity and cross-implementation tree identity.

Corpus / boundary matrix:
- current G9 fusion specification;
- current Dialect Registry;
- tight, spaced, many-space and tab-separated `Needle.owns(...)` calls;
- `Needle.owns X` and `Needle.lowers X` prefix relations;
- bare owns accepted in the admitted context;
- bare lowers rejected;
- reserved-word negative cases;
- Unicode string case;
- newline-heavy record case.

Additional invariants:
- horizontal call trivia must preserve call-tree identity;
- call vs prefix-relation tree identity must remain distinct;
- no grammar/compiler/runtime semantic mutation is made;
- `promotion=NONE` regardless of PASS;
- rollback is deletion of the experiment/workflow/receipt only.

## Execution state / measurements

As of the final in-turn recheck, neither of these receipt paths existed on current GitHub main:

- `research_entity/claycode/remote_vps/oob_standalone/LATEST.json`
- `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json`

Classification: `EXECUTION_RECEIPT_PENDING / MISSING_EVIDENCE`, not PASS and not FAIL.

The dedicated OOB workflow is committed and push-triggerable on its own workflow/script/grammar/corpus/lock paths. Its receipt schema records exact tested GitHub SHA, repository head/dirty state, run ID/attempt, runner name/OS/arch/hostname/platform/Python, exact dependency lock SHA, Lark/interegular versions, generated stand-alone artifact hash/size/generation time, per-case parse times/tree hashes, experiment return code, authority boundary and release scope guard.

The current ChatGPT container was separately probed only as a capability falsifier: it has Python 3.13.5 and Lark 1.3.1, but `interegular` is absent and network/DNS access cannot clone GitHub. Under the strict-mode contract this environment cannot mint the strict WP02 receipt; it is therefore correctly rejected as a substitute for the selected Hostinger lane.

No remote numerical PASS values are invented while the transported receipt is absent.

## Architecture / test consequence

Architecture delta: `NO_CHANGE` to V17, ClayCode semantics, canonicalizer, compiler or Frank architecture.

Test delta: `COMMITTED`.

Evidence consequence:
- generated-parser translation/deployment equivalence is now a dedicated falsifier;
- a future PASS adds independent implementation-path evidence only;
- a future FAIL blocks promotion and localizes repair around generation/contextual/lookahead behavior;
- the existing strict/full-corpus/canonical/WP06/target gates remain authoritative.

## Negative evidence / blockers

- Main WP02 Hostinger receipt remains missing at final check.
- This cycle's stand-alone Hostinger receipt remains missing at final check.
- A workflow commit/trigger is not counted as executed evidence.
- The ChatGPT local container cannot satisfy strict Lark evidence because `interegular` is absent; network fetch is also unavailable there.
- Physical registered Andreas Ubuntu acceptance remains mandatory and separate from Hostinger preliminary evidence.
- No final/paid model training was authorized or attempted.

## Swarm fusion / current frontier

Concurrent branches observed during the cycle include:
- hash-locked WP02 self-hosted dependency hardening;
- canonical-syntax contract clarification;
- WP14 mixed-commit receipt binding regression/fix;
- a separate bounded Lark nontermination sentinel;
- real-Qwen/runner-scope research deltas.

None of those changes invalidates this experiment's premise. They reinforce the current program conclusion: the highest-value BASE action is receipt-backed execution closure, not another broad ClayCode semantic rewrite.

Next discriminators:
1. Consume and validate the first persisted main WP02 Hostinger receipt against exact tested SHA, V17 SHA, strict/full-corpus/canonical/OOB/WP06 components, dependency isolation and resource rows.
2. Consume and validate this stand-alone differential receipt; preserve any failure as first-class negative evidence.
3. If preliminary WP02 evidence is clean, execute the registered physical Andreas Ubuntu BASE target acceptance path; Hostinger remains preliminary.
4. Only declared receipt gates may promote WP02/BASE state.

Research/test write state for this cycle: `COMMITTED`; execution-effect state: `PENDING_RECEIPT`; architecture promotion: `NONE`.
