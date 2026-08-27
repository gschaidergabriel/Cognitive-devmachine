import numpy as np, json, hashlib

SEEDS=50
W_A0=0.8
W_B0=0.2

def exp1():
    steps=400; eta=0.03; rows=[]
    for seed in range(SEEDS):
        rng=np.random.default_rng(seed)
        x=rng.normal(size=steps); y=x.copy()
        base=np.mean((W_A0*x+W_B0*x-y)**2)
        frozen=(W_B0*x-y)**2
        wB=W_B0; ae=[]
        for t in range(steps):
            pred=wB*x[t]; e=pred-y[t]; ae.append(e*e)
            wB -= eta*2*e*x[t]
        perm=rng.permutation(steps); wBs=W_B0; se=[]
        for t in range(steps):
            pred=wBs*x[t]; e=pred-y[t]; se.append(e*e)
            credit_target=y[perm[t]]; ce=pred-credit_target
            wBs -= eta*2*ce*x[t]
        mech_rescue=np.mean((W_A0*x[-100:]+wB*x[-100:]-y[-100:])**2)
        rollback=np.mean((W_A0*x[-100:]+W_B0*x[-100:]-y[-100:])**2)
        rows.append({
            'base_mse':base,
            'frozen_immediate_mse':float(np.mean(frozen[:25])),
            'frozen_delayed_mse':float(np.mean(frozen[-100:])),
            'adaptive_immediate_mse':float(np.mean(ae[:25])),
            'adaptive_delayed_mse':float(np.mean(ae[-100:])),
            'adaptive_final_wB':float(wB),
            'shuffled_delayed_mse':float(np.mean(se[-100:])),
            'shuffled_final_wB':float(wBs),
            'mechanism_only_rescue_mse':float(mech_rescue),
            'state_rollback_rescue_mse':float(rollback),
        })
    keys=rows[0].keys(); s={}
    for k in keys:
        a=np.array([r[k] for r in rows]); s[k]={'mean':float(a.mean()),'sd':float(a.std(ddof=1))}
    s['adaptation_recovery_fraction']={'mean':float(np.mean([(r['frozen_delayed_mse']-r['adaptive_delayed_mse'])/r['frozen_delayed_mse'] for r in rows]))}
    s['rescue_sign_flip_fraction']={'mean':float(np.mean([r['mechanism_only_rescue_mse'] > r['adaptive_delayed_mse'] for r in rows]))}
    return {'design':{'seeds':SEEDS,'steps':steps,'eta':eta,'baseline_weights':{'A':W_A0,'B':W_B0}},'summary':s}

def exp2():
    eta=0.01; steps=5000; ps=[1.0,.5,.25,.1]; out={}
    for p in ps:
        rows=[]
        for seed in range(SEEDS):
            rng=np.random.default_rng(seed+1000); wB=W_B0
            for _ in range(steps):
                x=float(rng.normal()); y=x; lesion=(rng.random()<p); a=0.0 if lesion else W_A0
                e=(a+wB)*x-y; wB -= eta*2*e*x
            xt=rng.normal(size=10000)
            lesion_mse=float(np.mean((wB*xt-xt)**2))
            intact_mse=float(np.mean(((W_A0+wB)*xt-xt)**2))
            rows.append((wB,lesion_mse,intact_mse))
        a=np.array(rows)
        out[str(p)]={
            'final_wB_mean':float(a[:,0].mean()),'final_wB_sd':float(a[:,0].std(ddof=1)),
            'lesion_state_mse_mean':float(a[:,1].mean()),'intact_state_mse_mean':float(a[:,2].mean())}
    return {'design':{'seeds':SEEDS,'steps':steps,'eta':eta,'lesion_duty_cycles':ps},'results':out}

result={'experiment_id':'EXP-SPAWN-EM-ADAPTIVE-LESION-001','exp1_adaptation_and_rescue':exp1(),'exp2_intervention_duty_cycle':exp2()}
print(json.dumps(result,sort_keys=True,indent=2))
