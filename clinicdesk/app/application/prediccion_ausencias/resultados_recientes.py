from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.queries.prediccion_ausencias_resultados_queries import (
    DiagnosticoResultadosRecientesRaw,
    FilaResultadoRecientePrediccion,
    ItemRegistroPrediccionAusencia,
    ResultadoRecientePrediccion,
    ahora_utc_iso,
)

LOGGER = get_logger(__name__)
_RIESGOS_ORDEN = ("BAJO", "MEDIO", "ALTO")


class DiagnosticoResultadosRecientes(StrEnum):
    OK = "OK"
    SIN_CITAS_CERRADAS = "SIN_CITAS_CERRADAS"
    SIN_PREDICCIONES_REGISTRADAS = "SIN_PREDICCIONES_REGISTRADAS"
    DATOS_INSUFICIENTES = "DATOS_INSUFICIENTES"


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
    diagnostico: DiagnosticoResultadosRecientes
    mensaje_i18n_key: str
    acciones_i18n_keys: tuple[str, ...]
    total_citas_cerradas_en_ventana: int
    total_predicciones_registradas_en_ventana: int
    total_predicciones_con_resultado: int


class RepositorioResultadosRecientesPrediccion(Protocol):
    def registrar_predicciones_ausencias(self, modelo_fecha_utc: str, items: list[ItemRegistroPrediccionAusencia]) -> int:
        ...

    def obtener_resultados_recientes_prediccion(self, ventana_dias: int = 60) -> ResultadoRecientePrediccion:
        ...

    def obtener_diagnostico_resultados_recientes(self, ventana_dias: int) -> DiagnosticoResultadosRecientesRaw:
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
        diagnostico_raw = self.repositorio.obtener_diagnostico_resultados_recientes(ventana_dias=ventana_dias)
        diagnostico = self._resolver_diagnostico(diagnostico_raw)
        filas = tuple()
        if diagnostico is DiagnosticoResultadosRecientes.OK:
            resultado = self.repositorio.obtener_resultados_recientes_prediccion(ventana_dias=ventana_dias)
            filas = self._normalizar_filas(resultado.filas)
            version_modelo = resultado.version_modelo_fecha_utc
        else:
            version_modelo = diagnostico_raw.version_objetivo
        return ResultadoRecientesPrediccionDTO(
            version_modelo_fecha_utc=version_modelo,
            ventana_dias=ventana_dias,
            filas=filas,
            diagnostico=diagnostico,
            mensaje_i18n_key=self._mensaje_clave(diagnostico),
            acciones_i18n_keys=self._acciones_clave(diagnostico),
            total_citas_cerradas_en_ventana=diagnostico_raw.total_citas_cerradas_en_ventana,
            total_predicciones_registradas_en_ventana=diagnostico_raw.total_predicciones_registradas_en_ventana,
            total_predicciones_con_resultado=diagnostico_raw.total_predicciones_con_resultado,
        )

    def _resolver_diagnostico(self, datos: DiagnosticoResultadosRecientesRaw) -> DiagnosticoResultadosRecientes:
        if datos.total_citas_cerradas_en_ventana < self.umbral_minimo:
            return DiagnosticoResultadosRecientes.SIN_CITAS_CERRADAS
        if datos.total_predicciones_registradas_en_ventana == 0:
            return DiagnosticoResultadosRecientes.SIN_PREDICCIONES_REGISTRADAS
        if datos.total_predicciones_con_resultado < self.umbral_minimo:
            return DiagnosticoResultadosRecientes.DATOS_INSUFICIENTES
        return DiagnosticoResultadosRecientes.OK

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
    def _mensaje_clave(diagnostico: DiagnosticoResultadosRecientes) -> str:
        return f"prediccion_ausencias.resultados.diagnostico.{diagnostico.value.lower()}"

    @staticmethod
    def _acciones_clave(diagnostico: DiagnosticoResultadosRecientes) -> tuple[str, ...]:
        if diagnostico is DiagnosticoResultadosRecientes.SIN_CITAS_CERRADAS:
            return ("prediccion_ausencias.resultados.cta.cerrar_citas_antiguas",)
        if diagnostico is DiagnosticoResultadosRecientes.SIN_PREDICCIONES_REGISTRADAS:
            return (
                "prediccion_ausencias.resultados.cta.abrir_confirmaciones",
                "prediccion_ausencias.resultados.cta.activar_riesgo_agenda",
            )
        if diagnostico is DiagnosticoResultadosRecientes.DATOS_INSUFICIENTES:
            return (
                "prediccion_ausencias.resultados.cta.cerrar_citas_antiguas",
                "prediccion_ausencias.resultados.cta.abrir_confirmaciones",
            )
        return tuple()
