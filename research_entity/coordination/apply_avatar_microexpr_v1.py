#!/usr/bin/env python3
from pathlib import Path
import hashlib, os, re, shutil, subprocess, sys, tempfile

LIVE = Path('/home/ai-core-node/.claude/star/visual/buehne.html')
ROOT = LIVE.parent
ENGINE = Path(__file__).with_name('avatar_microexpr_v1.js')
EXPECTED = '18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e'
raw = LIVE.read_bytes()
pre = hashlib.sha256(raw).hexdigest()
print('PRE_SHA=' + pre)
if pre != EXPECTED:
    print('CAS_REFUSED expected=' + EXPECTED + ' actual=' + pre)
    raise SystemExit(42)
text = raw.decode('utf-8')
engine = ENGINE.read_text(encoding='utf-8')
if 'FRANK_MICROEXPR_V1 BEGIN' in text:
    print('ALREADY_PRESENT')
    raise SystemExit(41)
required = ['id="mund-effekt"', 'function mundSchritt', 'function schleife(t)',
            'async function statusHolen()', 'const b = d.buehne || {};']
missing = [x for x in required if x not in text]
if missing:
    print('SOURCE_SHAPE_REFUSED=' + repr(missing))
    raise SystemExit(43)

# Fail closed if any mouth asset required by the engine is missing.
asset_paths = []
for stem in ['mund_31_smirk_left','mund_32_smirk_right','mund_33_pout',
             'mund_34_jaw_clench','mund_22_snarl_left','mund_23_snarl_right',
             'mund_25_tongue_tip']:
    asset_paths += [f'mund_keyframes/{stem}/stufe_0{i}.png' for i in range(5)]
asset_paths += [
    'mund_keyframes/mund_26_tongue_out__stufe_00.png',
    'mund_keyframes/mund_26_tongue_out__stufe_02.png',
    'mund_keyframes/mund_26_tongue_out__stufe_03.png',
    'mund_keyframes/mund_26_tongue_out__stufe_04.png',
    'mund_keyframes/mund_27_tongue_left__stufe_01.png',
    'mund_keyframes/mund_27_tongue_left__stufe_02.png',
    'mund_keyframes/mund_27_tongue_left__stufe_03.png',
    'mund_keyframes/mund_27_tongue_left__stufe_04.png',
    'mund_keyframes/mund_28_tongue_right__stufe_01.png',
    'mund_keyframes/mund_28_tongue_right__stufe_02.png',
    'mund_keyframes/mund_28_tongue_right__stufe_03.png',
    'mund_keyframes/mund_28_tongue_right__stufe_04.png',
    'mund_keyframes/mund_35_gasp__stufe_00.png',
    'mund_keyframes/mund_35_gasp__stufe_02.png',
    'mund_keyframes/mund_35_gasp__stufe_03.png',
    'mund_keyframes/mund_20_grin_closed__stufe_00.png',
    'mund_keyframes/mund_20_grin_closed__stufe_02.png',
    'mund_keyframes/mund_20_grin_closed__stufe_04.png',
    'mund_keyframes/mund_29_whistle_small/stufe_00.png',
    'mund_keyframes/mund_29_whistle_small/stufe_02.png',
    'mund_keyframes/mund_29_whistle_small/stufe_04.png',
]
missing_assets = [x for x in asset_paths if not (ROOT / x).is_file()]
print('ASSET_CHECK=' + str(len(asset_paths)))
if missing_assets:
    print('MISSING_ASSETS=' + repr(missing_assets))
    raise SystemExit(44)

if text.count('function schleife(t){') != 1:
    print('LOOP_FUNCTION_COUNT=' + str(text.count('function schleife(t){')))
    raise SystemExit(45)
text = text.replace('function schleife(t){', engine + '\n\nfunction schleife(t){', 1)
old_loop = '  mundSchritt(t);\n  kopfKoerperDrehSchritt();'
if text.count(old_loop) != 1:
    print('LOOP_ANCHOR_COUNT=' + str(text.count(old_loop)))
    raise SystemExit(46)
text = text.replace(old_loop, '  mundSchritt(t);\n  _mikroMimikSchritt(t);\n  kopfKoerperDrehSchritt();', 1)
old_status = '    const b = d.buehne || {};\n    if(typeof b.broadcast_value === "number"){' 
if text.count(old_status) != 1:
    print('STATUS_ANCHOR_COUNT=' + str(text.count(old_status)))
    raise SystemExit(47)
text = text.replace(old_status,
                    '    const b = d.buehne || {};\n    _mikroMimikStateAktualisieren(b);\n    if(typeof b.broadcast_value === "number"){', 1)
if text.count('FRANK_MICROEXPR_V1 BEGIN') != 1:
    print('MARKER_COUNT_FAIL')
    raise SystemExit(48)

# Syntax-check all inline JavaScript before the live byte replacement.
parts = []
for m in re.finditer(r'<script([^>]*)>(.*?)</script>', text, re.I | re.S):
    if 'src=' not in m.group(1).lower():
        parts.append(m.group(2))
fd, tmpjs = tempfile.mkstemp(prefix='buehne-microexpr-', suffix='.js')
os.close(fd)
Path(tmpjs).write_text('\n;\n'.join(parts), encoding='utf-8')
try:
    cp = subprocess.run(['node', '--check', tmpjs], capture_output=True, text=True)
    if cp.returncode:
        print('NODE_CHECK_FAIL')
        print(cp.stdout[-2000:])
        print(cp.stderr[-4000:])
        raise SystemExit(49)
finally:
    try: os.unlink(tmpjs)
    except OSError: pass

backup = LIVE.with_name(LIVE.name + '.pre-microexpr-' + pre[:12] + '.bak')
if not backup.exists():
    shutil.copy2(LIVE, backup)
fd, tmp = tempfile.mkstemp(prefix='.buehne.microexpr.', dir=str(ROOT))
os.close(fd)
Path(tmp).write_text(text, encoding='utf-8')
os.chmod(tmp, LIVE.stat().st_mode)
os.replace(tmp, LIVE)
post_raw = LIVE.read_bytes()
post = hashlib.sha256(post_raw).hexdigest()
print('BACKUP=' + str(backup))
print('POST_SHA=' + post)
print('BYTES=' + str(len(post_raw)))
print('MICROEXPR_PATCH_PASS')
