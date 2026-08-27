import hashlib
import os
import subprocess

import pytest

from clayverse.entityos_bridge import EntityOSBridge


def test_entityos_exec_uses_sealed_verified_snapshot_after_source_mutation(tmp_path):
    """Bounded GO experiment: mutate the backing path after verification.

    The executed object must remain the exact digest-pinned snapshot and direct
    writes to that snapshot must be rejected by Linux file seals.
    """

    entityos = tmp_path / "EntityOS"
    original = b"#!/bin/sh\nprintf 'PINNED\\n'\n"
    replacement = b"#!/bin/sh\nprintf 'MUTATED\\n'\n"
    entityos.write_bytes(original)
    entityos.chmod(0o700)

    bridge = EntityOSBridge(str(entityos), hashlib.sha256(original).hexdigest(), timeout=3)
    fd = bridge._open_verified()
    try:
        entityos.write_bytes(replacement)
        entityos.chmod(0o700)

        with pytest.raises(OSError):
            os.write(fd, b"X")

        executable = f"/proc/self/fd/{fd}"
        cp = subprocess.run(
            [executable],
            executable=executable,
            pass_fds=(fd,),
            shell=False,
            capture_output=True,
            text=False,
            timeout=3,
            check=False,
        )
        assert cp.returncode == 0
        assert cp.stdout == b"PINNED\n"
        assert b"MUTATED" not in cp.stdout
    finally:
        os.close(fd)
