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


@dataclass(frozen=True, slots=True)
class SaludPrediccionDTO:
    estado: str
    mensaje_i18n_key: str
    acciones_i18n_keys: tuple[str, ...]
    fecha_ultima_actualizacion: str | None
    citas_validas_recientes: int


@dataclass(frozen=True, slots=True)
class CitaPendienteCierreDTO:
    cita_id: int
    inicio_local: str
    paciente: str
    medico: str
    estado_actual: str


@dataclass(frozen=True, slots=True)
class ListadoCitasPendientesCierreDTO:
    items: list[CitaPendienteCierreDTO]
    total: int


@dataclass(frozen=True, slots=True)
class ResultadoCierreCitasDTO:
    actualizadas: int
    ignoradas: int
    errores: int


@dataclass(frozen=True, slots=True)
class ResumenEntrenamientoModeloDTO:
    disponible: bool
    reason_code: str | None
    fecha_entrenamiento: str | None
    model_type: str | None
    version: str | None
    citas_usadas: int | None
    muestras_train: int | None
    muestras_validacion: int | None
    tasa_no_show_train: float | None
    tasa_no_show_validacion: float | None
    accuracy: float | None
    precision_no_show: float | None
    recall_no_show: float | None
    f1_no_show: float | None


@dataclass(frozen=True, slots=True)
class HistorialEntrenamientoModeloDTO:
    fecha_entrenamiento: str
    model_type: str
    version: str
    citas_usadas: int
    muestras_train: int | None
    muestras_validacion: int | None
    accuracy: float | None
    precision_no_show: float | None
    recall_no_show: float | None
    f1_no_show: float | None
    calidad_ux: str
    ganador_criterio: str | None
    baseline_f1: float | None
    v2_f1: float | None


@dataclass(frozen=True, slots=True)
class ResumenTendenciaHistorialDTO:
    tendencia_accuracy: str
    tendencia_recall_no_show: str
    alerta_rojo_consecutivo: bool
    rojos_consecutivos: int


@dataclass(frozen=True, slots=True)
class RecomendacionOperativaMonitorMLDTO:
    codigo: str
    i18n_key: str
    razon_corta_i18n_key: str
    es_fuerte: bool
