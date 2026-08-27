import pytest

import clayverse.adapters as adapters
from clayverse.adapters import MistralInference
from clayverse.inference_protocol import InferenceProtocolError


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=-1):
        return b"not-json"


def _adapter_traceback_locals(exc):
    frames = []
    tb = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        if frame.f_globals.get("__name__") == "clayverse.adapters":
            frames.append(dict(frame.f_locals))
        tb = tb.tb_next
    return frames


def test_mistral_secret_not_retained_in_adapter_traceback_locals_after_transport(monkeypatch):
    secret = "TRACEBACK_SECRET_MUST_NOT_SURVIVE"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)
    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: _FakeResponse())

    with pytest.raises(InferenceProtocolError) as caught:
        MistralInference(model="model-x").reason({}, "hello")

    frames = _adapter_traceback_locals(caught.value)
    assert frames
    assert all(secret not in repr(locals_) for locals_ in frames)
    reason_frame = next(locals_ for locals_ in frames if "request" in locals_)
    assert reason_frame["token"] == ""
    assert reason_frame["request"] is None
