import json

import pytest

from clayverse import service


def _mapping(monkeypatch, value):
    monkeypatch.setenv("CLAYVERSE_CLERK_MAP_JSON", json.dumps(value))
    return service._clerk_map()


def test_clerk_mapping_requires_exact_two_subject_bijection(monkeypatch):
    assert _mapping(monkeypatch, {"clerk_g": "gabriel", "clerk_a": "andreas"}) == {
        "clerk_g": "gabriel",
        "clerk_a": "andreas",
    }


@pytest.mark.parametrize(
    "value,match",
    [
        ({"clerk_g": "gabriel"}, "exactly two"),
        ({"clerk_g": "gabriel", "clerk_a": "andreas", "clerk_g2": "gabriel"}, "exactly two"),
        ({"clerk_g": "gabriel", "clerk_g2": "gabriel"}, "exactly once"),
        ({"": "gabriel", "clerk_a": "andreas"}, "non-empty strings"),
        ({"   ": "gabriel", "clerk_a": "andreas"}, "non-empty strings"),
        ({"clerk_g": "gabriel", "clerk_x": "other"}, "gabriel/andreas"),
    ],
)
def test_clerk_mapping_rejects_ambiguous_or_extra_identity_routes(monkeypatch, value, match):
    monkeypatch.setenv("CLAYVERSE_CLERK_MAP_JSON", json.dumps(value))
    with pytest.raises(RuntimeError, match=match):
        service._clerk_map()


def test_clerk_mapping_rejects_non_object_and_malformed_json(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_CLERK_MAP_JSON", '["gabriel", "andreas"]')
    with pytest.raises(RuntimeError, match="exactly two"):
        service._clerk_map()

    monkeypatch.setenv("CLAYVERSE_CLERK_MAP_JSON", "{")
    with pytest.raises(RuntimeError, match="invalid JSON"):
        service._clerk_map()
