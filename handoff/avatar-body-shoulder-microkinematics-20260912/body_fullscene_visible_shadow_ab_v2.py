#!/usr/bin/env python3
"""Visible-X11 production-shape successor to body_fullscene_shadow_ab.py.

This is deliberately a thin, fail-closed execution-surface adapter around the
already-reviewed whole-scene BASE-vs-SHADOW discriminator.  It does not create
a second body implementation and never writes the live avatar tree.

The only semantic changes to the parent discriminator are:
  * fresh *visible* Chrome app window instead of --headless=new;
  * production window geometry (746x449) on the real X11 display;
  * fresh profile per condition remains unchanged;
  * report schema is explicitly marked VISIBLE.

The parent source is patched only when every expected source marker occurs
exactly once.  Any parent drift fails closed before Chrome is started.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

PARENT = Path(__file__).with_name("body_fullscene_shadow_ab.py")
source = PARENT.read_text(encoding="utf-8")
parent_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()

patches = [
    (
        "import argparse, hashlib, json, pathlib, statistics, subprocess, tempfile, threading, time, urllib.request",
        "import argparse, hashlib, json, pathlib, statistics, subprocess, tempfile, threading, time, urllib.request, os",
        "IMPORT_OS",
    ),
    (
        "p=subprocess.Popen([a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run','--window-size=620,414',f'--user-data-dir={tempfile.mkdtemp(prefix=\"body-fullscene-chrome-\")}',url],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True);time.sleep(a.duration)",
        "p=subprocess.Popen([a.chrome,'--no-sandbox','--disable-background-networking','--no-first-run','--window-size=746,449','--window-position=60,120',f'--user-data-dir={tempfile.mkdtemp(prefix=\"body-fullscene-visible-chrome-\")}',f'--app={url}'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,env=dict(os.environ,DISPLAY=os.environ.get('GO_AVATAR_DISPLAY',':0')));time.sleep(a.duration)",
        "VISIBLE_CHROME_LAUNCH",
    ),
    (
        "'schema':'BODY_FULLSCENE_SHADOW_AB/v1'",
        "'schema':'BODY_FULLSCENE_VISIBLE_SHADOW_AB/v2','execution_surface':'VISIBLE_X11_FRESH_CHROME_APP_746x449','display':os.environ.get('GO_AVATAR_DISPLAY',':0'),'parent_source_sha256':'%s'" % parent_sha256,
        "VISIBLE_SCHEMA",
    ),
]

for old, new, label in patches:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"VISIBLE_WRAPPER_PATCH_PRECONDITION_FAILED {label} count={count}")
    source = source.replace(old, new, 1)

compile(source, str(PARENT) + ":visible-shadow-v2", "exec")
print(f"VISIBLE_WRAPPER_PARENT_SHA256={parent_sha256}")
print(f"VISIBLE_WRAPPER_DISPLAY={os.environ.get('GO_AVATAR_DISPLAY', ':0')}")
namespace = {
    "__name__": "__main__",
    "__file__": str(PARENT),
    "__package__": None,
}
exec(compile(source, str(PARENT) + ":visible-shadow-v2", "exec"), namespace, namespace)
