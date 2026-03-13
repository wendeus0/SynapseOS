from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aignt_os.runtime.state import STATE_DIR_MODE, STATE_FILE_MODE

if TYPE_CHECKING:
    from aignt_os.config import AppSettings


Role = Literal["admin", "operator", "viewer"]
Permission = Literal[
    "run:read",
    "run:write",
    "runtime:manage",
    "auth:manage",
]

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    "admin": frozenset(
        {
            "run:read",
            "run:write",
            "runtime:manage",
            "auth:manage",
        }
    ),
    "operator": frozenset({"run:read", "run:write", "runtime:manage"}),
    "viewer": frozenset({"run:read"}),
}


class AuthConfigurationError(RuntimeError):
    pass


class AuthPrincipal(BaseModel):
    model_config = ConfigDict(strict=True)

    principal_id: str = Field(min_length=1)
    roles: list[Role] = Field(min_length=1)


class AuthTokenRecord(BaseModel):
    model_config = ConfigDict(strict=True)

    token_id: str | None = Field(default=None, min_length=1)
    principal_id: str = Field(min_length=1)
    token_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    disabled: bool = False


class AuthRegistry(BaseModel):
    model_config = ConfigDict(strict=True)

    principals: list[AuthPrincipal]
    tokens: list[AuthTokenRecord]


class AuthenticatedPrincipal(BaseModel):
    model_config = ConfigDict(strict=True)

    principal_id: str = Field(min_length=1)
    roles: tuple[Role, ...]
    permissions: frozenset[str] = Field(default_factory=frozenset)


@runtime_checkable
class AuthProvider(Protocol):
    def authenticate(self, token: str) -> AuthenticatedPrincipal | None: ...


class IssuedAuthToken(BaseModel):
    model_config = ConfigDict(strict=True)

    principal_id: str = Field(min_length=1)
    role: Role
    token_id: str = Field(min_length=1)
    token: str = Field(min_length=1)


class AuthRegistryStore:
    def __init__(self, path: Path) -> None:
        if ".." in path.parts:
            raise ValueError("Invalid auth registry path.")
        self.path = path

    def load_registry(self) -> AuthRegistry:
        if not self.path.exists():
            raise AuthConfigurationError("Auth registry is not configured.")

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AuthConfigurationError("Auth registry is corrupted.") from exc
        except OSError as exc:
            raise AuthConfigurationError("Auth registry could not be read.") from exc

        try:
            return AuthRegistry.model_validate(payload)
        except ValidationError as exc:
            raise AuthConfigurationError("Auth registry is invalid.") from exc

    def write_registry(self, registry: AuthRegistry) -> None:
        normalized_registry = self._normalized_registry(registry)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=STATE_DIR_MODE)
        os.chmod(self.path.parent, STATE_DIR_MODE)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(normalized_registry.model_dump_json())
            temporary_path = Path(temporary_file.name)

        os.chmod(temporary_path, STATE_FILE_MODE)
        os.replace(temporary_path, self.path)
        os.chmod(self.path, STATE_FILE_MODE)

    def initialize_registry(self, *, principal_id: str, role: Role = "admin") -> IssuedAuthToken:
        if self.path.exists():
            raise AuthConfigurationError("Auth registry is already configured.")

        issued_token = self._issue_token(principal_id=principal_id, role=role)
        registry = AuthRegistry(
            principals=[AuthPrincipal(principal_id=principal_id, roles=[role])],
            tokens=[
                AuthTokenRecord(
                    token_id=issued_token.token_id,
                    principal_id=principal_id,
                    token_sha256=hash_token(issued_token.token),
                )
            ],
        )
        self.write_registry(registry)
        return issued_token

    def issue_token(self, *, principal_id: str, role: Role | None = None) -> IssuedAuthToken:
        registry = self.load_registry()

        principal = next(
            (
                candidate
                for candidate in registry.principals
                if candidate.principal_id == principal_id
            ),
            None,
        )
        resolved_role: Role
        if principal is None:
            if role is None:
                # Default to admin for backward compatibility / ease of use
                resolved_role = "admin"
            else:
                resolved_role = role

            registry.principals.append(
                AuthPrincipal(principal_id=principal_id, roles=[resolved_role])
            )
        else:
            resolved_role = principal.roles[0]
            if role is not None and role not in principal.roles:
                raise ValueError(
                    "Role conflicts with the principal already stored in the auth registry."
                )

        issued_token = self._issue_token(principal_id=principal_id, role=resolved_role)
        registry.tokens.append(
            AuthTokenRecord(
                token_id=issued_token.token_id,
                principal_id=principal_id,
                token_sha256=hash_token(issued_token.token),
            )
        )
        self.write_registry(registry)
        return issued_token

    def disable_token(self, *, token_id: str) -> None:
        registry = self.load_registry()

        for token_record in registry.tokens:
            if token_record.token_id == token_id:
                token_record.disabled = True
                self.write_registry(registry)
                return

        raise LookupError("Auth token was not found.")

    def authenticate(self, token: str) -> AuthenticatedPrincipal | None:
        normalized_token = token.strip()
        if not normalized_token:
            return None

        registry = self.load_registry()
        token_hash = hash_token(normalized_token)

        for token_record in registry.tokens:
            if token_record.disabled:
                continue
            # Constant time comparison
            if not hmac.compare_digest(token_record.token_sha256, token_hash):
                continue

            # Find principal for this token
            principal_record = next(
                (p for p in registry.principals if p.principal_id == token_record.principal_id),
                None,
            )

            if principal_record is None:
                raise AuthConfigurationError("Auth registry references an unknown principal.")

            # Resolve permissions
            permissions: set[str] = set()
            for role in principal_record.roles:
                # Handle legacy or unknown roles gracefully by ignoring them
                # or treating them as having no permissions if not in map
                if role in ROLE_PERMISSIONS:
                    permissions.update(ROLE_PERMISSIONS[role])

            return AuthenticatedPrincipal(
                principal_id=token_record.principal_id,
                roles=tuple(principal_record.roles),
                permissions=frozenset(permissions),
            )

        return None

    def _normalized_registry(self, registry: AuthRegistry) -> AuthRegistry:
        principals = [principal.model_copy(deep=True) for principal in registry.principals]
        tokens = []
        for token in registry.tokens:
            token_copy = token.model_copy(deep=True)
            if token_copy.token_id is None:
                token_copy.token_id = self._generate_token_id()
            tokens.append(token_copy)
        return AuthRegistry(principals=principals, tokens=tokens)

    def _issue_token(self, *, principal_id: str, role: Role) -> IssuedAuthToken:
        return IssuedAuthToken(
            principal_id=principal_id,
            role=role,
            token_id=self._generate_token_id(),
            token=self._generate_token(),
        )

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(24)

    def _generate_token_id(self) -> str:
        return secrets.token_hex(8)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_authorized(principal: AuthenticatedPrincipal, *, permission: str) -> bool:
    return permission in principal.permissions


def get_auth_provider(settings: AppSettings) -> AuthProvider:
    if settings.auth_provider == "file":
        return AuthRegistryStore(settings.auth_registry_file)
    raise ValueError(f"Unknown auth provider: {settings.auth_provider}")
