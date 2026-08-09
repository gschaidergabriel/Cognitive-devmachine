import hashlib, json, random, re, subprocess, sys, copy

GRAMMAR_SHA='ec2f17077333955cfdabe6c64868d597e7e734e3'
PARSER_VERSION='cc-chain-probe-parser-v0.1'
TYPECHECK_VERSION='cc-chain-probe-type-v0.1'
LOWERING_VERSION='cc-chain-probe-lower-v0.1'
SEED=20260809

def h_bytes(b): return hashlib.sha256(b).hexdigest()
def canon(obj): return json.dumps(obj, sort_keys=True, separators=(',',':')).encode()
def h_obj(obj): return h_bytes(canon(obj))

def parse_source(src):
    m_mod=re.search(r'\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)',src)
    m_metric=re.search(r'\bmetric\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+)\s*\+\s*(-?\d+)',src)
    if not (m_mod and m_metric): raise ValueError('subset parse failed')
    return {'module':m_mod.group(1),'metric':{'name':m_metric.group(1),'op':'add','lhs':int(m_metric.group(2)),'rhs':int(m_metric.group(3))}}

def typed_ir(ast):
    return {'kind':'Program','module':ast['module'],'metric':{**ast['metric'],'lhs_type':'Int','rhs_type':'Int','result_type':'Int'}}

def lower_good(tir):
    m=tir['metric']; return f"print({m['lhs']} + {m['rhs']})\n"

def lower_bad(tir):
    m=tir['metric']; return f"print({m['lhs']} - {m['rhs']})\n"

def execute(code):
    p=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=3)
    return {'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'stdout_hash':h_bytes(p.stdout.encode())}

def build_chain(src,bad_lower=False,execute_artifact=True):
    source_hash=h_bytes(src.encode()); ast=parse_source(src); ast_hash=h_obj(ast); tir=typed_ir(ast); tir_hash=h_obj(tir); sem=tir; sem_hash=h_obj(sem)
    code=(lower_bad if bad_lower else lower_good)(tir); artifact_hash=h_bytes(code.encode())
    ex=execute(code) if execute_artifact else {'exit_code':0,'stdout':'','stderr':'','stdout_hash':h_bytes(b'')}
    contract={'source_hash':source_hash,'grammar_sha':GRAMMAR_SHA,'parser_version':PARSER_VERSION,'typecheck_version':TYPECHECK_VERSION,'semantic_hash':sem_hash,'lowering_version':LOWERING_VERSION,'artifact_hash':artifact_hash}
    return {'source':{'bytes':src,'source_hash':source_hash},'parse':{'parent_source_hash':source_hash,'grammar_sha':GRAMMAR_SHA,'parser_version':PARSER_VERSION,'ast':ast,'ast_hash':ast_hash},'typed':{'parent_ast_hash':ast_hash,'typecheck_version':TYPECHECK_VERSION,'typed_ir':tir,'typed_ir_hash':tir_hash},'semantic':{'parent_typed_ir_hash':tir_hash,'semantic':sem,'semantic_hash':sem_hash},'lower':{'parent_semantic_hash':sem_hash,'lowering_version':LOWERING_VERSION,'artifact':code,'artifact_hash':artifact_hash},'execution':{'parent_artifact_hash':artifact_hash,**ex},'contract_hash':h_obj(contract),'contract':contract}

def validate_chain(c):
    errors=[]; sh=h_bytes(c['source']['bytes'].encode())
    if c['source']['source_hash']!=sh: errors.append('source_hash')
    if c['parse']['parent_source_hash']!=sh: errors.append('parse_parent_source')
    if c['parse']['grammar_sha']!=GRAMMAR_SHA: errors.append('grammar_sha')
    if c['parse']['parser_version']!=PARSER_VERSION: errors.append('parser_version')
    ah=h_obj(c['parse']['ast'])
    if c['parse']['ast_hash']!=ah: errors.append('ast_hash')
    if c['typed']['parent_ast_hash']!=ah: errors.append('typed_parent_ast')
    if c['typed']['typecheck_version']!=TYPECHECK_VERSION: errors.append('typecheck_version')
    th=h_obj(c['typed']['typed_ir'])
    if c['typed']['typed_ir_hash']!=th: errors.append('typed_ir_hash')
    if c['semantic']['parent_typed_ir_hash']!=th: errors.append('semantic_parent_typed')
    seh=h_obj(c['semantic']['semantic'])
    if c['semantic']['semantic_hash']!=seh: errors.append('semantic_hash')
    if c['lower']['parent_semantic_hash']!=seh: errors.append('lower_parent_semantic')
    if c['lower']['lowering_version']!=LOWERING_VERSION: errors.append('lowering_version')
    ar=h_bytes(c['lower']['artifact'].encode())
    if c['lower']['artifact_hash']!=ar: errors.append('artifact_hash')
    if c['execution']['parent_artifact_hash']!=ar: errors.append('exec_parent_artifact')
    contract={'source_hash':sh,'grammar_sha':GRAMMAR_SHA,'parser_version':PARSER_VERSION,'typecheck_version':TYPECHECK_VERSION,'semantic_hash':seh,'lowering_version':LOWERING_VERSION,'artifact_hash':ar}
    if c['contract']!=contract: errors.append('contract_fields')
    if c['contract_hash']!=h_obj(contract): errors.append('contract_hash')
    return errors

MUTATORS=[('source_hash',lambda c:c['source'].__setitem__('source_hash','0'*64)),('parse_parent',lambda c:c['parse'].__setitem__('parent_source_hash','1'*64)),('grammar_sha',lambda c:c['parse'].__setitem__('grammar_sha','2'*40)),('parser_version',lambda c:c['parse'].__setitem__('parser_version','stale-parser')),('ast_payload',lambda c:c['parse']['ast']['metric'].__setitem__('lhs',999)),('ast_hash',lambda c:c['parse'].__setitem__('ast_hash','3'*64)),('typed_parent',lambda c:c['typed'].__setitem__('parent_ast_hash','4'*64)),('typed_payload',lambda c:c['typed']['typed_ir']['metric'].__setitem__('result_type','Float')),('typed_hash',lambda c:c['typed'].__setitem__('typed_ir_hash','5'*64)),('semantic_parent',lambda c:c['semantic'].__setitem__('parent_typed_ir_hash','6'*64)),('semantic_payload',lambda c:c['semantic']['semantic']['metric'].__setitem__('op','sub')),('semantic_hash',lambda c:c['semantic'].__setitem__('semantic_hash','7'*64)),('lower_parent',lambda c:c['lower'].__setitem__('parent_semantic_hash','8'*64)),('lowering_version',lambda c:c['lower'].__setitem__('lowering_version','stale-lower')),('artifact_payload',lambda c:c['lower'].__setitem__('artifact','print(999)\n')),('artifact_hash',lambda c:c['lower'].__setitem__('artifact_hash','9'*64)),('exec_parent',lambda c:c['execution'].__setitem__('parent_artifact_hash','a'*64)),('contract_hash',lambda c:c.__setitem__('contract_hash','b'*64))]

rnd=random.Random(SEED); base=build_chain('module probe\nmetric answer = 7 + 5\n'); variant=build_chain('module    probe\n\nmetric   answer=7+5\n',execute_artifact=False)
identity={'source_hash_equal':base['source']['source_hash']==variant['source']['source_hash'],'ast_hash_equal':base['parse']['ast_hash']==variant['parse']['ast_hash'],'typed_ir_hash_equal':base['typed']['typed_ir_hash']==variant['typed']['typed_ir_hash'],'semantic_hash_equal':base['semantic']['semantic_hash']==variant['semantic']['semantic_hash'],'artifact_hash_equal':base['lower']['artifact_hash']==variant['lower']['artifact_hash'],'contract_hash_equal':base['contract_hash']==variant['contract_hash']}
N=50000; detected=0
for _ in range(N):
    c=copy.deepcopy(base); _,fn=rnd.choice(MUTATORS); fn(c); detected+=bool(validate_chain(c))
CLEAN_N=10000; clean_reject=0
for _ in range(CLEAN_N):
    s='module'+(' '*rnd.randint(1,5))+'probe\n'+('\n'*rnd.randint(0,2))+'metric'+(' '*rnd.randint(1,5))+'answer'+(' '*rnd.randint(0,3))+'='+(' '*rnd.randint(0,3))+str(rnd.randint(-99,99))+(' '*rnd.randint(0,3))+'+'+(' '*rnd.randint(0,3))+str(rnd.randint(-99,99))+'\n'
    try:
        c=build_chain(s,execute_artifact=False); clean_reject+=bool(validate_chain(c))
    except Exception: clean_reject+=1
BAD_N=10000; chain_pass_wrong=oracle_catches=oracle_misses=0
wrong=build_chain('module probe\nmetric answer = 7 + 5\n',bad_lower=True,execute_artifact=True)
for _ in range(BAD_N):
    a=rnd.randint(-1000,1000); b=rnd.randint(-1000,1000); c=build_chain(f'module probe\nmetric answer = {a} + {b}\n',bad_lower=True,execute_artifact=False); chain_pass_wrong+=not bool(validate_chain(c)); oracle_catches+=(a-b)!=(a+b); oracle_misses+=(a-b)==(a+b)
out={'experiment_id':'EXP-CC-CHAIN-SEMANTIC-GATE-20260809-01','seed':SEED,'identity_whitespace_variant':identity,'tamper_fuzz':{'cases':N,'detected':detected,'missed':N-detected},'clean_variants':{'cases':CLEAN_N,'false_rejects':clean_reject},'self_consistent_wrong_lowering':{'cases':BAD_N,'chain_integrity_passed':chain_pass_wrong,'semantic_oracle_catches':oracle_catches,'semantic_oracle_misses':oracle_misses,'executed_sample':{'chain_errors':validate_chain(wrong),'observed':int(wrong['execution']['stdout'].strip()),'expected':12,'artifact_hash':wrong['lower']['artifact_hash'],'exit_code':wrong['execution']['exit_code']}},'scope':'Local synthetic mechanism test; not production parser/compiler or target-host evidence.'}
print(json.dumps(out,indent=2,sort_keys=True))
