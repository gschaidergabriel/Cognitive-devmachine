import re, json, hashlib, sys, pathlib
src=pathlib.Path(sys.argv[1]).read_text()

def parse(src):
    classes=[]
    for m in re.finditer(r'class\s+(\w+)\s*=\s*([^\n]+)',src):
        classes.append({'name':m.group(1),'variants':[x.strip() for x in m.group(2).split('|')]})
    records=[]
    for m in re.finditer(r'record\s+(\w+)\s*\{(.*?)\}',src,re.S):
        fields=[]
        for line in m.group(2).splitlines():
            line=line.strip().rstrip(';')
            if not line: continue
            mm=re.fullmatch(r'([A-Za-z_][\w-]*)\s*:\s*(.+)',line)
            if not mm: raise SystemExit(f"parse_error:{m.group(1)}:{line}")
            fields.append({'name':mm.group(1),'type':mm.group(2).strip()})
        records.append({'name':m.group(1),'fields':fields})
    rules=[m.group(1).strip() for m in re.finditer(r'^rule\s+(.+)$',src,re.M)]
    cm=re.search(r'cycle\s*\((.*?)\)\s*\{(.*?)\}',src,re.S)
    if not cm: raise SystemExit('parse_error:cycle_missing')
    actions=[x.strip().rstrip(';') for x in cm.group(2).splitlines() if x.strip()]
    return {'classes':classes,'records':records,'rules':rules,'cycle':{'params':[x.strip() for x in cm.group(1).split(',')],'actions':actions}}

ir=parse(src)
declared={x['name'] for x in ir['classes']}|{x['name'] for x in ir['records']}
builtins={'Ref','Duration','Epoch','Score','Int','Cost','RecoveryRef','EvidenceRef','Set','Symbol','CapabilityToken','CapabilityRef','AuthorityRef','EffectAuthority','EffectToken'}
errors=[]
for rec in ir['records']:
    for f in rec['fields']:
        for t in re.findall(r'[A-Za-z_][\w-]*',f['type']):
            if t not in declared and t not in builtins: errors.append([rec['name'],f['name'],t])
if errors: raise SystemExit('type_error:'+json.dumps(errors))
for rec in ir['records']:
    if rec['name']=='LoopDynamicsReadout':
        for f in rec['fields']:
            if any(x in f['type'] for x in ['CapabilityToken','CapabilityRef','AuthorityRef','EffectAuthority','EffectToken']):
                raise SystemExit('effect_error:authority_in_readout')
canon=json.dumps(ir,sort_keys=True,separators=(',',':'))
pathlib.Path(sys.argv[2]).write_text(json.dumps(ir,indent=2,sort_keys=True))
runtime='''from dataclasses import dataclass\n\n@dataclass\nclass Readout:\n    loop_id: str\n    state_delta: float\n    residual_pressure: float\n    recurrence_count: int\n    recurrence_budget: int\n    convergence_rate: float\n    period: float | None\n    marginal_utility: float\n    compute_cost: float\n    bounded: bool\n    residual_trend: float\n    delta_trend: float\n\ndef classify(r):\n    if r.marginal_utility < -0.02 or r.residual_trend > 0.025 or r.delta_trend > 0.025:\n        return (\"DIVERGING_OR_OVERTHINKING\",\"ESCALATE\",\"negative_utility_or_growth\")\n    if r.state_delta < 0.035 and r.residual_pressure > 0.30:\n        return (\"STALLED\",\"ESCALATE\",\"low_delta_high_pressure\")\n    if r.state_delta < 0.035 and r.residual_pressure < 0.15 and r.residual_trend <= 0.005:\n        return (\"CONVERGING_FIXED_POINT\",\"HALT\",\"low_delta_low_pressure\")\n    if r.period is not None and r.bounded and r.marginal_utility > r.compute_cost:\n        if r.recurrence_count < r.recurrence_budget:\n            return (\"PRODUCTIVE_LIMIT_CYCLE\",\"CONTINUE\",\"bounded_periodic_positive_utility\")\n        return (\"PRODUCTIVE_LIMIT_CYCLE\",\"ROUTE\",\"budget_reached_preserve_cycle_class\")\n    return (\"CHAOTIC_OR_UNCLASSIFIED\",\"ROUTE\",\"insufficient_regime_evidence\")\n\ndef scalar_baseline(r):\n    if r.state_delta < 0.035:\n        return (\"CONVERGING_FIXED_POINT\",\"HALT\")\n    if r.period is not None:\n        return (\"DIVERGING_OR_OVERTHINKING\",\"HALT\")\n    if r.recurrence_count >= r.recurrence_budget:\n        return (\"CHAOTIC_OR_UNCLASSIFIED\",\"HALT\")\n    return (\"CHAOTIC_OR_UNCLASSIFIED\",\"CONTINUE\")\n'''
pathlib.Path(sys.argv[3]).write_text(runtime)
print(json.dumps({'source_hash':hashlib.sha256(src.encode()).hexdigest(),'canonical_ir_hash':hashlib.sha256(canon.encode()).hexdigest(),'generated_hash':hashlib.sha256(runtime.encode()).hexdigest(),'records':len(ir['records']),'rules':len(ir['rules']),'typecheck':'PASS','effectcheck':'PASS'}))
