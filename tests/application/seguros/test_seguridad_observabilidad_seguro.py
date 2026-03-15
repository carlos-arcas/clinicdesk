from __future__ import annotations

from datetime import date

import pytest

from clinicdesk.app.application.seguros.seguridad_observabilidad import (
    MetadataSeguraSeguroError,
    construir_evento_log_seguro,
    sanitizar_metadata_segura_seguro,
    snapshot_campania_ejecutiva_segura,
    snapshot_economia_poliza_segura,
    snapshot_postventa_seguro,
)
from clinicdesk.app.application.seguros import CampaniaAccionableSeguro
from clinicdesk.app.domain.seguros import (
    AseguradoPrincipalSeguro,
    BeneficiarioSeguro,
    EstadoAseguradoSeguro,
    EstadoPagoPolizaSeguro,
    EstadoPolizaSeguro,
    ResumenEconomicoPolizaSeguro,
    EstadoRenovacionPolizaSeguro,
    NivelRiesgoEconomicoPolizaSeguro,
    PolizaSeguro,
    RenovacionPolizaSeguro,
    VigenciaPolizaSeguro,
)


def _poliza_demo() -> PolizaSeguro:
    return PolizaSeguro(
        id_poliza="pol-1",
        id_oportunidad_origen="opp-1",
        id_paciente="pac-1",
        id_plan="plan-a",
        estado=EstadoPolizaSeguro.ACTIVA,
        titular=AseguradoPrincipalSeguro(
            id_asegurado="tit-pol-1",
            nombre="Ana López",
            documento="12345678A",
            estado=EstadoAseguradoSeguro.ACTIVO,
        ),
        beneficiarios=(BeneficiarioSeguro("ben-1", "Juan", "HIJO", EstadoAseguradoSeguro.ACTIVO),),
        vigencia=VigenciaPolizaSeguro(date(2026, 1, 1), date(2026, 12, 31)),
        renovacion=RenovacionPolizaSeguro(date(2026, 12, 31), EstadoRenovacionPolizaSeguro.PENDIENTE),
        coberturas=(),
        incidencias=(),
    )


def test_metadata_segura_por_whitelist_y_sin_claves_sensibles() -> None:
    saneada = sanitizar_metadata_segura_seguro(
        "logging_tecnico_seguro",
        {
            "horizonte": "30d",
            "volumen": 12,
            "email": "ana@test.com",
            "payload": {"documento": "123"},
        },
    )

    assert saneada == {"horizonte": "30d", "volumen": 12}


def test_contexto_invalido_falla_explicito() -> None:
    with pytest.raises(MetadataSeguraSeguroError):
        sanitizar_metadata_segura_seguro("no_soportado", {})


def test_snapshot_postventa_no_expone_nombre_ni_documento() -> None:
    snapshot = snapshot_postventa_seguro(_poliza_demo())

    assert snapshot["titular_ref"] == "tit-pol-1"
    serializado = str(snapshot)
    assert "Ana López" not in serializado
    assert "12345678A" not in serializado


def test_snapshot_economia_usa_tramo_y_no_importe_detallado() -> None:
    resumen = ResumenEconomicoPolizaSeguro(
        id_poliza="pol-1",
        estado_pago=EstadoPagoPolizaSeguro.IMPAGADA,
        nivel_riesgo=NivelRiesgoEconomicoPolizaSeguro.ALTO,
        total_emitido=1200.0,
        total_pagado=600.0,
        total_pendiente=600.0,
        cuotas_emitidas=12,
        cuotas_pagadas=6,
        cuotas_vencidas=2,
        cuotas_impagadas=1,
        suspendida=False,
        reactivable=False,
        motivo_estado="cuotas impagadas",
    )

    snapshot = snapshot_economia_poliza_segura(resumen)

    assert snapshot["pendiente_tramo"] == ">=500"
    assert "600.0" not in str(snapshot)


def test_campania_activa_resume_ids_en_lugar_de_lista_completa() -> None:
    campania = CampaniaAccionableSeguro(
        id_campania="camp-1",
        titulo="Retención",
        criterio="renovación",
        tamano_estimado=4,
        motivo="riesgo",
        accion_recomendada="contactar",
        cautela="muestra",
        ids_oportunidad=("opp-1", "opp-2", "opp-3"),
    )

    snapshot = snapshot_campania_ejecutiva_segura(campania)

    assert snapshot["ids_resumen"] == "3 ids"


def test_evento_log_seguro_no_arrastra_payload_ni_pii() -> None:
    payload = construir_evento_log_seguro(
        "logging_tecnico_seguro",
        "forecast_seguro_generado",
        {"horizonte": "30", "payload": {"documento": "123"}, "email": "ana@test.com"},
    )

    assert payload == {"horizonte": "30", "evento": "forecast_seguro_generado"}
