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
        restaurar_pagina_ultima_en_arranque=True,
        filtros_pacientes={"activo": None, "texto": "sin pii"},
        filtros_confirmaciones={"rango": "7D", "texto": "seguimiento"},
        last_search_by_context={"confirmaciones": "recordatorio"},
        columnas_por_contexto={"confirmaciones": {"fecha_width": 120, "paciente_order": "asc"}},
    )

    repo.set("default", original)
    restauradas = repo.get("default")

    assert restauradas == original


def test_repositorio_json_escritura_atomica_crea_archivo_valido(tmp_path) -> None:
    ruta = tmp_path / "prefs" / "prefs.json"
    repo = RepositorioPreferenciasJson(ruta)

    repo.set(None, PreferenciasUsuario(pagina_ultima="home"))

    assert ruta.exists()
    assert '"default"' in ruta.read_text(encoding="utf-8")


def test_repositorio_json_env_override(tmp_path, monkeypatch) -> None:
    ruta_override = tmp_path / "prefs_override.json"
    monkeypatch.setenv("CLINICDESK_PREFS_PATH", str(ruta_override))

    repo = RepositorioPreferenciasJson()
    repo.set("perfil", PreferenciasUsuario(pagina_ultima="pacientes"))

    assert ruta_override.exists()
    monkeypatch.delenv("CLINICDESK_PREFS_PATH", raising=False)
