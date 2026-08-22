#!/usr/bin/env python3
"""Exact-revision Hugging Face architecture attestation for ClayCog BYOM preflight.

This is a negative/compatibility gate, not provider admission. It proves only that two
exact Hugging Face config.json revisions declare the same model_type and at least one
common architecture. Together must still admit the template/checkpoint tuple itself.
"""
import argparse, hashlib, json, re, urllib.parse, urllib.request
from pathlib import Path

PRIMARY_HF_MODEL="Qwen/Qwen2.5-0.5B"
PRIMARY_HF_REVISION="060db6499f32faf8b98477b0a26969ef7d8b9987"
REV_RE=re.compile(r"[0-9a-fA-F]{40}")


def exact_revision(value):
    value=str(value or "").strip()
    if not REV_RE.fullmatch(value):
        raise SystemExit("HF_ARCH_ATTESTATION_EXACT_REVISION_REQUIRED: expected 40-hex commit")
    return value.lower()


def config_url(model, revision):
    revision=exact_revision(revision)
    quoted_model="/".join(urllib.parse.quote(x,safe="") for x in str(model).split("/"))
    return f"https://huggingface.co/{quoted_model}/resolve/{revision}/config.json"


def attest_config_bytes(model, revision, raw):
    revision=exact_revision(revision)
    try: cfg=json.loads(raw.decode("utf-8"))
    except Exception as exc: raise SystemExit(f"HF_ARCH_ATTESTATION_CONFIG_INVALID: {type(exc).__name__}") from exc
    model_type=cfg.get("model_type")
    architectures=cfg.get("architectures") or []
    if not isinstance(model_type,str) or not model_type:
        raise SystemExit("HF_ARCH_ATTESTATION_MODEL_TYPE_MISSING")
    if not isinstance(architectures,list) or not architectures or not all(isinstance(x,str) and x for x in architectures):
        raise SystemExit("HF_ARCH_ATTESTATION_ARCHITECTURES_MISSING")
    return {
        "schema":"claycog-hf-architecture-attestation/v1",
        "model":str(model),
        "revision":revision,
        "config_sha256":hashlib.sha256(raw).hexdigest(),
        "model_type":model_type,
        "architectures":sorted(set(architectures)),
        "trust_remote_code":bool(cfg.get("auto_map")),
    }


def fetch_attestation(model, revision, timeout=20):
    url=config_url(model,revision)
    req=urllib.request.Request(url,headers={"User-Agent":"claycog-hf-arch-attestation/1"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response: raw=response.read()
    except Exception as exc: raise SystemExit(f"HF_ARCH_ATTESTATION_FETCH_FAILED: {type(exc).__name__}") from exc
    att=attest_config_bytes(model,revision,raw)
    if att["trust_remote_code"]:
        raise SystemExit("HF_ARCH_ATTESTATION_CUSTOM_CODE_REJECTED")
    return att


def compare_attestations(target, template):
    if target.get("schema")!="claycog-hf-architecture-attestation/v1" or template.get("schema")!="claycog-hf-architecture-attestation/v1":
        raise SystemExit("HF_ARCH_ATTESTATION_SCHEMA_MISMATCH")
    if target.get("model")!=PRIMARY_HF_MODEL or target.get("revision")!=PRIMARY_HF_REVISION:
        raise SystemExit("HF_ARCH_TARGET_IDENTITY_MISMATCH")
    if target.get("trust_remote_code") or template.get("trust_remote_code"):
        raise SystemExit("HF_ARCH_ATTESTATION_CUSTOM_CODE_REJECTED")
    target_arch=set(target.get("architectures") or [])
    template_arch=set(template.get("architectures") or [])
    common_arch=sorted(target_arch & template_arch)
    same_type=target.get("model_type")==template.get("model_type")
    if not same_type or not common_arch:
        raise SystemExit(
            "HF_ARCHITECTURE_MISMATCH: "
            f"target={target.get('model_type')}/{sorted(target_arch)} "
            f"template={template.get('model_type')}/{sorted(template_arch)}"
        )
    return {
        "schema":"claycog-byom-architecture-comparison/v1",
        "status":"ARCHITECTURE_MATCH_LOCAL_ONLY",
        "target_model":target["model"],
        "target_revision":target["revision"],
        "template_model":template["model"],
        "template_revision":template["revision"],
        "model_type":target["model_type"],
        "common_architectures":common_arch,
        "provider_admission":"UNPROVEN_UNTIL_TOGETHER_ACCEPTS_EXACT_TUPLE",
    }


def read_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def write_json(path,obj): Path(path).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n",encoding="utf-8")


def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    f=sub.add_parser("fetch"); f.add_argument("--model",required=True); f.add_argument("--revision",required=True); f.add_argument("--output",required=True)
    c=sub.add_parser("compare"); c.add_argument("--target",required=True); c.add_argument("--template",required=True)
    args=ap.parse_args()
    if args.cmd=="fetch":
        att=fetch_attestation(args.model,args.revision); write_json(args.output,att); print(json.dumps(att,sort_keys=True)); return
    result=compare_attestations(read_json(args.target),read_json(args.template)); print(json.dumps(result,sort_keys=True))

if __name__=="__main__": main()
