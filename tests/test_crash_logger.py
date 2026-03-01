from __future__ import annotations

import sys
import threading
from pathlib import Path

from clinicdesk.app.infrastructure.crash_logger import instalar_hooks_crash


class _ThreadArgs:
    def __init__(self, exc: BaseException) -> None:
        self.exc_type = type(exc)
        self.exc_value = exc
        self.exc_traceback = exc.__traceback__


def test_instalar_hooks_crash_crea_archivo_y_escribe_excepcion_python(tmp_path: Path) -> None:
    instalar_hooks_crash(tmp_path)
    crash_file = tmp_path / "crash.log"
    assert crash_file.exists()

    try:
        raise RuntimeError("boom python")
    except RuntimeError as exc:
        sys.excepthook(type(exc), exc, exc.__traceback__)

    contenido = crash_file.read_text(encoding="utf-8")
    assert "unhandled_python_exception" in contenido
    assert "RuntimeError: boom python" in contenido


def test_instalar_hooks_crash_registra_excepcion_threading(tmp_path: Path) -> None:
    instalar_hooks_crash(tmp_path)
    crash_file = tmp_path / "crash.log"

    try:
        raise ValueError("boom thread")
    except ValueError as exc:
        threading.excepthook(_ThreadArgs(exc))  # type: ignore[arg-type]

    contenido = crash_file.read_text(encoding="utf-8")
    assert "ValueError: boom thread" in contenido
