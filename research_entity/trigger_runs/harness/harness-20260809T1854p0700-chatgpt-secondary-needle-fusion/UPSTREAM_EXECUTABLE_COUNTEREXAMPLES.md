# Upstream Needle Executable Counterexamples

Run: `harness-20260809T1854p0700-chatgpt-secondary-needle-fusion`
Evidence class: `REMOTE_SANDBOX_SOURCE_EXECUTION + CURRENT_UPSTREAM_SOURCE_IDENTITY`
Promotion limit: exact findings apply to the inspected Python/JAX implementation; they do not by themselves prove the Cactus production runtime behaves identically.

## Source identity result

The connected Drive source files were hashed as Git blobs and compared with current `cactus-compute/needle` `main`.

Byte-identical/current-upstream blob identity was confirmed for:

- `needle/model/constrained.py` — `b6afbd7a06378d0d146caba881dac92be5d00cd9`
- `needle/model/run.py` — `954022e5b96dcf3aee30a3537c3a2cd2ac1c0e67`
- `needle/dataset/dataset.py` — `3d4a1ea4150d455ee598f2e66c656bbda5f82ea7`
- `needle/dataset/tokenizer.py` — `efa2cc8bc3d83fbf9ef1e22ca8700c0a5bb13d23`
- `needle/training/train.py` — `657559ffbc13a2ce81d7e306b7c270b32d997ad2`
- `needle/training/finetune.py` — `3f0264534bfb10e665654e8fb65c8d3cd081b567`
- `needle/training/eval.py` — `1b0d1dcd229d3ae81838ccf16037c47306cbc8a1`

Therefore the following findings are not attributable merely to a stale Aug-4 copy.

## CE-NDL-01 — JSON-Schema docstring/code mismatch

`ToolConstraints` states that it extracts `parameters.properties`, but the executable loop iterates the direct `parameters` dictionary.

Observed:

- Needle-flat `parameters: {location: {...}}` -> constrained key `location`.
- OpenAI/JSON-Schema `parameters: {type: object, properties: {location: {...}}, required: [...]}` -> constrained key `properties` rather than `location`.

Consequence: Frank must normalize to Needle-flat schemas before this decoder path.

## CE-NDL-02 — Legal JSON whitespace bypasses constraint activation

`JsonStateMachine` activates by exact compact suffixes such as:

- `"name":"`
- `"arguments":{`
- argument-key starts `{"` and `,"`

Systematic whitespace sweep:

- name marker: 16 legal combinations of {none, space, tab, newline} before/after `:`; only 1/16 entered `IN_NAME`, 15/16 stayed FREE.
- first argument-key marker: 64 legal combinations around `:` and after `{`; only 1/64 entered `IN_ARG_KEY`, 63/64 stayed FREE.

This does not mean the trained model usually emits whitespace; Needle training uses compact JSON. It does mean the state machine is not a general JSON grammar and cannot serve as a security boundary.

## CE-NDL-03 — Multiple fail-open paths

Observed/source-confirmed:

- malformed tool JSON -> empty constraints;
- no valid mask tokens -> original logits returned;
- off-trie constrained prefix -> original logits returned;
- missing param trie -> original logits returned.

This is reasonable as a model-generation recovery choice, but incompatible with treating constrained decoding as execution authorization.

## CE-NDL-04 — Blind encoder truncation

`_build_encoder_input()` truncates query first and then slices the serialized tool-token stream to remaining tokens. It has no requirement that the tool JSON remain complete or end at a tool boundary.

H1 requirement: exact token-budget preflight must reject/escalate before Needle when the complete selected catalogue cannot fit; do not rely on this truncation for semantic safety.

## CE-NDL-05 — Snake-case normalization collision

Current upstream `normalize_tools()` stores `name_map[snake] = orig` without collision detection.

Executable example:

- `FooBar` -> `foo_bar`
- `foo_bar` -> `foo_bar`

Both normalized tool definitions receive the same name and the reverse map retains only the last source name.

H1 wrapper now rejects many-to-one alias/normalization collisions.

## CE-NDL-06 — Invalid-JSON restore fallback can mutate argument values

If `restore_tool_names()` cannot parse generated JSON, it performs global string replacement over the entire output.

Executable example with alias `list_capabilities -> moeglichkeiten`:

input malformed output contains argument value:

`"text":"list_capabilities"`

after fallback:

`"text":"moeglichkeiten"`

H1 policy: never use string-level reverse mapping for a decision receipt. Strict parse/validate first, then modify only structured tool/parameter identity fields.

## CE-NDL-07 — Contrastive retriever excludes no-tool cases

`get_contrastive_batches()` constructs `valid_queries` only for examples with at least one positive tool. No-tool examples have no positive and are omitted.

The current official retrieval benchmark likewise skips examples with no positive tool.

Consequence: the contrastive head is not evidence of a no-tool classifier. It may be tested as a candidate ranker on tool-positive cases only; no-tool/fallback requires a separate decision path.

## CE-NDL-08 — Contrastive loss cadence vs Frank mini-finetune

Current/Aug-4 `train.py` activates contrastive loss only when:

`global_step > 0 and global_step % 1000 == 0`

Current/Aug-4 `finetune.py` defaults:

- 1 epoch;
- batch size 64;
- per-tool split 100 train / 10 val / 10 test when 120 examples exist.

The documented Frank `mini_alle` had 720 examples: five tools + no-tool, 120 each. Under defaults this yields about 600 training examples and 9 full batches/steps, hence no step 1000 and zero contrastive updates.

Exact historical CLI overrides have not been recovered, so the zero-update claim is conditional on documented/default settings; the cadence and default arithmetic are code-confirmed.

## CE-NDL-09 — No-tool blind spot in finetune evaluation/model selection

`finetune.py::_quick_tool_eval()` explicitly filters out examples whose answers are empty/`[]`.

The `train.py` checkpoint-selection metric pools also skip samples classified as `empty` and select the best checkpoint by `single.call_f1`.

Therefore a Frank hard gate such as no-tool precision >=90% is not protected by the stock finetune quick report or best-checkpoint selection. No-tool examples may participate in text training, but performance can drift without blocking checkpoint promotion.

## CE-NDL-10 — Current Python path unpickles checkpoint

`load_checkpoint()` calls `pickle.load()` directly. Python's own documentation warns that pickle is unsafe for untrusted/tampered input.

H1 requirement: bind allowed checkpoint hash/source before loading. A safetensors artifact exists upstream, but current JAX `load_checkpoint()` is not automatically a safetensors drop-in; parity/mapping must be verified before replacing the exact JAX baseline.

## Static architecture consistency check

For current no-FFN configuration:

- vocab=8192, d_model=512;
- 12 encoder layers;
- 8 decoder layers;
- 8 query heads / 4 KV heads;
- contrastive projection 512 -> 128 -> 128;
- shared/tied embedding/output matrix.

Static source-derived trainable parameter count: `26,315,421`.

At 2 bytes/parameter (BF16), pure parameter bytes = `52,630,842`.
Official `needle.pkl` remote size = `52,633,098` bytes, only 2,256 bytes larger, consistent with the reported ~26M architecture plus container/config overhead.

## Hardened H1 response

The Research Entity implemented `research_entity/harness/reference/needle_runtime_contract.py` with:

- strict JSON parser;
- duplicate-key rejection;
- NaN/Infinity/non-finite rejection;
- standard-schema -> Needle-flat conversion;
- collision-checked bidirectional aliases;
- offered-tool enforcement;
- unknown/missing/type-invalid argument rejection;
- complete encoder-budget preflight contract;
- toolset/output hashes;
- proposal-only `authority=NONE`, `effect_eligible=false`, external effect-gate requirement.

Latest local mirror regression: 31/31 tests PASS after strict-JSON hardening.
Latest additional deterministic mutation campaign: 30,000 cases, 0 false accepts and 0 false rejects in the generated test domain.
Earlier independent mutation campaign: 15,000 cases, likewise 0 false accepts/false rejects in its generated domain.

These tests establish component behavior, not German semantic routing accuracy.
