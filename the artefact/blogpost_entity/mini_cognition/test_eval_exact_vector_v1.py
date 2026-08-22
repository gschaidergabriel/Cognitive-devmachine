#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(HERE/'generate_eval_ood_v1.py')],check=True,stdout=subprocess.DEVNULL)
specs=[json.loads(x) for x in (HERE/'eval_ood_v1.jsonl').read_text().splitlines()]
HEAD='module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n  role_bind(c,cfg("application.role"))\n  goal_bind(c,cfg("application.goal"))\n  personality_bind(c,cfg("application.personality"))\n'
TAIL='  return c\n}'

def attack_output(s):
    fam=s['family']
    if fam=='omega_valid_ood':
        op=s['expected_omega']['operation']
        o=HEAD+'  let w = omega_new(c,"w0")\n'+f'  omega_bind(w,"operation","{op}")\n'+'  omega_authority(w,cfg("architecture.effect_authority"))\n  omega_generation(w,cfg("state.generation"))\n'
        for g in ('grammar','types','schema','authority','generation'): o+=f'  omega_validate(w,"{g}")\n'
        return o+'  omega_commit_candidate(c,w)\n'+TAIL
    if fam=='omega_reject_ood':
        return HEAD+'  let w = omega_new(c,"w0")\n  omega_reject(w,"generic_reject")\n  unknown_preserve(c,"action_transition","generic")\n'+TAIL
    if fam=='hyperposition_ood':
        return HEAD+'  let hp = hyper_new(c,"hp0")\n  hyper_alt(hp,"x","PLAUSIBLE")\n  hyper_alt(hp,"y","PLAUSIBLE")\n  hyper_discriminator(hp,"generic")\n  collapse_guard(hp,"R6_required")\n'+TAIL
    return HEAD+'  focus_set(c,"generic_runtime_cfg")\n'+TAIL

def q(v): return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def oracle_output(s):
    fam=s['family']
    if fam=='omega_valid_ood':
        e=s['expected_omega']; o=HEAD+'  let w = omega_new(c,"w0")\n'
        o+=f'  omega_bind(w,"operation",{q(e["operation"])})\n'
        for a in e['args']: o+=f'  omega_arg(w,{q(a["name"])},{q(a["value"])},{q(a["type"])})\n'
        o+=f'  omega_schema(w,{q(e["schema"])})\n  omega_authority(w,{e["authority_expr"]})\n  omega_generation(w,{e["generation_expr"]})\n'
        for g in e['validators']: o+=f'  omega_validate(w,{q(g)})\n'
        return o+'  omega_commit_candidate(c,w)\n'+TAIL
    return attack_output(s)

def write(name,fn):
    (HERE/name).write_text(''.join(json.dumps({'id':s['id'],'output':fn(s)},separators=(',',':'))+'\n' for s in specs))

write('attack_outputs.jsonl',attack_output)
attack=subprocess.run([sys.executable,str(HERE/'eval_outputs_v1.py'),str(HERE/'eval_ood_v1.jsonl'),str(HERE/'attack_outputs.jsonl')],capture_output=True,text=True)
assert attack.returncode==1, attack.stdout+attack.stderr
ar=json.loads(attack.stdout)
assert ar['strict_claycode_rate']==1.0
assert ar['by_family']['omega_valid_ood']['semantic']==0.0
assert ar['semantic_gate_rate']==0.6

write('oracle_outputs.jsonl',oracle_output)
oracle=subprocess.run([sys.executable,str(HERE/'eval_outputs_v1.py'),str(HERE/'eval_ood_v1.jsonl'),str(HERE/'oracle_outputs.jsonl')],capture_output=True,text=True)
assert oracle.returncode==0, oracle.stdout+oracle.stderr
orr=json.loads(oracle.stdout)
assert orr['strict_claycode_rate']==1.0 and orr['semantic_gate_rate']==1.0

rows=(HERE/'oracle_outputs.jsonl').read_text().splitlines()
(HERE/'duplicate_outputs.jsonl').write_text('\n'.join(rows+[rows[0]])+'\n')
dup=subprocess.run([sys.executable,str(HERE/'eval_outputs_v1.py'),str(HERE/'eval_ood_v1.jsonl'),str(HERE/'duplicate_outputs.jsonl')],capture_output=True,text=True)
assert dup.returncode==1 and json.loads(dup.stdout)['duplicate_output_ids']
unknown=json.dumps({'id':'unexpected_extra','output':oracle_output(specs[0])},separators=(',',':'))
(HERE/'unknown_outputs.jsonl').write_text('\n'.join(rows+[unknown])+'\n')
unk=subprocess.run([sys.executable,str(HERE/'eval_outputs_v1.py'),str(HERE/'eval_ood_v1.jsonl'),str(HERE/'unknown_outputs.jsonl')],capture_output=True,text=True)
assert unk.returncode==1 and json.loads(unk.stdout)['unknown_output_ids']==['unexpected_extra']

# Comment-smuggling regression: the shared canonical syntax authority now rejects
# comment syntax at admission and independently grants no semantic call credit.
from eval_outputs_v1 import semantic_ok
from validate_sft_v1 import validate_code
from claycode_calls_v2 import call_set, fn_counts

hyper=next(s for s in specs if s['family']=='hyperposition_ood')
comment_hyper=(HEAD+
    '  // hyper_alt(hp,"x","PLAUSIBLE")\n'
    '  // hyper_discriminator(hp,"generic")\n'
    '  // collapse_guard(hp,"R6_required")\n'+TAIL)
assert 'comment_syntax_forbidden' in validate_code(comment_hyper)
assert not semantic_ok(comment_hyper,hyper)
assert fn_counts(comment_hyper).get('hyper_alt',0)==0

omega=next(s for s in specs if s['family']=='omega_valid_ood')
e=omega['expected_omega']
comment_omega=HEAD
comment_omega+=f'  // omega_bind(w,"operation",{q(e["operation"])})\n'
for a in e['args']:
    comment_omega+=f'  // omega_arg(w,{q(a["name"])},{q(a["value"])},{q(a["type"])})\n'
comment_omega+=f'  // omega_schema(w,{q(e["schema"])})\n'
comment_omega+=f'  // omega_authority(w,{e["authority_expr"]})\n'
comment_omega+=f'  // omega_generation(w,{e["generation_expr"]})\n'
for g in e['validators']:
    comment_omega+=f'  // omega_validate(w,{q(g)})\n'
comment_omega+='  // omega_commit_candidate(c,w)\n'+TAIL
assert 'comment_syntax_forbidden' in validate_code(comment_omega)
assert not semantic_ok(comment_omega,omega)
assert fn_counts(comment_omega).get('omega_commit_candidate',0)==0

block='/* omega_commit_candidate(c,w) */\n'+oracle_output(omega)
assert fn_counts(block).get('omega_commit_candidate',0)==1
assert 'omega_commit_candidate(c,w)' in call_set(block)

print(json.dumps({'attack_rejected':True,'attack_semantic_rate':ar['semantic_gate_rate'],'omega_valid_attack_semantic':ar['by_family']['omega_valid_ood']['semantic'],'oracle_passed':True,'duplicate_id_rejected':True,'unknown_id_rejected':True,'comment_syntax_fail_closed':True,'comment_smuggling_rejected':True,'comment_only_hyper_calls':0,'comment_only_omega_commit_calls':0,'block_comment_ignored':True},indent=2))
