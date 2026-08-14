<!-- RAE_META
{"packet_id":"CLAYCODE_V17_INTEREGULAR_LOOKAHEAD_LIMIT_20260810","title":"V17 strict/interegular is necessary but lookahead requires explicit boundary falsifiers","domains":["claycode","harness","security"],"topics":["CC-WP-02","V17","Lark","interegular","lookahead","lexical collisions","contextual lexer"],"epistemic_class":"PRIMARY_DOCS_PLUS_CURRENT_REPO_SYNTHESIS","claim_status_hint":"SUPPORTED_TEST_OBLIGATION_NO_ARCHITECTURE_CHANGE","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-10T00:25:00+07:00","canonical_parent":"RAE-8.8/r2/04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346","fresh_main_before_write":"27e061460db0aa4c477e1d014d15554970f09a3c","source_refs":["https://lark-parser.readthedocs.io/en/latest/how_to_use.html","https://pypi.org/project/lark/","https://pypi.org/project/interegular/","research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark","tools/claycode_base_frontend_validation.py","tools/claycode_v17_declarative_trivia_discriminator.py","tools/claycode_wp02_oob_trivia_metamorphic.py"],"confidence":"HIGH_TOOL_LIMITATION_MEDIUM_PRACTICAL_RESIDUAL_RISK","falsifier_or_next_test":"Require the exact-V17 self-hosted Ubuntu strict receipt to include the targeted call-vs-dotted-relation boundary suite; on Lark/interegular upgrades rerun the same suite and reject any semantic-hash or acceptance drift."}
RAE_META -->

## Result

Current Lark documentation says `strict=True` is the correct LALR gate for shift/reduce and regex collisions and that `interegular` is required for strict collision checking. The same official documentation also warns that advanced regex features such as lookahead/lookbehind can prevent `interegular` from detecting existing collisions. PyPI currently exposes Lark 1.3.1 with an `interegular` extra and interegular 0.3.3.

V17 intentionally contains a lookahead-bearing terminal:

`DOTTED_PREFIX_REL.11: /Needle\.(?:lowers|owns)(?=[ \t]+[^ \t\n;\/\(])/`

Therefore a clean strict/interegular construction is **necessary but not by itself sufficient evidence** that the lookahead boundary is collision-free for every admitted input. This is a tooling-evidence limitation, not evidence that V17 is wrong.

## Current repository coverage

The repository already supplies direct falsifiers for the exposed boundary rather than trusting collision analysis alone:

- `tools/claycode_base_frontend_validation.py` checks tight/spaced `Needle.owns(...)`, dotted `owns/lowers`, lexical discrimination and trivia equivalence.
- `tools/claycode_v17_declarative_trivia_discriminator.py` reproduces the V9 whitespace counterexample, requires V17 tight/spaced semantic equality, checks dotted relations, comment-not-RHS behavior, and scaling inputs up to 40,000 spaces.
- `tools/claycode_wp02_oob_trivia_metamorphic.py` provides the bounded seeded horizontal-trivia call-vs-relation lesion/falsifier used by the `go` VPS lane.

## Hypothesis / counterhypothesis

H1: V17 is adequate for the currently admitted declarative surface because exact boundary regressions cover the practical overlap that generic collision analysis may miss.

Counterhypothesis: a currently untested lookahead/contextual-lexer boundary still changes acceptance or semantic identity even when strict/interegular reports clean construction.

Cheapest discriminator: keep exact selected-grammar SHA + Lark/interegular versions bound to the receipt and require the targeted boundary suite on the same tested bytes. Any new accepted syntax or dependency upgrade must rerun/extend this suite before promotion.

## Architecture / work consequence

Architecture delta: `NO_CHANGE` to V17 or ClayCode semantics.

Test obligation: `SUPPORTED`. Strict/interegular remains mandatory, but no worker may use its green result as a substitute for the V17 call-vs-dotted-relation boundary regressions. Preserve both evidence classes in WP02 receipts.

Authority/release boundary remains unchanged: Hostinger is preliminary Ubuntu execution evidence; physical Andreas Ubuntu target acceptance is still mandatory; model output is not execution authority.