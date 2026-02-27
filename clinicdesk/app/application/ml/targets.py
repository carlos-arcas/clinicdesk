from __future__ import annotations

from clinicdesk.app.application.features.citas_features import CitasFeatureRow


def derive_target_from_feature(row: CitasFeatureRow) -> int:
    """Etiqueta proxy determinista para entrenamiento/evaluación offline."""
    return int(row.has_incidencias or row.is_suspicious)
