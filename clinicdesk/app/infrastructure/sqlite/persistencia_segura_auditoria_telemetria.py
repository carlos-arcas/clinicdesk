from __future__ import annotations

import json
from typing import Any

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
        valor_metadata, redaccion_metadata = sanear_valor_pii(metadata_json, clave="metadata")
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

        payload_saneado, redaccion_aplicada = sanear_valor_pii(payload, clave="contexto")
        if isinstance(payload_saneado, dict) and redaccion_aplicada:
            payload_saneado["redaccion_aplicada"] = True
        return json.dumps(payload_saneado, ensure_ascii=False, sort_keys=True), redaccion_aplicada

    valor, redaccion_aplicada = sanear_valor_pii(texto, clave="contexto")
    return str(valor), redaccion_aplicada


def _to_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    return {"valor": value}
