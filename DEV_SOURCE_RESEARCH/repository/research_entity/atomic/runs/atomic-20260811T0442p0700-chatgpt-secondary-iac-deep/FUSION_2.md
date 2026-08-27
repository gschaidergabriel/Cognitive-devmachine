# FUSION 2 — external collision and mechanism compression

Fresh external research destroys the broad story. Rational metareasoning already defines computation selection in terms of expected utility and cost. Value-directed belief approximation explicitly argues that state approximation error is the wrong objective when decision quality is what matters. Later POMDP simplification work goes further: adaptive bounds can accelerate planning while guaranteeing the same action as an unsimplified planner. Current LLM research also directly targets when to stop seeking or reasoning.

Therefore `epistemic uncertainty != decision uncertainty` is **not** a new general principle, and `stop when more thinking cannot change the action` cannot support a world-first claim.

The Frank-specific residue is narrower and useful:

1. Hyperposition already preserves unresolved alternatives as typed, provenance-bound branches rather than a single scalar belief/confidence.
2. Frank's effect semantics already distinguish action kind, exact target/scope, effect class, confirmation requirements and execution authority.
3. The loop-of-loops contract already wants adaptive recurrence and explicitly warns that low state-delta may be stagnation.
4. Therefore a cheap exact sufficient stop test can be expressed as a **projection from every current covered branch to a non-authoritative ActionSemanticKey**, followed by singleton-support checking.
5. The witness is valid only for the current semantic/state/decision/effect epochs and only when coverage is certified. Missing branches are not false branches.
6. This witness does not claim optimal metareasoning. It only proves that represented alternatives do not currently disagree on what action would be routed.

The strongest collision is fatal to a separate runtime organ: an ordinary `Set<ActionSemanticKey>` cardinality test is predicate-equivalent to IAC. Thus IAC should be evaluated as a typed loop-core contract/test interface, not as a new cognitive organ.

DCA and TRSE refine the boundary further. DCA can preserve distinctions before model/context assembly; TRSE can say whether recurrence is dynamically stable. Neither implies action invariance. Conversely IAC says nothing about whether the recurrence is stable or whether the context is complete unless their receipts are explicitly consumed.
