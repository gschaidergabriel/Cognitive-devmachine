#!/usr/bin/env python3
import json, time

CASES=20000

class NaiveTable:
    def __init__(self):
        self.slots={}
        self.free=[]
    def alloc(self, typ, value):
        slot=self.free.pop() if self.free else len(self.slots)
        self.slots[slot]=(typ,value)
        return slot
    def drop(self, slot):
        self.slots.pop(slot, None)
        self.free.append(slot)
    def resolve(self, slot):
        return self.slots.get(slot)
    def capability_allows(self, capability_designates_slot, supplied_slot):
        return capability_designates_slot == supplied_slot and self.resolve(supplied_slot) is not None

class HardenedTable:
    def __init__(self):
        self.slots={}
        self.free=[]
        self.generation={}
        self.call_epoch=0
    def alloc(self, typ, value, instance="host0", mode="OWN"):
        slot=self.free.pop() if self.free else len(self.generation)
        gen=self.generation.get(slot,0)+1
        self.generation[slot]=gen
        self.slots[slot]=(gen,typ,value)
        return {"resource_type":typ,"instance":instance,"slot":slot,"generation":gen,"mode":mode,"borrow_epoch":None}
    def identity(self,h):
        return (h["resource_type"],h["instance"],h["slot"],h["generation"],h["mode"])
    def borrow(self, own):
        h=dict(own); h["mode"]="BORROW"; h["borrow_epoch"]=self.call_epoch
        return h
    def next_call(self):
        self.call_epoch += 1
    def drop(self,h):
        if h["mode"]!="OWN": return False
        cur=self.slots.get(h["slot"])
        if not cur or cur[0]!=h["generation"] or cur[1]!=h["resource_type"]: return False
        self.slots.pop(h["slot"],None); self.free.append(h["slot"]); return True
    def resolve(self,h):
        cur=self.slots.get(h["slot"])
        if not cur: return None
        if cur[0]!=h["generation"] or cur[1]!=h["resource_type"]: return None
        if h["mode"]=="BORROW" and h["borrow_epoch"]!=self.call_epoch: return None
        return cur[2]
    def capability_allows(self, capability_designates_identity, supplied_handle):
        return capability_designates_identity == self.identity(supplied_handle) and self.resolve(supplied_handle) is not None

def main():
    t0=time.perf_counter()
    naive_stale=naive_cross=naive_borrow=naive_stale_cap=0
    hard_stale=hard_cross=hard_borrow=hard_stale_cap=hard_valid=0

    for i in range(CASES):
        n=NaiveTable()
        old=n.alloc("File",f"old-{i}")
        naive_cap_designates=old
        n.drop(old)
        new=n.alloc("File" if i%2==0 else "Socket",f"new-{i}")
        if n.resolve(old) is not None:
            naive_stale += 1
        if n.capability_allows(naive_cap_designates, old):
            naive_stale_cap += 1
        if i%2==1 and n.resolve(old) is not None:
            naive_cross += 1
        if n.resolve(new) is not None:
            naive_borrow += 1

        h=HardenedTable()
        own=h.alloc("File",f"old-{i}")
        hard_cap_designates=h.identity(own)
        borrowed=h.borrow(own)
        if h.resolve(borrowed)==f"old-{i}":
            hard_valid += 1
        h.next_call()
        if h.resolve(borrowed) is not None:
            hard_borrow += 1
        h.drop(own)
        newh=h.alloc("File" if i%2==0 else "Socket",f"new-{i}")
        if h.resolve(own) is not None:
            hard_stale += 1
        if h.capability_allows(hard_cap_designates, own):
            hard_stale_cap += 1
        fake=dict(own); fake["resource_type"]="Socket"
        if h.resolve(fake) is not None:
            hard_cross += 1
        if h.resolve(newh)==f"new-{i}":
            hard_valid += 1

    result={
      "cases":CASES,
      "naive_slot_only":{
        "stale_handle_accepts":naive_stale,
        "stale_capability_resource_alias_accepts":naive_stale_cap,
        "cross_type_stale_accepts":naive_cross,
        "borrow_after_return_accepts":naive_borrow
      },
      "typed_generation_lifetime":{
        "stale_handle_accepts":hard_stale,
        "stale_capability_resource_alias_accepts":hard_stale_cap,
        "cross_type_stale_accepts":hard_cross,
        "borrow_after_return_accepts":hard_borrow,
        "valid_operation_accepts":hard_valid
      },
      "elapsed_seconds":time.perf_counter()-t0
    }
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
