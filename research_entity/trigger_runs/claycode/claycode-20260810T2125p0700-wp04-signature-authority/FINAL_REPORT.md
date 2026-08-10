# ClayCode — WP04 exact signature authority cycle

Run: `claycode-20260810T2125p0700-wp04-signature-authority`

## Result

This cycle converted the WP04 signature-authority problem from one unresolved mechanism question into a measured layered pipeline.

1. **Explicit Clay semantic callable contract** is the semantic authority.
2. **Static exact source/signature admission** may validate pinned source bytes, exact qualified symbol, exact arity and annotation compatibility, but may not invent Clay semantic types.
3. **Runtime/binary/lease/effect binding** is a separate current-runtime identity gate.
4. **Execution admission remains downstream** and was never granted in this cycle.

The new static admission probe passed 11/11 local controls and the exact mirrored bytes passed on the Hostinger self-hosted Ubuntu runner in Dr.-Unterweger PR #113 / workflow run `31397569012`. No candidate runtime code was imported or executed.

A concurrent Clay worker supplied the first explicit versioned callable architecture candidate in PR #188:

`frank_reward.update(evidence: RewardOutcomeEvidence) -> RewardPlasticityReceipt`

with effect class `DERIVED_STATE`, binding authority `NONE`, execution `false`, and truth authority `NONE`.

Its first Target-VPS transport run (`31397756769`) failed before analysis because the workflow carried a stale content-addressed test-blob pin. The failure was preserved as negative continuity evidence. The workflow pin was repaired without semantic-code changes in Dr.-Unterweger commit `7beea9b6c7bca528236dd1e3154ef659567414ea`; rerun `31397986926` then passed the exact real-contract differential.

Measured Target-VPS frontier after that PASS:

- exact declared ordinary signatures: **1**
- unresolved ordinary signatures: **25**
- separate unresolved effect-boundary signatures: **1** (`Needle.execute/1`)
- total unresolved signature obligations: **26**
- execution admitted calls: **0**
- truth authority: **NONE**
- effect authority: **NONE**
- anchored equality components: **2 / 37**
- conflicting anchored components: **0**
- WP03: **OPEN**
- WP04: **OPEN**
- Frank v0.1: **IN_PROGRESS**

Exact successful hashes:

- contract semantic hash: `999283fef30bb709b5247fa002a9dfb513843daee4a22442e476bcb6522617a4`
- candidate TypedIR SHA-256: `02ab372c762e5c617a80ab3e8e62975474eae42467207135e4eeecf8b24f6f01`
- candidate constraint graph SHA-256: `62d549a239be2d4c3228c9fe0759535d9ebc425304cd4ef4be083d0810cbff49`
- anchor report SHA-256: `5d5a64b8c7ed5cd7a21824455421cb5f01be1c5b234285b57b9d32918733ba19`

## Hypothesis adjudication

The initial hypothesis that version-pinned runtime/source signatures could directly originate Clay CallContracts was **refuted as stated**. The strongest counterhypothesis was supported: runtime/source signatures can be a compatibility/binding oracle only after a versioned Clay semantic contract already exists. Otherwise the annotation-to-Clay mapping itself silently becomes a second semantic authority.

## Cross-branch fusion

The current complementary pipeline is therefore:

`PR #188 explicit Clay callable semantics`
→ `PR #191 / Dr PR #113 static exact source compatibility`
→ `PR #189 / Dr PR #111 current runtime/binary/lease/effect binding`
→ `downstream WP05 execution admission`

These are complementary lanes with shared ancestry; they are not counted as independent scientific replications.

## Negative evidence retained

- Caller-side type equalities, type-name resemblance, fuzzy/basename/suffix matching and model output remain insufficient signature authority.
- Runtime/source annotations cannot mint Clay semantic types.
- Stale content-addressed pins must fail before execution; the first PR #118 run did so correctly.
- One exact callable contract does not imply execution admission, WP04 completion or Frank-v0.1 acceptance.
- Generic Frank Deep Integrity remains separately red/unresolved on relevant Dr.-Unterweger PR heads; dedicated ClayCode passes do not override it.

## Next discriminator

Bind the exact `frank_reward.update/1` semantic contract to a current runtime/binary/lease identity through the separate runtime-binding gate **without executing it**. If no exact current runtime export exists, keep it non-executable. Then select the next explicit callable contract from architecture evidence and historical functional obligations—not from caller constraints—and repeat the exact differential.

No V18 syntax change, no Frank/self.root Harness mutation, no WP03/WP04 promotion, no whole-Frank acceptance, and no paid/final training authorization occurred in this run.
