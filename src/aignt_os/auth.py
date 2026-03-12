from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aignt_os.runtime.state import STATE_DIR_MODE, STATE_FILE_MODE

Role = Literal["viewer", "operator"]
Permission = Literal["runs.submit", "runtime.manage"]

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    "viewer": frozenset(),
    "operator": frozenset({"runs.submit", "runtime.manage"}),
}


class AuthConfigurationError(RuntimeError):
    pass


class AuthPrincipal(BaseModel):
    model_config = ConfigDict(strict=True)

    principal_id: str = Field(min_length=1)
    roles: list[Role] = Field(min_length=1)


class AuthTokenRecord(BaseModel):
    model_config = ConfigDict(strict=True)

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
            temporary_file.write(registry.model_dump_json())
            temporary_path = Path(temporary_file.name)

        os.chmod(temporary_path, STATE_FILE_MODE)
        os.replace(temporary_path, self.path)
        os.chmod(self.path, STATE_FILE_MODE)

    def authenticate(self, token: str) -> AuthenticatedPrincipal | None:
        normalized_token = token.strip()
        if not normalized_token:
            return None

        registry = self.load_registry()
        token_hash = hash_token(normalized_token)

        principal_roles = {
            principal.principal_id: principal.roles for principal in registry.principals
        }
        for token_record in registry.tokens:
            if token_record.disabled:
                continue
            if not hmac.compare_digest(token_record.token_sha256, token_hash):
                continue

            roles = principal_roles.get(token_record.principal_id)
            if roles is None:
                raise AuthConfigurationError("Auth registry references an unknown principal.")

            return AuthenticatedPrincipal(
                principal_id=token_record.principal_id,
                roles=tuple(roles),
            )

        return None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_authorized(principal: AuthenticatedPrincipal, *, permission: Permission) -> bool:
    allowed_permissions: set[Permission] = set()
    for role in principal.roles:
        allowed_permissions.update(ROLE_PERMISSIONS.get(role, frozenset()))
    return permission in allowed_permissions
