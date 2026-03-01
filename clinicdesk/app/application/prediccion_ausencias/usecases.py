from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.dtos import (
    DatosEntrenamientoPrediccion,
    PrediccionCitaDTO,
    ResultadoComprobacionDatos,
    ResultadoPrevisualizacionPrediccion,
)
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.domain.prediccion_ausencias import CitaParaPrediccion, RegistroEntrenamiento
from clinicdesk.app.infrastructure.prediccion_ausencias import (
    AlmacenamientoModeloPrediccion,
    ModeloPrediccionNoDisponibleError,
)
from clinicdesk.app.queries.prediccion_ausencias_queries import PrediccionAusenciasQueries

LOGGER = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ResultadoEntrenamientoPrediccion:
    citas_usadas: int
    fecha_entrenamiento: str


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
        predictor,
        almacenamiento: AlmacenamientoModeloPrediccion,
    ) -> None:
        self._comprobar_datos_uc = comprobar_datos_uc
        self._queries = queries
        self._predictor = predictor
        self._almacenamiento = almacenamiento

    def ejecutar(self) -> ResultadoEntrenamientoPrediccion:
        chequeo = self._comprobar_datos_uc.ejecutar()
        if not chequeo.apto_para_entrenar:
            raise ValueError("datos_insuficientes")

        dataset = self._construir_dataset(self._queries.obtener_dataset_entrenamiento())
        predictor_entrenado = self._predictor.entrenar(dataset)
        metadata = self._almacenamiento.guardar(
            predictor_entrenado,
            citas_usadas=len(dataset),
            version="prediccion_ausencias_v1",
        )
        return ResultadoEntrenamientoPrediccion(
            citas_usadas=metadata.citas_usadas,
            fecha_entrenamiento=metadata.fecha_entrenamiento,
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
