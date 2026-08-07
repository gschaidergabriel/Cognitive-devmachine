# KMP-G7 — Resolution- and Recurrence-Aware Memory

- **packet_id:** KMP-G7-RESOLUTION-RECURRENCE-MEMORY
- **status:** OPEN / synthetic-supported + external-implementation-supported
- **domains:** model-runtime, active-memory, synthetic-clay
- **claim:** Memory should support exact detail, coarse summaries and on-demand zoom; retention should include recurrence/future-utility signals, not only instantaneous salience.
- **evidence:** EXP-G7-RESOLUTION-MEMORY-004: equal 20-unit summary+zoom accuracy `.97765`, latency `2.2914` vs flat `.8476`, `3.8078`. EXP-G7-RECURRENCE-MEMORY-005: future-hit `.7638` recurrence model vs `.3852` current salience, oracle `.7960`. External SeKV/LazyEviction/HiKV/ForesightKV/K-VEC provide adjacent implementation/literature evidence.
- **boundary:** synthetic relevance/recurrence generators; no claim that all real KV/state has periodic importance.
- **next falsifier:** pinned model/FRANK context benchmark at equal bytes against recency, heavy-hitter, coverage, recurrence, future-contribution and receipt-causal-spine policies.
- **origin:** chatgpt-secondary / OpenAI / GPT-5.6 Sol / clay-20260808T0542p0700-chatgpt-secondary
