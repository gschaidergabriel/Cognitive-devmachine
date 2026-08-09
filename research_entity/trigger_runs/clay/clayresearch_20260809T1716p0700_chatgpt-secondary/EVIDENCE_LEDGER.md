# Clayresearch 2026-08-09 — Evidence Ledger

Run: `clayresearch_20260809T1716p0700_chatgpt-secondary`

## Evidence classes

This run keeps source classes separate. Repository state and executed synthetic experiments are not conflated with external papers; preprints are not treated as standards; implementation documentation is not treated as a formal proof.

### A. Verified current repository state

- `RESEARCH_ENTITY_CANONICAL.json`: RAE-8.8, revision 2, state hash `04234ef...`.
- `PROGRAM_STATE.json`: Level 0 PASS; current stage `BASE_CLAYCODE_RELEASE`; downstream stages blocked in sequence.
- `CLAYCODE_RELEASE_WORKSPACE.json`: 14 BASE work packages OPEN, general-purpose gate NOT_PASS; Ubuntu Linux developer system is the only Frank v0.1 target host.
- `CLAYCODE_G9_FUSION_SPEC_V3.clay`: current semantic candidate contains delta calculus, `IncrementalReceipt`, capability-bearing effects, typed graph/hyperrelation state, GWT causal axes, `EffectIntent`, bounded equality saturation and the main recurrent cycle.
- `FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md`: OPEN cross-branch hypothesis requiring typed loop regimes/readouts and intervention rather than recurrence-as-proof.

**Boundary:** repository status establishes project state and declared mechanisms, not that the unfinished compiler/runtime already executes them.

### B. External implementation / official documentation

1. **Bytecode Alliance `cap-std`** — repository `bytecodealliance/cap-std`, README. Capability-based versions of standard APIs; `Dir`-based file access avoids ambient path authority; path escapes return permission errors; ambient directory opening is explicitly unsandboxed. The project also states that cap-std alone does not sandbox arbitrary untrusted Rust code because unsafe/ambient APIs can bypass it.
   - Supports: unforgeable/scoped resource-handle lowering and explicit ambient-authority boundary.
   - Does not establish: complete Clay foreign-code closure or Linux end-to-end mediation.

2. **Bytecode Alliance Wasmtime/WASI official documentation** — security, WASI and component resource documentation.
   - Supports: capability-style filesystem/resource access; host-defined resource handles; sandboxed guest/host boundary as an implementation candidate.
   - Important counterevidence/constraint: host configuration matters; threads/resource-limiting integration and other runtime boundaries must be tested rather than assumed complete. Terminal/control-sequence output can itself be security-relevant, so output sinks are not automatically PURE.

3. **egglog official project documentation** — repository `egraphs-good/egglog`.
   - Supports: practical combination of equality saturation and Datalog, parallel execution option, benchmark-driven performance discipline, and a real implementation path for bounded equivalence/dataflow research.
   - Does not establish: that EqSat belongs in ClayCode semantics or that it improves the current BASE path.

### C. External scholarly/preprint research

1. **Fides: Securing AI Agents with Information-Flow Control**, arXiv:2505.23643.
   - Relevance: confidentiality/integrity labels and deterministic enforcement for agent information flows.
   - Use here: independent mechanism support for separating model reasoning from protected-data/effect flow.

2. **AgentSecBench**, arXiv:2605.26269.
   - Relevance: instruction, retrieval and capability integrity; provenance projection/capability restriction/output validation.
   - Use here: reinforces that prompt text alone is weaker than capability/integrity boundaries.

3. **Towards Verifiably Safe Tool Use for LLM Agents**, arXiv:2601.08012.
   - Relevance: structured tool specifications and capability/confidentiality/trust labels.
   - Use here: supports explicit tool/effect contracts while remaining a preprint rather than a deployed Clay proof.

4. **Partial Effective Information Decomposition (PEID)**, arXiv:2605.03267.
   - Relevance: max-entropy interventions and decomposition of unique/synergistic causal contributions, including higher-order structure.
   - Use here: candidate emergence measurement alongside lesion/rescue/shuffle controls.
   - Boundary: intervention assumptions and estimator behavior must be validated on the exact variables/scales used by Frank.

5. **Differentially maintained recursive queries**, arXiv:2208.00273.
   - Relevance: differential maintenance can improve recursive query execution but may incur substantial memory cost; selective recomputation is a live alternative.
   - Use here: supports `IncrementalReceipt` plus drop/recompute rather than dogmatic always-incremental maintenance.

6. **FlowLog**, arXiv:2511.00865.
   - Relevance: explicit relational IR, semi-naive recursion, SQL optimization and Differential Dataflow for batch/incremental execution.
   - Use here: implementation analogue for typed incremental semantic views.

### D. Executed synthetic evidence

See `EXPERIMENTS.md`.

- EXP-SAFE-001: 0/100k safe intersection authority violations; 99.866% violations in ambient/request-as-grant comparator; 0/50k nested-safe violations.
- EXP-HYPER-001: naive unordered pairwise role projection collided 50k/50k under role permutations; reified role-bearing representation 0/50k.
- EXP-INCR-001: favorable local topology median affected closure 0.156% of 100k nodes; synthetic median traversal ratio ~279.6× versus full trivial scan.
- EXP-REENTRY-001: favorable smooth-state regime truthful re-entry MSE 0.1523 vs lesion 0.6384 vs shuffled 1.1847.
- EXP-REENTRY-002 NEGATIVE_RESULT: fixed truthful re-entry became worse than lesion across most high-process-volatility settings despite high temporal autocorrelation.

### E. Evidence not obtained / not promoted

- No current Ubuntu ClayCode compiler/runtime execution receipt was produced by this hosted ChatGPT surface.
- No live Frank H1/H2/H3 replay was executed.
- No target Qwen-class 4B model experiment was executed.
- No OS-level generated Python/Bash/C/Rust/Wasm/FFI escape matrix was executed.
- No current-stage work package is marked PASS by this run.
- Reddit/community anecdotes were not used as evidence because the active technical-source policy for this worker requires primary sources.

## Highest-information next evidence

1. Compile and run a minimal `LoopDynamicsReadout` program through parser → canonical IR → type/effect → evaluator/runtime.
2. In the same BASE slice, lower a `CapabilityToken` to an Ubuntu capability/resource handle and execute nested child-effect non-amplification tests.
3. Add terminal-sink/control-sequence policy to APP-08 negative tests.
4. Instrument innovation/process-vs-observation volatility and compare fixed vs adaptive re-entry gain under matched replay.
5. Only after those receipts exist should semantic change or stronger loop/emergence claims be considered.
