# Trigger 2 — Qwen3.5-0.8B Training Web Research Ledger v2

Status: **CURRENT LIVING RESEARCH LEDGER / OWNER-TARGET SYNC**  
Date: 2026-08-25  
Trigger: exact `2` / `triggerwort 2`  
Target lock: **Qwen3.5-0.8B only**  
Branch: `research/trigger2-qwen35-08b-hcu-fullft-20260825`

This v2 ledger supersedes v1 for current Trigger-2 decision-making while preserving v1 as provenance. It inherits all non-conflicting v1 findings and records the new owner-architecture synchronization, current Qwen source evidence, current provider-documentation evidence, and resulting recipe/evaluation changes.

## 0. Authority refresh

Observed canonical `main` at this run:

`60a81a1eafed6d878b7b27bc074ebf01924528ae`

Newest owner target read from `main`:

`research_entity/global/XENO_HCU_GO_TARGET_ARCHITECTURE_OWNER_DIRECTIVE_2026-08-25.md`

Trigger-2 branch owner binding:

`research_entity/claycode/TRIGGER2_BINDING_TO_GO_TARGET_ARCHITECTURE_2026-08-25.md`

Current supervisor surface observed in the authority stack is newer than the bootstrap cache and remains `FREE_ONLY`; paid/provider credential execution is not authorized by this Trigger-2 research run.

## 1. Owner-target training delta

The previous function-to-data matrix underrepresented the now-binding physical GRID10 target. Current training/evaluation must explicitly cover:

1. role-free autonomous boot/join from shared state;
2. exact S1 epoch/digest reconstruction;
3. useful/unclaimed-work selection;
4. ordinary-node S1 read-only behavior;
5. ephemeral typed `NODE_RESULT/v1` result return;
6. stale/duplicate/out-of-scope result rejection;
7. ordinary-node -> valid leased coordinator -> ordinary-node role transition;
8. coordinator fan-in and evidence arbitration;
9. Hyperposition-preserving coordinator integration;
10. compact minimum-sufficient S1 delta generation;
11. coordinator-only S1 writes under scoped non-stale lease;
12. multiple scoped coordinators with CAS/rebase rather than last-writer-wins;
13. recursive temporary coordinator hierarchy for scale;
14. coordinator failure/successor/rejoin continuation;
15. correlated-consensus traps where independent evidence beats node count;
16. GWT broadcast/uptake/re-entry through coordinator-written S1;
17. physical GRID10 acceptance against matched-budget challengers.

The current compiled matrix for these families is:

`TRIGGER2_XENO_FUNCTIONALITY_TO_DATA_MATRIX_V2.md`

These owner-specific families remain evidence/data-status bounded. Architecture text alone does not make them validated training data.

## 2. Qwen3.5-0.8B current primary-source refresh

Primary sources refreshed on 2026-08-25:

- `https://huggingface.co/Qwen/Qwen3.5-0.8B-Base`
- `https://huggingface.co/Qwen/Qwen3.5-0.8B-Base/blob/main/config.json`
- `https://huggingface.co/Qwen/Qwen3.5-0.8B`
- official QwenLM GitHub release material for the Qwen3.5 series.

Observed source facts relevant to Trigger-2:

- Qwen officially released Qwen3.5-0.8B on 2026-03-02.
- Current Qwen3.5-0.8B model material identifies a 0.8B causal language model with vision encoder.
- Current `config.json` exposes `hidden_size=1024`, 24 language-model layers and `full_attention_interval=4`.
- The current architecture alternates three linear-attention/Gated-DeltaNet-class layers followed by one full-attention layer, producing 18 linear-attention layers and 6 full-attention layers over 24 layers.
- Native context is 262,144 tokens, far above expected normal Xeno/HCU control episodes; max training sequence length must therefore be selected from measured episode statistics rather than copied from native context.

### Important source-drift observation

Searchable older/pull-request model-card material can disagree with the current main model card/config on the displayed hidden-layout grouping count. Therefore prose-level model-card descriptions are not sufficient identity for J-Space site labels or training sidecars.

**Recipe/eval consequence:** every model-internal site row/receipt must bind exact checkpoint revision, tokenizer revision, config bytes or digest, runtime/build identity, layer index and layer class. No generic `Qwen3.5-0.8B layer N` positive label is admitted without that binding.

Current source-identity progress is recorded separately in:

`TRIGGER2_QWEN35_08B_CANDIDATE_SOURCE_IDENTITY_V1.json`

That file already pins official candidate artifact revisions plus weight/tokenizer SHA-256 values. Exact config byte digests, deterministic checkpoint-manifest digests, runtime consumed-byte attestation and baseline measurement remain open.

## 3. Together current documentation refresh — documentation only, no provider execution

Primary/current sources refreshed:

- `https://www.together.ai/pricing`
- `https://www.together.ai/fine-tuning`
- Together fine-tuning support/pricing documentation and 2026 fine-tuning update.

Current documentation supports these limited claims:

- Together offers both LoRA and full fine-tuning; full fine-tuning updates all model weights.
- Current published standard supervised full-FT price for models up to 16B is **$0.54 per 1M processed tokens**.
- Current pricing states a **$4 minimum job charge**.
- Processed-token pricing includes training tokens multiplied by epochs plus validation tokens multiplied by evaluation count.
- Together marketing currently states broad Hugging Face/open-source model compatibility.
- Together's 2026 Qwen3.5 fine-tuning announcement explicitly names larger Qwen3.5 variants, but the material observed in this run does **not explicitly establish Qwen3.5-0.8B as a supported full-FT model**.

Therefore current status is:

`QWEN35_08B_TOGETHER_FULL_FT_COMPATIBILITY = UNVERIFIED`

Broad compatibility marketing is not exact-model execution evidence.

### FREE_ONLY correction

The v1 backlog item requesting an exact live Together compatibility/preflight must be interpreted under current supervisor authority. Under `FREE_ONLY`, this run does **not** consume credentials, submit tokenization, request a provider-side estimate, create a job, or perform any paid/preflight operation.

Allowed now:

- read public provider documentation;
- keep exact compatibility as an unresolved future gate;
- prepare dataset/recipe/evaluation artifacts offline;
- calculate hypothetical cost only from public pricing and frozen token counts, clearly marked non-executed.

A future provider-side compatibility/preflight requires authority that explicitly permits that provider action.

## 4. J-Space consequence for Qwen3.5 hybrid architecture

Current Trigger-2 J-Space source map remains method-level/source-level until model-specific runtime evidence exists.

The hybrid architecture creates at least three distinct claim surfaces that must not be collapsed:

1. DeltaNet/linear-attention-layer residual measurement/intervention;
2. DeltaNet recurrent state or runtime-exposed equivalent state, if actually exposed;
3. periodic full-attention-layer residual measurement/intervention.

Hard negatives required in training/evaluation:

- same depth does not imply same layer-class mechanism;
- residual steering does not prove recurrent-state control;
- final/readout steering does not prove intermediate semantic J-Space;
- Qwen3-0.6B coordinates do not transfer as Qwen3.5-0.8B positive geometry;
- broadcast-wide effect does not prove token-local/state-local equivalence.

No same-model Qwen3.5 semantic J-Space positive is minted by this web/source run.

## 5. Corpus/recipe change from this exact `2`

This run changes current Trigger-2 preparation in four concrete ways:

1. **Function coverage:** owner-specific autonomous boot, read-only ordinary-node, result-return, dynamic coordinator, recursive coordination and failure/rejoin families are mandatory current dataset families.
2. **Negative density:** ordinary S1 write, invalid lease write, scope overflow, stale result acceptance, correlated-majority collapse, last-writer-wins and S0 authority bypass become first-class hard-negative families rather than incidental examples.
3. **Identity sidecars:** all Qwen3.5 internal-site examples require exact revision/config/runtime/site identity; prose model name is insufficient.
4. **Provider gate:** Together Qwen3.5-0.8B full-FT compatibility remains `UNVERIFIED`; no provider-side action is permitted by this Trigger-2 run under FREE_ONLY.

No token-mixture percentage is raised solely because the new owner-specific families are numerous. First create independent family IDs and reviewed candidate rows, then measure coverage and duplicate-family saturation.

## 6. Evaluation delta

Add/retain separate frozen evaluation families for:

- `XENO_BOOT`
- `S1_READ`
- `WORK_SELECTION`
- `ORDINARY_READ_ONLY`
- `NODE_RESULT`
- `RESULT_ADMISSION`
- `COORDINATOR_ROLE`
- `COORDINATOR_LEASE`
- `COORDINATOR_FANIN`
- `COORDINATOR_HYPERPOSITION`
- `COORDINATOR_COMPRESSION`
- `S1_WRITE_AUTHORITY`
- `MULTI_COORDINATOR`
- `RECURSIVE_COORDINATION`
- `COORDINATOR_RECOVERY`
- `GRID_ACTIVATION`
- `PHYSICAL_GRID10`
- `GRID_CRITICAL_MASS`
- `QWEN35_HYBRID_SITE`

Promotion must use worst-family hard floors. Aggregate score cannot rescue an authority failure such as ordinary-node S1 mutation or invalid coordinator write.

## 7. Current evidence/credit boundary

This run adds **source/research/data-specification progress only**.

Not granted:

- Qwen3.5-0.8B model runtime credit;
- Qwen3.5 J-Space causal credit;
- physical GRID10 runtime credit;
- checkpoint-selection credit;
- dataset validation credit merely from source docs;
- training credit;
- provider execution credit;
- whole EntityOS/HCU acceptance.

The queued Qwen3-0.6B structural-native workflow remains a separate model-bound research lane and cannot supply Qwen3.5 positive geometry by inheritance.

## 8. Next highest-information Trigger-2 gate

Do not duplicate the already-created owner-aligned matrix or candidate-source identity work.

Next nonduplicate preparation gate:

1. complete exact config-byte SHA-256 and deterministic checkpoint-manifest identity for both pinned Qwen3.5-0.8B candidates;
2. specify a deterministic JSONL + ancestry-sidecar compiler for the owner-target trajectory families;
3. instantiate a small reviewed candidate corpus with explicit family IDs and hard-negative transforms;
4. run leak/dedup/family-split validation offline;
5. only then revisit mixture ratios and Base-vs-post-trained zero-cost baseline execution on an admitted free surface.

Provider compatibility stays unresolved until a future authority permits an exact provider-side check or Together publishes explicit public Qwen3.5-0.8B full-FT support.
