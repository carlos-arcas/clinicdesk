from __future__ import annotations

from clinicdesk.app.application.usecases.filtros_auditoria import redactar_texto_filtro_auditoria


def test_redactar_texto_filtro_auditoria_trunca_a_12() -> None:
    assert redactar_texto_filtro_auditoria("usuario.super.sensible") == "usuario.supe…"


def test_redactar_texto_filtro_auditoria_devuelve_none_con_vacio() -> None:
    assert redactar_texto_filtro_auditoria("   ") is None
