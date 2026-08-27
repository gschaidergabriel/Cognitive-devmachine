#!/usr/bin/env python3
"""Reproduce the SPAWN loop decision lowering discriminator.
Research proxy only: this is not the production ClayCode parser/compiler or frozen FRANK policy.
"""
import ctypes, random, subprocess, tempfile
from pathlib import Path

D={"CONTINUE":0,"HALT_CANDIDATE_CONVERGED":1,"ROUTE":2,"ESCALATE_STALLED":3,"ABORT_DIVERGING":4,"ROLLBACK":5}

def oracle(r):
    if r["mixed_epoch"]: return D["ROUTE"]
    if r["recurrence_count"] >= r["recurrence_budget"]: return D["ESCALATE_STALLED"] if r["residual_pressure"] > .35 else D["HALT_CANDIDATE_CONVERGED"]
    if r["overthinking_indicator"]: return D["ROLLBACK"]
    if r["diverging_indicator"] or (r["step_norm_current"] > r["step_norm_previous"]*1.2 and r["second_order_step_delta"] > .10): return D["ABORT_DIVERGING"]
    if r["residual_pressure"] <= .10 and r["step_norm_current"] <= .05 and abs(r["second_order_step_delta"]) <= .03: return D["HALT_CANDIDATE_CONVERGED"]
    if r["state_capacity_saturation"] >= .95 and r["residual_pressure"] > .20: return D["ROUTE"]
    if r["stagnation_indicator"] and r["residual_pressure"] > .20: return D["ESCALATE_STALLED"]
    return D["CONTINUE"]

C=r'''#include <math.h>
int decide(int me,int rc,int rb,double rp,double sc,double sp,double so,double cs,int st,int ov,int dv){
 if(me)return 2; if(rc>=rb)return rp>.35?3:1; if(ov)return 5;
 if(dv||(sc>sp*1.2&&so>.10))return 4;
 if(rp<=.10&&sc<=.05&&fabs(so)<=.03)return 1;
 if(cs>=.95&&rp>.20)return 2; if(st&&rp>.20)return 3; return 0;
}'''

def case(rng):
    return {"mixed_epoch":rng.random()<.02,"recurrence_count":rng.randint(0,40),"recurrence_budget":rng.randint(1,32),"residual_pressure":rng.random(),"step_norm_current":rng.random()*2,"step_norm_previous":rng.random()*2,"second_order_step_delta":rng.uniform(-1,1),"state_capacity_saturation":rng.random(),"stagnation_indicator":rng.random()<.10,"overthinking_indicator":rng.random()<.05,"diverging_indicator":rng.random()<.05}

def main(n=100000,seed=202608091743):
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); (td/'x.c').write_text(C); subprocess.run(['gcc','-O2','-fPIC','-shared',str(td/'x.c'),'-o',str(td/'x.so'),'-lm'],check=True)
        f=ctypes.CDLL(str(td/'x.so')).decide; f.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_int,ctypes.c_int,ctypes.c_int]; f.restype=ctypes.c_int
        rng=random.Random(seed); mismatch=0
        for _ in range(n):
            r=case(rng); got=f(int(r['mixed_epoch']),r['recurrence_count'],r['recurrence_budget'],r['residual_pressure'],r['step_norm_current'],r['step_norm_previous'],r['second_order_step_delta'],r['state_capacity_saturation'],int(r['stagnation_indicator']),int(r['overthinking_indicator']),int(r['diverging_indicator'])); mismatch += got != oracle(r)
        print({'cases':n,'mismatches':mismatch,'evidence_class':'LOCAL_REPRODUCER_NOT_TARGET_UBUNTU_ACCEPTANCE'})

if __name__=='__main__': main()
