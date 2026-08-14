# Clayresearch 2026-08-09 — Experiment Receipts

Run: `clayresearch_20260809T1716p0700_chatgpt-secondary`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Evidence class: synthetic mechanism tests executed during this trigger run. None is a live Frank, Ubuntu compiler, Harness, or target-model result.

## EXP-SAFE-001 — Capability intersection / authority non-amplification

**Question.** Does a simple parent-capability intersection algebra prevent synthetic child authority amplification?

**Setup.** Universe of 32 abstract effects. 100,000 randomized parent/request cases. Safe delegation computed `grant = parent ∩ request`. Unsafe/ambient comparison gives the child its requested set. Additional 50,000 nested trials, delegation depth 8, repeatedly intersect child requests with current authority.

**Results.**

- Safe intersection violations: **0 / 100,000**.
- Ambient/request-as-grant violations: **99,866 / 100,000 = 99.866%**.
- Nested safe-intersection violations: **0 / 50,000**.
- Mean safe grant cardinality: **2.00046** effects.
- Mean ambient requested cardinality: **8.00096** effects.

**Interpretation.** The algebraic non-amplification invariant is mechanically coherent in this abstract model. It does **not** prove that Linux/Wasm/FFI/tool execution is completely mediated. The next falsifier is an executable child-process/FFI escape matrix on the Ubuntu target.

---

## EXP-HYPER-001 — N-ary role-binding projection collision

**Question.** Does naive unordered pairwise projection preserve role identity for n-ary relations?

**Setup.** 50,000 randomized relations of arity 3–5. For each relation, member identities are held constant while role assignments are permuted. Compare: (a) naive unordered member-pair projection; (b) a reified role-bearing representation.

**Results.**

- Naive unordered pairwise collisions: **50,000 / 50,000**.
- Reified role-bearing collisions: **0 / 50,000**.

**Interpretation.** Naive pairwise flattening destroys role permutation identity by construction. This supports explicit role semantics but **does not prove native hyperedges are mandatory**: a reified pairwise encoding can preserve the information. H0-H remains open.

---

## EXP-INCR-001 — Local dependency closure versus global recomputation

**Question.** How much state is touched by localized updates in a deliberately sparse/local dependency topology?

**Setup.** Synthetic graph with 100,000 nodes: 1,000 independent components × 100 local DAG nodes. Each trial updates 10 mid-component nodes and traverses affected dependency closure. 50 trials. Compare closure traversal with a trivial full-node scan.

**Results.**

- Median affected nodes: **156 / 100,000 = 0.156%**.
- 95th percentile affected fraction: **0.262%**.
- Median incremental closure traversal: **0.0418 ms**.
- Median full trivial scan: **11.69 ms**.
- Synthetic median ratio: approximately **279.6×** in favor of local closure traversal.

**Interpretation.** The result supports the feasibility of G9 `IncrementalReceipt`/dependency-closure hot paths under strong locality. It is intentionally favorable and must not be projected onto Frank until real ClayGraph/UnifiedDB dependency distributions are measured. The likely failure modes are broad fan-out, bookkeeping overhead and retained differential-state memory.

---

## EXP-REENTRY-001 — Truthful vs lesion vs shuffled re-entry

**Question.** Can truthful recurrent state improve noisy state estimation relative to no re-entry and shuffled re-entry?

**Setup.** Synthetic AR(1)-style latent state, `rho=0.97`, state-noise sigma `0.15`, observation-noise sigma `0.8`; fixed estimator mix `alpha=0.35`, `beta=0.65`. Compare truthful previous-state re-entry, no re-entry/direct observation, and shuffled previous-state control.

**Results (MSE).**

- Truthful re-entry: **0.1523**.
- No re-entry/direct observation: **0.6384**.
- Shuffled re-entry: **1.1847**.
- Truthful vs lesion improvement: approximately **76.1%**.
- Truthful vs shuffled improvement: approximately **87.1%**.

**Interpretation.** Under this favorable smooth-state/noisy-observation regime, informative re-entry is useful and shuffled recurrence is actively harmful. This is a state-estimation proxy, not evidence that Frank's GWT/re-entry mechanism has the same causal benefit.

---

## EXP-REENTRY-002 — Volatility sweep; negative result for fixed re-entry gain

**Question.** Is fixed truthful re-entry monotonically beneficial as temporal recurrence increases?

**Setup.** Same estimator family, but process/state noise raised to sigma `1.0`; observation noise remains approximately `0.8`. Sweep `rho` across `[0, 0.3, 0.6, 0.8, 0.9, 0.97]` while keeping the same fixed gain.

**Results (truthful MSE vs no-reentry MSE).**

- `rho=0.00`: **0.6509 vs 0.6369** — truthful worse.
- `rho=0.30`: **0.6271 vs 0.6385** — slight truthful benefit.
- `rho=0.60`: **0.6622 vs 0.6389** — truthful worse.
- `rho=0.80`: **0.7353 vs 0.6368** — truthful worse.
- `rho=0.90`: **0.7864 vs 0.6381** — truthful worse.
- `rho=0.97`: **0.8396 vs 0.6433** — truthful worse.

A lower-volatility comparison (`sigma_state≈0.5`) retained a strong truthful benefit (roughly 0.26–0.31 vs ~0.64 lesion), and at `sigma_state≈0.2` truthful error was roughly ~0.16 vs ~0.64.

**NEGATIVE RESULT.** The simple hypothesis “more temporal continuity + truthful re-entry + fixed gain is always better” is false in this synthetic family. High process volatility can make stale recurrent state harmful even when `rho` is high.

**Refinement.** Re-entry gain/continuation should be tested as a function of innovation, process-vs-observation noise, residual pressure and marginal utility, not recurrence count or autocorrelation alone. This directly strengthens the need for adaptive typed loop control while preserving H0-A/H0-D alternatives.

---

## Cross-experiment synthesis

The experiments jointly favor four implementation tests, not four canonical claims:

1. **Authority:** enforce narrowing structurally at every child boundary.
2. **Representation:** preserve n-ary roles explicitly, while keeping reified pairwise encoding as a live simpler alternative.
3. **Performance:** use dependency-local incremental recomputation only where measured topology supports locality; allow selective rebuild.
4. **Recurrence:** adaptive, volatility-sensitive re-entry/loop control is a better hypothesis than fixed recurrence gain.

No experiment in this file closes `CLAYCODE_RELEASE_GATE`, demonstrates live Frank causal emergence, or promotes phenomenal-consciousness claims.
