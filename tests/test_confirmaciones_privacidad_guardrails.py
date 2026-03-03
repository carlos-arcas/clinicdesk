from __future__ import annotations

from clinicdesk.app.application.citas.filtros import redactar_texto_busqueda
from clinicdesk.app.pages.confirmaciones.columnas import claves_columnas_confirmaciones
from clinicdesk.app.pages.confirmaciones.lote_resumen import construir_texto_resumen_lote

_COLUMNAS_PII_PROHIBIDAS = {"telefono", "email", "documento", "direccion", "notas"}


def test_columnas_confirmaciones_no_incluyen_pii() -> None:
    columnas = set(claves_columnas_confirmaciones())

    assert not (columnas & _COLUMNAS_PII_PROHIBIDAS)


def test_resumen_lote_no_filtra_pii() -> None:
    texto = construir_texto_resumen_lote(
        3,
        2,
        lambda clave: {
            "confirmaciones.lote.hecho_resumen": "Hechas: 3 Omitidas: 2",
            "confirmaciones.lote.omitidas_generico": "Se omitieron algunos casos",
        }[clave],
    )

    assert "@" not in texto
    assert "+34" not in texto
    assert "Paciente" not in texto


def test_redaccion_texto_busqueda_en_confirmaciones() -> None:
    texto = "mi dni 12345678Z"

    redaccion = redactar_texto_busqueda(texto)

    assert redaccion != texto
    assert redaccion == "mi dni 12345…"
