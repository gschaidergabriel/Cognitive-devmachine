from __future__ import annotations
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]

def _installer():
    p=ROOT/'build'/'install_pinned_xterm.py'
    spec=importlib.util.spec_from_file_location('install_pinned_xterm',p); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def _archive(extra=(), *, package='@xterm/xterm', version='6.0.0'):
    entries=[
        ('package/package.json',json.dumps({'name':package,'version':version}).encode()),
        ('package/lib/xterm.js',b'console.log("xterm")'),
        ('package/css/xterm.css',b'.xterm{}'),
        *extra,
    ]
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w:gz') as tf:
        for name,payload in entries:
            info=tarfile.TarInfo(name); info.size=len(payload); info.mode=0o644; tf.addfile(info,io.BytesIO(payload))
    return out.getvalue()

def test_lock_is_exact_registry_tarball_and_sha512_sri(monkeypatch):
    mod=_installer(); monkeypatch.setattr(mod,'LOCK_PATH',ROOT/'SOURCE_LOCK.json')
    package,version,url,digest=mod.load_config()
    assert package=='@xterm/xterm' and version=='6.0.0'
    assert url=='https://registry.npmjs.org/@xterm/xterm/-/xterm-6.0.0.tgz'
    assert len(digest)==hashlib.sha512().digest_size

def test_installer_extracts_only_runtime_assets_with_readable_permissions(tmp_path):
    mod=_installer(); target=tmp_path/'xterm'; mod.install_archive(_archive(),target)
    assert sorted(str(p.relative_to(target)) for p in target.rglob('*') if p.is_file())==['css/xterm.css','lib/xterm.js','package.json']
    assert (target/'lib/xterm.js').read_bytes()==b'console.log("xterm")'
    assert (target/'css/xterm.css').read_bytes()==b'.xterm{}'
    assert (target.stat().st_mode & 0o555)==0o555
    assert ((target/'lib').stat().st_mode & 0o555)==0o555
    assert ((target/'css').stat().st_mode & 0o555)==0o555

def test_installer_rejects_package_identity_mismatch(tmp_path):
    mod=_installer(); target=tmp_path/'xterm'
    try: mod.install_archive(_archive(package='attacker/xterm'),target)
    except SystemExit as exc: assert 'package identity mismatch' in str(exc)
    else: raise AssertionError('wrong package identity accepted')
    assert not target.exists()

def test_digest_authorized_traversal_still_fails_closed(tmp_path):
    mod=_installer(); target=tmp_path/'xterm'; archive=_archive((('package/../../escape',b'owned'),))
    assert len(hashlib.sha512(archive).digest())==64
    try: mod.install_archive(archive,target)
    except SystemExit as exc: assert 'unsafe xterm archive member' in str(exc)
    else: raise AssertionError('digest-authorized traversal archive accepted')
    assert not (tmp_path/'escape').exists()
    assert not target.exists()

def test_digest_fault_injection_fails_before_archive_open(monkeypatch):
    mod=_installer(); good=_archive(); damaged=bytearray(good); damaged[len(damaged)//2]^=1; damaged=bytes(damaged)
    expected=hashlib.sha512(good).digest()
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def read(self,*args): return damaged
    monkeypatch.setattr(mod.urllib.request,'urlopen',lambda *args,**kwargs: Response())
    try: mod.fetch_verified('https://registry.npmjs.org/@xterm/xterm/-/xterm-6.0.0.tgz',expected)
    except SystemExit as exc: assert 'digest mismatch' in str(exc)
    else: raise AssertionError('tampered xterm tarball accepted')
