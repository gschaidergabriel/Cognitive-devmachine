#!/usr/bin/env python3
"""SPL-001 deterministic synthetic semantic-boundary discriminator.

This is a controlled-German reference micro-harness paired to CANDIDATE_ATOMIC_SPL_001.clay.
It is deliberately not a general German translator and does not claim model/VPS measurements.
It creates stable common-mode translator faults, compares weak roundtrip, an independent full
validator and SPL per-field partial oracles, then exercises unknown, ablation, expression and
checker-fault controls.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from collections import Counter
import hashlib, json, random, re, statistics, time

PEOPLE=["Andreas","Gabriel","Frank","Patrick","Markus"]
MOD_DE={"MUST":"muss","MAY":"darf","MUST_NOT":"darf keinesfalls","UNCERTAIN":"kann vielleicht"}; MOD_PARSE={v:k for k,v in MOD_DE.items()}
TEMP_DE={"NOW":"jetzt","TOMORROW":"morgen","AFTER_RESTART":"nach Neustart","BEFORE_EFFECT":"vor Ausführung"}; TEMP_PARSE={v:k for k,v in TEMP_DE.items()}
SP_DE={"ASSERT":"Aussage","QUESTION":"Frage","REQUEST":"Bitte","COMMAND":"Befehl"}; SP_PARSE={v:k for k,v in SP_DE.items()}
PERM_DE={"NONE":"neutral","ALLOW":"erlaubt","DENY":"verboten"}; PERM_PARSE={v:k for k,v in PERM_DE.items()}
EFF_DE={"NONE":"beobachten","READ":"lesen","WRITE_REVERSIBLE":"ändern","DELETE":"löschen","ROTATE_CREDENTIAL":"Token-rotieren","SECURITY_CHANGE":"Sicherheit-ändern"}; EFF_PARSE={v:k for k,v in EFF_DE.items()}
NEG_DE={False:"positiv",True:"negiert"}; NEG_PARSE={v:k for k,v in NEG_DE.items()}
UNITS=["MB","GB","Anfragen","Minuten"]
FIELDS=("person","negated","modality","quantity","unit","temporal","speech_act","permission","effect")
BUGS=("DROP_NEGATION","MAY_AS_MUST","ANDREAS_AS_GABRIEL","TEN_AS_HUNDRED","QUESTION_AS_COMMAND","READ_AS_WRITE","ALLOW_AS_DENY","TOMORROW_AS_NOW")

@dataclass(frozen=True)
class Frame:
    person:str; negated:bool; modality:str; quantity:int; unit:str; temporal:str; speech_act:str; permission:str; effect:str

FULL_RE=re.compile(
 r"^(?:(?:Freundlich|Formell|Dringend): )?(?P<speech>Aussage|Frage|Bitte|Befehl): Person=(?P<person>[^;]+); "
 r"Modal=(?P<modal>muss|darf|darf keinesfalls|kann vielleicht); Negation=(?P<neg>positiv|negiert); Menge=(?P<qty>\d+); "
 r"Einheit=(?P<unit>MB|GB|Anfragen|Minuten); Zeit=(?P<temp>jetzt|morgen|nach Neustart|vor Ausführung); "
 r"Erlaubnis=(?P<perm>neutral|erlaubt|verboten); Aktion=(?P<effect>beobachten|lesen|ändern|löschen|Token-rotieren|Sicherheit-ändern)$")

PAT={
 "person":re.compile(r"Person=([^;]+);"),"modality":re.compile(r"Modal=(muss|darf|darf keinesfalls|kann vielleicht);"),
 "negated":re.compile(r"Negation=(positiv|negiert);"),"quantity":re.compile(r"Menge=(\d+);"),
 "unit":re.compile(r"Einheit=(MB|GB|Anfragen|Minuten);"),"temporal":re.compile(r"Zeit=(jetzt|morgen|nach Neustart|vor Ausführung);"),
 "speech_act":re.compile(r"(?:(?:^|: ))(Aussage|Frage|Bitte|Befehl): Person="),
 "permission":re.compile(r"Erlaubnis=(neutral|erlaubt|verboten);"),
 "effect":re.compile(r"Aktion=(beobachten|lesen|ändern|löschen|Token-rotieren|Sicherheit-ändern)$")}

def render(f:Frame,style="neutral"):
    prefix={"neutral":"","warm":"Freundlich: ","formal":"Formell: ","urgent":"Dringend: "}[style]
    return f"{prefix}{SP_DE[f.speech_act]}: Person={f.person}; Modal={MOD_DE[f.modality]}; Negation={NEG_DE[f.negated]}; Menge={f.quantity}; Einheit={f.unit}; Zeit={TEMP_DE[f.temporal]}; Erlaubnis={PERM_DE[f.permission]}; Aktion={EFF_DE[f.effect]}"

def full_parse(s):
    m=FULL_RE.match(s)
    if not m:return None
    g=m.groupdict(); return Frame(g['person'],NEG_PARSE[g['neg']],MOD_PARSE[g['modal']],int(g['qty']),g['unit'],TEMP_PARSE[g['temp']],SP_PARSE[g['speech']],PERM_PARSE[g['perm']],EFF_PARSE[g['effect']])

def apply_bug(f,s,b):
    if b=="DROP_NEGATION" and "Negation=negiert" in s:return replace(f,negated=False)
    if b=="MAY_AS_MUST" and "Modal=darf;" in s:return replace(f,modality="MUST")
    if b=="ANDREAS_AS_GABRIEL" and "Person=Andreas;" in s:return replace(f,person="Gabriel")
    if b=="TEN_AS_HUNDRED" and "Menge=10;" in s:return replace(f,quantity=100)
    if b=="QUESTION_AS_COMMAND" and re.search(r"(?:^|: )Frage: Person=",s):return replace(f,speech_act="COMMAND")
    if b=="READ_AS_WRITE" and "Aktion=lesen" in s:return replace(f,effect="WRITE_REVERSIBLE")
    if b=="ALLOW_AS_DENY" and "Erlaubnis=erlaubt;" in s:return replace(f,permission="DENY")
    if b=="TOMORROW_AS_NOW" and "Zeit=morgen;" in s:return replace(f,temporal="NOW")
    return f

def main_translate(s,b):
    f=full_parse(s); return None if f is None else apply_bug(f,s,b)

def same_codec_roundtrip(s,cand,b): return main_translate(render(cand),b)==cand

def observe(field,s):
    m=PAT[field].search(s)
    if not m:return "UNKNOWN",None
    v=m.group(1)
    if field=="negated":v=NEG_PARSE[v]
    elif field=="modality":v=MOD_PARSE[v]
    elif field=="quantity":v=int(v)
    elif field=="temporal":v=TEMP_PARSE[v]
    elif field=="speech_act":v=SP_PARSE[v]
    elif field=="permission":v=PERM_PARSE[v]
    elif field=="effect":v=EFF_PARSE[v]
    return "OBSERVED",v

def spl_validate(s,cand,enabled=FIELDS):
    unknown=[]
    for f in enabled:
        k,v=observe(f,s)
        if k=="UNKNOWN":unknown.append(f);continue
        if getattr(cand,f)!=v:return "REJECT"
    return "AMBIGUOUS" if unknown else "ACCEPT"

def full_validate(s,cand):
    f=full_parse(s); return "AMBIGUOUS" if f is None else "ACCEPT" if f==cand else "REJECT"

def random_frame(r):
    q=10 if r.random()<.22 else r.choice([1,2,5,20,42,100,256,999])
    return Frame(r.choice(PEOPLE),r.choice([False,True]),r.choice(list(MOD_DE)),q,r.choice(UNITS),r.choice(list(TEMP_DE)),r.choice(list(SP_DE)),r.choice(list(PERM_DE)),r.choice(list(EFF_DE)))

def active_fault(r,truth,s):
    for _ in range(12):
        b=r.choice(BUGS); c=apply_bug(truth,s,b)
        if c!=truth:return b,c
    return "NONE",truth

def percentile(xs,p):
    xs=sorted(xs); return xs[min(len(xs)-1,int((len(xs)-1)*p))]

def benchmark(n=100000,seed=20260810,sample=20000):
    r=random.Random(seed); c=Counter(); ls=[];lf=[];lr=[];sizes=[];abl=Counter();abn=Counter()
    for i in range(n):
        truth=random_frame(r); s=render(truth)
        b,cand=active_fault(r,truth,s) if r.random()<.65 else ("NONE",truth)
        bad=cand!=truth; c['corrupt']+=bad;c['valid']+=not bad
        if bad:c['type_fa']+=1
        t=time.perf_counter_ns();rv=same_codec_roundtrip(s,cand,b);d=time.perf_counter_ns()-t
        if i<sample:lr.append(d/1000)
        if rv and bad:c['rt_fa']+=1
        t=time.perf_counter_ns();fv=full_validate(s,cand);d=time.perf_counter_ns()-t
        if i<sample:lf.append(d/1000)
        if fv=='ACCEPT' and bad:c['full_fa']+=1
        if fv!='ACCEPT' and not bad:c['full_fd']+=1
        t=time.perf_counter_ns();sv=spl_validate(s,cand);d=time.perf_counter_ns()-t
        if i<sample:ls.append(d/1000)
        if sv=='ACCEPT' and bad:c['spl_fa']+=1
        if sv!='ACCEPT' and not bad:c['spl_fd']+=1
        if i<sample:
            w={"src":hashlib.sha256(s.encode()).hexdigest(),"cand":hashlib.sha256(repr(cand).encode()).hexdigest(),"observed":{f:observe(f,s)[1] for f in FIELDS},"admission":sv}
            sizes.append(len(json.dumps(w,separators=(',',':')).encode()))
        if bad:
            changed=[f for f in FIELDS if getattr(truth,f)!=getattr(cand,f)]
            if len(changed)==1:
                f=changed[0];abn[f]+=1
                if spl_validate(s,cand,[x for x in FIELDS if x!=f])=='ACCEPT':abl[f]+=1
    corrupt=max(1,c['corrupt']);valid=max(1,c['valid'])
    return {"seed":seed,"cases":n,"counts":dict(c),"rates":{"type_fa":c['type_fa']/corrupt,"roundtrip_fa":c['rt_fa']/corrupt,"full_fa":c['full_fa']/corrupt,"full_fd":c['full_fd']/valid,"spl_fa":c['spl_fa']/corrupt,"spl_fd":c['spl_fd']/valid},"latency_us":{"roundtrip":{"p50":percentile(lr,.5),"p95":percentile(lr,.95)},"full":{"p50":percentile(lf,.5),"p95":percentile(lf,.95)},"spl":{"p50":percentile(ls,.5),"p95":percentile(ls,.95)}},"witness_bytes":{"p50":percentile(sizes,.5),"p95":percentile(sizes,.95)},"ablation_escape":{f:abl[f]/abn[f] for f in abn}}

if __name__=='__main__':
    print(json.dumps(benchmark(),indent=2,sort_keys=True))
