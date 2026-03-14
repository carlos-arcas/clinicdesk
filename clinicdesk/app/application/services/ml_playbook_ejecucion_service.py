from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from clinicdesk.app.application.ml.interpretacion_ml_humana import (
    interpretar_drift,
    interpretar_entrenamiento,
    interpretar_scoring,
)
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.services.ml_playbooks_service import PlaybookML, PasoPlaybookML
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)

EstadoPasoEjecucion = Literal[
    "pendiente",
    "listo",
    "ejecutando",
    "completado",
    "fallido",
    "bloqueado",
    "innecesario",
]
TipoPermisoEjecucion = Literal["directa", "requiere_confirmacion", "bloqueada"]


@dataclass(frozen=True, slots=True)
class AccionPlaybookEjecutable:
    playbook_codigo: str
    paso_clave: str
    accion_clave: str
    permiso: TipoPermisoEjecucion
    motivo_key: str
    cta_key: str
    requiere_confirmacion: bool


@dataclass(frozen=True, slots=True)
class ResultadoPasoPlaybook:
    playbook_codigo: str
    paso_clave: str
    accion_clave: str
    estado: EstadoPasoEjecucion
    resumen_key: str
    detalle_humano: str
    siguiente_paso_clave: str
    reintento_permitido: bool


@dataclass(frozen=True, slots=True)
class ResumenProgresoPlaybook:
    total_pasos: int
    completados: int
    fallidos: int
    bloqueados: int
    ejecutables: int
    paso_actual_clave: str


@dataclass(frozen=True, slots=True)
class EstadoEjecucionPlaybook:
    playbook_codigo: str
    accion_siguiente: AccionPlaybookEjecutable
    progreso: ResumenProgresoPlaybook


@dataclass(frozen=True, slots=True)
class ContextoEjecucionPlaybook:
    from_date: str
    to_date: str
    score_limit: int
    export_dir: str


class PlaybookEjecucionService:
    _EJECUTABLES = {"prepare", "train", "score", "drift"}

    def __init__(self, facade: DemoMLFacade) -> None:
        self._facade = facade

    def construir_estado(self, playbook: PlaybookML) -> EstadoEjecucionPlaybook:
        accion_siguiente = self._resolver_accion(playbook)
        return EstadoEjecucionPlaybook(
            playbook_codigo=playbook.codigo,
            accion_siguiente=accion_siguiente,
            progreso=self._resumen_progreso(playbook),
        )

    def ejecutar_accion(
        self,
        accion: AccionPlaybookEjecutable,
        contexto: ContextoEjecucionPlaybook,
    ) -> ResultadoPasoPlaybook:
        if accion.permiso == "bloqueada":
            raise ValueError("Acción bloqueada por guardrails")
        try:
            detalle = self._ejecutar_por_accion(accion.accion_clave, contexto)
        except Exception:  # noqa: BLE001
            LOGGER.exception(
                "playbook_step_failed",
                extra={"playbook": accion.playbook_codigo, "accion": accion.accion_clave},
            )
            return ResultadoPasoPlaybook(
                playbook_codigo=accion.playbook_codigo,
                paso_clave=accion.paso_clave,
                accion_clave=accion.accion_clave,
                estado="fallido",
                resumen_key="demo_ml.playbook.ejecucion.resultado.fallido",
                detalle_humano="",
                siguiente_paso_clave=accion.accion_clave,
                reintento_permitido=True,
            )
        LOGGER.info(
            "playbook_step_done",
            extra={"playbook": accion.playbook_codigo, "accion": accion.accion_clave},
        )
        return ResultadoPasoPlaybook(
            playbook_codigo=accion.playbook_codigo,
            paso_clave=accion.paso_clave,
            accion_clave=accion.accion_clave,
            estado="completado",
            resumen_key="demo_ml.playbook.ejecucion.resultado.ok",
            detalle_humano=detalle,
            siguiente_paso_clave=self._siguiente_esperado(accion.accion_clave),
            reintento_permitido=False,
        )

    def _resolver_accion(self, playbook: PlaybookML) -> AccionPlaybookEjecutable:
        paso = self._buscar_siguiente_paso(playbook)
        if paso is None:
            return AccionPlaybookEjecutable(
                playbook_codigo=playbook.codigo,
                paso_clave=f"{playbook.codigo}.summary",
                accion_clave="summary",
                permiso="bloqueada",
                motivo_key="demo_ml.playbook.ejecucion.bloqueada.sin_pasos",
                cta_key="demo_ml.playbook.ejecucion.cta.sin_accion",
                requiere_confirmacion=False,
            )
        permiso = self._resolver_permiso(paso)
        return AccionPlaybookEjecutable(
            playbook_codigo=playbook.codigo,
            paso_clave=paso.clave,
            accion_clave=paso.accion_clave,
            permiso=permiso,
            motivo_key=self._resolver_motivo_permiso(paso, permiso),
            cta_key=paso.cta_key,
            requiere_confirmacion=permiso == "requiere_confirmacion",
        )

    def _buscar_siguiente_paso(self, playbook: PlaybookML) -> PasoPlaybookML | None:
        for estado in ("recomendado", "disponible", "completado"):
            for paso in playbook.pasos:
                if paso.estado == estado and paso.accion_clave in self._EJECUTABLES:
                    return paso
        return None

    def _resolver_permiso(self, paso: PasoPlaybookML) -> TipoPermisoEjecucion:
        if paso.estado in {"bloqueado", "innecesario"}:
            return "bloqueada"
        if paso.estado == "completado":
            return "requiere_confirmacion"
        if not paso.habilitado or paso.accion_clave not in self._EJECUTABLES:
            return "bloqueada"
        return "directa"

    def _resolver_motivo_permiso(self, paso: PasoPlaybookML, permiso: TipoPermisoEjecucion) -> str:
        if permiso == "directa":
            return "demo_ml.playbook.ejecucion.permiso.directa"
        if permiso == "requiere_confirmacion":
            return "demo_ml.playbook.ejecucion.permiso.confirmacion"
        return paso.motivo_estado_key

    def _resumen_progreso(self, playbook: PlaybookML) -> ResumenProgresoPlaybook:
        total = len(playbook.pasos)
        completados = sum(1 for paso in playbook.pasos if paso.estado == "completado")
        bloqueados = sum(1 for paso in playbook.pasos if paso.estado == "bloqueado")
        ejecutables = sum(1 for paso in playbook.pasos if paso.estado in {"recomendado", "disponible"})
        return ResumenProgresoPlaybook(
            total_pasos=total,
            completados=completados,
            fallidos=0,
            bloqueados=bloqueados,
            ejecutables=ejecutables,
            paso_actual_clave=playbook.siguiente_paso_clave,
        )

    def _ejecutar_por_accion(self, accion: str, contexto: ContextoEjecucionPlaybook) -> str:
        if accion == "prepare":
            dataset_version = self._facade.build_features(contexto.from_date, contexto.to_date, None)
            return f"Dataset generado: {dataset_version}."
        if accion == "train":
            dataset_version = self._latest(self._facade.list_dataset_versions())
            if dataset_version is None:
                raise ValueError("No hay dataset para entrenar")
            train_response = self._facade.train(dataset_version, None)
            texto = interpretar_entrenamiento(
                train_response.test_metrics.accuracy,
                train_response.test_metrics.precision,
                train_response.test_metrics.recall,
            )
            return f"Modelo {train_response.model_version}. {texto.significado}"
        if accion == "score":
            dataset_version = self._latest(self._facade.list_dataset_versions())
            model_version = self._latest(self._facade.list_model_versions())
            if dataset_version is None or model_version is None:
                raise ValueError("Faltan dataset/modelo para scoring")
            score_response = self._facade.score(
                dataset_version,
                predictor_kind="trained",
                model_version=model_version,
                limit=contexto.score_limit,
            )
            riesgo = sum(1 for item in score_response.items if item.label == "risk")
            texto = interpretar_scoring(score_response.total, riesgo)
            return f"Scoring sobre {score_response.total} citas. {texto.recomendacion}"
        if accion == "drift":
            versions = sorted(self._facade.list_dataset_versions())
            if len(versions) < 2:
                raise ValueError("Se requieren dos datasets para drift")
            report = self._facade.drift(versions[-2], versions[-1])
            texto = interpretar_drift(report)
            return f"Drift {report.overall_flag}. {texto.significado}"
        raise ValueError(f"Acción no soportada: {accion}")

    def _latest(self, versions: list[str]) -> str | None:
        if not versions:
            return None
        return sorted(versions)[-1]

    def _siguiente_esperado(self, accion: str) -> str:
        orden = ["prepare", "train", "score", "drift", "export"]
        if accion not in orden:
            return "summary"
        indice = orden.index(accion)
        return orden[indice + 1] if indice + 1 < len(orden) else "summary"
