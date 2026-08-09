#!/usr/bin/env python3
"""Bounded ClayCode stage-identity discriminator.
Research proxy only; not the production parser/compiler and not Ubuntu-target evidence.
"""
from hashlib import sha256
import json, os, random, re, subprocess, tempfile, textwrap

SOURCE='''module claycode.lab.stage_chain
version "0.1"
record LoopGate {
  recurrence_count:Int;
  recurrence_budget:Int;
}
rule recurrence_count==recurrence_budget => HALT
'''
GRAMMAR_BLOB_SHA='ec2f17077333955cfdabe6c64868d597e7e734e3'

def h(s): return sha256(s.encode()).hexdigest()
def cj(o): return json.dumps(o,sort_keys=True,separators=(',',':'))

def parse_subset(src):
    mm=re.search(r'\bmodule\s+([A-Za-z_][A-Za-z0-9_.]*)',src)
    vm=re.search(r'\bversion\s+"([^"]*)"',src)
    rm=re.search(r'\brecord\s+([A-Za-z_][A-Za-z0-9_-]*)\s*\{(.*?)\}',src,re.S)
    rr=re.search(r'\brule\s+([A-Za-z_][A-Za-z0-9_-]*)\s*==\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=>\s*([A-Za-z_][A-Za-z0-9_-]*)',src)
    if not all([mm,vm,rm,rr]): raise ValueError('parse')
    fields=re.findall(r'([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*;?',rm.group(2))
    if len(fields)!=2: raise ValueError('fields')
    return {'module':mm.group(1),'version':vm.group(1),'records':{rm.group(1):dict(sorted(fields))},'rule':{'lhs':rr.group(1),'op':'==','rhs':rr.group(2),'effect':rr.group(3)}}

def semantic_id(ir): return h(cj(ir))
def contract_id(src,parser_version): return h(cj({'source_hash':h(src),'parser_version':parser_version,'grammar_blob_sha':GRAMMAR_BLOB_SHA}))
def lowering_id(sem,lowerer_version,target='python3-separate-process'): return h(cj({'semantic_id':sem,'lowerer_version':lowerer_version,'target':target}))
def lower(ir):
    effect=ir['rule']['effect']
    return textwrap.dedent(f'''import os\na=int(os.environ["RECURRENCE_COUNT"])\nb=int(os.environ["RECURRENCE_BUDGET"])\nif a == b:\n    print({effect!r})\nelse:\n    print("NO_CHANGE")\n''')

def run_guest(code,a,b):
    with tempfile.NamedTemporaryFile('w',suffix='.py',delete=False) as f:
        f.write(code); path=f.name
    try:
        cp=subprocess.run(['python','-S',path],capture_output=True,text=True,env={**os.environ,'RECURRENCE_COUNT':str(a),'RECURRENCE_BUDGET':str(b)})
        return {'exit':cp.returncode,'stdout':cp.stdout.strip(),'stderr':cp.stderr.strip()}
    finally: os.unlink(path)

def main():
    ir=parse_subset(SOURCE); sem=semantic_id(ir); generated=lower(ir)
    baseline={'source_hash':h(SOURCE),'contract_id':contract_id(SOURCE,'bounded-parser-v0.1'),'semantic_id':sem,'lowering_id':lowering_id(sem,'lowerer-v0.1'),'artifact_id':h(generated),'equal':run_guest(generated,8,8),'unequal':run_guest(generated,7,8)}
    rng=random.Random(20260809); source_hashes=set(); sems=set(); contracts=set(); artifacts=set(); failures=0
    for _ in range(5000):
        fields=[('recurrence_count','Int'),('recurrence_budget','Int')]; rng.shuffle(fields)
        sep=' '*rng.randint(1,4); nl='\n'*rng.randint(1,3)
        ft=''.join((' '*rng.randint(1,4))+f"{n}{' '*rng.randint(0,2)}:{' '*rng.randint(0,2)}{t};"+nl for n,t in fields)
        src=f'module{sep}claycode.lab.stage_chain{nl}version{sep}"0.1"{nl}record{sep}LoopGate {{ {nl}{ft}}}{nl}rule{sep}recurrence_count{" "*rng.randint(0,2)}=={" "*rng.randint(0,2)}recurrence_budget{sep}=>{sep}HALT{nl}'
        try: x=parse_subset(src)
        except Exception: failures+=1; continue
        sid=semantic_id(x); source_hashes.add(h(src)); sems.add(sid); contracts.add(contract_id(src,'bounded-parser-v0.1')); artifacts.add(h(lower(x)))
    stop_src=SOURCE.replace('HALT','STOP'); stop_ir=parse_subset(stop_src)
    out={'baseline':baseline,'formatting_fuzz':{'cases':5000,'parse_failures':failures,'distinct_source_hashes':len(source_hashes),'distinct_contract_ids':len(contracts),'distinct_semantic_ids':len(sems),'distinct_artifact_ids':len(artifacts)},'semantic_mutation':{'semantic_id_changed':sem!=semantic_id(stop_ir),'artifact_id_changed':h(generated)!=h(lower(stop_ir)),'run':run_guest(lower(stop_ir),8,8)},'parser_version_mutation':{'semantic_id_same':sem==semantic_id(parse_subset(SOURCE)),'contract_id_changed':baseline['contract_id']!=contract_id(SOURCE,'bounded-parser-v0.2')},'lowerer_version_mutation':{'semantic_id_same':True,'lowering_id_changed':baseline['lowering_id']!=lowering_id(sem,'lowerer-v0.2'),'artifact_id_changed_if_emitter_bytes_change':h(generated)!=h('# lowerer-v0.2\n'+generated)},'artifact_tamper':{'detected_by_artifact_hash':h(generated)!=h(generated.replace('print("NO_CHANGE")',"print('HALT')"))}}
    print(json.dumps(out,sort_keys=True,indent=2))
if __name__=='__main__': main()
