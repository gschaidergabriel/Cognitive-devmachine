#!/usr/bin/env python3
"""Synthetic discriminator for ClayCode capability authority + gate admission.
NOT production ClayCode and NOT Andreas target-host acceptance.
"""
from dataclasses import dataclass
import collections, hashlib, hmac, json, random, secrets

N=300000
SEED=0xC1A7C0DE
def H(s): return hashlib.sha256(s.encode()).hexdigest()

@dataclass(frozen=True)
class Cap:
    runtime:str; cid:str; kind:str; epoch:int; nonce:str

class Issuer:
    def __init__(self):
        self.runtime=secrets.token_hex(8); self.secret=secrets.token_bytes(32)
        self.epoch=1; self.reg={}; self.revoked=set()
    def sig(self,cid,kind,epoch):
        return hmac.new(self.secret,f"{self.runtime}|{cid}|{kind}|{epoch}".encode(),hashlib.sha256).hexdigest()
    def mint(self,kind):
        cid=secrets.token_hex(8); c=Cap(self.runtime,cid,kind,self.epoch,self.sig(cid,kind,self.epoch))
        self.reg[cid]=c; return c
    def ok(self,c,kind):
        return (isinstance(c,Cap) and c.runtime==self.runtime and self.reg.get(c.cid) is c
                and c.cid not in self.revoked and c.epoch==self.epoch and c.kind==kind
                and hmac.compare_digest(c.nonce,self.sig(c.cid,c.kind,c.epoch)))

def naive_cap(c,kind):
    if isinstance(c,str): return c==kind
    if isinstance(c,dict): return c.get("kind")==kind
    return isinstance(c,Cap) and c.kind==kind

EXPECT={"gate":"CC-WP-07-RUNTIME-ABI-FFI","head":H("head-A"),"runtime":H("runtime"),
        "test":H("test"),"workflow":H("workflow"),"scope":"ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"}

def strict_gate(e):
    return (e["defined"] and e["state"]=="completed" and e["conclusion"]=="success" and e["receipt"]
            and e["gate"]==EXPECT["gate"] and e["head"]==EXPECT["head"] and e["runtime"]==EXPECT["runtime"]
            and e["test"]==EXPECT["test"] and e["workflow"]==EXPECT["workflow"] and e["scope"]==EXPECT["scope"]
            and e["pass"] and e["negative"])

def naive_gate(e): return e.get("defined",False) and e.get("conclusion") in (None,"success")

def run():
    r=random.Random(SEED); issuer=Issuer(); other=Issuer()
    stale=issuer.mint("fs.read"); issuer.epoch+=1; good=issuer.mint("fs.read")
    revoked=issuer.mint("fs.read"); issuer.revoked.add(revoked.cid)
    foreign=other.mint("fs.read")
    copied=Cap(good.runtime,good.cid,good.kind,good.epoch,good.nonce)
    forged={"runtime":issuer.runtime,"cid":good.cid,"kind":"fs.read","epoch":issuer.epoch,"nonce":"00"}
    caps=[("good",good,True),("text","fs.read",False),("forged",forged,False),("foreign",foreign,False),
          ("stale",stale,False),("revoked",revoked,False),("copied",copied,False)]
    cc=collections.Counter()
    for _ in range(N):
        _,c,truth=r.choice(caps); s=issuer.ok(c,"fs.read"); n=naive_cap(c,"fs.read")
        cc["strict_false_accept"]+=s and not truth; cc["strict_false_reject"]+=(not s) and truth
        cc["naive_false_accept"]+=n and not truth; cc["naive_false_reject"]+=(not n) and truth; cc["cases"]+=1

    base={"defined":True,"state":"completed","conclusion":"success","receipt":True,**EXPECT,"pass":True,"negative":True}
    muts=[("valid",None,None,True),("defined","state","defined",False),("queued","state","queued",False),
          ("running","state","in_progress",False),("failure","conclusion","failure",False),("no_receipt","receipt",False,False),
          ("stale_head","head",H("old"),False),("runtime","runtime",H("other"),False),("test","test",H("other"),False),
          ("workflow","workflow",H("other"),False),("scope","scope","HOSTED_UBUNTU_CI_PROXY",False),
          ("test_fail","pass",False,False),("negative_fail","negative",False,False)]
    gc=collections.Counter()
    for _ in range(N):
        _,k,v,truth=r.choice(muts); e=dict(base)
        if k is not None: e[k]=v
        s=strict_gate(e); n=naive_gate(e)
        gc["strict_false_accept"]+=s and not truth; gc["strict_false_reject"]+=(not s) and truth
        gc["naive_false_accept"]+=n and not truth; gc["naive_false_reject"]+=(not n) and truth; gc["cases"]+=1
    return {"schema_version":"1.0","experiment":"capability+attested-gate synthetic discriminator",
            "evidence_class":"HOSTED_SYNTHETIC_PROXY_NOT_PRODUCTION_NOT_ANDREAS_TARGET_ACCEPTANCE",
            "seed":hex(SEED),"n_per_suite":N,"capability":dict(cc),"gate":dict(gc),
            "guard":"Constructed adversarial distribution; counts are discrimination sensitivity, not prevalence."}

if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
