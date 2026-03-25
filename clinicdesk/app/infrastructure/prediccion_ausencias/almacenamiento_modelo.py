from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.infrastructure.prediccion_ausencias.rutas_app import carpeta_datos_app


LOGGER = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MetadataModeloPrediccion:
    fecha_entrenamiento: str
    citas_usadas: int
    version: str
    model_type: str = "PredictorAusenciasBaseline"
    muestras_train: int | None = None
    muestras_validacion: int | None = None
    tasa_no_show_train: float | None = None
    tasa_no_show_validacion: float | None = None
    accuracy: float | None = None
    precision_no_show: float | None = None
    recall_no_show: float | None = None
    f1_no_show: float | None = None


class ModeloPrediccionNoDisponibleError(FileNotFoundError):
    pass


class AlmacenamientoModeloPrediccion:
    def __init__(self, base_dir: Path | None = None) -> None:
        root = base_dir or carpeta_datos_app()
        self._dir = root / "prediccion_ausencias"
        self._dir.mkdir(parents=True, exist_ok=True)

    @property
    def carpeta_modelo(self) -> Path:
        return self._dir

    def guardar(
        self,
        predictor_entrenado: Any,
        *,
        citas_usadas: int,
        version: str,
        model_type: str = "PredictorAusenciasBaseline",
        muestras_train: int | None = None,
        muestras_validacion: int | None = None,
        tasa_no_show_train: float | None = None,
        tasa_no_show_validacion: float | None = None,
        accuracy: float | None = None,
        precision_no_show: float | None = None,
        recall_no_show: float | None = None,
        f1_no_show: float | None = None,
    ) -> MetadataModeloPrediccion:
        metadata = MetadataModeloPrediccion(
            fecha_entrenamiento=datetime.now(timezone.utc).isoformat(),
            citas_usadas=citas_usadas,
            version=version,
            model_type=model_type,
            muestras_train=muestras_train,
            muestras_validacion=muestras_validacion,
            tasa_no_show_train=tasa_no_show_train,
            tasa_no_show_validacion=tasa_no_show_validacion,
            accuracy=accuracy,
            precision_no_show=precision_no_show,
            recall_no_show=recall_no_show,
            f1_no_show=f1_no_show,
        )
        with self._modelo_path().open("wb") as handle:
            pickle.dump(predictor_entrenado, handle)
        with self._metadata_path().open("w", encoding="utf-8") as handle:
            json.dump(asdict(metadata), handle, ensure_ascii=False, indent=2)
        return metadata

    def cargar(self) -> tuple[Any, MetadataModeloPrediccion]:
        if not self._modelo_path().exists() or not self._metadata_path().exists():
            raise ModeloPrediccionNoDisponibleError("sin_modelo")
        with self._modelo_path().open("rb") as handle:
            predictor = pickle.load(handle)
        metadata = self._leer_metadata()
        return predictor, metadata

    def cargar_metadata(self) -> MetadataModeloPrediccion | None:
        if not self._metadata_path().exists():
            return None
        try:
            return self._leer_metadata()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning(
                "prediccion_metadata_no_legible",
                extra={"reason_code": "metadata_load_failed", "error": str(exc)},
            )
            return None

    def _leer_metadata(self) -> MetadataModeloPrediccion:
        data = json.loads(self._metadata_path().read_text(encoding="utf-8"))
        return MetadataModeloPrediccion(**data)

    def _modelo_path(self) -> Path:
        return self._dir / "predictor.pkl"

    def _metadata_path(self) -> Path:
        return self._dir / "metadata.json"
