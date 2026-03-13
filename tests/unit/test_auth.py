from __future__ import annotations

import json
import os
from importlib import import_module
from pathlib import Path


def test_auth_registry_store_persists_atomically_with_restricted_permissions(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    auth_module = import_module("aignt_os.auth")

    registry_path = tmp_path / "auth-registry.json"
    store = auth_module.AuthRegistryStore(registry_path)
    replace_calls: list[tuple[Path, Path]] = []
    original_replace = auth_module.os.replace

    def track_replace(source: Path, destination: Path) -> None:
        replace_calls.append((source, destination))
        original_replace(source, destination)

    monkeypatch.setattr(auth_module.os, "replace", track_replace)

    store.write_registry(
        auth_module.AuthRegistry(
            principals=[
                auth_module.AuthPrincipal(
                    principal_id="ops",
                    roles=["operator"],
                )
            ],
            tokens=[
                auth_module.AuthTokenRecord(
                    principal_id="ops",
                    token_sha256=auth_module.hash_token("operator-token"),
                )
            ],
        )
    )

    persisted = json.loads(registry_path.read_text(encoding="utf-8"))

    assert replace_calls
    assert replace_calls[-1][1] == registry_path
    assert "operator-token" not in registry_path.read_text(encoding="utf-8")
    assert persisted["tokens"][0]["token_sha256"] == auth_module.hash_token("operator-token")
    assert stat_mode(registry_path) == 0o600
    assert stat_mode(registry_path.parent) == 0o700


def test_auth_registry_store_authenticates_known_token(tmp_path: Path) -> None:
    auth_module = import_module("aignt_os.auth")

    registry_path = tmp_path / "auth-registry.json"
    store = auth_module.AuthRegistryStore(registry_path)
    store.write_registry(
        auth_module.AuthRegistry(
            principals=[
                auth_module.AuthPrincipal(principal_id="ops", roles=["operator"]),
                auth_module.AuthPrincipal(principal_id="viewer", roles=["viewer"]),
            ],
            tokens=[
                auth_module.AuthTokenRecord(
                    principal_id="ops",
                    token_sha256=auth_module.hash_token("operator-token"),
                ),
                auth_module.AuthTokenRecord(
                    principal_id="viewer",
                    token_sha256=auth_module.hash_token("viewer-token"),
                ),
            ],
        )
    )

    principal = store.authenticate("operator-token")

    assert principal is not None
    assert principal.principal_id == "ops"
    assert principal.roles == ("operator",)


def test_auth_registry_store_init_creates_initial_operator_token(tmp_path: Path) -> None:
    auth_module = import_module("aignt_os.auth")

    registry_path = tmp_path / "auth-registry.json"
    store = auth_module.AuthRegistryStore(registry_path)

    issued_token = store.initialize_registry(principal_id="local-operator", role="operator")
    persisted = json.loads(registry_path.read_text(encoding="utf-8"))

    assert issued_token.principal_id == "local-operator"
    assert issued_token.role == "operator"
    assert issued_token.token
    assert issued_token.token_id
    assert persisted["principals"] == [{"principal_id": "local-operator", "roles": ["operator"]}]
    assert persisted["tokens"][0]["principal_id"] == "local-operator"
    assert persisted["tokens"][0]["token_id"] == issued_token.token_id
    assert persisted["tokens"][0]["disabled"] is False
    assert issued_token.token not in registry_path.read_text(encoding="utf-8")


def test_auth_registry_store_issue_token_creates_new_principal_when_role_is_provided(
    tmp_path: Path,
) -> None:
    auth_module = import_module("aignt_os.auth")

    registry_path = tmp_path / "auth-registry.json"
    store = auth_module.AuthRegistryStore(registry_path)
    store.write_registry(auth_module.AuthRegistry(principals=[], tokens=[]))

    issued_token = store.issue_token(principal_id="viewer-user", role="viewer")
    registry = store.load_registry()

    assert issued_token.principal_id == "viewer-user"
    assert issued_token.role == "viewer"
    assert any(principal.principal_id == "viewer-user" for principal in registry.principals)
    assert any(token.token_id == issued_token.token_id for token in registry.tokens)


def test_auth_registry_store_issue_token_rejects_role_conflict(tmp_path: Path) -> None:
    auth_module = import_module("aignt_os.auth")

    registry_path = tmp_path / "auth-registry.json"
    store = auth_module.AuthRegistryStore(registry_path)
    store.write_registry(
        auth_module.AuthRegistry(
            principals=[auth_module.AuthPrincipal(principal_id="viewer-user", roles=["viewer"])],
            tokens=[],
        )
    )

    try:
        store.issue_token(principal_id="viewer-user", role="operator")
    except ValueError as exc:
        assert "role" in str(exc).lower()
    else:
        raise AssertionError("Expected role conflict to raise ValueError.")


def test_auth_registry_store_disable_token_revokes_authentication(tmp_path: Path) -> None:
    auth_module = import_module("aignt_os.auth")

    registry_path = tmp_path / "auth-registry.json"
    store = auth_module.AuthRegistryStore(registry_path)
    issued_token = store.initialize_registry(principal_id="ops", role="operator")

    assert store.authenticate(issued_token.token) is not None

    store.disable_token(token_id=issued_token.token_id)
    registry = store.load_registry()

    assert store.authenticate(issued_token.token) is None
    assert registry.tokens[0].disabled is True


def test_auth_registry_store_rejects_unknown_token(tmp_path: Path) -> None:
    auth_module = import_module("aignt_os.auth")

    registry_path = tmp_path / "auth-registry.json"
    store = auth_module.AuthRegistryStore(registry_path)
    store.write_registry(
        auth_module.AuthRegistry(
            principals=[auth_module.AuthPrincipal(principal_id="ops", roles=["operator"])],
            tokens=[
                auth_module.AuthTokenRecord(
                    principal_id="ops",
                    token_sha256=auth_module.hash_token("operator-token"),
                )
            ],
        )
    )

    assert store.authenticate("wrong-token") is None


def test_auth_registry_store_raises_for_missing_registry(tmp_path: Path) -> None:
    auth_module = import_module("aignt_os.auth")

    store = auth_module.AuthRegistryStore(tmp_path / "auth-registry.json")

    try:
        store.load_registry()
    except auth_module.AuthConfigurationError as exc:
        assert "not configured" in str(exc).lower()
    else:
        raise AssertionError("Expected missing registry to raise AuthConfigurationError.")


def test_authorize_requires_operator_for_mutating_permissions() -> None:
    auth_module = import_module("aignt_os.auth")

    viewer = auth_module.AuthenticatedPrincipal(
        principal_id="viewer", roles=("viewer",), permissions=frozenset(["run:read"])
    )
    operator = auth_module.AuthenticatedPrincipal(
        principal_id="ops",
        roles=("operator",),
        permissions=frozenset(["run:read", "run:write", "runtime:manage"]),
    )

    assert auth_module.is_authorized(viewer, permission="run:write") is False
    assert auth_module.is_authorized(operator, permission="run:write") is True
    assert auth_module.is_authorized(viewer, permission="runtime:manage") is False
    assert auth_module.is_authorized(operator, permission="runtime:manage") is True


def stat_mode(path: Path) -> int:
    return os.stat(path).st_mode & 0o777
