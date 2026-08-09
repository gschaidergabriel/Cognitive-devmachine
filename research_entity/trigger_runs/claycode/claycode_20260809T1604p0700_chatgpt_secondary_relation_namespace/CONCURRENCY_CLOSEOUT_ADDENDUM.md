# Concurrency Closeout Addendum — Full-G9 Assimilation

Run: `claycode_20260809T1604p0700_chatgpt_secondary_relation_namespace`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Why this addendum exists

After this run's `FINAL_REPORT.md` was committed, the parallel whole-current-G9 surface-closure worker completed. Its result is material to the parser-freeze decision and is therefore assimilated here rather than left for a later trigger.

Completed concurrent report:

`research_entity/trigger_runs/claycode/claycode-20260809T1605p0700-chatgpt-full-g9-surface-closure/FINAL_REPORT.md`

Commit observed at closeout: `74669d6f661f5497be392ca3093d4fd24f4275e0`.

## Combined evidence

Whole-current-G9 worker:

- complete current top-level G9 chunks: **86**;
- current checked-in grammar proxy: **61/86 PASS, 25/86 FAIL**;
- strict normalization candidate N: **86/86 PASS**;
- candidate N used four general surface additions (`if`, postfix optional value, comparisons, `or`) plus 20 explicit source normalizations;
- no new cognitive/runtime semantic primitive was required for parse closure in that proxy;
- N was deliberately **not selected** solely from parse closure.

This run's relation-namespace discriminator adds a new constraint to the concurrent N/S/D comparison:

- current `@relation` candidate S passed its relation-only corpus, but when mixed with the already-existing `@ref` namespace the combined proxy produced **5/7** under LALR contextual and **3/7** under LALR basic, versus **7/7** under Earley dynamic;
- a lexically disjoint sigil control and the quoted generic relation form were **7/7 across all three modes**;
- therefore current S as written cannot be treated as a backend-neutral lexical namespace without a production-parser/full-corpus proof or lexical redesign.

Declared finite relation candidate D remains independently live at the proxy level: its concurrent resolver accepted the sampled declared relations and failed unknown relation words closed. It has not yet won the full-corpus matched comparison.

## Refined freeze hypothesis

The highest-value shared oracle for the matched N/S/D test is now:

`surface source -> deterministic typed canonical Relation IR -> semantic_hash`

The winning source spelling should be selected only after identical full-corpus testing of:

1. complete G9+dialects parse closure;
2. mixed `@ref` + relation cases and all other overlapping token classes;
3. intended typed AST equality;
4. canonical roundtrip and semantic-hash stability;
5. malformed/undeclared relation fail-closed behavior;
6. diagnostics and mutation survival;
7. migration edit count;
8. source/token/context cost;
9. target-reader repair/accuracy cost;
10. parser/compiler complexity and latency.

A compact surface may still win. The current evidence only says that compactness must not be purchased by lexical ambiguity or parser-backend dependence.

## Program implication

- `CC-WP-02-PARSER-CANON` remains OPEN.
- No ClayCode semantic generation or BASE gate is promoted by this addendum.
- Candidate N remains OPEN/NOT_SELECTED despite 86/86 parse closure.
- Current `@relation` S is CHALLENGED/NOT_SELECTED as written, not globally REFUTED for every possible redesigned sigil syntax.
- Candidate D remains OPEN.
- The typed canonical Relation-node hypothesis is strengthened as the common comparison target.
- Continue directly into the production parser and canonical IR rather than inventing a new FRANK-specific semantic primitive.

## Concurrency boundary

Additional same-window workers have begun or completed HTTP/application, semantic-publication, control-flow and Ubuntu effect-boundary work. This addendum does not infer acceptance from their commit names. The authoritative `CLAYCODE_RELEASE_WORKSPACE.json` must remain the gate source; no application or work-package PASS is claimed here unless that workspace is explicitly advanced by validated evidence.
