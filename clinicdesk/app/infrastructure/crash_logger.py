from __future__ import annotations

import faulthandler
import threading
import traceback
from datetime import UTC, datetime
from pathlib import Path
import sys

_ARCHIVO_CRASH = None


def _marca_tiempo() -> str:
    return datetime.now(tz=UTC).isoformat()


def _escribir_linea(archivo, encabezado: str, detalle: str) -> None:
    archivo.write(f"[{_marca_tiempo()}] {encabezado}\n")
    if detalle:
        archivo.write(f"{detalle}\n")
    archivo.flush()


def instalar_hooks_crash(ruta_logs: Path | str) -> None:
    global _ARCHIVO_CRASH
    base = Path(ruta_logs)
    base.mkdir(parents=True, exist_ok=True)
    _ARCHIVO_CRASH = open(base / "crash.log", "a", encoding="utf-8", buffering=1)

    try:
        faulthandler.enable(file=_ARCHIVO_CRASH, all_threads=True)
    except Exception:  # noqa: BLE001
        _escribir_linea(_ARCHIVO_CRASH, "faulthandler_enable_fail", traceback.format_exc())

    def _hook_python(exc_type: type[BaseException], exc_value: BaseException, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            if sys.__excepthook__:
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        detalle = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        _escribir_linea(_ARCHIVO_CRASH, "unhandled_python_exception", detalle)

    sys.excepthook = _hook_python

    if hasattr(threading, "excepthook"):

        def _hook_thread(args: threading.ExceptHookArgs) -> None:
            _hook_python(args.exc_type, args.exc_value, args.exc_traceback)

        threading.excepthook = _hook_thread  # type: ignore[assignment]
