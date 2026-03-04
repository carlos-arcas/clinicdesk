from __future__ import annotations

from dataclasses import replace

from clinicdesk.app.application.preferencias.preferencias_usuario import (
    PreferenciasService,
    PreferenciasUsuario,
    sanitize_search_text,
)


class RepositorioPreferenciasFake:
    def __init__(self) -> None:
        self._data: dict[str, PreferenciasUsuario] = {}

    def get(self, perfil_id: str | None) -> PreferenciasUsuario:
        perfil = perfil_id or "default"
        return self._data.get(perfil, PreferenciasUsuario())

    def set(self, perfil_id: str | None, preferencias: PreferenciasUsuario) -> None:
        perfil = perfil_id or "default"
        self._data[perfil] = replace(preferencias)


def test_preferencias_service_roundtrip_perfil() -> None:
    repo = RepositorioPreferenciasFake()
    service = PreferenciasService(repo)

    prefs = PreferenciasUsuario(
        pagina_ultima="pacientes",
        filtros_pacientes={"activo": True, "texto": "Ana"},
        filtros_confirmaciones={"riesgo": "ALTO_MEDIO"},
        last_search_by_context={"pacientes": "ana"},
        columnas_por_contexto={"pacientes": {"nombre_width": 140, "nombre_order": "asc"}},
    )
    service.set(prefs, perfil_id="admin")

    restauradas = service.get(perfil_id="admin")
    assert restauradas.pagina_ultima == "pacientes"
    assert restauradas.filtros_pacientes["texto"] == "Ana"
    assert restauradas.last_search_by_context["pacientes"] == "ana"


def test_sanitize_search_text_detecta_pii() -> None:
    assert sanitize_search_text("test@example.com") is None
    assert sanitize_search_text("12345678Z") is None
    assert sanitize_search_text("+34 666 777 888") is None
    assert sanitize_search_text("Calle Mayor 12") is None


def test_sanitize_search_text_permite_texto_normal_y_limite() -> None:
    assert sanitize_search_text("  revisión    trimestral  ") == "revisión trimestral"
    assert sanitize_search_text("   ") is None
    assert sanitize_search_text("x" * 121) is None
