from __future__ import annotations

from dataclasses import dataclass
import re

from clinicdesk.app.application.auditoria_acceso import (
    AccionAuditoriaAcceso,
    EntidadAuditoriaAcceso,
    EventoAuditoriaAcceso,
    JsonObject,
    JsonValue,
    now_utc_iso,
)
from clinicdesk.app.application.ports.auditoria_acceso_port import RepositorioAuditoriaAcceso
from clinicdesk.app.application.security import UserContext
from clinicdesk.app.bootstrap_logging import get_logger


LOGGER = get_logger(__name__)

_ALLOWED_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "origen",
        "modulo",
        "vista",
        "accion_ui",
        "reason_code",
        "duracion_ms",
        "resultado",
        "contexto",
    }
)
_BLOCKED_KEY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"email", re.IGNORECASE),
    re.compile(r"telefono|teléfono|tlf", re.IGNORECASE),
    re.compile(r"dni|nif", re.IGNORECASE),
    re.compile(r"historia[_\s]?clinica|historia[_\s]?clínica", re.IGNORECASE),
    re.compile(r"direccion|dirección", re.IGNORECASE),
)
_RE_EMAIL = re.compile(r"[\w.%-]+@[\w.-]+\.[A-Za-z]{2,}")
_RE_DNI = re.compile(r"\b\d{8}[A-Za-z]?\b")
_RE_PHONE = re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){9,}\b")
_RE_HC = re.compile(r"\b(?:hc|historia(?:\s+clinica)?)\s*[:#-]?\s*[A-Za-z0-9-]{3,}\b", re.IGNORECASE)


@dataclass(slots=True)
class RegistrarAuditoriaAcceso:
    repositorio: RepositorioAuditoriaAcceso

    def execute(
        self,
        *,
        contexto_usuario: UserContext,
        accion: AccionAuditoriaAcceso,
        entidad_tipo: EntidadAuditoriaAcceso,
        entidad_id: int | str,
        metadata: JsonObject | None = None,
    ) -> None:
        self.ejecutar(
            contexto_usuario=contexto_usuario,
            accion=accion,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            metadata=metadata,
        )

    def ejecutar(
        self,
        *,
        contexto_usuario: UserContext,
        accion: AccionAuditoriaAcceso,
        entidad_tipo: EntidadAuditoriaAcceso,
        entidad_id: int | str,
        metadata: JsonObject | None = None,
    ) -> None:
        metadata_saneada, redaccion_aplicada = _sanear_metadata_acceso(metadata)
        if redaccion_aplicada and metadata_saneada is not None:
            metadata_saneada["redaccion_aplicada"] = True
        evento = EventoAuditoriaAcceso(
            timestamp_utc=now_utc_iso(),
            usuario=contexto_usuario.username,
            modo_demo=contexto_usuario.demo_mode,
            accion=accion,
            entidad_tipo=entidad_tipo,
            entidad_id=str(entidad_id),
            metadata_json=metadata_saneada,
        )
        self.repositorio.registrar(evento)
        LOGGER.info(
            "auditoria_acceso_registrada accion=%s entidad=%s entidad_id=%s",
            accion.value,
            entidad_tipo.value,
            evento.entidad_id,
        )


def _sanear_metadata_acceso(metadata: JsonObject | None) -> tuple[JsonObject | None, bool]:
    if metadata is None:
        return None, False
    saneada: JsonObject = {}
    redaccion_aplicada = False
    for key, value in metadata.items():
        if key not in _ALLOWED_METADATA_KEYS:
            redaccion_aplicada = True
            continue
        if _es_clave_sensible(key):
            redaccion_aplicada = True
            continue
        valor_saneado, valor_redactado = _sanear_valor(value)
        saneada[key] = valor_saneado
        redaccion_aplicada = redaccion_aplicada or valor_redactado
    if not saneada:
        return None, redaccion_aplicada
    return saneada, redaccion_aplicada


def _es_clave_sensible(key: str) -> bool:
    return any(pattern.search(key) for pattern in _BLOCKED_KEY_PATTERNS)


def _sanear_valor(value: JsonValue) -> tuple[JsonValue, bool]:
    if isinstance(value, dict):
        saneado: JsonObject = {}
        redaccion_aplicada = False
        for key, nested in value.items():
            if _es_clave_sensible(key):
                redaccion_aplicada = True
                continue
            nested_saneado, nested_redactado = _sanear_valor(nested)
            saneado[key] = nested_saneado
            redaccion_aplicada = redaccion_aplicada or nested_redactado
        return saneado, redaccion_aplicada
    if isinstance(value, list):
        saneada_lista: list[JsonValue] = []
        redaccion_aplicada = False
        for item in value:
            item_saneado, item_redactado = _sanear_valor(item)
            saneada_lista.append(item_saneado)
            redaccion_aplicada = redaccion_aplicada or item_redactado
        return saneada_lista, redaccion_aplicada
    if isinstance(value, str):
        redacted = _RE_EMAIL.sub("[REDACTED_EMAIL]", value)
        redacted = _RE_DNI.sub("[REDACTED_DNI]", redacted)
        redacted = _RE_PHONE.sub("[REDACTED_PHONE]", redacted)
        redacted = _RE_HC.sub("[REDACTED_HISTORIA_CLINICA]", redacted)
        return redacted, redacted != value
    return value, False
