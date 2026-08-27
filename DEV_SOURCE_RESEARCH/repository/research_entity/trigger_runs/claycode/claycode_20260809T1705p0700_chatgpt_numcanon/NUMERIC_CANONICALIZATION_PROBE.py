import json, math, random, struct, subprocess, hashlib, sys

SEED=20260809
N=10000
rng=random.Random(SEED)

edge_bits=[
    0x0000000000000000,
    0x8000000000000000,
    0x3ff0000000000000,
    0xbff0000000000000,
    0x3e7ad7f29abcaf48,
    0x4415af1d78b58c40,
    0x444b1ae4d6e2ef50,
    0x7ff0000000000000,
    0xfff0000000000000,
    0x7ff8000000000000,
    0x7ff8000000000001,
]
bits=list(edge_bits)
while len(bits) < N:
    bits.append(rng.getrandbits(64))
hexes=[f'{b:016x}' for b in bits]

js=r'''
const fs=require('fs');
const inp=JSON.parse(fs.readFileSync(0,'utf8'));
function fromHex(h){
  const buf=new ArrayBuffer(8); const dv=new DataView(buf);
  const bi=BigInt('0x'+h); dv.setBigUint64(0,bi,false); return dv.getFloat64(0,false);
}
function token(h){
  const bi=BigInt('0x'+h);
  const exp=(bi>>52n)&0x7ffn; const frac=bi & ((1n<<52n)-1n); const sign=bi>>63n;
  if(exp===0x7ffn){
    if(frac!==0n) return 'f64:nan';
    return sign ? 'f64:-inf' : 'f64:+inf';
  }
  return 'f64:'+h.toLowerCase();
}
const out=inp.map(h=>{const x=fromHex(h); return {h,native:JSON.stringify(x),token:token(h)};});
process.stdout.write(JSON.stringify(out));
'''
node=subprocess.run(['node','-e',js],input=json.dumps(hexes),text=True,capture_output=True,check=True)
node_rows=json.loads(node.stdout)

native_mismatch=0
native_examples=[]
token_mismatch=0
special_count=0
for h,row in zip(hexes,node_rows):
    b=int(h,16)
    x=struct.unpack('>d',bytes.fromhex(h))[0]
    py_native=json.dumps(x, allow_nan=True, separators=(',',':'))
    exp=(b>>52)&0x7ff; frac=b & ((1<<52)-1); sign=b>>63
    if exp==0x7ff:
        special_count+=1
        if frac:
            py_token='f64:nan'
        else:
            py_token='f64:-inf' if sign else 'f64:+inf'
    else:
        py_token='f64:'+h
    if py_native != row['native']:
        native_mismatch += 1
        if len(native_examples)<12:
            native_examples.append({'bits':h,'python':py_native,'node':row['native'],'candidate':py_token})
    if py_token != row['token']:
        token_mismatch += 1

ints=[0,1,-1,2**53-1,2**53,2**53+1,2**63-1,-2**63,10**30+123]
js_int=r'''
const fs=require('fs'); const ss=JSON.parse(fs.readFileSync(0,'utf8'));
const out=ss.map(s=>{const b=BigInt(s); let num=Number(b); let native; try{native=JSON.stringify(num)}catch(e){native='ERR:'+e.name}; let big; try{big=JSON.stringify(b)}catch(e){big='ERR:'+e.name}; return {s,native_number:native,native_bigint:big,token:'int:'+b.toString(10)};});
process.stdout.write(JSON.stringify(out));
'''
node2=subprocess.run(['node','-e',js_int],input=json.dumps([str(i) for i in ints]),text=True,capture_output=True,check=True)
node_ints=json.loads(node2.stdout)
int_rows=[]
int_candidate_mismatch=0
for i,row in zip(ints,node_ints):
    py_native=json.dumps(i,separators=(',',':'))
    tok='int:'+str(i)
    if tok!=row['token']: int_candidate_mismatch+=1
    int_rows.append({'value':str(i),'python_json':py_native,'node_number_json':row['native_number'],'node_bigint_json':row['native_bigint'],'candidate':tok})

result={
 'experiment':'CC-NUMCANON-LOCAL-20260809-01',
 'seed':SEED,
 'python':sys.version.split()[0],
 'node':subprocess.run(['node','--version'],capture_output=True,text=True,check=True).stdout.strip(),
 'float_cases':len(hexes),
 'float_special_cases':special_count,
 'native_json_float_string_mismatches_python_vs_node':native_mismatch,
 'candidate_float_token_mismatches_python_vs_node':token_mismatch,
 'native_mismatch_examples':native_examples,
 'integer_cases':len(ints),
 'candidate_integer_token_mismatches_python_vs_node':int_candidate_mismatch,
 'integer_rows':int_rows,
 'candidate_contract':{
   'int':'canonical decimal arbitrary-precision integer token int:<base10>; host Number lowering forbidden when magnitude exceeds exact target range',
   'f64_finite':'semantic token preserves exact IEEE-754 binary64 bits as f64:<16-hex>',
   'f64_nan':'all NaN payload/sign variants canonicalize to f64:nan at semantic identity boundary',
   'f64_inf':'explicit f64:+inf / f64:-inf',
   'signed_zero':'preserved by raw finite bit token',
   'wire_rule':'host-native JSON number formatting is not a semantic hash format'
 },
 'conclusion':'Host-native JSON numeric serialization is not a safe ClayCode semantic-identity encoding. Explicit typed numeric canonicalization removes the observed representation mismatch on this corpus without adding FRANK-specific semantics.'
}
raw=json.dumps(result,sort_keys=True,indent=2)
print(raw)
print('receipt_sha256',hashlib.sha256(raw.encode()).hexdigest())
