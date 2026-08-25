import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'tools' / 'trigger2_qwen35_checkpoint_input_identity_probe_v1.py'
spec = importlib.util.spec_from_file_location('probe', P)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def _identity(tmp_path: Path):
    (tmp_path / 'model.safetensors').write_bytes(b'weights')
    (tmp_path / 'config.json').write_text('{}', encoding='utf-8')
    return {
        'candidate_id': 'C',
        'identity_complete': True,
        'file_manifest': [
            {'path': 'model.safetensors', 'size': 7, 'sha256': probe._sha256_file(tmp_path / 'model.safetensors')},
            {'path': 'config.json', 'size': 2, 'sha256': probe._sha256_file(tmp_path / 'config.json')},
        ],
    }


def test_verify_manifest_exact_and_mutation(tmp_path):
    ident = _identity(tmp_path)
    ok, bad = probe._verify_manifest(tmp_path, ident)
    assert ok and bad == []
    (tmp_path / 'config.json').write_text('{"x":1}', encoding='utf-8')
    ok, bad = probe._verify_manifest(tmp_path, ident)
    assert not ok
    assert {x['failure'] for x in bad} >= {'SIZE_MISMATCH', 'SHA256_MISMATCH'}


def test_compare_consumed_requires_every_weight_shard(tmp_path):
    ident = _identity(tmp_path)
    r = probe._compare_consumed_to_manifest(tmp_path, ident, ['config.json'])
    assert not r['pass']
    assert r['missing_weight_shards'] == ['model.safetensors']
    r = probe._compare_consumed_to_manifest(tmp_path, ident, ['config.json', 'model.safetensors'])
    assert r['pass']


def test_compare_consumed_rejects_unmanifested_open(tmp_path):
    ident = _identity(tmp_path)
    (tmp_path / 'mystery.bin').write_bytes(b'x')
    r = probe._compare_consumed_to_manifest(tmp_path, ident, ['model.safetensors', 'mystery.bin'])
    assert not r['pass']
    assert r['unknown_opened_local_files'] == ['mystery.bin']


def test_parse_strace_only_accepts_absolute_files_under_local_dir(tmp_path):
    a = tmp_path / 'model.safetensors'
    a.write_bytes(b'w')
    outside = tmp_path.parent / 'outside.txt'
    outside.write_text('x', encoding='utf-8')
    trace = (
        f'1 openat(AT_FDCWD, "{a}", O_RDONLY|O_CLOEXEC) = 3\n'
        f'1 openat(AT_FDCWD, "{outside}", O_RDONLY) = 4\n'
        '1 openat(AT_FDCWD, "relative.json", O_RDONLY) = 5\n'
    )
    assert probe._parse_strace_opened_paths(trace, tmp_path) == ['model.safetensors']


def test_manifest_duplicate_path_fails_closed(tmp_path):
    ident = _identity(tmp_path)
    ident['file_manifest'].append(dict(ident['file_manifest'][0]))
    try:
        probe._manifest_map(ident)
    except probe.ProbeError as exc:
        assert str(exc) == 'IDENTITY_FILE_MANIFEST_DUPLICATE_PATH'
    else:
        raise AssertionError('expected ProbeError')


def test_parse_strace_preserves_snapshot_symlink_member_path(tmp_path):
    blobs = tmp_path / 'blobs'
    snap = tmp_path / 'snapshot'
    blobs.mkdir()
    snap.mkdir()
    target = blobs / 'abc'
    target.write_bytes(b'weights')
    link = snap / 'model.safetensors'
    link.symlink_to(target)
    trace = f'1 openat(AT_FDCWD, "{link}", O_RDONLY|O_CLOEXEC) = 3\n'
    assert probe._parse_strace_opened_paths(trace, snap) == ['model.safetensors']
