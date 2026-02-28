from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

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
    demo_data_dir = (_repo_root() / "data").resolve()
    default_demo_db = (demo_data_dir / "clinicdesk.db").resolve()
    is_inside_data_dir = demo_data_dir in resolved.parents
    has_demo_name = "demo" in resolved.name.lower()
    if resolved == default_demo_db:
        return ResetSafetyDecision(True, False, "default_demo_db")
    if is_inside_data_dir:
        return ResetSafetyDecision(True, False, "inside_demo_data_dir")
    if has_demo_name:
        return ResetSafetyDecision(True, True, "safe_by_demo_name_only")
    return ResetSafetyDecision(False, False, "outside_demo_zone")


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
    if safety.requires_strong_confirmation:
        expected_token = _build_expected_confirmation_token(target)
        if confirmation_token != expected_token:
            LOGGER.warning(
                "seed_demo_reset_blocked reason=missing_strong_confirmation safety=%s target=%s",
                safety.reason_code,
                path_hint,
            )
            raise UnsafeDatabaseResetError(reason="missing_strong_confirmation", path_hint=path_hint)
        LOGGER.info(
            "seed_demo_reset_permission_granted reason=strong_confirmation safety=%s target=%s",
            safety.reason_code,
            path_hint,
        )
    else:
        LOGGER.info(
            "seed_demo_reset_permission_granted reason=safe_zone safety=%s target=%s",
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
    return f"RESET::{target.name}"


def _path_hint(target: Path) -> str:
    digest = hashlib.sha256(target.as_posix().encode("utf-8")).hexdigest()[:8]
    return f"{target.name}#{digest}"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]
