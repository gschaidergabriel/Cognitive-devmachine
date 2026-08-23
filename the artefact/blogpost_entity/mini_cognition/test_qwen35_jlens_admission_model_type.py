import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from check_qwen35_jlens_admission import (
    EXPECTED_MODEL_TYPE,
    _load_config_and_meta_model,
    _normalize_requested_dtype,
    _observe_and_validate_weighted_dtype,
)


class _Device:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _TextConfig:
    model_type = "qwen3_5_text"
    num_hidden_layers = 24
    hidden_size = 1024
    dtype = "bfloat16"


class _CompositeConfig:
    dtype = "bfloat16"

    def get_text_config(self):
        return _TextConfig()


class _AutoConfig:
    @staticmethod
    def from_pretrained(*args, **kwargs):
        return _CompositeConfig()


class _AutoModelForCausalLM:
    @staticmethod
    def from_config(config, **kwargs):
        return SimpleNamespace(config=_TextConfig())


class _Weight:
    def __init__(self, dtype):
        self.dtype = dtype


class _Module:
    def __init__(self, dtype):
        self.weight = _Weight(dtype)

    def parameters(self):
        return iter([SimpleNamespace(dtype=self.weight.dtype)])


class _WeightedModel:
    def __init__(self, dtype):
        self.config = _CompositeConfig()
        self.model = SimpleNamespace(layers=[_Module(dtype)])
        self._input = _Module(dtype)
        self._output = _Module(dtype)

    def get_input_embeddings(self):
        return self._input

    def get_output_embeddings(self):
        return self._output


class Qwen35JLenseAdmissionModelTypeTests(unittest.TestCase):
    def _modules(self):
        torch = types.ModuleType("torch")
        torch.device = lambda *_args, **_kwargs: _Device()
        transformers = types.ModuleType("transformers")
        transformers.AutoConfig = _AutoConfig
        transformers.AutoModelForCausalLM = _AutoModelForCausalLM
        return {"torch": torch, "transformers": transformers}

    def _args(self, expected_model_type=EXPECTED_MODEL_TYPE, dtype="auto"):
        return SimpleNamespace(
            model="fixture",
            allow_network=False,
            trust_remote_code=False,
            expected_model_type=expected_model_type,
            expected_layers=24,
            expected_d_model=1024,
            dtype=dtype,
        )

    def test_default_matches_official_qwen35_text_subconfig_type(self):
        self.assertEqual(EXPECTED_MODEL_TYPE, "qwen3_5_text")
        with patch.dict(sys.modules, self._modules()):
            _config, text_config, _model = _load_config_and_meta_model(
                self._args(EXPECTED_MODEL_TYPE)
            )
        self.assertEqual(text_config.model_type, "qwen3_5_text")

    def test_old_composite_model_type_expectation_is_rejected(self):
        with patch.dict(sys.modules, self._modules()):
            with self.assertRaisesRegex(AssertionError, "model_type mismatch"):
                _load_config_and_meta_model(self._args("qwen3_5"))

    def test_dtype_aliases_are_canonicalized(self):
        self.assertIsNone(_normalize_requested_dtype("auto"))
        self.assertEqual(_normalize_requested_dtype("torch.float32"), "float32")
        self.assertEqual(_normalize_requested_dtype("fp32"), "float32")
        self.assertEqual(_normalize_requested_dtype("bf16"), "bfloat16")
        self.assertEqual(_normalize_requested_dtype("half"), "float16")

    def test_auto_dtype_observes_without_forcing(self):
        observed = _observe_and_validate_weighted_dtype(
            self._args(dtype="auto"), _WeightedModel("torch.bfloat16")
        )
        self.assertIsNone(observed["expected_concrete"])
        self.assertIsNone(observed["concrete_request_match"])
        self.assertEqual(
            observed["sampled_weight_dtypes"],
            {
                "first_decoder_block": "bfloat16",
                "input_embeddings": "bfloat16",
                "output_embeddings": "bfloat16",
            },
        )

    def test_concrete_dtype_match_passes(self):
        observed = _observe_and_validate_weighted_dtype(
            self._args(dtype="float32"), _WeightedModel("torch.float32")
        )
        self.assertEqual(observed["expected_concrete"], "float32")
        self.assertTrue(observed["concrete_request_match"])

    def test_concrete_dtype_mismatch_fails_closed(self):
        with self.assertRaisesRegex(AssertionError, "requested dtype=float32"):
            _observe_and_validate_weighted_dtype(
                self._args(dtype="float32"), _WeightedModel("torch.bfloat16")
            )

    def test_unknown_concrete_dtype_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unsupported concrete --dtype"):
            _observe_and_validate_weighted_dtype(
                self._args(dtype="float8_e4m3fn"), _WeightedModel("torch.float8_e4m3fn")
            )


if __name__ == "__main__":
    unittest.main()
