import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_qwen35_model_state_digest_v1.py"
spec = importlib.util.spec_from_file_location("state_digest", P)
state_digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state_digest)


def test_raw_digest_is_order_independent():
    a = ("a.weight", "torch.float32", [1, 2], b"abcdefgh")
    b = ("b.bias", "torch.float32", [1], b"ijkl")
    one = state_digest.digest_raw_entries([a, b])
    two = state_digest.digest_raw_entries([b, a])
    assert one["model_state_sha256"] == two["model_state_sha256"]
    assert [x["name"] for x in one["entries"]] == ["a.weight", "b.bias"]


def test_raw_digest_changes_on_one_byte_mutation():
    base = state_digest.digest_raw_entries([
        ("a.weight", "torch.float32", [1, 2], b"abcdefgh"),
    ])
    changed = state_digest.digest_raw_entries([
        ("a.weight", "torch.float32", [1, 2], b"abcdefgI"),
    ])
    assert base["model_state_sha256"] != changed["model_state_sha256"]
    assert base["entries"][0]["raw_bytes_sha256"] != changed["entries"][0]["raw_bytes_sha256"]


def test_raw_digest_binds_name_dtype_and_shape():
    raw = b"abcdefgh"
    base = state_digest.digest_raw_entries([("x", "torch.float32", [2], raw)])
    renamed = state_digest.digest_raw_entries([("y", "torch.float32", [2], raw)])
    redtyped = state_digest.digest_raw_entries([("x", "torch.float16", [4], raw)])
    reshaped = state_digest.digest_raw_entries([("x", "torch.float32", [1, 2], raw)])
    assert len({
        base["model_state_sha256"],
        renamed["model_state_sha256"],
        redtyped["model_state_sha256"],
        reshaped["model_state_sha256"],
    }) == 4


def test_duplicate_and_empty_state_fail_closed():
    with pytest.raises(state_digest.ModelStateDigestError, match="MODEL_STATE_EMPTY"):
        state_digest.digest_raw_entries([])
    with pytest.raises(state_digest.ModelStateDigestError, match="DUPLICATE_STATE_ENTRY:x"):
        state_digest.digest_raw_entries([
            ("x", "torch.uint8", [1], b"a"),
            ("x", "torch.uint8", [1], b"a"),
        ])


def test_torch_state_dict_digest_tracks_tensor_mutation_and_numel():
    torch = pytest.importorskip("torch")
    state = {
        "w": torch.tensor([[1.0, 2.0]], dtype=torch.float32),
        "b": torch.tensor([3], dtype=torch.int64),
    }
    first = state_digest.digest_state_dict(state)
    assert first["state_entry_count"] == 2
    assert {x["name"]: x["numel"] for x in first["entries"]} == {"b": 1, "w": 2}
    state["w"][0, 1] = 9.0
    second = state_digest.digest_state_dict(state)
    assert first["model_state_sha256"] != second["model_state_sha256"]


def test_loaded_model_binds_model_class_and_zero_credit():
    torch = pytest.importorskip("torch")

    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.weight = torch.nn.Parameter(torch.tensor([1.0, 2.0]))
            self.register_buffer("persistent_counter", torch.tensor([7]), persistent=True)
            self.register_buffer("ephemeral", torch.tensor([9]), persistent=False)

    result = state_digest.digest_loaded_model(Tiny())
    assert result["model_class"] == "Tiny"
    assert {x["name"] for x in result["entries"]} == {"persistent_counter", "weight"}
    assert "ephemeral" not in {x["name"] for x in result["entries"]}
    assert result["credit_boundary"]["checkpoint_selection_credit"] == 0
