import json, random, struct, subprocess, tempfile, pathlib, hashlib, platform, time, math

SEED = 202608091713
N_INT = 20000
N_FLOAT = 50000
rng = random.Random(SEED)

int_lexemes=[]
for _ in range(N_INT):
    bits=rng.randrange(0,257)
    if bits==0:
        n=0
    else:
        n=rng.getrandbits(bits)
    if rng.randrange(2): n=-n
    int_lexemes.append(str(n))
int_lexemes += [str(x) for x in [-(2**255), -(2**63), -(2**53+1), -2**53, -1, 0, 1, 2**53, 2**53+1, 2**63-1, 2**64-1, 2**127-1, 2**255-1]]

float_lexemes=[]
while len(float_lexemes)<N_FLOAT:
    sign='-' if rng.randrange(2) else ''
    nd=rng.randrange(1,18)
    digits=''.join(str(rng.randrange(10)) for _ in range(nd))
    if all(c=='0' for c in digits): digits='1'+digits[1:]
    split=rng.randrange(0,nd+1)
    if split==0: mant='0.'+digits
    elif split==nd: mant=digits
    else: mant=digits[:split]+'.'+digits[split:]
    exp=rng.randrange(-340,309)
    s=f"{sign}{mant}e{exp}"
    try: f=float(s)
    except Exception: continue
    if math.isfinite(f): float_lexemes.append(s)
float_lexemes += ['0','-0','0.0','-0.0','5e-324','2.2250738585072014e-308','2.225073858507201e-308','1.7976931348623157e308','9007199254740993.0','0.1000000000000000055511151231257827021181583404541015625']

def py_f64_bits(s):
    return struct.pack('>d', float(s)).hex()

def py_json_num(s):
    return json.dumps(float(s), allow_nan=False, separators=(',',':'))

payload={'ints':int_lexemes,'floats':float_lexemes}
js=r'''
const fs=require('fs');
const p=JSON.parse(fs.readFileSync(0,'utf8'));
function f64bits(s){ const x=Number(s); const b=Buffer.allocUnsafe(8); b.writeDoubleBE(x,0); return b.toString('hex'); }
const ints=p.ints.map(s=>{ const exact='I:'+BigInt(s).toString(); const n=Number(s); let rt=null; if (Number.isFinite(n)) rt=BigInt(Math.trunc(n)).toString(); return {exact, number_roundtrip:rt}; });
const floats=p.floats.map(s=>({bits:f64bits(s), json:JSON.stringify(Number(s))}));
process.stdout.write(JSON.stringify({ints,floats}));
'''
start=time.perf_counter()
cp=subprocess.run(['node','-e',js],input=json.dumps(payload),text=True,capture_output=True,check=True)
node=json.loads(cp.stdout)
elapsed=time.perf_counter()-start

int_exact_mismatches=0
int_number_mismatches=0
int_number_finite=0
for s,r in zip(int_lexemes,node['ints']):
    py='I:'+str(int(s))
    if py!=r['exact']: int_exact_mismatches+=1
    if r['number_roundtrip'] is not None:
        int_number_finite+=1
        if int(r['number_roundtrip'])!=int(s): int_number_mismatches+=1

float_bit_mismatches=0
float_json_mismatches=0
float_json_examples=[]
for s,r in zip(float_lexemes,node['floats']):
    pb=py_f64_bits(s)
    if pb!=r['bits']: float_bit_mismatches+=1
    pj=py_json_num(s)
    if pj!=r['json']:
        float_json_mismatches+=1
        if len(float_json_examples)<10: float_json_examples.append({'source':s,'python_json':pj,'node_json':r['json'],'bits':pb})

edges={s:{'python_bits':py_f64_bits(s),'node_bits':r['bits'],'python_json':py_json_num(s),'node_json':r['json']} for s,r in zip(float_lexemes[-10:],node['floats'][-10:])}
src=pathlib.Path(__file__).read_bytes()
result={
 'experiment':'EXP-CC-TYPED-NUMERIC-CANON-20260809-01','seed':SEED,'classification':'LOCAL_CROSS_RUNTIME_PROXY_NOT_TARGET_UBUNTU',
 'environment':{'python':platform.python_version(),'node':subprocess.check_output(['node','--version'],text=True).strip(),'platform':platform.platform()},
 'corpus':{'int_cases':len(int_lexemes),'float_cases':len(float_lexemes),'payload_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()},
 'typed_int_token':{'scheme':'I:<canonical base10 integer>','cross_runtime_mismatches':int_exact_mismatches},
 'naive_int_to_js_number':{'finite_cases':int_number_finite,'exactness_mismatches':int_number_mismatches,'mismatch_rate':int_number_mismatches/int_number_finite if int_number_finite else None},
 'typed_f64_token':{'scheme':'F64:<IEEE-754 binary64 big-endian bits>','cross_runtime_parse_bit_mismatches':float_bit_mismatches},
 'host_json_float_text':{'cross_runtime_text_mismatches':float_json_mismatches,'mismatch_rate':float_json_mismatches/len(float_lexemes),'examples':float_json_examples},
 'edge_cases':edges,'elapsed_seconds':elapsed,'source_sha256':hashlib.sha256(src).hexdigest(),
 'interpretation_boundary':['This tests decimal-literal parse identity between local CPython and Node/V8, not all ClayCode targets.','F64 bit identity for parsed literals does not prove cross-backend arithmetic determinism or NaN-payload preservation.','No production ClayCode parser/compiler/runtime or Andreas target Ubuntu host was executed.']
}
print(json.dumps(result,indent=2,sort_keys=True))
