from clinicdesk.app.application.usecases.recordatorios_citas import ResultadoLoteRecordatoriosDTO
from clinicdesk.app.pages.confirmaciones.lote_resumen import construir_resumen_lote, construir_texto_resumen_lote


def test_construir_resumen_lote_suma_hechas_y_omitidas() -> None:
    dto = ResultadoLoteRecordatoriosDTO(preparadas=3, enviadas=2, omitidas_sin_contacto=1, omitidas_ya_enviado=4)

    hechas, omitidas = construir_resumen_lote(dto)

    assert hechas == 5
    assert omitidas == 5


def test_construir_resumen_lote_vacio() -> None:
    hechas, omitidas = construir_resumen_lote(ResultadoLoteRecordatoriosDTO())

    assert hechas == 0
    assert omitidas == 0


def test_construir_texto_resumen_lote_con_omitidas() -> None:
    texto = construir_texto_resumen_lote(
        5,
        2,
        lambda clave: {
            "confirmaciones.lote.hecho_resumen": "Hechas 5, omitidas 2",
            "confirmaciones.lote.omitidas_generico": "Se omitieron casos",
        }[clave],
    )

    assert texto == "Hechas 5, omitidas 2. Se omitieron casos"
