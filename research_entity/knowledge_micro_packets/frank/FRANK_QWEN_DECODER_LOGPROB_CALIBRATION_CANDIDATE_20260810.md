<!-- RAE_META
{"packet_id":"FRANK_QWEN_DECODER_LOGPROB_CALIBRATION_CANDIDATE_20260810","title":"Decoder log-probability candidate after raw-confidence V2 refutation","domains":["frank","model_runtime","harness","gwt"],"topics":["Qwen4B","llama.cpp","logprobs","calibration","uncertainty","selective prediction"],"epistemic_class":"PRIMARY_SOURCE_CAPABILITY_PLUS_RESEARCH_CANDIDATE","claim_status_hint":"CANDIDATE_NOT_VALIDATED","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T01:27:00+07:00","source_refs":["https://github.com/ggml-org/llama.cpp/blob/08659901c43b51de735740f1cf61bb82fbe0c4e4/tools/server/server-task.cpp","https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md","https://arxiv.org/abs/2607.17447","https://arxiv.org/abs/2404.03163","gschaidergabriel/Dr.-Unterweger@0c6d9de4ffc314765bcc03b1d7e487cb9bbaec21"],"confidence":"HIGH_FOR_RUNTIME_CAPABILITY_LOW_FOR_CALIBRATION_UTILITY","verification_required":true,"falsifier_or_next_test":"After the already-preregistered fresh-context experiment closes, collect visible-answer token logprobs from the exact pinned runtime on matched tasks and test calibration/rank/selective-risk against correctness without granting online halt authority."}
RAE_META -->

## Why this candidate exists

The admitted post-guard real-Qwen V2 falsified raw verbalized confidence as a usable W4 stopping signal: `CONFIDENCE=100` was observed on a stable wrong answer, the post-hoc audit measured 75% accuracy at 100% mean stated confidence, and the corrected V2 therefore set residual uncertainty to 1.0 and admitted zero early halts.

The next calibration question is therefore not how to rescale the printed `CONFIDENCE=` field, but whether a different *observable* signal carries useful rank/selective information while remaining non-authoritative.

## Exact runtime capability

The exact pinned llama.cpp source used by the prebuilt Qwen lane (`b10333`, source commit `08659901c43b51de735740f1cf61bb82fbe0c4e4`) already supports OpenAI-compatible completion/chat `logprobs`: when probability output is requested, the non-streaming chat response attaches token-level probability records under `choice["logprobs"]["content"]`. This is therefore reproducible on the current runtime family; no runtime upgrade is required merely to expose the signal.

## Hypothesis and strongest counterhypothesis

**H-LOGPROB-RANK:** Decoder-derived probabilities over the visible final answer may rank some wrong answers as less reliable than correct answers better than raw self-reported confidence, and could eventually support a calibrated abstention/verification trigger after held-out validation.

**Counterhypothesis:** Decoder logprobs may be just as overconfident, wording/tokenization-sensitive, or domain-specific as verbalized confidence. High probability of a generated token sequence is not probability that the underlying answer is true. A model can confidently assign high token probability to a stable wrong attractor.

Recent primary research reinforces the counterhypothesis: semantic uncertainty work distinguishes application-relevant state uncertainty from wording-dependent language probabilities and requires held-out calibration; rank-calibration work evaluates whether uncertainty scores actually order lower-quality generations rather than assuming their numeric scale is meaningful.

## Required test before any architecture use

Do **not** change production W4 or the local-model public contract from this packet alone. After the already-gated fresh-context experiment finishes:

1. use the exact pinned model/runtime and matched tasks;
2. request logprobs only for visible answer output, with hidden reasoning still disabled/nonpersisted;
3. preserve token-level raw measurements in bounded experimental evidence or reduce them to explicitly defined visible-answer statistics;
4. compare raw verbalized confidence, answer-token logprob statistics, stability, and fresh-context disagreement;
5. evaluate correctness ranking, Brier/ECE only after an explicit probability mapping, selective risk/coverage, confidently-wrong tails and task partitions;
6. separate anchor replications from genuinely new held-out data;
7. calibrate on one set and evaluate on a disjoint held-out set before assigning any W4 residual uncertainty below 1.0;
8. keep all signals offline/proposal-only until calibration, reliability, OOD and authority gates pass.

## Architecture status

`CANDIDATE_NOT_VALIDATED`.

- Raw verbalized confidence remains diagnostic-only and uncalibrated.
- W4 real-Qwen uncertainty remains 1.0.
- Decoder logprobs are an available measurement channel, **not** a correctness probability, truth signal, halt authority or effect authority.
- No training is authorized.
- No release, reliability, emergence or consciousness claim.
