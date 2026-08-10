# FUSION 1 — current problem surface

Current stage is `BASE_CLAYCODE_RELEASE`. WP01 semantic freeze and WP02 parser/canonicalizer are PASS; WP03 typed IR and WP04 type/effect are OPEN. Owner-fixed 2026-08-10 target semantics add proactive/autotelic goals, open-web untrusted-data ingress, authenticated direct-message intent, and deterministic effect authority. Current G9 already separates `ProvExpr` from `CapabilityToken` and requires valid capabilities at `effect.commit`.

Highest-leverage tension:

1. Final deterministic effect gating can prevent unauthorized external effects.
2. Effect-bearing candidates may still consume GWT competition/recurrence before that gate.
3. Proactive self-generated goals need a standing authority boundary that survives restart without turning self-generated goals into authority.
4. Blanket web-taint blocking destroys useful web-informed tasks.
5. BASE semantics are frozen, so a useful candidate should compile from existing records/sets/constraints/capabilities rather than reopen the language.

Selected measurement question: can authenticated authority be compiled into a feasible action region that limits only effect-bearing GWT competition, while evidence/thought remains free and web-informed authorized actions remain usable?
