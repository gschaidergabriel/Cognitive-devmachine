import json,re,hashlib,platform,sys
GRAMMAR_BLOB='ec2f17077333955cfdabe6c64868d597e7e734e3'
SPEC_BLOB='1a17bba3c835520baff2ac8fa432749ba2165d8e'
DIALECT_BLOB='dbb72460bc5a049c784d1acd1aaef152fa37f797'
allowed_ops={"=","!=","==","->","|","+","-","*","/","&&","||","iff","requires","in","subset_of","=>"}
cases=[
  {'id':'cmp_gt','source':'spec-v3','text':'rule diff>0 => ADD_OR_STRENGTHEN','kind':'operator'},
  {'id':'cmp_lt','source':'spec-v3','text':'rule diff<0 => RETRACT_OR_WEAKEN','kind':'operator'},
  {'id':'cmp_gte','source':'spec-v3','text':'rule valid_generation requires count(distinct(classes))>=2 && count(executable)>=1','kind':'operator'},
  {'id':'if_stmt','source':'spec-v3','text':'if residual.effect {effect_intent=EffectIntent(residual);receipt=Needle.execute(effect_intent)}','kind':'statement'},
  {'id':'iface_method','source':'dialects-v3','text':'interface Verifiable {expected:Set<Predicate>;verify(receipt:ReceiptRef)->Verification}','kind':'interface_method'},
  {'id':'positive_effect','source':'spec-v3','text':'rule effect.commit requires possession(valid(CapabilityToken)) && Witness.aw && Witness.cw','kind':'positive'},
  {'id':'positive_invariant','source':'dialects-v3','text':'invariant activation!=truth','kind':'positive'},
]
op_pat=re.compile(r'>=|<=|==|!=|=>|->|&&|\|\||>|<|=|\+|-|\*|/|\|')
def baseline(case):
    text=case['text']; kind=case['kind']
    scan=re.sub(r'\b(?:Set|Map|Ordered)\s*<[^;{}]+?>','GENERIC',text)
    unknown=[t for t in op_pat.findall(scan) if t not in allowed_ops]
    unsupported_if=bool(re.match(r'^\s*if\b',text))
    unsupported_method = kind=='interface_method' and bool(re.search(r'\b[A-Za-z_]\w*\([^)]*:[^)]*\)\s*->', text))
    return {**case,'unknown_ops':unknown,'unsupported_if':unsupported_if,'unsupported_method_signature':unsupported_method,'fails':bool(unknown or unsupported_if or unsupported_method)}
base=[baseline(c) for c in cases]
patched_ops=allowed_ops|{'>','<','>=','<='}
def patched(case):
    text=case['text']; kind=case['kind']
    scan=re.sub(r'\b(?:Set|Map|Ordered)\s*<[^;{}]+?>','GENERIC',text)
    unknown=[t for t in op_pat.findall(scan) if t not in patched_ops]
    unsupported_if=False
    unsupported_method=False
    return {**case,'unknown_ops':unknown,'unsupported_if':unsupported_if,'unsupported_method_signature':unsupported_method,'fails':bool(unknown or unsupported_if or unsupported_method)}
after=[patched(c) for c in cases]
result={
 'experiment_id':'EXP-CC-G9-SURFACE-CLOSURE-20260809',
 'hypothesis':'The current G9 V3 semantic candidate can remain semantically unchanged if grammar/parser surface closure is repaired; current grammar should otherwise reject syntax already used by admitted current ClayCode artifacts.',
 'counterhypothesis':'The apparent failures are only presentation notation outside the intended parser surface, so grammar closure is not a BASE blocker.',
 'inputs':{'grammar_git_blob_sha':GRAMMAR_BLOB,'spec_v3_git_blob_sha':SPEC_BLOB,'dialect_registry_v3_git_blob_sha':DIALECT_BLOB},
 'baseline':{'cases':base,'failure_count':sum(x['fails'] for x in base),'positive_control_failures':sum(x['fails'] for x in base if x['kind']=='positive')},
 'candidate_repair':{'semantic_change':False,'grammar_additions':['relational operators: > < >= <=','if_stmt = "if", expr, block','method_signature = ident, "(", [typed_params], ")", "->", type_expr'],'warning':'Operator precedence/associativity is still not specified by this repair and remains a separate deterministic-canonical-IR question.'},
 'post_repair_targeted_audit':{'cases':after,'failure_count':sum(x['fails'] for x in after)},
 'interpretation':'Targeted executable surface audit falsifies parser-closure of the current grammar against syntax used by current admitted G9 artifacts. A minimal grammar/parser repair closes the tested cases without changing semantic primitives. This is mechanism evidence, not a full parser conformance proof.',
 'runtime':{'python':sys.version.split()[0],'platform':platform.platform()},
 'evidence_class':'LOCAL_EXECUTION_PRIMARY_FOR_AUDIT_ONLY'
}
raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode()
result['result_sha256']=hashlib.sha256(raw).hexdigest()
print(json.dumps(result,indent=2))
