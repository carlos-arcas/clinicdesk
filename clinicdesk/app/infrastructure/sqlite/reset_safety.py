from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clinicdesk.app.bootstrap import bootstrap_database
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class UnsafeDatabaseResetError(ValueError):
    sqlite_path: str

    def __str__(self) -> str:
        return (
            "Reset inseguro bloqueado para evitar borrado accidental. "
            f"Ruta: {self.sqlite_path}. Usa --no-reset o mueve la DB a ./data/."
        )


def is_safe_demo_db_path(sqlite_path: Path) -> bool:
    resolved = sqlite_path.expanduser().resolve()
    demo_data_dir = (_repo_root() / "data").resolve()
    default_demo_db = (demo_data_dir / "clinicdesk.db").resolve()
    is_inside_data_dir = demo_data_dir in resolved.parents
    has_demo_name = "demo" in resolved.name.lower()
    return resolved == default_demo_db or is_inside_data_dir or has_demo_name


def reset_demo_database(sqlite_path: Path) -> None:
    target = sqlite_path.expanduser().resolve()
    if not is_safe_demo_db_path(target):
        raise UnsafeDatabaseResetError(target.as_posix())
    if target.exists():
        target.unlink()
        LOGGER.info("seed_demo_db_removed path=%s", target)
    connection = bootstrap_database(apply_schema=True, sqlite_path=target.as_posix())
    connection.close()
    LOGGER.info("seed_demo_db_recreated path=%s", target)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]
