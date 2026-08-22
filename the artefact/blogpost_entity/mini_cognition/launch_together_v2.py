#!/usr/bin/env python3
"""Fail-closed Together BYOM launcher for ClayCode cognition corpus v2."""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
import together
from together import Together

HERE=Path(__file__).resolve().parent
TRAIN=HERE/'train_v2.jsonl'
VALID=HERE/'validation_v2.jsonl'
HF_MODEL=os.environ.get('CLAYCOG_HF_MODEL','Qwen/Qwen2.5-0.5B')
HF_REVISION=os.environ.get('CLAYCOG_HF_REVISION')
TEMPLATE=os.environ.get('CLAYCOG_TOGETHER_TEMPLATE','Qwen/Qwen2.5-7B-Instruct-Turbo')
EPOCHS=int(os.environ.get('CLAYCOG_EPOCHS','3'))
EVALS=int(os.environ.get('CLAYCOG_EVALS','2'))
MAX_USD=float(os.environ.get('CLAYCOG_MAX_JOB_USD','18.00'))
GUARD=Path(os.environ.get('CLAYCOG_CREATE_GUARD',str(HERE/'together_create_guard_v2.json')))

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomwrite(path,obj):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2,default=str)+'\n',encoding='utf-8')
    os.replace(tmp,path)

def run_local_checks():
    subprocess.run([sys.executable,str(HERE/'generate_sft_v2.py')],check=True)
    subprocess.run([sys.executable,str(HERE/'validate_sft_v1.py'),str(TRAIN)],check=True)
    subprocess.run([sys.executable,str(HERE/'validate_sft_v1.py'),str(VALID)],check=True)
    subprocess.run([sys.executable,str(HERE/'corpus_split_gate_v2.py'),str(TRAIN),str(VALID)],check=True)

def wait_file(client,file_id):
    while True:
        meta=client.files.retrieve(file_id)
        status=str(meta.processing_status)
        if status=='COMPLETED': return meta
        if status in ('INVALID_FORMAT','FAILED'):
            raise RuntimeError(f'Together rejected {file_id}: {status} {getattr(meta,"validation_report",None)}')
        time.sleep(5)

def objdict(x):
    if hasattr(x,'model_dump'): return x.model_dump()
    if hasattr(x,'dict'): return x.dict()
    return str(x)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--create',action='store_true')
    ap.add_argument('--instruct-ablation',action='store_true')
    args=ap.parse_args()
    if not os.environ.get('TOGETHER_API_KEY'):
        raise SystemExit('TOGETHER_API_KEY must exist only in the execution environment')
    if args.create and GUARD.exists():
        raise SystemExit('CREATE_GUARD_PRESENT: inspect/retrieve the prior attempt; do not create again blindly: '+GUARD.read_text(encoding='utf-8'))

    hf_model='Qwen/Qwen2.5-0.5B-Instruct' if args.instruct_ablation else HF_MODEL
    run_local_checks()
    client=Together()

    limits=client.fine_tuning.model_limits(model_name=TEMPLATE)
    if not getattr(limits,'supports_full_training',False):
        raise SystemExit(f'Template is not full-FT capable: {TEMPLATE}')

    train_file=client.files.upload(file=str(TRAIN),purpose='fine-tune',check=True)
    valid_file=client.files.upload(file=str(VALID),purpose='fine-tune',check=True)
    wait_file(client,train_file.id); wait_file(client,valid_file.id)

    estimate=client.fine_tuning.estimate_price(
        training_file=train_file.id, validation_file=valid_file.id, model=TEMPLATE,
        n_epochs=EPOCHS, n_evals=EVALS,
        training_method={'method':'sft','train_on_inputs':'auto'}, training_type={'type':'Full'},
    )
    price=float(estimate.estimated_total_price)
    report={
        'schema':'CLAYCOG_05B_TRAINING_PREFLIGHT/v2',
        'mode':'preflight' if not args.create else 'create',
        'sdk_version':getattr(together,'__version__','UNKNOWN'),
        'from_hf_model':hf_model,'hf_model_revision':HF_REVISION,
        'template_model':TEMPLATE,'epochs':EPOCHS,'evals':EVALS,
        'train_sha256':sha(TRAIN),'validation_sha256':sha(VALID),
        'estimated_usd':price,'allowed_to_proceed':bool(estimate.allowed_to_proceed),
        'price_detail':objdict(estimate),
        'compatibility_status':'UNPROVEN_UNTIL_TOGETHER_ACCEPTS_BYOM_CHECKPOINT',
    }
    print(json.dumps(report,indent=2,default=str))
    if not estimate.allowed_to_proceed: raise SystemExit('Together price/admission endpoint does not allow this job')
    if price>MAX_USD: raise SystemExit(f'BUDGET_ABORT estimated ${price:.2f} > ${MAX_USD:.2f}')
    if not args.create:
        print('PREFLIGHT_ONLY: no billed fine-tuning job created')
        return

    intent={
        'schema':'claycog-together-create-guard/v2','status':'CREATE_ATTEMPTED_UNKNOWN',
        'from_hf_model':hf_model,'hf_model_revision':HF_REVISION,'template_model':TEMPLATE,
        'train_file_id':train_file.id,'validation_file_id':valid_file.id,
        'train_sha256':sha(TRAIN),'validation_sha256':sha(VALID),
        'estimated_usd':price,'epochs':EPOCHS,'evals':EVALS,
        'rule':'If this process exits without a job_id, inspect Together jobs before any retry. Never delete the guard just to retry blindly.',
    }
    atomwrite(GUARD,intent)
    kwargs=dict(
        training_file=train_file.id,validation_file=valid_file.id,model=TEMPLATE,from_hf_model=hf_model,
        n_epochs=EPOCHS,n_evals=EVALS,n_checkpoints=1,learning_rate=1e-5,warmup_ratio=0.03,
        train_on_inputs='auto',lora=False,suffix='claycog_05b_v2',
    )
    if HF_REVISION: kwargs['hf_model_revision']=HF_REVISION
    job=client.fine_tuning.create(**kwargs)
    intent.update({'status':'CREATED','job_id':job.id})
    atomwrite(GUARD,intent)
    print(json.dumps({'job_id':job.id,'guard_file':str(GUARD),'estimated_usd':price,'next':'retrieve job; never duplicate create'},indent=2))

if __name__=='__main__': main()
