from __future__ import annotations

from clinicdesk.app.application.preferencias.preferencias_usuario import PreferenciasUsuario
from clinicdesk.app.infrastructure.preferencias.repositorio_preferencias_json import RepositorioPreferenciasJson


def test_repositorio_json_devuelve_defaults_si_no_existe(tmp_path) -> None:
    repo = RepositorioPreferenciasJson(tmp_path / "prefs_inexistente.json")

    preferencias = repo.get("default")

    assert preferencias == PreferenciasUsuario()


def test_repositorio_json_roundtrip(tmp_path) -> None:
    repo = RepositorioPreferenciasJson(tmp_path / "prefs.json")
    original = PreferenciasUsuario(
        pagina_ultima="confirmaciones",
        filtros_pacientes={"activo": None, "texto": "sin pii"},
        filtros_confirmaciones={"rango": "7D", "texto": "seguimiento"},
        last_search_by_context={"confirmaciones": "recordatorio"},
    )

    repo.set("default", original)
    restauradas = repo.get("default")

    assert restauradas == original
