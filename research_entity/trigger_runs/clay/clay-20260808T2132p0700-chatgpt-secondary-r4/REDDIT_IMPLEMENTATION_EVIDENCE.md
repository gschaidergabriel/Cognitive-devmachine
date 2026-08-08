# Clay G12 Reddit / practitioner evidence

This file is community implementation evidence only. It is lower-trust than primary documentation and controlled benchmarks.

## On-device Qwen3 / llama.cpp reports

- r/LocalLLaMA, 2026-02-10: practitioner reports shipping iOS/Android local inference with llama.cpp and Qwen3 1.7B/3B/4B Q4_K_M; notes Android debug builds without native optimization can become unusably slow. Source: https://www.reddit.com/r/LocalLLaMA/comments/1r0q7j2/shipping_llama_32_and_qwen3_ondevice_in_a_mobile/
- r/LocalLLM, 2026-03-22: LocalRAG practitioner reports Qwen3 4B Q4_K_M at roughly 3 GB download, 4k-8k context focus and highly device-dependent response latency. Source: https://www.reddit.com/r/LocalLLM/comments/1s0ewky/iosandroid_rag_app_with_a_localllm_qwen3_4b/
- r/LocalLLaMA, 2026-04-29: discussion reports Termux/llama.cpp as usable but calls out battery drain and slow decode on phones. Source: https://www.reddit.com/r/LocalLLaMA/comments/1szamcy/whats_up_with_mobile_llms/

## Research transfer

These reports strengthen only the engineering priority of sustained Android measurements and native build/runtime optimization. They do not establish FRANK performance, Qwen3-4B quality, thermal stability, or a preferred backend.

G12 therefore keeps mobile evaluation multidimensional: model + quantization + context/KV + prefill + decode + runtime/backend + build flags + battery/thermal steady state + reader rail.
