# GO — CC-WP-02 V17 lookahead adversarial local replication

Date: 2026-08-10 06:38 +07  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay Research Entity worker; NOT Frank  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffähig auf Andreas PC`

## Scope / evidence class

`HOSTED_LOCAL_PROXY / RECONSTRUCTED_SEMANTIC_GRAMMAR / NON_STRICT`

This is independent adversarial replication evidence only. It does **not** satisfy CC-WP-02, Ubuntu target, or BASE acceptance and does not authorize a grammar change. The exact self-hosted Ubuntu version is carried separately by PR #59 and remains subject to actual runner allocation.

The local runtime has Lark 1.3.1 but no `interegular`, so this run intentionally used `strict=False`. The V9/V17 grammar rules were reconstructed from current repository source for semantic parsing; exact repository byte identity was not claimed for this proxy execution. Current authoritative source identities at retrieval were:

- `research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark` — Git blob `cdeff8095e6703a6889a60093876c8f0cb0a2b8a`
- `research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark` — Git blob `c3619e3168fdce9115bc7b9ab55425e7b02e0c2a`
- `tools/claycode_base_frontend.py` — Git blob `f7ac0d63c0d1f1fe3b8753c8246859340aba02ca`

## Fresh primary-source counterevidence already fused on main

Current Lark documentation warns that advanced regex constructs including lookahead/lookbehind can prevent `interegular` from detecting some collisions. Main already records this as `research_entity/claycode/base/CC_WP02_LARK_LOOKAHEAD_STRICT_MODE_COUNTEREVIDENCE_20260810.md` with `NO_GRAMMAR_CHANGE` and the narrowed interpretation:

`STRICT_PASS != EXHAUSTIVE_REGEX_COLLISION_PROOF_WHEN_ADVANCED_LOOKAROUND_IS_PRESENT`

## Hypothesis / strongest counterhypothesis

H: V17 can hide a semantic boundary instability behind `DOTTED_PREFIX_REL` lookahead even when ordinary strict construction succeeds.

Counterhypothesis: the minimal V17 repair is stable on the direct boundary family; broader mixed horizontal-trivia/RHS metamorphs reveal no additional semantic failure beyond the known V9 call-spacing counterexample.

## Exactly one bounded out-of-the-box experiment for this worker

A deterministic seed-1729 metamorphic boundary expansion was executed against the reconstructed V9/V17 semantic grammar:

- 768 dotted-prefix cases;
- 384 `Needle.owns (...)` horizontal-trivia call cases;
- 2 boundary equivalence pairs (comment boundary and call-parenthesis boundary);
- relation-label mutation discriminator;
- V9 lesion baseline + V17 rescue check.

Horizontal trivia was generated from spaces/tabs with lengths 1..64. RHS families included qid, REF, signed number, string, boolean, list, set, and call.

## Result

- V9 known `Needle.owns(X)` vs `Needle.owns (X)` counterexample: **REPRODUCED**.
- V17 same counterexample: **RESCUED**.
- Metamorphic V17 failures: **0**.
- Relation mutation `Needle.owns X` vs `Needle.lowers X`: **DISCRIMINATED**.
- Timed metamorphic parse attempts recorded: **1,158**.
- Mean parse+canonical-hash latency: **0.04147 ms**.
- p50: **0.04021 ms**.
- p95: **0.05215 ms**.
- p99: **0.07451 ms**.
- max: **1.14745 ms**.

Local runtime metadata:

- OS: `Linux-6.18.35-x86_64-with-glibc2.41`
- Python: `3.13.5`
- Lark: `1.3.1`
- interegular: `MISSING`
- strict parser collision check: `NO`

Disposition: `NO_NEW_FAILURE_FOUND_LOCAL_PROXY`.

This supports the strongest counterhypothesis only within the bounded local proxy family. It is **not** proof that V17 is collision-free and does not supersede the strict/current-main/full-corpus/canonical/Ubuntu requirements.

## Self-hosted Ubuntu lane

PR #59 (`research(wp02): adversarial V17 lookahead boundary replication`) contains the isolated exact-source test and a read-only self-hosted Linux/X64 workflow. At the observation point, the job was queued and had executed zero steps. Current shared research already classifies Clay-repository self-hosted allocation as a transport/repository-eligibility blocker: `QUEUED != EXECUTED != PASS`.

## Architecture / test re-entry

Architecture delta: `NO_CHANGE`.

Test obligation delta:

1. retain direct lookahead-boundary metamorphic replication alongside strict construction;
2. once a Clay-eligible self-hosted runner actually allocates, execute PR #59 or equivalent against exact current-main bytes with `lark[interegular]==1.3.1`;
3. preserve any counterexample as a negative result; otherwise record `NO_NEW_FAILURE_FOUND`, never correctness proof;
4. do not promote WP-02 until its stated exact-source/current-host receipts exist.

Affected routing: `claycode`, `capability`, `recovery`, `harness`.  
Paid/final model training: not attempted or authorized.
