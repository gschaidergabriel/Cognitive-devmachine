import json, os, random, tempfile
from state_ledger import StateLedger, StaleEpoch, h
rng=random.Random(20260809); base=list(range(12)); sh=h({'$kind':'set','items':base})
for _ in range(5000):
    x=base[:]+[rng.choice(base) for _ in range(rng.randrange(8))]; rng.shuffle(x); assert h({'$kind':'set','items':x})==sh
ordered=['proposal','permit','reserve','commit','outcome','reentry']; oh=h({'$kind':'ordered','items':ordered}); changed=0
for _ in range(5000):
    x=ordered[:]; a,b=rng.sample(range(6),2); x[a],x[b]=x[b],x[a]; changed+=h({'$kind':'ordered','items':x})!=oh
assert changed==5000
l=StateLedger()
for i in range(1000):
    d=['world','memory','gwt','loop_dynamics','authority'][i%5]; v={'i':i,'window':{'$kind':'ordered','items':[max(0,i-2),max(0,i-1),i]},'tags':{'$kind':'set','items':[d,str(i%7),d]}}
    l.append_event(event_id=f'e{i}',idem=f'k{i}',base_epoch=i,event_type='STRESS',writer='stress',ops=[{'op':'SET','domain':d,'key':f'k{i%31}','value':v}],provenance={'fixture':'stress'},source={'baseline':'H1'},execution={'runtime':'local'})
ev=l.export_events(); sem=l.semantic_state_hash; trace=l.trace_root_hash; deps=l.domain_epochs(); r=StateLedger.replay(ev); assert (sem,trace,deps)==(r.semantic_state_hash,r.trace_root_hash,r.domain_epochs())
with tempfile.TemporaryDirectory() as td:
    p=os.path.join(td,'c.db'); a=StateLedger(p); b=StateLedger(p); a.append_event(event_id='a',idem='a',base_epoch=0,event_type='A',writer='A',ops=[{'op':'SET','domain':'world','key':'x','value':1}])
    try: b.append_event(event_id='b',idem='b',base_epoch=0,event_type='B',writer='B',ops=[{'op':'SET','domain':'world','key':'x','value':2}]); raise AssertionError('stale accepted')
    except StaleEpoch: pass
    a.close(); b.close()
s=StateLedger(); s.append_event(event_id='s',idem='s',base_epoch=0,event_type='S',writer='S',ops=[{'op':'SET','domain':'memory','key':'m','value':1}]); s.snapshot('s'); s.conn.execute("UPDATE snapshots SET state_json='[]' WHERE id='s'"); s.conn.commit(); assert not s.verify_snapshot('s')
print(json.dumps({'status':'PASS','tests':{'typed_set_permutations':5000,'ordered_mutations_detected':changed,'long_replay_events':1000,'stale_writer_rejected':True,'snapshot_tamper_detected':True},'semantic_state_hash':sem,'trace_root_hash':trace,'domain_epochs':deps},sort_keys=True))
