from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Protocol

from clinicdesk.app.application.security import Role


class AuditMetadataError(ValueError):
    pass


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
    def append(self, event: AuditEvent) -> None:
        ...


class AuditService:
    _ALLOWED_METADATA_KEYS: frozenset[str] = frozenset(
        {
            "cita_id",
            "medico_id",
            "sala_id",
            "paciente_id_hash",
            "motivo_override",
            "warnings_count",
            "incidencia_id",
            "error_code",
            "error_type",
            "seed",
            "n_doctors",
            "n_patients",
            "n_appointments",
            "incidences",
            "medicamentos",
            "materiales",
            "recetas",
            "movimientos",
            "turnos",
            "ausencias",
            "from_date",
            "to_date",
            "dataset_version",
            "reason_code",
            "db_path_hint",
            "export_rows",
        }
    )
    _BLOCKED_KEY_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"dni", re.IGNORECASE),
        re.compile(r"documento", re.IGNORECASE),
        re.compile(r"email", re.IGNORECASE),
        re.compile(r"telefono|tlf", re.IGNORECASE),
        re.compile(r"direccion", re.IGNORECASE),
    )
    _RE_EMAIL = re.compile(r"[\w.%-]+@[\w.-]+\.[A-Za-z]{2,}")
    _RE_DNI = re.compile(r"\b\d{8}[A-Za-z]?\b")
    _RE_PHONE = re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){9,}\b")

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
        sanitized: dict[str, str | int | float | bool | None] = {}
        for key, value in metadata.items():
            if key not in self._ALLOWED_METADATA_KEYS:
                raise AuditMetadataError(f"Metadata key no permitida: {key}")
            self._ensure_key_is_not_pii(key)
            sanitized[key] = self._sanitize_value(value)
        return sanitized

    def _ensure_key_is_not_pii(self, key: str) -> None:
        for pattern in self._BLOCKED_KEY_PATTERNS:
            if pattern.search(key):
                raise AuditMetadataError(f"Metadata key bloqueada por PII: {key}")

    def _sanitize_value(self, value: str | int | float | bool | None) -> str | int | float | bool | None:
        if isinstance(value, str):
            redacted = self._RE_EMAIL.sub("[REDACTED_EMAIL]", value)
            redacted = self._RE_DNI.sub("[REDACTED_DNI]", redacted)
            redacted = self._RE_PHONE.sub("[REDACTED_PHONE]", redacted)
            return redacted
        return value

