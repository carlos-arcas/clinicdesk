from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.application.features.citas_features import CitasFeatureRow

PredictorInput = CitasFeatureRow


@dataclass(slots=True)
class PredictionResult:
    score: float
    label: str
    reasons: list[str]


class PredictorPort(Protocol):
    def predict_one(self, x: PredictorInput) -> PredictionResult:
        ...

    def predict_batch(self, xs: list[PredictorInput]) -> list[PredictionResult]:
        ...
