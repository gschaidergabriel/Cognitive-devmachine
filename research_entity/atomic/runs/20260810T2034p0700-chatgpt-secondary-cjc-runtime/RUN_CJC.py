#!/usr/bin/env python3
"""Repo-local runner for the ATOMIC CJC packet."""
from __future__ import annotations
import json,pathlib,subprocess,sys,time,os
ROOT=pathlib.Path(__file__).resolve().parent; IMPL=ROOT/'implementation'; TESTS=ROOT/'tests'; BENCH=ROOT/'benchmarks'
def run(cmd):
    env=dict(os.environ); env['PYTHONPATH']=str(IMPL)+(':'+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True)
    return {'cmd':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def main():
    started=time.time(); checks=[]
    checks.append(run([sys.executable,'-m','unittest','-v',str(TESTS/'test_cjc_runtime_all.py')]))
    checks.append(run([sys.executable,str(IMPL/'causal_jet_commutator.py')]))
    checks.append(run([sys.executable,str(BENCH/'benchmark_cjc_compact.py'),'--n','100']))
    receipt={'schema_version':'1.0','candidate':'ATOMIC-CANDIDATE-CJC-001','started_unix':started,'finished_unix':time.time(),'checks':checks,'pass':all(x['returncode']==0 for x in checks),'architecture_promotion':False,'effect_authority_minted':False,'target_vps_evidence':False}
    text=json.dumps(receipt,indent=2,sort_keys=True)+'\n'; (ROOT/'RUN_RECEIPT.json').write_text(text); print(text,end=''); return 0 if receipt['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
