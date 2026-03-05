from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from clinicdesk.app.application.prediccion_operativa.dtos import (
    CitaProximaOperativaDTO,
    ExplicacionOperativaDTO,
    PrediccionOperativaDTO,
    ResultadoComprobacionOperativa,
    ResultadoEntrenamientoOperativo,
    SaludPrediccionOperativaDTO,
)
from clinicdesk.app.application.prediccion_operativa.salud import resolver_estado_salud
from clinicdesk.app.domain.prediccion_operativa import CitaOperativa, RegistroOperativo
from clinicdesk.app.infrastructure.prediccion_operativa import (
    AlmacenamientoModeloOperativo,
    ModeloOperativoNoDisponibleError,
)
from clinicdesk.app.queries.prediccion_operativa_queries import PrediccionOperativaQueries


@dataclass(frozen=True, slots=True)
class ComprobarDatosPrediccionOperativa:
    queries: PrediccionOperativaQueries
    tipo: str
    minimo_requerido: int = 50

    def ejecutar(self) -> ResultadoComprobacionOperativa:
        total = len(self._dataset_ventana())
        return ResultadoComprobacionOperativa(total, self.minimo_requerido, total >= self.minimo_requerido)

    def _dataset_ventana(self) -> list[object]:
        desde, hasta = _ventana_180d()
        if self.tipo == "duracion":
            return self.queries.obtener_dataset_duracion(desde, hasta)
        return self.queries.obtener_dataset_espera(desde, hasta)


@dataclass(frozen=True, slots=True)
class EntrenarPrediccionOperativa:
    queries: PrediccionOperativaQueries
    predictor: object
    almacenamiento: AlmacenamientoModeloOperativo
    tipo: str

    def ejecutar(self) -> ResultadoEntrenamientoOperativo:
        desde, hasta = _ventana_180d()
        dataset = self._cargar_dataset(desde, hasta)
        modelo = self.predictor.entrenar(dataset)
        metadata = self.almacenamiento.guardar_con_ventana(
            modelo,
            n_ejemplos=len(dataset),
            desde=desde,
            hasta=hasta,
            version=f"prediccion_{self.tipo}_v1",
        )
        return ResultadoEntrenamientoOperativo(metadata.n_ejemplos, metadata.fecha_entrenamiento)

    def _cargar_dataset(self, desde: str, hasta: str) -> list[RegistroOperativo]:
        if self.tipo == "duracion":
            return [
                RegistroOperativo(x.medico_id, x.tipo_cita, None, None, x.duracion_min)
                for x in self.queries.obtener_dataset_duracion(desde, hasta)
            ]
        return [
            RegistroOperativo(x.medico_id, None, x.franja_hora, x.dia_semana, x.espera_min)
            for x in self.queries.obtener_dataset_espera(desde, hasta)
        ]


@dataclass(frozen=True, slots=True)
class PrevisualizarPrediccionOperativa:
    queries: PrediccionOperativaQueries
    almacenamiento: AlmacenamientoModeloOperativo

    def ejecutar(self, dias: int = 7) -> dict[int, PrediccionOperativaDTO]:
        try:
            modelo, _ = self.almacenamiento.cargar()
        except ModeloOperativoNoDisponibleError:
            return {}
        desde = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hasta = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
        citas = [
            CitaOperativa(x.cita_id, x.medico_id, x.tipo_cita, x.franja_hora, x.dia_semana)
            for x in self.queries.obtener_proximas_citas_para_prediccion(desde, hasta)
        ]
        return {x.cita_id: PrediccionOperativaDTO(x.cita_id, x.nivel.value) for x in modelo.predecir(citas)}


@dataclass(frozen=True, slots=True)
class ObtenerSaludPrediccionOperativa:
    queries: PrediccionOperativaQueries
    almacenamiento: AlmacenamientoModeloOperativo
    tipo: str

    def ejecutar(self) -> SaludPrediccionOperativaDTO:
        metadata = self.almacenamiento.cargar_metadata()
        recientes = (
            self.queries.contar_citas_validas_recientes_duracion()
            if self.tipo == "duracion"
            else self.queries.contar_citas_validas_recientes_espera()
        )
        fecha = metadata.fecha_entrenamiento if metadata else None
        return SaludPrediccionOperativaDTO(resolver_estado_salud(fecha, recientes), fecha, recientes)


@dataclass(frozen=True, slots=True)
class ObtenerExplicacionPrediccionOperativa:
    almacenamiento: AlmacenamientoModeloOperativo

    def ejecutar(self, cita_id: int, nivel: str) -> ExplicacionOperativaDTO:
        try:
            modelo, _ = self.almacenamiento.cargar()
        except ModeloOperativoNoDisponibleError:
            return ExplicacionOperativaDTO(
                "NO_DISPONIBLE",
                ("citas.prediccion_operativa.motivo.no_disponible",),
                ("citas.prediccion_operativa.cta.entrenar",),
                True,
            )
        reasons = getattr(modelo, "ultimos_motivos", {}).get(cita_id, ())
        motivos = tuple(f"citas.prediccion_operativa.motivo.{code.lower()}" for code in reasons) or (
            "citas.prediccion_operativa.motivo.referencia_general",
        )
        return ExplicacionOperativaDTO(
            nivel,
            motivos[:3],
            ("citas.prediccion_operativa.cta.ajustar_huecos", "citas.prediccion_operativa.cta.avisar_paciente"),
            False,
        )


@dataclass(frozen=True, slots=True)
class ListarProximasCitasOperativas:
    queries: PrediccionOperativaQueries

    def ejecutar(self, dias: int = 30, limite: int = 30) -> list[CitaProximaOperativaDTO]:
        desde = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hasta = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
        filas = self.queries.obtener_proximas_citas_detalle(desde, hasta, limite)
        return [
            CitaProximaOperativaDTO(
                cita_id=fila.cita_id,
                fecha=fila.fecha,
                hora=fila.hora,
                paciente=fila.paciente,
                medico=fila.medico,
            )
            for fila in filas
        ]


def _ventana_180d() -> tuple[str, str]:
    hasta = datetime.now()
    desde = hasta - timedelta(days=180)
    return desde.strftime("%Y-%m-%d %H:%M:%S"), hasta.strftime("%Y-%m-%d %H:%M:%S")
