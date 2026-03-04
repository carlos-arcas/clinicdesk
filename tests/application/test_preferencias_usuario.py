from __future__ import annotations

from dataclasses import replace

from clinicdesk.app.application.preferencias.preferencias_usuario import (
    MARCADOR_REDACTADO,
    PreferenciasService,
    PreferenciasUsuario,
    sanitize_search_text,
)


class RepositorioPreferenciasFake:
    def __init__(self) -> None:
        self._data: dict[str, PreferenciasUsuario] = {}

    def get(self, perfil: str) -> PreferenciasUsuario:
        return self._data.get(perfil, PreferenciasUsuario())

    def set(self, perfil: str, preferencias: PreferenciasUsuario) -> None:
        self._data[perfil] = replace(preferencias)


def test_preferencias_service_roundtrip_perfil() -> None:
    repo = RepositorioPreferenciasFake()
    service = PreferenciasService(repo)

    prefs = PreferenciasUsuario(
        pagina_ultima="pacientes",
        filtros_pacientes={"activo": True, "texto": "Ana"},
        filtros_confirmaciones={"riesgo": "ALTO_MEDIO"},
        last_search_by_context={"pacientes": "ana"},
        columnas_por_contexto={"pacientes": ["nombre", "telefono"]},
    )
    service.set(prefs, perfil="admin")

    restauradas = service.get(perfil="admin")
    assert restauradas.pagina_ultima == "pacientes"
    assert restauradas.filtros_pacientes["texto"] == "Ana"
    assert restauradas.last_search_by_context["pacientes"] == "ana"


def test_sanitize_search_text_detecta_pii() -> None:
    assert sanitize_search_text("test@example.com") == MARCADOR_REDACTADO
    assert sanitize_search_text("12345678Z") == MARCADOR_REDACTADO
    assert sanitize_search_text("+34 666 777 888") == MARCADOR_REDACTADO


def test_sanitize_search_text_permite_texto_normal() -> None:
    assert sanitize_search_text("revisión trimestral") == "revisión trimestral"
    assert sanitize_search_text("   ") is None
