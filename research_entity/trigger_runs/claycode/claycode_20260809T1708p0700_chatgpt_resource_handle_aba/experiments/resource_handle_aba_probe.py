import random, json, hashlib, platform
from dataclasses import dataclass

SEED=20260809
N=100000

@dataclass(frozen=True)
class GenHandle:
    slot:int
    gen:int

class NaiveTable:
    def __init__(self): self.slots={}; self.free=[]; self.next=0
    def open(self, resource):
        if self.free: s=self.free.pop(0)
        else: s=self.next; self.next+=1
        self.slots[s]=resource; return s
    def close(self,h):
        if h in self.slots: del self.slots[h]; self.free.append(h); self.free.sort()
    def use(self,h): return self.slots.get(h)

class GenTable:
    def __init__(self): self.slots={}; self.gens={}; self.free=[]; self.next=0
    def open(self, resource):
        if self.free: s=self.free.pop(0)
        else: s=self.next; self.next+=1
        g=self.gens.get(s,0)+1; self.gens[s]=g; self.slots[s]=(g,resource); return GenHandle(s,g)
    def close(self,h):
        cur=self.slots.get(h.slot)
        if cur and cur[0]==h.gen:
            del self.slots[h.slot]; self.free.append(h.slot); self.free.sort()
    def use(self,h):
        cur=self.slots.get(h.slot)
        return cur[1] if cur and cur[0]==h.gen else None

def one_case(extra_opens=0):
    # stale handle to A, close it, reuse same slot for B, then stale use.
    nt=NaiveTable(); gt=GenTable()
    nh=nt.open('A'); gh=gt.open('A')
    nt.close(nh); gt.close(gh)
    # Optional churn to vary allocator state; first reopen necessarily reuses freed slot.
    nb=nt.open('B'); gb=gt.open('B')
    for i in range(extra_opens):
        nt.open(f'X{i}'); gt.open(f'X{i}')
    return {
      'naive_stale_observed': nt.use(nh),
      'gen_stale_observed': gt.use(gh),
      'naive_new_handle': nb,
      'gen_new_handle': {'slot':gb.slot,'gen':gb.gen},
      'old_gen_handle': {'slot':gh.slot,'gen':gh.gen}
    }

# Exhaustive compact event family: resource label B/C x churn count 0..7
ex=[]
for b in ['B','C']:
    for churn in range(8):
        nt=NaiveTable(); gt=GenTable(); nh=nt.open('A'); gh=gt.open('A'); nt.close(nh); gt.close(gh)
        nt.open(b); gt.open(b)
        for i in range(churn): nt.open(f'X{i}'); gt.open(f'X{i}')
        ex.append((nt.use(nh), gt.use(gh)))

rng=random.Random(SEED)
naive_unsafe=0; gen_unsafe=0
for _ in range(N):
    nt=NaiveTable(); gt=GenTable()
    old_label=f'A{rng.randrange(1000)}'; new_label=f'B{rng.randrange(1000)}'
    nh=nt.open(old_label); gh=gt.open(old_label)
    # random opens then close old; free-list policy guarantees later eventual reuse
    for i in range(rng.randrange(4)): nt.open(f'pre{i}'); gt.open(f'pre{i}')
    nt.close(nh); gt.close(gh)
    # force one allocation so freed slot may be reused; same allocator policy in both arms
    nt.open(new_label); gt.open(new_label)
    # random additional churn and stale read
    for i in range(rng.randrange(5)): nt.open(f'post{i}'); gt.open(f'post{i}')
    if nt.use(nh) is not None: naive_unsafe += 1
    if gt.use(gh) is not None: gen_unsafe += 1

source=open(__file__,'rb').read()
result={
  'experiment':'EXP-CC-RESOURCE-HANDLE-ABA-20260809-01',
  'seed':SEED,
  'cases':N,
  'exhaustive_cases':len(ex),
  'exhaustive_naive_unsafe':sum(a is not None for a,b in ex),
  'exhaustive_generation_unsafe':sum(b is not None for a,b in ex),
  'fuzz_naive_unsafe':naive_unsafe,
  'fuzz_generation_unsafe':gen_unsafe,
  'python':platform.python_version(),
  'platform':platform.platform(),
  'source_sha256':hashlib.sha256(source).hexdigest(),
  'example':one_case(3)
}
print(json.dumps(result, indent=2, sort_keys=True))
