from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from clinicdesk.app.common.redaccion_pii import redactar_texto_pii
from clinicdesk.app.domain.seguros import PolizaSeguro, ResumenEconomicoPolizaSeguro


class _CampaniaEjecutivaLike(Protocol):
    id_campania: str
    titulo: str
    criterio: str
    tamano_estimado: int
    motivo: str
    accion_recomendada: str
    cautela: str
    ids_oportunidad: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReglaMetadataSeguraSeguro:
    contexto: str
    campos_permitidos: frozenset[str]


_REGLAS_METADATA_SEGURO: tuple[ReglaMetadataSeguraSeguro, ...] = (
    ReglaMetadataSeguraSeguro(
        contexto="logging_tecnico_seguro",
        campos_permitidos=frozenset(
            {
                "evento",
                "correlation_id",
                "horizonte",
                "volumen",
                "conversiones_esperadas",
                "alertas",
                "tareas",
                "renovaciones",
                "outcome",
            }
        ),
    ),
    ReglaMetadataSeguraSeguro(
        contexto="auditoria_seguro",
        campos_permitidos=frozenset(
            {
                "action",
                "outcome",
                "correlation_id",
                "id_oportunidad",
                "id_poliza",
                "id_campania",
                "estado",
                "resultado",
                "reason_code",
                "items_count",
                "beneficiarios_count",
                "incidencias_count",
                "cuotas_impagadas",
                "nivel_riesgo",
            }
        ),
    ),
    ReglaMetadataSeguraSeguro(
        contexto="dataset_seguro",
        campos_permitidos=frozenset(
            {
                "id_oportunidad",
                "id_campania",
                "horizonte",
                "volumen_esperado",
                "conversiones_esperadas",
                "renovaciones_salvables_esperadas",
                "cautela",
                "riesgo_principal",
                "estado_pago",
                "nivel_riesgo",
                "cuotas_emitidas",
                "cuotas_pagadas",
                "cuotas_vencidas",
                "cuotas_impagadas",
                "pendiente_tramo",
            }
        ),
    ),
)

_PATRONES_CLAVE_BLOQUEADA: tuple[re.Pattern[str], ...] = (
    re.compile(r"dni|nif|documento", re.IGNORECASE),
    re.compile(r"email|correo|mail", re.IGNORECASE),
    re.compile(r"telefono|teléfono|tlf|movil|móvil", re.IGNORECASE),
    re.compile(r"direccion|dirección", re.IGNORECASE),
    re.compile(r"nota|historia|beneficiarios|titular", re.IGNORECASE),
    re.compile(r"objecion|objeción", re.IGNORECASE),
    re.compile(r"payload|raw|completo", re.IGNORECASE),
    re.compile(r"_enc$|_hash$", re.IGNORECASE),
)


class MetadataSeguraSeguroError(ValueError):
    pass


def sanitizar_metadata_segura_seguro(contexto: str, metadata: Mapping[str, Any]) -> dict[str, Any]:
    regla = _resolver_regla(contexto)
    saneada: dict[str, Any] = {}
    for raw_key, valor in metadata.items():
        key = str(raw_key)
        if key not in regla.campos_permitidos:
            continue
        if _es_clave_bloqueada(key):
            continue
        saneada[key] = _sanear_valor(valor)
    return saneada


def construir_evento_log_seguro(contexto: str, evento: str, metadata: Mapping[str, Any]) -> dict[str, Any]:
    payload = sanitizar_metadata_segura_seguro(contexto, metadata)
    payload["evento"] = evento
    return payload


def snapshot_campania_ejecutiva_segura(campania: _CampaniaEjecutivaLike) -> dict[str, object]:
    return {
        "id_campania": campania.id_campania,
        "titulo": campania.titulo,
        "criterio": campania.criterio,
        "tamano_estimado": campania.tamano_estimado,
        "motivo": campania.motivo,
        "accion_recomendada": campania.accion_recomendada,
        "cautela": campania.cautela,
        "ids_resumen": _resumen_ids(campania.ids_oportunidad),
    }


def snapshot_postventa_seguro(poliza: PolizaSeguro) -> dict[str, object]:
    return {
        "id_poliza": poliza.id_poliza,
        "estado": poliza.estado.value,
        "titular_ref": poliza.titular.id_asegurado,
        "beneficiarios": len(poliza.beneficiarios),
        "vigencia_inicio": poliza.vigencia.fecha_inicio.isoformat(),
        "vigencia_fin": poliza.vigencia.fecha_fin.isoformat(),
        "renovacion": poliza.renovacion.estado.value,
        "incidencias": len(poliza.incidencias),
    }


def snapshot_economia_poliza_segura(resumen: ResumenEconomicoPolizaSeguro) -> dict[str, object]:
    return {
        "id_poliza": resumen.id_poliza,
        "estado": resumen.estado_pago.value,
        "riesgo": resumen.nivel_riesgo.value,
        "pendiente_tramo": _tramo_pendiente(resumen.total_pendiente),
        "emitidas": resumen.cuotas_emitidas,
        "pagadas": resumen.cuotas_pagadas,
        "vencidas": resumen.cuotas_vencidas,
        "impagadas": resumen.cuotas_impagadas,
        "motivo": resumen.motivo_estado,
    }


def _resolver_regla(contexto: str) -> ReglaMetadataSeguraSeguro:
    for regla in _REGLAS_METADATA_SEGURO:
        if regla.contexto == contexto:
            return regla
    raise MetadataSeguraSeguroError(f"Contexto de metadata no soportado: {contexto}")


def _es_clave_bloqueada(clave: str) -> bool:
    return any(p.search(clave) for p in _PATRONES_CLAVE_BLOQUEADA)


def _sanear_valor(valor: Any) -> Any:
    if isinstance(valor, str):
        redactado, _ = redactar_texto_pii(valor)
        return redactado[:120]
    if isinstance(valor, (int, float, bool)) or valor is None:
        return valor
    if isinstance(valor, (tuple, list, set)):
        return len(valor)
    if isinstance(valor, dict):
        return len(valor)
    return str(valor)


def _resumen_ids(ids_oportunidad: tuple[str, ...]) -> str:
    cantidad = len(ids_oportunidad)
    if cantidad == 0:
        return "-"
    if cantidad <= 2:
        return ", ".join(ids_oportunidad)
    return f"{cantidad} ids"


def _tramo_pendiente(total_pendiente: float) -> str:
    if total_pendiente <= 0:
        return "0"
    if total_pendiente < 100:
        return "(0,100)"
    if total_pendiente < 500:
        return "[100,500)"
    return ">=500"
