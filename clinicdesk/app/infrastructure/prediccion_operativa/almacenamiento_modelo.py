from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clinicdesk.app.infrastructure.prediccion_operativa.rutas_app import carpeta_datos_app


@dataclass(frozen=True, slots=True)
class MetadataModeloOperativo:
    fecha_entrenamiento: str
    n_ejemplos: int
    ventana_desde: str
    ventana_hasta: str
    version_esquema: str


class ModeloOperativoNoDisponibleError(FileNotFoundError):
    pass


class AlmacenamientoModeloOperativo:
    def __init__(self, nombre_modelo: str, base_dir: Path | None = None) -> None:
        self._dir = (base_dir or carpeta_datos_app()) / nombre_modelo
        self._dir.mkdir(parents=True, exist_ok=True)

    def guardar(self, predictor_entrenado: Any, metadata: MetadataModeloOperativo) -> MetadataModeloOperativo:
        self._modelo_path().write_bytes(pickle.dumps(predictor_entrenado))
        self._metadata_path().write_text(json.dumps(asdict(metadata), ensure_ascii=False, indent=2), encoding="utf-8")
        return metadata

    def guardar_con_ventana(self, predictor_entrenado: Any, *, n_ejemplos: int, desde: str, hasta: str, version: str) -> MetadataModeloOperativo:
        return self.guardar(
            predictor_entrenado,
            MetadataModeloOperativo(
                fecha_entrenamiento=datetime.now(timezone.utc).isoformat(),
                n_ejemplos=n_ejemplos,
                ventana_desde=desde,
                ventana_hasta=hasta,
                version_esquema=version,
            ),
        )

    def cargar(self) -> tuple[Any, MetadataModeloOperativo]:
        if not self._modelo_path().exists() or not self._metadata_path().exists():
            raise ModeloOperativoNoDisponibleError("sin_modelo")
        return pickle.loads(self._modelo_path().read_bytes()), self.cargar_metadata_obligatoria()

    def cargar_metadata(self) -> MetadataModeloOperativo | None:
        if not self._metadata_path().exists():
            return None
        return self.cargar_metadata_obligatoria()

    def cargar_metadata_obligatoria(self) -> MetadataModeloOperativo:
        return MetadataModeloOperativo(**json.loads(self._metadata_path().read_text(encoding="utf-8")))

    def _modelo_path(self) -> Path:
        return self._dir / "modelo.pkl"

    def _metadata_path(self) -> Path:
        return self._dir / "metadata.json"
