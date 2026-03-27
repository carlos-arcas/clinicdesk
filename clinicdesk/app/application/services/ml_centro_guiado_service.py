from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clinicdesk.app.application.ml_artifacts.feature_artifacts import FeatureArtifactMetadata
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.services.ml_playbooks_service import PlaybookML, PlaybooksMLService

ARCHIVOS_EXPORTACION = (
    "features_export.csv",
    "model_metrics_export.csv",
    "scoring_export.csv",
    "drift_export.csv",
)


@dataclass(frozen=True, slots=True)
class PasoCentroML:
    clave: str
    titulo: str
    descripcion: str
    estado: str
    habilitado: bool
    motivo_bloqueo: str


@dataclass(frozen=True, slots=True)
class EstadoCentroML:
    dataset_version: str | None
    model_version: str | None
    dataset_modelo_compatible: bool
    score_disponible: bool
    drift_disponible: bool
    export_disponible: bool
    archivos_exportados: tuple[str, ...]
    siguiente_accion: str
    pasos: tuple[PasoCentroML, ...]
    recomendaciones: tuple[RecomendacionML, ...]
    resumen_ejecutivo: ResumenEjecutivoML
    playbooks: tuple[PlaybookML, ...]
    playbook_sugerido: str


@dataclass(frozen=True, slots=True)
class RecomendacionML:
    codigo: str
    prioridad: int
    tipo: str
    estado_accion: str
    titulo_key: str
    explicacion_key: str
    motivo_key: str
    beneficio_key: str
    accion_key: str
    cta_key: str
    condicion_aplicabilidad: str


@dataclass(frozen=True, slots=True)
class ResumenEjecutivoML:
    estado_actual_key: str
    que_falta_key: str
    siguiente_paso_key: str
    riesgo_principal_key: str
    utilidad_inmediata_key: str


class CentroMLGuiadoService:
    def __init__(self, facade: DemoMLFacade) -> None:
        self._facade = facade
        self._playbooks = PlaybooksMLService()

    def construir_estado(self, export_dir: str) -> EstadoCentroML:
        dataset_versions = self._facade.list_dataset_versions()
        dataset_version = self._latest(dataset_versions)
        model_version = self._latest(self._facade.list_model_versions())
        dataset_meta = self._facade.load_dataset_metadata(dataset_version) if dataset_version else None
        model_meta = self._facade.load_model_metadata(model_version) if model_version else None
        compatible = self._is_compatible(dataset_version, model_meta)
        score_disponible = bool(dataset_version and model_version and compatible)
        drift_disponible = bool(dataset_version and len(dataset_versions) > 1)
        archivos = self._listar_archivos_exportados(export_dir)
        export_disponible = score_disponible and bool(archivos)
        pasos = self._build_pasos(dataset_meta, score_disponible, drift_disponible, export_disponible)
        recomendaciones = self._resolver_recomendaciones(
            dataset_ok=dataset_meta is not None and dataset_meta.row_count > 0,
            model_version=model_version,
            compatible=compatible,
            score_disponible=score_disponible,
            drift_disponible=drift_disponible,
            export_disponible=export_disponible,
            archivos=archivos,
            model_meta=model_meta,
        )
        resumen = self._build_resumen_ejecutivo(recomendaciones)
        estado_base = EstadoCentroML(
            dataset_version=dataset_version,
            model_version=model_version,
            dataset_modelo_compatible=compatible,
            score_disponible=score_disponible,
            drift_disponible=drift_disponible,
            export_disponible=export_disponible,
            archivos_exportados=archivos,
            siguiente_accion=self._resolver_siguiente_accion(pasos),
            pasos=pasos,
            recomendaciones=recomendaciones,
            resumen_ejecutivo=resumen,
            playbooks=(),
            playbook_sugerido="demo_completa",
        )
        playbooks = self._playbooks.construir_playbooks(estado_base)
        return EstadoCentroML(
            dataset_version=dataset_version,
            model_version=model_version,
            dataset_modelo_compatible=compatible,
            score_disponible=score_disponible,
            drift_disponible=drift_disponible,
            export_disponible=export_disponible,
            archivos_exportados=archivos,
            siguiente_accion=self._resolver_siguiente_accion(pasos),
            pasos=pasos,
            recomendaciones=recomendaciones,
            resumen_ejecutivo=resumen,
            playbooks=playbooks,
            playbook_sugerido=self._playbooks.sugerir_playbook(playbooks),
        )

    def _resolver_recomendaciones(
        self,
        dataset_ok: bool,
        model_version: str | None,
        compatible: bool,
        score_disponible: bool,
        drift_disponible: bool,
        export_disponible: bool,
        archivos: tuple[str, ...],
        model_meta: dict[str, object] | None,
    ) -> tuple[RecomendacionML, ...]:
        recomendaciones: list[RecomendacionML] = []
        if not dataset_ok:
            recomendaciones.append(self._recomendacion("dataset_faltante", 100, "bloqueo", "bloqueada"))
            recomendaciones.append(self._recomendacion("seed_demo", 90, "recomendacion", "recomendada"))
            return tuple(recomendaciones)
        if model_version is None:
            recomendaciones.append(self._recomendacion("entrenar_modelo", 95, "recomendacion", "recomendada"))
            recomendaciones.append(self._recomendacion("baseline_referencia", 50, "informacion", "posible"))
            return tuple(sorted(recomendaciones, key=lambda item: item.prioridad, reverse=True))
        if not compatible:
            recomendaciones.append(self._recomendacion("modelo_incompatible", 100, "bloqueo", "bloqueada"))
            recomendaciones.append(self._recomendacion("reentrenar_compatible", 92, "recomendacion", "recomendada"))
            return tuple(sorted(recomendaciones, key=lambda item: item.prioridad, reverse=True))
        if score_disponible:
            recomendaciones.append(self._recomendacion("ejecutar_scoring", 88, "recomendacion", "recomendada"))
            recomendaciones.append(self._evaluar_calidad_modelo(model_meta))
        if drift_disponible and "drift_export.csv" not in archivos:
            recomendaciones.append(self._recomendacion("drift_pendiente", 76, "advertencia", "recomendada"))
        elif not drift_disponible:
            recomendaciones.append(self._recomendacion("drift_no_necesario", 35, "informacion", "innecesaria"))
        if not export_disponible:
            recomendaciones.append(self._recomendacion("exportar_resultados", 70, "recomendacion", "posible"))
        else:
            recomendaciones.append(self._recomendacion("export_ok", 40, "informacion", "innecesaria"))
        return tuple(sorted(recomendaciones, key=lambda item: item.prioridad, reverse=True))

    def _evaluar_calidad_modelo(self, model_meta: dict[str, object] | None) -> RecomendacionML:
        if model_meta is None:
            return self._recomendacion("evaluacion_pendiente", 65, "advertencia", "posible")
        test_metrics = model_meta.get("test_metrics")
        if not isinstance(test_metrics, dict):
            return self._recomendacion("evaluacion_pendiente", 65, "advertencia", "posible")
        accuracy = float(test_metrics.get("accuracy", 0.0))
        precision = float(test_metrics.get("precision", 0.0))
        recall = float(test_metrics.get("recall", 0.0))
        if min(accuracy, precision, recall) < 0.55:
            return self._recomendacion("resultados_debiles", 84, "advertencia", "recomendada")
        return self._recomendacion("evaluacion_disponible", 58, "informacion", "posible")

    def _recomendacion(self, codigo: str, prioridad: int, tipo: str, estado_accion: str) -> RecomendacionML:
        base = f"demo_ml.asistente.{codigo}"
        return RecomendacionML(
            codigo=codigo,
            prioridad=prioridad,
            tipo=tipo,
            estado_accion=estado_accion,
            titulo_key=f"{base}.titulo",
            explicacion_key=f"{base}.explicacion",
            motivo_key=f"{base}.motivo",
            beneficio_key=f"{base}.beneficio",
            accion_key=f"{base}.accion",
            cta_key=f"{base}.cta",
            condicion_aplicabilidad=f"{base}.condicion",
        )

    def _build_resumen_ejecutivo(self, recomendaciones: tuple[RecomendacionML, ...]) -> ResumenEjecutivoML:
        principal = recomendaciones[0] if recomendaciones else None
        codigo = principal.codigo if principal else "sin_accion"
        base = f"demo_ml.resumen.{codigo}"
        return ResumenEjecutivoML(
            estado_actual_key=f"{base}.estado_actual",
            que_falta_key=f"{base}.que_falta",
            siguiente_paso_key=f"{base}.siguiente_paso",
            riesgo_principal_key=f"{base}.riesgo",
            utilidad_inmediata_key=f"{base}.utilidad",
        )

    def _build_pasos(
        self,
        dataset_meta: FeatureArtifactMetadata | None,
        score_disponible: bool,
        drift_disponible: bool,
        export_disponible: bool,
    ) -> tuple[PasoCentroML, ...]:
        dataset_ok = dataset_meta is not None and dataset_meta.row_count > 0
        return (
            PasoCentroML(
                clave="prepare",
                titulo="Preparar datos",
                descripcion="Genera el dataset de features para entrenar y analizar riesgo.",
                estado="completado" if dataset_ok else "pendiente",
                habilitado=True,
                motivo_bloqueo="",
            ),
            PasoCentroML(
                clave="train",
                titulo="Entrenar modelo",
                descripcion="Crea un modelo con el dataset preparado para poder puntuar.",
                estado="completado" if score_disponible else "pendiente",
                habilitado=dataset_ok,
                motivo_bloqueo="Necesitas preparar datos antes de entrenar." if not dataset_ok else "",
            ),
            PasoCentroML(
                clave="score",
                titulo="Puntuar citas",
                descripcion="Calcula riesgo por cita para priorizar seguimiento operativo.",
                estado="listo" if score_disponible else "bloqueado",
                habilitado=score_disponible,
                motivo_bloqueo="Modelo y dataset deben ser compatibles para puntuar." if not score_disponible else "",
            ),
            PasoCentroML(
                clave="drift",
                titulo="Revisar drift",
                descripcion="Compara versiones de dataset para detectar cambios de comportamiento.",
                estado="listo" if drift_disponible else "bloqueado",
                habilitado=drift_disponible,
                motivo_bloqueo="Necesitas al menos dos datasets para calcular drift." if not drift_disponible else "",
            ),
            PasoCentroML(
                clave="export",
                titulo="Exportar artefactos",
                descripcion="Genera CSV para reporting, auditoría y seguimiento externo.",
                estado="completado" if export_disponible else "pendiente",
                habilitado=score_disponible,
                motivo_bloqueo="Primero ejecuta scoring para exportar resultados útiles."
                if not score_disponible
                else "",
            ),
        )

    def _resolver_siguiente_accion(self, pasos: tuple[PasoCentroML, ...]) -> str:
        for paso in pasos:
            if paso.estado in {"pendiente", "bloqueado", "listo"}:
                return paso.clave
        return "summary"

    def _listar_archivos_exportados(self, export_dir: str) -> tuple[str, ...]:
        base = Path(export_dir)
        if not base.exists():
            return ()
        encontrados = [name for name in ARCHIVOS_EXPORTACION if (base / name).exists()]
        return tuple(encontrados)

    def _is_compatible(self, dataset_version: str | None, model_meta: dict[str, object] | None) -> bool:
        if not dataset_version or model_meta is None:
            return False
        trained_on = str(model_meta.get("trained_on_dataset_version", ""))
        return trained_on == dataset_version

    def _latest(self, versions: list[str]) -> str | None:
        if not versions:
            return None
        return sorted(versions)[-1]
