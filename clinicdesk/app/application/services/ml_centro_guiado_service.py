from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clinicdesk.app.application.ml_artifacts.feature_artifacts import FeatureArtifactMetadata
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade

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


class CentroMLGuiadoService:
    def __init__(self, facade: DemoMLFacade) -> None:
        self._facade = facade

    def construir_estado(self, export_dir: str) -> EstadoCentroML:
        dataset_version = self._latest(self._facade.list_dataset_versions())
        model_version = self._latest(self._facade.list_model_versions())
        dataset_meta = self._facade.load_dataset_metadata(dataset_version) if dataset_version else None
        model_meta = self._facade.load_model_metadata(model_version) if model_version else None
        compatible = self._is_compatible(dataset_version, model_meta)
        score_disponible = bool(dataset_version and model_version and compatible)
        drift_disponible = bool(dataset_version and len(self._facade.list_dataset_versions()) > 1)
        archivos = self._listar_archivos_exportados(export_dir)
        export_disponible = score_disponible and bool(archivos)
        pasos = self._build_pasos(dataset_meta, score_disponible, drift_disponible, export_disponible)
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
                motivo_bloqueo="Primero ejecuta scoring para exportar resultados útiles." if not score_disponible else "",
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
