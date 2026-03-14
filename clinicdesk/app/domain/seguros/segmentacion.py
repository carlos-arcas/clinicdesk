from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SegmentoClienteSeguro(str, Enum):
    PACIENTE_ACTUAL_CLINICA = "PACIENTE_ACTUAL_CLINICA"
    FAMILIAR_PACIENTE = "FAMILIAR_PACIENTE"
    CLIENTE_NUEVO = "CLIENTE_NUEVO"
    ASEGURADO_EXTERNO_MIGRAR = "ASEGURADO_EXTERNO_MIGRAR"
    CLIENTE_PLAN_GENERAL = "CLIENTE_PLAN_GENERAL"
    CLIENTE_PRODUCTO_CLINICA = "CLIENTE_PRODUCTO_CLINICA"
    EMPRESA_COLECTIVO = "EMPRESA_COLECTIVO"


class OrigenClienteSeguro(str, Enum):
    WEB = "WEB"
    REFERIDO = "REFERIDO"
    MOSTRADOR_CLINICA = "MOSTRADOR_CLINICA"
    CALL_CENTER = "CALL_CENTER"
    CAMPAÑA_DIGITAL = "CAMPAÑA_DIGITAL"


class NecesidadPrincipalSeguro(str, Enum):
    AHORRO_COSTE = "AHORRO_COSTE"
    COBERTURA_FAMILIAR = "COBERTURA_FAMILIAR"
    ACCESO_ESPECIALISTAS = "ACCESO_ESPECIALISTAS"
    CONTINUIDAD_MEDICA = "CONTINUIDAD_MEDICA"
    URGENCIAS_INMEDIATAS = "URGENCIAS_INMEDIATAS"


class MotivacionCompraSeguro(str, Enum):
    MEJOR_RELACION_CALIDAD_PRECIO = "MEJOR_RELACION_CALIDAD_PRECIO"
    REDUCE_ESPERAS = "REDUCE_ESPERAS"
    CONFIANZA_EN_CLINICA = "CONFIANZA_EN_CLINICA"
    COBERTURA_DENTAL = "COBERTURA_DENTAL"
    COBERTURA_FAMILIAR_AMPLIA = "COBERTURA_FAMILIAR_AMPLIA"


class ObjecionComercialSeguro(str, Enum):
    PRECIO_PERCIBIDO_ALTO = "PRECIO_PERCIBIDO_ALTO"
    DUDAS_COBERTURA = "DUDAS_COBERTURA"
    NO_TIENE_TIEMPO = "NO_TIENE_TIEMPO"
    MIEDO_CAMBIO = "MIEDO_CAMBIO"
    PERMANENCIA_ACTUAL = "PERMANENCIA_ACTUAL"


class SensibilidadPrecioSeguro(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class FriccionMigracionSeguro(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class EncajePlanSeguro(str, Enum):
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"
    REVISAR = "REVISAR"


@dataclass(frozen=True, slots=True)
class PerfilComercialSeguro:
    segmento_cliente: SegmentoClienteSeguro
    origen_cliente: OrigenClienteSeguro
    necesidad_principal: NecesidadPrincipalSeguro
    motivaciones: tuple[MotivacionCompraSeguro, ...]
    objecion_principal: ObjecionComercialSeguro
    sensibilidad_precio: SensibilidadPrecioSeguro
    friccion_migracion: FriccionMigracionSeguro


@dataclass(frozen=True, slots=True)
class EvaluacionFitComercialSeguro:
    encaje_plan: EncajePlanSeguro
    motivo_principal: str
    riesgos_friccion: tuple[str, ...]
    argumentos_valor: tuple[str, ...]
    conviene_insistir: bool
    revision_humana_recomendada: bool
