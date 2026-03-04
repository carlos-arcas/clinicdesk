from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from clinicdesk.app.application.seguridad.politica_rutas_seguras import es_ruta_db_segura_para_reset
from clinicdesk.app.bootstrap import bootstrap_database
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class UnsafeDatabaseResetError(ValueError):
    reason: str
    path_hint: str

    def __str__(self) -> str:
        return (
            "Reset inseguro bloqueado para evitar borrado accidental. "
            f"Motivo: {self.reason}. Objetivo: {self.path_hint}. "
            "Usa --no-reset o mueve la DB a ./data/."
        )


@dataclass(frozen=True, slots=True)
class ResetSafetyDecision:
    is_allowed: bool
    requires_strong_confirmation: bool
    reason_code: str


def is_safe_demo_db_path(sqlite_path: Path) -> bool:
    return evaluate_reset_safety(sqlite_path).is_allowed


def evaluate_reset_safety(sqlite_path: Path) -> ResetSafetyDecision:
    resolved = sqlite_path.expanduser().resolve()
    if not es_ruta_db_segura_para_reset(resolved):
        return ResetSafetyDecision(False, False, "unsafe_db_path")
    return ResetSafetyDecision(True, True, "safe_path_requires_confirmation")


def reset_demo_database(sqlite_path: Path, *, confirmation_token: str | None = None) -> None:
    target = sqlite_path.expanduser().resolve()
    path_hint = _path_hint(target)
    safety = evaluate_reset_safety(target)
    if not safety.is_allowed:
        LOGGER.warning(
            "seed_demo_reset_blocked reason=%s target=%s",
            safety.reason_code,
            path_hint,
        )
        raise UnsafeDatabaseResetError(reason=safety.reason_code, path_hint=path_hint)
    expected_token = _build_expected_confirmation_token(target)
    if safety.requires_strong_confirmation and confirmation_token != expected_token:
        LOGGER.warning(
            "seed_demo_reset_blocked reason=confirmation_required safety=%s target=%s",
            safety.reason_code,
            path_hint,
        )
        raise UnsafeDatabaseResetError(reason="confirmation_required", path_hint=path_hint)
    LOGGER.info(
        "seed_demo_reset_permission_granted reason=explicit_confirmation safety=%s target=%s",
        safety.reason_code,
        path_hint,
    )
    if target.exists():
        target.unlink()
        LOGGER.info("seed_demo_db_removed target=%s", path_hint)
    connection = bootstrap_database(apply_schema=True, sqlite_path=target.as_posix())
    connection.close()
    LOGGER.info("seed_demo_db_recreated target=%s", path_hint)


def build_reset_confirmation_help(sqlite_path: Path) -> str:
    return _build_expected_confirmation_token(sqlite_path.expanduser().resolve())


def _build_expected_confirmation_token(target: Path) -> str:
    _ = target
    return "RESET-DEMO"


def _path_hint(target: Path) -> str:
    digest = hashlib.sha256(target.as_posix().encode("utf-8")).hexdigest()[:8]
    return f"{target.name}#{digest}"

