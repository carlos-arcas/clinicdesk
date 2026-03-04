from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "clinicdesk" / "app" / "ui" / "widgets" / "toast_manager.py"
    spec = spec_from_file_location("test_toast_manager_module", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProgramadorFalso:
    def __init__(self) -> None:
        self.callbacks = []
        self.cancelados = []

    def programar(self, _delay_ms: int, callback):
        self.callbacks.append(callback)
        return callback

    def cancelar(self, handle) -> None:
        self.cancelados.append(handle)


def test_toast_manager_encola_y_respeta_orden() -> None:
    toast_module = _load_module()
    programador = ProgramadorFalso()
    manager = toast_module.ToastManager(
        traducir=lambda key: f"tr:{key}",
        programar=programador.programar,
        cancelar=programador.cancelar,
    )

    manager.success("toast.a")
    manager.error("toast.b")

    assert manager.actual is not None
    assert manager.actual.mensaje_key == "toast.a"

    manager.close_current()

    assert manager.actual is not None
    assert manager.actual.mensaje_key == "toast.b"


def test_toast_manager_autohide_avanza_cola() -> None:
    toast_module = _load_module()
    programador = ProgramadorFalso()
    manager = toast_module.ToastManager(
        traducir=lambda key: key,
        programar=programador.programar,
        cancelar=programador.cancelar,
    )

    manager.info("toast.info")
    manager.success("toast.ok")

    assert len(programador.callbacks) == 1
    programador.callbacks[0]()

    assert manager.actual is not None
    assert manager.actual.mensaje_key == "toast.ok"
