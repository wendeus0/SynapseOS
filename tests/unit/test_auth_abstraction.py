import pytest

from aignt_os.auth import AuthProvider, AuthRegistryStore, get_auth_provider
from aignt_os.config import AppSettings


def test_auth_provider_protocol():
    # Verify AuthRegistryStore implements AuthProvider
    assert issubclass(AuthRegistryStore, AuthProvider)
    # Also verify via runtime check if needed, but issubclass is better for Protocol


def test_get_auth_provider_file(tmp_path):
    settings = AppSettings(
        auth_provider="file",
        workspace_root=tmp_path,
        runtime_state_dir=tmp_path / ".aignt-os/runtime",
    )
    provider = get_auth_provider(settings)
    assert isinstance(provider, AuthRegistryStore)
    assert provider.path == settings.auth_registry_file


def test_get_auth_provider_unknown(tmp_path):
    # Bypass validation if possible or mock settings
    # Since Literal["file"] is enforced by Pydantic, we need to bypass validation or mock
    # But for runtime check inside function, we can just pass an object that has
    # auth_provider="unknown"

    class MockSettings:
        auth_provider = "unknown"

    with pytest.raises(ValueError, match="Unknown auth provider"):
        get_auth_provider(MockSettings())  # type: ignore


def test_auth_provider_authenticate(tmp_path):
    # Verify authenticate method works on the returned provider
    settings = AppSettings(
        auth_provider="file",
        workspace_root=tmp_path,
        runtime_state_dir=tmp_path / ".aignt-os/runtime",
    )
    provider = get_auth_provider(settings)

    # Initialize registry first
    token = provider.initialize_registry(principal_id="admin").token

    principal = provider.authenticate(token)
    assert principal is not None
    assert principal.principal_id == "admin"
