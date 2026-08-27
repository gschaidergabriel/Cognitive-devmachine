import json, random, pathlib, importlib.util, sys
HERE=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location("rt", HERE/"generated_runtime.py")
rt=importlib.util.module_from_spec(spec); sys.modules["rt"]=rt; spec.loader.exec_module(rt)
LABEL_ACTION={"CONVERGING_FIXED_POINT":"HALT","PRODUCTIVE_LIMIT_CYCLE":"CONTINUE","STALLED":"ESCALATE","DIVERGING_OR_OVERTHINKING":"ESCALATE","CHAOTIC_OR_UNCLASSIFIED":"ROUTE"}

def mk(label,rng):
    n=rng.randint(8,28); budget=n+rng.randint(3,10)
    if label=="CONVERGING_FIXED_POINT":
        delta=max(0.002,rng.gauss(0.018,0.007)); residual=max(0.005,rng.gauss(0.07,0.03)); rtnd=rng.gauss(-0.025,0.008); dtnd=rng.gauss(-0.018,0.008); period=None; util=max(0.0,rng.gauss(0.015,0.01)); cost=max(0.001,rng.gauss(0.01,0.003)); bounded=True
    elif label=="PRODUCTIVE_LIMIT_CYCLE":
        delta=max(0.06,rng.gauss(0.18,0.04)); residual=max(0.05,rng.gauss(0.32,0.10)); rtnd=rng.gauss(-0.012,0.006); dtnd=rng.gauss(0.0,0.006); period=max(1.0,rng.choice([2,3,4])+rng.gauss(0,0.05)); util=max(0.02,rng.gauss(0.08,0.02)); cost=max(0.003,rng.gauss(0.02,0.005)); bounded=True
    elif label=="STALLED":
        delta=max(0.001,rng.gauss(0.015,0.006)); residual=min(1.0,max(0.35,rng.gauss(0.70,0.10))); rtnd=rng.gauss(0.0,0.006); dtnd=rng.gauss(0.0,0.006); period=None; util=rng.gauss(0.0,0.008); cost=max(0.005,rng.gauss(0.018,0.004)); bounded=True
    elif label=="DIVERGING_OR_OVERTHINKING":
        delta=max(0.04,rng.gauss(0.22,0.07)); residual=min(1.5,max(0.45,rng.gauss(0.85,0.15))); rtnd=max(0.03,rng.gauss(0.055,0.015)); dtnd=max(0.03,rng.gauss(0.050,0.015)); period=None; util=min(-0.025,rng.gauss(-0.08,0.025)); cost=max(0.01,rng.gauss(0.035,0.01)); bounded=False
    else:
        delta=max(0.04,rng.gauss(0.25,0.10)); residual=max(0.15,rng.gauss(0.50,0.18)); rtnd=rng.gauss(0.0,0.015); dtnd=rng.gauss(0.0,0.015); period=None; util=rng.gauss(0.0,0.015); cost=max(0.01,rng.gauss(0.025,0.006)); bounded=rng.random()>0.25
    return rt.Readout("L",delta,residual,n,budget,-dtnd,period,util,cost,bounded,rtnd,dtnd)

def evaluate(seed=90210,per_class=20000):
    rng=random.Random(seed); labels=list(LABEL_ACTION); conf={l:{p:0 for p in labels} for l in labels}; base={l:{p:0 for p in labels} for l in labels}; aok=baok=total=0
    for label in labels:
        for _ in range(per_class):
            r=mk(label,rng); pr,pa,_=rt.classify(r); br,ba=rt.scalar_baseline(r); conf[label][pr]+=1; base[label][br]+=1; aok+=(pa==LABEL_ACTION[label]); baok+=(ba==LABEL_ACTION[label]); total+=1
    return {"seed":seed,"per_class":per_class,"total":total,"typed_regime_accuracy":sum(conf[l][l] for l in labels)/total,"typed_action_accuracy":aok/total,"scalar_regime_accuracy":sum(base[l][l] for l in labels)/total,"scalar_action_accuracy":baok/total,"typed_confusion":conf,"scalar_confusion":base}

if __name__=="__main__": print(json.dumps(evaluate(),sort_keys=True))
