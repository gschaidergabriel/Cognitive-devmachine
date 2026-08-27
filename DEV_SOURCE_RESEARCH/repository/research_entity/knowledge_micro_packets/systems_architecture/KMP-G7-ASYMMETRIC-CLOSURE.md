# KMP-G7 — Asymmetric Coordination Closure

- **packet_id:** KMP-G7-ASYMMETRIC-CLOSURE
- **status:** OPEN / synthetic-supported + external-theory-supported
- **domains:** distributed-systems, systems-architecture, ClayCode
- **claim:** Coordination should be planned over asymmetric operation-pair/path dependencies plus declared invariants and authority, not only risky operation classes. Candidate outcomes: local, escrow/idempotent, pair-ordered or global closure.
- **evidence:** EXP-G7-PAIRWISE-CLOSURE-003: strict coordination 1.0, G6 class-risk `.81510`, exact pair-sensitive `.06281`, zero misses of the constructed dependency set. External invariant-confluence and Semi-Linearizability work motivates the mechanism.
- **critical boundary:** gains depend on correct dependency/invariant specification. Unknown coverage must fail closed.
- **next falsifier:** FRANK/twin partition replay with incomplete invariant specifications and correctness/availability metrics.
- **origin:** chatgpt-secondary / OpenAI / GPT-5.6 Sol / clay-20260808T0542p0700-chatgpt-secondary
