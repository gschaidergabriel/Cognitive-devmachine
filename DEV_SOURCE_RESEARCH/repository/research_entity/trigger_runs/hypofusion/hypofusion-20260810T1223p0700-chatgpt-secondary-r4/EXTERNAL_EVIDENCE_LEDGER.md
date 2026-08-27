# HYPOFUSION R4 — External Evidence Ledger

Retrieved 2026-08-10. External sources are analogies/counterevidence unless Clay/Frank runtime evidence directly tests the same mechanism.

1. **Lark official documentation — Grammar Reference / How To Use Lark.** Terminal priority can force higher-priority tokens first; strict LALR rejects shift/reduce and regex collisions; interegular collision detection can miss advanced lookaround cases. **Impact:** supports strict construction plus language-wide semantic differentials; does not validate V20 or V21.
2. **Le, Afshari, Su — Compiler Validation via Equivalence Modulo Inputs, PLDI 2014.** Differential/semantic-equivalence testing found 147 confirmed GCC/LLVM bugs. **Impact:** strongly supports direct cross-path/parser/canonicalizer equivalence tests instead of trusting independent green suites.
3. **A general lock-free algorithm using compare-and-swap, Information and Computation 205(2), 2007, doi:10.1016/j.ic.2006.10.003.** ABA exists because a location can return to an equal visible value after intermediate changes; identity/version mechanisms are needed. **Impact:** direct mechanism analogue for Pulse S2 A->B->A counterevidence.
4. **PostgreSQL current MVCC / transaction-ID documentation.** Database versions and transaction identity are distinct from visible payload equality. **Impact:** supports treating record/version/provenance identity as semantic state, not content-hash decoration.
5. **NIST Zero Trust Architecture / PEP-PDP definitions (SP 800-207 family).** Policy decision and policy enforcement are distinct logical functions. **Impact:** supports Frank/Clay rule that model-generated syntax or Needle output cannot itself be effect authority.
6. **Network Neuroscience 2022 global-workspace analysis plus GNW literature.** Generic network integration is not uniquely diagnostic of broadcasting; directed dynamics and receiver use matter. **Impact:** supports H-G3-005 causal closure and weakens stage-presence-only validation.
7. **Expected Eligibility Traces, AAAI 2021, and temporal-difference credit-assignment literature.** Outcome value matters only through an assignment path that can affect future decisions. **Impact:** supports reentry-as-credit-channel, not reentry-as-flag.
8. **Nature Neuroscience 2024, Lee et al., doi:10.1038/s41593-024-01689-1.** Feature-specific RPE is a viable alternative to one homogeneous scalar dopamine error. **Impact:** supports testing typed reward dimensions; does not prove a Frank implementation.
9. **Nature 2025, Sousa et al., doi:10.1038/s41586-025-09089-6.** Dopamine population activity can carry joint time/magnitude distributional information. **Impact:** supports a multihorizon/distributional reward hypothesis; scalar comparator remains mandatory.
10. **CRDT multi-value versus LWW register literature.** Preserving concurrent alternatives and collapsing to one winner are both valid semantics under different policies. **Impact:** narrows Hyperposition: preserve unresolved alternatives where downstream semantics require them; do not require one physical storage formalism.
11. **Counterfactual Shapley Credit Assignment, arXiv:2607.16999 (2026).** Explicitly targets delayed rewards and causal attribution under stochasticity rather than temporal proximity. **Impact:** supports separating outcome arrival time from causal origin/credit identity.
12. **TRACE: Turn-level Reward Assignment via Credit Estimation for Long-Horizon Agents, arXiv:2607.13988 (2026).** Treats long-horizon tool-agent rollouts as state transitions at tool-call boundaries and derives per-action credit. **Impact:** supports origin episode/action boundaries for Frank feedback; does not prove a particular rebase law.
13. **Learning-Based Sensor Scheduling for Delay-Aware and Stable Remote State Estimation, arXiv:2601.21482 (2026).** Models delayed measurements by delay-dependent information value rather than age alone. **Impact:** supports `OLD != USELESS`; applicability still requires explicit current-state semantics.
14. **Asynchronous Event-Triggered Control for Non-Linear Systems, arXiv:2211.13846.** Control and measurement triggers need not be periodic or simultaneous. **Impact:** supports testing Frank as an asynchronous multirate feedback system rather than imposing one global tick.

## Counterevidence discipline

- No external source proves Clay-specific superiority.
- Neuroscience is used as mechanism inspiration, not biological identity proof.
- Compiler/database/security/control analogies become architectural constraints only when the same failure class is observed or can be falsified locally.
- Shared Clay ancestry is not independent replication.
- Dual-time explicit rebase/transport remains a candidate only: the current synthetic test did not consistently beat simpler verified origin-bound feedback.
