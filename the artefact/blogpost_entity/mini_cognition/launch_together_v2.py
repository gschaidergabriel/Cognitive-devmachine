#!/usr/bin/env python3
"""Fail-closed Together BYOM preflight/launcher for ClayCog 0.5B.

The 0.5B target stays Qwen/Qwen2.5-0.5B. As of the 2026-08-22 docs snapshot,
Together's fine-tuning catalog no longer exposes a Qwen2.5 training template and the
native smallest Qwen full-FT entry is Qwen3.5-0.8B. BYOM requires a matching architecture.
Therefore no template is guessed by default. An explicit currently-admitted Qwen2.x
fine-tuning template must be supplied after API verification.
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path
from together import Together
HERE=Path(__file__).resolve().parent
TRAIN=HERE/'train_v2.jsonl'; VALID=HERE/'validation_v2.jsonl'
HF_MODEL=os.environ.get('CLAYCOG_HF_MODEL','Qwen/Qwen2.5-0.5B')
EPOCHS=int(os.environ.get('CLAYCOG_EPOCHS','3')); EVALS=int(os.environ.get('CLAYCOG_EVALS','2'))
MAX_USD=float(os.environ.get('CLAYCOG_MAX_JOB_USD','18.00'))

def run_local_checks():
    subprocess.run([sys.executable,str(HERE/'generate_sft_v2.py')],check=True)
    subprocess.run([sys.executable,str(HERE/'validate_sft_v1.py'),str(TRAIN)],check=True)
    subprocess.run([sys.executable,str(HERE/'validate_sft_v1.py'),str(VALID)],check=True)
    subprocess.run([sys.executable,str(HERE/'corpus_diversity_gate_v2.py'),str(TRAIN),str(VALID)],check=True)
    subprocess.run([sys.executable,str(HERE/'generate_eval_ood_v2.py')],check=True)

def wait_file(client,file_id):
    while True:
        meta=client.files.retrieve(file_id); status=str(meta.processing_status)
        if status=='COMPLETED': return meta
        if status in ('INVALID_FORMAT','FAILED'):
            raise RuntimeError(f'Together rejected {file_id}: {status} {getattr(meta,"validation_report",None)}')
        time.sleep(5)

def objdict(x):
    if hasattr(x,'model_dump'): return x.model_dump()
    if hasattr(x,'dict'): return x.dict()
    return str(x)

def validate_template(hf_model, template):
    if not template:
        raise SystemExit('NO_COMPATIBLE_TEMPLATE_CONFIGURED: current docs expose no native Qwen2.5 fine-tuning template. Set --template only after Together exposes/confirms a full-FT Qwen2.x template compatible with Qwen2.5-0.5B.')
    h=hf_model.lower(); t=template.lower()
    if 'qwen2.5' in h and 'qwen3' in t:
        raise SystemExit(f'ARCHITECTURE_FAIL_CLOSED: refusing Qwen2.5 BYOM weights with Qwen3.x template {template}')
    if 'qwen2.5' in h and 'qwen2' not in t:
        raise SystemExit(f'ARCHITECTURE_FAIL_CLOSED: template does not identify Qwen2.x family: {template}')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--create',action='store_true')
    ap.add_argument('--instruct-ablation',action='store_true')
    ap.add_argument('--template',default=os.environ.get('CLAYCOG_TOGETHER_TEMPLATE',''))
    args=ap.parse_args()
    if not os.environ.get('TOGETHER_API_KEY'):
        raise SystemExit('TOGETHER_API_KEY must exist only in the execution environment')
    hf_model='Qwen/Qwen2.5-0.5B-Instruct' if args.instruct_ablation else HF_MODEL
    validate_template(hf_model,args.template)
    run_local_checks()
    client=Together()
    try:
        limits=client.fine_tuning.model_limits(model_name=args.template)
    except Exception as exc:
        raise SystemExit(f'TEMPLATE_MODEL_LIMITS_REJECTED: {args.template}: {exc}') from exc
    if not getattr(limits,'supports_full_training',False):
        raise SystemExit(f'TEMPLATE_NOT_FULL_FT: {args.template}')
    train_file=client.files.upload(file=str(TRAIN),purpose='fine-tune',check=True)
    valid_file=client.files.upload(file=str(VALID),purpose='fine-tune',check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)
    estimate=client.fine_tuning.estimate_price(training_file=train_file.id,validation_file=valid_file.id,model=args.template,
        n_epochs=EPOCHS,n_evals=EVALS,training_method={'method':'sft','train_on_inputs':'auto'},training_type={'type':'Full'})
    price=float(estimate.estimated_total_price)
    report={'mode':'preflight' if not args.create else 'create','from_hf_model':hf_model,'template_model':args.template,
      'epochs':EPOCHS,'evals':EVALS,'estimated_usd':price,'allowed_to_proceed':bool(estimate.allowed_to_proceed),
      'price_detail':objdict(estimate),'compatibility_status':'UNPROVEN_UNTIL_TOGETHER_ACCEPTS_BYOM_CHECKPOINT',
      'corpus':'claycog-sft/v2','ood_cases':240}
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed: raise SystemExit('Together price/admission endpoint does not allow this job')
    if price>MAX_USD: raise SystemExit(f'BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}')
    if not args.create:
        print('PREFLIGHT_ONLY: no billed fine-tuning job created'); return
    job=client.fine_tuning.create(training_file=train_file.id,validation_file=valid_file.id,model=args.template,
        from_hf_model=hf_model,n_epochs=EPOCHS,n_evals=EVALS,n_checkpoints=1,learning_rate=1e-5,warmup_ratio=0.03,
        train_on_inputs='auto',lora=False,suffix='claycog_05b_v2')
    print(json.dumps({'job_id':job.id,'from_hf_model':hf_model,'template_model':args.template,'full_fine_tune':True,
      'estimated_usd':price,'next':'retrieve job; do not retry create blindly'},indent=2))
if __name__=='__main__': main()
