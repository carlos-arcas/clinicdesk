from __future__ import annotations

import logging
from pathlib import Path

from clinicdesk.app.application.usecases.exportar_auditoria_csv import _obtener_columna_permitida
from clinicdesk.app.application.usecases.registrar_auditoria_acceso import _sanear_metadata_acceso
from clinicdesk.app.application.usecases.registrar_telemetria import _sanear_contexto_telemetria
from clinicdesk.app.bootstrap_logging import _PIIRedactionFilter
from clinicdesk.app.common.politica_placeholders_pii import (
    TOKEN_PII_DIRECCION,
    TOKEN_PII_DNI_NIF,
    TOKEN_PII_EMAIL,
    TOKEN_PII_HISTORIA_CLINICA,
    TOKEN_PII_TELEFONO,
)
from clinicdesk.app.common.redaccion_pii import redactar_texto_pii
from clinicdesk.app.infrastructure.sqlite.persistencia_segura_auditoria_telemetria import (
    sanear_contexto_telemetria_para_persistencia,
)


RUTAS_CRITICAS = (
    "clinicdesk/app/common/redaccion_pii.py",
    "clinicdesk/app/common/politica_saneo_auditoria_telemetria.py",
    "clinicdesk/app/infrastructure/sqlite/persistencia_segura_auditoria_telemetria.py",
    "clinicdesk/app/application/usecases/registrar_auditoria_acceso.py",
    "clinicdesk/app/application/usecases/registrar_telemetria.py",
    "clinicdesk/app/queries/auditoria_accesos_queries.py",
    "clinicdesk/app/application/usecases/exportar_auditoria_csv.py",
)

TOKENS_DIVERGENTES_PROHIBIDOS = (
    "[REDACTED_DNI]",
    "[REDACTED_NIF]",
    "[REDACTED_TELEFONO]",
    "[REDACTED_HC]",
    "[REDACTED_ADDRESS]",
)


def test_politica_canonica_en_texto_runtime_y_saneo_export() -> None:
    texto = (
        "email ana@test.com telefono 600123123 dni 12345678Z "
        "hc HC-123 direccion Avenida Salud 1"
    )

    texto_redactado, redaccion_texto = redactar_texto_pii(texto)
    contexto_app, redaccion_app = _sanear_contexto_telemetria(f"detalle={texto}")
    contexto_persistencia, redaccion_persistencia = sanear_contexto_telemetria_para_persistencia(f"detalle={texto}")
    columna_export = _obtener_columna_permitida({"entidad_id": texto}, "entidad_id")

    assert redaccion_texto is True
    assert redaccion_app is True
    assert redaccion_persistencia is True
    for token in (
        TOKEN_PII_EMAIL,
        TOKEN_PII_TELEFONO,
        TOKEN_PII_DNI_NIF,
        TOKEN_PII_HISTORIA_CLINICA,
        TOKEN_PII_DIRECCION,
    ):
        assert token in texto_redactado
        assert contexto_app is not None and token in contexto_app
        assert contexto_persistencia is not None and token in contexto_persistencia
        assert token in columna_export


def test_politica_canonica_en_estructura_anidada_y_preserva_no_sensible() -> None:
    metadata, redaccion = _sanear_metadata_acceso(
        {
            "origen": "auditoria",
            "contexto": {
                "detalle": "contacto ana@test.com",
                "lista": [{"nota": "dni 12345678Z"}, "ok"],
            },
            "resultado": "ok",
        }
    )

    assert redaccion is True
    assert metadata is not None
    assert metadata["origen"] == "auditoria"
    assert metadata["resultado"] == "ok"
    assert metadata["contexto"]["detalle"] == f"contacto {TOKEN_PII_EMAIL}"
    assert metadata["contexto"]["lista"][0]["nota"] == f"dni {TOKEN_PII_DNI_NIF}"


def test_contexto_kv_marca_redaccion_aplicada_cuando_hay_saneo() -> None:
    contexto, redaccion = _sanear_contexto_telemetria("page=auditoria;detalle=email ana@test.com")

    assert redaccion is True
    assert contexto is not None
    assert "redaccion_aplicada=true" in contexto


def test_logging_marca_reason_code_pii_redacted() -> None:
    filtro = _PIIRedactionFilter(permitir_pii=False)
    record = logging.LogRecord(
        name="clinicdesk.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="email ana@test.com",
        args=(),
        exc_info=None,
    )

    assert filtro.filter(record) is True
    assert getattr(record, "reason_code") == "pii_redacted"


def test_guardrail_no_permite_tokens_divergentes_en_modulos_criticos() -> None:
    for ruta in RUTAS_CRITICAS:
        contenido = Path(ruta).read_text(encoding="utf-8")
        for token in TOKENS_DIVERGENTES_PROHIBIDOS:
            assert token not in contenido, f"Token divergente detectado en {ruta}: {token}"
