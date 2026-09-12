#!/usr/bin/env python3
"""Read-only runtime asset gate for the idle microexpression controller."""
from __future__ import annotations
import pathlib
import struct

ROOT = pathlib.Path('/home/ai-core-node/.claude/star/visual/mund_keyframes')
ASSETS = [
    'mund_01_closed_mbp','mund_02_breath','mund_08_o_small',
    'mund_20_grin_closed','mund_21_grin_teeth','mund_22_snarl_left',
    'mund_23_snarl_right','mund_24_bare_teeth','mund_25_tongue_tip',
    'mund_26_tongue_out','mund_27_tongue_left','mund_28_tongue_right',
    'mund_29_whistle_small','mund_30_whistle_strong','mund_31_smirk_left',
    'mund_32_smirk_right','mund_33_pout','mund_34_jaw_clench','mund_35_gasp',
    'mund_00_rest'
]
EXPECTED_WH = (334, 286)


def png_wh(path: pathlib.Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise SystemExit(f'ASSET_GATE_FAIL not_png {path}')
    return struct.unpack('>II', data[16:24])


def check(path: pathlib.Path) -> None:
    if not path.is_file():
        raise SystemExit(f'ASSET_GATE_FAIL missing {path}')
    wh = png_wh(path)
    if wh != EXPECTED_WH:
        raise SystemExit(f'ASSET_GATE_FAIL geometry {path} got={wh} expected={EXPECTED_WH}')


def main() -> None:
    checked = 0
    for asset in ASSETS:
        check(ROOT / f'{asset}.png'); checked += 1
        for stage in range(5):
            check(ROOT / f'{asset}__stufe_0{stage}.png'); checked += 1
    print(f'ASSET_GATE_PASS assets={len(ASSETS)} files={checked} geometry={EXPECTED_WH[0]}x{EXPECTED_WH[1]}')


if __name__ == '__main__':
    main()
