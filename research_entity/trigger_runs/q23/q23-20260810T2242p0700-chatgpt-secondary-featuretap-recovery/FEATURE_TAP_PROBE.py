#!/usr/bin/env python3
"""Diagnostic-only Q23 probe: one Qwen3.5 visual encode, two feature taps.

This does not mutate Frank state. It is intended for the accepted Ubuntu/VPS lane.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("image")
    p.add_argument("--model", default="Qwen/Qwen3.5-4B")
    p.add_argument("--device", default="auto")
    args = p.parse_args()

    import torch
    import transformers
    from PIL import Image
    from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration

    image_path = Path(args.image)
    raw = image_path.read_bytes()
    image = Image.open(image_path).convert("RGB")
    processor = AutoProcessor.from_pretrained(args.model)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        args.model,
        torch_dtype="auto",
        device_map=args.device,
    ).eval()

    inputs = processor(images=image, text="<|vision_start|><|image_pad|><|vision_end|>", return_tensors="pt")
    device = next(model.parameters()).device
    pixel_values = inputs["pixel_values"].to(device)
    image_grid_thw = inputs["image_grid_thw"].to(device)

    torch.cuda.synchronize() if device.type == "cuda" else None
    t0 = time.perf_counter_ns()
    with torch.inference_mode():
        out = model.model.get_image_features(
            pixel_values=pixel_values,
            image_grid_thw=image_grid_thw,
            return_dict=True,
        )
    torch.cuda.synchronize() if device.type == "cuda" else None
    t1 = time.perf_counter_ns()

    pre = out.last_hidden_state.detach().float().cpu()
    post_parts = out.pooler_output
    post = torch.cat(tuple(x.detach().float().cpu() for x in post_parts), dim=0)

    pre_desc = torch.nn.functional.normalize(pre.mean(dim=0), dim=0)
    post_desc = torch.nn.functional.normalize(post.mean(dim=0), dim=0)

    cfg = model.config.to_json_string().encode("utf-8")
    result = {
        "probe": "Q23_FEATURE_TAP_PRE_POST_MERGER_V1",
        "model": args.model,
        "image_sha256": sha256_bytes(raw),
        "config_sha256": sha256_bytes(cfg),
        "transformers_version": transformers.__version__,
        "torch_version": torch.__version__,
        "device": str(device),
        "dtype": str(pixel_values.dtype),
        "image_grid_thw": image_grid_thw.cpu().tolist(),
        "one_visual_encode_ns": t1 - t0,
        "pre_merger_shape": list(pre.shape),
        "post_merger_shape": list(post.shape),
        "pre_descriptor_norm": float(pre_desc.norm()),
        "post_descriptor_norm": float(post_desc.norm()),
        "note": "Both taps come from the same get_image_features() visual forward pass.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
