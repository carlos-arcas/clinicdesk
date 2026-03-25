from __future__ import annotations

from clinicdesk.app.ui.lifecycle.controlador_cierre_app import ControladorCierreApp


class RelojFalso:
    def __init__(self) -> None:
        self.ahora = 0

    def avanzar(self, ms: int) -> None:
        self.ahora += ms

    def __call__(self) -> int:
        return self.ahora


def test_cierre_inmediato_sin_jobs() -> None:
    reloj = RelojFalso()
    controlador = ControladorCierreApp(timeout_ms=1000, reloj_ms=reloj)

    decision = controlador.solicitar_cierre(ids_jobs_activos=())

    assert decision.permitir_cierre is True
    assert decision.ignorar_evento is False
    assert controlador.permitir_cierre_directo is True


def test_cierre_con_jobs_inicia_shutdown_idempotente() -> None:
    reloj = RelojFalso()
    controlador = ControladorCierreApp(timeout_ms=1000, reloj_ms=reloj)

    primera = controlador.solicitar_cierre(ids_jobs_activos=("job-1",))
    segunda = controlador.solicitar_cierre(ids_jobs_activos=("job-1",))

    assert primera.iniciar_shutdown is True
    assert primera.toast_key == "job.shutdown.requested"
    assert segunda.iniciar_shutdown is False
    assert segunda.ignorar_evento is True
    assert controlador.cierre_en_progreso is True


def test_shutdown_completa_antes_de_timeout() -> None:
    reloj = RelojFalso()
    controlador = ControladorCierreApp(timeout_ms=1000, reloj_ms=reloj)

    controlador.solicitar_cierre(ids_jobs_activos=("job-1", "job-2"))
    reloj.avanzar(300)
    decision = controlador.registrar_cierre_completado()

    assert decision.completar_cierre is True
    assert controlador.cierre_en_progreso is False
    assert controlador.permitir_cierre_directo is True


def test_timeout_aborta_cierre_y_restablece_estado() -> None:
    reloj = RelojFalso()
    controlador = ControladorCierreApp(timeout_ms=500, reloj_ms=reloj)

    controlador.solicitar_cierre(ids_jobs_activos=("job-bloqueado",))
    reloj.avanzar(499)
    sin_timeout = controlador.intentar_timeout(ids_jobs_activos=("job-bloqueado",))
    reloj.avanzar(1)
    con_timeout = controlador.intentar_timeout(ids_jobs_activos=("job-bloqueado",))

    assert sin_timeout.restaurar_estado_ui is False
    assert con_timeout.restaurar_estado_ui is True
    assert con_timeout.toast_key == "job.shutdown.timeout"
    assert controlador.cierre_en_progreso is False
    assert controlador.permitir_cierre_directo is False


def test_reintento_luego_de_timeout() -> None:
    reloj = RelojFalso()
    controlador = ControladorCierreApp(timeout_ms=500, reloj_ms=reloj)

    controlador.solicitar_cierre(ids_jobs_activos=("job-bloqueado",))
    reloj.avanzar(500)
    controlador.intentar_timeout(ids_jobs_activos=("job-bloqueado",))

    reintento = controlador.solicitar_cierre(ids_jobs_activos=("job-bloqueado",))

    assert reintento.iniciar_shutdown is True
    assert controlador.cierre_en_progreso is True
