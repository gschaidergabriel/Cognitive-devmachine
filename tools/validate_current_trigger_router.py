#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / 'research_entity/global/CURRENT_TRIGGER_ROUTER.json'

EXPECTED = {
    '3': {'3', 'triggerword 3', 'triggerwort 3'},
    '4': {'4', 'triggerword 4', 'triggerwort 4'},
    '5': {'5', 'triggerword 5', 'triggerwort 5'},
}


def normalize(s: str) -> str:
    return ' '.join(s.strip().lower().split())


def main() -> int:
    errors = []
    try:
        data = json.loads(ROUTER.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'CURRENT trigger router unreadable: {e}')
        return 2

    macros = data.get('macros', {})
    if set(macros) != set(EXPECTED):
        errors.append(f'macro keys differ: got={sorted(macros)} expected={sorted(EXPECTED)}')

    reverse = {}
    for macro, expected_aliases in EXPECTED.items():
        spec = macros.get(macro, {})
        aliases = {normalize(x) for x in spec.get('aliases', [])}
        if aliases != expected_aliases:
            errors.append(f'{macro}: aliases={sorted(aliases)} expected={sorted(expected_aliases)}')
        for alias in aliases:
            if alias in reverse:
                errors.append(f'alias collision: {alias!r} -> {reverse[alias]} and {macro}')
            reverse[alias] = macro

        if macro in {'4', '5'}:
            if not spec.get('fetch_before_execute'):
                errors.append(f'{macro}: fetch_before_execute must be true')
            if spec.get('failure_behavior') != 'TRIGGER_ROUTING_FAILED':
                errors.append(f'{macro}: failure behavior must be TRIGGER_ROUTING_FAILED')
            for rel in spec.get('protocols', []):
                if not (ROOT / rel).is_file():
                    errors.append(f'{macro}: missing protocol {rel}')

    for alias, macro in sorted(reverse.items()):
        if macro not in macros:
            errors.append(f'{alias}: routes to missing macro {macro}')

    if errors:
        print('CURRENT trigger routing FAILED')
        for e in errors:
            print(' -', e)
        return 1

    print('CURRENT trigger routing PASS')
    for alias, macro in sorted(reverse.items()):
        print(f' {alias!r} -> {macro}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
