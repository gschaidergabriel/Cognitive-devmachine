import clayverse.api_providers as providers


def test_api_terminal_mode_hardens_secret_holding_process(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_TERMINAL_PROVIDER", "api")
    monkeypatch.setenv("CLAYVERSE_LLM_API_PROFILE", "mistral")
    monkeypatch.setenv("CLAYVERSE_LLM_API_MODEL", "mistral-test-model")
    monkeypatch.setenv("MISTRAL_API_KEY", "runtime-token")
    called = []
    monkeypatch.setattr(
        providers,
        "harden_api_secret_process_boundary",
        lambda: called.append(True) or {"process_dumpable": False},
    )

    inference = providers.build_api_inference_from_env()

    assert inference.available() is True
    assert called == [True]


def test_stage1_builder_does_not_mutate_process_dumpability(monkeypatch):
    monkeypatch.delenv("CLAYVERSE_TERMINAL_PROVIDER", raising=False)
    monkeypatch.setenv("CLAYVERSE_LLM_API_PROFILE", "mistral")
    monkeypatch.setenv("CLAYVERSE_LLM_API_MODEL", "mistral-test-model")
    monkeypatch.setenv("MISTRAL_API_KEY", "runtime-token")
    called = []
    monkeypatch.setattr(
        providers,
        "harden_api_secret_process_boundary",
        lambda: called.append(True) or {"process_dumpable": False},
    )

    inference = providers.build_api_inference_from_env()

    assert inference.available() is True
    assert called == []
