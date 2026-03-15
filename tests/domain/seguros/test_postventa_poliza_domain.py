from datetime import date

from clinicdesk.app.domain.seguros.postventa import (
    AseguradoPrincipalSeguro,
    BeneficiarioSeguro,
    CoberturaActivaPolizaSeguro,
    EstadoAseguradoSeguro,
    EstadoPolizaSeguro,
    EstadoRenovacionPolizaSeguro,
    PolizaSeguro,
    RenovacionPolizaSeguro,
    VigenciaPolizaSeguro,
)


def test_contrato_poliza_postventa_tipado() -> None:
    poliza = PolizaSeguro(
        id_poliza="pol-1",
        id_oportunidad_origen="opp-1",
        id_paciente="pac-1",
        id_plan="clinica_integral",
        estado=EstadoPolizaSeguro.ACTIVA,
        titular=AseguradoPrincipalSeguro(
            id_asegurado="tit-1",
            nombre="Ana",
            documento="DOC-1",
            estado=EstadoAseguradoSeguro.ACTIVO,
        ),
        beneficiarios=(
            BeneficiarioSeguro(
                id_beneficiario="ben-1",
                nombre="Luis",
                parentesco="hijo",
                estado=EstadoAseguradoSeguro.ACTIVO,
            ),
        ),
        vigencia=VigenciaPolizaSeguro(fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)),
        renovacion=RenovacionPolizaSeguro(
            fecha_renovacion_prevista=date(2026, 12, 31),
            estado=EstadoRenovacionPolizaSeguro.PENDIENTE,
        ),
        coberturas=(CoberturaActivaPolizaSeguro(codigo_cobertura="COB_BASE", descripcion="base", activa=True),),
        incidencias=(),
    )

    assert poliza.estado is EstadoPolizaSeguro.ACTIVA
    assert poliza.beneficiarios[0].parentesco == "hijo"
    assert poliza.renovacion.estado is EstadoRenovacionPolizaSeguro.PENDIENTE
