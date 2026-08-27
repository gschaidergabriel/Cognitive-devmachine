from __future__ import annotations


def _version_tuple(version: str) -> tuple[int, int, int]:
    parts = version.split('.')
    if len(parts) < 3:
        raise ValueError('need full SQLite x.y.z version')
    return tuple(int(x) for x in parts[:3])


def evaluate_wal_reset_safety(
    *,
    sqlite_version: str,
    journal_mode: str,
    verified_backport: bool = False,
    machine_checked_topology_excludes_race: bool = False,
) -> str:
    """Research candidate for Frank v0.1 UnifiedDB release gating.

    This checks only the upstream 2026 SQLite WAL-reset bug class. It is not a
    general SQLite security/correctness certification.
    """
    v = _version_tuple(sqlite_version)
    if journal_mode.upper() != 'WAL':
        return 'PASS_WAL_RESET_NOT_APPLICABLE'
    if verified_backport:
        return 'PASS_VERIFIED_BACKPORT'
    if v in {(3, 44, 6), (3, 50, 7)} or v >= (3, 51, 3):
        return 'PASS_UPSTREAM_FIXED_VERSION'
    if machine_checked_topology_excludes_race:
        return 'CONDITIONAL_PASS_MACHINE_CHECKED_TOPOLOGY'
    return 'FAIL_CLOSED_WAL_RESET_VULNERABILITY_UNKNOWN_OR_AFFECTED'


def target_workspace_example() -> str:
    # Current workspace observation at this run: accepted target reports 3.45.1 + WAL.
    # No verified distro backport or topology exclusion receipt was available here.
    return evaluate_wal_reset_safety(
        sqlite_version='3.45.1',
        journal_mode='WAL',
        verified_backport=False,
        machine_checked_topology_excludes_race=False,
    )


if __name__ == '__main__':
    assert target_workspace_example() == 'FAIL_CLOSED_WAL_RESET_VULNERABILITY_UNKNOWN_OR_AFFECTED'
    assert evaluate_wal_reset_safety(sqlite_version='3.51.3', journal_mode='WAL') == 'PASS_UPSTREAM_FIXED_VERSION'
    assert evaluate_wal_reset_safety(sqlite_version='3.50.7', journal_mode='WAL') == 'PASS_UPSTREAM_FIXED_VERSION'
    assert evaluate_wal_reset_safety(sqlite_version='3.45.1', journal_mode='DELETE') == 'PASS_WAL_RESET_NOT_APPLICABLE'
    assert evaluate_wal_reset_safety(sqlite_version='3.45.1', journal_mode='WAL', machine_checked_topology_excludes_race=True) == 'CONDITIONAL_PASS_MACHINE_CHECKED_TOPOLOGY'
    print('PASS')
