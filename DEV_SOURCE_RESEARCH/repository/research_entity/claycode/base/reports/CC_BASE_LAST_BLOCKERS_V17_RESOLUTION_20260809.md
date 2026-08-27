# ClayCode BASE — last blocker resolution delta (V17 contract-selected path)

Date: 2026-08-09
Actor: chatgpt-secondary (OpenAI / GPT-5.6 Sol)
Canonical parent: r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346
Status: SOFTWARE/ORCHESTRATION DELTA COMMITTED; RELEASE EVIDENCE STILL OPEN
Authority invariant: model output != execution authority

## Result

The remaining ClayCode BASE release path has been reduced to receipt-gated execution rather than unresolved software-routing ambiguity.

### Resolved in code/orchestration

1. **Physical self-hosted runner desktop restart gap**
   - Existing registered runners can restart without requiring a fresh registration token merely for restart.
   - Active desktop environment is imported/recovered before listener restart.
   - A real mapped Tk preflight is required.
   - The restarted listener process itself must inherit DISPLAY or WAYLAND_DISPLAY.
   - Failure receipts preserve the concrete failure cause.

2. **Stale parser-candidate / latest-wins drift**
   - The known-bad V6 latest-work path was superseded.
   - V5/V6 defaults in active declarative validation paths were removed.

3. **FRANK root-contract false release blocker**
   - The exact external `frank_runtime.clay` root semantic contract is preserved byte-identically with provenance and a drift-failing probe.
   - Existing generic structured ClayCode already implements the main procedural constructs (`fn`, `let`, `require`, `return`, `if`, `for`, calls/field access) without FRANK-specific authority primitives.
   - The root semantic contract is classified CONTEXT_ONLY_NON_GATE because the current APP10/WP13 production handoff selects other executable frozen FRANK programs. It becomes gate-relevant immediately if later selected as a production executable.

4. **V9/V10 horizontal-trivia parser bug**
   - Concrete counterexample: `Needle.owns(X)` and `Needle.owns (X)` can acquire different parse/canonical semantics under the predecessor high-priority dotted-prefix lookahead.
   - V17 (`D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark`) is the minimal declarative successor: it changes only dotted-prefix RHS lookahead so whitespace before call parentheses cannot change call semantics, while preserving the V5/V6 obligations.
   - Production declarative frontend, strict frontend validator, canonicalizer and production canonicalizer validation now contain the explicit trivia-invariance guard.
   - V17 selection is **not** a PASS claim. Strict interegular-enabled evidence is mandatory.

5. **Multiple independent WP02 grammar authorities**
   - Removed structurally.
   - `ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json` is now the single target-acceptance selection authority for WP02 declarative grammar identity.
   - It currently selects V17 and defines the strict/frontend/canonical receipt paths plus exact identity rule.
   - `claycode_base_andreas_target_runner_v2.py` and `claycode_andreas_ubuntu_acceptance_assembler.py` derive their WP02 grammar from this contract rather than hardcoding V9.
   - The legacy `claycode_andreas_ubuntu_target_gate.py` was collapsed into a fail-closed compatibility wrapper over the canonical contract-driven collector, eliminating a duplicated old V9 evidence battery.

6. **Strict local evidence fragmentation**
   - `tools/claycode_wp02_strict_local_closure_v2.py` is the one-command fail-closed local Ubuntu closure path for the contract-selected grammar.
   - For V17 it requires: strict V17 selection discriminator, strict LALR construction, exact G9 V3 and Dialect V3 full-corpus frontend acceptance, canonical trivia identity, grammar-bound declarative IR for both admitted corpora, and the production canonicalizer default.
   - Every self-contained component must bind to the exact selected grammar SHA.

7. **Hosted CI parser-evidence ambiguity**
   - A semantics-free PR probe showed both ClayCode BASE Frontend CI and the independent Research Entity Identity Guard failing before Step 1; a ClayCode rerun reproduced zero executed steps.
   - This is preserved as NEGATIVE_RESULT infrastructure evidence and is not interpreted as a grammar failure.
   - The hosted workflow has since been refactored to resolve the selected grammar from the acceptance contract, but hosted CI remains non-evidence until a run actually executes steps.

8. **Physical autoprobe stale trigger scope**
   - The Andreas self-hosted autoprobe now retriggers on the acceptance contract, all grammar candidates and the V17 discriminator instead of watching only V9.
   - The autoprobe records the contract-selected WP02 grammar in its probe receipt.

9. **Release manifest drift**
   - `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json` now records V17 as implementation-selected/promotion-pending, the V9 horizontal-trivia counterexample, V10/V15/V16 as non-promoted research lines, the hosted-CI negative result, and the real remaining promotion blockers.

## Real remaining blockers

These are deliberately not marked resolved because their required execution receipts are absent on current main:

1. **Strict selected-WP02 Ubuntu receipt**
   - `research_entity/claycode/base/receipts/LOCAL_WP02_SELECTED_GRAMMAR_CLOSURE.json`
   - or equivalent exact selected-grammar strict target evidence.

2. **Registered physical Andreas Ubuntu target execution**
   - `research_entity/claycode/target/ANDREAS_SELF_HOSTED_AUTOPROBE.json`
   - `research_entity/claycode/target_receipts/STRICT_LALR_D_SELECTED_WP02_TARGET_RECEIPT.json`
   - `research_entity/claycode/target_receipts/ANDREAS_BASE14_CLOSURE_RUN.json`
   - `research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json`

3. **Physical ten-application + FULL_FRANK evidence**
   - all ten required real application receipts including mapped Ubuntu GUI
   - five-path `FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT` with no semantic escape hatch.

4. **Independent WP14 + promotion**
   - WP14 strict audit PASS
   - zero open P0/P1 defects
   - release workspace 14/14 PASS and applications 10/10 PASS
   - manifest GENERAL_PURPOSE_GATE=PASS and CLAYCODE_RELEASE_GATE=PASS only from those receipts.

## Next executable commands

On a verified local Ubuntu executor with Lark + interegular:

```bash
python3 tools/claycode_wp02_strict_local_closure_v2.py
```

Then on the owner-registered physical Andreas Ubuntu developer system:

```bash
bash tools/claycode_bootstrap_andreas_self_hosted_runner.sh
python3 tools/claycode_run_andreas_target_acceptance.py
```

No proxy, sandbox, hosted pre-Step-1 failure, or model statement substitutes for these receipts.
