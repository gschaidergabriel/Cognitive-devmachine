#!/usr/bin/env python3
"""Target-only real desktop UI adapter for ClayCode APP-05.

Uses Tk's actual OS window/event loop. It is deliberately unavailable in headless CI.
Synthetic virtual input is injected through Tk's event queue so the acceptance test is
automatable while still exercising window creation, event dispatch, state transition and
render update on the physical Ubuntu desktop session.
"""
from __future__ import annotations
import os,time
from typing import Any
from claycode_base_runtime import CapabilityFault,ClayRuntime,ResourceFault
VERSION='claycode-ubuntu-desktop-adapter/0.1'

def _run(policy:dict[str,Any],initial:dict[str,Any],events:list[dict[str,Any]])->dict[str,Any]:
 if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):raise ResourceFault('UBUNTU_DESKTOP_DISPLAY_UNAVAILABLE')
 allowed=set(policy.get('events',['click','reset']))
 if len(events)>int(policy.get('max_events',64)):raise ResourceFault('UI_EVENT_LIMIT')
 for event in events:
  if event.get('kind') not in allowed:raise CapabilityFault('UI_EVENT_NOT_ALLOWED:'+str(event.get('kind')))
 try:
  import tkinter as tk
 except Exception as exc:raise ResourceFault('TKINTER_UNAVAILABLE') from exc
 state={'counter':int(initial.get('counter',0)),'label':str(initial.get('label','idle'))};pending=list(events);trace=[]
 root=tk.Tk();root.title('ClayCode APP-05 target gate');root.geometry('360x120+40+40')
 label_var=tk.StringVar(value=state['label']);label=tk.Label(root,textvariable=label_var);label.pack()
 button=tk.Button(root,text='Clay input');button.pack()
 def handle(_evt=None):
  if not pending:return
  e=pending.pop(0);kind=e['kind']
  if kind=='click':state['counter']+=int(e.get('value',1));state['label']=f"count:{state['counter']}"
  elif kind=='reset':state['counter']=0;state['label']='reset'
  label_var.set(state['label']);trace.append({'kind':kind,'state':dict(state),'rendered':label_var.get()})
  if pending:root.after(20,lambda:button.event_generate('<<ClayInput>>',when='tail'))
  else:root.after(40,root.destroy)
 button.bind('<<ClayInput>>',handle)
 root.update_idletasks();mapped=bool(root.winfo_ismapped());display=root.winfo_screen()
 root.after(20,lambda:button.event_generate('<<ClayInput>>',when='tail')) if pending else root.after(20,root.destroy)
 started=time.monotonic();root.mainloop();elapsed_ms=int((time.monotonic()-started)*1000)
 return {'io_mode':'TK_REAL_DESKTOP_EVENT_LOOP','state':state,'trace':trace,'rendered_label':label_var.get(),'window_was_mapped':mapped,'screen':display,'elapsed_ms':elapsed_ms,'event_count':len(events)}

def install(rt:ClayRuntime)->ClayRuntime:
 rt.register_adapter('ui.ubuntu_desktop_event_loop','ui.desktop',_run);return rt
__all__=['install','VERSION']
