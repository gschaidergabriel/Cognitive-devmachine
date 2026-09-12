#!/usr/bin/env python3
"""Harness-only repair for body_dormant_residual_matched_gate.py.

The v1 gate's local HTTP handler class was named H, shadowing the module's
H=414 display-height constant inside main(), which made image analysis fail
with `float * type`. This wrapper changes ONLY that identifier collision.
No thresholds, renderer code, residual policy, source binding, or acceptance
criteria are modified.
"""
from __future__ import annotations
import pathlib
import runpy
import tempfile

src_path = pathlib.Path(__file__).with_name('body_dormant_residual_matched_gate.py')
src = src_path.read_text(encoding='utf-8')
old_class = '        class H(BaseHTTPRequestHandler):\n'
new_class = '        class HttpHandler(BaseHTTPRequestHandler):\n'
old_srv = "        srv=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{srv.server_address[1]}/?body_test_lock=1'\n"
new_srv = "        srv=ThreadingHTTPServer(('127.0.0.1',0),HttpHandler);threading.Thread(target=srv.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{srv.server_address[1]}/?body_test_lock=1'\n"
if src.count(old_class) != 1:
    raise SystemExit(f'HARNESS_PATCH_CLASS_ANCHOR_COUNT={src.count(old_class)}')
if src.count(old_srv) != 1:
    raise SystemExit(f'HARNESS_PATCH_SERVER_ANCHOR_COUNT={src.count(old_srv)}')
patched = src.replace(old_class, new_class, 1).replace(old_srv, new_srv, 1)
with tempfile.TemporaryDirectory(prefix='body-dormant-v2-') as td:
    p = pathlib.Path(td) / 'gate.py'
    p.write_text(patched, encoding='utf-8')
    runpy.run_path(str(p), run_name='__main__')
