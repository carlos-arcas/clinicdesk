from __future__ import annotations


def redactar_texto(valor: str) -> str:
    limpio = (valor or "").strip()
    if not limpio:
        return ""
    if len(limpio) <= 2:
        return "**"
    return f"{limpio[:2]}***{limpio[-1:]}"


def redactar_email(valor: str) -> str:
    limpio = (valor or "").strip()
    if "@" not in limpio:
        return redactar_texto(limpio)
    local, dominio = limpio.split("@", 1)
    return f"{redactar_texto(local)}@{dominio}"


def redactar_telefono(valor: str) -> str:
    digitos = "".join(ch for ch in (valor or "") if ch.isdigit())
    if not digitos:
        return ""
    if len(digitos) <= 3:
        return "***"
    return f"***{digitos[-3:]}"
