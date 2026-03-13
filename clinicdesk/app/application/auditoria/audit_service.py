from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from clinicdesk.app.application.auditoria.metadata_segura import (
    CLAVES_METADATA_AUDITORIA_PERMITIDAS,
    MetadataAuditoriaError as AuditMetadataError,
    sanitizar_metadata_auditoria,
)
from clinicdesk.app.application.security import Role


@dataclass(frozen=True, slots=True)
class AuditEvent:
    action: str
    outcome: str
    actor_username: str
    actor_role: str
    correlation_id: str | None
    metadata: dict[str, str | int | float | bool | None]
    timestamp_utc: str


class AuditRepository(Protocol):
    def append(self, event: AuditEvent) -> None: ...


class AuditService:
    _ALLOWED_METADATA_KEYS: frozenset[str] = CLAVES_METADATA_AUDITORIA_PERMITIDAS

    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    @classmethod
    def allowed_metadata_keys(cls) -> frozenset[str]:
        return cls._ALLOWED_METADATA_KEYS

    def registrar(
        self,
        *,
        action: str,
        outcome: str,
        actor_username: str,
        actor_role: Role | str,
        correlation_id: str | None,
        metadata: dict[str, str | int | float | bool | None] | None = None,
    ) -> AuditEvent:
        normalized_outcome = outcome.lower()
        if normalized_outcome not in {"ok", "fail"}:
            raise AuditMetadataError("outcome debe ser 'ok' o 'fail'.")
        sanitized_metadata = self._sanitize_metadata(metadata or {})
        actor_role_value = actor_role.value if isinstance(actor_role, Role) else actor_role
        event = AuditEvent(
            action=action,
            outcome=normalized_outcome,
            actor_username=actor_username,
            actor_role=actor_role_value,
            correlation_id=correlation_id,
            metadata=sanitized_metadata,
            timestamp_utc=datetime.now(UTC).replace(microsecond=0).isoformat(),
        )
        self._repository.append(event)
        return event

    def _sanitize_metadata(
        self, metadata: dict[str, str | int | float | bool | None]
    ) -> dict[str, str | int | float | bool | None]:
        return sanitizar_metadata_auditoria(metadata)
