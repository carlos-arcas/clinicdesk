from clinicdesk.app.ui.ux.contexto_tabla import FilaTabla, construir_contexto_tabla, resolver_fila_a_restaurar


def test_construir_contexto_tabla_contrata_campos() -> None:
    contexto = construir_contexto_tabla(fila_id=55, scroll_vertical=12, mantener_foco=True)

    assert contexto.fila_id == 55
    assert contexto.scroll_vertical == 12
    assert contexto.mantener_foco is True


def test_resolver_fila_a_restaurar_encuentra_id_objetivo() -> None:
    filas = [
        FilaTabla(fila=0, fila_id=10),
        FilaTabla(fila=1, fila_id=25),
        FilaTabla(fila=2, fila_id=30),
    ]

    assert resolver_fila_a_restaurar(filas, fila_id_objetivo=25) == 1


def test_resolver_fila_a_restaurar_devuelve_none_sin_match() -> None:
    filas = [FilaTabla(fila=0, fila_id=10), FilaTabla(fila=1, fila_id=None)]

    assert resolver_fila_a_restaurar(filas, fila_id_objetivo=99) is None
    assert resolver_fila_a_restaurar(filas, fila_id_objetivo=None) is None
