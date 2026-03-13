from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ReglaMinimizacionContexto:
    contexto: str
    campos_permitidos: tuple[str, ...]
    campos_redactados: tuple[str, ...]
    campos_prohibidos: tuple[str, ...]
    reemplazos_por_id: tuple[str, ...] = ()


MATRIZ_MINIMIZACION_SALIDA: tuple[ReglaMinimizacionContexto, ...] = (
    ReglaMinimizacionContexto(
        contexto="ui_operativa_interna",
        campos_permitidos=("id", "nombre_completo", "estado", "fecha", "hora_inicio", "hora_fin", "canal"),
        campos_redactados=(),
        campos_prohibidos=("documento_enc", "telefono_enc", "email_enc", "documento_hash", "telefono_hash"),
    ),
    ReglaMinimizacionContexto(
        contexto="api_demo_read_only",
        campos_permitidos=(
            "id",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "estado",
            "sala",
            "medico",
            "paciente",
            "nombre",
            "apellidos",
            "nombre_completo",
            "documento",
            "telefono",
            "email",
            "activo",
            "tiene_incidencias",
        ),
        campos_redactados=("paciente", "documento", "telefono", "email"),
        campos_prohibidos=("*_enc", "*_hash", "direccion", "alergias", "observaciones", "notas", "motivo"),
    ),
    ReglaMinimizacionContexto(
        contexto="export_analitico_bi",
        campos_permitidos=("dataset_version", "model_version", "score", "label", "count", "pct"),
        campos_redactados=(),
        campos_prohibidos=("*_enc", "*_hash", "documento", "telefono", "email", "direccion", "notas"),
        reemplazos_por_id=("cita_id", "paciente_id", "medico_id"),
    ),
    ReglaMinimizacionContexto(
        contexto="recordatorios_contacto",
        campos_permitidos=("cita_id", "inicio", "paciente_nombre", "medico_nombre", "telefono", "email", "canal"),
        campos_redactados=(),
        campos_prohibidos=("*_enc", "*_hash", "direccion", "alergias", "observaciones"),
    ),
    ReglaMinimizacionContexto(
        contexto="auditoria",
        campos_permitidos=("action", "outcome", "actor_role", "correlation_id", "reason_code", "export_rows"),
        campos_redactados=("actor_username",),
        campos_prohibidos=("documento", "telefono", "email", "direccion", "*_enc", "*_hash"),
    ),
    ReglaMinimizacionContexto(
        contexto="logging_tecnico",
        campos_permitidos=("action", "run_id", "status", "error_code", "count", "entity_id"),
        campos_redactados=(),
        campos_prohibidos=("payload", "documento", "telefono", "email", "direccion", "notas", "*_enc", "*_hash"),
    ),
)


def serializar_cita_api_demo(fila: Mapping[str, Any]) -> dict[str, object]:
    paciente = redactar_texto_visible(str(fila.get("paciente", "")))
    return {
        "id": int(fila.get("id", 0)),
        "fecha": str(fila.get("fecha", "")),
        "hora_inicio": str(fila.get("hora_inicio", "")),
        "hora_fin": str(fila.get("hora_fin", "")),
        "estado": str(fila.get("estado", "")),
        "sala": str(fila.get("sala", "")),
        "medico": str(fila.get("medico", "")),
        "paciente": paciente,
        "tiene_incidencias": bool(fila.get("tiene_incidencias", False)),
    }


def serializar_paciente_api_demo(fila: Mapping[str, Any]) -> dict[str, object]:
    return {
        "id": int(fila.get("id", 0)),
        "nombre": str(fila.get("nombre", "")),
        "apellidos": str(fila.get("apellidos", "")),
        "nombre_completo": str(fila.get("nombre_completo", "")),
        "documento": redactar_texto_visible(str(fila.get("documento", ""))),
        "telefono": redactar_telefono_visible(str(fila.get("telefono", ""))),
        "email": redactar_email_visible(str(fila.get("email", ""))),
        "activo": bool(fila.get("activo", False)),
    }


def serializar_persona_demo_ml(fila: Mapping[str, Any], *, incluir_especialidad: bool) -> dict[str, object]:
    resultado: dict[str, object] = {
        "id": int(fila.get("id", 0)),
        "documento": redactar_texto_visible(str(fila.get("documento", ""))),
        "nombre_completo": str(fila.get("nombre_completo", "")),
        "telefono": redactar_telefono_visible(str(fila.get("telefono", ""))),
        "activo": bool(fila.get("activo", False)),
    }
    if incluir_especialidad:
        resultado["especialidad"] = str(fila.get("especialidad", ""))
    return resultado


def serializar_cita_demo_ml(fila: Mapping[str, Any]) -> dict[str, object]:
    return {
        "id": int(fila.get("id", 0)),
        "inicio": str(fila.get("inicio", "")),
        "fin": str(fila.get("fin", "")),
        "paciente_nombre": redactar_texto_visible(str(fila.get("paciente_nombre", ""))),
        "medico_nombre": str(fila.get("medico_nombre", "")),
        "estado": str(fila.get("estado", "")),
        "motivo": redactar_texto_visible(str(fila.get("motivo", ""))),
    }


def serializar_incidencia_demo_ml(fila: Mapping[str, Any]) -> dict[str, object]:
    return {
        "id": int(fila.get("id", 0)),
        "fecha_hora": str(fila.get("fecha_hora", "")),
        "tipo": str(fila.get("tipo", "")),
        "severidad": str(fila.get("severidad", "")),
        "estado": str(fila.get("estado", "")),
        "descripcion": redactar_texto_visible(str(fila.get("descripcion", ""))),
    }


def redactar_texto_visible(valor: str) -> str:
    limpio = (valor or "").strip()
    if not limpio:
        return ""
    if len(limpio) <= 2:
        return "**"
    return f"{limpio[:2]}***{limpio[-1:]}"


def redactar_email_visible(valor: str) -> str:
    limpio = (valor or "").strip()
    if "@" not in limpio:
        return redactar_texto_visible(limpio)
    local, dominio = limpio.split("@", 1)
    return f"{redactar_texto_visible(local)}@{dominio}"


def redactar_telefono_visible(valor: str) -> str:
    digitos = "".join(ch for ch in (valor or "") if ch.isdigit())
    if not digitos:
        return ""
    if len(digitos) <= 3:
        return "***"
    return f"***{digitos[-3:]}"
