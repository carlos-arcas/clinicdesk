from __future__ import annotations

import pytest

from clinicdesk.app.application.prediccion_ausencias import EntrenamientoPrediccionError
from clinicdesk.app.pages.prediccion_ausencias.coordinador_entrenamiento import (
    CoordinadorEntrenamientoPrediccionAusencias,
    crear_worker_entrenamiento_prediccion,
)
from clinicdesk.app.ui.jobs.job_manager import JobCancelledError


class _FakeEntrenarUc:
    def __init__(self, *, resultado: object = None, exc: Exception | None = None) -> None:
        self.resultado = resultado
        self.exc = exc
        self.llamadas = 0

    def ejecutar(self):
        self.llamadas += 1
        if self.exc is not None:
            raise self.exc
        return self.resultado


class _FakeProveedorConexion:
    def __init__(self) -> None:
        self.cierres = 0

    def cerrar_conexion_del_hilo_actual(self) -> None:
        self.cierres += 1


class _FakeMainWindow:
    def __init__(self) -> None:
        self.kwargs = None

    def run_premium_job(self, **kwargs) -> None:
        self.kwargs = kwargs


def test_worker_entrenamiento_reporta_progreso_y_cierra_conexion() -> None:
    entrenar_uc = _FakeEntrenarUc(resultado={"ok": True})
    proveedor = _FakeProveedorConexion()
    worker = crear_worker_entrenamiento_prediccion(entrenar_uc=entrenar_uc, proveedor_conexion=proveedor)
    progreso: list[tuple[int, str]] = []

    class _Token:
        is_cancelled = False

    resultado = worker(_Token(), lambda p, k: progreso.append((p, k)))

    assert resultado == {"ok": True}
    assert entrenar_uc.llamadas == 1
    assert proveedor.cierres == 1
    assert progreso[-1] == (100, "job.prediccion_ausencias_entrenar.progress.done")


def test_worker_entrenamiento_normaliza_reason_code_en_excepcion() -> None:
    entrenar_uc = _FakeEntrenarUc(exc=EntrenamientoPrediccionError("dataset_empty"))
    worker = crear_worker_entrenamiento_prediccion(entrenar_uc=entrenar_uc, proveedor_conexion=None)

    class _Token:
        is_cancelled = False

    with pytest.raises(RuntimeError, match="dataset_empty"):
        worker(_Token(), lambda _p, _k: None)


def test_worker_entrenamiento_respeta_cancelacion() -> None:
    entrenar_uc = _FakeEntrenarUc(resultado={"ok": True})
    worker = crear_worker_entrenamiento_prediccion(entrenar_uc=entrenar_uc, proveedor_conexion=None)

    class _Token:
        is_cancelled = True

    with pytest.raises(JobCancelledError):
        worker(_Token(), lambda _p, _k: None)

    assert entrenar_uc.llamadas == 0


def test_coordinador_dispara_run_premium_job_con_wiring_canonic() -> None:
    coordinador = CoordinadorEntrenamientoPrediccionAusencias(entrenar_uc=_FakeEntrenarUc(), proveedor_conexion=None)
    parent = _FakeMainWindow()

    lanzado = coordinador.iniciar(parent_window=parent, on_success=lambda _r: None, on_failed=lambda _e: None)

    assert lanzado is True
    assert parent.kwargs is not None
    assert parent.kwargs["job_id"] == "prediccion_ausencias_entrenar"
    assert parent.kwargs["title_key"] == "job.prediccion_ausencias_entrenar.title"
