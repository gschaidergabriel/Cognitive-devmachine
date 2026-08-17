import inspect

from clayverse import service


def test_tier2_boot_fence_runs_before_any_snapshot_restore_publication():
    source = inspect.getsource(service.main)
    restore = source.index("_snapshot_restore_before_db_open(state_root)")
    boot_fence = source.index("assert_tier2_boot_allowed(state_root, current_pod_uid=pod_uid)")
    assert boot_fence < restore
