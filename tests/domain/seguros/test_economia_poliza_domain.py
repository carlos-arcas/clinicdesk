from datetime import date

from clinicdesk.app.domain.seguros.economia_poliza import CuotaPolizaSeguro, EstadoCuotaPolizaSeguro


def test_contrato_cuota_poliza_seguro_tipado() -> None:
    cuota = CuotaPolizaSeguro(
        id_cuota="cu-1",
        id_poliza="pol-1",
        periodo="2026-01",
        fecha_emision=date(2026, 1, 1),
        fecha_vencimiento=date(2026, 1, 10),
        importe=99.9,
        estado=EstadoCuotaPolizaSeguro.EMITIDA,
        fecha_pago=None,
    )

    assert cuota.id_poliza == "pol-1"
    assert cuota.estado is EstadoCuotaPolizaSeguro.EMITIDA
