from clinicdesk.app.application.citas import HitoAtencion, ModoTimestampHito, ResultadoLoteHitosDTO
from clinicdesk.app.pages.citas.lote_hitos_estado import estado_boton_hito_lote
from clinicdesk.app.pages.citas.lote_hitos_resumen import construir_resumen_hitos_lote


class _TraductorFalso:
    def __call__(self, clave: str) -> str:
        catalogo = {
            "citas.hitos.lote.hecho_resumen_detallado": "Hecho: {aplicadas} — Ya estaban: {ya_estaban} — Omitidas: {omitidas}",
            "citas.hitos.lote.algunas_no_actualizadas": "Algunas no se pudieron actualizar. Reintenta.",
        }
        return catalogo[clave]


def test_construir_resumen_hitos_lote_incluye_ya_estaban_y_omitidas() -> None:
    dto = ResultadoLoteHitosDTO(aplicadas=4, ya_estaban=2, omitidas_por_orden=1, no_encontradas=3)

    texto = construir_resumen_hitos_lote(dto, _TraductorFalso())

    assert texto == "Hecho: 4 — Ya estaban: 2 — Omitidas: 4"


def test_construir_resumen_hitos_lote_agrega_advertencia_si_hay_errores() -> None:
    dto = ResultadoLoteHitosDTO(aplicadas=1, errores=1)

    texto = construir_resumen_hitos_lote(dto, _TraductorFalso())

    assert texto.endswith("Algunas no se pudieron actualizar. Reintenta.")


def test_estado_boton_hito_lote_programada_solo_permite_llegada_e_inicio() -> None:
    estado_fin = estado_boton_hito_lote(ModoTimestampHito.PROGRAMADA, HitoAtencion.FIN_CONSULTA)
    estado_llegada = estado_boton_hito_lote(ModoTimestampHito.PROGRAMADA, HitoAtencion.CHECK_IN)

    assert not estado_fin.habilitado
    assert estado_fin.tooltip_key == "citas.hitos.lote.programada_solo_llegada_inicio"
    assert estado_llegada.habilitado
