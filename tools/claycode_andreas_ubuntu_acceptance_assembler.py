#!/usr/bin/env python3
"""Strict ClayCode BASE adjudication for Andreas' Ubuntu target.

The V2 runner is only a collector. This script combines that collector with the real
10-application target suite, owner-local host identity and the actual full FRANK handoff.
It writes the contract's STRICT receipt only when every hard rule passes. Hosted/proxy
receipts can never substitute for target execution.

CC-WP-02 grammar identity is selected only by ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json.
The collector's claim is insufficient on its own: strict-LALR, full-corpus frontend and
the active production canonicalizer must all identify the exact same selected grammar.

Cross-receipt coherence law:
- the clean target collector defines the exact repository commit under adjudication;
- every real per-application receipt and the full-FRANK production receipt must carry
  that same git_head;
- mixed-commit PASS receipts fail closed before a STRICT target receipt can be emitted.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
CONTRACT = ROOT / 'research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json'
APPS = ROOT / 'research_entity/claycode/target/ANDREAS_UBUNTU_APPLICATIONS.json'
APP_RECEIPT_DIR = ROOT / 'research_entity/claycode/target_receipts/apps'
FULL_FRANK = ROOT / 'research_entity/claycode/target/FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT.json'
COUNTEREXAMPLES = ROOT / 'research_entity/claycode/base/UNRESOLVED_LANGUAGE_COUNTEREXAMPLES.json'
DIAGNOSTIC = ROOT / 'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_ACCEPTANCE_ASSEMBLY_DIAGNOSTIC.json'
COMPILER = ROOT / 'tools/claycode_base_compiler.py'
EFFECT_PIPELINE = ROOT / 'tools/claycode_base_effect_pipeline.py'
BASE_PHASE_RECEIPTS = {
    'typed_ir': 'research_entity/claycode/autonomous/WP03_TYPED_IR_RECEIPT.json',
    'effect_pipeline': 'research_entity/claycode/autonomous/BASE_EFFECT_PIPELINE_RECEIPT.json',
    'pure_native': 'research_entity/claycode/autonomous/BASE_PURE_TOOLCHAIN_RECEIPT.json',
    'int_division': 'research_entity/claycode/autonomous/BASE_INT_DIVISION_REGRESSION_RECEIPT.json',
    'package_link': 'research_entity/claycode/autonomous/BASE_PACKAGE_LINK_RECEIPT.json',
    'runtime': 'research_entity/claycode/autonomous/BASE_RUNTIME_CAPABILITY_RECEIPT.json',
    'runtime_v04_hardening': 'research_entity/claycode/autonomous/BASE_RUNTIME_V04_HARDENING_RECEIPT.json',
    'compiler_mainline_runtime_bridge': 'research_entity/claycode/autonomous/BASE_COMPILER_MAINLINE_RUNTIME_BRIDGE_RECEIPT.json',
    'concurrency_cancellation_error': 'research_entity/claycode/autonomous/BASE_CONCURRENCY_CANCELLATION_RECEIPT.json',
    'fuzz': 'research_entity/claycode/autonomous/BASE_FUZZ_CONFORMANCE_RECEIPT.json',
    'corpus': 'research_entity/claycode/corpus/base_v1/CORPUS_MANIFEST.json',
    'frank': 'research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_SCORE_HANDOFF_RECEIPT.json',
}
WP_PHASES = {
    'CC-WP-02-PARSER-CANON': ['strict_lalr', 'frontend', 'canonicalizer'],
    'CC-WP-03-IR-TYPES': ['typed_ir', 'pure_native'],
    'CC-WP-04-TYPE-EFFECT': ['effect_pipeline', 'compiler_mainline_runtime_bridge'],
    'CC-WP-05-EVALUATOR': ['pure_native', 'int_division'],
    'CC-WP-06-COMPILER-LOWERING': ['pure_native', 'int_division', 'compiler_mainline_runtime_bridge'],
    'CC-WP-07-RUNTIME-ABI-FFI': ['package_link', 'runtime', 'runtime_v04_hardening', 'compiler_mainline_runtime_bridge'],
    'CC-WP-08-STDLIB-SDK': ['package_link', 'runtime', 'runtime_v04_hardening', 'compiler_mainline_runtime_bridge'],
    'CC-WP-09-CONCURRENCY-MEMORY': ['runtime', 'concurrency_cancellation_error'],
    'CC-WP-10-GENERAL-APP-SUITE': [],
    'CC-WP-11-FUZZ-CONFORMANCE': ['fuzz'],
    'CC-WP-12-CORPUS-HELDOUT': ['corpus'],
    'CC-WP-13-HARNESS-HANDOFF': ['frank'],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def host_identity() -> tuple[bool, dict[str, Any]]:
    cp = subprocess.run(
        [sys.executable, 'tools/claycode_target_host_identity.py', 'verify', '--json'],
        cwd=ROOT, text=True, capture_output=True, timeout=15, check=False,
    )
    try:
        data = json.loads(cp.stdout)
    except Exception:
        data = {
            'verified': False,
            'errors': ['HOST_IDENTITY_OUTPUT_INVALID'],
            'stdout_tail': cp.stdout[-1000:],
            'stderr_tail': cp.stderr[-1000:],
        }
    return cp.returncode == 0 and data.get('verified') is True, data


def phase_map(collector: dict) -> dict[str, dict]:
    return {
        str(x.get('phase')): x
        for x in collector.get('phases', [])
        if isinstance(x, dict) and x.get('phase')
    }


def phase_evidence(name: str, row: dict, phase_receipts: dict[str, str]) -> dict[str, Any]:
    rel = phase_receipts.get(name)
    path = ROOT / rel if rel else None
    ev = {
        'test_id': name,
        'argv': row.get('argv'),
        'process_pass': row.get('process_pass'),
        'semantic_pass': row.get('semantic_pass'),
        'stdout_sha256': row.get('stdout_sha256'),
        'stderr_sha256': row.get('stderr_sha256'),
        'receipt_path': rel,
        'receipt_sha256': sha(path) if path and path.exists() else None,
        'receipt_exists': bool(path and path.exists()),
    }
    if path and path.exists() and path.suffix == '.json':
        try:
            data = load(path)
            if name in {'strict_lalr', 'frontend'}:
                ev['grammar_path'] = data.get('grammar_path')
                ev['grammar_sha256'] = data.get('grammar_sha256')
            elif name == 'canonicalizer':
                ev['grammar_path'] = data.get('grammar')
        except Exception:
            ev['receipt_parse_error'] = True
    return ev


def real_app_receipt(app: str, expected_head: str) -> tuple[bool, dict[str, Any]]:
    path = APP_RECEIPT_DIR / f'{app}.json'
    reasons: list[str] = []
    data: dict[str, Any] = {}
    if not path.exists():
        reasons.append('MISSING')
    else:
        try:
            data = load(path)
        except Exception as exc:
            reasons.append('INVALID_JSON:' + type(exc).__name__)
    observed_head = str(data.get('git_head') or '').strip()
    if data:
        if data.get('pass') is not True:
            reasons.append('PASS_NOT_TRUE')
        if data.get('target_host') != TARGET:
            reasons.append('WRONG_TARGET_HOST')
        if data.get('evidence_class') != 'ANDREAS_UBUNTU_REAL_APPLICATION':
            reasons.append('WRONG_EVIDENCE_CLASS')
        if data.get('model_output_is_execution_authority') is not False:
            reasons.append('AUTHORITY_INVARIANT_NOT_PROVEN')
        if not observed_head:
            reasons.append('GIT_HEAD_MISSING')
        elif not expected_head:
            reasons.append('EXPECTED_COLLECTOR_GIT_HEAD_MISSING')
        elif observed_head != expected_head:
            reasons.append('GIT_HEAD_MISMATCH')
    return not reasons, {
        'app': app,
        'path': str(path.relative_to(ROOT)),
        'sha256': sha(path) if path.exists() else None,
        'git_head': observed_head or None,
        'expected_git_head': expected_head or None,
        'git_head_match': bool(observed_head and expected_head and observed_head == expected_head),
        'reasons': reasons,
    }


def main() -> int:
    failures: list[str] = []
    if not CONTRACT.exists():
        raise SystemExit('target receipt contract missing')
    contract = load(CONTRACT)
    collector = ROOT / contract.get('collector_receipt_path', '')
    final = ROOT / contract.get('expected_receipt_path', '')
    wp02_contract = contract.get('wp02_parser_contract') if isinstance(contract.get('wp02_parser_contract'), dict) else {}
    wp02_grammar_rel = str(wp02_contract.get('selected_grammar_path') or '')
    wp02_grammar = ROOT / wp02_grammar_rel if wp02_grammar_rel else ROOT / '__MISSING_WP02_GRAMMAR__'
    phase_receipts = dict(BASE_PHASE_RECEIPTS)
    phase_receipts.update({
        'strict_lalr': str(wp02_contract.get('strict_receipt_path') or ''),
        'frontend': str(wp02_contract.get('frontend_receipt_path') or ''),
        'canonicalizer': str(wp02_contract.get('canonicalizer_receipt_path') or ''),
    })
    if not wp02_grammar_rel:
        failures.append('WP02_SELECTED_GRAMMAR_PATH_MISSING')
    if not all(phase_receipts.get(x) for x in ('strict_lalr', 'frontend', 'canonicalizer')):
        failures.append('WP02_RECEIPT_PATH_CONTRACT_INCOMPLETE')
    for path in (collector, APPS, COUNTEREXAMPLES, COMPILER, EFFECT_PIPELINE, wp02_grammar):
        if not path.exists():
            failures.append('MISSING:' + (str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)))

    c = load(collector) if collector.exists() else {}
    apps_doc = load(APPS) if APPS.exists() else {}
    ledger = load(COUNTEREXAMPLES) if COUNTEREXAMPLES.exists() else {}
    frank = load(FULL_FRANK) if FULL_FRANK.exists() else {}
    repo = (c.get('repo_head') or {}).get('stdout_tail') if isinstance(c.get('repo_head'), dict) else None
    repo = (repo or '').strip()
    if not repo:
        failures.append('REPOSITORY_COMMIT_MISSING')

    host_ok, host = host_identity()
    if not host_ok:
        failures.append('OWNER_REGISTERED_TARGET_HOST_NOT_VERIFIED')
    if contract.get('target_host') != TARGET:
        failures.append('CONTRACT_TARGET_MISMATCH')
    if c.get('target_host') != TARGET:
        failures.append('COLLECTOR_TARGET_MISMATCH')
    host_checks = c.get('target_host_checks') or {}
    collector_attested = bool(host_checks) and all(host_checks.values())
    if not collector_attested:
        failures.append('COLLECTOR_CLEAN_TARGET_ATTESTATION_NOT_PASS')
    if c.get('target_component_battery_pass') is not True:
        failures.append('COLLECTOR_COMPONENT_BATTERY_NOT_PASS')

    runtime_v04 = c.get('runtime_v04_hardening_pass') is True
    bridge = c.get('compiler_mainline_runtime_bridge_pass') is True
    if not runtime_v04:
        failures.append('RUNTIME_V04_HARDENING_NOT_PASS')
    if not bridge:
        failures.append('COMPILER_MAINLINE_RUNTIME_BRIDGE_NOT_PASS')
    if c.get('concurrency_cancellation_error_pass') is not True:
        failures.append('CONCURRENCY_CANCELLATION_ERROR_NOT_PASS')
    if c.get('int_division_pass') is not True:
        failures.append('CHECKED_INT_DIVISION_NOT_PASS')

    bad_pattern = 'int(left / right) if isinstance(left, int) and isinstance(right, int)'
    for path in (COMPILER, EFFECT_PIPELINE):
        if path.exists() and bad_pattern in path.read_text(encoding='utf-8'):
            failures.append('KNOWN_FLOAT_MEDIATED_INT_DIVISION:' + str(path.relative_to(ROOT)))

    unresolved = ledger.get('unresolved_language_counterexamples')
    if unresolved is None:
        failures.append('COUNTEREXAMPLE_LEDGER_MISSING_FIELD')
        unresolved = []
    elif unresolved:
        failures.append('UNRESOLVED_LANGUAGE_COUNTEREXAMPLES:' + str(len(unresolved)))

    expected_wp02_sha = sha(wp02_grammar) if wp02_grammar.exists() else None
    collector_wp02 = c.get('wp02_parser_contract') if isinstance(c.get('wp02_parser_contract'), dict) else {}
    collector_wp02_bound = bool(
        expected_wp02_sha
        and collector_wp02.get('grammar_path') == wp02_grammar_rel
        and collector_wp02.get('grammar_sha256') == expected_wp02_sha
        and collector_wp02.get('contract_path') == str(CONTRACT.relative_to(ROOT))
    )
    if not collector_wp02_bound:
        failures.append('COLLECTOR_WP02_SELECTED_GRAMMAR_BINDING_NOT_PASS')

    names = contract.get('required_applications', [])
    app_receipt_rows = [real_app_receipt(name, repo) for name in names]
    app_commit_coherence = bool(repo) and bool(app_receipt_rows) and all(ok for ok, _ in app_receipt_rows)
    if not app_commit_coherence:
        failures.append('REAL_APPLICATION_RECEIPT_COMMIT_COHERENCE_NOT_PASS')

    frank_head = str(frank.get('git_head') or '').strip()
    frank_commit_coherence = bool(repo and frank_head and frank_head == repo)
    if not frank_commit_coherence:
        failures.append('FULL_FRANK_RECEIPT_COMMIT_COHERENCE_NOT_PASS')

    phases = phase_map(c)
    work_packages: dict[str, Any] = {}
    for wp in contract.get('required_work_packages', []):
        required = WP_PHASES.get(wp)
        evidence: list[dict[str, Any]] = []
        ok = True
        if required is None:
            failures.append('UNMAPPED_WORK_PACKAGE:' + wp)
            required = []
            ok = False
        for name in required:
            row = phases.get(name)
            if not row:
                evidence.append({'test_id': name, 'missing': True})
                ok = False
                continue
            ev = phase_evidence(name, row, phase_receipts)
            evidence.append(ev)
            ok = ok and row.get('semantic_pass') is True and row.get('process_pass') is True and ev['receipt_exists'] and bool(ev['receipt_sha256'])

        if wp == 'CC-WP-02-PARSER-CANON':
            strict_ev = next((x for x in evidence if x.get('test_id') == 'strict_lalr'), {})
            frontend_ev = next((x for x in evidence if x.get('test_id') == 'frontend'), {})
            canonical_ev = next((x for x in evidence if x.get('test_id') == 'canonicalizer'), {})
            grammar_bind_ok = bool(
                expected_wp02_sha and collector_wp02_bound
                and strict_ev.get('grammar_path') == wp02_grammar_rel and strict_ev.get('grammar_sha256') == expected_wp02_sha
                and frontend_ev.get('grammar_path') == wp02_grammar_rel and frontend_ev.get('grammar_sha256') == expected_wp02_sha
                and canonical_ev.get('grammar_path') == wp02_grammar_rel
            )
            evidence.append({
                'test_id': 'WP02_SELECTED_GRAMMAR_IDENTITY',
                'expected_grammar_path': wp02_grammar_rel,
                'expected_grammar_sha256': expected_wp02_sha,
                'collector_bound': collector_wp02_bound,
                'pass': grammar_bind_ok,
            })
            ok = ok and grammar_bind_ok

        if wp == 'CC-WP-10-GENERAL-APP-SUITE':
            rows = apps_doc.get('applications') if isinstance(apps_doc.get('applications'), dict) else {}
            aggregate_ok = apps_doc.get('target_host') == TARGET and all(
                isinstance(rows.get(name), dict) and rows[name].get('pass') is True
                for name in names
            )
            evidence.append({
                'test_id': 'tools/claycode_base_target_application_suite.py',
                'receipt_path': str(APPS.relative_to(ROOT)),
                'receipt_sha256': sha(APPS) if APPS.exists() else None,
                'all_ten_real_apps_pass': aggregate_ok,
            })
            evidence.append({
                'test_id': 'REAL_APPLICATION_RECEIPT_COMMIT_COHERENCE',
                'expected_git_head': repo or None,
                'pass': app_commit_coherence,
                'receipts': [detail for _, detail in app_receipt_rows],
            })
            ok = ok and aggregate_ok and app_commit_coherence

        if wp == 'CC-WP-13-HARNESS-HANDOFF':
            frank_ok = bool(frank) and frank.get('pass') is True and frank.get('target_host') == TARGET and frank.get('h2_h3_handoff_ready') is True and frank.get('semantic_escape_hatches') in ([], None, 0)
            evidence.append({
                'test_id': 'FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT',
                'receipt_path': str(FULL_FRANK.relative_to(ROOT)),
                'receipt_sha256': sha(FULL_FRANK) if FULL_FRANK.exists() else None,
                'full_stateful_handoff_pass': frank_ok,
                'git_head': frank_head or None,
                'expected_git_head': repo or None,
                'git_head_match': frank_commit_coherence,
            })
            ok = ok and frank_ok and frank_commit_coherence

        work_packages[wp] = {'pass': bool(ok), 'evidence': evidence}
        if not ok:
            failures.append('WORK_PACKAGE_NOT_ACCEPTED:' + wp)

    applications = apps_doc.get('applications') if isinstance(apps_doc.get('applications'), dict) else {}
    for app in names:
        row = applications.get(app)
        if not isinstance(row, dict):
            failures.append('APPLICATION_MISSING:' + app)
            continue
        for field in contract.get('application_row_required', []):
            if field not in row:
                failures.append(f'APPLICATION_FIELD_MISSING:{app}:{field}')
        if row.get('pass') is not True:
            failures.append('APPLICATION_NOT_PASS:' + app)
        if row.get('authority_boundary_preserved') is not True:
            failures.append('APPLICATION_AUTHORITY_BOUNDARY_FAIL:' + app)

    gui = applications.get('GUI_INTERACTIVE') or {}
    if (gui.get('observed') or {}).get('io_mode') != 'REAL_KERNEL_FD_EVENT_LOOP':
        failures.append('GUI_NOT_REAL_KERNEL_EVENT_LOOP')
    full_app = applications.get('FULL_FRANK_HANDOFF') or {}
    if full_app.get('pass') is not True or not frank:
        failures.append('FULL_FRANK_APP_NOT_PRODUCTION_HANDOFF')

    frank_handoff = {
        'pass': bool(frank.get('pass') is True and frank.get('h2_h3_handoff_ready') is True and frank.get('semantic_escape_hatches') in ([], None, 0) and frank_commit_coherence),
        'git_head': frank_head or None,
        'repository_commit_match': frank_commit_coherence,
        'frozen_frank_source_hashes': frank.get('frozen_frank_source_hashes'),
        'claycode_source_hashes': frank.get('claycode_source_hashes'),
        'production_chain_receipts': frank.get('production_chain_receipts'),
        'semantic_escape_hatches': frank.get('semantic_escape_hatches'),
        'h2_h3_handoff_ready': frank.get('h2_h3_handoff_ready') is True,
    }
    for field in contract.get('frank_handoff_required', []):
        if field not in frank_handoff or frank_handoff[field] is None:
            failures.append('FRANK_FIELD_MISSING:' + field)
    if not frank_handoff['pass']:
        failures.append('FULL_FRANK_HANDOFF_NOT_ACCEPTED')

    host_fp = host.get('host_fingerprint') if isinstance(host.get('host_fingerprint'), dict) else {}
    for field in contract.get('host_fingerprint_required', []):
        if not host_fp.get(field):
            failures.append('HOST_FINGERPRINT_FIELD_MISSING:' + field)

    cross_receipt_commit_coherence = bool(repo and app_commit_coherence and frank_commit_coherence)
    receipt = {
        'schema_version': '1.4',
        'target_host': TARGET,
        'repository_commit': repo,
        'cross_receipt_commit_coherence_pass': cross_receipt_commit_coherence,
        'real_application_receipt_commit_coherence_pass': app_commit_coherence,
        'full_frank_receipt_commit_coherence_pass': frank_commit_coherence,
        'host_fingerprint': host_fp,
        'compiler_runtime': {
            'compiler_sha256': sha(COMPILER) if COMPILER.exists() else None,
            'effect_pipeline_sha256': sha(EFFECT_PIPELINE) if EFFECT_PIPELINE.exists() else None,
            'collector_sha256': sha(collector) if collector.exists() else None,
            'application_suite_sha256': sha(APPS) if APPS.exists() else None,
            'versions': apps_doc.get('compiler_runtime'),
        },
        'wp02_parser_contract': {
            'grammar_path': wp02_grammar_rel,
            'grammar_sha256': expected_wp02_sha,
            'collector_bound': collector_wp02_bound,
            'contract_selected': True,
        },
        'work_packages': work_packages,
        'applications': applications,
        'frank_handoff': frank_handoff,
        'unresolved_language_counterexamples': unresolved,
        'runtime_v04_hardening_pass': runtime_v04,
        'compiler_mainline_runtime_bridge_pass': bridge,
        'collector_clean_target_attestation_pass': collector_attested,
        'overall_pass': not failures and cross_receipt_commit_coherence,
        'assembled_at': datetime.now(timezone.utc).isoformat(),
        'contract_path': str(CONTRACT.relative_to(ROOT)),
        'contract_sha256': sha(CONTRACT),
        'collector_receipt_path': str(collector.relative_to(ROOT)),
        'authority_invariant': 'model_output != execution_authority',
    }
    for field in contract.get('required_top_level', []):
        if field not in receipt:
            failures.append('STRICT_TOP_LEVEL_FIELD_MISSING:' + field)
    if not cross_receipt_commit_coherence:
        failures.append('CROSS_RECEIPT_COMMIT_COHERENCE_NOT_PASS')
    receipt['overall_pass'] = not failures

    diagnostic = {
        'schema_version': '1.4',
        'pass': not failures,
        'failures': failures,
        'candidate': receipt,
    }
    DIAGNOSTIC.parent.mkdir(parents=True, exist_ok=True)
    DIAGNOSTIC.write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    if failures:
        if final.exists():
            final.unlink()
        print(json.dumps({'overall_pass': False, 'failures': failures, 'diagnostic': str(DIAGNOSTIC.relative_to(ROOT))}, ensure_ascii=False))
        return 2

    final.parent.mkdir(parents=True, exist_ok=True)
    final.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'overall_pass': True, 'receipt': str(final.relative_to(ROOT)), 'sha256': sha(final)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
