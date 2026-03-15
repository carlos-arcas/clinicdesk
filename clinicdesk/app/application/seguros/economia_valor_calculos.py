from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.domain.seguros import OportunidadSeguro


@dataclass(frozen=True, slots=True)
class ValorTemporal:
    id_oportunidad: str
    valor_estimado: float
    confianza: float


def estimar_esfuerzo(oportunidad: OportunidadSeguro) -> float:
    return round(
        18 + len(oportunidad.seguimientos) * 9 + (7 if oportunidad.estado_actual.value == "EN_SEGUIMIENTO" else 0), 2
    )


def penalizacion_cautela(nivel: str) -> float:
    penalizaciones = {"BAJA": 0.08, "MEDIA": 0.18, "ALTA": 0.34}
    return penalizaciones[nivel]


def categoria_valor(valor: float, confianza: float) -> str:
    if confianza < 0.4:
        return "EVIDENCIA_INSUFICIENTE"
    if valor >= 260:
        return "ALTO"
    if valor >= 130:
        return "RAZONABLE"
    return "BAJO"


def accion_por_valor(categoria: str, cautela: str) -> str:
    if categoria == "ALTO" and cautela != "ALTA":
        return "INSISTIR_CON_PRIORIDAD_ALTA"
    if categoria == "RAZONABLE":
        return "TRABAJAR_SI_HAY_HUECO"
    if categoria == "BAJO":
        return "NO_SOBREINVERTIR_ESFUERZO"
    return "REVISAR_CASO_MANUALMENTE"


def normalizar_valor(valor: float) -> float:
    return min(max(valor / 400, 0.0), 1.0)


def cautela_por_categoria(categoria: str, confianza: float) -> str:
    if categoria == "EVIDENCIA_INSUFICIENTE" or confianza < 0.45:
        return "ALTA"
    if categoria == "BAJO":
        return "MEDIA"
    return "BAJA"


def mapear_campania(
    nombre: str,
    valores: tuple[ValorTemporal, ...],
) -> tuple[float, float, str, str, str, str]:
    total = round(sum(item.valor_estimado for item in valores), 2)
    media = round(total / max(len(valores), 1), 2)
    confianza_media = sum(item.confianza for item in valores) / max(len(valores), 1)
    categoria = categoria_valor(media, confianza_media)
    cautela = cautela_por_categoria(categoria, confianza_media)
    accion = accion_por_valor(categoria, cautela)
    explicacion = f"Canal {nombre} con valor medio esperado {media}."
    return total, media, categoria, cautela, accion, explicacion


def mapear_segmento(
    segmento: str,
    items: tuple[tuple[OportunidadSeguro, ValorTemporal], ...],
) -> tuple[float, float | None, str, str, str, str]:
    total = round(sum(valor.valor_estimado for _, valor in items), 2)
    conversiones = sum(1 for oportunidad, _ in items if oportunidad.estado_actual.value in {"CONVERTIDA", "RENOVADA"})
    tasa = round(conversiones / len(items), 4) if len(items) >= 3 else None
    media = total / max(len(items), 1)
    confianza_media = sum(valor.confianza for _, valor in items) / max(len(items), 1)
    categoria = categoria_valor(media, confianza_media)
    cautela = cautela_por_categoria(categoria, confianza_media)
    accion = accion_por_valor(categoria, cautela)
    explicacion = f"Segmento {segmento} con valor total esperado {total}."
    return total, tasa, categoria, cautela, accion, explicacion
