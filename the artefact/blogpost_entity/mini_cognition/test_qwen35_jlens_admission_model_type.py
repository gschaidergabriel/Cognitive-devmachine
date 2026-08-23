import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from check_qwen35_jlens_admission import EXPECTED_MODEL_TYPE, _load_config_and_meta_model


class _Device:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _TextConfig:
    model_type = "qwen3_5_text"
    num_hidden_layers = 24
    hidden_size = 1024


class _CompositeConfig:
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


class Qwen35JLenseAdmissionModelTypeTests(unittest.TestCase):
    def _modules(self):
        torch = types.ModuleType("torch")
        torch.device = lambda *_args, **_kwargs: _Device()
        transformers = types.ModuleType("transformers")
        transformers.AutoConfig = _AutoConfig
        transformers.AutoModelForCausalLM = _AutoModelForCausalLM
        return {"torch": torch, "transformers": transformers}

    def _args(self, expected_model_type):
        return SimpleNamespace(
            model="fixture",
            allow_network=False,
            trust_remote_code=False,
            expected_model_type=expected_model_type,
            expected_layers=24,
            expected_d_model=1024,
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


if __name__ == "__main__":
    unittest.main()
