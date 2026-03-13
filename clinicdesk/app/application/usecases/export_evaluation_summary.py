from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from clinicdesk.app.application.ml.evaluation import EvalMetrics


@dataclass(slots=True)
class EvaluationSummaryData:
    model_name: str
    model_version: str
    dataset_version: str
    predictor_kind: str
    trained_on_dataset_version: str
    created_at: str
    calibrated_threshold: float
    train_metrics: EvalMetrics
    test_metrics: EvalMetrics
    calibrated_test_metrics: EvalMetrics
    test_row_count: int
    evaluation_note: str


class ExportEvaluationSummary:
    JSON_NAME = "evaluation_summary.json"
    MD_NAME = "evaluation_summary.md"

    def execute(self, data: EvaluationSummaryData, output_path: str | Path) -> dict[str, Path]:
        base = Path(output_path)
        base.mkdir(parents=True, exist_ok=True)
        json_path = base / self.JSON_NAME
        md_path = base / self.MD_NAME
        self._write_json(json_path, data)
        self._write_markdown(md_path, data)
        return {"json": json_path, "markdown": md_path}

    def _write_json(self, target: Path, data: EvaluationSummaryData) -> None:
        payload = {
            "schema_version": "ml_eval_summary_v1",
            "context": {
                "model_name": data.model_name,
                "model_version": data.model_version,
                "dataset_version": data.dataset_version,
                "predictor_kind": data.predictor_kind,
                "trained_on_dataset_version": data.trained_on_dataset_version,
                "created_at": data.created_at,
            },
            "metrics": {
                "train": asdict(data.train_metrics),
                "test": asdict(data.test_metrics),
                "test_calibrated": asdict(data.calibrated_test_metrics),
                "calibrated_threshold": data.calibrated_threshold,
                "test_row_count": data.test_row_count,
            },
            "interpretation": self._build_interpretation_notes(data),
            "limitations": [data.evaluation_note],
        }
        with target.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)

    def _write_markdown(self, target: Path, data: EvaluationSummaryData) -> None:
        delta_recall = data.calibrated_test_metrics.recall - data.test_metrics.recall
        lines = [
            "# Model Card ligera - Evaluación",
            "",
            f"- Modelo: `{data.model_name}@{data.model_version}`",
            f"- Predictor: `{data.predictor_kind}`",
            f"- Dataset evaluación: `{data.dataset_version}`",
            f"- Entrenado con dataset: `{data.trained_on_dataset_version}`",
            f"- Threshold calibrado: `{data.calibrated_threshold:.3f}`",
            f"- Test rows: `{data.test_row_count}`",
            "",
            "## Métricas clave (test)",
            f"- Accuracy: `{data.test_metrics.accuracy:.3f}`",
            f"- Precision: `{data.test_metrics.precision:.3f}`",
            f"- Recall: `{data.test_metrics.recall:.3f}`",
            "",
            "## Comparación calibración",
            f"- Recall (sin calibrar): `{data.test_metrics.recall:.3f}`",
            f"- Recall (calibrado): `{data.calibrated_test_metrics.recall:.3f}`",
            f"- Delta recall: `{delta_recall:+.3f}`",
            "",
            "## Notas de interpretación",
        ]
        lines.extend([f"- {note}" for note in self._build_interpretation_notes(data)])
        lines.append("")
        lines.append("## Limitaciones")
        lines.append(f"- {data.evaluation_note}")
        target.write_text("\n".join(lines), encoding="utf-8")

    def _build_interpretation_notes(self, data: EvaluationSummaryData) -> list[str]:
        notes = [
            "El predictor baseline no usa entrenamiento; el predictor trained sí usa metadata versionada.",
            "Si una métrica no aplica por falta de casos positivos/negativos, se reporta como 0.0 sin inferencia causal.",
        ]
        if data.test_row_count < 30:
            notes.append("Muestra de test pequeña (<30): interpretar métricas con cautela.")
        if data.dataset_version != data.trained_on_dataset_version:
            notes.append("Dataset de evaluación distinto al de entrenamiento: potencial shift no controlado.")
        return notes
