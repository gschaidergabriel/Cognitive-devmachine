#!/usr/bin/env python3
"""Final WP14 auditor over one strict Andreas-Ubuntu target adjudication.

The V2 collector is the only component battery that must start from a pristine checkout.
The strict adjudication binds that collector to ten real application results, the full
FRANK handoff, host fingerprint and zero unresolved language counterexamples. WP14 then
independently rechecks per-app receipts, full FRANK and the P0/P1 defect ledger.

Cross-receipt coherence law:
- the strict target adjudication defines the exact release repository commit;
- every real per-application receipt and the full-FRANK receipt must carry the same git_head;
- that release commit must also equal the checkout HEAD executing WP14;
- mixed-commit or stale-but-internally-coherent green receipts fail closed.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json'
STRICT = ROOT / 'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json'
SPEC = ROOT / 'research_entity/claycode/base/BASE_SEMANTIC_FREEZE_V1.json'
FULL_FRANK = ROOT / 'research_entity/claycode/target_receipts/FULL_FRANK_HANDOFF_RECEIPT.json'
DEFECT = ROOT / 'research_entity/claycode/BASE_DEFECT_LEDGER.json'
APP_DIR = ROOT / 'research_entity/claycode/target_receipts/apps'
TARGET = 'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
APPS = [
    'CLI', 'HTTP_WEBSITE', 'DB_SERVICE', 'CONCURRENT_SERVICE', 'GUI_INTERACTIVE',
    'COMPILER_TOOL', 'GPU_ML_NUMERICAL', 'SYSTEM_EFFECT_SANDBOX', 'FRANK_COMPONENT',
    'FULL_FRANK_HANDOFF',
]


def load(path: Path):
    if not path.exists():
        return None, 'MISSING'
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return None, 'INVALID_JSON:' + type(exc).__name__
    return (value, None) if isinstance(value, dict) else (None, 'NOT_OBJECT')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_wp(strict: dict[str, Any], prefix: str):
    wps = strict.get('work_packages') if isinstance(strict.get('work_packages'), dict) else {}
    for name, row in wps.items():
        if str(name).startswith(prefix) and isinstance(row, dict):
            return str(name), row
    return None, None


def receipt_head(data: dict[str, Any] | None) -> str:
    return str((data or {}).get('git_head') or '').strip()


def current_checkout_head() -> str:
    cp = subprocess.run(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, capture_output=True, check=False
    )
    return cp.stdout.strip() if cp.returncode == 0 else ''


def release_commit_is_current(release_commit: str, checkout_head: str) -> bool:
    return bool(release_commit and checkout_head and release_commit == checkout_head)


def real_app(app: str, expected_head: str):
    path = APP_DIR / f'{app}.json'
    data, error = load(path)
    reasons: list[str] = []
    observed_head = receipt_head(data)
    if error:
        reasons.append(error)
    if data:
        if data.get('pass') is not True:
            reasons.append('PASS_NOT_TRUE')
        if data.get('target_host') != TARGET:
            reasons.append('WRONG_TARGET_HOST')
        if data.get('evidence_class') != 'ANDREAS_UBUNTU_REAL_APPLICATION':
            reasons.append('NOT_REAL_APPLICATION_EVIDENCE')
        if data.get('model_output_is_execution_authority') is not False:
            reasons.append('AUTHORITY_INVARIANT_NOT_PROVEN')
        if not observed_head:
            reasons.append('GIT_HEAD_MISSING')
        elif not expected_head:
            reasons.append('EXPECTED_RELEASE_GIT_HEAD_MISSING')
        elif observed_head != expected_head:
            reasons.append('GIT_HEAD_MISMATCH')
        for key in ('source_sha256', 'artifact_sha256', 'expected', 'observed', 'positive_test', 'negative_test'):
            if key not in data:
                reasons.append('MISSING_FIELD:' + key)
        if not isinstance(data.get('positive_test'), dict) or data['positive_test'].get('pass') is not True:
            reasons.append('POSITIVE_TEST_NOT_PASS')
        if not isinstance(data.get('negative_test'), dict) or data['negative_test'].get('pass') is not True:
            reasons.append('NEGATIVE_TEST_NOT_PASS')
    return not reasons, {
        'app': app,
        'path': str(path.relative_to(ROOT)),
        'sha256': sha(path) if path.exists() else None,
        'git_head': observed_head or None,
        'expected_git_head': expected_head or None,
        'git_head_match': bool(observed_head and expected_head and observed_head == expected_head),
        'reasons': reasons,
    }


def full_frank(expected_head: str):
    data, error = load(FULL_FRANK)
    reasons: list[str] = []
    observed_head = receipt_head(data)
    if error:
        reasons.append(error)
    if data:
        if data.get('pass') is not True:
            reasons.append('PASS_NOT_TRUE')
        if data.get('target_host') != TARGET:
            reasons.append('WRONG_TARGET_HOST')
        if data.get('evidence_class') != 'ANDREAS_UBUNTU_FULL_FRANK_HANDOFF':
            reasons.append('WRONG_EVIDENCE_CLASS')
        if data.get('semantic_escape_hatch_used') is not False:
            reasons.append('SEMANTIC_ESCAPE_HATCH')
        if data.get('model_output_is_execution_authority') is not False:
            reasons.append('AUTHORITY_INVARIANT_NOT_PROVEN')
        if data.get('h2_h3_handoff_ready') is not True:
            reasons.append('H2_H3_NOT_READY')
        if not observed_head:
            reasons.append('GIT_HEAD_MISSING')
        elif not expected_head:
            reasons.append('EXPECTED_RELEASE_GIT_HEAD_MISSING')
        elif observed_head != expected_head:
            reasons.append('GIT_HEAD_MISMATCH')
        for key in ('frank_input_sha256', 'clay_source_sha256', 'artifact_sha256', 'expected', 'observed', 'production_chain_receipts'):
            if key not in data:
                reasons.append('MISSING_FIELD:' + key)
    return not reasons, {
        'path': str(FULL_FRANK.relative_to(ROOT)),
        'sha256': sha(FULL_FRANK) if FULL_FRANK.exists() else None,
        'git_head': observed_head or None,
        'expected_git_head': expected_head or None,
        'git_head_match': bool(observed_head and expected_head and observed_head == expected_head),
        'reasons': reasons,
    }


def defects():
    data, error = load(DEFECT)
    if error:
        return False, {'path': str(DEFECT.relative_to(ROOT)), 'reasons': [error]}
    rows = data.get('defects') if isinstance(data.get('defects'), list) else []
    open_high = [
        d for d in rows
        if isinstance(d, dict)
        and d.get('severity') in {'P0', 'P1'}
        and d.get('status') not in {'CLOSED', 'REFUTED', 'NOT_APPLICABLE'}
    ]
    explicit_counts_ok = (
        data.get('open_p0', len([d for d in open_high if d.get('severity') == 'P0'])) == 0
        and data.get('open_p1', len([d for d in open_high if d.get('severity') == 'P1'])) == 0
    )
    return not open_high and explicit_counts_ok, {
        'path': str(DEFECT.relative_to(ROOT)),
        'sha256': sha(DEFECT),
        'open_p0_p1': open_high,
        'open_p0': data.get('open_p0'),
        'open_p1': data.get('open_p1'),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    strict, strict_error = load(STRICT)
    spec, spec_error = load(SPEC)
    wp: dict[str, dict[str, Any]] = {}
    strict_commit = str((strict or {}).get('repository_commit') or '').strip()
    checkout_head = current_checkout_head()
    strict_commit_fresh = release_commit_is_current(strict_commit, checkout_head)

    wp1 = bool(
        spec
        and spec_error is None
        and isinstance(spec.get('decision'), dict)
        and spec['decision'].get('CC-WP-01-SPEC-FREEZE') == 'PASS'
        and spec.get('unresolved_language_counterexamples') == []
    )
    wp['CC-WP-01-SPEC-FREEZE'] = {
        'pass': wp1,
        'evidence': str(SPEC.relative_to(ROOT)),
        'sha256': sha(SPEC) if SPEC.exists() else None,
        'freeze_status': spec.get('status') if spec else None,
        'decision': (spec.get('decision') or {}).get('CC-WP-01-SPEC-FREEZE') if spec else None,
        'reason': None if wp1 else (spec_error or 'SPEC_DECISION_NOT_PASS'),
    }

    strict_identity = bool(
        strict
        and strict_error is None
        and strict.get('overall_pass') is True
        and strict.get('target_host') == TARGET
        and strict_commit_fresh
        and isinstance(strict.get('host_fingerprint'), dict)
        and all(strict['host_fingerprint'].get(k) for k in ('uname', 'architecture', 'python_version', 'c_compiler_version'))
        and strict.get('collector_clean_target_attestation_pass') is True
    )

    for i in list(range(2, 10)) + [11, 12]:
        prefix = f'CC-WP-{i:02d}-'
        name, row = find_wp(strict or {}, prefix)
        ok = strict_identity and bool(row and row.get('pass') is True)
        wp[name or prefix.rstrip('-')] = {
            'pass': ok,
            'strict_target_receipt': str(STRICT.relative_to(ROOT)),
            'strict_target_receipt_sha256': sha(STRICT) if STRICT.exists() else None,
            'strict_work_package': row,
        }

    app_rows = [real_app(app, strict_commit) for app in APPS]
    app_commit_coherence = bool(strict_commit) and all(
        row.get('git_head_match') is True for _, row in app_rows
    )
    _, strict_wp10 = find_wp(strict or {}, 'CC-WP-10-')
    wp10_ok = (
        strict_identity
        and bool(strict_wp10 and strict_wp10.get('pass') is True)
        and all(ok for ok, _ in app_rows)
        and app_commit_coherence
    )
    wp['CC-WP-10-GENERAL-APP-SUITE'] = {
        'pass': wp10_ok,
        'repository_commit': strict_commit or None,
        'checkout_head': checkout_head or None,
        'release_commit_freshness_pass': strict_commit_fresh,
        'cross_receipt_commit_coherence_pass': app_commit_coherence,
        'applications': [row for _, row in app_rows],
    }

    frank_ok, frank_row = full_frank(strict_commit)
    _, strict_wp13 = find_wp(strict or {}, 'CC-WP-13-')
    wp13_ok = strict_identity and bool(strict_wp13 and strict_wp13.get('pass') is True) and frank_ok
    wp['CC-WP-13-HARNESS-HANDOFF'] = {
        'pass': wp13_ok,
        'repository_commit': strict_commit or None,
        'checkout_head': checkout_head or None,
        'release_commit_freshness_pass': strict_commit_fresh,
        'cross_receipt_commit_coherence_pass': frank_row.get('git_head_match') is True,
        'strict_work_package': strict_wp13,
        'full_frank': frank_row,
    }

    prior_ok = all(
        any(name.startswith(f'CC-WP-{i:02d}-') and row.get('pass') is True for name, row in wp.items())
        for i in range(1, 14)
    )
    defects_ok, defect_row = defects()
    cross_receipt_commit_coherence = bool(
        strict_commit
        and app_commit_coherence
        and frank_row.get('git_head_match') is True
    )
    wp14_ok = prior_ok and defects_ok and cross_receipt_commit_coherence and strict_commit_fresh
    wp['CC-WP-14-BASE-AUDIT'] = {
        'pass': wp14_ok,
        'wp01_13_all_pass': prior_ok,
        'zero_open_p0_p1': defects_ok,
        'cross_receipt_commit_coherence_pass': cross_receipt_commit_coherence,
        'release_commit_freshness_pass': strict_commit_fresh,
        'repository_commit': strict_commit or None,
        'checkout_head': checkout_head or None,
        'defect_ledger': defect_row,
    }

    evidence_paths = [STRICT, SPEC, FULL_FRANK, DEFECT] + [APP_DIR / f'{app}.json' for app in APPS]
    evidence_hashes = {
        str(p.relative_to(ROOT)): sha(p)
        for p in evidence_paths
        if p.exists()
    }
    failed = [name for name, row in wp.items() if row.get('pass') is not True]
    manifest = {
        'schema_version': '1.4',
        'manifest': 'CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'target_host': TARGET,
        'repository_commit': strict_commit or None,
        'checkout_head': checkout_head or None,
        'release_commit_freshness_pass': strict_commit_fresh,
        'cross_receipt_commit_coherence_pass': cross_receipt_commit_coherence,
        'authority_invariant': 'model output != execution authority',
        'strict_target_receipt': str(STRICT.relative_to(ROOT)),
        'strict_target_receipt_error': strict_error,
        'strict_target_identity_pass': strict_identity,
        'work_packages': wp,
        'failed_work_packages': failed,
        'evidence_sha256': evidence_hashes,
        'general_purpose_gate_pass': not failed,
        'claycode_release_gate_pass': not failed,
        'promotion_allowed': not failed,
        'scope_guard': (
            'One clean target collector -> strict target adjudication -> independent per-app/full-FRANK/P0-P1 WP14 audit. '
            'Every target application and full-FRANK receipt must bind the exact strict target repository commit, and that '
            'commit must equal the checkout HEAD executing WP14. Hosted/proxy, mixed-commit, or stale release evidence cannot promote BASE.'
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        'pass': not failed,
        'repository_commit': strict_commit or None,
        'checkout_head': checkout_head or None,
        'release_commit_freshness_pass': strict_commit_fresh,
        'cross_receipt_commit_coherence_pass': cross_receipt_commit_coherence,
        'failed_work_packages': failed,
        'output': str(args.output.relative_to(ROOT)) if args.output.is_relative_to(ROOT) else str(args.output),
    }))
    return 0 if not failed else 2


if __name__ == '__main__':
    raise SystemExit(main())
