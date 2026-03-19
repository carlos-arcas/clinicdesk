from clinicdesk.app.pages.seguros.workspace_navegacion import (
    EstadoWorkspaceSeguros,
    SECCIONES_WORKSPACE_SEGUROS,
    construir_opciones_selector,
    indice_seccion,
    normalizar_seccion_workspace,
    restaurar_seccion_preferida,
)


class _I18nDummy:
    def t(self, key: str, **kwargs: object) -> str:
        return key


def test_normalizar_seccion_workspace_invalida_vuelve_preventa() -> None:
    assert normalizar_seccion_workspace("desconocida") == "preventa"


def test_estado_workspace_mantiene_seccion_valida() -> None:
    estado = EstadoWorkspaceSeguros()
    assert estado.seleccionar("agenda") == "agenda"


def test_restaurar_seccion_respeta_disponibles() -> None:
    estado = EstadoWorkspaceSeguros(seccion_activa="economia")
    assert restaurar_seccion_preferida(estado, {"preventa", "economia"}) == "economia"
    assert restaurar_seccion_preferida(estado, {"preventa", "agenda"}) == "preventa"


def test_construir_opciones_selector_cubre_todas_las_secciones() -> None:
    opciones = construir_opciones_selector(_I18nDummy())
    valores = [valor for _, valor in opciones]
    assert valores == list(SECCIONES_WORKSPACE_SEGUROS)


def test_indice_seccion_usa_orden_canonico() -> None:
    assert indice_seccion("preventa") == 0
    assert indice_seccion("economia") == len(SECCIONES_WORKSPACE_SEGUROS) - 1
