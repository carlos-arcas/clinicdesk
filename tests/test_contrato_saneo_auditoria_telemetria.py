from __future__ import annotations

import json

from clinicdesk.app.application.usecases.registrar_auditoria_acceso import (
    _sanear_metadata_acceso,
)
from clinicdesk.app.application.usecases.registrar_telemetria import _sanear_contexto_telemetria
from clinicdesk.app.infrastructure.sqlite.persistencia_segura_auditoria_telemetria import (
    sanear_contexto_telemetria_para_persistencia,
    sanear_evento_auditoria_para_persistencia,
)


def test_contrato_auditoria_conserva_claves_permitidas() -> None:
    metadata = {"origen": "auditoria", "resultado": "ok", "duracion_ms": 17}

    metadata_app, redaccion_app = _sanear_metadata_acceso(metadata)
    _, _, metadata_persistencia, redaccion_persistencia = sanear_evento_auditoria_para_persistencia(
        usuario="auditor",
        entidad_id="22",
        metadata_json=metadata,
    )

    assert redaccion_app is False
    assert redaccion_persistencia is False
    assert metadata_app == metadata
    assert metadata_persistencia == metadata


def test_contrato_auditoria_descarta_clave_desconocida_safe_by_default() -> None:
    metadata = {"origen": "auditoria", "token_privado": "secreto"}

    metadata_app, redaccion_app = _sanear_metadata_acceso(metadata)
    _, _, metadata_persistencia, redaccion_persistencia = sanear_evento_auditoria_para_persistencia(
        usuario="auditor",
        entidad_id="22",
        metadata_json=metadata,
    )

    assert metadata_app == {"origen": "auditoria"}
    assert metadata_persistencia == {"origen": "auditoria", "redaccion_aplicada": True}
    assert redaccion_app is True
    assert redaccion_persistencia is True


def test_contrato_telemetria_conserva_claves_permitidas() -> None:
    contexto = "page=auditoria;resultado=ok;vista=listado"

    contexto_app, redaccion_app = _sanear_contexto_telemetria(contexto)
    contexto_persistencia, redaccion_persistencia = sanear_contexto_telemetria_para_persistencia(contexto)

    assert contexto_app == contexto
    assert contexto_persistencia == contexto
    assert redaccion_app is False
    assert redaccion_persistencia is False


def test_contrato_telemetria_descarta_clave_desconocida_safe_by_default() -> None:
    contexto = "page=auditoria;token_privado=secreto"

    contexto_app, redaccion_app = _sanear_contexto_telemetria(contexto)
    contexto_persistencia, redaccion_persistencia = sanear_contexto_telemetria_para_persistencia(contexto)

    assert contexto_app == "page=auditoria;redaccion_aplicada=true"
    assert contexto_persistencia == "page=auditoria;redaccion_aplicada=true"
    assert redaccion_app is True
    assert redaccion_persistencia is True


def test_contrato_no_persiste_pii_en_claro_ni_anidada() -> None:
    metadata = {
        "origen": "auditoria",
        "contexto": {
            "email": "ana@test.com",
            "telefono": "600123123",
            "tlf": "611111111",
            "movil": "622222222",
            "dni": "12345678Z",
            "nif": "12345678Z",
            "historia_clinica": "HC-999",
            "direccion": "Avenida Salud 1",
            "detalle": "email ana@test.com telefono 600123123",
            "lista": [{"dni": "12345678Z"}, "ok"],
        },
    }

    _, _, metadata_persistencia, redaccion_persistencia = sanear_evento_auditoria_para_persistencia(
        usuario="ana@test.com",
        entidad_id="12345678Z",
        metadata_json=metadata,
    )

    serializado = json.dumps(metadata_persistencia, ensure_ascii=False)
    for valor in (
        "ana@test.com",
        "600123123",
        "611111111",
        "622222222",
        "12345678Z",
        "HC-999",
        "Avenida Salud 1",
    ):
        assert valor not in serializado
    assert metadata_persistencia is not None
    assert metadata_persistencia["redaccion_aplicada"] is True
    assert redaccion_persistencia is True


def test_contrato_marca_redaccion_aplicada_solo_si_hay_saneo() -> None:
    _, _, metadata_sin_saneo, _ = sanear_evento_auditoria_para_persistencia(
        usuario="auditor",
        entidad_id="22",
        metadata_json={"origen": "auditoria"},
    )
    _, _, metadata_con_saneo, _ = sanear_evento_auditoria_para_persistencia(
        usuario="auditor",
        entidad_id="22",
        metadata_json={"origen": "auditoria", "dni": "12345678Z"},
    )

    assert metadata_sin_saneo == {"origen": "auditoria"}
    assert metadata_con_saneo == {"origen": "auditoria", "redaccion_aplicada": True}


def test_contrato_json_anidado_telemetria_saneado_en_app_y_persistencia() -> None:
    contexto = json.dumps(
        {
            "page": "auditoria",
            "contexto": {
                "detalle": "dni 12345678Z",
                "lista": [{"email": "ana@test.com"}, "ok"],
            },
            "token_privado": "secreto",
        },
        ensure_ascii=False,
    )

    contexto_app, redaccion_app = _sanear_contexto_telemetria(contexto)
    contexto_persistencia, redaccion_persistencia = sanear_contexto_telemetria_para_persistencia(contexto)

    assert contexto_app is not None
    assert contexto_persistencia is not None
    json_app = json.loads(contexto_app)
    json_persistencia = json.loads(contexto_persistencia)
    assert "token_privado" not in json_app
    assert "token_privado" not in json_persistencia
    assert "12345678Z" not in json.dumps(json_app, ensure_ascii=False)
    assert "12345678Z" not in json.dumps(json_persistencia, ensure_ascii=False)
    assert "ana@test.com" not in json.dumps(json_app, ensure_ascii=False)
    assert "ana@test.com" not in json.dumps(json_persistencia, ensure_ascii=False)
    assert json_app["redaccion_aplicada"] is True
    assert json_persistencia["redaccion_aplicada"] is True
    assert redaccion_app is True
    assert redaccion_persistencia is True
