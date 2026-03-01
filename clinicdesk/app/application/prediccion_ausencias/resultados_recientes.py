from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.queries.prediccion_ausencias_resultados_queries import (
    FilaResultadoRecientePrediccion,
    ItemRegistroPrediccionAusencia,
    ResultadoRecientePrediccion,
    ahora_utc_iso,
)

LOGGER = get_logger(__name__)
_RIESGOS_ORDEN = ("BAJO", "MEDIO", "ALTO")


@dataclass(frozen=True, slots=True)
class FilaResultadoRecienteDTO:
    riesgo: str
    total_predichas: int
    total_no_vino: int
    total_vino: int


@dataclass(frozen=True, slots=True)
class ResultadoRecientesPrediccionDTO:
    version_modelo_fecha_utc: str | None
    ventana_dias: int
    filas: tuple[FilaResultadoRecienteDTO, ...]
    estado_evaluacion: str
    mensaje_i18n_key: str
    acciones_i18n_keys: tuple[str, ...]


class RepositorioResultadosRecientesPrediccion(Protocol):
    def registrar_predicciones_ausencias(self, modelo_fecha_utc: str, items: list[ItemRegistroPrediccionAusencia]) -> int:
        ...

    def obtener_resultados_recientes_prediccion(self, ventana_dias: int = 60) -> ResultadoRecientePrediccion:
        ...


@dataclass(slots=True)
class RegistrarPrediccionesAusenciasAgenda:
    repositorio: RepositorioResultadosRecientesPrediccion

    def ejecutar(self, modelo_fecha_utc: str, riesgo_por_cita: dict[int, str], source: str = "agenda") -> int:
        if not modelo_fecha_utc:
            return 0
        items = self._construir_items(riesgo_por_cita, source)
        insertadas = self.repositorio.registrar_predicciones_ausencias(modelo_fecha_utc, items)
        LOGGER.info(
            "registrar_predicciones",
            extra={
                "action": "registrar_predicciones",
                "modelo_fecha_utc": modelo_fecha_utc,
                "total_citas": len(riesgo_por_cita),
                "total_registrables": len(items),
                "insertadas": insertadas,
            },
        )
        return insertadas

    @staticmethod
    def _construir_items(riesgo_por_cita: dict[int, str], source: str) -> list[ItemRegistroPrediccionAusencia]:
        timestamp = ahora_utc_iso()
        return [
            ItemRegistroPrediccionAusencia(cita_id=cita_id, riesgo=riesgo, timestamp_utc=timestamp, source=source)
            for cita_id, riesgo in riesgo_por_cita.items()
            if riesgo in _RIESGOS_ORDEN
        ]


@dataclass(slots=True)
class ObtenerResultadosRecientesPrediccionAusencias:
    repositorio: RepositorioResultadosRecientesPrediccion
    umbral_minimo: int = 20

    def ejecutar(self, ventana_dias: int = 60) -> ResultadoRecientesPrediccionDTO:
        resultado = self.repositorio.obtener_resultados_recientes_prediccion(ventana_dias=ventana_dias)
        filas = self._normalizar_filas(resultado.filas)
        total_predichas = sum(fila.total_predichas for fila in filas)
        estado = "OK" if total_predichas >= self.umbral_minimo else "SIN_DATOS"
        return ResultadoRecientesPrediccionDTO(
            version_modelo_fecha_utc=resultado.version_modelo_fecha_utc,
            ventana_dias=ventana_dias,
            filas=filas,
            estado_evaluacion=estado,
            mensaje_i18n_key=self._mensaje_clave(estado),
            acciones_i18n_keys=self._acciones_clave(estado),
        )

    @staticmethod
    def _normalizar_filas(filas: tuple[FilaResultadoRecientePrediccion, ...]) -> tuple[FilaResultadoRecienteDTO, ...]:
        por_riesgo = {
            fila.riesgo: FilaResultadoRecienteDTO(
                riesgo=fila.riesgo,
                total_predichas=fila.total_predichas,
                total_no_vino=fila.total_no_vino,
                total_vino=fila.total_vino,
            )
            for fila in filas
        }
        return tuple(
            por_riesgo.get(
                riesgo,
                FilaResultadoRecienteDTO(riesgo=riesgo, total_predichas=0, total_no_vino=0, total_vino=0),
            )
            for riesgo in _RIESGOS_ORDEN
        )

    @staticmethod
    def _mensaje_clave(estado: str) -> str:
        if estado == "OK":
            return "prediccion_ausencias.resultados.estado.ok"
        return "prediccion_ausencias.resultados.estado.sin_datos"

    @staticmethod
    def _acciones_clave(estado: str) -> tuple[str, ...]:
        if estado == "OK":
            return tuple()
        return ("prediccion_ausencias.resultados.accion.completar_resultado",)
