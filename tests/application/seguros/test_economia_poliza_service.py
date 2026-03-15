from datetime import date

from clinicdesk.app.application.seguros.economia_poliza import (
    GestionEconomicaPolizaSeguroService,
    SolicitudEmitirCuotaPolizaSeguro,
    SolicitudRegistrarImpagoSeguro,
    SolicitudRegistrarPagoCuotaSeguro,
    construir_resumen_economico_poliza,
)
from clinicdesk.app.domain.seguros.economia_poliza import (
    CuotaPolizaSeguro,
    EstadoCuotaPolizaSeguro,
    EstadoPagoPolizaSeguro,
    ImpagoPolizaSeguro,
    NivelRiesgoEconomicoPolizaSeguro,
    ReactivacionPolizaSeguro,
    SuspensionPolizaSeguro,
)


class RepoEconomiaFake:
    def __init__(self) -> None:
        self.cuotas: dict[str, CuotaPolizaSeguro] = {}
        self.suspendidas: set[str] = set()

    def guardar_cuota(self, cuota: CuotaPolizaSeguro) -> None:
        self.cuotas[cuota.id_cuota] = cuota

    def obtener_cuota(self, id_cuota: str) -> CuotaPolizaSeguro:
        return self.cuotas[id_cuota]

    def listar_cuotas_poliza(self, id_poliza: str) -> tuple[CuotaPolizaSeguro, ...]:
        return tuple(item for item in self.cuotas.values() if item.id_poliza == id_poliza)

    def listar_cuotas(self) -> tuple[CuotaPolizaSeguro, ...]:
        return tuple(self.cuotas.values())

    def guardar_impago(self, evento: ImpagoPolizaSeguro) -> None:
        return None

    def guardar_suspension(self, evento: SuspensionPolizaSeguro) -> None:
        self.suspendidas.add(evento.id_poliza)

    def guardar_reactivacion(self, evento: ReactivacionPolizaSeguro) -> None:
        self.suspendidas.discard(evento.id_poliza)

    def tiene_suspension_activa(self, id_poliza: str) -> bool:
        return id_poliza in self.suspendidas


def test_reglas_resumen_impago_y_riesgo_alto() -> None:
    resumen = construir_resumen_economico_poliza(
        id_poliza="pol-1",
        cuotas=(
            CuotaPolizaSeguro(
                id_cuota="c1",
                id_poliza="pol-1",
                periodo="2026-01",
                fecha_emision=date(2026, 1, 1),
                fecha_vencimiento=date(2026, 1, 5),
                importe=100,
                estado=EstadoCuotaPolizaSeguro.IMPAGADA,
            ),
        ),
        hoy=date(2026, 1, 10),
        suspension_activa=False,
    )

    assert resumen.estado_pago is EstadoPagoPolizaSeguro.IMPAGADA
    assert resumen.nivel_riesgo is NivelRiesgoEconomicoPolizaSeguro.ALTO


def test_service_emitir_pago_e_impago() -> None:
    repo = RepoEconomiaFake()
    servicio = GestionEconomicaPolizaSeguroService(repo)

    servicio.emitir_cuota(
        SolicitudEmitirCuotaPolizaSeguro(
            id_cuota="c1",
            id_poliza="pol-1",
            periodo="2026-01",
            fecha_emision=date(2026, 1, 1),
            fecha_vencimiento=date(2026, 1, 3),
            importe=130,
        )
    )
    servicio.registrar_impago(
        SolicitudRegistrarImpagoSeguro(
            id_evento="imp-1",
            id_poliza="pol-1",
            id_cuota="c1",
            fecha_evento=date(2026, 1, 6),
            motivo="devolucion",
        )
    )

    resumen = servicio.obtener_resumen_poliza("pol-1", hoy=date(2026, 1, 7))
    assert resumen.estado_pago is EstadoPagoPolizaSeguro.IMPAGADA

    servicio.registrar_pago_cuota(SolicitudRegistrarPagoCuotaSeguro(id_cuota="c1", fecha_pago=date(2026, 1, 8)))
    resumen_pagada = servicio.obtener_resumen_poliza("pol-1", hoy=date(2026, 1, 8))
    assert resumen_pagada.estado_pago is EstadoPagoPolizaSeguro.AL_DIA
