from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.dtos import (
    DatosEntrenamientoPrediccion,
    ExplicacionRiesgoAusenciaDTO,
    MetadataExplicacionRiesgoDTO,
    MotivoRiesgoDTO,
    PrediccionCitaDTO,
    ResumenEntrenamientoModeloDTO,
    ResultadoComprobacionDatos,
    ResultadoPrevisualizacionPrediccion,
)
from clinicdesk.app.application.prediccion_ausencias.seleccion_modelo import (
    ResultadoMetricasModelo,
    seleccionar_mejor_modelo,
)
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.domain.prediccion_ausencias import CitaParaPrediccion, RegistroEntrenamiento
from clinicdesk.app.infrastructure.prediccion_ausencias import (
    AlmacenamientoModeloPrediccion,
    ModeloPrediccionNoDisponibleError,
    PredictorAusenciasBaseline,
    PredictorAusenciasV2,
)
from clinicdesk.app.queries.prediccion_ausencias_queries import (
    PrediccionAusenciasQueries,
    ResumenHistorialPaciente,
)

LOGGER = get_logger(__name__)

_POCOS_DATOS_MAX = 2
_MAX_MOTIVOS = 4


@dataclass(frozen=True, slots=True)
class ResultadoEntrenamientoPrediccion:
    citas_usadas: int
    fecha_entrenamiento: str
    accuracy: float
    recall_no_show: float


@dataclass(frozen=True, slots=True)
class ResultadoEvaluacionEntrenamiento:
    muestras_train: int
    muestras_validacion: int
    tasa_no_show_train: float
    tasa_no_show_validacion: float
    accuracy: float
    precision_no_show: float
    recall_no_show: float
    f1_no_show: float


class EntrenamientoPrediccionError(Exception):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class ComprobarDatosPrediccionAusencias:
    def __init__(self, queries: PrediccionAusenciasQueries, minimo_requerido: int = 50) -> None:
        self._queries = queries
        self._minimo_requerido = minimo_requerido

    def ejecutar(self) -> ResultadoComprobacionDatos:
        total = self._queries.contar_citas_validas()
        apto = total >= self._minimo_requerido
        key = "prediccion_ausencias.estado.datos_ok" if apto else "prediccion_ausencias.estado.datos_insuficientes"
        return ResultadoComprobacionDatos(
            citas_validas=total,
            minimo_requerido=self._minimo_requerido,
            apto_para_entrenar=apto,
            mensaje_clave=key,
        )


class EntrenarPrediccionAusencias:
    def __init__(
        self,
        comprobar_datos_uc: ComprobarDatosPrediccionAusencias,
        queries: PrediccionAusenciasQueries,
        predictor_baseline: PredictorAusenciasBaseline | None,
        predictor_v2: PredictorAusenciasV2 | None,
        almacenamiento: AlmacenamientoModeloPrediccion,
    ) -> None:
        self._comprobar_datos_uc = comprobar_datos_uc
        self._queries = queries
        self._predictor_baseline = predictor_baseline or PredictorAusenciasBaseline()
        self._predictor_v2 = predictor_v2 or PredictorAusenciasV2()
        self._almacenamiento = almacenamiento

    def ejecutar(self) -> ResultadoEntrenamientoPrediccion:
        chequeo = self._comprobar_datos_uc.ejecutar()
        if not chequeo.apto_para_entrenar:
            raise EntrenamientoPrediccionError("dataset_insuficiente")

        dataset = self._construir_dataset(self._queries.obtener_dataset_entrenamiento())
        if not dataset:
            raise EntrenamientoPrediccionError("dataset_empty")

        dataset_train, dataset_validacion = _split_determinista_train_validacion(dataset)
        predictor_baseline_entrenado = self._predictor_baseline.entrenar(dataset_train)
        predictor_v2_entrenado = self._predictor_v2.entrenar(dataset_train)
        evaluacion_baseline = _evaluar_predictor(
            predictor_entrenado=predictor_baseline_entrenado,
            dataset_train=dataset_train,
            dataset_validacion=dataset_validacion,
        )
        evaluacion_v2 = _evaluar_predictor(
            predictor_entrenado=predictor_v2_entrenado,
            dataset_train=dataset_train,
            dataset_validacion=dataset_validacion,
        )
        seleccion = seleccionar_mejor_modelo(
            baseline=ResultadoMetricasModelo(
                model_type="PredictorAusenciasBaseline",
                accuracy=evaluacion_baseline.accuracy,
                recall_no_show=evaluacion_baseline.recall_no_show,
                f1_no_show=evaluacion_baseline.f1_no_show,
            ),
            candidato_v2=ResultadoMetricasModelo(
                model_type="PredictorAusenciasV2",
                accuracy=evaluacion_v2.accuracy,
                recall_no_show=evaluacion_v2.recall_no_show,
                f1_no_show=evaluacion_v2.f1_no_show,
            ),
        )
        predictor_ganador = (
            predictor_v2_entrenado
            if seleccion.ganador.model_type == "PredictorAusenciasV2"
            else predictor_baseline_entrenado
        )
        evaluacion_ganador = (
            evaluacion_v2 if seleccion.ganador.model_type == "PredictorAusenciasV2" else evaluacion_baseline
        )
        try:
            metadata = self._almacenamiento.guardar(
                predictor_ganador,
                citas_usadas=len(dataset),
                version="prediccion_ausencias_v1",
                model_type=seleccion.ganador.model_type,
                muestras_train=evaluacion_ganador.muestras_train,
                muestras_validacion=evaluacion_ganador.muestras_validacion,
                tasa_no_show_train=evaluacion_ganador.tasa_no_show_train,
                tasa_no_show_validacion=evaluacion_ganador.tasa_no_show_validacion,
                accuracy=evaluacion_ganador.accuracy,
                precision_no_show=evaluacion_ganador.precision_no_show,
                recall_no_show=evaluacion_ganador.recall_no_show,
                f1_no_show=evaluacion_ganador.f1_no_show,
            )
        except OSError as exc:
            LOGGER.error(
                "prediccion_entrenamiento_no_guardado",
                extra={"reason_code": "save_failed", "error": str(exc)},
            )
            raise EntrenamientoPrediccionError("save_failed") from exc

        LOGGER.info(
            "prediccion_entrenar_modelo_seleccionado",
            extra={
                "model_type_ganador": seleccion.ganador.model_type,
                "criterio_decision": seleccion.criterio,
                "baseline": {
                    "accuracy": evaluacion_baseline.accuracy,
                    "recall_no_show": evaluacion_baseline.recall_no_show,
                    "f1_no_show": evaluacion_baseline.f1_no_show,
                },
                "v2": {
                    "accuracy": evaluacion_v2.accuracy,
                    "recall_no_show": evaluacion_v2.recall_no_show,
                    "f1_no_show": evaluacion_v2.f1_no_show,
                },
            },
        )

        if not metadata.fecha_entrenamiento:
            raise EntrenamientoPrediccionError("metadata_invalid")
        return ResultadoEntrenamientoPrediccion(
            citas_usadas=metadata.citas_usadas,
            fecha_entrenamiento=metadata.fecha_entrenamiento,
            accuracy=metadata.accuracy or 0.0,
            recall_no_show=metadata.recall_no_show or 0.0,
        )

    @staticmethod
    def _construir_dataset(rows: list) -> list[RegistroEntrenamiento]:
        mapped: list[RegistroEntrenamiento] = []
        for row in rows:
            dto = DatosEntrenamientoPrediccion(
                paciente_id=row.paciente_id,
                no_vino=1 if row.estado == "NO_PRESENTADO" else 0,
                dias_antelacion=row.dias_antelacion,
            )
            mapped.append(
                RegistroEntrenamiento(
                    paciente_id=dto.paciente_id,
                    no_vino=dto.no_vino,
                    dias_antelacion=dto.dias_antelacion,
                )
            )
        return mapped


class PrevisualizarPrediccionAusencias:
    def __init__(self, queries: PrediccionAusenciasQueries, almacenamiento: AlmacenamientoModeloPrediccion) -> None:
        self._queries = queries
        self._almacenamiento = almacenamiento

    def ejecutar(self, limite: int = 30) -> ResultadoPrevisualizacionPrediccion:
        try:
            predictor_entrenado, _ = self._almacenamiento.cargar()
        except ModeloPrediccionNoDisponibleError:
            return ResultadoPrevisualizacionPrediccion(estado="SIN_MODELO", items=[])
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(
                "prediccion_carga_fallida",
                extra={"reason_code": "model_load_failed", "error": str(exc)},
            )
            return ResultadoPrevisualizacionPrediccion(estado="ERROR", items=[])

        proximas = self._queries.listar_proximas_citas(limite)
        predicciones = predictor_entrenado.predecir(
            [
                CitaParaPrediccion(cita_id=r.cita_id, paciente_id=r.paciente_id, dias_antelacion=r.dias_antelacion)
                for r in proximas
            ]
        )
        riesgo_por_cita = {item.cita_id: item for item in predicciones}
        items = [
            PrediccionCitaDTO(
                fecha=r.fecha,
                hora=r.hora,
                paciente=r.paciente,
                medico=r.medico,
                riesgo=riesgo_por_cita[r.cita_id].riesgo.value,
                explicacion=riesgo_por_cita[r.cita_id].explicacion_corta,
            )
            for r in proximas
            if r.cita_id in riesgo_por_cita
        ]
        return ResultadoPrevisualizacionPrediccion(estado="LISTO", items=items)


class ObtenerExplicacionRiesgoAusenciaCita:
    def __init__(self, queries: PrediccionAusenciasQueries, almacenamiento: AlmacenamientoModeloPrediccion) -> None:
        self._queries = queries
        self._almacenamiento = almacenamiento

    def ejecutar(self, cita_id: int) -> ExplicacionRiesgoAusenciaDTO:
        cita = self._queries.obtener_cita_para_explicacion(cita_id)
        if cita is None:
            return self._resultado_no_disponible(fecha_entrenamiento=None)

        try:
            predictor, metadata = self._almacenamiento.cargar()
        except ModeloPrediccionNoDisponibleError:
            return self._resultado_no_disponible(fecha_entrenamiento=None)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(
                "prediccion_explicacion_no_disponible",
                extra={"reason_code": "predictor_load_failed", "error": str(exc), "cita_id": cita_id},
            )
            return self._resultado_no_disponible(fecha_entrenamiento=None)

        prediccion = predictor.predecir(
            [
                CitaParaPrediccion(
                    cita_id=cita.cita_id, paciente_id=cita.paciente_id, dias_antelacion=cita.dias_antelacion
                )
            ]
        )
        if not prediccion:
            return self._resultado_no_disponible(fecha_entrenamiento=metadata.fecha_entrenamiento)

        historial = self._queries.obtener_resumen_historial_paciente(cita.paciente_id)
        motivos = self._construir_motivos(historial=historial, dias_antelacion=cita.dias_antelacion)
        return ExplicacionRiesgoAusenciaDTO(
            nivel=prediccion[0].riesgo.value,
            motivos=tuple(motivos[:_MAX_MOTIVOS]),
            acciones_sugeridas=(
                "citas.riesgo_dialogo.accion.enviar_recordatorio",
                "citas.riesgo_dialogo.accion.confirmar_telefono",
                "citas.riesgo_dialogo.accion.recordatorio_dia_previo",
            ),
            metadata_simple=MetadataExplicacionRiesgoDTO(
                fecha_entrenamiento=metadata.fecha_entrenamiento,
                necesita_entrenar=False,
            ),
        )

    @staticmethod
    def _resultado_no_disponible(fecha_entrenamiento: str | None) -> ExplicacionRiesgoAusenciaDTO:
        return ExplicacionRiesgoAusenciaDTO(
            nivel="NO_DISPONIBLE",
            motivos=(
                MotivoRiesgoDTO(
                    code="PREDICCION_NO_DISPONIBLE",
                    i18n_key="citas.riesgo_dialogo.motivo.prediccion_no_disponible",
                ),
            ),
            acciones_sugeridas=("citas.riesgo_dialogo.accion.ir_prediccion",),
            metadata_simple=MetadataExplicacionRiesgoDTO(
                fecha_entrenamiento=fecha_entrenamiento,
                necesita_entrenar=True,
            ),
        )

    def _construir_motivos(self, *, historial: ResumenHistorialPaciente, dias_antelacion: int) -> list[MotivoRiesgoDTO]:
        motivos: list[MotivoRiesgoDTO] = []
        total = historial.citas_realizadas + historial.citas_no_presentadas
        if historial.citas_no_presentadas > 0:
            motivos.append(
                MotivoRiesgoDTO(
                    code="HISTORIAL_AUSENCIAS",
                    i18n_key="citas.riesgo_dialogo.motivo.historial_ausencias",
                )
            )
        if total <= _POCOS_DATOS_MAX:
            motivos.append(
                MotivoRiesgoDTO(
                    code="POCOS_DATOS_PACIENTE",
                    i18n_key="citas.riesgo_dialogo.motivo.pocos_datos",
                    detalle_suave_key="citas.riesgo_dialogo.detalle.pocas_citas",
                )
            )
        if dias_antelacion <= 2:
            motivos.append(
                MotivoRiesgoDTO(
                    code="POCA_ANTELACION",
                    i18n_key="citas.riesgo_dialogo.motivo.poca_antelacion",
                )
            )
        if not motivos:
            motivos.append(
                MotivoRiesgoDTO(
                    code="HISTORIAL_ASISTENCIA",
                    i18n_key="citas.riesgo_dialogo.motivo.historial_asistencia",
                )
            )
        return motivos


class ObtenerResumenUltimoEntrenamientoPrediccion:
    def __init__(self, almacenamiento: AlmacenamientoModeloPrediccion) -> None:
        self._almacenamiento = almacenamiento

    def ejecutar(self) -> ResumenEntrenamientoModeloDTO:
        metadata = self._almacenamiento.cargar_metadata()
        if metadata is None:
            return ResumenEntrenamientoModeloDTO(
                disponible=False,
                reason_code="sin_metadata",
                fecha_entrenamiento=None,
                model_type=None,
                version=None,
                citas_usadas=None,
                muestras_train=None,
                muestras_validacion=None,
                tasa_no_show_train=None,
                tasa_no_show_validacion=None,
                accuracy=None,
                precision_no_show=None,
                recall_no_show=None,
                f1_no_show=None,
            )
        fecha_entrenamiento = getattr(metadata, "fecha_entrenamiento", None)
        if not isinstance(fecha_entrenamiento, str) or not fecha_entrenamiento.strip():
            LOGGER.warning(
                "prediccion_resumen_metadata_incompleta",
                extra={"reason_code": "fecha_entrenamiento_invalida", "metadata_type": type(metadata).__name__},
            )
            return ResumenEntrenamientoModeloDTO(
                disponible=False,
                reason_code="metadata_incompleta",
                fecha_entrenamiento=None,
                model_type=getattr(metadata, "model_type", None),
                version=getattr(metadata, "version", None),
                citas_usadas=getattr(metadata, "citas_usadas", None),
                muestras_train=getattr(metadata, "muestras_train", None),
                muestras_validacion=getattr(metadata, "muestras_validacion", None),
                tasa_no_show_train=getattr(metadata, "tasa_no_show_train", None),
                tasa_no_show_validacion=getattr(metadata, "tasa_no_show_validacion", None),
                accuracy=getattr(metadata, "accuracy", None),
                precision_no_show=getattr(metadata, "precision_no_show", None),
                recall_no_show=getattr(metadata, "recall_no_show", None),
                f1_no_show=getattr(metadata, "f1_no_show", None),
            )
        if getattr(metadata, "precision_no_show", None) is None or getattr(metadata, "f1_no_show", None) is None:
            LOGGER.info(
                "prediccion_resumen_metadata_legacy",
                extra={"reason_code": "legacy_metadata", "fecha_entrenamiento": fecha_entrenamiento},
            )
        return ResumenEntrenamientoModeloDTO(
            disponible=True,
            reason_code=None,
            fecha_entrenamiento=fecha_entrenamiento,
            model_type=getattr(metadata, "model_type", None),
            version=getattr(metadata, "version", None),
            citas_usadas=getattr(metadata, "citas_usadas", None),
            muestras_train=getattr(metadata, "muestras_train", None),
            muestras_validacion=getattr(metadata, "muestras_validacion", None),
            tasa_no_show_train=getattr(metadata, "tasa_no_show_train", None),
            tasa_no_show_validacion=getattr(metadata, "tasa_no_show_validacion", None),
            accuracy=getattr(metadata, "accuracy", None),
            precision_no_show=getattr(metadata, "precision_no_show", None),
            recall_no_show=getattr(metadata, "recall_no_show", None),
            f1_no_show=getattr(metadata, "f1_no_show", None),
        )


def _split_determinista_train_validacion(
    dataset: list[RegistroEntrenamiento],
    proporcion_validacion: float = 0.2,
) -> tuple[list[RegistroEntrenamiento], list[RegistroEntrenamiento]]:
    if len(dataset) <= 1:
        return dataset, []
    muestras_validacion = max(1, int(len(dataset) * proporcion_validacion))
    if muestras_validacion >= len(dataset):
        muestras_validacion = len(dataset) - 1
    corte = len(dataset) - muestras_validacion
    return dataset[:corte], dataset[corte:]


def _evaluar_predictor(
    *,
    predictor_entrenado,
    dataset_train: list[RegistroEntrenamiento],
    dataset_validacion: list[RegistroEntrenamiento],
) -> ResultadoEvaluacionEntrenamiento:
    etiquetas_reales = [item.no_vino for item in dataset_validacion]
    predicciones = predictor_entrenado.predecir(
        [
            CitaParaPrediccion(cita_id=idx, paciente_id=item.paciente_id, dias_antelacion=item.dias_antelacion)
            for idx, item in enumerate(dataset_validacion)
        ]
    )
    etiquetas_predichas = [1 if item.riesgo.value in {"MEDIO", "ALTO"} else 0 for item in predicciones]
    return ResultadoEvaluacionEntrenamiento(
        muestras_train=len(dataset_train),
        muestras_validacion=len(dataset_validacion),
        tasa_no_show_train=_tasa_no_show(dataset_train),
        tasa_no_show_validacion=_ratio(sum(etiquetas_reales), len(etiquetas_reales)),
        accuracy=_accuracy(etiquetas_reales, etiquetas_predichas),
        precision_no_show=_precision(etiquetas_reales, etiquetas_predichas),
        recall_no_show=_recall(etiquetas_reales, etiquetas_predichas),
        f1_no_show=_f1(etiquetas_reales, etiquetas_predichas),
    )


def _tasa_no_show(dataset: list[RegistroEntrenamiento]) -> float:
    return _ratio(sum(item.no_vino for item in dataset), len(dataset))


def _ratio(numerador: int, denominador: int) -> float:
    if denominador <= 0:
        return 0.0
    return round(numerador / denominador, 4)


def _accuracy(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true:
        return 0.0
    aciertos = sum(1 for real, pred in zip(y_true, y_pred, strict=False) if real == pred)
    return round(aciertos / len(y_true), 4)


def _precision(y_true: list[int], y_pred: list[int]) -> float:
    verdaderos_positivos = sum(1 for real, pred in zip(y_true, y_pred, strict=False) if pred == 1 and real == 1)
    falsos_positivos = sum(1 for real, pred in zip(y_true, y_pred, strict=False) if pred == 1 and real == 0)
    return _ratio(verdaderos_positivos, verdaderos_positivos + falsos_positivos)


def _recall(y_true: list[int], y_pred: list[int]) -> float:
    verdaderos_positivos = sum(1 for real, pred in zip(y_true, y_pred, strict=False) if pred == 1 and real == 1)
    falsos_negativos = sum(1 for real, pred in zip(y_true, y_pred, strict=False) if pred == 0 and real == 1)
    return _ratio(verdaderos_positivos, verdaderos_positivos + falsos_negativos)


def _f1(y_true: list[int], y_pred: list[int]) -> float:
    precision = _precision(y_true, y_pred)
    recall = _recall(y_true, y_pred)
    if precision + recall == 0:
        return 0.0
    return round((2 * precision * recall) / (precision + recall), 4)
