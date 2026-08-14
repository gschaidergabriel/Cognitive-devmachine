#!/usr/bin/env python3
"""Contract-driven local Ubuntu strict closure for selected CC-WP-02 grammar.

V2 intentionally limits itself to evidence that can be self-contained and grammar-bound:
selection discriminator (when required), strict LALR construction, full G9/Dialect
frontend validation, canonical syntax identity, both admitted declarative IR corpora, and
the active production canonicalizer default. It does not consume the legacy declaration
IR self-test because that receipt does not embed its grammar hash.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json'
RDIR = ROOT / 'research_entity/claycode/base/receipts'
DEFAULT_OUT = RDIR / 'LOCAL_WP02_SELECTED_GRAMMAR_CLOSURE.json'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'JSON_NOT_OBJECT:{path}')
    return value


def ver(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def osid() -> str | None:
    path = Path('/etc/os-release')
    if not path.exists():
        return None
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith('ID='):
            return line.split('=', 1)[1].strip().strip('"').lower()
    return None


def memory_total_kib() -> int | None:
    path = Path('/proc/meminfo')
    if not path.exists():
        return None
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith('MemTotal:'):
            parts = line.split()
            return int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
    return None


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ''
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def run(argv: list[str], timeout: int = 300) -> dict[str, Any]:
    """Execute one closure component and preserve bounded process/resource evidence.

    RUSAGE_CHILDREN counters are cumulative for terminated children, so deltas are reported
    for additive counters while max RSS is explicitly labelled as the cumulative maximum
    observed up to this point in the closure process.
    """
    command = [sys.executable, *argv]
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started_ns = time.perf_counter_ns()
    timed_out = False
    returncode: int | None
    stdout = ''
    stderr = ''
    try:
        cp = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        returncode = cp.returncode
        stdout = cp.stdout
        stderr = cp.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        stdout = _text(exc.stdout)
        stderr = _text(exc.stderr)
    finished_ns = time.perf_counter_ns()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)

    return {
        'argv': command,
        'timeout_s': timeout,
        'timed_out': timed_out,
        'returncode': returncode,
        'process_pass': returncode == 0 and not timed_out,
        'elapsed_ns': finished_ns - started_ns,
        'elapsed_ms': round((finished_ns - started_ns) / 1_000_000, 3),
        'child_user_cpu_s_delta': round(max(0.0, after.ru_utime - before.ru_utime), 6),
        'child_system_cpu_s_delta': round(max(0.0, after.ru_stime - before.ru_stime), 6),
        'child_minor_faults_delta': max(0, after.ru_minflt - before.ru_minflt),
        'child_major_faults_delta': max(0, after.ru_majflt - before.ru_majflt),
        'child_input_blocks_delta': max(0, after.ru_inblock - before.ru_inblock),
        'child_output_blocks_delta': max(0, after.ru_oublock - before.ru_oublock),
        'child_voluntary_context_switches_delta': max(0, after.ru_nvcsw - before.ru_nvcsw),
        'child_involuntary_context_switches_delta': max(0, after.ru_nivcsw - before.ru_nivcsw),
        'child_maxrss_cumulative_platform_units': after.ru_maxrss,
        'stdout_sha256': hashlib.sha256(stdout.encode()).hexdigest(),
        'stderr_sha256': hashlib.sha256(stderr.encode()).hexdigest(),
        'stdout_tail': stdout[-3000:],
        'stderr_tail': stderr[-3000:],
    }


def embedded_grammar(doc: dict[str, Any], fallback_path: str | None = None) -> tuple[str | None, str | None]:
    path = doc.get('grammar_path') or doc.get('grammar') or fallback_path
    digest = doc.get('grammar_sha256')
    identity = doc.get('identity') if isinstance(doc.get('identity'), dict) else {}
    digest = digest or identity.get('grammar_sha256')
    return (str(path) if path else None, str(digest) if digest else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=DEFAULT_OUT)
    ap.add_argument('--allow-ci', action='store_true')
    args = ap.parse_args()

    contract = load(CONTRACT)
    wp02 = contract.get('wp02_parser_contract') if isinstance(contract.get('wp02_parser_contract'), dict) else {}
    grel = str(wp02.get('selected_grammar_path') or '')
    grammar = ROOT / grel if grel else ROOT / '__MISSING__'
    grammar_sha = sha(grammar) if grammar.exists() else None

    preconditions = {
        'linux': platform.system() == 'Linux',
        'ubuntu': osid() == 'ubuntu',
        'not_github_actions': args.allow_ci or os.getenv('GITHUB_ACTIONS', '').lower() != 'true',
        'not_ci': args.allow_ci or os.getenv('CI', '').lower() not in {'1', 'true', 'yes'},
        'selected_grammar_exists': bool(grel) and grammar.exists(),
        'lark_installed': ver('lark') is not None,
        'interegular_installed': ver('interegular') is not None,
    }
    try:
        import interegular  # noqa:F401
    except Exception as exc:
        preconditions['interegular_importable'] = False
        preconditions['interegular_import_error'] = f'{type(exc).__name__}:{exc}'
    else:
        preconditions['interegular_importable'] = True

    gh = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, capture_output=True, check=False)
    gs = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, text=True, capture_output=True, check=False)
    base = {
        'schema_version': '2.1',
        'receipt_id': 'LOCAL_WP02_SELECTED_GRAMMAR_CLOSURE',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'contract': {'path': str(CONTRACT.relative_to(ROOT)), 'sha256': sha(CONTRACT)},
        'selected_grammar': {'path': grel or None, 'sha256': grammar_sha},
        'host': {
            'node': platform.node(),
            'platform': platform.platform(),
            'system': platform.system(),
            'kernel_release': platform.release(),
            'machine': platform.machine(),
            'python': platform.python_version(),
            'os_id': osid(),
            'cpu_logical': os.cpu_count(),
            'memory_total_kib': memory_total_kib(),
        },
        'measurement': {
            'wall_clock': 'time.perf_counter_ns',
            'child_resources': 'resource.getrusage(RUSAGE_CHILDREN)',
            'maxrss_scope': 'cumulative maximum for terminated children in this closure process; platform units preserved',
        },
        'packages': {'lark': ver('lark'), 'interegular': ver('interegular')},
        'repository': {
            'head': gh.stdout.strip() if gh.returncode == 0 else None,
            'dirty': bool(gs.stdout.strip()) if gs.returncode == 0 else None,
        },
        'preconditions': preconditions,
        'authority_invariant': 'model output != execution authority',
        'scope_guard': 'Local strict selected-WP02 evidence only; physical target/apps/FULL_FRANK/WP14 remain mandatory.',
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not all(v is True for k, v in preconditions.items() if k != 'interegular_import_error'):
        base.update({'components': [], 'pass': False, 'failure': 'PRECONDITION_FAILED'})
        args.output.write_text(json.dumps(base, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'pass': False, 'failure': 'PRECONDITION_FAILED', 'preconditions': preconditions}))
        return 3

    specs = []
    if grammar.name == 'D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark':
        specs.append((
            'selection_discriminator',
            ['tools/claycode_v17_declarative_trivia_discriminator.py', '--require-strict', '--output', 'research_entity/claycode/base/receipts/LOCAL_WP02_SELECTION_DISCRIMINATOR.json'],
            RDIR / 'LOCAL_WP02_SELECTION_DISCRIMINATOR.json',
            'disc',
        ))
    specs += [
        ('strict_lalr', ['tools/claycode_strict_lalr_probe.py', '--grammar', grel, '--output', 'research_entity/claycode/base/receipts/LOCAL_WP02_STRICT_LALR.json'], RDIR / 'LOCAL_WP02_STRICT_LALR.json', 'strict'),
        ('frontend', ['tools/claycode_base_frontend_validation.py', '--grammar', grel, '--output', 'research_entity/claycode/base/receipts/LOCAL_WP02_FRONTEND.json'], RDIR / 'LOCAL_WP02_FRONTEND.json', 'pass'),
        ('canonical', ['tools/claycode_base_canonicalizer.py', '--grammar', grel, '--output', 'research_entity/claycode/base/receipts/LOCAL_WP02_CANONICAL.json'], RDIR / 'LOCAL_WP02_CANONICAL.json', 'pass'),
        ('decl_ir_g9', ['tools/claycode_base_ir.py', 'research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay', '--grammar', grel, '--output', 'research_entity/claycode/base/receipts/LOCAL_WP02_IR_G9.json'], RDIR / 'LOCAL_WP02_IR_G9.json', 'decl'),
        ('decl_ir_dialect', ['tools/claycode_base_ir.py', 'research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay', '--grammar', grel, '--output', 'research_entity/claycode/base/receipts/LOCAL_WP02_IR_DIALECT.json'], RDIR / 'LOCAL_WP02_IR_DIALECT.json', 'decl'),
    ]

    rows = []
    for name, argv, receipt_path, kind in specs:
        if receipt_path.exists():
            receipt_path.unlink()
        proc = run(argv)
        doc = load(receipt_path) if receipt_path.exists() else {}
        embedded_path, embedded_sha = embedded_grammar(doc, grel if kind == 'decl' else None)
        if kind == 'disc':
            candidate = doc.get('candidate') if isinstance(doc.get('candidate'), dict) else {}
            embedded_path = str(candidate.get('path') or '')
            embedded_sha = str(candidate.get('sha256') or '')
            semantic_ok = doc.get('pass') is True and doc.get('promotion_allowed') is True and doc.get('counts_as_wp02_pass') is True
        elif kind == 'strict':
            semantic_ok = doc.get('strict_build_ok') is True and not doc.get('conflict_diagnostics')
        elif kind == 'decl':
            semantic_ok = bool(doc.get('declarations'))
        else:
            semantic_ok = doc.get('pass') is True
        bound = embedded_path == grel and embedded_sha == grammar_sha
        row = {
            'name': name,
            **proc,
            'receipt_path': str(receipt_path.relative_to(ROOT)),
            'receipt_exists': receipt_path.exists(),
            'receipt_sha256': sha(receipt_path) if receipt_path.exists() else None,
            'embedded_grammar_path': embedded_path,
            'embedded_grammar_sha256': embedded_sha,
            'grammar_bound': bound,
            'semantic_pass': bool(proc['process_pass'] and receipt_path.exists() and semantic_ok and bound),
        }
        rows.append(row)
        if not row['semantic_pass']:
            break

    prod = run(['tools/claycode_base_canonicalizer_validation.py'], 180)
    production_receipt = ROOT / str(wp02.get('canonicalizer_receipt_path') or 'research_entity/claycode/autonomous/BASE_CANONICALIZER_RECEIPT.json')
    production_doc = load(production_receipt) if production_receipt.exists() else {}
    production_bound = production_doc.get('grammar') == grel
    production_row = {
        **prod,
        'receipt_path': str(production_receipt.relative_to(ROOT)),
        'receipt_exists': production_receipt.exists(),
        'receipt_sha256': sha(production_receipt) if production_receipt.exists() else None,
        'embedded_grammar_path': production_doc.get('grammar'),
        'grammar_bound': production_bound,
        'semantic_pass': bool(prod['process_pass'] and production_doc.get('pass') is True and production_bound),
    }

    passed = len(rows) == len(specs) and all(x['semantic_pass'] for x in rows) and production_row['semantic_pass']
    base.update({'components': rows, 'production_canonicalizer': production_row, 'pass': passed})
    if not passed:
        base['failure'] = 'SELECTED_WP02_COMPONENT_FAILED'
    args.output.write_text(json.dumps(base, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        'pass': passed,
        'selected_grammar': grel,
        'grammar_sha256': grammar_sha,
        'output': str(args.output.relative_to(ROOT)),
        'failed': [x['name'] for x in rows if not x['semantic_pass']] + ([] if production_row['semantic_pass'] else ['production_canonicalizer']),
    }))
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
