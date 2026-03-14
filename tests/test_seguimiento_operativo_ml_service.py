from __future__ import annotations

from clinicdesk.app.application.services.seguimiento_operativo_ml_service import (
    AccionHumanaItemML,
    AccionTomadaML,
    EstadoSeguimientoItemML,
    SeguimientoOperativoMLService,
)


class _RepoMemoria:
    def __init__(self) -> None:
        self._items: list = []

    def registrar_decision(self, decision) -> None:
        self._items.append(decision)

    def obtener_historial(self, cita_id: str):
        return tuple(item for item in self._items if item.cita_id == cita_id)


def test_registra_y_devuelve_estado_actual() -> None:
    service = SeguimientoOperativoMLService(_RepoMemoria())

    resultado = service.registrar_accion(
        AccionTomadaML(
            cita_id="101",
            prioridad_ml="alta",
            accion_sugerida_ml="confirmar_hoy",
            accion_humana=AccionHumanaItemML.REVISAR_MANUAL,
            estado=EstadoSeguimientoItemML.REVISADO,
            nota_corta="Paciente contactado",
            actor="recepcion",
        )
    )

    assert resultado.cita_id == "101"
    assert resultado.estado_actual == EstadoSeguimientoItemML.REVISADO
    assert resultado.accion_humana_actual == AccionHumanaItemML.REVISAR_MANUAL
    assert resultado.historial[-1].actor == "recepcion"


def test_normaliza_nota_larga() -> None:
    service = SeguimientoOperativoMLService(_RepoMemoria())

    resultado = service.registrar_accion(
        AccionTomadaML(
            cita_id="9",
            prioridad_ml="media",
            accion_sugerida_ml="revisar_manual",
            accion_humana=AccionHumanaItemML.SIN_ACCION,
            estado=EstadoSeguimientoItemML.POSPUESTO,
            nota_corta="x" * 220,
        )
    )

    assert len(resultado.historial[-1].nota_corta) == 160


def test_objetivo_navegacion_requiere_cita_numerica() -> None:
    service = SeguimientoOperativoMLService(_RepoMemoria())

    assert service.construir_objetivo_navegacion("abc") is None
    objetivo = service.construir_objetivo_navegacion("22")
    assert objetivo is not None
    assert objetivo.cita_id == 22
    assert objetivo.destino == "citas"
