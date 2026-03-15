from __future__ import annotations

from clinicdesk.app.application.seguros.economia_valor import PrioridadValorSeguro
from clinicdesk.app.domain.seguros import OportunidadSeguro, RenovacionSeguro


def ratio_convertidas(oportunidades: tuple[OportunidadSeguro, ...], umbral: int) -> float | None:
    if len(oportunidades) < umbral:
        return None
    convertidas = sum(
        1 for item in oportunidades if item.resultado_comercial and item.resultado_comercial.value == "CONVERTIDO"
    )
    return round(convertidas / len(oportunidades), 4)


def ratio_renovacion_salvable(renovaciones: tuple[RenovacionSeguro, ...], umbral: int) -> float | None:
    if len(renovaciones) < umbral:
        return None
    salvables = sum(1 for item in renovaciones if item.revision_pendiente)
    return round(salvables / len(renovaciones), 4)


def factor_horizonte(horizonte: str) -> float:
    return {"30D": 1.0, "60D": 1.8, "90D": 2.4}[horizonte]


def valor_total_esperado(prioridades: tuple[PrioridadValorSeguro, ...], factor: float) -> float:
    return round(sum(item.score_impacto for item in prioridades[:10]) * 320 * factor, 2)


def cautela_general(volumen: int, conversion: float | None, renovacion: float | None) -> str:
    if volumen < 4 or conversion is None or renovacion is None:
        return "ALTA"
    if conversion < 0.2:
        return "MEDIA"
    return "BAJA"


def riesgo_general(cautela: str, conversion: float | None, renovacion: float | None) -> str:
    if cautela == "ALTA":
        return "EVIDENCIA_LIMITADA"
    if conversion and conversion < 0.2:
        return "CONVERSION_DEBIL"
    if renovacion and renovacion < 0.35:
        return "RETENCION_FRAGIL"
    return "RIESGO_CONTROLADO"


def accion_general(cautela: str) -> str:
    if cautela == "ALTA":
        return "VALIDAR_SEMANALMENTE_SIN_SOBREINVERTIR"
    if cautela == "MEDIA":
        return "PRIORIZAR_LOTES_DE_MEJOR_FIT"
    return "ESCALAR_CAMPANIAS_PRIORITARIAS"


def cautela_por_muestra(tamano: int) -> str:
    if tamano < 4:
        return "ALTA"
    if tamano < 8:
        return "MEDIA"
    return "BAJA"


def ratio_con_guardrail(valor: float | None, tamano: int, umbral: int) -> float | None:
    return valor if valor is not None and tamano >= umbral else None
