#!/usr/bin/env python3
"""Deterministic gate for coupling calibrated shoulder residual to existing actions.

No live mutation. Models the intended single-authority integration: existing
KOERPER_AKTIONEN determines the semantic action; this envelope only attenuates the
already-calibrated residual shoulder mesh with smoothstep ramps.
"""
from __future__ import annotations
import json, math

FPS=60.0
DT=1000.0/FPS
IDLE=4.0
TARGETS={
 'schulterzucken':0.0,
 'schulterdrehung':0.0,
 'aufrichten':1.5,
 'lehnen':1.5,
 'gewicht':1.5,
}
DURATIONS_MS={
 'schulterzucken':8*110,
 'schulterdrehung':11*170,
 'aufrichten':8*200,
 'lehnen':9*300,
 'gewicht':11*300,
}
ENTER_MS=120.0
EXIT_MS=180.0
DISPLAY_PX_PER_SCALE=0.93796875/4.0

def smoothstep(x:float)->float:
 x=max(0.0,min(1.0,x));return x*x*(3.0-2.0*x)

def ramp(a:float,b:float,elapsed:float,duration:float)->float:
 return a+(b-a)*smoothstep(elapsed/duration if duration>0 else 1.0)

def simulate(name:str):
 target=TARGETS[name]; action_ms=DURATIONS_MS[name]
 # Include 250 ms idle before entry and 350 ms after exit.
 t=-250.0; vals=[]
 while t<=action_ms+350.0+1e-9:
  if t<0: s=IDLE
  elif t<=ENTER_MS: s=ramp(IDLE,target,t,ENTER_MS)
  elif t<=action_ms: s=target
  elif t<=action_ms+EXIT_MS: s=ramp(target,IDLE,t-action_ms,EXIT_MS)
  else: s=IDLE
  vals.append((t,s));t+=DT
 steps=[abs(vals[i][1]-vals[i-1][1]) for i in range(1,len(vals))]
 pxsteps=[x*DISPLAY_PX_PER_SCALE for x in steps]
 # Exact continuity is analytical: ramp starts exactly from previous authority value.
 entry_jump=abs(ramp(IDLE,target,0,ENTER_MS)-IDLE)
 exit_jump=abs(ramp(target,IDLE,0,EXIT_MS)-target)
 plateau=[s for t,s in vals if ENTER_MS+DT<=t<=action_ms-DT]
 post=[s for t,s in vals if t>=action_ms+EXIT_MS+DT]
 return {
   'target_scale':target,'action_duration_ms':action_ms,'samples':len(vals),
   'entry_jump_scale':entry_jump,'exit_jump_scale':exit_jump,
   'max_frame_step_scale':max(steps),'max_frame_step_display_px':max(pxsteps),
   'plateau_min':min(plateau) if plateau else None,'plateau_max':max(plateau) if plateau else None,
   'post_min':min(post) if post else None,'post_max':max(post) if post else None,
 }

def main():
 rows={k:simulate(k) for k in TARGETS}
 acceptance={
   'zero_entry_step':all(v['entry_jump_scale']==0 for v in rows.values()),
   'zero_exit_step':all(v['exit_jump_scale']==0 for v in rows.values()),
   'max_frame_step_display_px_le_0_25':all(v['max_frame_step_display_px']<=0.25 for v in rows.values()),
   'shoulder_actions_reach_zero':all(abs(rows[k]['plateau_min'])<1e-12 and abs(rows[k]['plateau_max'])<1e-12 for k in ('schulterzucken','schulterdrehung')),
   'other_actions_reach_1_5':all(abs(rows[k]['plateau_min']-1.5)<1e-12 and abs(rows[k]['plateau_max']-1.5)<1e-12 for k in ('aufrichten','lehnen','gewicht')),
   'returns_to_idle_4':all(abs(v['post_min']-4)<1e-12 and abs(v['post_max']-4)<1e-12 for v in rows.values()),
 }
 out={'schema':'BODY_RESIDUAL_ACTION_ENVELOPE/v1','fps':FPS,'idle_scale':IDLE,'enter_ms':ENTER_MS,'exit_ms':EXIT_MS,'display_px_per_scale':DISPLAY_PX_PER_SCALE,'actions':rows,'acceptance':acceptance,'pass':all(acceptance.values()),'live_mutation':False}
 print(json.dumps(out,indent=2,sort_keys=True))
 raise SystemExit(0 if out['pass'] else 2)
if __name__=='__main__':main()
