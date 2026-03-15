from datetime import date

import pytest

from clinicdesk.app.application.seguros.postventa import (
    GestionPostventaPolizaSeguroService,
    SolicitudAltaPolizaDesdeConversion,
    SolicitudRegistrarIncidenciaPoliza,
)
from clinicdesk.app.domain.seguros.comercial import (
    CandidatoSeguro,
    EstadoOportunidadSeguro,
    OportunidadSeguro,
)
from clinicdesk.app.domain.seguros.postventa import TipoIncidenciaPolizaSeguro


class RepositorioPolizaFake:
    def __init__(self) -> None:
        self.polizas = {}

    def guardar_poliza(self, poliza) -> None:
        self.polizas[poliza.id_poliza] = poliza

    def obtener_poliza(self, id_poliza: str):
        return self.polizas[id_poliza]

    def listar_polizas(self, filtro):
        return tuple(self.polizas.values())

    def guardar_incidencia(self, id_poliza: str, incidencia) -> None:
        poliza = self.polizas[id_poliza]
        self.polizas[id_poliza] = poliza.__class__(
            id_poliza=poliza.id_poliza,
            id_oportunidad_origen=poliza.id_oportunidad_origen,
            id_paciente=poliza.id_paciente,
            id_plan=poliza.id_plan,
            estado=poliza.estado,
            titular=poliza.titular,
            beneficiarios=poliza.beneficiarios,
            vigencia=poliza.vigencia,
            renovacion=poliza.renovacion,
            coberturas=poliza.coberturas,
            incidencias=poliza.incidencias + (incidencia,),
        )


class RepositorioOportunidadFake:
    def __init__(self, estado: EstadoOportunidadSeguro) -> None:
        self._oportunidad = OportunidadSeguro(
            id_oportunidad="opp-1",
            candidato=CandidatoSeguro(id_candidato="cand-1", id_paciente="pac-1", segmento="SEG"),
            plan_origen_id="externo_basico",
            plan_destino_id="clinica_integral",
            estado_actual=estado,
            clasificacion_motor="ALTA",
            perfil_comercial=None,
            evaluacion_fit=None,
            seguimientos=(),
            resultado_comercial=None,
        )

    def obtener_oportunidad(self, id_oportunidad: str) -> OportunidadSeguro:
        assert id_oportunidad == self._oportunidad.id_oportunidad
        return self._oportunidad


def test_materializar_poliza_desde_conversion() -> None:
    servicio = GestionPostventaPolizaSeguroService(
        RepositorioPolizaFake(),
        RepositorioOportunidadFake(EstadoOportunidadSeguro.CONVERTIDA),
    )

    poliza = servicio.materializar_poliza_desde_conversion(
        SolicitudAltaPolizaDesdeConversion(
            id_oportunidad="opp-1",
            id_poliza="pol-1",
            nombre_titular="Ana",
            documento_titular="DOC-1",
            fecha_inicio=date(2026, 1, 1),
        )
    )

    assert poliza.id_plan == "clinica_integral"
    assert poliza.vigencia.fecha_fin == date(2027, 1, 1)


def test_rechaza_materializar_si_no_convertida() -> None:
    servicio = GestionPostventaPolizaSeguroService(
        RepositorioPolizaFake(),
        RepositorioOportunidadFake(EstadoOportunidadSeguro.EN_SEGUIMIENTO),
    )

    with pytest.raises(ValueError):
        servicio.materializar_poliza_desde_conversion(
            SolicitudAltaPolizaDesdeConversion(
                id_oportunidad="opp-1",
                id_poliza="pol-1",
                nombre_titular="Ana",
                documento_titular="DOC-1",
                fecha_inicio=date(2026, 1, 1),
            )
        )


def test_registrar_incidencia_postventa() -> None:
    repo_poliza = RepositorioPolizaFake()
    servicio = GestionPostventaPolizaSeguroService(
        repo_poliza,
        RepositorioOportunidadFake(EstadoOportunidadSeguro.CONVERTIDA),
    )
    servicio.materializar_poliza_desde_conversion(
        SolicitudAltaPolizaDesdeConversion(
            id_oportunidad="opp-1",
            id_poliza="pol-1",
            nombre_titular="Ana",
            documento_titular="DOC-1",
            fecha_inicio=date(2026, 1, 1),
        )
    )

    incidencia = servicio.registrar_incidencia(
        SolicitudRegistrarIncidenciaPoliza(
            id_poliza="pol-1",
            id_incidencia="inc-1",
            tipo=TipoIncidenciaPolizaSeguro.DOCUMENTACION_PENDIENTE,
            descripcion="falta documento",
            fecha_apertura=date(2026, 2, 10),
        )
    )

    assert incidencia.tipo is TipoIncidenciaPolizaSeguro.DOCUMENTACION_PENDIENTE
    assert len(repo_poliza.obtener_poliza("pol-1").incidencias) == 1
