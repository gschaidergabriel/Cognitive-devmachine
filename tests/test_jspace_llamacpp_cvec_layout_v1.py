from __future__ import annotations

import math
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import jspace_llamacpp_cvec_layout_v1 as cvec


def test_single_1024_vector_only_populates_native_layer_one() -> None:
    # This captures the upstream llama.cpp buffer law that motivates the adapter:
    # a naked n_embd-sized buffer cannot populate native layer 20.
    assert cvec.consumed_native_layers(data_len_floats=1024, n_embd=1024, n_layer=28) == [1]


def test_layer20_vector_is_placed_at_layer20_native_slot() -> None:
    vector = [0.0] * 1024
    vector[7] = 0.5
    layout = cvec.build_single_native_layer_buffer(
        vector,
        n_embd=1024,
        n_layer=28,
        native_layer_index=20,
        gain=16.0,
        source_layer_index=20,
    )
    assert layout["target_offset_floats"] == 19 * 1024
    assert layout["data_len_floats"] == 27 * 1024
    assert layout["il_start"] == 20
    assert layout["il_end"] == 20
    assert layout["nonzero_native_layers"] == [20]
    assert layout["buffer"][19 * 1024 + 7] == 8.0
    assert layout["buffer"][7] == 0.0
    assert layout["runtime_credit_minted"] is False
    assert layout["mapping_credit_minted"] is False


def test_source_layer_does_not_silently_mint_native_mapping() -> None:
    layout = cvec.build_single_native_layer_buffer(
        [1.0, 0.0],
        n_embd=2,
        n_layer=4,
        native_layer_index=2,
        source_layer_index=20,
    )
    assert layout["source_layer_index"] == 20
    assert layout["native_layer_index"] == 2
    assert layout["layer_mapping_evidence_sha256"] is None
    assert layout["mapping_credit_minted"] is False


def test_rejects_layer_zero_and_out_of_range() -> None:
    with pytest.raises(cvec.CvecLayoutError, match="NATIVE_LAYER_INDEX_INVALID"):
        cvec.build_single_native_layer_buffer([1.0, 2.0], n_embd=2, n_layer=4, native_layer_index=0)
    with pytest.raises(cvec.CvecLayoutError, match="NATIVE_LAYER_INDEX_INVALID"):
        cvec.build_single_native_layer_buffer([1.0, 2.0], n_embd=2, n_layer=4, native_layer_index=4)


def test_rejects_dimension_and_nonfinite_values() -> None:
    with pytest.raises(cvec.CvecLayoutError, match="VECTOR_DIMENSION_MISMATCH"):
        cvec.build_single_native_layer_buffer([1.0], n_embd=2, n_layer=4, native_layer_index=2)
    with pytest.raises(cvec.CvecLayoutError, match="FINITE_FLOAT_REQUIRED"):
        cvec.build_single_native_layer_buffer([1.0, math.nan], n_embd=2, n_layer=4, native_layer_index=2)


def test_receipt_safe_projection_drops_large_payload() -> None:
    layout = cvec.build_single_native_layer_buffer(
        [1.0, -1.0], n_embd=2, n_layer=3, native_layer_index=1, gain=0.5
    )
    receipt = cvec.sparse_buffer_without_payload(layout)
    assert "buffer" not in receipt
    assert len(receipt["buffer_f32le_sha256"]) == 64
    assert receipt["nonzero_native_layers"] == [1]
