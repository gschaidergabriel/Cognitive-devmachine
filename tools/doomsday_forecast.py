#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, json, math, re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

COMPLETE={"PASS","COMPLETE","COMPLETED","DONE","CLOSED"}
EVENT_TYPES={"ACCELERATOR","ELIMINATION","BLOCKER","REWORK","CAPACITY_CHANGE","NEW_DEPENDENCY","OWNER_AUTHORIZATION"}
VERIFIED_PREFIXES=("RUNTIME_VERIFIED",)


def load_json(path: Path, default=None):
    try:
        x=json.loads(path.read_text(encoding='utf-8'))
        return x if isinstance(x,dict) else (default if default is not None else {})
    except (FileNotFoundError,json.JSONDecodeError):
        return default if default is not None else {}

def load_jsonl(path: Path):
    out=[]
    try: lines=path.read_text(encoding='utf-8').splitlines()
    except FileNotFoundError: return out
    for n,line in enumerate(lines,1):
        if not line.strip(): continue
        try: x=json.loads(line)
        except json.JSONDecodeError as e:
            out.append({'_invalid':True,'_line':n,'_error':str(e)}); continue
        if isinstance(x,dict): x.setdefault('_line',n); out.append(x)
        else: out.append({'_invalid':True,'_line':n,'_error':'not_object'})
    return out

def nested(d:dict,dotted:str,default=None):
    x=d
    for p in dotted.split('.'):
        if not isinstance(x,dict) or p not in x: return default
        x=x[p]
    return x

def is_complete(v): return str(v or '').upper() in COMPLETE

def package_progress(workspace:dict, field='work_packages', prefixes=None):
    pkgs=nested(workspace,field,{})
    if not isinstance(pkgs,dict) or not pkgs: return 0.0
    rows=[]
    for pid,payload in pkgs.items():
        if prefixes and not any(str(pid).startswith(x) for x in prefixes): continue
        rows.append(payload if isinstance(payload,dict) else {'status':str(payload)})
    if not rows:return 0.0
    done=total=0.0
    for p in rows:
        w=float(p.get('weight',1) or 1)
        frac=1.0 if is_complete(p.get('status')) else 0.0
        sc=p.get('subchecks')
        if isinstance(sc,dict) and sc:
            sd=st=0.0
            for item in sc.values():
                if isinstance(item,dict): sw=float(item.get('weight',1) or 1); ss=item.get('status')
                else: sw=1.0; ss=item
                st+=sw; sd+=sw if is_complete(ss) else 0
            frac=sd/st if st else 0
        done+=w*frac; total+=w
    return done/total if total else 0.0

def stage_progress(root:Path, program:dict, stage_id:str):
    stage=(program.get('stage_gates') or {}).get(stage_id) or {}
    if is_complete(stage.get('status')): return 1.0,'stage_status_pass'
    s=stage.get('progress_source') or {}; kind=s.get('kind')
    if kind=='archive_assimilation':
        w=load_json(root/str(s.get('path','')), {})
        pct=float(nested(w,str(s.get('percent_field','combined_progress.exact_coverage_percent')),s.get('fallback_percent',0)) or 0)
        return max(0,min(1,pct/100)),'frozen_atomic_obligations'
    if kind in {'work_packages','stage_workspace'}:
        p=root/str(s.get('path',''))
        if not p.exists(): return float(s.get('missing_means',0) or 0)/100.0,'workspace_missing'
        w=load_json(p,{})
        pref=[str(x) for x in s.get('include_prefixes',[])] or None
        return package_progress(w,str(s.get('field','work_packages')),pref),'work_packages'
    if kind=='terminal': return max(0,min(1,float(s.get('value',0) or 0)/100)),'terminal'
    return 0.0,'no_progress_source'

def row_progress(root,program,row,events):
    kind=row.get('kind')
    if kind=='program_stage': return stage_progress(root,program,str(row['stage_id']))
    if kind=='owner_gate':
        ok=any(e.get('type')=='OWNER_AUTHORIZATION' and e.get('status')=='VERIFIED' and 'OWNER_TRAINING_RELEASE_GATE' in e.get('affected_rows',[]) for e in events)
        return (1.0,'owner_authorization_receipt') if ok else (0.0,'conditional_immediate_authorization_assumption')
    rel=row.get('future_workspace')
    if not rel:return 0.0,'no_workspace_yet'
    w=load_json(root/str(rel),{})
    if not w:return 0.0,'workspace_missing'
    if is_complete(w.get('status')) or is_complete(w.get('gate_status')):return 1.0,'workspace_pass'
    return package_progress(w),'work_packages'

def validate_event(e,known):
    if e.get('_invalid'):return False,'invalid_json'
    t=str(e.get('type',''))
    if t not in EVENT_TYPES:return False,'unknown_event_type'
    if e.get('status')!='VERIFIED':return False,'not_verified'
    affected=e.get('affected_rows') or []
    if not isinstance(affected,list) or not affected:return False,'missing_affected_rows'
    if any(str(r) not in known for r in affected):return False,'unknown_affected_row'
    if t!='OWNER_AUTHORIZATION':
        refs=e.get('evidence_refs') or []
        if not isinstance(refs,list) or not refs:return False,'missing_evidence_refs'
    if t in {'ACCELERATOR','BLOCKER','REWORK'}:
        try:m=float(e.get('multiplier'))
        except: return False,'invalid_multiplier'
        if m<=0:return False,'invalid_multiplier'
        if t=='ACCELERATOR' and m>=1:return False,'accelerator_multiplier_must_lt_1'
        if t in {'BLOCKER','REWORK'} and m<=1:return False,'blocker_multiplier_must_gt_1'
    if t=='NEW_DEPENDENCY' and str(e.get('dependency_row')) not in known:return False,'unknown_dependency'
    return True,'ok'

def apply_events(rows,raw):
    cooked=copy.deepcopy(rows); acc=[]; rej=[]; known=set(cooked)
    for e in raw:
        ok,reason=validate_event(e,known)
        if not ok: rej.append({'event_id':e.get('event_id'),'line':e.get('_line'),'reason':reason}); continue
        acc.append(e); t=e.get('type')
        if t=='OWNER_AUTHORIZATION':continue
        for rid in e.get('affected_rows',[]):
            r=cooked[str(rid)]; r.setdefault('event_factor',1.0); r.setdefault('applied_events',[]); r['applied_events'].append(e.get('event_id') or f"line-{e.get('_line')}")
            if t in {'ACCELERATOR','BLOCKER','REWORK'}:r['event_factor']*=float(e['multiplier'])
            elif t=='ELIMINATION':r['eliminated']=True;r['event_factor']=0.0
            elif t=='CAPACITY_CHANGE' and e.get('earliest_start'):r['event_earliest_start']=str(e['earliest_start'])
            elif t=='NEW_DEPENDENCY':
                dep=str(e['dependency_row']); deps=[str(x) for x in r.get('dependencies',[])]
                if dep not in deps:deps.append(dep)
                r['dependencies']=deps
    return cooked,acc,rej

def load_capabilities(root:Path, registry_path:Path):
    reg=load_json(registry_path,{'tools':[]}); tools=list(reg.get('tools',[])); by={x.get('tool_name'):i for i,x in enumerate(tools) if isinstance(x,dict) and x.get('tool_name')}
    for p in sorted((root/'research_entity'/'global').glob('*_RESEARCH_CAPABILITY.json')):
        x=load_json(p,{})
        name=x.get('tool_name')
        if not name: continue
        x['_capability_file']=str(p.relative_to(root))
        if name in by:
            merged=dict(tools[by[name]]); merged.update(x); tools[by[name]]=merged
        else:
            by[name]=len(tools); tools.append(x)
    return [x for x in tools if isinstance(x,dict) and x.get('tool_name')]

def runtime_verified(status): return str(status or '').startswith(VERIFIED_PREFIXES)

def infer_relevance(tool, rules):
    text=' '.join([str(tool.get('class','')),str(tool.get('provider','')),str(tool.get('tool_name',''))]+[str(x) for x in tool.get('preferred_for',[]) if x]).lower()
    rows=set()
    for rule in rules.get('inference_rules',[]):
        kws=[str(x).lower() for x in rule.get('keywords',[])]
        if any(k in text for k in kws): rows.update(str(x) for x in rule.get('rows',[]))
    return sorted(rows)

def capability_impacts(capabilities,rules,known_rows):
    table=[]; calibrated_by_row={}
    for tool in capabilities:
        relevant=infer_relevance(tool,rules)
        explicit=tool.get('doomsday_forecast') if isinstance(tool.get('doomsday_forecast'),dict) else {}
        for rid in explicit.get('relevant_rows',[]) or []:
            if str(rid) in known_rows: relevant.append(str(rid))
        relevant=sorted(set(x for x in relevant if x in known_rows))
        verified=runtime_verified(tool.get('status'))
        calibrated=[]
        for imp in explicit.get('impacts',[]) or []:
            if not isinstance(imp,dict) or imp.get('status')!='VERIFIED': continue
            refs=imp.get('evidence_refs') or []
            try:m=float(imp.get('multiplier'))
            except:continue
            if not refs or m<=0:continue
            for rid in imp.get('rows',[]) or []:
                rid=str(rid)
                if rid not in known_rows:continue
                calibrated.append({'row':rid,'multiplier':m,'evidence_refs':refs})
                if verified:
                    calibrated_by_row.setdefault(rid,[]).append({'tool':tool['tool_name'],'multiplier':m,'evidence_refs':refs})
        state='ACTIVE_CALIBRATED' if calibrated and verified else ('ACTIVE_UNCALIBRATED' if verified and relevant else ('POTENTIAL_UNVERIFIED' if relevant else 'NO_DIRECT_PATH_IMPACT'))
        table.append({'tool':tool['tool_name'],'provider':tool.get('provider'),'status':tool.get('status'),'state':state,'relevant_rows':relevant,'calibrated_impacts':calibrated})
    row_factors={};chosen={}
    for rid,items in calibrated_by_row.items():
        best=min(items,key=lambda x:x['multiplier'])
        row_factors[rid]=best['multiplier']; chosen[rid]=best
    return table,row_factors,chosen

def topo(rows):
    out=[]; temp=set(); perm=set()
    def visit(n):
        if n in perm:return
        if n in temp:raise ValueError(f'dependency_cycle:{n}')
        if n not in rows:raise ValueError(f'missing_dependency:{n}')
        temp.add(n)
        for d in rows[n].get('dependencies',[]):visit(str(d))
        temp.remove(n);perm.add(n);out.append(n)
    for n in rows:visit(n)
    return out

def measured_eta(stage_id,progress,throughput,prior):
    rates=[]
    for o in throughput.get('observations',[]) or []:
        if not isinstance(o,dict) or o.get('stage_id')!=stage_id:continue
        frac=o.get('completed_fraction')
        if frac is None:
            try: frac=float(o.get('completed_weight'))/float(o.get('total_weight'))
            except: frac=None
        try:hours=float(o.get('owner_active_hours'))
        except:hours=0
        if frac and hours>0: rates.append(float(frac)/hours)
    if rates:
        rates.sort(); rate=rates[len(rates)//2]; hpd=float(throughput.get('user_active_hours_per_day',10) or 10); c=((1-progress)/rate)/hpd
        return max(.05,c*.7),max(.1,c*1.5),'measured_stage_velocity'
    return float(prior.get('low',0) or 0)*(1-progress),float(prior.get('high',0) or 0)*(1-progress),'row_prior'

def row_duration(row,progress,throughput,cap_factor):
    if row.get('eliminated'):return 0.0,0.0,'verified_elimination'
    prior=row.get('prior_days') or {'low':0,'high':0}
    if row.get('kind')=='program_stage': low,high,basis=measured_eta(str(row.get('stage_id')),progress,throughput,prior)
    else: low=float(prior.get('low',0) or 0)*(1-progress);high=float(prior.get('high',0) or 0)*(1-progress);basis='row_prior'
    event_factor=float(row.get('event_factor',1.0) or 1.0)
    factor=event_factor*cap_factor
    return low*factor,high*factor,basis

def parse_iso_date(v):
    if not v:return None
    try:return date.fromisoformat(str(v)[:10])
    except:return None

def extract_dates(strings):
    out=[]
    for s in strings or []:
        for m in re.finditer(r'20\d\d-\d\d-\d\d',str(s)):
            d=parse_iso_date(m.group(0))
            if d:out.append(d)
    return sorted(set(out))

def capacity_floor(row_id,row,capacity,bound):
    event=parse_iso_date(row.get('event_earliest_start'))
    if row_id!='PROJECT_HARDWARE_DEPLOYMENT':return event,('event_floor' if event else None)
    active=nested(capacity,'compute.available_now',[]) or []
    expected=nested(capacity,'compute.expected_not_yet_available',[]) or []
    expdates=extract_dates(expected)
    next_hw=min(expdates) if expdates else None
    if active and bound=='low':return event,'active_project_hardware_assumed_capable_for_low_bound'
    if active:
        floor=max([d for d in [event,next_hw] if d],default=None)
        return floor,'high_bound_allows_expected_hardware_fallback' if floor else 'active_project_hardware_no_dated_fallback'
    floor=max([d for d in [event,next_hw] if d],default=None)
    return floor,'no_active_project_hardware'

def confidence(rows,rejected,conditional,cap_table):
    very_low=any(str(r.get('confidence','')).startswith('VERY_LOW') for r in rows.values())
    uncal=sum(1 for x in cap_table if x['state']=='ACTIVE_UNCALIBRATED')
    if very_low or conditional or rejected:return 'VERY_LOW' if very_low else 'LOW_CONDITIONAL'
    if uncal>2:return 'LOW'
    return 'MEDIUM'

def resolve(root:Path,as_of:date):
    program=load_json(root/'research_entity/rooms/PROGRAM_STATE.json',{})
    throughput=load_json(root/'research_entity/rooms/PROGRAM_THROUGHPUT.json',{})
    capacity=load_json(root/'research_entity/rooms/CAPACITY_STATE.json',{})
    model=load_json(root/'research_entity/forecast/DOOMSDAY_FORECAST_MODEL.json',{})
    rules=load_json(root/'research_entity/forecast/DOOMSDAY_CAPABILITY_RULES.json',{})
    raw=load_jsonl(root/'research_entity/forecast/DOOMSDAY_EVENTS.jsonl')
    rows,events,rejected=apply_events(model.get('rows') or {},raw)
    capabilities=load_capabilities(root,root/'research_entity/global/EXTERNAL_RESEARCH_TOOL_REGISTRY.json')
    cap_table,cap_factors,cap_chosen=capability_impacts(capabilities,rules,set(rows))
    order=topo(rows); epoch=datetime.combine(as_of,datetime.min.time())
    conditional=not any(e.get('type')=='OWNER_AUTHORIZATION' and 'OWNER_TRAINING_RELEASE_GATE' in e.get('affected_rows',[]) for e in events)
    results={}; total_scope=completed_scope=0.0
    for rid in order:
        row=rows[rid]; p,pbasis=row_progress(root,program,row,events); cf=float(cap_factors.get(rid,1.0)); low,high,ebasis=row_duration(row,p,throughput,cf)
        prior=row.get('prior_days') or {}; center=(float(prior.get('low',0) or 0)+float(prior.get('high',0) or 0))/2
        event_factor=float(row.get('event_factor',1.0) or 1.0); scope=0 if row.get('eliminated') else center*event_factor*cf
        total_scope+=scope; completed_scope+=scope*p
        deps=[str(x) for x in row.get('dependencies',[])]
        sl=max([epoch]+[results[d]['finish_low'] for d in deps]); sh=max([epoch]+[results[d]['finish_high'] for d in deps])
        fl,cb1=capacity_floor(rid,row,capacity,'low'); fh,cb2=capacity_floor(rid,row,capacity,'high')
        if fl:sl=max(sl,datetime.combine(fl,datetime.min.time()))
        if fh:sh=max(sh,datetime.combine(fh,datetime.min.time()))
        finish_low=sl+timedelta(days=max(0,low));finish_high=sh+timedelta(days=max(0,high));finish_high=max(finish_high,finish_low)
        results[rid]={'row_id':rid,'label':row.get('label',rid),'progress_percent':round(p*100,2),'progress_basis':pbasis,'remaining_days_low':round(low,3),'remaining_days_high':round(high,3),'effort_basis':ebasis,'event_factor':event_factor,'capability_factor':cf,'capability_choice':cap_chosen.get(rid),'dependencies':deps,'start_low':sl,'start_high':sh,'finish_low':finish_low,'finish_high':finish_high,'capacity_basis_low':cb1,'capacity_basis_high':cb2,'confidence':row.get('confidence'),'applied_events':row.get('applied_events',[])}
    terminal=str(model.get('terminal_row')); tr=results[terminal]
    prog=completed_scope/total_scope if total_scope else 0
    center=tr['finish_low']+(tr['finish_high']-tr['finish_low'])/2
    return {'as_of':as_of.isoformat(),'target':'DOOMSDAY / Clay 0.1','progress_percent':round(prog*100,1),'forecast_low':tr['finish_low'].date().isoformat(),'forecast_high':tr['finish_high'].date().isoformat(),'forecast_center':center.date().isoformat(),'confidence':confidence(rows,rejected,conditional,cap_table),'conditional_on_immediate_training_authorization':conditional,'rows':[results[r] for r in order],'capabilities':cap_table,'accepted_events':events,'rejected_events':rejected,'scope_center_days':round(total_scope,2)}

def serializable(x):
    if isinstance(x,(datetime,date)):return x.isoformat()
    raise TypeError

def render_table(r):
    lines=[f"DOOMSDAY / Clay 0.1: {r['progress_percent']}% | {r['forecast_low']} .. {r['forecast_high']} | center {r['forecast_center']} | {r['confidence']}","","WORKSTREAM | % | DAYS LOW-HIGH | CAPABILITY FACTOR | FINISH LOW..HIGH","---|---:|---:|---:|---"]
    for x in r['rows']:
        lines.append(f"{x['row_id']} | {x['progress_percent']:.1f} | {x['remaining_days_low']:.1f}-{x['remaining_days_high']:.1f} | {x['capability_factor']:.2f} | {x['finish_low'].date()}..{x['finish_high'].date()}")
    lines.append('');lines.append('CAPABILITIES')
    for c in r['capabilities']:
        if c['state']!='NO_DIRECT_PATH_IMPACT':lines.append(f"- {c['tool']}: {c['state']} -> {','.join(c['relevant_rows']) or '-'}")
    if r['conditional_on_immediate_training_authorization']:lines.append('- Conditional: assumes owner authorizes final training immediately when corpus is ready.')
    return '\n'.join(lines)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--as-of');ap.add_argument('--json',action='store_true');a=ap.parse_args();d=parse_iso_date(a.as_of) if a.as_of else date.today();r=resolve(Path(a.root),d);print(json.dumps(r,default=serializable,indent=2) if a.json else render_table(r))
if __name__=='__main__':main()
