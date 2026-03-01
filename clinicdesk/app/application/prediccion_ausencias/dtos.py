from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatosEntrenamientoPrediccion:
    paciente_id: int
    no_vino: int
    dias_antelacion: int


@dataclass(frozen=True, slots=True)
class ResultadoComprobacionDatos:
    citas_validas: int
    minimo_requerido: int
    apto_para_entrenar: bool
    mensaje_clave: str


@dataclass(frozen=True, slots=True)
class PrediccionCitaDTO:
    fecha: str
    hora: str
    paciente: str
    medico: str
    riesgo: str
    explicacion: str


@dataclass(frozen=True, slots=True)
class ResultadoPrevisualizacionPrediccion:
    estado: str
    items: list[PrediccionCitaDTO]


@dataclass(frozen=True, slots=True)
class CitaParaPrediccionDTO:
    id: int
    fecha: str
    hora: str
    paciente_id: int
    medico_id: int
    antelacion_dias: int


@dataclass(frozen=True, slots=True)
class MotivoRiesgoDTO:
    code: str
    i18n_key: str
    detalle_suave_key: str | None = None


@dataclass(frozen=True, slots=True)
class MetadataExplicacionRiesgoDTO:
    fecha_entrenamiento: str | None
    necesita_entrenar: bool


@dataclass(frozen=True, slots=True)
class ExplicacionRiesgoAusenciaDTO:
    nivel: str
    motivos: tuple[MotivoRiesgoDTO, ...]
    acciones_sugeridas: tuple[str, ...]
    metadata_simple: MetadataExplicacionRiesgoDTO
