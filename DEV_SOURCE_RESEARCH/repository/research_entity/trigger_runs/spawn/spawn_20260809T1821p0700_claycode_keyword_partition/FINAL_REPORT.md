# SPAWN Final Report — ClayCode Keyword/Separator Strict-LALR Causal Partition

Run: `spawn_20260809T1821p0700_claycode_keyword_partition`  
Trigger: `spawn`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Origin branch: `claycode`  
Promotion: **NONE**

## 1. Stochastic selection

The branch was selected with OS-CSPRNG-backed `secrets.SystemRandom` using the canonical SPAWN distribution. The recorded raw branch draw was `132229831` on `[0,1000000000)`, selecting the ClayCode 50% interval.

Four current-evidence-derived microdirections were constructed. A second CSPRNG draw selected the keyword-as-ident partition direction (index 1 of 4).

This direction overlaps the currently active strict-LALR investigation, so it is explicitly treated as **replication with a new causal discriminator**, not as a falsely novel topic. The run independently reproduced the exact current grammar blob, partitioned the conflict roots, and exposed a separate strict-CI certification dependency failure.

Random selection carries no evidence weight.

## 2. Exact artifact reproduction

The tested artifact is:

`research_entity/trigger_runs/claycode/claycode-20260809T1717p0700-all-workers-production-parser/D_LALR_GRAMMAR_CANDIDATE_V3.lark`

The local test copy reproduced the exact Git content blob:

- Git blob SHA-1: `1d2a62053ffdd2fc008cbd33aecedf71b6387bce`
- SHA-256: `ef39d1460c0cea719422680e5c2037082b36c6e7fb3cd3c3c2c71dd131de6537`

Runtime:

- Linux 6.18.35 x86_64
- Python 3.13.5
- Lark 1.3.1
- interegular absent

This is local isolated Linux proxy evidence, not Andreas' Ubuntu target-host evidence and not live-FRANK evidence.

## 3. Main executable result

### 3.1 Baseline conflict structure

The exact D grammar builds in non-strict LALR/contextual mode but emits **13 shift/reduce conflict diagnostics**.

The diagnostics partition cleanly:

- 6 conflicts reduce `IF` as generic `ident` against lookaheads `(`, `in`, `subset_of`, `iff`, `or`, `requires`;
- 6 equivalent conflicts reduce `INVARIANT` as generic `ident` against the same lookaheads;
- 1 conflict comes from the nested newline separator repetition `_bsep: NEWLINE+` under surrounding separator repetition.

Strict construction fails on the parser-table conflict before regex-collision closure can be established.

### 3.2 Causal alias ablation

Removing only:

- `"invariant" -> ident_invariant`
- `"if" -> ident_if`

from the generic `ident` alternatives removes **12/13** observed conflicts. Exactly one separator/newline conflict remains.

This is strong local causal evidence that `if` and `invariant` are not merely correlated with the ambiguity: their dual role as reserved control/declaration tokens and generic identifiers is the reducible-symbol root of those 12 parser states.

Removing operator-keyword aliases alone does **not** close the parser conflicts. Rule/identifier priority annotations also do **not** close them. These negative results are retained.

### 3.3 Separator ablation

Changing:

`_bsep: ";" | NEWLINE+`

to:

`_bsep: ";" | NEWLINE`

in the alias-repaired variant removes the final observed shift/reduce conflict. The surrounding grammar already performs separator repetition, so the inner repetition was redundant in the tested parser states.

Combined minimal candidate SHA-256:

`2e51fd87c8eefc206170eaad47993f780374e6202fa361ff4bb56f2f06187dec`

Result in non-strict LALR/contextual construction:

- build: PASS
- captured shift/reduce/collision diagnostics: **0**

This is **not** strict closure yet.

## 4. Partial semantic-preservation discriminator

Four representative current-source cases were parsed with the baseline and combined repair:

1. dialect-local `invariant` declaration;
2. cycle-local `if` block;
3. keyword-like record fields including `status`, `dialect`, `version`, `requires`;
4. a `requires` expression operator.

Results:

- baseline parse: 4/4 PASS
- repaired parse: 4/4 PASS
- identical parse-tree SHA-256: 4/4

Tree hashes are preserved in `KEYWORD_PARTITION_EXECUTION_RECEIPT.json`.

Interpretation: the minimal repair can preserve representative current parse meaning while removing the known parser-table conflicts. This is **partial evidence only**. It is not a full G9/Dialect semantic-equivalence proof and does not justify grammar promotion.

The highest-value counterhypothesis remains that current or required ClayCode may legitimately use `if` or `invariant` as generic identifiers elsewhere. Full-corpus identifier-use and typed/canonical differential testing is therefore mandatory before selection.

## 5. New strict-CI implementation counterexample

After the combined repair removes the known parser-table conflicts, Lark strict construction progresses further and then fails with:

`LexError: interegular must be installed for strict mode`

The current committed strict-LALR GitHub Actions workflow installs only:

`lark==1.3.1`

It does not install `interegular` / the Lark strict regex-collision dependency.

Lark's official strict-mode documentation states that strict mode treats both parser ambiguities and regex collisions as errors and that regex-collision checking for the relevant lexers requires `interegular`.

Therefore the current CI surface has a distinct validation defect:

**once the parser-table conflict is actually repaired, the workflow cannot certify strict PASS with its declared dependency closure.**

It may instead report a dependency/infrastructure LexError. Grammar failure and validation-environment failure must be distinguished.

This is a new executable/implementation constraint for ClayCode + Harness validation. It does not prove the grammar repair is complete; installing `interegular` may expose additional regex collisions, which remain an explicit open counterhypothesis.

## 6. Required next discriminating sequence

The next high-information execution path is now narrow:

1. pin/install the strict regex-collision dependency in the CI environment, preferably the Lark 1.3.1-compatible `interegular` extra/dependency;
2. make the probe classify dependency/infrastructure failure separately from grammar conflict and regex-collision failure;
3. execute strict construction on the combined minimal candidate;
4. preserve every regex-collision diagnostic as negative/counterevidence;
5. if strict construction closes, run full current G9 + Dialect + relevant repository corpus parsing;
6. compare typed AST/canonical semantic hash rather than parse acceptance alone;
7. only then continue typed-function reintegration and real parser/canonicalizer/type-effect handoff;
8. later obtain Ubuntu target-host execution and target-reader evidence before BASE promotion.

Do not switch parser backends merely to bypass the current counterexample. Do not award BASE progress from this proxy run.

## 7. Mesh feedback

Material feedback:

- `claycode`: **IMPLEMENTATION_COUNTEREXAMPLE + NEW_CONSTRAINT + SUPPORTING_EVIDENCE**
- `harness`: **IMPLEMENTATION_COUNTEREXAMPLE + NEW_CONSTRAINT**

No architecture/scientific mechanism change:

- `frank`: NO_CHANGE
- `clayresearch`: NO_CHANGE
- `gwt`: NO_CHANGE
- `emergenz`: NO_CHANGE
- `hyperposition`: NO_CHANGE
- `claygraph`: NO_CHANGE
- `unifieddb`: NO_CHANGE

Parser acceptance, strict validation and branch agreement do not mint semantic truth, execution authority or emergence evidence.

## 8. Stage impact

`BASE_CLAYCODE_RELEASE`: **remains IN_PROGRESS**.  
`CLAYCODE_RELEASE_GATE`: **NOT_PASS**.  
`GENERAL_PURPOSE_GATE`: **NOT_PASS**.  
`CC-WP-02-PARSER-CANON`: **remains OPEN**.

This run materially reduces the uncertainty around the current D strict-LALR failure and exposes a validation dependency gap, but it does not satisfy the full parser/canonicalizer acceptance contract.

## 9. Stop condition

The current organ exhausted the high-value local discriminator available without inventing strict closure. Further decisive progress requires an `interegular`-enabled strict execution surface and then the full current corpus differential. No background continuation is claimed.

## 10. Durable artifacts

- `SPAWN_RECEIPT.json`
- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESES.json`
- `EVIDENCE_MANIFEST.json`
- `KEYWORD_PARTITION_EXECUTION_RECEIPT.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `FINAL_REPORT.md`

Compact result:

`exact D grammar -> 13 S/R conflicts -> {if,invariant aliases}=12 + nested NEWLINE=1 -> minimal repair=0 observed S/R -> strict dependency blocker exposed -> full strict+semantic differential still required`
