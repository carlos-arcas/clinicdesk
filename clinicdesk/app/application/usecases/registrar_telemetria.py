from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from clinicdesk.app.application.ports.telemetria_port import RepositorioTelemetria
from clinicdesk.app.application.security import UserContext
from clinicdesk.app.application.telemetria import EventoTelemetriaDTO, ahora_utc_iso
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)

_ALLOWED_CONTEXTO_KEYS: frozenset[str] = frozenset(
    {
        "page",
        "origen",
        "tipo",
        "clave",
        "resultado",
        "destino",
        "vista",
        "found",
        "modulo",
        "accion_ui",
        "reason_code",
        "contexto",
        "tab",
        "detalle",
    }
)
_BLOCKED_KEY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"email", re.IGNORECASE),
    re.compile(r"telefono|teléfono|tlf|movil|móvil", re.IGNORECASE),
    re.compile(r"dni|nif", re.IGNORECASE),
    re.compile(r"historia[_\s]?clinica|historia[_\s]?clínica", re.IGNORECASE),
    re.compile(r"direccion|dirección", re.IGNORECASE),
)
_RE_EMAIL = re.compile(r"[\w.%-]+@[\w.-]+\.[A-Za-z]{2,}")
_RE_DNI = re.compile(r"\b\d{8}[A-Za-z]?\b")
_RE_PHONE = re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){9,}\b")
_RE_HC = re.compile(r"\b(?:hc|historia(?:\s+clinica)?)\s*[:#-]?\s*[A-Za-z0-9-]{3,}\b", re.IGNORECASE)


@dataclass(slots=True)
class RegistrarTelemetria:
    repositorio: RepositorioTelemetria

    def ejecutar(
        self,
        *,
        contexto_usuario: UserContext,
        evento: str,
        contexto: str | None = None,
        entidad_tipo: str | None = None,
        entidad_id: int | str | None = None,
    ) -> None:
        contexto_saneado, redaccion_aplicada = _sanear_contexto_telemetria(contexto)
        evento_dto = EventoTelemetriaDTO(
            timestamp_utc=ahora_utc_iso(),
            usuario=contexto_usuario.username,
            modo_demo=contexto_usuario.demo_mode,
            evento=evento,
            contexto=contexto_saneado,
            entidad_tipo=entidad_tipo,
            entidad_id=str(entidad_id) if entidad_id is not None else None,
        )
        self.repositorio.registrar(evento_dto)
        LOGGER.info(
            "telemetria_evento",
            extra={
                "action": "telemetria_evento",
                "evento": evento,
                "entidad_tipo": entidad_tipo,
                "redaccion_aplicada": redaccion_aplicada,
            },
        )


def _sanear_contexto_telemetria(contexto: str | None) -> tuple[str | None, bool]:
    if contexto is None:
        return None, False
    texto = contexto.strip()
    if not texto:
        return None, False

    if texto.startswith("{") or texto.startswith("["):
        return _sanear_contexto_json(texto)

    return _sanear_contexto_kv(texto)


def _sanear_contexto_json(texto: str) -> tuple[str | None, bool]:
    try:
        payload = json.loads(texto)
    except json.JSONDecodeError:
        redacted = _redactar_texto(texto)
        aplicado = redacted != texto
        if aplicado:
            return f"detalle={redacted};redaccion_aplicada=true", True
        return f"detalle={redacted}", False

    saneado, redaccion_aplicada = _sanear_payload(payload, es_raiz=True)
    if saneado is None:
        return "redaccion_aplicada=true", True

    if redaccion_aplicada and isinstance(saneado, dict):
        saneado["redaccion_aplicada"] = True
    return json.dumps(saneado, ensure_ascii=False, sort_keys=True), redaccion_aplicada


def _sanear_contexto_kv(texto: str) -> tuple[str | None, bool]:
    partes_saneadas: list[str] = []
    redaccion_aplicada = False
    for parte in texto.split(";"):
        chunk = parte.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            redacted = _redactar_texto(chunk)
            if redacted != chunk:
                redaccion_aplicada = True
            continue
        key, value = chunk.split("=", 1)
        key_norm = key.strip()
        value_norm = value.strip()
        if key_norm not in _ALLOWED_CONTEXTO_KEYS:
            redaccion_aplicada = True
            continue
        if _es_clave_sensible(key_norm):
            redaccion_aplicada = True
            continue
        valor_redactado = _redactar_texto(value_norm)
        if valor_redactado != value_norm:
            redaccion_aplicada = True
        partes_saneadas.append(f"{key_norm}={valor_redactado}")

    if redaccion_aplicada:
        partes_saneadas.append("redaccion_aplicada=true")
    if not partes_saneadas:
        return None, redaccion_aplicada
    return ";".join(partes_saneadas), redaccion_aplicada


def _sanear_payload(payload: Any, *, es_raiz: bool = False) -> tuple[Any | None, bool]:
    if isinstance(payload, dict):
        saneado: dict[str, Any] = {}
        redaccion_aplicada = False
        for raw_key, value in payload.items():
            key = str(raw_key)
            if key not in _ALLOWED_CONTEXTO_KEYS and es_raiz:
                redaccion_aplicada = True
                continue
            if _es_clave_sensible(key):
                redaccion_aplicada = True
                continue
            valor_saneado, valor_redactado = _sanear_payload(value)
            if valor_saneado is None and isinstance(value, dict):
                redaccion_aplicada = True
                continue
            saneado[key] = valor_saneado
            redaccion_aplicada = redaccion_aplicada or valor_redactado
        if not saneado:
            return None, redaccion_aplicada
        return saneado, redaccion_aplicada
    if isinstance(payload, list):
        saneada: list[Any] = []
        redaccion_aplicada = False
        for value in payload:
            valor_saneado, valor_redactado = _sanear_payload(value)
            if valor_saneado is None and isinstance(value, dict):
                redaccion_aplicada = True
                continue
            saneada.append(valor_saneado)
            redaccion_aplicada = redaccion_aplicada or valor_redactado
        return saneada, redaccion_aplicada
    if isinstance(payload, str):
        redactado = _redactar_texto(payload)
        return redactado, redactado != payload
    return payload, False


def _es_clave_sensible(key: str) -> bool:
    return any(pattern.search(key) for pattern in _BLOCKED_KEY_PATTERNS)


def _redactar_texto(value: str) -> str:
    redacted = _RE_EMAIL.sub("[REDACTED_EMAIL]", value)
    redacted = _RE_DNI.sub("[REDACTED_DNI]", redacted)
    redacted = _RE_PHONE.sub("[REDACTED_PHONE]", redacted)
    redacted = _RE_HC.sub("[REDACTED_HISTORIA_CLINICA]", redacted)
    return redacted
