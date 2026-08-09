# Historical Correction — Frank Needle Contrastive/Retrieval Rationale

Run: `harness-20260809T1854p0700-chatgpt-secondary-needle-fusion`
Date: 2026-08-09
Status: `CORRECTION_WITH_EXACT_AUG4_CODE / NO_ARCHITECTURE_PROMOTION`

## Historical claim being corrected

The 2026-08-04 handover (`UEBERGABE-P3-2026-08-04`) argued against a top-k prefilter partly because Needle was described as contrastively learning roughly `600 queries × 51 tools = 30,600` query/tool relations, implying that each training query directly contrasts against the full 51-tool inventory.

The same handover documents `mini_alle.jsonl` as 720 examples: 120 each for five tools plus one no-tool class.

## Exact Aug-4 code inspection

The Drive snapshot dated 2026-08-04 was inspected directly:

- `needle/dataset/dataset.py`
- `needle/training/train.py`
- `needle/training/finetune.py`

### What dataset.py actually does

`_build_contrastive_arrays()` tokenizes every individual tool definition and marks whether each tool is a positive for an example.

But `get_contrastive_batches()` then:

1. builds `pos_map` only from tools whose `tool_is_pos` is true;
2. drops queries that have no positive tool;
3. for each selected query, randomly selects **one positive tool**;
4. forms CLIP-style batches where negatives are the other paired tools in the batch.

Therefore the loss does **not** directly contrast every query against all 51 tools. Preparing/tokenizing all tools is not equivalent to using all 51 as per-query negative supervision.

### No-tool consequence

No-tool examples have no positive tool and therefore never enter `valid_queries` for the contrastive batch generator. The upstream retrieval benchmark also skips examples without a positive tool.

Conclusion: the contrastive head is a tool ranker/retriever for tool-positive cases, not a trained no-tool classifier.

### What train.py actually does

The Aug-4 training loop sets:

`do_contrastive = ... global_step > 0 and global_step % 1000 == 0`

So the contrastive loss is activated only once per 1000 global text-training steps under this snapshot.

### What finetune.py defaults imply for the documented mini_alle run

`finetune.py` defaults:

- epochs = 1
- batch size = 64
- 120 examples/class -> 100 train + 10 validation + 10 test for a full class.

For the documented 720-example, six-class `mini_alle.jsonl`, that implies approximately 600 training examples and:

`floor(600 / 64) × 1 = 9 training steps`

if the defaults were used.

Nine steps never reach step 1000, so such a default run would perform **zero contrastive updates**.

## Epistemic limit

The exact historical Frank finetune command/log has not been recovered in the connected Drive snapshot. Epoch/batch overrides could change the exact historical step count. Therefore:

- the old `51 tools per query` rationale is corrected by exact code;
- the no-tool exclusion is code-confirmed;
- the `zero contrastive updates in the Frank mini-finetune` statement remains a strongly supported conditional on documented/default settings until the exact command/log is recovered.

## Research consequence

Inference-time retrieval/top-k is reopened as an experiment. It is **not** promoted as architecture.

Required discriminating test:

1. official unchanged Needle checkpoint;
2. audited German tool-positive cases;
3. full-51 generation vs Needle contrastive retrieval at k={4,8,12,16,24} followed by generation;
4. report relevant-tool recall@k, MRR, downstream route/argument accuracy, latency and encoder-token cost;
5. preserve a separate no-tool/fallback path;
6. reject retrieval architecture if candidate recall loss dominates downstream benefits.
