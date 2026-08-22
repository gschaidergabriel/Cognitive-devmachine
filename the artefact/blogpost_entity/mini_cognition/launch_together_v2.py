#!/usr/bin/env python3
"""Leakage-gated ClayCog 0.5B Together preflight/create launcher.

Local-only mode needs no Together package or secret. Remote preflight validates/uploads
v2 train+validation and asks Together for limits/price. BYOM compatibility remains OPEN
until create accepts from_hf_model; the current price-estimate endpoint does not take it.
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRAIN=HERE/'train_v2.jsonl'; VALID=HERE/'validation_v2.jsonl'; OOD=HERE/'eval_ood_v2.jsonl'
HF_MODEL=os.environ.get('CLAYCOG_HF_MODEL','Qwen/Qwen2.5-0.5B')
TEMPLATE=os.environ.get('CLAYCOG_TOGETHER_TEMPLATE','Qwen/Qwen2.5-7B-Instruct-Turbo')
EPOCHS=int(os.environ.get('CLAYCOG_EPOCHS','3')); EVALS=int(os.environ.get('CLAYCOG_EVALS','2'))
MAX_USD=float(os.environ.get('CLAYCOG_MAX_JOB_USD','18.00')); MIN_CHARGE_USD=4.0
STATE=HERE/'together_job_v2.local.json'

def run_local_checks():
    subprocess.run([sys.executable,str(HERE/'generate_sft_v2.py')],check=True)
    subprocess.run([sys.executable,str(HERE/'validate_sft_v2.py'),str(TRAIN),str(VALID)],check=True)
    subprocess.run([sys.executable,str(HERE/'generate_eval_ood_v2.py')],check=True)
    chars=TRAIN.stat().st_size+VALID.stat().st_size
    rough_tokens=chars/4
    rough_processed=rough_tokens*((EPOCHS*TRAIN.stat().st_size + EVALS*VALID.stat().st_size)/chars)
    return {'train_bytes':TRAIN.stat().st_size,'validation_bytes':VALID.stat().st_size,'ood_cases':sum(1 for _ in OOD.open()),'rough_raw_tokens_char4':round(rough_tokens),'rough_processed_tokens_char4':round(rough_processed),'pricing_floor_usd':MIN_CHARGE_USD}

def wait_file(client,file_id):
    while True:
        meta=client.files.retrieve(file_id); status=str(meta.processing_status)
        if status=='COMPLETED': return meta
        if status in ('INVALID_FORMAT','FAILED'): raise RuntimeError(f'Together rejected {file_id}: {status} {getattr(meta,"validation_report",None)}')
        time.sleep(5)

def objdict(x):
    if hasattr(x,'model_dump'): return x.model_dump()
    if hasattr(x,'dict'): return x.dict()
    return str(x)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--local-only',action='store_true')
    ap.add_argument('--create',action='store_true',help='create exactly one billed job after remote preflight')
    ap.add_argument('--instruct-ablation',action='store_true')
    args=ap.parse_args()
    local=run_local_checks()
    if args.local_only:
        print(json.dumps({'mode':'local_only','local':local,'byom_compatibility':'NOT_TESTED','job_created':False},indent=2)); return
    key=os.environ.get('TOGETHER_API_KEY')
    if not key: raise SystemExit('TOGETHER_API_KEY must exist only in the execution environment')
    try: from together import Together
    except ImportError as exc: raise SystemExit('Install current Together SDK: pip install -U together') from exc
    hf_model='Qwen/Qwen2.5-0.5B-Instruct' if args.instruct_ablation else HF_MODEL
    client=Together(api_key=key)
    limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits,'supports_full_training',False): raise SystemExit(f'Template is not full-FT capable: {TEMPLATE}')
    train_file=client.files.upload(file=str(TRAIN),purpose='fine-tune',check=True)
    valid_file=client.files.upload(file=str(VALID),purpose='fine-tune',check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)
    estimate=client.fine_tuning.estimate_price(training_file=train_file.id,validation_file=valid_file.id,model=TEMPLATE,n_epochs=EPOCHS,n_evals=EVALS,training_method={'method':'sft','train_on_inputs':'auto'},training_type={'type':'Full'})
    price=float(estimate.estimated_total_price)
    report={'mode':'remote_preflight' if not args.create else 'create','from_hf_model':hf_model,'template_model':TEMPLATE,'epochs':EPOCHS,'evals':EVALS,'estimated_usd':price,'allowed_to_proceed':bool(estimate.allowed_to_proceed),'local':local,'price_detail':objdict(estimate),'byom_compatibility':'OPEN_UNTIL_CREATE_ACCEPTS_FROM_HF_MODEL','template_distance_warning':'Qwen2.5 0.5B BYOM vs 7B template is a material size mismatch; Together docs say from_hf_model should be as close as possible in architecture and size.'}
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed: raise SystemExit('Together price/admission endpoint does not allow this job')
    if price>MAX_USD: raise SystemExit(f'BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}')
    if not args.create:
        print('PREFLIGHT_ONLY: no billed fine-tuning job created; BYOM compatibility still open'); return
    if STATE.exists():
        prior=json.loads(STATE.read_text()); raise SystemExit(f'DUPLICATE_CREATE_BLOCKED existing local job state: {prior.get("job_id","UNKNOWN")}. Retrieve/cancel that job instead of creating blindly.')
    job=client.fine_tuning.create(training_file=train_file.id,validation_file=valid_file.id,model=TEMPLATE,from_hf_model=hf_model,n_epochs=EPOCHS,n_evals=EVALS,n_checkpoints=1,learning_rate=1e-5,warmup_ratio=0.03,train_on_inputs='auto',lora=False,suffix='claycog_05b_v2')
    state={'schema':'claycog-together-job/v2','job_id':job.id,'from_hf_model':hf_model,'template_model':TEMPLATE,'estimated_usd':price,'created_at_unix':int(time.time())}
    STATE.write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps(state,indent=2))
if __name__=='__main__': main()
