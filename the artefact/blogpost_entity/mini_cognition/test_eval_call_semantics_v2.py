#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from eval_outputs_v1 import semantic_ok
from validate_sft_v1 import validate_code
from claycode_calls_v2 import fn_counts
subprocess.run([sys.executable,str(HERE/'generate_eval_ood_v1.py')],check=True,stdout=subprocess.DEVNULL)
specs=[json.loads(x) for x in (HERE/'eval_ood_v1.jsonl').read_text().splitlines()]
HEAD='module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n  role_bind(c,cfg("application.role"))\n  goal_bind(c,cfg("application.goal"))\n  personality_bind(c,cfg("application.personality"))\n'
TAIL='  return c\n}'
def legacy(output,spec): return all(x in output for x in spec['must_contain']) and all(x not in output for x in spec['must_not_contain'])
hyper=next(x for x in specs if x['family']=='hyperposition_ood')
h=HEAD+'  state_note(c,"spoof","hyper_alt(hp,","REPORTED")\n  let hp = hyper_new(c,"hp0")\n  hyper_discriminator(hp,"external")\n  collapse_guard(hp,"R6_required")\n'+TAIL
assert validate_code(h)==[] and fn_counts(h).get('hyper_alt',0)==0 and legacy(h,hyper) and not semantic_ok(h,hyper)
reject=next(x for x in specs if x['family']=='omega_reject_ood')
r=HEAD+'  state_note(c,"spoof","omega_reject(","REPORTED")\n  unknown_preserve(c,"action_transition","invalid_or_unbound_argument")\n'+TAIL
assert validate_code(r)==[] and fn_counts(r).get('omega_reject',0)==0 and legacy(r,reject) and not semantic_ok(r,reject)
quoted=HEAD+'  state_note(c,"spoof","omega_commit_candidate(c,w)","REPORTED")\n'+TAIL
assert validate_code(quoted)==[] and fn_counts(quoted).get('omega_commit_candidate',0)==0
print(json.dumps({'legacy_hyper_marker_attack_would_pass':True,'hardened_hyper_marker_attack_rejected':True,'legacy_reject_marker_attack_would_pass':True,'hardened_reject_marker_attack_rejected':True,'quoted_commit_not_structural_commit':True},indent=2))
