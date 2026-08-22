#!/usr/bin/env bash
set -euo pipefail

: "${TOGETHER_API_KEY:?TOGETHER_API_KEY must be exported in the shell; never commit it}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

python3 generate_sft_v0.py
python3 validate_sft_v0.py train_v0.jsonl
python3 validate_sft_v0.py validation_v0.jsonl

# Do NOT add --confirm here. Current Together CLI prints the estimated price
# before submission and asks for confirmation. The owner-authorized campaign
# cap is EUR 20 equivalent; abort if the displayed estimate would exceed it.
tg fine-tuning create \
  --training-file train_v0.jsonl \
  --validation-file validation_v0.jsonl \
  --model Qwen/Qwen3.5-0.8B \
  --no-lora \
  --n-epochs 3 \
  --n-evals 2 \
  --n-checkpoints 1 \
  --learning-rate 1e-5 \
  --warmup-ratio 0.03 \
  --train-on-inputs auto \
  --random-seed 42 \
  --suffix claycog_v0

# After completion:
#   tg fine-tuning retrieve <FT_ID>
#   tg fine-tuning list-events <FT_ID>
#   tg fine-tuning download <FT_ID> --output-dir ./weights_v0
