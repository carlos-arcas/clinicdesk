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


def test_ver_detalles_solo_aparece_si_hay_detalle() -> None:
    toast_module = _load_module()
    manager = toast_module.ToastManager(traducir=lambda key: key)

    payload_sin_detalle = manager.error("toast.fail")
    assert payload_sin_detalle.tiene_detalle is False

    manager.close_current()
    payload_con_detalle = manager.error("toast.fail", detalle="stacktrace")
    assert payload_con_detalle.tiene_detalle is True


def test_accion_toast_se_ejecuta_una_sola_vez() -> None:
    toast_module = _load_module()
    manager = toast_module.ToastManager(traducir=lambda key: key)
    ejecuciones: list[str] = []

    manager.error(
        "toast.retry",
        accion_label_key="toast.action.retry",
        accion_callback=lambda: ejecuciones.append("retry"),
        persistente=True,
    )

    assert manager.run_current_action() is True
    assert manager.run_current_action() is False
    assert ejecuciones == ["retry"]


def test_cierre_toast_notifica_once() -> None:
    toast_module = _load_module()
    manager = toast_module.ToastManager(traducir=lambda key: key)
    cierres: list[str] = []

    manager.success("toast.ok", on_close=lambda: cierres.append("close"))
    manager.close_current()
    manager.close_current()

    assert cierres == ["close"]
