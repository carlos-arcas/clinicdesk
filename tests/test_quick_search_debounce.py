from clinicdesk.app.ui.quick_search_debounce import DespachadorDebounce


def test_despachador_debounce_despacha_ultimo_texto() -> None:
    debounce = DespachadorDebounce(delay_ms=250)

    debounce.registrar("ana", ahora_ms=1000)
    debounce.registrar("anabel", ahora_ms=1100)

    assert debounce.extraer_si_listo(ahora_ms=1300) is None
    assert debounce.extraer_si_listo(ahora_ms=1350) == "anabel"


def test_despachador_debounce_reinicia_espera() -> None:
    debounce = DespachadorDebounce(delay_ms=200)

    debounce.registrar("a", ahora_ms=0)
    assert debounce.siguiente_espera_ms(ahora_ms=50) == 150

    debounce.registrar("ab", ahora_ms=80)
    assert debounce.siguiente_espera_ms(ahora_ms=200) == 80
