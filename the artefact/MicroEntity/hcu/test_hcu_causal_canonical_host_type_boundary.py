import shutil
import subprocess

import pytest

from hcu_causal_canonical_v1 import HCUCanonicalizationError, canonical_bytes, canonical_sha256


def test_integer_valued_binary64_above_safe_range_rejects_like_int():
    with pytest.raises(HCUCanonicalizationError, match="INTEGER_OUTSIDE_IJSON_SAFE_RANGE"):
        canonical_bytes({"n": 2**53})
    with pytest.raises(HCUCanonicalizationError, match="INTEGER_OUTSIDE_IJSON_SAFE_RANGE"):
        canonical_bytes({"n": float(2**53)})


def test_max_safe_integer_stays_host_type_stable():
    value = (1 << 53) - 1
    assert canonical_sha256({"n": value}) == canonical_sha256({"n": float(value)})


def test_node_reference_agrees_on_boundary_policy():
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    script = r'''
const max=Number.MAX_SAFE_INTEGER;
for (const v of [9007199254740991,9007199254740992]) {
  if (!Number.isFinite(v)) throw new Error('NONFINITE_NUMBER_FORBIDDEN');
  if (Number.isInteger(v) && Math.abs(v)>max) console.log('REJECT');
  else console.log('ACCEPT');
}
'''
    lines = subprocess.check_output([node, "-e", script], text=True).strip().splitlines()
    assert lines == ["ACCEPT", "REJECT"]
