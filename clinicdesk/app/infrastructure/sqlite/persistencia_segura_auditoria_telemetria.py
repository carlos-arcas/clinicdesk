from __future__ import annotations

import json
from typing import Any

from clinicdesk.app.common.politica_saneo_auditoria_telemetria import (
    CLAVES_CONTEXTO_TELEMETRIA_PERMITIDAS,
    CLAVES_METADATA_AUDITORIA_PERMITIDAS,
    es_clave_sensible_auditoria_telemetria,
)
from clinicdesk.app.common.redaccion_pii import sanear_valor_pii


def sanear_evento_auditoria_para_persistencia(
    *,
    usuario: str,
    entidad_id: str,
    metadata_json: dict[str, Any] | None,
) -> tuple[str, str, dict[str, Any] | None, bool]:
    usuario_saneado, redaccion_usuario = sanear_valor_pii(usuario, clave="usuario")
    entidad_id_saneado, redaccion_entidad_id = sanear_valor_pii(entidad_id, clave="entidad_id")

    metadata_saneada: dict[str, Any] | None = None
    redaccion_metadata = False
    if metadata_json is not None:
        metadata_filtrada, claves_descartadas = _filtrar_diccionario_raiz_safe_by_default(
            metadata_json, CLAVES_METADATA_AUDITORIA_PERMITIDAS
        )
        valor_metadata, redaccion_metadata = sanear_valor_pii(metadata_filtrada, clave="metadata")
        redaccion_metadata = redaccion_metadata or claves_descartadas
        metadata_saneada = _to_dict(valor_metadata)
        if redaccion_metadata and metadata_saneada is not None:
            metadata_saneada["redaccion_aplicada"] = True

    redaccion_aplicada = redaccion_usuario or redaccion_entidad_id or redaccion_metadata
    return str(usuario_saneado), str(entidad_id_saneado), metadata_saneada, redaccion_aplicada


def sanear_contexto_telemetria_para_persistencia(contexto: str | None) -> tuple[str | None, bool]:
    if contexto is None:
        return None, False

    texto = contexto.strip()
    if not texto:
        return None, False

    if texto.startswith("{") or texto.startswith("["):
        try:
            payload = json.loads(texto)
        except json.JSONDecodeError:
            valor, redaccion_aplicada = sanear_valor_pii(texto, clave="contexto")
            return str(valor), redaccion_aplicada

        payload_filtrado, claves_descartadas = _filtrar_diccionario_raiz_safe_by_default(
            payload, CLAVES_CONTEXTO_TELEMETRIA_PERMITIDAS
        )
        payload_saneado, redaccion_aplicada = sanear_valor_pii(payload_filtrado, clave="contexto")
        redaccion_aplicada = redaccion_aplicada or claves_descartadas
        if isinstance(payload_saneado, dict) and redaccion_aplicada:
            payload_saneado["redaccion_aplicada"] = True
        return json.dumps(payload_saneado, ensure_ascii=False, sort_keys=True), redaccion_aplicada

    if "=" in texto:
        partes_saneadas: list[str] = []
        redaccion_aplicada = False
        for parte in texto.split(";"):
            chunk = parte.strip()
            if not chunk:
                continue
            if "=" not in chunk:
                valor_libre, redactado_libre = sanear_valor_pii(chunk, clave="detalle")
                redaccion_aplicada = redaccion_aplicada or redactado_libre
                continue
            raw_key, raw_value = chunk.split("=", 1)
            key = raw_key.strip()
            value = raw_value.strip()
            if key not in CLAVES_CONTEXTO_TELEMETRIA_PERMITIDAS:
                redaccion_aplicada = True
                continue
            if es_clave_sensible_auditoria_telemetria(key):
                redaccion_aplicada = True
                continue
            value_saneado, value_redactado = sanear_valor_pii(value, clave=key)
            redaccion_aplicada = redaccion_aplicada or value_redactado
            partes_saneadas.append(f"{key}={value_saneado}")

        if redaccion_aplicada:
            partes_saneadas.append("redaccion_aplicada=true")
        if not partes_saneadas:
            return None, redaccion_aplicada
        return ";".join(partes_saneadas), redaccion_aplicada

    valor, redaccion_aplicada = sanear_valor_pii(texto, clave="contexto")
    return str(valor), redaccion_aplicada


def _filtrar_diccionario_raiz_safe_by_default(
    value: Any,
    claves_permitidas: frozenset[str],
) -> tuple[Any, bool]:
    if not isinstance(value, dict):
        return value, False

    saneado: dict[str, Any] = {}
    redaccion_aplicada = False
    for raw_key, raw_valor in value.items():
        key = str(raw_key)
        if key not in claves_permitidas:
            redaccion_aplicada = True
            continue
        if es_clave_sensible_auditoria_telemetria(key):
            redaccion_aplicada = True
            continue
        saneado[key] = raw_valor
    return saneado, redaccion_aplicada


def _to_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    return {"valor": value}
