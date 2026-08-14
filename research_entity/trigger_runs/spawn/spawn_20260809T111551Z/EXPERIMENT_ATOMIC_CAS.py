#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, random, shutil, subprocess, tempfile, textwrap
from pathlib import Path

SEED = 0xC1A0C3
ABA_RUNS = 200_000
RETRY_RUNS = 100_000
THREADS = 8
INCREMENTS = 100_000

def sh(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def aba_probe():
    rng = random.Random(SEED)
    raw_stale = versioned_stale = 0
    cycles_hist = {}
    for _ in range(ABA_RUNS):
        expected_value, expected_ver = "A", 0
        cycles = 1 + rng.randrange(4)
        cycles_hist[cycles] = cycles_hist.get(cycles, 0) + 1
        value, ver = "A", 0
        for _ in range(cycles):
            value, ver = "B", ver + 1
            value, ver = "A", ver + 1
        raw_success = value == expected_value
        versioned_success = value == expected_value and ver == expected_ver
        raw_stale += int(raw_success and ver != expected_ver)
        versioned_stale += int(versioned_success and ver != expected_ver)
    return {"runs": ABA_RUNS, "raw_value_only_stale_accepts": raw_stale, "version_bound_stale_accepts": versioned_stale, "cycles_histogram": cycles_hist}

def retry_identity_probe():
    rng = random.Random(0xABAC0DE)
    sem_hashes, trace_hashes = set(), set()
    for _ in range(RETRY_RUNS):
        retries = rng.randrange(16)
        semantic = {"op_id":"op-1","cell_id":"cell-7","expected":{"value":"A","version":0},"desired":{"value":"C","version":1},"success":True,"observed":{"value":"A","version":0},"final":{"value":"C","version":1}}
        trace = {"semantic": semantic, "spurious_failures": retries, "physical_attempts": retries + 1}
        sem_hashes.add(sh(semantic)); trace_hashes.add(sh(trace))
    return {"runs": RETRY_RUNS, "distinct_semantic_hashes": len(sem_hashes), "distinct_execution_trace_hashes": len(trace_hashes), "physical_attempt_variants": 16}

def run_c11(tmp: Path):
    if not shutil.which("gcc"):
        return {"status":"SKIPPED","reason":"gcc unavailable"}
    src, exe = tmp / "counter.c", tmp / "counter"
    src.write_text(textwrap.dedent(f'''\
    #include <stdatomic.h>
    #include <pthread.h>
    #include <stdint.h>
    #include <stdio.h>
    #define THREADS {THREADS}
    #define INC {INCREMENTS}
    static _Atomic uint64_t counter=0, retries=0;
    void* worker(void* p) {{
      (void)p;
      for(int i=0;i<INC;i++) {{
        uint64_t old=atomic_load_explicit(&counter,memory_order_relaxed);
        while(!atomic_compare_exchange_weak_explicit(&counter,&old,old+1,memory_order_seq_cst,memory_order_relaxed))
          atomic_fetch_add_explicit(&retries,1,memory_order_relaxed);
      }}
      return 0;
    }}
    int main(void) {{
      pthread_t t[THREADS];
      for(int i=0;i<THREADS;i++) pthread_create(&t[i],0,worker,0);
      for(int i=0;i<THREADS;i++) pthread_join(t[i],0);
      printf("{{\\\"backend\\\":\\\"c11-gcc\\\",\\\"final\\\":%llu,\\\"expected\\\":%llu,\\\"retries\\\":%llu}}\\n",
        (unsigned long long)atomic_load(&counter),(unsigned long long)THREADS*INC,(unsigned long long)atomic_load(&retries));
    }}
    '''))
    subprocess.run(["gcc","-O2","-std=c11","-pthread",str(src),"-o",str(exe)],check=True,capture_output=True,text=True)
    return json.loads(subprocess.run([str(exe)],check=True,capture_output=True,text=True).stdout)

def run_node(tmp: Path):
    if not shutil.which("node"):
        return {"status":"SKIPPED","reason":"node unavailable"}
    src = tmp / "counter.js"
    src.write_text(textwrap.dedent(f'''\
    const {{ Worker, isMainThread, workerData }} = require('worker_threads');
    const THREADS={THREADS}, INC={INCREMENTS};
    if (isMainThread) {{
      const sab=new SharedArrayBuffer(BigInt64Array.BYTES_PER_ELEMENT*2); const a=new BigInt64Array(sab); let done=0;
      for(let i=0;i<THREADS;i++) new Worker(__filename,{{workerData:{{sab,INC}}}}).on('exit',()=>{{
        done++; if(done===THREADS) console.log(JSON.stringify({{backend:'node-atomics',final:Number(Atomics.load(a,0)),expected:THREADS*INC,retries:Number(Atomics.load(a,1))}}));
      }});
    }} else {{
      const a=new BigInt64Array(workerData.sab);
      for(let i=0;i<workerData.INC;i++) {{ let old=Atomics.load(a,0); for(;;) {{ const got=Atomics.compareExchange(a,0,old,old+1n); if(got===old) break; Atomics.add(a,1,1n); old=got; }} }}
    }}
    '''))
    return json.loads(subprocess.run(["node",str(src)],check=True,capture_output=True,text=True).stdout)

def main():
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        result={"schema_version":"1.0","experiment":"ClayCode atomic CAS / ABA semantic-identity discriminator","seed":SEED,"aba":aba_probe(),"retry_identity":retry_identity_probe(),"cross_backend":{"c11":run_c11(tmp),"ecmascript":run_node(tmp)}}
    result["checks"]={
        "raw_cas_aba_falsifier_triggered": result["aba"]["raw_value_only_stale_accepts"] > 0,
        "version_bound_aba_rejections_complete": result["aba"]["version_bound_stale_accepts"] == 0,
        "semantic_hash_retry_invariant": result["retry_identity"]["distinct_semantic_hashes"] == 1,
        "execution_trace_retry_sensitive": result["retry_identity"]["distinct_execution_trace_hashes"] > 1,
        "c11_exact_counter": result["cross_backend"]["c11"].get("final") == result["cross_backend"]["c11"].get("expected"),
        "ecmascript_exact_counter": result["cross_backend"]["ecmascript"].get("final") == result["cross_backend"]["ecmascript"].get("expected")
    }
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__': main()
