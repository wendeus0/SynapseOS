from importlib import import_module


def test_settings_exposes_runtime_poll_interval(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    config_module = import_module("aignt_os.config")
    monkeypatch.setenv("AIGNT_OS_RUNTIME_POLL_INTERVAL_SECONDS", "0.25")

    settings = config_module.AppSettings()

    assert settings.runtime_poll_interval_seconds == 0.25
