from __future__ import annotations

from pathlib import Path

RUTA_PAGE_AUDITORIA = Path("clinicdesk/app/pages/auditoria/page.py")


def test_page_auditoria_inyecta_preflight_integridad_en_buscar_y_exportar() -> None:
    contenido = RUTA_PAGE_AUDITORIA.read_text(encoding="utf-8")

    assert "BuscarAuditoriaAccesos(self._queries, verificador_integridad=self._queries)" in contenido
    assert "ExportarAuditoriaCSV(self._queries, verificador_integridad=self._queries)" in contenido
