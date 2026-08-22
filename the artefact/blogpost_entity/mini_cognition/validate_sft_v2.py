#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
PREFIX='module clay.cog.turn\nfn think(i:Map)->Map {\n'
REQUIRED=(
 'self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
 'role_bind(c,cfg("application.role"))','goal_bind(c,cfg("application.goal"))',
 'personality_bind(c,cfg("application.personality"))','return c\n}',
)
FORBIDDEN=('```','<think>','</think>','self_bind(c,"zero"','self_bind(c,"mini_entity"','role_bind(c,"blog','goal_bind(c,"write blog','personality_bind(c,"zero"','omega_execute(','tool_execute(','api_call(')
GATES=('grammar','types','schema','authority','generation')
def outside_strings(s):
 out=[]; quoted=False; esc=False
 for ch in s:
  if quoted:
   if esc: esc=False
   elif ch=='\\': esc=True
   elif ch=='"': quoted=False
   out.append(' ')
  else:
   if ch=='"': quoted=True; out.append(' ')
   else: out.append(ch)
 return ''.join(out)
def validate_code(s):
 e=[]; low=s.lower(); structural=outside_strings(s)
 if not s.startswith(PREFIX): e.append('bad_prefix')
 if s.strip()!=s or not s.endswith('}'): e.append('outer_text')
 if structural.count('{')!=structural.count('}'): e.append('brace_balance')
 if structural.count('(')!=structural.count(')'): e.append('paren_balance')
 for x in REQUIRED:
  if x not in s: e.append('missing:'+x)
 for x in FORBIDDEN:
  if x.lower() in low: e.append('forbidden:'+x)
 if 'omega_commit_candidate(' in s:
  for g in GATES:
   if f'omega_validate(w,"{g}")' not in s: e.append('omega_missing_gate:'+g)
  if 'omega_authority(w,' not in s: e.append('omega_missing_authority')
  if 'omega_generation(w,' not in s: e.append('omega_missing_generation')
 if 'omega_reject(' in s and 'omega_commit_candidate(' in s: e.append('reject_and_commit')
 return e
def load(path):
 rows=[]; bad=[]
 for no,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
  try:
   row=json.loads(line); ms=row['messages']
   if [m['role'] for m in ms]!=['system','user','assistant']: raise ValueError('role_order')
   errs=validate_code(ms[-1]['content'])
   if errs: bad.append((no,errs))
   rows.append(row)
  except Exception as exc: bad.append((no,['schema:'+repr(exc)]))
 return rows,bad
def digest(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main(train,valid):
 tr,tbad=load(train); va,vbad=load(valid)
 td=[digest(x) for x in tr]; vd=[digest(x) for x in va]
 report={
  'schema':'claycog-sft-validation/v2','train_lines':len(tr),'validation_lines':len(va),
  'train_structural_invalid':len(tbad),'validation_structural_invalid':len(vbad),
  'train_exact_duplicates':len(td)-len(set(td)),'validation_exact_duplicates':len(vd)-len(set(vd)),
  'cross_split_full_duplicates':len(set(td)&set(vd)),
  'cross_split_user_duplicates':len({x['messages'][1]['content'] for x in tr}&{x['messages'][1]['content'] for x in va}),
  'cross_split_assistant_duplicates':len({x['messages'][2]['content'] for x in tr}&{x['messages'][2]['content'] for x in va}),
 }
 report['ok']=all(report[k]==0 for k in ('train_structural_invalid','validation_structural_invalid','train_exact_duplicates','validation_exact_duplicates','cross_split_full_duplicates','cross_split_user_duplicates','cross_split_assistant_duplicates')) and len(tr)==1485 and len(va)==165
 print(json.dumps(report,indent=2))
 if tbad[:5] or vbad[:5]: print('first_errors',tbad[:5],vbad[:5],file=sys.stderr)
 return 0 if report['ok'] else 1
if __name__=='__main__': raise SystemExit(main(sys.argv[1],sys.argv[2]))
