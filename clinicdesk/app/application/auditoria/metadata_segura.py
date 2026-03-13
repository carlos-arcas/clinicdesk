from __future__ import annotations

import re

from clinicdesk.app.common.redaccion_pii import redactar_texto_pii

ValorMetadataAuditoria = str | int | float | bool | None
MetadataAuditoria = dict[str, ValorMetadataAuditoria]


class MetadataAuditoriaError(ValueError):
    pass


CLAVES_METADATA_AUDITORIA_PERMITIDAS: frozenset[str] = frozenset(
    {
        "cita_id",
        "medico_id",
        "sala_id",
        "motivo_override",
        "warnings_count",
        "incidencia_id",
        "error_code",
        "error_type",
        "seed",
        "n_doctors",
        "n_patients",
        "n_appointments",
        "incidences",
        "medicamentos",
        "materiales",
        "recetas",
        "movimientos",
        "turnos",
        "ausencias",
        "from_date",
        "to_date",
        "dataset_version",
        "reason_code",
        "db_path_hint",
        "export_rows",
    }
)

PATRONES_CLAVE_BLOQUEADA_AUDITORIA: tuple[re.Pattern[str], ...] = (
    re.compile(r"dni|nif|documento", re.IGNORECASE),
    re.compile(r"email|correo|mail", re.IGNORECASE),
    re.compile(r"telefono|teléfono|tlf|movil|móvil", re.IGNORECASE),
    re.compile(r"direccion|dirección", re.IGNORECASE),
    re.compile(r"alergias|observaciones|nota_override|historia", re.IGNORECASE),
    re.compile(r"(_enc|_hash)$", re.IGNORECASE),
)


def sanitizar_metadata_auditoria(metadata: MetadataAuditoria) -> MetadataAuditoria:
    saneada: MetadataAuditoria = {}
    for key, value in metadata.items():
        _validar_clave_permitida(key)
        saneada[key] = _sanitizar_valor(value)
    return saneada


def _validar_clave_permitida(clave: str) -> None:
    if clave not in CLAVES_METADATA_AUDITORIA_PERMITIDAS:
        raise MetadataAuditoriaError(f"Metadata key no permitida: {clave}")
    for patron in PATRONES_CLAVE_BLOQUEADA_AUDITORIA:
        if patron.search(clave):
            raise MetadataAuditoriaError(f"Metadata key bloqueada por seguridad: {clave}")


def _sanitizar_valor(value: ValorMetadataAuditoria) -> ValorMetadataAuditoria:
    if isinstance(value, str):
        valor_redactado, _ = redactar_texto_pii(value)
        return valor_redactado
    return value
