from __future__ import annotations

import pytest

from clinicdesk.app.i18n_catalog import _TRANSLATIONS, _merge_catalogos_sin_duplicados


def test_catalogo_contiene_claves_esperadas() -> None:
    assert _TRANSLATIONS["es"]["ux_states.retry"] == "Reintentar"
    assert _TRANSLATIONS["es"]["job.cancel"] == "Cancelar"
    assert _TRANSLATIONS["es"]["quick_search.title.pacientes"] == "Búsqueda rápida · Pacientes"

    assert _TRANSLATIONS["en"]["ux_states.retry"] == "Retry"
    assert _TRANSLATIONS["en"]["job.cancel"] == "Cancel"
    assert _TRANSLATIONS["en"]["quick_search.title.pacientes"] == "Quick search · Patients"


def test_merge_catalogos_detecta_claves_duplicadas() -> None:
    with pytest.raises(ValueError, match="clave.unica"):
        _merge_catalogos_sin_duplicados(
            {"es": {"clave.unica": "valor1"}},
            {"es": {"clave.unica": "valor2"}},
        )
