from __future__ import annotations

from datetime import date

from clinicdesk.app.application.seguros import (
    AprendizajeEjecucionSeguro,
    BloqueoOperativoSeguro,
    CierreSemanalSeguro,
    CumplimientoPlanSeguro,
    PeriodoSemanaSeguro,
    ResumenSemanaSeguro,
    TareaComercialSeguro,
)
from clinicdesk.app.application.seguros.agenda_alertas_contratos import EstadoTareaSeguro, PrioridadAlertaSeguro
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.seguros.agenda_ui_support import construir_texto_bloqueos, construir_texto_cierre_semanal


def _tarea() -> TareaComercialSeguro:
    return TareaComercialSeguro(
        id_tarea="t1",
        tipo="RENOVACION",
        prioridad=PrioridadAlertaSeguro.CRITICA,
        motivo="x",
        accion_sugerida="accion",
        fecha_objetivo=date(2026, 3, 14),
        contexto="ctx",
        estado=EstadoTareaSeguro.PENDIENTE,
    )


def test_textos_cierre_muestran_patrones_y_bloqueos() -> None:
    i18n = I18nManager()
    periodo = PeriodoSemanaSeguro(date(2026, 3, 10), date(2026, 3, 16), date(2026, 3, 16))
    tarea = _tarea()
    cumplimiento = CumplimientoPlanSeguro(periodo, (tarea,), (), (tarea,), (), (tarea,), 0.0)
    bloqueo = BloqueoOperativoSeguro(periodo, "BLQ-X", "renovaciones postergadas", "evid", "asignar")
    cierre = CierreSemanalSeguro(periodo, (tarea,), (), (tarea,), (), (bloqueo,), ("patron-1",), "priorizar")
    resumen = ResumenSemanaSeguro(
        cierre=cierre,
        cumplimiento=cumplimiento,
        desvios=(),
        bloqueos=(bloqueo,),
        aprendizaje=AprendizajeEjecucionSeguro(periodo, (), (), (), (), "x"),
    )

    texto_cierre = construir_texto_cierre_semanal(i18n, resumen)
    texto_bloqueos = construir_texto_bloqueos(i18n, resumen)

    assert "Cumplimiento" in texto_cierre
    assert "patron-1" in texto_cierre
    assert "BLQ-X" in texto_bloqueos


def test_textos_cierre_sin_bloqueos() -> None:
    i18n = I18nManager()
    periodo = PeriodoSemanaSeguro(date(2026, 3, 10), date(2026, 3, 16), date(2026, 3, 16))
    tarea = _tarea()
    cierre = CierreSemanalSeguro(periodo, (tarea,), (tarea,), (), (), (), (), "mantener")
    resumen = ResumenSemanaSeguro(
        cierre=cierre,
        cumplimiento=CumplimientoPlanSeguro(periodo, (tarea,), (tarea,), (), (), (), 100.0),
        desvios=(),
        bloqueos=(),
        aprendizaje=AprendizajeEjecucionSeguro(periodo, (), (), (), (), "x"),
    )

    texto = construir_texto_bloqueos(i18n, resumen)

    assert "Sin bloqueos" in texto
