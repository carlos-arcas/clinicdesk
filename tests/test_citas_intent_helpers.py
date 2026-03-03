from clinicdesk.app.pages.citas.intent_helpers import buscar_indice_por_cita_id


def test_buscar_indice_por_cita_id_devuelve_indice() -> None:
    assert buscar_indice_por_cita_id([10, 20, 30], 20) == 1


def test_buscar_indice_por_cita_id_devuelve_none() -> None:
    assert buscar_indice_por_cita_id([10, 20, 30], 99) is None
