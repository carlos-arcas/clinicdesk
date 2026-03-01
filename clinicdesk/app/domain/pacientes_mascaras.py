"""Funciones puras para anonimización en listados."""

from __future__ import annotations


def enmascarar_documento(valor: str | None) -> str:
    limpio = _limpiar(valor)
    if not limpio:
        return ""
    visibles = min(2, len(limpio))
    ocultos = max(len(limpio) - visibles, 0)
    return f"{'*' * ocultos}{limpio[-visibles:]}"


def enmascarar_telefono(valor: str | None) -> str:
    limpio = _solo_alnum(valor)
    if not limpio:
        return ""
    visibles = min(3, len(limpio))
    ocultos = max(len(limpio) - visibles, 0)
    bloque_oculto = "*" * ocultos
    grupos = _agrupar_en_bloques_de_tres(bloque_oculto)
    if grupos:
        return f"{grupos} {limpio[-visibles:]}"
    return limpio[-visibles:]


def enmascarar_email(valor: str | None) -> str:
    limpio = _limpiar(valor)
    if not limpio or "@" not in limpio:
        return enmascarar_texto_general(limpio)
    local, dominio = limpio.split("@", 1)
    if not dominio:
        return enmascarar_texto_general(local)
    prefijo = local[:1]
    return f"{prefijo}***@{dominio}" if prefijo else f"***@{dominio}"


def enmascarar_texto_general(valor: str | None) -> str:
    limpio = _limpiar(valor)
    if not limpio:
        return ""
    if len(limpio) <= 2:
        return "*" * len(limpio)
    visibles_final = 2 if len(limpio) > 3 else 1
    ocultos = len(limpio) - 1 - visibles_final
    return f"{limpio[0]}{'*' * max(ocultos, 0)}{limpio[-visibles_final:]}"


def _limpiar(valor: str | None) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _solo_alnum(valor: str | None) -> str:
    if not isinstance(valor, str):
        return ""
    return "".join(c for c in valor if c.isalnum())


def _agrupar_en_bloques_de_tres(texto: str) -> str:
    if not texto:
        return ""
    return " ".join(texto[i : i + 3] for i in range(0, len(texto), 3))
