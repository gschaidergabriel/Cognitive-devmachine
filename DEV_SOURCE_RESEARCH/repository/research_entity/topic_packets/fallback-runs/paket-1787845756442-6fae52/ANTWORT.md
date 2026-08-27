# GRID10 Latency Reduction Concept (CPU‑only, 4 vCPUs)

## Measured baseline
- Decode of 4‑64 new tokens: 2‑6 s CPU time per task  
- Full tick (5 parallel tasks + 1 broadcast): ~4 s  
- Fabric transaction rate (10 processes): ~5 /s  
- Each process currently calls `torch.set_num_threads(1)` (single‑threaded inference).

## (a) Thread‑count trade‑off
- **Current setting (1 thread × 10 processes)** → oversubscription of the 4 cores, leading to frequent context switches and cache thrashing.  
- **Alternative (2 threads × 5 concurrent processes)** → each process can use both cores, reducing context‑switch overhead while keeping total thread count (10) ≤ 2 × cores.  
- **Expected impact:** ~15‑25 % reduction in per‑task decode time (≈0.3‑0.8 s saved) because each inference can utilize modest intra‑op parallelism (e.g., matrix‑multiply kernels) without exceeding core capacity.  
- **Implementation:** Dynamically adjust the number of active processes based on workload (e.g., a lightweight semaphore) or fix `torch.set_num_threads(2)` and limit concurrent processes to 5 via the fabric scheduler.

## (b) Quantized / smaller model for routine ticks
- **Int8 quantization (via `bitsandbytes` or `gguf`)** typically yields 2‑3× speed‑up on CPU with <1 % accuracy loss for classification‑style tasks (YES/NO, single‑word).  
- **Int4 quantization** can push 4‑5× speed‑up but may incur 2‑5 % accuracy drop; acceptable only for very high‑tolerance routing decisions.  
- **Fallback strategy:** Keep the full Qwen3.5‑0.8B model in memory; route simple prompts (detected by length < 16 tokens or keyword list) to the quantized model, complex prompts to the full model.  
- **Expected impact:** Routine ticks (≈70 % of traffic) drop from 2‑6 s to 0.7‑2 s, cutting average tick latency by ~30‑40 %. Implementation effort: replace `AutoModelForCausalLM` call with a wrapper that loads the quantized checkpoint via `bitsandbytes.load_qmodel` or `llama.cpp` bindings.

## (c) Speculative Decoding
- Overhead: running a draft model (e.g., 0.1 B) plus verification pass of the target model.  
- For 4‑64 new tokens, the draft model generates tokens quickly but the verification step still requires a full forward pass of the target model for each token, essentially doubling work.  
- **Verdict:** Not beneficial for such short sequences; the overhead outweighs any gains. Skip speculative decoding for now.

## (d) Batching multiple node requests
- Batching would require a shared model instance across processes, breaking the current fork‑COW isolation (each process has its own private copy of the model pages).  
- To batch, you would need to abandon the per‑process fork design and move to a threaded or multiprocess‑shared‑memory server (e.g., TorchServe, vLLM CPU backend).  
- **Complexity:** High – would require redesigning the fabric and loss of COW memory savings.  
- **Recommendation:** Defer batching until a larger refactor; focus on per‑process optimizations first.

## (e) Prefix / KV‑cache reuse
- Prompts are short and mostly dissimilar; exact prefix matches are rare.  
- Even with similarity, the KV cache for a 0.8B model is modest (~few MB), so storing and looking up caches adds overhead with little hit‑rate.  
- **Verdict:** Low benefit for the current workload; not worth engineering effort.

## Prioritized 2‑3 approaches for immediate implementation
1. **Adjust thread concurrency** – set `torch.set_num_threads(2)` and limit active processes to ≤5 (via a simple semaphore in the fabric). Expected latency reduction: ~20 % with virtually no code change.  
2. **Introduce an int8‑quantized model for routine ticks** – wrapper that selects quantized vs full model based on prompt heuristics. Expected latency reduction for ~70 % of traffic: 60‑80 % speed‑up, cutting average tick time by ~30‑40 %.  
3. (Optional) **Monitor prefix‑cache hit‑rate** – lightweight logging to verify if any reuse emerges; if hit‑rate > 15 % reconsider KV‑cache sharing.

These two changes can be applied today, require only minor code modifications, and stay within the existing CPU‑only, fork‑COW architecture. No GPU, no major architectural overhaul, and functional fidelity is preserved. 

--- 
*End of concept.* 
